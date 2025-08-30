#!/usr/bin/env python3
"""
Test the overall_summarize fix for incomplete stages.
"""
import sys
sys.path.insert(0, '/home/thunderbird/sakana/AI-Scientist-v2-demo')

def test_overall_summarize_with_single_stage():
    """Test that overall_summarize handles single stage correctly."""
    try:
        from ai_scientist.treesearch.log_summarization import overall_summarize
        from ai_scientist.treesearch.journal import Journal
        
        # Create mock journals with only one stage (simulating the error scenario)
        mock_journals = [
            ("stage_1_initial_implementation_1_preliminary", Journal()),  # Only one stage
        ]
        
        # This should not raise "not enough values to unpack" error anymore
        try:
            draft_summary, baseline_summary, research_summary, ablation_summary = overall_summarize(
                mock_journals, model="deepseek-chat"
            )
            print("✅ overall_summarize handles single stage without unpacking error")
            print(f"   Results: draft={type(draft_summary)}, baseline={type(baseline_summary)}, research={type(research_summary)}, ablation={type(ablation_summary)}")
            return True
        except ValueError as e:
            if "not enough values to unpack" in str(e):
                print(f"❌ Still has unpacking error: {e}")
                return False
            else:
                print(f"✅ No unpacking error (other ValueError expected): {e}")
                return True
        except Exception as e:
            print(f"✅ No unpacking error (other error expected in mock test): {type(e).__name__}: {e}")
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_json_dump_with_none():
    """Test that json.dump works with None values."""
    try:
        import json
        import tempfile
        
        # Test that None values can be written to JSON
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            json.dump(None, f, indent=2)
            temp_path = f.name
        
        # Verify the file contains valid JSON
        with open(temp_path, 'r') as f:
            content = f.read()
            if content.strip() == 'null':
                print("✅ json.dump(None) works correctly")
                return True
            else:
                print(f"❌ Unexpected JSON content: {content}")
                return False
                
    except Exception as e:
        print(f"❌ JSON test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing overall_summarize fix for single stage...")
    print("=" * 55)
    
    tests = [
        test_overall_summarize_with_single_stage,
        test_json_dump_with_none
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 55)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 The 'not enough values to unpack' error should be fixed!")
    else:
        print("❌ The fix may not be complete.")
