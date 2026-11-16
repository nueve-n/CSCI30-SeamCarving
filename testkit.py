"""Helpers shared by the seam carver tests.  DO NOT MODIFY THIS FILE.

The tests never import your code directly.  They ask this module for it, so
that the same tests can be pointed at any copy of seamcarver.py:

    SEAMCARVER_IMPL=path/to/seamcarver.py pytest

Without that variable the tests use the seamcarver.py next to this file.
"""

import importlib.util
import os
import pathlib
import sys

import pytest
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / "data"

if str(ROOT) not in sys.path:          # so that `from picture import Picture` works
    sys.path.insert(0, str(ROOT))

_modules = {}


def _load(path, name):
    path = pathlib.Path(path).resolve()
    key = (name, str(path))
    if key not in _modules:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            del sys.modules[name]
            raise
        _modules[key] = module
    return _modules[key]


def impl():
    """The module under test: your seamcarver.py."""
    return _load(os.environ.get("SEAMCARVER_IMPL") or ROOT / "seamcarver.py",
                 "seamcarver")


def reference():
    """The instructor's solution, if this run has access to it (yours won't)."""
    path = os.environ.get("SEAMCARVER_REF")
    return _load(path, "seamcarver_reference") if path else None


def SeamCarver(image):
    """Build a SeamCarver, from a file in data/ or from a PIL image."""
    if isinstance(image, str):
        image = Image.open(DATA / image)
    return impl().SeamCarver(image)


def seam_error():
    """The SeamError class defined in seamcarver.py."""
    cls = getattr(impl(), "SeamError", None)
    if not (isinstance(cls, type) and issubclass(cls, Exception)):
        pytest.fail("seamcarver.py must define SeamError (a subclass of Exception) "
                    "at the top level of the module, outside SeamCarver")
    return cls


# ---------------------------------------------------------------------------
# Building pictures
# ---------------------------------------------------------------------------

def image_from_rows(rows):
    """A PIL image whose pixel (i, j) is rows[j][i]."""
    height, width = len(rows), len(rows[0])
    image = Image.new("RGB", (width, height))
    image.putdata([tuple(pixel) for row in rows for pixel in row])
    return image


def rows_of(picture):
    """The pixels of a picture as a list of rows, read through picture[i, j]."""
    return [[picture[i, j] for i in range(picture.width())]
            for j in range(picture.height())]


def random_rows(width, height, seed, levels=256):
    """Deterministic pseudo-random pixels; small `levels` gives lots of ties.

    Uses its own generator rather than the random module, so the pictures are
    the same on every Python version.
    """
    state = seed * 2654435761 % 2**32 or 1
    step = 255 // max(levels - 1, 1)
    rows = []
    for _ in range(height):
        row = []
        for _ in range(width):
            pixel = []
            for _ in range(3):
                state = (1103515245 * state + 12345) % 2**31
                pixel.append((state >> 16) % levels * step)
            row.append(tuple(pixel))
        rows.append(row)
    return rows


def transpose_rows(rows):
    return [list(column) for column in zip(*rows)]


# ---------------------------------------------------------------------------
# Checking pictures and seams
# ---------------------------------------------------------------------------

def snapshot(picture):
    """Everything about a picture that a test might want to compare later."""
    return picture.width(), picture.height(), dict(picture)


def assert_unchanged(picture, before, what):
    width, height, pixels = before
    assert (picture.width(), picture.height()) == (width, height), \
        f"{what} changed the picture's size from {width}x{height} " \
        f"to {picture.width()}x{picture.height()}"
    assert dict(picture) == pixels, f"{what} changed the picture's pixels"


def assert_picture(picture, rows, what="the picture"):
    """`picture` holds exactly the pixels in `rows`: no more, no fewer."""
    height, width = len(rows), len(rows[0])
    assert (picture.width(), picture.height()) == (width, height), \
        f"{what} is {picture.width()}x{picture.height()}, expected {width}x{height}"
    expected_keys = {(i, j) for j in range(height) for i in range(width)}
    actual_keys = set(picture.keys())
    extra = sorted(actual_keys - expected_keys)
    missing = sorted(expected_keys - actual_keys)
    assert not extra, f"{what} still holds pixels outside its {width}x{height} area, e.g. {extra[:3]}"
    assert not missing, f"{what} is missing pixels, e.g. {missing[:3]}"
    for j in range(height):
        for i in range(width):
            assert picture[i, j] == tuple(rows[j][i]), \
                f"pixel ({i}, {j}) of {what} is {picture[i, j]}, expected {tuple(rows[j][i])}"


def assert_valid_seam(seam, length, bound, kind):
    """A seam of the right length, in range, and connected."""
    assert seam is not None, f"find_{kind}_seam returned None"
    seam = list(seam)
    assert len(seam) == length, f"{kind} seam has length {len(seam)}, expected {length}"
    for k, x in enumerate(seam):
        assert isinstance(x, int) and not isinstance(x, bool), \
            f"{kind} seam entry {k} is {x!r}, not an int"
        assert 0 <= x < bound, f"{kind} seam entry {k} is {x}, outside 0..{bound - 1}"
    for k in range(1, length):
        assert abs(seam[k] - seam[k - 1]) <= 1, \
            f"{kind} seam is not connected: entries {k - 1} and {k} are {seam[k - 1]} and {seam[k]}"
    return seam


def vertical_cost(picture, seam):
    return sum(picture.energy(i, j) for j, i in enumerate(seam))


def horizontal_cost(picture, seam):
    return sum(picture.energy(i, j) for i, j in enumerate(seam))


def check_vertical(picture, expected_cost):
    """Find a vertical seam, check that it is valid and optimal, return it."""
    width, height = picture.width(), picture.height()
    seam = assert_valid_seam(picture.find_vertical_seam(), height, width, "vertical")
    cost = vertical_cost(picture, seam)
    assert cost == pytest.approx(expected_cost, rel=1e-9, abs=1e-6), \
        f"vertical seam has total energy {cost}, but the minimum is {expected_cost}"
    return seam


def check_horizontal(picture, expected_cost):
    """Find a horizontal seam, check that it is valid and optimal, return it."""
    width, height = picture.width(), picture.height()
    seam = assert_valid_seam(picture.find_horizontal_seam(), width, height, "horizontal")
    cost = horizontal_cost(picture, seam)
    assert cost == pytest.approx(expected_cost, rel=1e-9, abs=1e-6), \
        f"horizontal seam has total energy {cost}, but the minimum is {expected_cost}"
    return seam


def remove_column_seam(rows, seam):
    """What removing vertical seam `seam` from `rows` should leave behind."""
    return [row[:i] + row[i + 1:] for row, i in zip(rows, seam)]


def remove_row_seam(rows, seam):
    """What removing horizontal seam `seam` from `rows` should leave behind."""
    return transpose_rows(remove_column_seam(transpose_rows(rows), seam))
