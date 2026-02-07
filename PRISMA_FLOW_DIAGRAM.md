# PRISMA 2020 Flow Diagram Generator

Create publication-ready PRISMA flow diagrams automatically from your screening results.

## What This Does

Generates PRISMA 2020 flow diagrams compliant with the official PRISMA 2020 Statement in multiple formats:
- **SVG** - Scalable vector (best for papers)
- **HTML** - Interactive web version
- **PNG** - Raster image (via online converter)

## Quick Start

### 1. Run the Pipeline First

```bash
python cdss_lit_review_pipeline_v3.py pubmed_export.csv
```

This creates: `lit_review_output/02_screening_results.json`

### 2. Generate the Diagram

```bash
python prisma_flow_diagram.py lit_review_output/02_screening_results.json
```

### 3. Use in Your Paper

The diagram is ready to insert into your manuscript!

## Diagram Structure (PRISMA 2020)

The generated diagram follows official PRISMA 2020 format with 4 phases:

```
┌─────────────────────────────────────────────────────────┐
│              IDENTIFICATION                             │
├─────────────────────────────────────────────────────────┤
│  Records identified (n = 487)                           │
│  [PubMed]                                               │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              SCREENING                                  │
├──────────────────────┬──────────────────────────────────┤
│  Records screened    │  Records excluded                │
│  (n = 487)           │  (n = 410)                       │
└──────────┬───────────┴──────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────┐
│              ELIGIBILITY                                │
├──────────────────────┬──────────────────────────────────┤
│  Full-text articles  │  Articles excluded               │
│  assessed            │  (n = 30)                        │
│  (n = 77)            │  - Not clinical (n=12)           │
│                      │  - No outcomes (n=18)            │
└──────────┬───────────┴──────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────┐
│              INCLUSION                                  │
├─────────────────────────────────────────────────────────┤
│  Studies included in qualitative synthesis              │
│  (n = 47)                                               │
│                                                         │
│  Studies included in quantitative synthesis             │
│  (meta-analysis) (n = 35)                               │
└─────────────────────────────────────────────────────────┘
```

## Output Files

After running the script, you'll get:

```
lit_review_output/
├── prisma_flow_diagram.svg      ← Vector (best for papers)
├── prisma_flow_diagram.html     ← Interactive web version
└── 02_screening_results.json    ← (input data)
```

### SVG Format (Recommended)

✅ **Best for publications**
- Scalable to any size
- No quality loss when resizing
- Small file size (~10KB)
- Can edit in Adobe Illustrator, Inkscape, PowerPoint

**Insert in Word/Google Docs:**
1. Insert → Image → Choose `prisma_flow_diagram.svg`
2. Right-click → Format Picture
3. Adjust size as needed

### HTML Format

✅ **Best for viewing/sharing**
- Interactive visualization
- Built-in summary statistics
- Click buttons to download
- Can view in any browser
- Print to PDF directly

**Usage:**
1. Open `prisma_flow_diagram.html` in web browser
2. View interactive diagram
3. Click "Download as SVG" or print
4. Share with collaborators

### PNG Format

⚠️ **Requires conversion tool**

**Option 1: Online Converter**
1. Go to: https://convertio.co/svg-png/
2. Upload `prisma_flow_diagram.svg`
3. Convert to PNG
4. Download

**Option 2: Inkscape (Free Software)**
```bash
inkscape prisma_flow_diagram.svg --export-png=diagram.png
```

**Option 3: ImageMagick**
```bash
convert prisma_flow_diagram.svg diagram.png
```

## Usage Examples

### Generate Both SVG and HTML

```bash
python prisma_flow_diagram.py lit_review_output/02_screening_results.json --format all
```

### Generate Only SVG

```bash
python prisma_flow_diagram.py lit_review_output/02_screening_results.json --format svg
```

### Generate Only HTML

```bash
python prisma_flow_diagram.py lit_review_output/02_screening_results.json --format html
```

### Specify Output Directory

```bash
python prisma_flow_diagram.py lit_review_output/02_screening_results.json --output-dir ./figures/
```

## Understanding the Numbers

The diagram pulls numbers directly from your screening results:

### IDENTIFICATION Phase
- **Records identified**: Total articles from PubMed search
- **Source**: PubMed, trial registers, other sources

### SCREENING Phase
- **Records screened**: Articles with title/abstract available
- **Records excluded**: Clearly not relevant (from LLM screening)

### ELIGIBILITY Phase
- **Full-text articles assessed**: Articles retrieved for detailed review
- **Articles excluded**: Not meeting criteria after full-text review
- **Reasons**: Why articles were excluded (optional detail)

### INCLUSION Phase
- **Qualitative synthesis**: All studies in final review
- **Quantitative synthesis**: Studies with data for meta-analysis (if applicable)

## Customization

### Edit the HTML Directly

The HTML file is fully editable. You can:

1. **Change title:**
   ```html
   <h1>PRISMA 2020 Flow Diagram - Pediatric Radiology CDSS Review</h1>
   ```

2. **Add more details in summary:**
   - Edit HTML in any text editor
   - Add more summary items as needed

3. **Change colors:**
   - Find the CSS color codes
   - Modify hex values (e.g., `#2C3E50` to your color)

### Edit the SVG (Advanced)

SVG files can be edited in:
- **Inkscape** (free)
- **Adobe Illustrator** (paid)
- Any text editor (since SVG is XML)

**Example: Change a label in SVG**
1. Open `prisma_flow_diagram.svg` in text editor
2. Find the text you want to change
3. Edit the text between `<text>` tags
4. Save and re-open in browser

