#!/usr/bin/env python3
"""
Continue the AI Scientist process from the writeup phase.
This script picks up after experiments and plotting are done.
"""

import os
import os.path as osp
import json
import argparse
import sys
import re
from ai_scientist.llm import create_client
from ai_scientist.perform_writeup import perform_writeup
from ai_scientist.perform_icbinb_writeup import (
    perform_writeup as perform_icbinb_writeup,
    gather_citations,
)
from ai_scientist.perform_llm_review import perform_review, load_paper
from ai_scientist.perform_vlm_review import perform_imgs_cap_ref_review
from ai_scientist.utils.token_tracker import token_tracker


def save_token_tracker(idea_dir):
    """Save token usage tracking data."""
    with open(osp.join(idea_dir, "token_tracker.json"), "w") as f:
        json.dump(token_tracker.get_summary(), f)
    with open(osp.join(idea_dir, "token_tracker_interactions.json"), "w") as f:
        json.dump(token_tracker.get_interactions(), f)


def find_pdf_path_for_review(idea_dir):
    """Find the PDF file for review."""
    pdf_files = [f for f in os.listdir(idea_dir) if f.endswith(".pdf")]
    reflection_pdfs = [f for f in pdf_files if "reflection" in f]
    
    pdf_path = None  # Initialize pdf_path
    
    if reflection_pdfs:
        # First check if there's a final version
        final_pdfs = [f for f in reflection_pdfs if "final" in f.lower()]
        if final_pdfs:
            # Use the final version if available
            pdf_path = osp.join(idea_dir, final_pdfs[0])
        else:
            # Try to find numbered reflections
            reflection_nums = []
            for f in reflection_pdfs:
                match = re.search(r"reflection[_.]?(\d+)", f)
                if match:
                    reflection_nums.append((int(match.group(1)), f))

            if reflection_nums:
                # Get the file with the highest reflection number
                highest_reflection = max(reflection_nums, key=lambda x: x[0])
                pdf_path = osp.join(idea_dir, highest_reflection[1])
            else:
                # Fall back to the first reflection PDF if no numbers found
                pdf_path = osp.join(idea_dir, reflection_pdfs[0])
    else:
        # No reflection PDFs found, look for any PDF file
        if pdf_files:
            # Use the first available PDF file
            pdf_path = osp.join(idea_dir, pdf_files[0])
    
    return pdf_path


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Continue AI scientist from writeup phase")
    parser.add_argument(
        "experiment_dir",
        type=str,
        help="Path to the experiment directory (e.g., experiments/2025-08-30_12-50-31_so_neat_attempt_0)",
    )
    parser.add_argument(
        "--writeup-type",
        type=str,
        default="icbinb",
        choices=["normal", "icbinb"],
        help="Type of writeup to generate (normal=8 page, icbinb=4 page)",
    )
    parser.add_argument(
        "--writeup-retries",
        type=int,
        default=3,
        help="Number of writeup attempts to try",
    )
    parser.add_argument(
        "--model_writeup",
        type=str,
        default="deepseek-reasoner",
        help="Model to use for writeup",
    )
    parser.add_argument(
        "--model_citation",
        type=str,
        default="deepseek-chat",
        help="Model to use for citation gathering",
    )
    parser.add_argument(
        "--num_cite_rounds",
        type=int,
        default=10,
        help="Number of citation rounds to perform",
    )
    parser.add_argument(
        "--model_review",
        type=str,
        default="deepseek-chat",
        help="Model to use for review main text and captions",
    )
    parser.add_argument(
        "--skip_writeup",
        action="store_true",
        help="If set, skip the writeup process",
    )
    parser.add_argument(
        "--skip_review",
        action="store_true",
        help="If set, skip the review process",
    )
    return parser.parse_args()


