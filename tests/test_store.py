import json

import pytest

from box_remaining.model import Box, BoxError
from box_remaining.store import BoxStore, default_data_path


@pytest.fixture
def data_file(tmp_path):
    return tmp_path / "boxes.json"


def test_missing_file_loads_as_empty_store(data_file):
    store = BoxStore.load(data_file)
    assert len(store) == 0
    assert store.names() == []
    assert store.total_remaining == 0


def test_add_save_and_reload(data_file):
    store = BoxStore.load(data_file)
    store.add("pantry", 12).put("tea", 5)
    store.add("attic", 30)
    store.save()

    reloaded = BoxStore.load(data_file)
    assert reloaded.names() == ["attic", "pantry"]
    assert reloaded.get("pantry").items == {"tea": 5}
    assert reloaded.get("pantry").remaining == 7
    assert reloaded.total_capacity == 42
    assert reloaded.total_used == 5
    assert reloaded.total_remaining == 37


def test_save_creates_parent_directories(tmp_path):
    path = tmp_path / "nested" / "deeper" / "boxes.json"
    store = BoxStore.load(path)
    store.add("pantry", 4)
    store.save()
    assert path.exists()
    assert json.loads(path.read_text())["boxes"][0]["name"] == "pantry"


def test_save_leaves_no_temp_file_behind(data_file):
    store = BoxStore.load(data_file)
    store.add("pantry", 4)
    store.save()
    assert sorted(p.name for p in data_file.parent.iterdir()) == ["boxes.json"]


def test_duplicate_add_is_refused(data_file):
    store = BoxStore.load(data_file)
    store.add("pantry", 4)
    with pytest.raises(BoxError, match="already exists"):
        store.add("pantry", 8)


def test_get_unknown_box_lists_the_known_ones(data_file):
    store = BoxStore.load(data_file)
    store.add("pantry", 4)
    with pytest.raises(BoxError, match=r"no box named 'attic' \(known boxes: pantry\)"):
        store.get("attic")


def test_remove_drops_the_box(data_file):
    store = BoxStore.load(data_file)
    store.add("pantry", 4)
    removed = store.remove("pantry")
    assert removed.name == "pantry"
    assert "pantry" not in store
    store.save()
    assert BoxStore.load(data_file).names() == []


def test_unicode_survives_the_round_trip(data_file):
    store = BoxStore.load(data_file)
    store.add("押し入れ", 10).put("毛布", 2)
    store.save()
    assert "毛布" in data_file.read_text(encoding="utf-8")
    assert BoxStore.load(data_file).get("押し入れ").remaining == 8


def test_invalid_json_is_reported_with_the_path(data_file):
    data_file.write_text("{not json")
    with pytest.raises(BoxError, match="is not valid JSON"):
        BoxStore.load(data_file)


def test_bare_list_payload_is_accepted(data_file):
    data_file.write_text(json.dumps([{"name": "pantry", "capacity": 3}]))
    assert BoxStore.load(data_file).get("pantry").remaining == 3


def test_wrong_shaped_payload_is_reported(data_file):
    data_file.write_text(json.dumps({"boxes": {"pantry": 3}}))
    with pytest.raises(BoxError, match="expected a list of boxes"):
        BoxStore.load(data_file)


def test_duplicate_records_are_reported(data_file):
    data_file.write_text(
        json.dumps({"boxes": [{"name": "pantry", "capacity": 3}] * 2})
    )
    with pytest.raises(BoxError, match="duplicate box 'pantry'"):
        BoxStore.load(data_file)


def test_iteration_is_sorted_by_name(data_file):
    store = BoxStore.load(data_file)
    for name in ("zebra", "attic", "pantry"):
        store.add(name, 1)
    assert [b.name for b in store] == ["attic", "pantry", "zebra"]


def test_env_var_overrides_the_default_path(tmp_path, monkeypatch):
    monkeypatch.setenv("BOX_REMAINING_DATA", str(tmp_path / "custom.json"))
    assert default_data_path() == tmp_path / "custom.json"
    monkeypatch.delenv("BOX_REMAINING_DATA")
    assert default_data_path().name == "boxes.json"
