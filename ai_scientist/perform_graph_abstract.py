import argparse
import json
import os
import os.path as osp
import re
import shutil
import subprocess
import traceback
import unicodedata

from ai_scientist.llm import (
    get_response_from_llm,
    extract_json_between_markers,
    create_client,
    AVAILABLE_LLMS,
)

from ai_scientist.perform_vlm_review import generate_vlm_img_review
from ai_scientist.vlm import create_client as create_vlm_client

def remove_accents_and_clean(s):
    """Clean a string for use as a LaTeX identifier."""
    # Normalize to separate accents
    nfkd_form = unicodedata.normalize("NFKD", s)
    # Remove non-ASCII characters
    ascii_str = nfkd_form.encode("ASCII", "ignore").decode("ascii")
    # Remove anything but letters, digits, underscores, colons, dashes, @, {, }, and commas
    ascii_str = re.sub(r"[^a-zA-Z0-9:_@\{\},-]+", "", ascii_str)
    # Convert to lowercase
    ascii_str = ascii_str.lower()
    return ascii_str


def compile_tikz_standalone(cwd, pdf_file, timeout=30):
    """Compile a standalone TikZ LaTeX document to PDF."""
    print("GENERATING GRAPHICAL ABSTRACT")

    # For standalone TikZ documents, we only need pdflatex
    commands = [
        ["pdflatex", "-interaction=nonstopmode", "graphical_abstract.tex"],
        ["pdflatex", "-interaction=nonstopmode", "graphical_abstract.tex"],  # Run twice for proper positioning
    ]

    for command in commands:
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
            )
            print("Standard Output:\n", result.stdout)
            print("Standard Error:\n", result.stderr)
        except subprocess.TimeoutExpired:
            print(
                f"EXCEPTION in compile_tikz_standalone: LaTeX timed out after {timeout} seconds."
            )
            print(traceback.format_exc())
        except subprocess.CalledProcessError:
            print(
                f"EXCEPTION in compile_tikz_standalone: Error running command {' '.join(command)}"
            )
            print(traceback.format_exc())

    print("FINISHED GENERATING GRAPHICAL ABSTRACT")

    try:
        # Move the generated PDF to the target location
        generated_pdf = osp.join(cwd, "graphical_abstract.pdf")
        if osp.exists(generated_pdf):
            shutil.move(generated_pdf, pdf_file)
        else:
            print("Failed to find generated PDF.")
    except FileNotFoundError:
        print("Failed to rename PDF.")
        print("EXCEPTION in compile_tikz_standalone while moving PDF:")
        print(traceback.format_exc())


