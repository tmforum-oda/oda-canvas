"""
normalize_whitespace.py

A tool to recursively normalize whitespace in all files matching a filename pattern.

Features:
- Normalizes all line endings (\\n, \\r, \\r\\n) to a single format (\\r\\n for Windows by default)
- Optionally replaces tab characters with spaces

Usage:
    python normalize_whitespace.py <folder> <pattern> [--line-ending {crlf,lf,cr}] [--tabs-to-spaces [N]] [--dry-run]

Examples:
    python normalize_whitespace.py . "*.py"
    python normalize_whitespace.py ./src "*.java" --line-ending lf
    python normalize_whitespace.py . "*.txt" --tabs-to-spaces 4
"""

import argparse
import fnmatch
import os
import sys


LINE_ENDINGS = {
    "crlf": b"\r\n",
    "lf": b"\n",
    "cr": b"\r",
}


def find_files(folder: str, pattern: str, include_hidden: bool = False):
    """Recursively yield file paths matching the given filename pattern.

    Args:
        folder: Root directory to walk.
        pattern: Filename glob pattern to match against.
        include_hidden: If True, also recurse into hidden directories (those
            starting with a dot, e.g. .git).
    """
    for root, dirs, files in os.walk(folder):
        # Skip hidden directories (e.g. .git) unless explicitly included
        if not include_hidden:
            dirs[:] = [d for d in dirs if not d.startswith(".")]
        for filename in files:
            if fnmatch.fnmatch(filename, pattern):
                yield os.path.join(root, filename)


def normalize_file(
    filepath: str,
    line_ending: bytes = b"\r\n",
    tabs_to_spaces: int = None,
    dry_run: bool = False,
) -> bool:
    """
    Normalize line endings (and optionally tabs) in a single file.

    Args:
        filepath: Path to the file to normalize.
        line_ending: The target line ending bytes (default: b'\\r\\n').
        tabs_to_spaces: If set, replace each tab with this many spaces. None means no replacement.
        dry_run: If True, do not write changes, only report what would change.

    Returns:
        True if the file was (or would be) modified, False otherwise.
    """
    try:
        with open(filepath, "rb") as f:
            original = f.read()
    except (OSError, IOError) as e:
        print(f"  ERROR reading {filepath}: {e}", file=sys.stderr)
        return False

    # Normalize all line endings to LF first, then convert to target.
    # Handle \r\n before \r to avoid double-processing.
    normalized = original.replace(b"\r\n", b"\n").replace(b"\r", b"\n")

    # Convert to target line ending
    normalized = normalized.replace(b"\n", line_ending)

    # Optionally replace tabs with spaces
    if tabs_to_spaces is not None:
        spaces = b" " * tabs_to_spaces
        normalized = normalized.replace(b"\t", spaces)

    if normalized == original:
        return False

    if not dry_run:
        try:
            with open(filepath, "wb") as f:
                f.write(normalized)
        except (OSError, IOError) as e:
            print(f"  ERROR writing {filepath}: {e}", file=sys.stderr)
            return False

    return True


def main():
    """Entry point: parse arguments and run the normalization."""
    parser = argparse.ArgumentParser(
        description="Recursively normalize whitespace in files matching a pattern.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "folder",
        help="Root folder to search recursively.",
    )
    parser.add_argument(
        "pattern",
        help='Filename glob pattern, e.g. "*.py" or "*.txt".',
    )
    parser.add_argument(
        "--line-ending",
        choices=["crlf", "lf", "cr"],
        default="crlf",
        help="Target line ending format (default: crlf = \\r\\n).",
    )
    parser.add_argument(
        "--tabs-to-spaces",
        metavar="N",
        type=int,
        nargs="?",
        const=4,
        default=None,
        help=(
            "Replace tab characters with spaces. "
            "Optionally specify number of spaces per tab (default when flag is set: 4)."
        ),
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Also recurse into hidden directories (those starting with a dot, e.g. .git).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show which files would be modified without actually changing them.",
    )

    args = parser.parse_args()

    if not os.path.isdir(args.folder):
        print(f"ERROR: '{args.folder}' is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    line_ending = LINE_ENDINGS[args.line_ending]
    line_ending_label = args.line_ending.upper()

    print(f"Folder      : {os.path.abspath(args.folder)}")
    print(f"Pattern     : {args.pattern}")
    print(f"Line ending : {line_ending_label} ({repr(line_ending)})")
    if args.tabs_to_spaces is not None:
        print(f"Tabs->spaces: {args.tabs_to_spaces} spaces per tab")
    if args.dry_run:
        print("Mode        : DRY RUN (no files will be modified)")
    if args.include_hidden:
        print("Hidden dirs : included")
    print()

    total = 0
    modified = 0

    for filepath in find_files(args.folder, args.pattern, include_hidden=args.include_hidden):
        total += 1
        changed = normalize_file(
            filepath,
            line_ending=line_ending,
            tabs_to_spaces=args.tabs_to_spaces,
            dry_run=args.dry_run,
        )
        if changed:
            modified += 1
            status = "[DRY RUN] would modify" if args.dry_run else "modified"
            print(f"  {status}: {filepath}")

    print()
    print(
        f"Done. {modified}/{total} file(s) "
        f"{'would be ' if args.dry_run else ''}modified."
    )


if __name__ == "__main__":
    #sys.argv = ["normalize_whitespace.py", "COMP/TMF638_Service_Inventory_NORM", "*.js", "--line-ending", "crlf", "--tabs-to-spaces", "4", "--dry-run"]
    #sys.argv = ["normalize_whitespace.py", "COMP/TMF638_Service_Inventory_NORM", "*", "--line-ending", "crlf", "--tabs-to-spaces", "4", "--include-hidden"]
    #sys.argv = ["normalize_whitespace.py", "COMP/TMF638_Service_Inventory-RI-v5.0.0_NORM", "*", "--line-ending", "crlf", "--tabs-to-spaces", "4", "--include-hidden"]
    main()
