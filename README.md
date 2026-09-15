# box-remaining

A small CLI for tracking what is in your boxes and, above all, **how much room is left**.

```
$ box remaining
BOX       CAPACITY  USED  REMAINING  FILL
pantry          12     7          5  ############........
押し入れ        30     4         26  ###.................

total: 31 of 42 free across 2 boxes
```

## Install

```sh
pip install -e .
```

That puts a `box` command on your PATH. Without installing, the same CLI runs as
`PYTHONPATH=src python3 -m box_remaining.cli ...`.

There are no runtime dependencies; Python 3.9 or newer is enough.

## Usage

```sh
box add pantry --capacity 12     # create a box that holds 12 items
box put pantry tea 5             # put 5 tea into it
box take pantry tea 2            # take 2 back out
box remaining                    # how much room is left, per box and in total
box remaining pantry             # just one box
box list                         # every box with its contents
box rm pantry                    # delete a box
```

`put` and `take` always print the new remaining count, so the common case —
"how much is left?" — needs no second command.

Operations that would break a box are refused and change nothing:

```sh
$ box put pantry rice 99
box: pantry: cannot fit 99 more (only 5 of 12 left)
$ echo $?
1
```

## Where the data lives

Boxes are stored as JSON, by default in `~/.box-remaining/boxes.json`. Override
it per invocation with `--data PATH`, or for a whole shell with the
`BOX_REMAINING_DATA` environment variable:

```sh
export BOX_REMAINING_DATA=~/Dropbox/boxes.json
```

Writes go to a temporary file that is then renamed over the target, so an
interrupted save cannot leave a half-written file behind.

The format is plain and hand-editable:

```json
{
  "boxes": [
    { "name": "pantry", "capacity": 12, "items": { "tea": 5, "coffee": 2 } }
  ]
}
```

## Library use

```python
from box_remaining import Box, BoxStore

store = BoxStore.load()          # honours BOX_REMAINING_DATA
pantry = store.get("pantry")
print(pantry.remaining)
pantry.put("tea", 3)
store.save()
```

`Box.put` / `Box.take` raise `BoxError` rather than letting a box overflow or go
negative, and `BoxStore.load` raises the same error for a malformed file.

## Development

```sh
pip install pytest
python3 -m pytest
```
