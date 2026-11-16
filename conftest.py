"""pytest configuration for the seam carver tests.  DO NOT MODIFY THIS FILE.

Two things happen here.

Time limits
-----------
Every test runs under a time limit: 10 seconds unless the test says otherwise
with @pytest.mark.time_limit(seconds).  A test that runs past its limit fails
with TimeLimitExceeded, and the remaining tests carry on.  This works the same
way on Windows, macOS, and Linux.

If your machine is much slower than the one we grade on, you can stretch every
limit by a factor to check whether a failure is only about speed:

    SEAMCARVER_TIME_SCALE=2 pytest        (Linux/macOS)
    set SEAMCARVER_TIME_SCALE=2           (Windows, then run pytest)

Grading always uses a factor of 1.

Milestones are graded independently
-----------------------------------
A test marked @pytest.mark.uses("energy", ...) also calls methods that belong
to other milestones.  When we grade, such a test that fails is run a second
time with those methods replaced by our own, and it counts as passed if that
second run passes.  So a bug costs you points in the milestone where it lives,
not again in every milestone that happens to call it.  On your machine there
is no second run: you see exactly what your own code does.
"""

import ctypes
import os
import threading

import pytest

from testkit import impl, reference

DEFAULT_TIME_LIMIT = 10.0
TIME_SCALE = float(os.environ.get("SEAMCARVER_TIME_SCALE") or 1.0)

# Tests run in a worker thread (that is how the time limit is enforced), and
# worker threads get a small stack by default on some platforms.  Give them
# as much as a main thread would have, and then some.
threading.stack_size(64 * 1024 * 1024)


class TimeLimitExceeded(BaseException):
    """Raised inside a test that has run past its time limit.

    A BaseException, like KeyboardInterrupt, so that `except Exception:` in the
    code under test does not swallow it.
    """


def _raise_in_thread(thread, exc_type):
    return ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_ulong(thread.ident), ctypes.py_object(exc_type))


def _call_with_time_limit(function, seconds):
    outcome = {}

    def target():
        try:
            function()
        except BaseException as exc:          # re-raised in the main thread
            outcome["error"] = exc

    worker = threading.Thread(target=target, name="seamcarver-test", daemon=True)
    try:
        worker.start()
    except RuntimeError:
        # No thread to be had (the process is out of memory, say): run the
        # test right here instead, just without a time limit.
        function()
        return
    worker.join(seconds)
    if worker.is_alive():
        # Interrupt the test where it stands.  This takes effect at the next
        # Python bytecode it executes, so keep asking until it lets go; a test
        # stuck inside a single C call cannot be interrupted, so give up on it
        # after a while and leave it running in the background.
        for _ in range(50):
            _raise_in_thread(worker, TimeLimitExceeded)
            worker.join(0.1)
            if not worker.is_alive():
                break
        raise TimeLimitExceeded(
            f"test did not finish within its time limit of {seconds:g}s "
            "(too slow, or an infinite loop)")
    if "error" in outcome:
        raise outcome["error"]


def _time_limit(item):
    marker = item.get_closest_marker("time_limit")
    seconds = marker.args[0] if marker else DEFAULT_TIME_LIMIT
    return seconds * TIME_SCALE


def _is_skip(exc):
    return isinstance(exc, (pytest.skip.Exception, pytest.xfail.Exception))


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem):
    function = pyfuncitem.obj
    kwargs = {name: pyfuncitem.funcargs[name]
              for name in pyfuncitem._fixtureinfo.argnames}
    seconds = _time_limit(pyfuncitem)

    def run():
        _call_with_time_limit(lambda: function(**kwargs), seconds)

    try:
        run()
        return True
    except BaseException as first:
        if _is_skip(first) or isinstance(first, KeyboardInterrupt):
            raise
        uses = _uses(pyfuncitem)
        ref = reference()
        if not uses or ref is None:
            raise

        with pytest.MonkeyPatch.context() as patch:
            _substitute(patch, ref, uses)
            try:
                run()
            except BaseException as second:
                if _is_skip(second) or isinstance(second, KeyboardInterrupt):
                    raise
                if hasattr(first, "add_note"):
                    first.add_note(f"(also fails with the reference {', '.join(uses)})")
                raise first from None

        pyfuncitem.user_properties.append(("substituted", list(uses)))
        return True


def _uses(item):
    names = []
    for marker in item.iter_markers("uses"):
        names.extend(marker.args)
    return names


def _substitute(patch, ref, names):
    """Swap the named methods of the student's SeamCarver for the reference's."""
    student = impl()
    for name in names:
        patch.setattr(student.SeamCarver, name, ref.SeamCarver.__dict__[name])
    # A reference method that raises SeamError must raise the student's
    # SeamError, or a test expecting the student's exception would not see it.
    if isinstance(getattr(student, "SeamError", None), type):
        patch.setattr(ref, "SeamError", student.SeamError)


def pytest_report_header(config):
    lines = []
    if TIME_SCALE != 1.0:
        lines.append(f"seamcarver: time limits scaled by {TIME_SCALE:g}")
    if os.environ.get("SEAMCARVER_IMPL"):
        lines.append(f"seamcarver: testing {os.environ['SEAMCARVER_IMPL']}")
    if os.environ.get("SEAMCARVER_REF"):
        lines.append("seamcarver: milestones graded independently (reference available)")
    return lines


def pytest_terminal_summary(terminalreporter):
    rescued = [report for report in terminalreporter.stats.get("passed", [])
               if any(key == "substituted" for key, _ in report.user_properties)]
    if rescued:
        terminalreporter.section("passed only with reference substitutes")
        for report in rescued:
            names = next(value for key, value in report.user_properties if key == "substituted")
            terminalreporter.line(f"{report.nodeid}  [{', '.join(names)}]")
