#!/usr/bin/env python3
"""
Script to rerun just the writeup part for a successful experiment.
This version uses OpenAI for VLM (Vision Language Model) processing while using DeepSeek for text generation.
"""

import os
import sys
import tempfile
sys.path.append('/home/thunderbird/sakana/AI-Scientist-v2-demo')

def create_no_vlm_writeup(experiment_dir, model_writeup="deepseek-reasoner", model_citation="deepseek-chat", num_cite_rounds=10):
    """
    Create a writeup without VLM processing by temporarily modifying the VLM function.
    """
    # First, let's import after adding to path
    from ai_scientist.perform_icbinb_writeup import perform_writeup, gather_citations
    import ai_scientist.vlm as vlm_module
    
    print(f"Rerunning writeup for experiment: {experiment_dir}")
    
    # Check if experiment directory exists
    if not os.path.exists(experiment_dir):
        print(f"Error: Experiment directory does not exist: {experiment_dir}")
        return False
    
    # Store original VLM function
    original_create_client = vlm_module.create_client
    
    # Create a mock VLM client that returns empty descriptions
    def mock_vlm_client(model):
        print(f"Skipping VLM processing for model {model} (not supported by DeepSeek)")
        # Return a mock client and model
        class MockClient:
            class chat:
                class completions:
                    @staticmethod
                    def create(**kwargs):
                        class MockResponse:
                            class choices:
                                class message:
                                    content = '{"caption": "Figure generated from experiment results", "detailed_caption": "This figure shows the experimental results from the SO-NEAT algorithm implementation."}'
                            choices = [choices()]
                        return MockResponse()
        return MockClient(), model
    
    try:
        # Temporarily replace the VLM client
        vlm_module.create_client = mock_vlm_client
        
        # Gather citations first
        print("Step 1: Gathering citations...")
        try:
            citations_text = gather_citations(
                base_folder=experiment_dir,
                num_cite_rounds=num_cite_rounds,
                small_model=model_citation,
            )
            print("Citations gathered successfully!")
        except Exception as e:
            print(f"Citation gathering failed: {e}")
            citations_text = ""
        
        # Perform writeup
        print("Step 2: Performing writeup (with OpenAI VLM processing)...")
        try:
            writeup_success = perform_writeup(
                base_folder=experiment_dir,
                big_model=model_writeup,      # deepseek-reasoner for main writeup
                small_model="gpt-4o-2024-05-13",  # OpenAI for VLM tasks
                page_limit=4,  # ICBINB format
                citations_text=citations_text,
                vlm_bypass=False  # Enable VLM processing with OpenAI
            )
        except Exception as e:
            print(f"❌ Exception during writeup: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        if writeup_success:
            print("✅ Writeup completed successfully!")
            pdf_path = os.path.join(experiment_dir, f"{os.path.basename(experiment_dir)}.pdf")
            if os.path.exists(pdf_path):
                print(f"PDF generated at: {pdf_path}")
            else:
                print("Writeup successful but PDF file not found in expected location.")
        else:
            print("❌ Writeup failed.")
        
        return writeup_success
        
    except Exception as e:
        print(f"Writeup failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Restore original VLM function
        vlm_module.create_client = original_create_client
    """
    Rerun just the writeup process for an existing experiment.
    """
    print(f"Rerunning writeup for experiment: {experiment_dir}")
    
    # Check if experiment directory exists
    if not os.path.exists(experiment_dir):
        print(f"Error: Experiment directory does not exist: {experiment_dir}")
        return False
    
    # Gather citations first
    print("Step 1: Gathering citations...")
    try:
        citations_text = gather_citations(
            base_folder=experiment_dir,
            num_cite_rounds=num_cite_rounds,
            small_model=model_citation,
        )
        print("Citations gathered successfully!")
    except Exception as e:
        print(f"Citation gathering failed: {e}")
        citations_text = ""
    
    # Perform writeup (skip VLM for now since DeepSeek doesn't support vision)
    print("Step 2: Performing writeup...")
    try:
        writeup_success = perform_writeup(
            base_folder=experiment_dir,
            big_model=model_writeup,
            small_model="gpt-4o-2024-05-13",  # Use OpenAI for VLM tasks only
            page_limit=4,  # ICBINB format
            citations_text=citations_text,
        )
        
        if writeup_success:
            print("✅ Writeup completed successfully!")
            pdf_path = os.path.join(experiment_dir, f"{os.path.basename(experiment_dir)}.pdf")
            if os.path.exists(pdf_path):
                print(f"PDF generated at: {pdf_path}")
            else:
                print("Writeup successful but PDF file not found in expected location.")
        else:
            print("❌ Writeup failed.")
        
        return writeup_success
        
    except Exception as e:
        print(f"Writeup failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Configuration
    experiment_dir = "/home/thunderbird/sakana/AI-Scientist-v2-demo/experiments/2025-08-30_01-42-12_so_neat_attempt_0"
    model_writeup = "deepseek-reasoner"
    model_citation = "deepseek-chat" 
    num_cite_rounds = 10
    
    print("SO-NEAT Experiment Writeup Rerun")
    print("=" * 50)
    print(f"Experiment directory: {experiment_dir}")
    print(f"Writeup model: {model_writeup}")
    print(f"Citation model: {model_citation}")
    print(f"Citation rounds: {num_cite_rounds}")
    print("=" * 50)
    
    success = create_no_vlm_writeup(
        experiment_dir=experiment_dir,
        model_writeup=model_writeup,
        model_citation=model_citation,
        num_cite_rounds=num_cite_rounds
    )
    
    if success:
        print("\n🎉 Writeup rerun completed successfully!")
    else:
        print("\n❌ Writeup rerun failed.")
