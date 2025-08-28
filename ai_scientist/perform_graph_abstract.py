import argparse
import json
import os
import os.path as osp
import re
import shutil
import subprocess
import traceback
import unicodedata
import uuid

from ai_scientist.llm import (
    get_response_from_llm,
    extract_json_between_markers,
    create_client,
    AVAILABLE_LLMS,
)

from ai_scientist.tools.semantic_scholar import search_for_papers

from ai_scientist.perform_vlm_review import generate_vlm_img_review
from ai_scientist.vlm import create_client as create_vlm_client
from ai_scientist.perform_llm_review import load_paper



def remove_accents_and_clean(s):
    # print("Original:", s)
    # Normalize to separate accents
    nfkd_form = unicodedata.normalize("NFKD", s)
    # Remove non-ASCII characters
    ascii_str = nfkd_form.encode("ASCII", "ignore").decode("ascii")
    # Remove anything but letters, digits, underscores, colons, dashes, @, {, }, and now commas
    ascii_str = re.sub(r"[^a-zA-Z0-9:_@\{\},-]+", "", ascii_str)
    # Convert to lowercase
    ascii_str = ascii_str.lower()
    # print("Cleaned: ", ascii_str)
    return ascii_str


def compile_latex(cwd, pdf_file, timeout=30):
    print("GENERATING LATEX")

    commands = [
        ["pdflatex", "-interaction=nonstopmode", "template.tex"],
        ["bibtex", "template"],
        ["pdflatex", "-interaction=nonstopmode", "template.tex"],
        ["pdflatex", "-interaction=nonstopmode", "template.tex"],
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
                f"EXCEPTION in compile_latex: LaTeX timed out after {timeout} seconds."
            )
            print(traceback.format_exc())
        except subprocess.CalledProcessError:
            print(
                f"EXCEPTION in compile_latex: Error running command {' '.join(command)}"
            )
            print(traceback.format_exc())

    print("FINISHED GENERATING LATEX")

    try:
        shutil.move(osp.join(cwd, "template.pdf"), pdf_file)
    except FileNotFoundError:
        print("Failed to rename PDF.")
        print("EXCEPTION in compile_latex while moving PDF:")
        print(traceback.format_exc())


