import sys
import os
import pytest
import polars as pl

# Ensure downloadstats src is on sys.path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../src')
))

from downloadstats.tool import scale_bitflux_data, summarize_bitflux_data

def test_scale_no_length():
    # stats length zero should return the original DataFrame unchanged
    df = pl.DataFrame({
        'value': [1, 2, 3],
        'idle_cpu': [5, 6, 7],
        'reclaimable': [0, 1, 2]
    })
    stats = {'length': 0}
    result = scale_bitflux_data(stats, df)
    # Compare row-wise dictionaries
    assert result.to_dicts() == df.to_dicts()

def test_scale_contiguous_drop_first():
    # contiguous buffer (tail <= head), with drop of first row when reclaimable == 0
    df = pl.DataFrame({
        'value': [10, 20, 30, 40, 50],
        'idle_cpu': [1, 2, 3, 4, 5],
        'reclaimable': [0, 0, 5, 6, 7]
    })
    stats = {'head': 3, 'tail': 1, 'length': 3, 'unitsize': 2}
    # Slice indices 1-3: rows 1,2,3 then scale; drop first because reclaimable*unitsize == 0
    result = scale_bitflux_data(stats, df)
    expected = pl.DataFrame({
        'value': [60, 80],
        'idle_cpu': [3, 4],
        'reclaimable': [10, 12]
    })
    # Compare row-wise dictionaries
    assert result.to_dicts() == expected.to_dicts()

def test_scale_wrap_around_no_drop():
    # wrap-around buffer (tail > head), no drop since reclaimable > 0
    df = pl.DataFrame({
        'value': [10, 20, 30, 40, 50],
        'idle_cpu': [1, 2, 3, 4, 5],
        'reclaimable': [5, 6, 7, 8, 9]
    })
    stats = {'head': 1, 'tail': 3, 'length': 4, 'unitsize': 1}
    # Slice tail->end rows 3,4 and start->head rows 0,1; no scaling change
    result = scale_bitflux_data(stats, df)
    expected = pl.DataFrame({
        'value': [40, 50, 10, 20],
        'idle_cpu': [4, 5, 1, 2],
        'reclaimable': [8, 9, 5, 6]
    })
    # Compare row-wise dictionaries
    assert result.to_dicts() == expected.to_dicts()

def test_summarize_empty():
    # empty DataFrame should return error dict
    df = pl.DataFrame({'x': []})
    result = summarize_bitflux_data(df)
    assert result == {"error": "No data available for summary"}

def test_summarize_basic():
    # basic summary statistics on single column
    df = pl.DataFrame({'x': [1, 2, 3]})
    result = summarize_bitflux_data(df)
    assert 'x' in result
    stats = result['x']
    # Check key statistics
    assert stats['min'] == 1
    assert stats['max'] == 3
    assert pytest.approx(stats['mean'], rel=1e-6) == 2.0
    assert pytest.approx(stats['sum'], rel=1e-6) == 6.0
    assert pytest.approx(stats['median'], rel=1e-6) == 2.0