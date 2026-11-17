"""Ground temperature must be aligned to the simulation window by date.

Before: the ground CSV column was written row-by-row onto the Modelica time
axis (t=0, dt, 2dt, ...), ignoring both the simulation start date and the
resolution of the ground data (hourly rows consumed at 15-min pace).
"""

import pandas as pd
import pytest

from uesgraphs.systemmodels.model_generation_pipeline import (
    align_ground_temp_to_simulation,
)


def _hourly(start, end, func):
    idx = pd.date_range(start, end, freq="1h")
    return pd.DataFrame({"1.0 m": [func(t) for t in idx]}, index=idx)


def test_dated_file_is_cut_by_date_and_resampled():
    # value = hours since 2025-11-01 -> linear, so interpolation is exact
    t0 = pd.Timestamp("2025-11-01")
    df = _hourly("2025-11-01", "2026-02-01", lambda t: (t - t0) / pd.Timedelta("1h"))
    start = pd.Timestamp("2025-11-17 00:00")

    vals = align_ground_temp_to_simulation(
        df, depth="1.0 m", start=start, stop_time=2 * 3600, timestep=900
    )

    expected_first = (start - t0) / pd.Timedelta("1h")
    assert len(vals) == 9  # stop/timestep + 1, like SystemModelHeating.time
    assert vals[0] == pytest.approx(expected_first)
    assert vals[1] == pytest.approx(expected_first + 0.25)  # 15 min, not 1 h
    assert vals[-1] == pytest.approx(expected_first + 2.0)


def test_single_year_file_is_projected_across_year_boundary():
    # typical-year file (like ground_temps_hassel.csv: 2020, ends 12-30 23:00)
    df = _hourly("2020-01-01", "2020-12-30 23:00", lambda t: float(t.dayofyear))
    start = pd.Timestamp("2025-12-29 00:00")

    vals = align_ground_temp_to_simulation(
        df, depth="1.0 m", start=start, stop_time=5 * 86400, timestep=3600
    )

    s = pd.Series(vals, index=pd.date_range(start, periods=len(vals), freq="1h"))
    assert s["2025-12-29 00:00"] == pytest.approx(364.0)   # from 2020-12-29 = doy 364
    assert s["2026-01-02 12:00"] == pytest.approx(2.0)     # wrapped to January
    assert not s.isna().any()


def test_multi_year_file_not_covering_window_raises():
    df = _hourly("2020-01-01", "2021-06-30", lambda t: 280.0)
    with pytest.raises(ValueError, match="ground temperature"):
        align_ground_temp_to_simulation(
            df, depth="1.0 m", start=pd.Timestamp("2025-11-17"),
            stop_time=86400, timestep=900,
        )


def test_missing_depth_raises():
    df = _hourly("2025-11-01", "2025-12-01", lambda t: 280.0)
    with pytest.raises(KeyError, match="2.0 m"):
        align_ground_temp_to_simulation(
            df, depth="2.0 m", start=pd.Timestamp("2025-11-17"),
            stop_time=86400, timestep=900,
        )
