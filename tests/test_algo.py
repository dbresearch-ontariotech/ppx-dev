import pytest
from ppx.core.algo import dp_align_nodes


def exact_sim(x, y_slice):
    """Returns 1.0 if x equals the joined slice, 0.0 otherwise."""
    return 1.0 if " ".join(y_slice) == x else 0.0


Y = ["hello", "world", "foo", "bar", "baz"]


def test_full_range_default():
    """Without a/b, covers all of Y."""
    X = ["hello world", "foo bar baz"]
    intervals = dp_align_nodes(X, Y, exact_sim)
    assert intervals == [(0, 2), (2, 5)]


def test_subrange_absolute_indices():
    """a=1, b=4 restricts alignment to Y[1:4] = ['world','foo','bar']."""
    X = ["world foo", "bar"]
    intervals = dp_align_nodes(X, Y, exact_sim, a=1, b=4)
    assert intervals == [(1, 3), (3, 4)]


def test_subrange_covers_only_sublist():
    """Intervals must be within [a, b] and partition it completely."""
    X = ["foo", "bar baz"]
    intervals = dp_align_nodes(X, Y, exact_sim, a=2, b=5)
    assert intervals[0][0] == 2          # starts at a
    assert intervals[-1][1] == 5         # ends at b
    assert intervals == [(2, 3), (3, 5)]


def test_contiguous_no_gaps():
    """All returned intervals are contiguous (end of one == start of next)."""
    X = ["hello", "world foo", "bar baz"]
    intervals = dp_align_nodes(X, Y, exact_sim)
    for i in range(len(intervals) - 1):
        assert intervals[i][1] == intervals[i + 1][0]


def test_single_element():
    """Single X element gets the full subrange."""
    intervals = dp_align_nodes(["foo bar"], Y, exact_sim, a=2, b=4)
    assert intervals == [(2, 4)]


def test_subrange_matches_full_run():
    """Result with explicit a=0, b=len(Y) matches default."""
    X = ["hello world", "foo", "bar baz"]
    default = dp_align_nodes(X, Y, exact_sim)
    explicit = dp_align_nodes(X, Y, exact_sim, a=0, b=len(Y))
    assert default == explicit
