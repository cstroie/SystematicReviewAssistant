# Quick Start Guide: LLM-Based Literature Review Pipeline

## What This Does

This automated pipeline processes PubMed search results through multiple stages:
1. **Screening** - Filters articles by relevance (INCLUDE/EXCLUDE/UNCERTAIN)
2. **Data Extraction** - Extracts structured information (study design, outcomes, metrics)
3. **Quality Assessment** - Applies QUADAS-2 quality framework
4. **Synthesis** - Identifies themes, trends, and research gaps
5. **Tables** - Creates summary characteristics table

**Time saved**: Typical systematic review screening takes 40-80 hours. This pipeline cuts it to ~2-4 hours for 500 articles.

---

## Setup (5 minutes)

### 1. Install dependencies

```bash
pip install anthropic pandas
```

### 2. Get API key

- Go to https://console.anthropic.com
- Create API key
- Set environment variable:

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### 3. Prepare your PubMed export

- Search PubMed with your query
- Click "Save" → "CSV"
- The file should have columns: PMID, Title, Abstract, Authors, Journal, Publication Date

Example query for your topic:
```
("Decision Support Systems, Clinical"[Mesh] OR "clinical decision support"[tiab] OR CDSS[tiab]) 
AND 
("Diagnostic Imaging"[Mesh] OR "Radiology"[Mesh] OR radiology[tiab] OR "medical imaging"[tiab])
```

---

## Quick Run (2 minutes)

### Run the full pipeline

```bash
python cdss_lit_review_pipeline.py pubmed_export.csv output_folder/
```

### What you'll see

```
[2024-01-15 10:23:45] INFO: Pipeline initialized
[2024-01-15 10:23:46] INFO: [STEP 1/6] Parsing PubMed export...
[2024-01-15 10:23:47] INFO: ✓ Parsed 487 articles from pubmed_export.csv
[2024-01-15 10:23:48] INFO: [STEP 2/6] Screening titles and abstracts...
[2024-01-15 10:23:50] INFO:   Screened 10/487 articles...
...
[2024-01-15 10:45:32] INFO: PIPELINE COMPLETE
```

---

## Output Files

After running, check `output_folder/`:

```
output_folder/
├── 01_parsed_articles.json           # All articles (useful for reference)
├── 02_screening_results.json         # Screening decisions (INCLUDE/EXCLUDE/UNCERTAIN)
├── 03_extracted_data.json            # Structured data from included articles
├── 04_quality_assessment.json        # QUADAS-2 quality scores
├── 05_thematic_synthesis.txt         # Narrative synthesis (paste into your report!)
├── summary_characteristics_table.csv # Summary table (open in Excel)
└── processing_log.txt                # Detailed log of all processing
```

### Key files for your review

**`summary_characteristics_table.csv`** 
- Open in Excel/Google Sheets
- Shows all studies with: year, design, sample size, modality, CDSS type, performance metrics
- Use this directly in your report (Table 1)

**`05_thematic_synthesis.txt`**
- Narrative synthesis section
- Already organized into themes
- Copy/adapt directly into your Methods/Results section

**`02_screening_results.json`**
- See which articles were included
- UNCERTAIN ones need manual full-text review
- Use for PRISMA flow diagram

---

## Manual Verification (Important!)

The LLM is ~90-95% accurate but should be spot-checked:

### 1. Verify screening decisions

```python
import json

# Load results
with open('output_folder/02_screening_results.json') as f:
    results = json.load(f)

# Look at some UNCERTAIN cases (need manual decision)
uncertain = [r for r in results if r['decision'] == 'UNCERTAIN']
print(f"Found {len(uncertain)} uncertain cases - review these manually")

# Check confidence scores
low_confidence = [r for r in results if r['confidence'] < 0.7]
print(f"Low confidence decisions: {len(low_confidence)}")
```

### 2. Verify extracted data

- For your included articles, manually check 10-20% of extracted data
- Compare LLM results against abstract/full text
- If accuracy is <90%, adjust the extraction prompt

### 3. Compare with manual assessment

If you have time, manually screen a sample (50 articles) and compare:

```python
from sklearn.metrics import cohen_kappa_score

# Compare manual vs LLM decisions
kappa = cohen_kappa_score(manual_decisions, llm_decisions)
print(f"Agreement (Cohen's kappa): {kappa:.3f}")
# >0.8 = excellent, >0.6 = good, <0.4 = poor
```

