import inspect

import numpy as np
import pandas as pd
import pandas._testing as tm
import pytest

from pandas.core.window.online import generate_online_numba_ewma_func


@pytest.mark.parametrize("adjust", [True, False])
@pytest.mark.parametrize("ignore_na", [True, False])
def test_online_single_column_matches_batch(adjust, ignore_na):
    df = pd.DataFrame({"A": [1.0, np.nan, 3.0, 4.0, 5.0]})
    expected = df.ewm(com=1, adjust=adjust, ignore_na=ignore_na).mean()

    online = (
        df.iloc[:3]
        .ewm(com=1, adjust=adjust, ignore_na=ignore_na)
        .online(engine_kwargs={"nogil": False, "parallel": False})
    )
    initial = online.mean()
    update = online.mean(update=df.iloc[3:])

    tm.assert_frame_equal(initial, expected.iloc[:3])
    tm.assert_frame_equal(update, expected.iloc[3:])


def test_online_ewma_uses_delta_for_each_row_not_each_column():
    kwargs = {"nogil": False, "parallel": False}
    if "nopython" in inspect.signature(generate_online_numba_ewma_func).parameters:
        kwargs["nopython"] = True
    ewm_func = generate_online_numba_ewma_func(**kwargs)

    values = np.array([[1.0, 10.0], [3.0, 30.0], [5.0, 50.0]])
    deltas = np.array([1.0, 2.0])
    result, old_wt = ewm_func(
        values,
        deltas,
        1,
        0.5,
        1.0,
        np.ones(2),
        True,
        False,
    )

    expected = np.array(
        [
            [1.0, 10.0],
            [7.0 / 3.0, 70.0 / 3.0],
            [47.0 / 11.0, 470.0 / 11.0],
        ]
    )
    np.testing.assert_allclose(result, expected, rtol=1e-12, atol=0)
    np.testing.assert_allclose(old_wt, np.array([1.375, 1.375]), rtol=1e-12, atol=0)
