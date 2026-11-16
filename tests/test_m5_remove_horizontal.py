"""Sample tests for Milestone 5: remove_horizontal_seam.

    pytest -m m5

If your remove_horizontal_seam uses remove_vertical_seam, as the handout
suggests, Milestone 4 has to work before these can pass on your machine.
(When we grade, they are insulated from it: see the handout.)
"""

import pytest

from testkit import (SeamCarver, seam_error, rows_of, assert_picture,
                     remove_row_seam)

pytestmark = [pytest.mark.m5, pytest.mark.uses("remove_vertical_seam")]


@pytest.mark.weight(2)
def test_remove_the_seam_of_the_6x5_example():
    picture = SeamCarver("6x5.png")
    rows = rows_of(picture)
    picture.remove_horizontal_seam([2, 2, 1, 2, 1, 2])
    assert_picture(picture, remove_row_seam(rows, [2, 2, 1, 2, 1, 2]))


def test_remove_two_seams_in_a_row():
    picture = SeamCarver("6x5.png")
    rows = rows_of(picture)
    for seam in ([2, 2, 1, 2, 1, 2], [1, 1, 1, 0, 0, 1]):
        picture.remove_horizontal_seam(list(seam))
        rows = remove_row_seam(rows, seam)
    assert_picture(picture, rows)


@pytest.mark.parametrize("seam", [[0] * 6, [4] * 6, [0, 1, 2, 3, 4, 4], [4, 3, 4, 3, 4, 3]])
def test_remove_a_seam_that_touches_the_edges(seam):
    """The top and bottom rows can be part of a seam too."""
    picture = SeamCarver("6x5.png")
    rows = rows_of(picture)
    picture.remove_horizontal_seam(list(seam))
    assert_picture(picture, remove_row_seam(rows, seam))


def test_remove_seams_until_one_row_is_left():
    picture = SeamCarver("3x4.png")
    rows = rows_of(picture)
    for seam in ([1, 2, 3], [0, 0, 1], [1, 0, 0]):
        picture.remove_horizontal_seam(list(seam))
        rows = remove_row_seam(rows, seam)
        assert_picture(picture, rows)
    assert (picture.width(), picture.height()) == (3, 1)


def test_reject_a_seam_when_one_row_is_left():
    picture = SeamCarver("3x4.png")
    for _ in range(3):
        picture.remove_horizontal_seam([0, 0, 0])
    with pytest.raises(seam_error()):
        picture.remove_horizontal_seam([0, 0, 0])


@pytest.mark.parametrize("seam", [[1, 2, 3, 2], [1, 2, 3, 2, 2, 2, 2], []])
def test_reject_a_seam_of_the_wrong_length(seam):
    picture = SeamCarver("6x5.png")
    with pytest.raises(seam_error()):
        picture.remove_horizontal_seam(list(seam))


def test_reject_a_seam_that_is_not_connected():
    picture = SeamCarver("6x5.png")
    with pytest.raises(seam_error()):
        picture.remove_horizontal_seam([2, 3, 2, 4, 3, 1])


def test_reject_a_seam_that_leaves_the_picture():
    picture = SeamCarver("6x5.png")
    with pytest.raises(seam_error()):
        picture.remove_horizontal_seam([4, 4, 5, 4, 4, 4])
