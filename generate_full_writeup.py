#!/usr/bin/env python3
"""
Generate a complete academic paper by writing it section by section.
This overcomes token limits by generating each section separately.
"""

import os
import sys
import json
import argparse
from ai_scientist.llm import get_response_from_llm, create_client

def load_experiment_data(experiment_dir):
    """Load all necessary data for paper generation."""
    # Load idea
    with open(os.path.join(experiment_dir, "idea.json"), "r") as f:
        idea = json.load(f)
    
    # Load experiment summaries from logs
    summaries = {}
    logs_dir = os.path.join(experiment_dir, "logs")
    if os.path.exists(logs_dir):
        for log_file in os.listdir(logs_dir):
            if log_file.endswith('.json'):
                try:
                    with open(os.path.join(logs_dir, log_file), "r") as f:
                        log_data = json.load(f)
                        summaries[log_file] = log_data
                except:
                    pass
    
    # Load any experiment results or data files
    data_dir = os.path.join(experiment_dir, "data")
    data_files = {}
    if os.path.exists(data_dir):
        for data_file in os.listdir(data_dir):
            if data_file.endswith(('.json', '.txt', '.csv')):
                try:
                    file_path = os.path.join(data_dir, data_file)
                    with open(file_path, "r") as f:
                        if data_file.endswith('.json'):
                            data_files[data_file] = json.load(f)
                        else:
                            data_files[data_file] = f.read()
                except:
                    pass
    
    # Load plot aggregator code
    agg_file = os.path.join(experiment_dir, "auto_plot_aggregator.py")
    if os.path.exists(agg_file):
        with open(agg_file, "r") as f:
            aggregator_code = f.read()
    else:
        aggregator_code = "# No aggregator code available"
    
    # List available plots
    figures_dir = os.path.join(experiment_dir, "figures")
    plot_list = []
    if os.path.exists(figures_dir):
        for file in os.listdir(figures_dir):
            if file.endswith(('.png', '.pdf', '.jpg', '.jpeg')):
                plot_list.append(file)
    
    # Load cached citations if available
    citations = {}
    citations_file = os.path.join(experiment_dir, "cached_citations.bib")
    if os.path.exists(citations_file):
        with open(citations_file, "r") as f:
            citations_content = f.read()
    else:
        citations_content = "No cached citations available"
    
    return idea, summaries, aggregator_code, plot_list, data_files, citations_content

def generate_section(client, model, section_name, context, current_latex=""):
    """Generate a specific section of the paper with full context of previous sections."""
    
    section_prompts = {
        "header": """Generate the complete LaTeX document header and abstract. Include:
- \\documentclass[12pt]{article}
- All necessary packages (amsmath, graphicx, natbib, hyperref, etc.)
- Title: "SO-NEAT: Self-Organizing NeuroEvolution of Augmenting Topologies"
- Author and affiliation placeholders
- Abstract (150-200 words) summarizing the work, methods, and key findings
- \\begin{document}, \\maketitle

Return the complete LaTeX header and abstract section.""",

        "introduction": """Generate the Introduction section. Include:
- Motivation for combining self-organization with NEAT
- Background on neuroevolution and plasticity
- Key contributions and novelty of SO-NEAT
- Paper organization overview
- Proper citations from the available references

Return ONLY the LaTeX code for the Introduction section with \\section{Introduction} and \\label{sec:intro}.""",

        "related_work": """Generate the Related Work section. Include:
- Overview of NEAT algorithm and its extensions
- Previous work on neural plasticity in evolution
- Self-organization in neural networks
- Gap analysis motivating SO-NEAT approach
- Comprehensive citations from available references

Return ONLY the LaTeX code for the Related Work section with \\section{Related Work} and \\label{sec:related}.""",

        "methods": """Generate the Methods section describing SO-NEAT algorithm. Include:
- Detailed algorithm description
- Homeostatic plasticity mechanisms
- Utility-based structural changes
- Multi-objective selection criteria
- Mathematical formulations and pseudocode
- Integration with NEAT framework

Use the experimental data and plot generation code to understand the implementation. Return ONLY the LaTeX code for Methods section with \\section{Methods} and \\label{sec:methods}.""",

        "experiments": """Generate the Experiments and Results section. Include:
- Experimental setup and benchmark problems
- Performance metrics and evaluation criteria
- Results presentation with ALL available figure references
- Statistical analysis and comparisons
- Discussion of findings from the experimental data

IMPORTANT: Reference ALL available plots using \\includegraphics and proper captions. Use the plot generation code to understand what each figure shows. Return ONLY the LaTeX code for Experiments section with \\section{Experiments} and \\label{sec:experiments}.""",

        "conclusion": """Generate the Discussion and Conclusion sections. Include:
- Analysis of experimental results and their implications
- Limitations of the current approach
- Future research directions
- Overall conclusions about SO-NEAT's effectiveness
- Bibliography commands: \\bibliographystyle{iclr2025} \\bibliography{references}
- Document closing: \\end{document}

Return ONLY the LaTeX code for Discussion, Conclusion, and document ending."""
    }

    # Build the system message with full context and previous sections
    system_message = f"""You are an expert academic writer generating a high-quality 4-page ICBINB workshop paper about SO-NEAT (Self-Organizing NeuroEvolution of Augmenting Topologies).

COMPLETE EXPERIMENTAL CONTEXT:
{context}

PAPER WRITTEN SO FAR (maintain consistency and flow):
{current_latex}

YOUR TASK: {section_prompts[section_name]}

CRITICAL REQUIREMENTS:
1. Use the experimental data and summaries to write accurate, data-driven content
2. Reference ALL available figures appropriately in the text
3. Maintain consistency with previously written sections
4. Use proper academic citations from the available references
5. Write in a scholarly, technical tone appropriate for a machine learning venue
6. Ensure the content flows naturally from the previous sections
7. Include specific results and findings from the experimental data
8. Return ONLY the requested LaTeX code with no markdown formatting or explanations"""

    prompt = f"Generate the {section_name} section based on the experimental context and data provided. Ensure it integrates seamlessly with the existing document structure."

    response, _ = get_response_from_llm(
        prompt=prompt,
        client=client,
        model=model,
        system_message=system_message,
        temperature=0.2  # Lower temperature for more focused, consistent output
    )
    
    # Clean the response to extract just the LaTeX code
    if "```latex" in response:
        import re
        latex_match = re.search(r"```latex\s*(.*?)\s*```", response, re.DOTALL)
        if latex_match:
            response = latex_match.group(1).strip()
    elif "```" in response:
        # Remove any code block markers
        response = re.sub(r"```\w*\n?", "", response).strip()
    
    return response

