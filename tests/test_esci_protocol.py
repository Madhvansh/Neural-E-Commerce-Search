"""Regression tests for explicit ESCI task selection."""

import pytest

from necs.data.esci import version_column_for_task


def test_task1_uses_small_version_flag():
    assert version_column_for_task("task1_ranking") == "small_version"


def test_task2_uses_large_version_flag():
    assert version_column_for_task("task2_classification") == "large_version"


def test_unknown_task_is_rejected():
    with pytest.raises(ValueError, match="Unknown ESCI task"):
        version_column_for_task("task2_but_unfiltered")
