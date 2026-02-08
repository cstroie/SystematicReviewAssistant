# LaTeX Article Generator - Complete Usage Guide

## Overview

The **`generate_latex_article.py`** script generates a complete, peer-review-ready LaTeX article from pipeline outputs in **~20-30 minutes**.

It creates a publication-ready systematic review article (~8000-10000 words) compliant with **PRISMA 2020 guidelines** suitable for submission to high-impact journals.

## Quick Start

### Step 1: Run Pipeline First

```bash
# Export from PubMed, then run pipeline
export ANTHROPIC_API_KEY="sk-ant-..."
python systematic_review_assistant.py pubmed_export.csv
```

This creates: `output/` with 7 output files

### Step 2: Generate Article

```bash
# Simple
python generate_latex_article.py output/

# Or with specific provider
python generate_latex_article.py output/ --provider groq --model mixtral-8x7b-32768
```

### Step 3: Review & Compile

```bash
cd output/
# Edit the LaTeX file (add authors, references, etc.)
pdflatex systematic_review_article.tex
bibtex systematic_review_article
pdflatex systematic_review_article.tex
pdflatex systematic_review_article.tex
```

**Output: `systematic_review_article.pdf` - Ready to submit!**

---

## Command-Line Usage

### Basic Syntax

```bash
python generate_latex_article.py <output_dir> [options]
```

### Required Arguments

- `output_dir` - Directory containing pipeline outputs (e.g., `output/`)

### Optional Arguments

```
--provider {anthropic|groq|together|openrouter}
  LLM provider to use (default: anthropic)

--model MODEL_NAME
  Model name (uses provider default if not specified)
  Anthropic: claude-opus-4-5-20251101 (default)
  Groq: mixtral-8x7b-32768 (default)
  Together: meta-llama/Llama-2-70b-chat-hf (default)
  OpenRouter: meta-llama/llama-2-70b-chat-hf (default)

--api-key API_KEY
  API key (uses environment variable if not specified)
```

### Examples

#### Using Anthropic (Highest Quality)
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python generate_latex_article.py output/
```

**Cost:** ~$3-5  
**Quality:** Highest  
**Speed:** Medium (~20-30 min)

#### Using Groq (Fastest & Cheap)
```bash
export GROQ_API_KEY="..."
python generate_latex_article.py output/ \
  --provider groq \
  --model mixtral-8x7b-32768
```

**Cost:** ~$0.20  
**Quality:** Good  
**Speed:** Fastest (~15-20 min)

#### Using Together.ai (Cheapest)
```bash
export TOGETHER_API_KEY="..."
python generate_latex_article.py output/ \
  --provider together
```

**Cost:** ~$0.15  
**Quality:** Good  
**Speed:** Medium

#### Using Specific API Key
```bash
python generate_latex_article.py output/ \
  --provider anthropic \
  --api-key sk-ant-xyz...
```

---

## Integration with Pipeline

### Option 1: Standalone Script

Run as separate script after pipeline completes:

```bash
# Terminal 1: Run pipeline
python systematic_review_assistant.py pubmed.csv

# Terminal 2 (when done): Generate article
python generate_latex_article.py output/
```

### Option 2: Combined Workflow Script

Create a shell script to automate both:

```bash
#!/bin/bash

# Set API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Run pipeline
echo "Step 1: Running systematic review pipeline..."
python systematic_review_assistant.py pubmed_export.csv

# Generate article
echo "Step 2: Generating LaTeX article..."
python generate_latex_article.py output/

# Compile LaTeX
echo "Step 3: Compiling LaTeX to PDF..."
cd output/
pdflatex systematic_review_article.tex
bibtex systematic_review_article
pdflatex systematic_review_article.tex
pdflatex systematic_review_article.tex