def main():
    """Main function to continue the AI scientist process."""
    args = parse_arguments()
    
    # Set AI_SCIENTIST_ROOT environment variable
    os.environ["AI_SCIENTIST_ROOT"] = os.path.dirname(os.path.abspath(__file__))
    print(f"Set AI_SCIENTIST_ROOT to {os.environ['AI_SCIENTIST_ROOT']}")
    
    # Validate experiment directory
    idea_dir = args.experiment_dir
    if not os.path.exists(idea_dir):
        print(f"Error: Experiment directory '{idea_dir}' does not exist!")
        sys.exit(1)
    
    print(f"Continuing AI Scientist process for: {idea_dir}")
    
    # Check if required files exist
    required_files = ["idea.json", "idea.md"]
    for req_file in required_files:
        if not os.path.exists(osp.join(idea_dir, req_file)):
            print(f"Warning: Required file '{req_file}' not found in {idea_dir}")
    
    # Save initial token tracker state
    save_token_tracker(idea_dir)

    # === WRITEUP PHASE ===
    if not args.skip_writeup:
        print("\n" + "="*50)
        print("🚀 Starting Writeup Phase")
        print("="*50)
        
        writeup_success = False
        print("📚 Gathering citations...")
        citations_text = gather_citations(
            idea_dir,
            num_cite_rounds=args.num_cite_rounds,
            small_model=args.model_citation,
        )
        
        print(f"📝 Starting writeup with model: {args.model_writeup}")
        print(f"🔗 Using citation model: {args.model_citation}")
        print(f"📄 Writeup type: {args.writeup_type}")
        
        for attempt in range(args.writeup_retries):
            print(f"\n📝 Writeup attempt {attempt+1} of {args.writeup_retries}")
            if args.writeup_type == "normal":
                writeup_success = perform_writeup(
                    base_folder=idea_dir,
                    big_model=args.model_writeup,
                    small_model='gpt-4o-2024-05-13',  # Use OpenAI for VLM tasks
                    page_limit=8,
                    citations_text=citations_text,
                )
            else:
                writeup_success = perform_icbinb_writeup(
                    base_folder=idea_dir,
                    big_model=args.model_writeup,
                    small_model='gpt-4o-2024-05-13',  # Use OpenAI for VLM tasks
                    page_limit=4,
                    citations_text=citations_text,
                )
            if writeup_success:
                print(f"✅ Writeup successful on attempt {attempt+1}")
                break
            else:
                print(f"❌ Writeup attempt {attempt+1} failed")

        if not writeup_success:
            print("❌ Writeup process did not complete successfully after all retries.")
        else:
            print("✅ Writeup phase completed successfully!")

    # Save token tracker after writeup
    save_token_tracker(idea_dir)

    # === REVIEW PHASE ===
    if not args.skip_review and not args.skip_writeup:
        print("\n" + "="*50)
        print("🔍 Starting Review Phase")
        print("="*50)
        
        # Perform paper review if the paper exists
        pdf_path = find_pdf_path_for_review(idea_dir)
        if pdf_path and os.path.exists(pdf_path):
            print(f"📄 Paper found at: {pdf_path}")
            print(f"🔍 Using review model: {args.model_review}")
            
            print("📖 Loading paper content...")
            paper_content = load_paper(pdf_path)
            
            print("🤖 Creating review client...")
            client, client_model = create_client(args.model_review)
            
            print("📝 Performing text review...")
            review_text = perform_review(paper_content, client_model, client)
            
            print("🖼️ Performing image/caption/reference review...")
            review_img_cap_ref = perform_imgs_cap_ref_review(
                client, client_model, pdf_path
            )
            
            # Save review results
            print("💾 Saving review results...")
            with open(osp.join(idea_dir, "review_text.txt"), "w") as f:
                f.write(json.dumps(review_text, indent=4))
            with open(osp.join(idea_dir, "review_img_cap_ref.json"), "w") as f:
                json.dump(review_img_cap_ref, f, indent=4)
            
            print("✅ Paper review completed successfully!")
        else:
            print("❌ No PDF file found for review")

    # === CLEANUP PHASE ===
    print("\n" + "="*50)
    print("🧹 Starting Cleanup Phase")
    print("="*50)
    
    try:
        import psutil
        import signal

        print("🔍 Finding processes to clean up...")
        # Get the current process and all its children
        current_process = psutil.Process()
        children = current_process.children(recursive=True)

        if children:
            print(f"🧹 Found {len(children)} child processes to terminate")
            # First try graceful termination
            for child in children:
                try:
                    child.send_signal(signal.SIGTERM)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Wait briefly for processes to terminate
            gone, alive = psutil.wait_procs(children, timeout=3)
            print(f"✅ {len(gone)} processes terminated gracefully")

            # If any processes remain, force kill them
            if alive:
                print(f"⚠️ Force killing {len(alive)} remaining processes")
                for process in alive:
                    try:
                        process.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

        # Additional cleanup: find any orphaned processes containing specific keywords
        print("🔍 Checking for orphaned processes...")
        keywords = ["python", "torch", "mp", "bfts", "experiment"]
        orphaned_count = 0
        for proc in psutil.process_iter(["name", "cmdline"]):
            try:
                # Check both process name and command line arguments
                cmdline = " ".join(proc.cmdline()).lower()
                if any(keyword in cmdline for keyword in keywords):
                    proc.send_signal(signal.SIGTERM)
                    proc.wait(timeout=3)
                    if proc.is_running():
                        proc.kill()
                    orphaned_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                continue
        
        if orphaned_count > 0:
            print(f"🧹 Cleaned up {orphaned_count} orphaned processes")
        else:
            print("✅ No orphaned processes found")

    except ImportError:
        print("⚠️ psutil not available, skipping process cleanup")
    except Exception as e:
        print(f"⚠️ Error during cleanup: {e}")

    print("\n" + "="*50)
    print("🎉 AI Scientist process completed!")
    print("="*50)
    
    # Final summary
    print(f"📁 Results saved in: {idea_dir}")
    if os.path.exists(osp.join(idea_dir, "template.pdf")):
        print("📄 PDF generated: template.pdf")
    if os.path.exists(osp.join(idea_dir, "figures")):
        figures = os.listdir(osp.join(idea_dir, "figures"))
        print(f"🖼️ Figures generated: {len(figures)} files")
    if os.path.exists(osp.join(idea_dir, "review_text.txt")):
        print("🔍 Review completed: review_text.txt")


if __name__ == "__main__":
    main()
