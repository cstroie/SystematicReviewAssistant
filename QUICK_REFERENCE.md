# Quick Reference: CDSS in Pediatric Radiology Query

## Copy-Paste Ready Queries

### 🎯 RECOMMENDED: Balanced Query (Best for most reviews)

```
("clinical decision support" OR CDSS OR "computer-aided detection" OR "machine learning")
AND
(radiology OR "diagnostic imaging" OR CT OR MRI OR ultrasound OR radiography OR "x-ray")
AND
(child* OR pediatric* OR paediatric* OR infant* OR adolescent*)
AND
(implement* OR evaluat* OR propos* OR develop* OR "user experience" OR usability OR acceptab* OR clinical)
```

**Expected Results:** 150-400 articles  
**Quality:** High relevance  
**Effort:** Moderate screening needed

---

### 🔍 RESTRICTIVE: High Precision Query (Fewer but more relevant)

```
("clinical decision support" OR CDSS)
AND
(CT OR MRI OR ultrasound OR radiology)
AND
(pediatric* OR paediatric* OR child*)
AND
(implement* OR evaluate* OR clinical outcome* OR "diagnostic accuracy")
```

**Expected Results:** 50-150 articles  
**Quality:** Very high relevance  
**Effort:** Minimal screening

---

### 🌐 COMPREHENSIVE: High Sensitivity Query (Find all relevant articles)

```
("Decision Support Systems, Clinical"[Mesh] OR CDSS OR "machine learning" OR "artificial intelligence" OR "deep learning")
AND
(radiology OR "diagnostic imaging" OR imaging)
AND
(child* OR pediatric* OR infant* OR adolescent*)
```

**Expected Results:** 300-800+ articles  
**Quality:** Moderate (more irrelevant items)  
**Effort:** Significant screening needed

---

## How to Use in PubMed

1. Go to: https://pubmed.ncbi.nlm.nih.gov/advanced
2. Copy one of the queries above
3. Paste in the search box
4. Click "Search"
5. In left sidebar, apply filters:
   - ✓ Language: English
   - ✓ Years: 2014-2024
   - ✓ Humans
   - ✓ Article types: Journal Articles, Trials, Reviews

---

## Imaging Modalities Covered

✓ MRI (Magnetic Resonance Imaging)  
✓ CT (Computed Tomography)  
✓ CR (Computed Radiography)  
✓ DX (Digital Radiography / X-ray)  
✓ PET-CT (Positron Emission Tomography)  
✓ Ultrasound  
✓ Interventional Radiology  
✓ Fluoroscopy  

---

## Population Covered

✓ Children (0-18 years)  
✓ Adolescents (13-18 years)  
✓ Young adults (18-24 years, if included)  
✓ Neonates/Infants (0-2 years)  

---

## Study Types Included

✓ Implementations (deployed systems)  
✓ Proposals (planned systems)  
✓ Evaluations (effectiveness studies)  
✓ User experiences (usability studies)  
✓ Clinical outcomes  
✓ Diagnostic accuracy studies  

---

## What to Do After Export

1. **Export from PubMed:**
   - Select all results
   - Send to → File
   - Format: MEDLINE or CSV
   - Download file

2. **Run through pipeline:**
   ```bash
   python systematic_review_assistant.py pubmed_export.csv
   ```

3. **Review outputs:**
   - `02_screening_results.json` - Which articles were included
   - `03_extracted_data.json` - Study characteristics
   - `summary_characteristics_table.csv` - For your paper

---

## Expected Workflow Timeline

| Step | Time | Tool |
|------|------|------|
| PubMed search | 5 min | Web browser |
| Export results | 2 min | PubMed |
| LLM screening | 30-60 min | Pipeline |
| Manual review (UNCERTAIN) | 2-4 hours | PDF reader |
| Data extraction | 1-2 hours | Pipeline |
| Quality assessment | 1-2 hours | Pipeline |
| Synthesis | 30 min | Pipeline |
| **Total** | **~4-6 hours** | **Automated + manual** |

---

## If Results Seem Wrong

### Too many results (1000+)?
Use the RESTRICTIVE query instead

### Too few results (<30)?
Try the COMPREHENSIVE query instead

### Wrong study types appearing?
Add to exclusions:
```
NOT (physics OR reconstruction OR algorithm* OR "image processing" NOT clinical)
NOT (animal OR veterinary OR preclinical)
```

### Wrong age group appearing?
Add exclusion:
```
NOT (adult*[tiab] OR geriatric*[tiab] OR elderly[tiab])
```

---

## Pro Tips 💡

1. **Run during off-peak hours** - PubMed faster (3am-6am)

2. **Save your search** - PubMed lets you create alerts for future articles

3. **Check the URL** - Your search is saved in the URL. Save it for the paper.

4. **Export multiple formats** - Keep both CSV and MEDLINE versions as backup

5. **Note the date** - Always record search date for reproducibility

6. **Use PROSPERO** - Pre-register your systematic review protocol at https://www.crd.york.ac.uk/prospero/

---

## Common Issues & Solutions

### "Query too complex"
**Solution:** Use RESTRICTED or BALANCED query instead

### "Getting non-pediatric articles"
**Solution:** Pipeline will filter these during screening with LLM

### "Missing articles you know exist"
**Solution:** 
- Try COMPREHENSIVE query
- Check citations/references manually
- Search Google Scholar for complements

### "CSV file won't open in Excel"
**Solution:** 
- Make sure encoding is UTF-8
- Try MEDLINE format instead
- Or open with Google Sheets

---

## Citation for Your Methods Section

> We performed a comprehensive search of PubMed on [DATE] using the following search strategy: ("clinical decision support" OR CDSS OR "computer-aided detection" OR "machine learning") AND (radiology OR "diagnostic imaging" OR CT OR MRI OR ultrasound) AND (child* OR pediatric* OR adolescent*) AND (implement* OR evaluat* OR clinical). The search was limited to English-language articles published between 2014-2024. Results were [FURTHER FILTERED BY/COMBINED WITH...]. Two independent reviewers screened titles and abstracts, with [X] articles progressing to full-text review.

---

## File Structure After Running Pipeline

```
your_project/
├── pubmed_export.csv (your export from PubMed)
├── systematic_review_assistant.py (pipeline script)
├── pubmed_parser.py (format handler)
└── output/ (results)
    ├── 00_articles_cache.json
    ├── 01_parsed_articles.json
    ├── 02_screening_results.json
    ├── 03_extracted_data.json
    ├── 04_quality_assessment.json
    ├── 05_thematic_synthesis.txt
    ├── summary_characteristics_table.csv ← USE THIS IN YOUR PAPER
    └── processing_log.txt
```

---

## Next Steps

1. ✅ Choose BALANCED query (recommended)
2. ✅ Go to PubMed Advanced Search
3. ✅ Paste query and run
4. ✅ Apply filters (English, 2014-2024, Humans)
5. ✅ Export as CSV
6. ✅ Run pipeline
7. ✅ Review results
8. ✅ Write paper!

Good luck! 🎯

---

## Questions?

See the full documentation:
- `REFINED_PUBMED_QUERY.md` - Detailed explanation
- `PUBMED_FORMATS.md` - Export format guide
- `DIRECT_API_SETUP.md` - Pipeline setup
- `QUICKSTART.md` - Getting started