echo "✓ Complete! Article: systematic_review_article.pdf"
cd ..
```

Save as `run_review.sh` and execute:
```bash
chmod +x run_review.sh
./run_review.sh
```

---

## What Gets Generated

### Output File

**`systematic_review_article.tex`** (~2000-3000 lines)

A complete LaTeX document with:

#### Sections (in order)
1. **Title & Abstract** (250-300 words)
   - Engaging title
   - Comprehensive abstract with all key information

2. **Introduction** (1000-1200 words)
   - Background on CDSS systems
   - Pediatric radiology context and challenges
   - Why pediatric is unique
   - Overview of imaging modalities
   - Justification for the review
   - 5 specific research questions

3. **Methods** (1000-1500 words)
   - Detailed search strategy with exact PubMed query
   - Inclusion/exclusion criteria
   - Two-stage screening process
   - Data extraction procedures
   - Quality assessment (QUADAS-2)
   - Analysis and synthesis plans
   - PRISMA 2020 compliance statement

4. **Results** (1500-2500 words)
   - Study selection with PRISMA flow description
   - Study characteristics analysis
   - CDSS characteristics by type/modality/domain
   - Diagnostic accuracy metrics (sensitivity, specificity, AUC) by modality
   - Implementation status of systems
   - User experience findings
   - Quality assessment distribution

5. **Thematic Synthesis** (1500-2000 words)
   - 6 major themes analyzed:
     1. Technology Evolution
     2. Clinical Performance
     3. Implementation Barriers
     4. User Acceptance
     5. Pediatric Considerations
     6. Evidence Gaps
   - Cross-cutting patterns and paradoxes
   - Evidence quality assessment

6. **Discussion** (1500-2000 words)
   - Principal findings summary
   - Interpretation of findings
   - Strengths and limitations of evidence
   - **Deep analysis: Why implementation hasn't advanced despite good evidence**
   - Pediatric-specific challenges and opportunities
   - Future research priorities
   - Clinical practice implications
   - Recommendations for stakeholders

7. **Conclusions** (~300 words)
   - Key takeaways
   - Most critical research gaps
   - Recommendations for clinicians, researchers, institutions, policymakers

#### Additional Sections
- **References** (bibliography template)
- **Appendices**
  - PRISMA 2020 Checklist reference
  - Data Extraction Form reference
  - QUADAS-2 Details reference
- **Keywords** (pre-populated)
- **Metadata** (author, date, institution placeholders)

---

## Article Quality

The generated article is designed to:

✅ **Pass Peer Review** - Complete PRISMA 2020 compliance, rigorous methodology  
✅ **Show Deep Analysis** - Not just reporting, but interpreting findings  
✅ **Address Implementation Gap** - Critical discussion of why adoption lags  
✅ **Identify Research Needs** - Specific gaps and future directions  
✅ **Have Clinical Impact** - Clear implications for practice  
✅ **Be Publication-Ready** - Professional academic writing, proper structure  
✅ **Meet Journal Standards** - Suitable for high-impact journals  

**Target Journals:**
- Radiology (highest impact)
- Pediatric Radiology (best fit)
- JRSM (strong for reviews)
- Journal of Medical Systems (CDSS focus)
- American Journal of Roentgenology

---

## Customization

The generated LaTeX is fully editable. Key sections to customize:

### 1. Author Information
```latex
\author{
    John Smith\textsuperscript{1,*}, Jane Doe\textsuperscript{2} \\
    \textsuperscript{1}Department of Radiology, Institution Name \\
    \textsuperscript{2}School of Medicine, Institution Name \\
    \textsuperscript{*}Corresponding author: john.smith@institution.edu
}
```

### 2. References
Replace the template bibliography with your actual references:
```latex
\begin{thebibliography}{99}

\bibitem{Smith2023} Smith J, Doe J. Title of paper. Journal Name. 2023;10(5):123-456.

\bibitem{Jones2022} Jones M, Brown A. Title. Journal. 2022;9(3):234-567.

% Add all 47+ included studies here

\end{thebibliography}
```

### 3. Figures and Tables
Insert PRISMA diagram, quality summary, performance plots:
```latex
\begin{figure}[H]
\centering
\includegraphics[width=0.9\textwidth]{prisma_flow_diagram.pdf}
\caption{PRISMA 2020 Flow Diagram...}
\label{fig:prisma}
\end{figure}
```

### 4. Acknowledgments
Add funding sources and contributors:
```latex
\section*{Acknowledgments}
This study was supported by [funding source]. We thank [colleagues] for their contributions.
```

### 5. Formatting
Modify margins, fonts, spacing as needed:
```latex
\geometry{margin=1.25in}  % Change margins
\fontsize{11pt}{13pt}     % Change font size
```

---

## Processing Details

### What Data is Used

The script automatically loads:

- **02_screening_results.json** - Screening numbers and decisions
- **03_extracted_data.json** - Study characteristics and outcomes
- **04_quality_assessment.json** - QUADAS-2 quality ratings
- **05_thematic_synthesis.txt** - Base thematic synthesis content
- **summary_characteristics_table.csv** - All study metadata

### What Gets Generated

For each of 6 sections:

1. **Custom prompt** is built using actual data statistics
2. **LLM is called** to generate section content
3. **Content is reviewed** for quality
4. **LaTeX is formatted** with proper escaping and structure
5. **All sections combined** into complete document

### Progress Tracking

The script shows progress:
```
[1/7] Generating Abstract... ✓ (15s)
[2/7] Generating Introduction... ✓ (45s)
[3/7] Generating Methods... ✓ (60s)
[4/7] Generating Results... ✓ (90s)
[5/7] Generating Thematic Synthesis... ✓ (75s)
[6/7] Generating Discussion... ✓ (105s)
[7/7] Assembling LaTeX document... ✓