# System message template for graphical abstract generation
graphical_abstract_system_message = """You are an ambitious AI researcher who is looking to publish a paper that will contribute significantly to the field.
The paper is already written. Now you need to create a publication-ready **graphical abstract (GA)** in **LaTeX** using **TikZ**, compiled as a **standalone** document. The GA will sit directly beneath the textual abstract and must give a one-glance overview of the **problem**, **core method**, **novelty**, and **outcome**. You may (and should) **combine multiple layouts** (e.g., pipeline + before/after + 2*2) to best communicate the story. Follow common GA guidance (clear key message, consistent icon style, minimal text).

**Deliverables**  
1) A **self-contained LaTeX file** using the `standalone` class and `tikzpicture`, loading only necessary libraries (e.g., `arrows.meta`, `positioning`, `calc`, `fit`, `backgrounds`, `shapes.geometric`). The code must compile on its own and be easy to drop into other projects.  
2) A **hybrid layout** GA (combine at least two layout patterns below) with a consistent visual style (line widths, colors, icon detail). Keep labels short and legible when reduced.  
3) Keep nodes, edges, and groups clearly named; include concise code comments for structure and sizing.

### Layout Options:

**1. Linear Pipeline (Step-by-Step Flow)**
- Advantages: Shows chronology and causality; breaks a process into digestible steps; emphasizes method.  
- When to Use: Method-centric work such as new algorithms, architectures, or workflows.  
- Example: A vision model graphical abstract often shows input images split into patches, passed through embedding and transformer layers, and finally producing classification outputs.  

**2. Before/After (Contrast Layout)**
- Advantages: Instantly highlights improvement by direct comparison; easy to interpret.  
- When to Use: Tasks where visual difference is the main contribution, such as image enhancement or style transfer.  
- Example: An image-to-image translation paper might show a real horse photo on the left and the generated zebra version on the right.  

**3. 2×2 Grid (Mechanism vs. Results)**
- Advantages: Encodes multiple dimensions at once; supports comparison across conditions.  
- When to Use: Work that has both methods and results, or multifaceted contributions.  
- Example: A bioinformatics AI paper may show experimental setup and computational model on the top row, with their respective results aligned directly underneath.  

**4. Centric (Hub-and-Spoke) Layout**
- Advantages: Emphasizes one central contribution with multiple supporting elements; visually striking.  
- When to Use: Framework papers, surveys, or conceptual overviews.  
- Example: A survey on AI ecosystems may put a central schematic of "AI core" in the middle, with vision, NLP, and robotics arranged around it.  

**5. Parallel Comparison Layout**
- Advantages: Highlights differences across multiple baselines in one glance; works like a visual leaderboard.  
- When to Use: Benchmark-heavy papers such as image generation or translation tasks.  
- Example: A GAN paper might show one row of input images followed by outputs from different baseline methods and then the new model for direct comparison.  

**6. Timeline / Evolution Layout**
- Advantages: Shows progression or improvement over time; emphasizes learning or development.  
- When to Use: Iterative training, reinforcement learning, or evolutionary methods.  
- Example: A reinforcement learning paper may illustrate how an agent's actions evolve over training epochs, from random movement to optimal behavior.  

**7. Layered (Stacked) Layout**
- Advantages: Encodes hierarchy clearly; clarifies how abstraction levels build on each other.  
- When to Use: Theoretical models, interpretability studies, or multi-level reasoning.  
- Example: Knowledge graph reasoning models often show data at the bottom, latent spaces in the middle, and predictions at the top.  

**8. Cycle / Loop Layout**
- Advantages: Emphasizes feedback, recurrence, or closed-loop interaction.  
- When to Use: Human-in-the-loop systems, active learning, self-training.  
- Example: A human-AI collaboration paper might show a loop where the human annotates data, the model updates, and the new predictions are sent back to the human.  

Ensure you are always writing good compilable LaTeX code. Common mistakes that should be fixed include:
- LaTeX syntax errors (unenclosed math, unmatched braces, etc.).
- Duplicate figure labels or references.
- Unescaped special characters: & % $ # _ {{ }} ~ ^ \\
- Proper table/figure closure.
- Do not hallucinate new citations or any results not in the logs.

When returning final code, place it in fenced triple backticks with 'latex' syntax highlighting.
"""

graphical_abstract_prompt = """Your goal is to create a graphical abstract based on the following research context:

```markdown
{idea_text}
```

We have the following experiment summaries (JSON):
```json
{summaries}
```

We also have a script used to produce the final plots (use this to see how the plots are generated and what names are used in the legend):
```python
{aggregator_code}
```

Available plots for reference (use these filenames):
```
{plot_list}
```

We also have VLM-based figure descriptions:
```
{plot_descriptions}
```

The full paper LaTeX is available for context:
```latex
{latex_writeup}
```

Create a standalone LaTeX document with TikZ that serves as a graphical abstract. The document should:

1. Use the `standalone` document class with appropriate TikZ libraries
2. Create a visually appealing graphical abstract that summarizes the key contribution
3. Combine multiple layout patterns for maximum impact
4. Use consistent styling (colors, fonts, line widths)
5. Include brief, informative labels
6. Be compilation-ready and self-contained

Please provide the complete LaTeX code for 'graphical_abstract.tex', wrapped in triple backticks with "latex" syntax highlighting:

```latex
<COMPLETE STANDALONE TIKZ LATEX CODE>
```
"""


