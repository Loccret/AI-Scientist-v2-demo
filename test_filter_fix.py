#!/usr/bin/env python3
"""
Test script to verify that the filter_experiment_summaries fix handles various scenarios correctly.
"""

import json
import tempfile
import os
from ai_scientist.perform_icbinb_writeup import filter_experiment_summaries, load_exp_summaries


def test_filter_with_none_values():
    """Test filter_experiment_summaries with None values (failed experiments)."""
    print("=== Testing filter_experiment_summaries with None values ===")
    
    exp_summaries = {
        'BASELINE_SUMMARY': None,
        'RESEARCH_SUMMARY': None,
        'ABLATION_SUMMARY': None
    }
    
    # Test all step types with their expected results
    test_cases = [
        ('citation_gathering', {'BASELINE_SUMMARY': None, 'RESEARCH_SUMMARY': None}),
        ('writeup', {'BASELINE_SUMMARY': None, 'RESEARCH_SUMMARY': None}),
        ('plot_aggregation', {'BASELINE_SUMMARY': None, 'RESEARCH_SUMMARY': None, 'ABLATION_SUMMARY': None})
    ]
    
    for step_name, expected in test_cases:
        print(f"Testing step_name: {step_name}")
        try:
            result = filter_experiment_summaries(exp_summaries, step_name)
            print(f"  ✓ Success: {result}")
            assert result == expected, f"Expected {expected}, got {result}"
        except Exception as e:
            print(f"  ✗ Error: {e}")
            raise


def test_filter_with_mixed_values():
    """Test filter_experiment_summaries with mixed None and valid values."""
    print("\n=== Testing filter_experiment_summaries with mixed values ===")
    
    exp_summaries = {
        'BASELINE_SUMMARY': None,
        'RESEARCH_SUMMARY': {'best node': {'overall_plan': 'Some plan', 'analysis': 'Some analysis'}},
        'ABLATION_SUMMARY': None
    }
    
    try:
        result = filter_experiment_summaries(exp_summaries, 'plot_aggregation')
        print(f"  ✓ Success: {result}")
        expected = {
            'BASELINE_SUMMARY': None,
            'RESEARCH_SUMMARY': {'best node': {'overall_plan': 'Some plan', 'analysis': 'Some analysis'}},
            'ABLATION_SUMMARY': None
        }
        assert result == expected
    except Exception as e:
        print(f"  ✗ Error: {e}")
        raise


def test_load_exp_summaries_with_null_files():
    """Test load_exp_summaries with files containing null values."""
    print("\n=== Testing load_exp_summaries with null JSON files ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create logs/0-run directory structure
        logs_dir = os.path.join(temp_dir, 'logs', '0-run')
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create JSON files with null content
        for filename in ['baseline_summary.json', 'research_summary.json', 'ablation_summary.json']:
            filepath = os.path.join(logs_dir, filename)
            with open(filepath, 'w') as f:
                json.dump(None, f)
        
        try:
            result = load_exp_summaries(temp_dir)
            print(f"  ✓ Success: {result}")
            expected = {'BASELINE_SUMMARY': None, 'RESEARCH_SUMMARY': None, 'ABLATION_SUMMARY': None}
            assert result == expected
        except Exception as e:
            print(f"  ✗ Error: {e}")
            raise


def test_integration():
    """Test the complete integration: load_exp_summaries + filter_experiment_summaries."""
    print("\n=== Testing complete integration ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create logs/0-run directory structure
        logs_dir = os.path.join(temp_dir, 'logs', '0-run')
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create JSON files with null content (simulating failed experiments)
        for filename in ['baseline_summary.json', 'research_summary.json', 'ablation_summary.json']:
            filepath = os.path.join(logs_dir, filename)
            with open(filepath, 'w') as f:
                json.dump(None, f)
        
        try:
            # Load experiment summaries
            exp_summaries = load_exp_summaries(temp_dir)
            print(f"  Loaded summaries: {exp_summaries}")
            
            # Filter for plot aggregation
            filtered = filter_experiment_summaries(exp_summaries, 'plot_aggregation')
            print(f"  ✓ Filtered successfully: {filtered}")
            
            expected = {'BASELINE_SUMMARY': None, 'RESEARCH_SUMMARY': None, 'ABLATION_SUMMARY': None}
            assert filtered == expected
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            raise


if __name__ == "__main__":
    try:
        test_filter_with_none_values()
        test_filter_with_mixed_values()
        test_load_exp_summaries_with_null_files()
        test_integration()
        print("\n🎉 All tests passed! The fix is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