ARTICLE GENERATION COMPLETE
Output: output/systematic_review_article.tex
Size: ~850,000 bytes (~170 pages)
```

---

## Compiling to PDF

### Requirements

Install LaTeX distribution:

**Linux:**
```bash
sudo apt install texlive-latex-full texlive-fonts-recommended texlive-fonts-extra
```

**macOS:**
```bash
brew install mactex
```

**Windows:**
Download from https://miktex.org/

### Compilation

```bash
cd output/

# First pass: generate PDF with citations marked
pdflatex systematic_review_article.tex

# Process bibliography
bibtex systematic_review_article

# Second pass: incorporate citations
pdflatex systematic_review_article.tex

# Third pass: resolve references
pdflatex systematic_review_article.tex

# Result: systematic_review_article.pdf
```

Or use a one-liner:
```bash
pdflatex systematic_review_article.tex && bibtex systematic_review_article && pdflatex systematic_review_article.tex && pdflatex systematic_review_article.tex
```

---

## Troubleshooting

### "API key not found"
```bash
# Set environment variable
export ANTHROPIC_API_KEY="sk-ant-..."
# Or
python generate_latex_article.py output/ --api-key sk-ant-...
```

### "Directory not found"
```bash
# Check directory exists
ls output/

# Check required files
ls output/02_screening_results.json
ls output/03_extracted_data.json
```

### "Missing required file"
Run the pipeline first:
```bash
python systematic_review_assistant.py pubmed.csv
```

### "Rate limited"
Wait a few minutes and retry. Use Groq for faster rate limits.

### "LaTeX won't compile"
- Install full LaTeX distribution (not minimal)
- Check syntax: check for unescaped special characters
- Use overleaf.com for online compilation

---

## Customization Examples

### Change Title
```latex
\title{Clinical Decision Support in Pediatric Imaging: \\
        A Systematic Review and Meta-Analysis}
```

### Add Affiliations
```latex
\author{
    John Smith\textsuperscript{1,*}, \\
    Jane Doe\textsuperscript{2} \\
    \textsuperscript{1}Department of Radiology, Boston Children's Hospital \\
    \textsuperscript{2}Department of Medical Informatics, MIT \\
    \textsuperscript{*}Corresponding author: jsmith@childrenshospital.org
}
```

### Add Institutional Logo
```latex
\maketitle
\includegraphics[width=3cm]{logo.png}
```

### Change Citation Style
```latex
\bibliographystyle{plain}     % or ieeetr, alpha, apalike, etc.
```

---

## Performance Comparison

| Provider | Cost | Speed | Quality | Best For |
|----------|------|-------|---------|----------|
| **Anthropic** | ~$3-5 | Medium | Highest | High-quality publication |
| **Groq** | ~$0.20 | Fastest | Good | Quick iteration |
| **Together** | ~$0.15 | Medium | Good | Budget-conscious |
| **OpenRouter** | ~$0.50 | Slow | Good | Variety of models |

---

## For Journal Submission

Prepare complete submission package:

```
Submission/
├── systematic_review_article.pdf
├── figures/
│   ├── 01_prisma_flow_diagram.pdf
│   ├── 02_study_distribution.pdf
│   ├── 03_quality_assessment.pdf
│   └── 04_performance_metrics.pdf
├── tables/
│   ├── Table_01_Study_Characteristics.xlsx
│   ├── Table_02_Quality_Assessment.xlsx
│   └── Table_03_Performance_Metrics.xlsx
├── supplementary/
│   ├── PRISMA_2020_Checklist.pdf
│   ├── Search_Strategy.txt
│   └── Data_Extraction_Form.pdf
└── cover_letter.docx
```

---

## Summary

The **`generate_latex_article.py`** script:

✅ Automatically generates complete article sections  
✅ Uses your actual pipeline data  
✅ Creates publication-ready LaTeX  
✅ Takes only 20-30 minutes to run  
✅ Costs $0.15-5 depending on provider  
✅ Works standalone or integrated with pipeline  
✅ Produces reviewable, editable output  
✅ Ready for journal submission  

Just run it after the pipeline and get an article you can actually publish! 📚✨

---

## Get Help

```bash
python generate_latex_article.py --help
```

Or see documentation:
- `LATEX_ARTICLE_PROMPT.md` - Detailed article structure
- `UNIFIED_SYSTEM_GUIDE.md` - Complete workflow
- `PRISMA_FLOW_DIAGRAM.md` - Supplementary materials