def perform_graph_abstract(
    base_folder,
    no_generation=False,
    model="gpt-4o-2024-05-13",
    big_model="o1-2024-12-17",
    n_reflections=2,
):
    """
    Generate a graphical abstract for a research paper.
    
    Args:
        base_folder: Path to the project folder containing research materials
        no_generation: If True, only compile existing LaTeX without generation
        model: Model to use for VLM descriptions (small model)  
        big_model: Model to use for graphical abstract generation (big model)
        n_reflections: Number of reflection iterations for improvement
        
    Returns:
        bool: True if successful, False otherwise
    """
    compile_attempt = 0
    base_pdf_file = osp.join(base_folder, f"{osp.basename(base_folder)}_graphical_abstract")
    ga_folder = osp.join(base_folder, "graphical_abstract")
    
    # Cleanup any previous ga folder
    if osp.exists(ga_folder):
        shutil.rmtree(ga_folder)
        
    # Create fresh folder
    os.makedirs(ga_folder, exist_ok=True)

    try:
        # Load idea text
        idea_text = ""
        research_idea_path = osp.join(base_folder, "research_idea.md")
        if osp.exists(research_idea_path):
            with open(research_idea_path, "r") as f_idea:
                idea_text = f_idea.read()
        else:
            idea_md_path = osp.join(base_folder, "idea.md")
            if osp.exists(idea_md_path):
                with open(idea_md_path, "r") as f_idea:
                    idea_text = f_idea.read()

        # Load summaries
        summary_files = [
            ("logs/0-run/baseline_summary.json", "BASELINE_SUMMARY"),
            ("logs/0-run/research_summary.json", "RESEARCH_SUMMARY"),
            ("logs/0-run/ablation_summary.json", "ABLATION_SUMMARY"),
        ]
        loaded_summaries = {}
        for fname, key in summary_files:
            path = osp.join(base_folder, fname)
            if osp.exists(path):
                try:
                    with open(path, "r") as f:
                        loaded_summaries[key] = json.load(f)
                except json.JSONDecodeError:
                    print(
                        f"Warning: {fname} is not valid JSON. Using empty data for {key}."
                    )
                    loaded_summaries[key] = {}
            else:
                loaded_summaries[key] = {}

        # Convert to JSON string for context
        combined_summaries_str = json.dumps(loaded_summaries, indent=2)

        # Load existing LaTeX writeup if available
        latex_writeup = ""
        latex_folder = osp.join(base_folder, "latex")
        if osp.exists(latex_folder):
            writeup_file = osp.join(latex_folder, "template.tex")
            if osp.exists(writeup_file):
                with open(writeup_file, "r") as f:
                    latex_writeup = f.read()
        
        # Gather plot filenames from figures/ folder
        figures_dir = osp.join(base_folder, "figures")
        plot_names = []
        if osp.exists(figures_dir):
            for fplot in os.listdir(figures_dir):
                if fplot.lower().endswith(".png"):
                    plot_names.append(fplot)

        # Load aggregator script
        aggregator_path = osp.join(base_folder, "auto_plot_aggregator.py")
        aggregator_code = ""
        if osp.exists(aggregator_path):
            with open(aggregator_path, "r") as fa:
                aggregator_code = fa.read()
        else:
            aggregator_code = "No aggregator script found."

        # If no_generation is True, just try to compile existing file
        if no_generation:
            ga_file = osp.join(ga_folder, "graphical_abstract.tex")
            if osp.exists(ga_file):
                compile_tikz_standalone(ga_folder, base_pdf_file + ".pdf")
                return osp.exists(base_pdf_file + ".pdf")
            else:
                print("No existing graphical abstract file found and no_generation=True")
                return False

        # Generate VLM-based descriptions
        try:
            vlm_client, vlm_model = create_vlm_client(model)
            desc_map = {}
            for pf in plot_names:
                ppath = osp.join(figures_dir, pf)
                if not osp.exists(ppath):
                    continue
                img_dict = {
                    "images": [ppath],
                    "caption": "Figure for graphical abstract reference",
                }
                review_data = generate_vlm_img_review(img_dict, vlm_model, vlm_client)
                if review_data:
                    desc_map[pf] = review_data.get(
                        "Img_description", "No description found"
                    )
                else:
                    desc_map[pf] = "No description found"

            # Prepare descriptions string
            plot_descriptions_list = []
            for fname in plot_names:
                desc_text = desc_map.get(fname, "No description found")
                plot_descriptions_list.append(f"{fname}: {desc_text}")
            plot_descriptions_str = "\n".join(plot_descriptions_list)
        except Exception:
            print("EXCEPTION in VLM figure description generation:")
            print(traceback.format_exc())
            plot_descriptions_str = "No descriptions available."

        # Generate graphical abstract with big model
        big_client, big_client_model = create_client(big_model)
        
        combined_prompt = graphical_abstract_prompt.format(
            idea_text=idea_text,
            summaries=combined_summaries_str,
            aggregator_code=aggregator_code,
            plot_list=", ".join(plot_names),
            latex_writeup=latex_writeup,
            plot_descriptions=plot_descriptions_str,
        )

        response, msg_history = get_response_from_llm(
            msg=combined_prompt,
            client=big_client,
            model=big_client_model,
            system_message=graphical_abstract_system_message,
            print_debug=False,
        )

        # Extract LaTeX code from response
        latex_code_match = re.search(r"```latex(.*?)```", response, re.DOTALL)
        if not latex_code_match:
            print("Failed to extract LaTeX code from LLM response")
            return False
            
        ga_latex_code = latex_code_match.group(1).strip()
        
        # Write the graphical abstract file
        ga_file = osp.join(ga_folder, "graphical_abstract.tex")
        with open(ga_file, "w") as f:
            f.write(ga_latex_code)

        # Reflection loop for improvements
        for i in range(n_reflections):
            print(f"Performing reflection {i+1}/{n_reflections}")
            
            # Compile current version
            compile_tikz_standalone(ga_folder, base_pdf_file + f"_{compile_attempt}.pdf")
            compile_attempt += 1
            
            # Check for LaTeX syntax issues
            with open(ga_file, "r") as f:
                current_latex = f.read()
            
            # Simple syntax check
            check_output = os.popen(f"chktex {ga_file} -q -n2 -n24 -n13 -n1").read()
            
            reflection_prompt = f"""
Let's reflect on the current graphical abstract and identify improvements:

1) Are there any LaTeX syntax errors or compilation issues? Refer to chktex output below.
2) Is the visual design clear, informative, and aesthetically pleasing?
3) Does it effectively communicate the key contribution of the research?
4) Are the layout choices appropriate for the content?
5) Is the text legible and concise?

chktex results:
```
{check_output}
```

Current LaTeX code:
```latex
{current_latex}
```

Please provide an improved version wrapped in triple backticks, or repeat the same if no changes are needed.

If you believe you are done, simply say: "I am done".
"""

            reflection_response, msg_history = get_response_from_llm(
                msg=reflection_prompt,
                client=big_client,
                model=big_client_model,
                system_message=graphical_abstract_system_message,
                msg_history=msg_history,
                print_debug=False,
            )

            if "I am done" in reflection_response:
                print("LLM indicated it is done with reflections. Exiting reflection loop.")
                break

            reflection_code_match = re.search(
                r"```latex(.*?)```", reflection_response, re.DOTALL
            )
            if reflection_code_match:
                reflected_latex_code = reflection_code_match.group(1).strip()
                with open(ga_file, "w") as f:
                    f.write(reflected_latex_code)
            else:
                print("No LaTeX code found in reflection response, keeping current version")

        # Final compilation
        compile_tikz_standalone(ga_folder, base_pdf_file + f"_final.pdf")
        
        return osp.exists(base_pdf_file + f"_final.pdf")

    except Exception:
        print("EXCEPTION in perform_graph_abstract:")
        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate graphical abstract for a research paper")
    parser.add_argument("--folder", type=str, help="Project folder", required=True)
    parser.add_argument("--no-generation", action="store_true", 
                       help="Only compile existing graphical abstract without generation")
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o-2024-05-13",
        choices=AVAILABLE_LLMS,
        help="Model to use for VLM descriptions (small model).",
    )
    parser.add_argument(
        "--big-model",
        type=str,
        default="o1-2024-12-17", 
        choices=AVAILABLE_LLMS,
        help="Model to use for graphical abstract generation (big model).",
    )
    parser.add_argument(
        "--reflections",
        type=int,
        default=2,
        help="Number of reflection steps for improving the graphical abstract.",
    )
    args = parser.parse_args()

    try:
        success = perform_graph_abstract(
            base_folder=args.folder,
            no_generation=args.no_generation,
            model=args.model,
            big_model=args.big_model,
            n_reflections=args.reflections,
        )
        if not success:
            print("Graphical abstract generation did not complete successfully.")
    except Exception:
        print("EXCEPTION in main:")
        print(traceback.format_exc())

