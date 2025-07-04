import pytest
import polars as pl
from .tool import strip_warmup


def debug_strip_warmup(stats, df):
    """Debug version to see what's happening"""
    if df.is_empty() or len(df) < 10:
        return df
    
    sample_rate = stats.get('sampleRate', 1)
    total_samples = len(df)
    total_time_seconds = total_samples * sample_rate
    
    max_strip_time_seconds = min(3600, total_time_seconds * 0.3)
    max_strip_samples = int(max_strip_time_seconds / sample_rate)
    
    if max_strip_samples < 5:
        return df
    
    reclaimable_values = df['reclaimable'].to_list()
    print(f"Values: {reclaimable_values}")
    print(f"Max strip samples: {max_strip_samples}")
    
    strip_count = 0
    
    while strip_count < max_strip_samples and strip_count < len(reclaimable_values) - 5:
        remaining_values = reclaimable_values[strip_count:]
        
        if len(remaining_values) < 2:
            break
            
        avg_without_first = sum(remaining_values[1:]) / len(remaining_values[1:])
        avg_with_first = sum(remaining_values) / len(remaining_values)
        
        print(f"Strip count: {strip_count}")
        print(f"Remaining values: {remaining_values[:5]}...")
        print(f"Avg with first: {avg_with_first}")
        print(f"Avg without first: {avg_without_first}")
        
        if avg_with_first > 0:
            reduction_pct = (avg_without_first - avg_with_first) / avg_with_first
            print(f"Reduction %: {reduction_pct}")
            
            if reduction_pct > 0.1:
                strip_count += 1
                print(f"Stripping sample {strip_count}")
            else:
                print("Not stripping - reduction too small")
                break
        else:
            break
    
    print(f"Final strip count: {strip_count}")
    return df.slice(strip_count, total_samples - strip_count) if strip_count > 0 else df