def combine_sections(sections, experiment_dir):
    """Combine all sections into a complete LaTeX document."""
    
    # Read the blank template to get the proper header structure
    blank_template_path = os.path.join(experiment_dir, "latex", "template.tex")
    
    # Start with a proper LaTeX document structure
    full_document = sections["header"]
    
    # Add each section
    for section in ["introduction", "related_work", "methods", "experiments", "conclusion"]:
        if section in sections:
            full_document += "\n\n" + sections[section]
    
    # Write the complete document
    output_path = os.path.join(experiment_dir, "latex", "template.tex")
    with open(output_path, "w") as f:
        f.write(full_document)
    
    print(f"✅ Complete paper written to: {output_path}")
    return output_path

def main():
    parser = argparse.ArgumentParser(description="Generate complete academic paper section by section")
    parser.add_argument("experiment_dir", help="Path to experiment directory")
    parser.add_argument("--model", default="deepseek-reasoner", help="Model to use for generation")
    args = parser.parse_args()
    
    print(f"🚀 Generating complete paper for: {args.experiment_dir}")
    print(f"📝 Using model: {args.model}")
    
    # Load experiment data
    idea, summaries, aggregator_code, plot_list, data_files, citations_content = load_experiment_data(args.experiment_dir)
    
    # Create comprehensive context string with all experimental data
    context = f"""
RESEARCH IDEA:
Name: {idea.get('Name', 'SO-NEAT')}
Description: {idea.get('Description', '')}
Full Idea Text: {idea.get('idea_text', '')}

EXPERIMENTAL DATA:
Available plots: {', '.join(plot_list)}

Experiment summaries: {json.dumps(summaries, indent=2) if summaries else 'No summaries available'}

Data files: {json.dumps(data_files, indent=2) if data_files else 'No data files available'}

PLOT GENERATION CODE:
{aggregator_code}

AVAILABLE CITATIONS:
{citations_content}

FIGURES AVAILABLE FOR REFERENCE:
{chr(10).join(f"- {plot}" for plot in plot_list)}
"""
    
    # Create client
    client, model = create_client(args.model)
    
    # Generate each section
    sections = {}
    current_latex = ""
    
    section_order = ["header", "introduction", "related_work", "methods", "experiments", "conclusion"]
    
    for section in section_order:
        print(f"📝 Generating {section} section...")
        print(f"📏 Current document length: {len(current_latex)} characters")
        try:
            sections[section] = generate_section(client, model, section, context, current_latex)
            current_latex += "\n\n" + sections[section]
            print(f"✅ {section} section completed ({len(sections[section])} chars)")
        except Exception as e:
            print(f"❌ Error generating {section}: {e}")
            continue
    
    # Combine all sections
    print("🔗 Combining sections into complete document...")
    output_path = combine_sections(sections, args.experiment_dir)
    
    print("🎉 Complete paper generation finished!")
    print(f"📄 Output: {output_path}")

if __name__ == "__main__":
    main()
