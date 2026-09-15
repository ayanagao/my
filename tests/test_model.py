import pytest

from box_remaining.model import Box, BoxError


def test_remaining_starts_at_capacity():
    box = Box("pantry", 12)
    assert box.used == 0
    assert box.remaining == 12
    assert not box.is_full


def test_put_reduces_remaining():
    box = Box("pantry", 12)
    box.put("tea", 4)
    box.put("tea", 2)
    box.put("coffee")
    assert box.items == {"tea": 6, "coffee": 1}
    assert box.used == 7
    assert box.remaining == 5


def test_put_beyond_capacity_is_refused_and_leaves_box_unchanged():
    box = Box("pantry", 3)
    box.put("tea", 3)
    assert box.is_full
    with pytest.raises(BoxError, match="only 0 of 3 left"):
        box.put("coffee")
    assert box.items == {"tea": 3}


def test_take_removes_the_key_when_it_empties():
    box = Box("pantry", 10, {"tea": 2})
    box.take("tea", 2)
    assert box.items == {}
    assert box.remaining == 10


def test_take_more_than_held_is_refused():
    box = Box("pantry", 10, {"tea": 2})
    with pytest.raises(BoxError, match="only 2 of 'tea'"):
        box.take("tea", 3)
    assert box.items == {"tea": 2}


def test_take_missing_item_is_refused():
    with pytest.raises(BoxError, match="only 0 of 'tea'"):
        Box("pantry", 10).take("tea")


@pytest.mark.parametrize("count", [0, -1])
def test_non_positive_counts_are_refused(count):
    box = Box("pantry", 10, {"tea": 5})
    with pytest.raises(BoxError, match="count must be positive"):
        box.put("tea", count)
    with pytest.raises(BoxError, match="count must be positive"):
        box.take("tea", count)


def test_zero_capacity_box_is_full_immediately():
    box = Box("sealed", 0)
    assert box.remaining == 0
    assert box.is_full


def test_invalid_boxes_are_rejected():
    with pytest.raises(BoxError, match="name must not be empty"):
        Box("  ", 5)
    with pytest.raises(BoxError, match="capacity must not be negative"):
        Box("pantry", -1)
    with pytest.raises(BoxError, match="must not be negative"):
        Box("pantry", 5, {"tea": -2})
    with pytest.raises(BoxError, match="exceed capacity"):
        Box("pantry", 2, {"tea": 3})


def test_round_trips_through_dict():
    box = Box("pantry", 9, {"tea": 3})
    clone = Box.from_dict(box.to_dict())
    assert clone == box
    assert clone.remaining == 6


def test_from_dict_rejects_malformed_records():
    with pytest.raises(BoxError, match="malformed box record"):
        Box.from_dict({"capacity": 3})
    with pytest.raises(BoxError, match="malformed items"):
        Box.from_dict({"name": "pantry", "capacity": 3, "items": [1, 2]})
