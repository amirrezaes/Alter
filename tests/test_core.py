from alter.core.downloader import compute_ranges
from alter.core.formatting import format_bytes


def test_compute_ranges_even_split() -> None:
    ranges = compute_ranges(100, 4)
    assert ranges[0] == (0, 24)
    assert ranges[-1] == (75, 99)
    assert len(ranges) == 4


def test_compute_ranges_small_size() -> None:
    ranges = compute_ranges(3, 10)
    assert ranges == [(0, 0), (1, 1), (2, 2)]


def test_format_bytes() -> None:
    assert format_bytes(0) == "0 B"
    assert format_bytes(1024) == "1.0 KB"
    assert format_bytes(1024 * 1024) == "1.0 MB"
