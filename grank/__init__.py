from typing import Optional, Union

import numpy as np
import numpy.typing as npt


def grank(
    a: npt.ArrayLike,
    g: Optional[npt.ArrayLike] = None,
    method: str = "average",
    axis: Optional[int] = None,
) -> Union[npt.NDArray[np.int_], npt.NDArray[np.float64]]:
    """Assign ranks independently within groups.

    When `g` is not None, the rankings are assigned independently within groups. When
    `g` is None, the behaviour is the same as scipy.stats.rankdata.

    """
    a = np.asarray(a)
    if axis is not None:
        if a.size == 0:
            dt = np.float64 if method == "average" else np.int_
            return np.empty(a.shape, dtype=dt)
        return np.apply_along_axis(grank, axis, a, g, method)

    if g is None:
        g = np.zeros_like(a)
    g = np.asarray(g)
    assert a.shape == g.shape, "`a` and `g` must be the same shape."

    try:
        nan_indexes = np.isnan(a)
    except Exception:
        nan_indexes = None

    # These helper indexes are inspired by numpy-indexed.
    sorter = np.lexsort((a, g))
    sorted_a = a[sorter]
    sorted_g = g[sorter]
    flag = sorted_g[:-1] != sorted_g[1:]
    slices = np.r_[0, np.flatnonzero(flag) + 1, len(a)]
    start = slices[:-1]

    # Convert sorted group id into the original rank
    g2inv = np.empty(sorter.size, int)
    g2inv[sorter] = np.cumsum(np.r_[False, flag])

    offset = start

    if method == "ordinal":
        rank = np.empty(len(a), int)
        rank[sorter] = np.arange(len(a))
        rank -= offset[g2inv]
        result = rank + 1
    else:
        # Convert sorted data into the original rank
        x2inv = np.empty(sorter.size, int)
        x2inv[sorter] = np.arange(sorter.size, dtype=np.intp)

        obs = np.r_[True, sorted_a[1:] != sorted_a[:-1]]
        obs[start] = True
        dense = obs.cumsum()
        if method == "dense":
            # the offset needs to count g unique values
            dense_offset = dense[start]
            result = dense[x2inv] - dense_offset[g2inv] + 1
        else:
            count = np.r_[np.flatnonzero(obs), len(obs)]
            if method == "max" or method == "average":
                max_rank = count[dense][x2inv] - offset[g2inv]

            if method == "min" or method == "average":
                min_rank = count[dense - 1][x2inv] - offset[g2inv] + 1

            if method == "average":
                avg_rank = 0.5 * (max_rank + min_rank)

            if method == "max":
                result = max_rank
            elif method == "min":
                result = min_rank
            elif method == "average":
                result = avg_rank

    if nan_indexes is not None:
        result = result.astype("float64")
        result[nan_indexes] = np.nan
    return result
