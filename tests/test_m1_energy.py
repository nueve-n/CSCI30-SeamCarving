"""Sample tests for Milestone 1: energy.

    pytest -m m1
"""

from math import sqrt

import pytest

from testkit import SeamCarver, image_from_rows, snapshot, assert_unchanged

pytestmark = pytest.mark.m1

# The dual-gradient energies of data/3x4.png, squared, as in the handout:
# ENERGY_3X4[j][i] is e(i, j) ** 2.
ENERGY_3X4 = [
    [20808, 52020, 20808],
    [20808, 52225, 21220],
    [20809, 52024, 20809],
    [20808, 52225, 21220],
]

ENERGY_6X5 = [
    [57685, 50893, 91370, 25418, 33055, 37246],
    [15421, 56334, 22808, 54796, 11641, 25496],
    [12344, 19236, 52030, 17708, 44735, 20663],
    [17074, 23678, 30279, 80663, 37831, 45595],
    [32337, 30796, 4909, 73334, 40613, 36556],
]


def test_energy_of_a_non_border_pixel():
    """Example 1 of the handout: pixel (1, 2) of the 3x4 picture."""
    picture = SeamCarver("3x4.png")
    assert picture.energy(1, 2) == pytest.approx(sqrt(52024))


def test_energy_of_a_border_pixel():
    """Example 2 of the handout: pixel (1, 0) wraps around to the bottom row."""
    picture = SeamCarver("3x4.png")
    assert picture.energy(1, 0) == pytest.approx(sqrt(52020))


@pytest.mark.weight(2)
@pytest.mark.parametrize("name, table", [("3x4.png", ENERGY_3X4), ("6x5.png", ENERGY_6X5)])
def test_energy_of_every_pixel(name, table):
    """Every pixel, including all four corners, which wrap in both directions."""
    picture = SeamCarver(name)
    for j, row in enumerate(table):
        for i, squared in enumerate(row):
            assert picture.energy(i, j) == pytest.approx(sqrt(squared)), \
                f"energy({i}, {j}) of {name}"


@pytest.mark.parametrize("i, j", [(-1, 0), (0, -1), (6, 0), (0, 5), (6, 5), (10, 10)])
def test_energy_rejects_pixels_outside_the_picture(i, j):
    """energy raises IndexError -- Python's own -- for any pixel outside 6x5."""
    picture = SeamCarver("6x5.png")
    with pytest.raises(IndexError):
        picture.energy(i, j)


def test_energy_in_a_picture_one_pixel_wide():
    """With W = 1 a pixel is its own left and right neighbor, so the x-gradient is 0."""
    picture = SeamCarver(image_from_rows([[(10, 20, 30)], [(40, 60, 80)], [(10, 20, 35)]]))
    assert picture.energy(0, 1) == pytest.approx(sqrt(0 + 0 + 25))
    assert picture.energy(0, 0) == pytest.approx(sqrt(30**2 + 40**2 + 45**2))


def test_energy_does_not_change_the_picture():
    picture = SeamCarver("6x5.png")
    before = snapshot(picture)
    for j in range(5):
        for i in range(6):
            picture.energy(i, j)
    assert_unchanged(picture, before, "energy")


@pytest.mark.time_limit(10)
def test_energy_takes_constant_time():
    """20000 calls on a 1428x968 picture: fast only if each call is O(1)."""
    picture = SeamCarver("tower.jpg")
    total = 0.0
    for k in range(20000):
        total += picture.energy(k * 7919 % 1428, k * 104729 % 968)
    assert total > 0
