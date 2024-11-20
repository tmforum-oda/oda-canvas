import sys
import fileinput
import datetime
import argparse
from rich.tree import Tree
from rich import print as rich_print

from rich.console import Console
from rich.text import Text


import re
import fnmatch
import json

from timedinput import timedinput
from _queue import Empty

import asyncio
import queue
import threading


config = {}


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


def checkCompFilter(compname, compfilter):
    if not compfilter:
        return True
    if compname == compfilter:
        return True
    if not compname:
        return False
    return fnmatch.fnmatch(compname, compfilter)


def checkTimeFilter(time, mintimefilter):
    if mintimefilter is None:
        return True
    return time >= mintimefilter


def calc_mintime_filter():
    lasthours = config["lasthours"]
    if not lasthours:
        return None
    tshifth = config["tshifth"]
    if tshifth:
        lasthours = lasthours - tshifth
    datetimeformat = config["datetimeformat"]
    now = datetime.datetime.now()
    mintime = now - datetime.timedelta(hours=lasthours)
    return mintime.strftime(datetimeformat)


def create_log_tree():
    filename = config["filename"]
    compfilter = config["compfilter"]
    mintimefilter = calc_mintime_filter()
    if filename == "-":  # stdin
        if config["follow"]:
            sysinq = config["sysinq"]
            lines = []
            try:
                while True:
                    line = sysinq.get(timeout=1.0)
                    lines.append(line)
            except Empty:
                pass
        else:
            lines = list(fileinput.input(files=[]))
    else:
        if config["follow"]:
            raise ValueError("--follow not yet supported with file inputs")
        lines = list(fileinput.input(files=[filename]))
    entries = parse_log(lines)
    logTree = {}
    for entry in entries:
        if not checkCompFilter(entry["component"], compfilter):
            continue
        if not checkTimeFilter(entry["time"], mintimefilter):
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


def show_log_tree():
    first_time = True
    while True:
        logTree = create_log_tree()
        if first_time or logTree:
            tree = Tree(f'[green]Canvas Log Viewer ({config["filename"]})')
            recursive_build_tree(logTree, tree)
            rich_print(tree)
        if not config["follow"]:
            break
        first_time = False


def sysinreader():
    sysinq = config["sysinq"]
    while True:
        line = sys.stdin.readline()
        sysinq.put(line.rstrip())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Canvas Log Viewer", description="display tree view of logfiles"
    )
    parser.add_argument(
        "-c",
        "--component-filter",
        type=str,
        help='filter components by name with wildcards (*/?), e.g. "comp-a-*"',
        required=False,
    )
    parser.add_argument(
        "-d",
        "--datetime-format",
        type=str,
        help='format of timestaps in log, default "%%Y-%%m-%%d %%H:%%M:%%S,000"',
        default="%Y-%m-%d %H:%M:%S,000",
    )
    parser.add_argument(
        "-f",
        "--follow",
        action=argparse.BooleanOptionalAction,
        help="keep the Log Viewer open and update the display on incoming logs",
    )
    parser.add_argument(
        "-l",
        "--last-hours",
        type=float,
        required=False,
        help="only look at the last n hours",
    )
    parser.add_argument(
        "-i",
        "--input-file",
        type=str,
        help="use file as input instead of stdin",
        default="-",
    )
    parser.add_argument(
        "-t",
        "--time-shift-hours",
        type=float,
        help="log files have a time shift by t hours",
        default=0.0,
    )

    # testargs = ["-i", "depapi.log", "-l", "8", "-t", "-1", "-d", "%Y-%m-%d %H:%M:%S,000", "-c", "testdapi-*"]
    # args = parser.parse_args(testargs)

    args = parser.parse_args()

    config["compfilter"] = args.component_filter
    config["datetimeformat"] = args.datetime_format
    config["follow"] = bool(args.follow)
    config["lasthours"] = args.last_hours
    config["filename"] = args.input_file
    config["tshifth"] = args.time_shift_hours

    if config["follow"]:
        config["sysinq"] = queue.Queue()
        threading.Thread(target=sysinreader, daemon=True).start()
    show_log_tree()
