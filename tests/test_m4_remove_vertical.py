"""Sample tests for Milestone 4: remove_vertical_seam.

    pytest -m m4

Every seam here is written out by hand, so these tests do not need
find_vertical_seam to work.
"""

import pytest

from testkit import (SeamCarver, seam_error, rows_of, assert_picture,
                     remove_column_seam)


pytestmark = pytest.mark.m4


@pytest.mark.weight(2)
def test_remove_the_seam_of_the_6x5_example():
    picture = SeamCarver("6x5.png")
    rows = rows_of(picture)
    picture.remove_vertical_seam([3, 4, 3, 2, 2])
    assert_picture(picture, remove_column_seam(rows, [3, 4, 3, 2, 2]))


def test_remove_two_seams_in_a_row():
    picture = SeamCarver("6x5.png")
    rows = rows_of(picture)
    for seam in ([3, 4, 3, 2, 2], [2, 3, 2, 1, 1]):
        picture.remove_vertical_seam(list(seam))
        rows = remove_column_seam(rows, seam)
    assert_picture(picture, rows)


@pytest.mark.parametrize("seam", [[0, 0, 0, 0, 0], [5, 5, 5, 5, 5], [0, 1, 2, 3, 4], [5, 4, 5, 4, 5]])
def test_remove_a_seam_that_touches_the_edges(seam):
    """The leftmost and rightmost columns can be part of a seam too."""
    picture = SeamCarver("6x5.png")
    rows = rows_of(picture)
    picture.remove_vertical_seam(list(seam))
    assert_picture(picture, remove_column_seam(rows, seam))


def test_remove_seams_until_one_column_is_left():
    picture = SeamCarver("3x4.png")
    rows = rows_of(picture)
    for seam in ([1, 2, 1, 0], [0, 0, 1, 1]):
        picture.remove_vertical_seam(list(seam))
        rows = remove_column_seam(rows, seam)
        assert_picture(picture, rows)
    assert (picture.width(), picture.height()) == (1, 4)


def test_reject_a_seam_when_one_column_is_left():
    picture = SeamCarver("3x4.png")
    picture.remove_vertical_seam([0, 0, 0, 0])
    picture.remove_vertical_seam([0, 0, 0, 0])
    with pytest.raises(seam_error()):
        picture.remove_vertical_seam([0, 0, 0, 0])


@pytest.mark.parametrize("seam", [[1, 2, 3, 2], [1, 2, 3, 2, 2, 2], []])
def test_reject_a_seam_of_the_wrong_length(seam):
    picture = SeamCarver("6x5.png")
    with pytest.raises(seam_error()):
        picture.remove_vertical_seam(list(seam))


def test_reject_a_seam_that_is_not_connected():
    picture = SeamCarver("6x5.png")
    with pytest.raises(seam_error()):
        picture.remove_vertical_seam([2, 2, 3, 4, 1])


def test_reject_a_seam_that_leaves_the_picture():
    picture = SeamCarver("6x5.png")
    with pytest.raises(seam_error()):
        picture.remove_vertical_seam([5, 5, 6, 5, 5])
