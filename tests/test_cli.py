import pytest

from box_remaining.cli import main


@pytest.fixture
def run(tmp_path, capsys):
    data = tmp_path / "boxes.json"

    def _run(*argv):
        code = main(["--data", str(data), *argv])
        captured = capsys.readouterr()
        return code, captured.out, captured.err

    return _run


def test_remaining_on_an_empty_store_is_not_an_error(run):
    code, out, err = run("remaining")
    assert code == 0
    assert "no boxes yet" in out
    assert err == ""


def test_add_put_and_remaining(run):
    assert run("add", "pantry", "--capacity", "12")[0] == 0
    assert run("put", "pantry", "tea", "5")[0] == 0

    code, out, _ = run("remaining")
    assert code == 0
    assert "BOX" in out and "REMAINING" in out
    assert "pantry" in out
    # capacity 12, used 5, remaining 7
    assert "12" in out and "5" in out and "7" in out


def test_remaining_reports_a_total_only_for_several_boxes(run):
    run("add", "pantry", "--capacity", "12")
    _, single, _ = run("remaining")
    assert "total:" not in single

    run("add", "attic", "--capacity", "30")
    _, both, _ = run("remaining")
    assert "total: 42 of 42 free across 2 boxes" in both


def test_remaining_can_be_limited_to_one_box(run):
    run("add", "pantry", "--capacity", "12")
    run("add", "attic", "--capacity", "30")
    code, out, _ = run("remaining", "pantry")
    assert code == 0
    assert "pantry" in out
    assert "attic" not in out


def test_put_beyond_capacity_fails_without_writing(run):
    run("add", "pantry", "--capacity", "2")
    run("put", "pantry", "tea", "2")

    code, out, err = run("put", "pantry", "coffee")
    assert code == 1
    assert out == ""
    assert "only 0 of 2 left" in err

    _, listing, _ = run("list")
    assert "coffee" not in listing


def test_take_puts_room_back(run):
    run("add", "pantry", "--capacity", "12")
    run("put", "pantry", "tea", "5")
    code, out, _ = run("take", "pantry", "tea", "3")
    assert code == 0
    assert "10 left" in out


def test_take_more_than_held_fails(run):
    run("add", "pantry", "--capacity", "12")
    run("put", "pantry", "tea")
    code, _, err = run("take", "pantry", "tea", "4")
    assert code == 1
    assert "only 1 of 'tea'" in err


def test_unknown_box_fails_cleanly(run):
    run("add", "pantry", "--capacity", "12")
    code, _, err = run("put", "attic", "tea")
    assert code == 1
    assert "no box named 'attic'" in err


def test_list_shows_contents_and_empty_boxes(run):
    run("add", "pantry", "--capacity", "12")
    run("put", "pantry", "tea", "5")
    run("add", "attic", "--capacity", "3")

    code, out, _ = run("list")
    assert code == 0
    assert "pantry  (5/12 used, 7 left)" in out
    assert "5 x tea" in out
    assert "attic  (0/3 used, 3 left)" in out
    assert "(empty)" in out


def test_rm_deletes_the_box(run):
    run("add", "pantry", "--capacity", "12")
    code, out, _ = run("rm", "pantry")
    assert code == 0
    assert "removed box 'pantry'" in out
    assert "no boxes yet" in run("list")[1]


def test_duplicate_add_fails(run):
    run("add", "pantry", "--capacity", "12")
    code, _, err = run("add", "pantry", "--capacity", "4")
    assert code == 1
    assert "already exists" in err


def test_fill_bar_tracks_usage(run):
    run("add", "pantry", "--capacity", "20")
    run("put", "pantry", "tea", "10")
    _, out, _ = run("remaining")
    assert "##########.........." in out


def test_a_single_item_always_shows_at_least_one_bar_segment(run):
    run("add", "warehouse", "--capacity", "1000")
    run("put", "warehouse", "tea")
    _, out, _ = run("remaining")
    assert "#..................." in out


def test_no_subcommand_is_a_usage_error(run):
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 2


def test_display_width_counts_cjk_as_two_columns():
    from box_remaining.cli import _display_width

    assert _display_width("pantry") == 6
    assert _display_width("押し入れ") == 8
    assert _display_width("箱x2") == 4


def test_columns_line_up_with_a_full_width_box_name(run):
    from box_remaining.cli import _display_width

    run("add", "pantry", "--capacity", "12")
    run("add", "押し入れ", "--capacity", "30")
    _, out, _ = run("remaining")

    rows = [line for line in out.splitlines() if "." in line and "#" not in line[:1]]
    assert len(rows) == 2, out
    # the FILL column starts at the same display column on every row
    fill_starts = {_display_width(row[: row.index(".")]) for row in rows}
    assert len(fill_starts) == 1
