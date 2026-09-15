"""Command line interface: `box remaining` and friends."""

from __future__ import annotations

import argparse
import sys
import unicodedata
from pathlib import Path
from typing import Container, List, Optional, Sequence

from .model import Box, BoxError
from .store import ENV_VAR, BoxStore


def _display_width(text: str) -> int:
    """Terminal columns `text` occupies, counting CJK characters as two."""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def _pad(text: str, width: int, right: bool) -> str:
    fill = " " * max(0, width - _display_width(text))
    return fill + text if right else text + fill


def _render_table(rows: Sequence[Sequence[str]], right_align: Container[int] = ()) -> str:
    if not rows:
        return ""
    widths = [max(_display_width(row[i]) for row in rows) for i in range(len(rows[0]))]
    lines = []
    for row in rows:
        cells = [_pad(cell, widths[i], i in right_align) for i, cell in enumerate(row)]
        lines.append("  ".join(cells).rstrip())
    return "\n".join(lines)


def _bar(box: Box, width: int = 20) -> str:
    if box.capacity == 0:
        return "-" * width
    filled = round(box.used / box.capacity * width)
    filled = min(width, max(0, filled))
    if box.used > 0 and filled == 0:
        filled = 1
    return "#" * filled + "." * (width - filled)


def _remaining_table(boxes: Sequence[Box]) -> List[List[str]]:
    rows = [["BOX", "CAPACITY", "USED", "REMAINING", "FILL"]]
    for box in boxes:
        rows.append(
            [
                box.name,
                str(box.capacity),
                str(box.used),
                str(box.remaining),
                _bar(box),
            ]
        )
    return rows


# -- commands -------------------------------------------------------------


def cmd_add(store: BoxStore, args: argparse.Namespace) -> int:
    box = store.add(args.name, args.capacity)
    store.save()
    print(f"added box {box.name!r} with capacity {box.capacity}")
    return 0


def cmd_rm(store: BoxStore, args: argparse.Namespace) -> int:
    box = store.remove(args.name)
    store.save()
    print(f"removed box {box.name!r} (held {box.used} item(s))")
    return 0


def cmd_put(store: BoxStore, args: argparse.Namespace) -> int:
    box = store.get(args.box)
    box.put(args.item, args.count)
    store.save()
    print(f"{box.name}: put {args.count} x {args.item} -> {box.remaining} left")
    return 0


def cmd_take(store: BoxStore, args: argparse.Namespace) -> int:
    box = store.get(args.box)
    box.take(args.item, args.count)
    store.save()
    print(f"{box.name}: took {args.count} x {args.item} -> {box.remaining} left")
    return 0


def cmd_remaining(store: BoxStore, args: argparse.Namespace) -> int:
    if len(store) == 0:
        print("no boxes yet - add one with: box add <name> --capacity N")
        return 0
    boxes = [store.get(args.name)] if args.name else list(store)
    print(_render_table(_remaining_table(boxes), right_align={1, 2, 3}))
    if len(boxes) > 1:
        print()
        print(
            f"total: {store.total_remaining} of {store.total_capacity} free "
            f"across {len(boxes)} boxes"
        )
    return 0


def cmd_list(store: BoxStore, args: argparse.Namespace) -> int:
    if len(store) == 0:
        print("no boxes yet - add one with: box add <name> --capacity N")
        return 0
    for box in store:
        print(f"{box.name}  ({box.used}/{box.capacity} used, {box.remaining} left)")
        for item, count in sorted(box.items.items()):
            print(f"    {count:>4} x {item}")
        if not box.items:
            print("    (empty)")
    return 0


# -- entry point ----------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="box",
        description="Track what is in your boxes and how much room is left.",
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=None,
        metavar="PATH",
        help=f"JSON file holding the boxes (default: ${ENV_VAR} or ~/.box-remaining/boxes.json)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="create a new box")
    p_add.add_argument("name")
    p_add.add_argument("--capacity", type=int, required=True, help="how many items fit")
    p_add.set_defaults(func=cmd_add)

    p_rm = sub.add_parser("rm", help="delete a box")
    p_rm.add_argument("name")
    p_rm.set_defaults(func=cmd_rm)

    p_put = sub.add_parser("put", help="put items into a box")
    p_put.add_argument("box")
    p_put.add_argument("item")
    p_put.add_argument("count", type=int, nargs="?", default=1)
    p_put.set_defaults(func=cmd_put)

    p_take = sub.add_parser("take", help="take items out of a box")
    p_take.add_argument("box")
    p_take.add_argument("item")
    p_take.add_argument("count", type=int, nargs="?", default=1)
    p_take.set_defaults(func=cmd_take)

    p_remaining = sub.add_parser("remaining", help="show how much room is left")
    p_remaining.add_argument("name", nargs="?", help="limit to a single box")
    p_remaining.set_defaults(func=cmd_remaining)

    p_list = sub.add_parser("list", help="show every box and its contents")
    p_list.set_defaults(func=cmd_list)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        store = BoxStore.load(args.data)
        return args.func(store, args)
    except BoxError as exc:
        print(f"box: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
