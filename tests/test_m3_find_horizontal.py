"""Sample tests for Milestone 3: find_horizontal_seam.

    pytest -m m3

As in Milestone 2, a seam is checked by adding up its energies with your
energy method.  And if your find_horizontal_seam uses find_vertical_seam, as
the handout suggests, Milestone 2 has to work too.  (When we grade, these
tests are insulated from both: see the handout.)
"""

import pytest

from testkit import (SeamCarver, image_from_rows, snapshot, assert_unchanged,
                     check_horizontal)

pytestmark = [pytest.mark.m3, pytest.mark.uses("energy", "find_vertical_seam")]

# Minimum total energy of a horizontal seam in some of the pictures in data/.
OPTIMAL = {
    "HJoceanSmall.jpg": 885.2947085620644,      # 507x285
    "balloons_small.jpg": 626.7838054983109,    # 320x209
    "people2.jpg": 1053.5654479987081,          # 446x295
}


def test_horizontal_seam_of_the_6x5_example():
    """The example in the handout; its minimum-energy seam is unique."""
    picture = SeamCarver("6x5.png")
    assert list(picture.find_horizontal_seam()) == [2, 2, 1, 2, 1, 2]


def test_horizontal_seam_of_the_3x4_example():
    """Two seams tie here; either is fine."""
    check_horizontal(SeamCarver("3x4.png"), 516.5785004290899)


@pytest.mark.weight(6)
@pytest.mark.parametrize("name", sorted(OPTIMAL))
def test_horizontal_seam_is_valid_and_optimal(name):
    check_horizontal(SeamCarver(name), OPTIMAL[name])


def test_horizontal_seam_through_a_flat_region():
    check_horizontal(SeamCarver("circles_small.png"), 0.0)


def test_horizontal_seam_of_a_picture_one_pixel_tall():
    rows = [[(i * 40 % 256, 0, 0) for i in range(5)]]
    picture = SeamCarver(image_from_rows(rows))
    assert list(picture.find_horizontal_seam()) == [0, 0, 0, 0, 0]


def test_horizontal_seam_of_a_picture_one_pixel_wide():
    """With one column, the seam is the single lowest-energy pixel."""
    reds = [200, 90, 10, 30, 45, 60, 250]       # energies 160 190 60 35 30 205 140
    rows = [[(red, 0, 0)] for red in reds]
    picture = SeamCarver(image_from_rows(rows))
    assert list(picture.find_horizontal_seam()) == [4]


@pytest.mark.weight(2)
def test_find_horizontal_seam_does_not_change_the_picture():
    """In particular, a picture transposed to find the seam is transposed back,
    size and all -- this one is not square."""
    picture = SeamCarver("6x5.png")
    before = snapshot(picture)
    picture.find_horizontal_seam()
    assert_unchanged(picture, before, "find_horizontal_seam")


@pytest.mark.weight(6)
@pytest.mark.time_limit(20)
def test_horizontal_seam_of_a_big_picture():
    """1052x709 pixels."""
    check_horizontal(SeamCarver("binarytree.jpg"), 2800.1315680023317)