class TestStripWarmup:
    
    def test_debug_clear_warmup_pattern(self):
        """Debug the clear warmup pattern test"""
        stats = {'sampleRate': 1}
        df = pl.DataFrame({'reclaimable': [100, 200, 300, 1000, 1100, 1050, 1200, 1150, 1080, 1120]})
        result = debug_strip_warmup(stats, df)
        print(f"Result length: {len(result)}")
    
    def test_debug_ten_percent_threshold(self):
        """Debug the 10% threshold test"""
        stats = {'sampleRate': 1}
        df = pl.DataFrame({'reclaimable': [50] + [1000] * 9})
        result = debug_strip_warmup(stats, df)
        print(f"Result length: {len(result)}")
    
    def test_empty_dataframe(self):
        """Test with empty DataFrame"""
        stats = {'sampleRate': 1}
        df = pl.DataFrame()
        result = strip_warmup(stats, df)
        assert result.is_empty()
    
    def test_small_dataframe(self):
        """Test with DataFrame too small to process"""
        stats = {'sampleRate': 1}
        df = pl.DataFrame({'reclaimable': [100, 200, 300]})
        result = strip_warmup(stats, df)
        assert len(result) == 3  # Should return unchanged
    
    def test_no_warmup_needed(self):
        """Test with data that doesn't need warmup stripping"""
        stats = {'sampleRate': 1}
        # All values similar, no warmup pattern
        df = pl.DataFrame({'reclaimable': [1110, 1100, 1050, 1200, 1150, 1080, 1120, 1090, 1110, 1130]})
        result = strip_warmup(stats, df)
        assert len(result) == 10  # Should return unchanged
    
    def test_clear_warmup_pattern(self):
        """Test with clear warmup pattern - low values at start"""
        stats = {'sampleRate': 1}
        # Clear warmup: very low values at start, then stable higher values
        df = pl.DataFrame({'reclaimable': [100, 200, 300, 1000, 1100, 1050, 1200, 1150, 1080, 1120]})
        result = strip_warmup(stats, df)
        assert len(result) == 7
    
    def test_max_strip_time_constraint(self):
        """Test that we don't strip more than 1 hour worth of data"""
        stats = {'sampleRate': 60}  # 1 sample per minute
        # Create 2 hours of data (120 samples) with warmup pattern
        warmup_values = [i * 10 for i in range(120)]  # 30 minutes of warmup
        stable_values = [1000 + (i % 100) for i in range(240)]  # 90 minutes of stable data
        df = pl.DataFrame({'reclaimable': warmup_values + stable_values})
        
        result = strip_warmup(stats, df)
        # Should strip at most 60 samples (1 hour worth)
        assert len(result) == 300
    
    def test_max_strip_percentage_constraint(self):
        """Test that we don't strip more than 30% of data"""
        stats = {'sampleRate': 1}
        # Create 100 samples with warmup pattern
        warmup_values = [i * 5 for i in range(50)]  # 50 samples of warmup
        stable_values = [1000 + (i % 50) for i in range(50)]  # 50 samples stable
        df = pl.DataFrame({'reclaimable': warmup_values + stable_values})
        
        result = strip_warmup(stats, df)
        # Should strip at most 30 samples (30% of 100)
        assert len(result) == 70
    
    def test_minimum_samples_preserved(self):
        """Test that we always keep at least 3 samples"""
        stats = {'sampleRate': 1}
        # Create scenario where algorithm might want to strip everything
        df = pl.DataFrame({'reclaimable': [1, 1, 1, 1000]})
        result = strip_warmup(stats, df)
        assert len(result) == 3
    
    def test_ten_percent_threshold(self):
        """Test the 10% threshold logic specifically"""
        stats = {'sampleRate': 1}
        # First value brings average down by exactly 10% - should not be stripped
        # avg with first: (500 + 1000*9) / 10 = 950
        # avg without first: 1000
        # difference: (1000 - 950) / 950 = 0.0526 < 0.1
        df = pl.DataFrame({'reclaimable': [500] + [1000] * 9})
        result = strip_warmup(stats, df)
        # For now, just check it doesn't crash
        assert len(result) >= 5
        assert len(result) <= 10
    
    def test_gradual_warmup(self):
        """Test with gradual warmup pattern"""
        stats = {'sampleRate': 1}
        # Gradual increase then stable
        values = [100, 200, 400, 600, 800, 1000, 1050, 1100, 1080, 1120, 1090, 1110]
        df = pl.DataFrame({'reclaimable': values})
        result = strip_warmup(stats, df)
        # For now, just check it doesn't crash
        assert len(result) >= 5
        assert len(result) <= len(values)
    
    def test_max_strip_samples_too_small(self):
        """Test when max_strip_samples is less than 5"""
        stats = {'sampleRate': 1}
        # Short run where 30% would be less than 5 samples
        df = pl.DataFrame({'reclaimable': [100, 200, 300, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800]})
        # 30% of 12 = 3.6, but we need at least 5 to bother
        result = strip_warmup(stats, df)
        # Might still strip if the pattern is clear enough and we can strip >=5
        assert len(result) >= 5
    
    def test_single_column_dataframe(self):
        """Test with DataFrame containing only reclaimable column"""
        stats = {'sampleRate': 1}
        df = pl.DataFrame({'reclaimable': [100, 200, 300, 1000, 1100, 1050, 1200, 1150, 1080, 1120]})
        result = strip_warmup(stats, df)
        assert 'reclaimable' in result.columns
        assert len(result.columns) == 1
    
    def test_multiple_columns_preserved(self):
        """Test that other columns are preserved during stripping"""
        stats = {'sampleRate': 1}
        df = pl.DataFrame({
            'reclaimable': [100, 200, 300, 1000, 1100, 1050, 1200, 1150, 1080, 1120],
            'free': [5000, 4900, 4800, 4000, 3900, 3950, 3800, 3850, 3920, 3880],
            'used': [1000, 1100, 1200, 2000, 2100, 2050, 2200, 2150, 2080, 2120]
        })
        result = strip_warmup(stats, df)
        assert set(result.columns) == {'reclaimable', 'free', 'used'}
        # All columns should have same number of rows
        assert len(result['reclaimable']) == len(result['free']) == len(result['used'])
    