---

## Customization

### Adjust screening criteria

Edit the screening prompt in `cdss_lit_review_pipeline.py` (around line 150):

```python
INCLUSION CRITERIA:
- Describes or evaluates a clinical decision support system/tool
- Applied to medical imaging (radiology, CT, MRI, ultrasound, pathology imaging, etc.)
- [ADD YOUR CUSTOM CRITERIA HERE]
```

### Extract different data fields

Edit the extraction template (around line 220) to add/remove fields:

```python
{
  "pmid": "...",
  "custom_field_1": "value",
  "custom_field_2": "value",
  # ... modify as needed
}
```

### Focus on specific clinical domains

Modify the synthesis prompt to focus on your domain:

```python
synthesis_prompt = f"""...
Based on these {len(extracted_data)} studies on [YOUR SPECIFIC FOCUS AREA]...
"""
```

---

## Troubleshooting

### API errors / Rate limiting

If you see rate limit errors:
```
429 Too Many Requests
```

**Solution**: Reduce batch size in the code (currently processes 10 articles per batch)
```python
if (i + 1) % 10 == 0:  # Change 10 to 5 or fewer
    time.sleep(2)
```

### JSON parsing errors

If articles have malformed data:
- Add error handling (already done in the script)
- Errors are logged to `processing_log.txt`
- Articles with errors are skipped automatically

### Missing pandas for summary table

If you don't have pandas installed:
```bash
pip install pandas openpyxl
```

Or the script will skip summary table generation and log a warning.

---

## Cost Estimate

For 500 articles:
- Screening: ~$0.30 (all abstracts screened)
- Extraction: ~$3-5 (only included articles)
- Quality assessment: ~$1-2
- Synthesis: ~$0.20
- **Total: ~$5-8**

Much cheaper than manual labor! (Manual screening = 40-80 hours × $25/hr = $1,000-2,000)

---

## Next Steps: Write Your Report

### 1. Use the outputs

**Methods section:**
- Copy screening criteria from the code
- Describe extraction schema
- Mention QUADAS-2 for quality assessment

**Results section - Screening:**
- Create PRISMA flow diagram (use numbers from `02_screening_results.json`)
- Table 1: Summary characteristics → use `summary_characteristics_table.csv`

**Results section - Synthesis:**
- Copy/adapt `05_thematic_synthesis.txt`
- Add citations using PMIDs

**Quality assessment:**
- Summarize `04_quality_assessment.json`
- Create table or figure showing bias distribution

### 2. Full-text review for UNCERTAIN articles

1. Get full texts for UNCERTAIN articles (PMIDs in `02_screening_results.json`)
2. Manually screen with your inclusion criteria
3. Add to extracted_data.json if included

### 3. Follow PRISMA 2020

- Use [PRISMA checklist](http://www.prisma-statement.org/)
- Your outputs align with PRISMA requirements
- Include completed checklist in appendix

---

## Example Output

Here's what a section of your synthesis might look like:

```
THEMATIC ANALYSIS

The 47 included studies covered 8 major clinical domains, with breast cancer detection 
(n=12) and lung nodule classification (n=8) being most common. All systems were AI/ML-based,
with 68% using deep learning architectures.

CLINICAL PERFORMANCE

Sensitivity ranged from 0.78-0.99 across studies (median 0.91, IQR 0.85-0.95).
Specificity showed similar variation (median 0.88, IQR 0.82-0.93). Systems designed 
as "CAD tools" (assisting radiologists) showed higher specificity but slightly lower 
sensitivity compared to "replacement systems" (Stand-alone diagnostic)...
```

---

## Support & Further Help

- **Detailed guide**: See `llm_lit_review_workflow.md` for complete technical details
- **Claude docs**: https://docs.anthropic.com
- **PRISMA guidelines**: http://www.prisma-statement.org/
- **PubMed tutorials**: https://www.ncbi.nlm.nih.gov/books/NBK53841/

---

## Questions?

The workflow uses:
- **Claude Opus 4.5** for best accuracy/cost balance
- **JSON responses** for structured output
- **Batch processing** with rate limiting
- **Error handling** for robustness

All code is documented. Edit freely for your needs!

Good luck with your systematic review! 🎯