## Data Source: Screening Results JSON

The diagram automatically reads from `02_screening_results.json`:

```json
[
  {
    "pmid": "12345678",
    "decision": "INCLUDE",
    "confidence": 0.95,
    "reasoning": "..."
  },
  {
    "pmid": "87654321",
    "decision": "EXCLUDE",
    "confidence": 0.92,
    "reasoning": "..."
  },
  {
    "pmid": "11111111",
    "decision": "UNCERTAIN",
    "confidence": 0.65,
    "reasoning": "..."
  }
]
```

**Automatic calculation:**
- INCLUDE → Studies in final review
- EXCLUDE → Excluded at screening
- UNCERTAIN → Goes to full-text review

## PRISMA 2020 Compliance

This diagram generator is compliant with **PRISMA 2020** requirements:

✅ Four phases: Identification → Screening → Eligibility → Inclusion  
✅ Clear numbering at each stage  
✅ Shows exclusions at screening and eligibility phases  
✅ Option to show exclusion reasons  
✅ Professional formatting  
✅ Publication-ready quality  

**Reference:** https://www.prisma-statement.org/

## Including in Your Paper

### Methods Section

> "Study selection was conducted in two stages. In the first stage, two independent reviewers screened titles and abstracts of all identified records using [TOOL]. In the second stage, full texts of potentially eligible studies were assessed against predetermined inclusion/exclusion criteria. Disagreements were resolved through discussion or consultation with a third reviewer. The screening process and study selection results are presented in the PRISMA 2020 flow diagram."

### Figure Caption

> "PRISMA 2020 flow diagram showing the systematic review process. PubMed search identified [X] records. After deduplication and screening, [Y] full-text articles were assessed for eligibility. [Z] studies met inclusion criteria and were included in the qualitative synthesis, with [W] studies included in the quantitative synthesis (meta-analysis)."

## Troubleshooting

### "File not found"

```bash
# Check the correct path
ls -la lit_review_output/02_screening_results.json

# Make sure pipeline has finished
python cdss_lit_review_pipeline_v3.py pubmed.csv
```

### "JSON parsing error"

The screening results file might be corrupted. Check:
```bash
# View the file
cat lit_review_output/02_screening_results.json

# Validate JSON
python -m json.tool lit_review_output/02_screening_results.json
```

### "Numbers don't match my manual count"

Possible causes:
- Manual count missed some articles
- Some articles have no PMID or title
- LLM screening marked differently than expected

**Solution:** Review `02_screening_results.json` and check decisions for each PMID.

### "Can't open SVG in PowerPoint"

Try these:
1. Right-click → Edit with Inkscape → Export to EMF → Insert EMF in PowerPoint
2. Use HTML version instead (print to PDF then insert image)
3. Convert to PNG first (see PNG conversion section)

## Advanced: Manual Numbers

If you want to manually create a diagram with specific numbers:

```python
from prisma_flow_diagram import DiagramNumbers, PRISMADiagramHTML

# Create custom numbers
numbers = DiagramNumbers(
    records_identified=487,
    records_screened=487,
    records_excluded=410,
    full_text_retrieved=77,
    full_text_excluded=30,
    full_text_exclude_reasons={
        'Not clinical CDSS': 12,
        'No clinical outcomes': 18
    },
    studies_included_qualitative=47,
    studies_included_quantitative=35
)

# Generate diagram
generator = PRISMADiagramHTML(numbers)
html = generator.generate()

# Save
with open('prisma_diagram.html', 'w') as f:
    f.write(html)
```

## Complete Workflow

```bash
# 1. Run literature search
python cdss_lit_review_pipeline_v3.py pubmed_export.csv

# 2. Generate PRISMA diagram
python prisma_flow_diagram.py lit_review_output/02_screening_results.json --format all

# 3. View results
open lit_review_output/prisma_flow_diagram.html

# 4. Use in paper
# - Insert SVG into Word/Google Docs
# - Or export HTML to PDF
# - Or convert to PNG via online tool
```

## Files to Submit with Your Paper

When publishing your systematic review, include:

1. ✅ **PRISMA Flow Diagram** (from this tool)
2. ✅ **PRISMA Checklist** (https://www.prisma-statement.org/)
3. ✅ **Supplementary Table 1** (summary_characteristics_table.csv)
4. ✅ **Search Strategy** (exact PubMed query)
5. ✅ **Protocol** (registered in PROSPERO)

## Resources

- **PRISMA 2020 Statement:** https://www.prisma-statement.org/
- **PRISMA Checklist:** https://www.prisma-statement.org/
- **PROSPERO Registration:** https://www.crd.york.ac.uk/prospero/
- **Flow Diagram Template:** https://www.prisma-statement.org/

## Support

If you encounter issues:

1. **Check input file format:**
   ```bash
   head lit_review_output/02_screening_results.json
   ```

2. **Validate JSON:**
   ```bash
   python -m json.tool lit_review_output/02_screening_results.json > /dev/null && echo "Valid JSON"
   ```

3. **Check Python version:**
   ```bash
   python --version  # Should be 3.6+
   ```

## Summary

The PRISMA flow diagram generator:

✅ Automatically reads screening results from pipeline  
✅ Generates publication-ready diagrams  
✅ Compliant with PRISMA 2020 guidelines  
✅ Available in multiple formats (SVG, HTML, PNG)  
✅ No additional packages needed  
✅ Fully customizable  

Just run it and insert the diagram into your paper! 🎯

---

**Questions?** See examples in the output directory or check PRISMA guidelines online.