def detect_pages_before_impact(latex_folder, timeout=30):
    """
    Temporarily copy the latex folder, compile, and detect on which page
    the phrase "Impact Statement" appears.
    Returns a tuple (page_number, line_number) if found, otherwise None.
    """
    temp_dir = osp.join(latex_folder, f"_temp_compile_{uuid.uuid4().hex}")
    try:
        shutil.copytree(latex_folder, temp_dir, dirs_exist_ok=True)

        # Compile in the temp folder
        commands = [
            ["pdflatex", "-interaction=nonstopmode", "template.tex"],
            ["bibtex", "template"],
            ["pdflatex", "-interaction=nonstopmode", "template.tex"],
            ["pdflatex", "-interaction=nonstopmode", "template.tex"],
        ]
        for command in commands:
            try:
                subprocess.run(
                    command,
                    cwd=temp_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=timeout,
                )
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                return None

        temp_pdf_file = osp.join(temp_dir, "template.pdf")
        if not osp.exists(temp_pdf_file):
            return None

        # Try page-by-page extraction to detect "Impact Statement"
        for i in range(1, 51):
            page_txt = osp.join(temp_dir, f"page_{i}.txt")
            subprocess.run(
                [
                    "pdftotext",
                    "-f",
                    str(i),
                    "-l",
                    str(i),
                    "-q",
                    temp_pdf_file,
                    page_txt,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if not osp.exists(page_txt):
                break
            with open(page_txt, "r", encoding="utf-8", errors="ignore") as fp:
                page_content = fp.read()
            lines = page_content.split("\n")
            for idx, line in enumerate(lines):
                if "Impact Statement" in line:
                    return (i, idx + 1)
        return None
    except Exception:
        return None
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)





# Using a template string to allow injection of the {page_limit} argument
writeup_system_message_template = """You are an ambitious AI researcher who is looking to publish a paper that will contribute significantly to the field.
The paper is already written. Now you need to create a publication-ready **graphical abstract (GA)** in **LaTeX** using **TikZ**, compiled as a **standalone** document. The GA will sit directly beneath the textual abstract and must give a one-glance overview of the **problem**, **core method**, **novelty**, and **outcome**. You may (and should) **combine multiple layouts** (e.g., pipeline + before/after + 2*2) to best communicate the story. Follow common GA guidance (clear key message, consistent icon style, minimal text.


**Deliverables**  
1) A **self-contained LaTeX file** using the `standalone` class and `tikzpicture`, loading only necessary libraries (e.g., `arrows.meta`, `positioning`, `calc`, `fit`, `backgrounds`, `shapes.geometric`). The code must compile on its own and be easy to drop into other projects.  
2) A **hybrid layout** GA (combine at least two layout patterns below) with a consistent visual style (line widths, colors, icon detail). Keep labels short and legible when reduced.  
3) Keep nodes, edges, and groups clearly named; include concise code comments for structure and sizing.


```markdown
### 1. Linear Pipeline (Step-by-Step Flow)
- Advantages: Shows chronology and causality; breaks a process into digestible steps; emphasizes method.  
- When to Use: Method-centric work such as new algorithms, architectures, or workflows.  
- Example: A vision model graphical abstract often shows input images split into patches, passed through embedding and transformer layers, and finally producing classification outputs.  

---

### 2. Before/After (Contrast Layout)
- Advantages: Instantly highlights improvement by direct comparison; easy to interpret.  
- When to Use: Tasks where visual difference is the main contribution, such as image enhancement or style transfer.  
- Example: An image-to-image translation paper might show a real horse photo on the left and the generated zebra version on the right.  

---

### 3. 2×2 Grid (Mechanism vs. Results)
- Advantages: Encodes multiple dimensions at once; supports comparison across conditions.  
- When to Use: Work that has both methods and results, or multifaceted contributions.  
- Example: A bioinformatics AI paper may show experimental setup and computational model on the top row, with their respective results aligned directly underneath.  

---

### 4. Centric (Hub-and-Spoke) Layout
- Advantages: Emphasizes one central contribution with multiple supporting elements; visually striking.  
- When to Use: Framework papers, surveys, or conceptual overviews.  
- Example: A survey on AI ecosystems may put a central schematic of “AI core” in the middle, with vision, NLP, and robotics arranged around it.  

---

### 5. Parallel Comparison Layout
- Advantages: Highlights differences across multiple baselines in one glance; works like a visual leaderboard.  
- When to Use: Benchmark-heavy papers such as image generation or translation tasks.  
- Example: A GAN paper might show one row of input images followed by outputs from different baseline methods and then the new model for direct comparison.  

---

### 6. Zoom-In / Hierarchical Layout
- Advantages: Connects the big picture with detailed modules; avoids overwhelming the viewer.  
- When to Use: Systems, robotics, or architectures with both global flow and critical submodules.  
- Example: A robotics system abstract might show the full robot in context, with zoomed-in panels focusing on the neural control module.  

---

### 7. Timeline / Evolution Layout
- Advantages: Shows progression or improvement over time; emphasizes learning or development.  
- When to Use: Iterative training, reinforcement learning, or evolutionary methods.  
- Example: A reinforcement learning paper may illustrate how an agent’s actions evolve over training epochs, from random movement to optimal behavior.  

---

### 8. Layered (Stacked) Layout
- Advantages: Encodes hierarchy clearly; clarifies how abstraction levels build on each other.  
- When to Use: Theoretical models, interpretability studies, or multi-level reasoning.  
- Example: Knowledge graph reasoning models often show data at the bottom, latent spaces in the middle, and predictions at the top.  

---

### 9. Cycle / Loop Layout
- Advantages: Emphasizes feedback, recurrence, or closed-loop interaction.  
- When to Use: Human-in-the-loop systems, active learning, self-training.  
- Example: A human-AI collaboration paper might show a loop where the human annotates data, the model updates, and the new predictions are sent back to the human.  

---

### 10. Conceptual Metaphor Layout
- Advantages: Eye-catching and intuitive; communicates the “big picture” rather than detail.  
- When to Use: Surveys, perspective papers, or conceptual work.  
- Example: A fairness study might depict a scale balancing “accuracy” on one side and “fairness” on the other to illustrate the trade-off.




Ensure you are always writing good compilable LaTeX code. Common mistakes that should be fixed include:
- LaTeX syntax errors (unenclosed math, unmatched braces, etc.).
- Duplicate figure labels or references.
- Unescaped special characters: & % $ # _ {{ }} ~ ^ \\
- Proper table/figure closure.
- Do not hallucinate new citations or any results not in the logs.

When returning final code, place it in fenced triple backticks with 'latex' syntax highlighting.
"""

writeup_prompt = """Your goal is to draw the GA according to the following context:

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
Please also consider which plots should naturally be grouped together as subfigures.

Available plots for the writeup (use these filenames):
```
{plot_list}
```

We also have VLM-based figure descriptions:
```
{plot_descriptions}
```

The paper is written in LaTeX as follows:
```latex
{latex_writeup}
```

Produce the final version of the LaTeX manuscript now, ensuring the paper is coherent, concise, and reports results accurately.
Return the entire file in full, with no unfilled placeholders!
This must be an acceptable complete LaTeX writeup.

Please provide the updated LaTeX code for 'template.tex', wrapped in triple backticks
with "latex" syntax highlighting, like so:

```latex
<UPDATED LATEX CODE>
```
"""


def perform_writeup(
    base_folder,
    no_writing=False,
    num_cite_rounds=20,
    small_model="gpt-4o-2024-05-13",
    big_model="o1-2024-12-17",
    n_writeup_reflections=3,
    page_limit=8,
):
    compile_attempt = 0
    base_pdf_file = osp.join(base_folder, f"{osp.basename(base_folder)}")
    latex_folder = osp.join(base_folder, "latex")

    # Cleanup any previous latex folder and pdf
    if osp.exists(latex_folder):
        shutil.rmtree(latex_folder)
    # if osp.exists(pdf_file):
    #     os.remove(pdf_file)

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

        # Convert them to one big JSON string for context
        combined_summaries_str = json.dumps(loaded_summaries, indent=2)

        # Prepare a new fresh latex folder
        if not osp.exists(osp.join(latex_folder, "template.tex")):
            shutil.copytree(
                "ai_scientist/blank_icml_latex", latex_folder, dirs_exist_ok=True
            )

        writeup_file = osp.join(latex_folder, "template.tex")
        with open(writeup_file, "r") as f:
            writeup_text = f.read()

        # Gather plot filenames from figures/ folder
        figures_dir = osp.join(base_folder, "figures")
        plot_names = []
        if osp.exists(figures_dir):
            for fplot in os.listdir(figures_dir):
                if fplot.lower().endswith(".png"):
                    plot_names.append(fplot)

        # Load aggregator script to include in the prompt
        aggregator_path = osp.join(base_folder, "auto_plot_aggregator.py")
        aggregator_code = ""
        if osp.exists(aggregator_path):
            with open(aggregator_path, "r") as fa:
                aggregator_code = fa.read()
        else:
            aggregator_code = "No aggregator script found."

        if no_writing:
            compile_latex(latex_folder, base_pdf_file + ".pdf")
            return osp.exists(base_pdf_file + ".pdf")

        # Generate VLM-based descriptions but do not overwrite plot_names
        try:
            vlm_client, vlm_model = create_vlm_client("gpt-4o-2024-05-13")
            desc_map = {}
            for pf in plot_names:
                ppath = osp.join(figures_dir, pf)
                if not osp.exists(ppath):
                    continue
                img_dict = {
                    "images": [ppath],
                    "caption": "No direct caption",
                }
                review_data = generate_vlm_img_review(img_dict, vlm_model, vlm_client)
                if review_data:
                    desc_map[pf] = review_data.get(
                        "Img_description", "No description found"
                    )
                else:
                    desc_map[pf] = "No description found"

            # Prepare a string listing all figure descriptions in order
            plot_descriptions_list = []
            for fname in plot_names:
                desc_text = desc_map.get(fname, "No description found")
                plot_descriptions_list.append(f"{fname}: {desc_text}")
            plot_descriptions_str = "\n".join(plot_descriptions_list)
        except Exception:
            print("EXCEPTION in VLM figure description generation:")
            print(traceback.format_exc())
            plot_descriptions_str = "No descriptions available."

        # Construct final prompt for big model, placing the figure descriptions alongside the plot list
        big_model_system_message = writeup_system_message_template.format(
            page_limit=page_limit
        )
        big_client, big_client_model = create_client(big_model)
        with open(writeup_file, "r") as f:
            writeup_text = f.read()

        # TODO

