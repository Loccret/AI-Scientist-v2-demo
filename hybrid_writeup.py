#!/usr/bin/env python3
"""
Script to rerun the writeup with hybrid model setup:
- DeepSeek for text generation (writeup, citations) 
- OpenAI for VLM (Vision Language Model) figure descriptions
"""

import os
import sys
import tempfile
sys.path.append('/home/thunderbird/sakana/AI-Scientist-v2-demo')

from ai_scientist.perform_icbinb_writeup import perform_writeup, gather_citations

def create_hybrid_writeup(experiment_dir, 
                         model_writeup="deepseek-reasoner",
                         model_citation="deepseek-chat", 
                         citation_rounds=10):
    """
    Create writeup using hybrid approach:
    - DeepSeek models for text generation
    - OpenAI gpt-4o for VLM figure descriptions
    """
    
    print(f"Rerunning writeup for experiment: {experiment_dir}")
    if not os.path.exists(experiment_dir):
        print(f"❌ Experiment directory not found: {experiment_dir}")
        return False
    
    # Step 1: Load or gather citations (using DeepSeek)
    print("Step 1: Gathering citations...")
    citations_cache_path = os.path.join(experiment_dir, "cached_citations.bib")
    
    if os.path.exists(citations_cache_path):
        try:
            with open(citations_cache_path, "r") as f:
                citations_text = f.read()
            progress_path = os.path.join(experiment_dir, "citations_progress.json")
            if os.path.exists(progress_path):
                import json
                with open(progress_path, "r") as f:
                    progress = json.load(f)
                    completed_rounds = progress.get("completed_rounds", 0)
                print(f"Resuming citation gathering from round {completed_rounds}")
            print(f"Using DeepSeek API with {model_citation}.")
        except Exception as e:
            print(f"Error loading cached citations: {e}")
            citations_text = None
    else:
        citations_text = None
    
    if citations_text is None or len(citations_text.strip()) == 0:
        print("Gathering new citations...")
        citations_text = gather_citations(
            experiment_dir, 
            num_cite_rounds=citation_rounds, 
            small_model=model_citation
        )
    
    if citations_text is None:
        print("❌ Citation gathering failed")
        return False
    
    print("Citations gathered successfully!")
    
    # Step 2: Perform writeup with hybrid models
    print("Step 2: Performing writeup (DeepSeek + OpenAI VLM)...")
    print(f"- Text generation: {model_writeup}")
    print(f"- VLM figure descriptions: gpt-4o-2024-05-13") 
    
    try:
        writeup_success = perform_writeup(
            base_folder=experiment_dir,
            big_model=model_writeup,          # DeepSeek reasoner for main writeup
            small_model="gpt-4o-2024-05-13", # OpenAI for VLM tasks and citations
            page_limit=4,                     # ICBINB format
            citations_text=citations_text,
            vlm_bypass=False,                 # Enable VLM with OpenAI
            n_writeup_reflections=2           # Reduced reflections for efficiency
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
            print(f"📄 PDF generated at: {pdf_path}")
        else:
            print("⚠️  Main PDF not found, checking for reflection PDFs...")
            for file in os.listdir(experiment_dir):
                if file.endswith('.pdf'):
                    print(f"📄 Found PDF: {file}")
    else:
        print("❌ Writeup failed.")
    
    return writeup_success

def main():
    # Configuration
    experiment_dir = "/home/thunderbird/sakana/AI-Scientist-v2-demo/experiments/2025-08-30_01-42-12_so_neat_attempt_0"
    model_writeup = "deepseek-reasoner"  # DeepSeek for main text generation
    model_citation = "deepseek-chat"     # DeepSeek for citation gathering
    citation_rounds = 10
    
    print("SO-NEAT Experiment Writeup - Hybrid Model Approach")
    print("=" * 55)
    print(f"Experiment directory: {experiment_dir}")
    print(f"Writeup model: {model_writeup}")
    print(f"Citation model: {model_citation}")
    print(f"VLM model: gpt-4o-2024-05-13")
    print(f"Citation rounds: {citation_rounds}")
    print("=" * 55)
    
    success = create_hybrid_writeup(
        experiment_dir, 
        model_writeup, 
        model_citation, 
        citation_rounds
    )
    
    if success:
        print("\n🎉 Hybrid writeup completed successfully!")
        print("   - Text content generated with DeepSeek")  
        print("   - Figure descriptions generated with OpenAI")
        print("   - Academic PDF ready for review!")
    else:
        print("\n❌ Hybrid writeup failed.")
        
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
