import sys
import fileinput
from rich.tree import Tree
from rich import print

from rich.console import Console
from rich.text import Text


import re
import fnmatch
import json

# [2024-11-17 13:05:34,612] SManOP               [INFO    ] [demo-a-productcatalogmanagement|SMan/demo-a-productcatalogmanagement|secretsmanagementDelete|secretsmanagementDelete] Delete  called with namespace: components
# [<TIME>] <LOGGER> [<LEVEL>] [<COMPONENT>|<RESOURCE>|<HANDLER>|<FUNCTION>] <SUBJECT>: <MESSAGE>
sp = "\\s+"
TIME_RX = "\\[(?P<time>[-0-9 :,.]+)\\]"
LOGGER_RX = "(?P<logger>[^ ]+)"
LEVEL_RX = "\\[(?P<level>[A-Z]+)\\s*\\]"
COMPONENT_RX = "\\[(?P<component>[^|]*)\\|"
RESOURCE_RX = "(?P<resource>[^|]*)\\|"
RESOURCE_ONLY_RX = "\\[(?P<resourceonly>[^\\]|]*)\\]"
HANDLER_RX = "(?P<handler>[^|]*)\\|"
FUNCTION_RX = "(?P<function>[^\\]]*)\\]"
SUBJECT_RX = "(?P<subject>[^:]+):"
MESSAGE_RX = "(?P<message>.*)"

LINE_RX = re.compile(
    f"{TIME_RX}{sp}{LOGGER_RX}{sp}{LEVEL_RX}{sp}({COMPONENT_RX}{RESOURCE_RX}{HANDLER_RX}{FUNCTION_RX}{sp}{SUBJECT_RX}{sp}|{RESOURCE_ONLY_RX}{sp}|){MESSAGE_RX}"
)


def nvl(obj, none_value):
    if obj is None:
        return none_value
    else:
        return str(obj)


def parse_log(lines):
    result = []
    last_entry = {"message": ""}
    for line in lines:
        m = LINE_RX.match(line)
        if m:
            entry = {
                "time": m.group("time"),
                "logger": m.group("logger"),
                "level": m.group("level"),
                "component": nvl(m.group("component"), ""),
                "resource": nvl(m.group("resource"), nvl(m.group("resourceonly"), "")),
                "handler": nvl(m.group("handler"), ""),
                "function": nvl(m.group("function"), ""),
                "subject": nvl(m.group("subject"), ""),
                "message": m.group("message"),
            }
            result.append(entry)
            last_entry = entry
        else:
            last_entry["message"] = f"{last_entry['message']}\n{line}"
    return result


def checkFilter(compname, compfilter):
    if not compfilter:
        return True
    if compname == compfilter:
        return True
    if not compname:
        return False
    return fnmatch.fnmatch(compname, compfilter)


def create_log_tree(filename, compfilter):
    files = [] if filename == "-" else [filename]
    lines = list(fileinput.input(files=files))
    # lines = lines[0:20]
    entries = parse_log(lines)
    logTree = {}
    for entry in entries:
        if not checkFilter(entry["component"], compfilter):
            continue
        next = logTree
        if entry["component"] not in next:
            next[entry["component"]] = {}
        next = next[entry["component"]]
        if entry["resource"] not in next:
            next[entry["resource"]] = {}
        next = next[entry["resource"]]
        if entry["logger"] not in next:
            next[entry["logger"]] = {}
        next = next[entry["logger"]]
        if entry["handler"] not in next:
            next[entry["handler"]] = {}
        next = next[entry["handler"]]
        if entry["function"] not in next:
            next[entry["function"]] = []
        next = next[entry["function"]]
        message = (
            f'{entry["subject"]}: {entry["message"]}'
            if entry["subject"]
            else entry["message"]
        )

        text = Text()
        text.append(entry["time"] + " ", style="#808080")
        if entry["function"]:
            text.append(entry["function"] + ": ")
        if entry["level"] == "INFO":
            text.append(message, style="green")
        elif entry["level"] == "ERROR":
            text.append(message, style="red")
        elif entry["level"] == "WARNING":
            text.append(message, style="yellow")
        elif entry["level"] == "DEBUG":
            text.append(message, style="lightblue")
        else:
            text.append(message)
        next.append(text)
    return logTree


def recursive_build_tree(input_tree, output_tree):
    if isinstance(input_tree, list):
        for line in input_tree:
            output_tree.add(line)
        return
    for k, v in input_tree.items():
        if k:
            child = output_tree.add(k)
        else:
            child = output_tree
        recursive_build_tree(v, child)


def show_log_tree(filename, compfilter):
    logTree = create_log_tree(filename, compfilter)
    tree = Tree(f"[green]Canvas Log Viewer ({filename})")
    recursive_build_tree(logTree, tree)
    print(tree)


if __name__ == "__main__":
    compfilter = sys.argv[1] if len(sys.argv) > 1 else None
    filename = "-"  # stdin
    show_log_tree(filename, compfilter)
