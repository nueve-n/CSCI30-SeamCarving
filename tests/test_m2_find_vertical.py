"""Sample tests for Milestone 2: find_vertical_seam.

    pytest -m m2

These tests check a seam by adding up the energies of its pixels with *your*
energy method, so Milestone 1 has to work before they can pass on your
machine.  (When we grade, they are insulated from Milestone 1: see the
handout.)
"""

import pytest

from testkit import (SeamCarver, image_from_rows, snapshot, assert_unchanged,
                     assert_valid_seam, check_vertical)

pytestmark = [pytest.mark.m2, pytest.mark.uses("energy")]

# Minimum total energy of a vertical seam in some of the pictures in data/.
OPTIMAL = {
    "HJoceanSmall.jpg": 1719.4661790399298,     # 507x285
    "balloons_small.jpg": 646.7181655667498,    # 320x209
    "people2.jpg": 1986.4636832568715,          # 446x295
}


def test_vertical_seam_of_the_6x5_example():
    """The example in the handout; its minimum-energy seam is unique."""
    picture = SeamCarver("6x5.png")
    assert list(picture.find_vertical_seam()) == [3, 4, 3, 2, 2]


def test_vertical_seam_of_the_3x4_example():
    picture = SeamCarver("3x4.png")
    assert list(picture.find_vertical_seam()) == [0, 0, 0, 0]


@pytest.mark.weight(6)
@pytest.mark.parametrize("name", sorted(OPTIMAL))
def test_vertical_seam_is_valid_and_optimal(name):
    check_vertical(SeamCarver(name), OPTIMAL[name])


def test_vertical_seam_through_a_flat_region():
    """Large areas of zero energy, so many seams tie; any of them will do,
    as long as it is a seam: one pixel per row, each next to the one above."""
    picture = SeamCarver("circles_small.png")
    check_vertical(picture, 0.0)


def test_vertical_seam_of_a_picture_one_pixel_wide():
    rows = [[(j * 40 % 256, 0, 0)] for j in range(5)]
    picture = SeamCarver(image_from_rows(rows))
    assert list(picture.find_vertical_seam()) == [0, 0, 0, 0, 0]


def test_vertical_seam_of_a_picture_one_pixel_tall():
    """With one row, the seam is the single lowest-energy pixel."""
    reds = [200, 90, 10, 30, 45, 60, 250]       # energies 160 190 60 35 30 205 140
    rows = [[(red, 0, 0) for red in reds]]
    picture = SeamCarver(image_from_rows(rows))
    assert list(picture.find_vertical_seam()) == [4]


def test_find_vertical_seam_does_not_change_the_picture():
    picture = SeamCarver("6x5.png")
    before = snapshot(picture)
    picture.find_vertical_seam()
    assert_unchanged(picture, before, "find_vertical_seam")


@pytest.mark.weight(6)
@pytest.mark.time_limit(20)
def test_vertical_seam_of_a_big_picture():
    """1052x709 pixels: needs the dynamic programming solution, not a search."""
    check_vertical(SeamCarver("binarytree.jpg"), 5451.1156473404235)
