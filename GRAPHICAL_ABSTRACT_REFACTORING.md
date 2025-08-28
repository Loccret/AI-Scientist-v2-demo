# Graphical Abstract Generator Refactoring Summary

## Overview
The `perform_graph_abstract.py` file has been completely refactored to follow the architecture and CLI behavior of `perform_writeup.py`, providing a consistent interface for generating graphical abstracts for research papers.

## Key Changes Made

### 1. **Architecture Alignment**
- Followed the same modular structure as `perform_writeup.py`
- Used similar parameter patterns and function signatures
- Maintained consistent error handling and logging patterns

### 2. **Core Function Refactoring**
- **`perform_graph_abstract()`**: Main function similar to `perform_writeup()`
  - Takes `base_folder`, `no_generation`, `model`, `big_model`, `n_reflections` parameters  
  - Follows same workflow: load data → generate content → reflect/improve → compile
  - Returns boolean success indicator

### 3. **LaTeX Compilation**
- **`compile_tikz_standalone()`**: Specialized for standalone TikZ documents
  - Replaces the multi-step LaTeX compilation with streamlined pdflatex-only approach
  - Handles standalone document class compilation requirements
  - Proper error handling and output capture

### 4. **Prompt Engineering**
- **`graphical_abstract_system_message`**: Comprehensive system prompt
  - Detailed instructions for creating publication-ready graphical abstracts
  - Multiple layout pattern options (Linear Pipeline, Before/After, 2x2 Grid, etc.)
  - Clear deliverables and technical requirements

- **`graphical_abstract_prompt`**: Template for contextual prompt
  - Uses same data sources as writeup (idea text, summaries, plots, VLM descriptions)
  - Formatted for TikZ/LaTeX generation

### 5. **CLI Interface**
- **Argument Parser**: Mirrors `perform_writeup.py` structure
  - `--folder`: Project folder (required)
  - `--no-generation`: Compile-only mode  
  - `--model`: Small model for VLM descriptions
  - `--big-model`: Large model for generation
  - `--reflections`: Number of improvement iterations

### 6. **File Organization**
- Creates `graphical_abstract/` subfolder in project directory
- Generates `graphical_abstract.tex` as standalone document
- Produces PDFs with versioned naming (`_0.pdf`, `_1.pdf`, `_final.pdf`)

### 7. **Integration Features**
- **VLM Integration**: Uses existing VLM system for plot descriptions
- **Data Loading**: Loads same experimental summaries and research context
- **Reflection Loop**: Iterative improvement system with syntax checking
- **Error Handling**: Comprehensive exception handling and logging

## Usage Examples

### Basic Generation
```bash
python ai_scientist/perform_graph_abstract.py --folder /path/to/project
```

### Custom Models and Reflections  
```bash
python ai_scientist/perform_graph_abstract.py \
    --folder /path/to/project \
    --model gpt-4o-2024-05-13 \
    --big-model o1-2024-12-17 \
    --reflections 3
```

### Compile Only Mode
```bash
python ai_scientist/perform_graph_abstract.py \
    --folder /path/to/project \
    --no-generation
```

## Technical Improvements

1. **Standalone Document Approach**: Uses LaTeX `standalone` class for self-contained TikZ documents
2. **Reduced Compilation Complexity**: No bibtex or multiple LaTeX runs needed
3. **Modular Design**: Clean separation between data loading, generation, and compilation
4. **Consistent Error Handling**: Matches patterns used in other AI Scientist modules
5. **Flexible Model Selection**: Support for different LLM backends through existing infrastructure

## Output Structure
```
project_folder/
├── graphical_abstract/
│   ├── graphical_abstract.tex    # Standalone TikZ document
│   ├── graphical_abstract.aux    # LaTeX auxiliary files
│   └── ...
├── project_name_graphical_abstract_0.pdf
├── project_name_graphical_abstract_1.pdf  
└── project_name_graphical_abstract_final.pdf
```

The refactored module now provides a professional-grade tool for generating publication-ready graphical abstracts that integrates seamlessly with the existing AI Scientist workflow.
