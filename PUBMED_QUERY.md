# Refined PubMed Query for CDSS in Pediatric Radiology

## Research Focus
Clinical decision support systems (CDSS) implementations, proposals, and user experiences in pediatric radiology imaging across multiple modalities.

## Target Population
- Primary: Children aged 0-18 years
- Secondary: Young adults aged 18-24 years (as extension)

## Imaging Modalities
- MRI (Magnetic Resonance Imaging)
- CT (Computed Tomography)
- CR (Computed Radiography)
- DX (Digital Radiography)
- PET-CT (Positron Emission Tomography-Computed Tomography)
- Ultrasound
- Interventional Radiology
- Fluoroscopy

## Article Types
- Implementations (deployed systems)
- Proposals (planned systems)
- User experiences (acceptance studies, usability evaluations)
- Clinical outcomes
- Diagnostic accuracy studies

---

## Primary Query (Comprehensive)

### Full Query String:

```
("Decision Support Systems, Clinical"[Mesh] OR "clinical decision support"[tiab] OR CDSS[tiab] OR "decision support tool"[tiab] OR "decision support system"[tiab] OR "intelligent decision support"[tiab] OR "computer-aided detection"[tiab] OR CAD[tiab] OR "artificial intelligence"[tiab] OR AI[tiab] OR "machine learning"[tiab] OR "deep learning"[tiab] OR "neural network"[tiab])
AND
("Diagnostic Imaging"[Mesh] OR "Radiology"[Mesh] OR radiology[tiab] OR "radiological"[tiab] OR "medical imaging"[tiab] OR imaging[tiab] OR
"Tomography, X-Ray Computed"[Mesh] OR "computed tomography"[tiab] OR CT[tiab] OR "CAT scan"[tiab] OR
"Magnetic Resonance Imaging"[Mesh] OR MRI[tiab] OR "magnetic resonance"[tiab] OR
"Ultrasonography"[Mesh] OR ultrasound[tiab] OR "ultrasonic imaging"[tiab] OR
"Radiography"[Mesh] OR radiograph*[tiab] OR "x-ray"[tiab] OR radiography[tiab] OR CR[tiab] OR DX[tiab] OR
"Positron-Emission Tomography"[Mesh] OR PET[tiab] OR "PET-CT"[tiab] OR "PET/CT"[tiab] OR
"Interventional Radiology"[Mesh] OR "interventional radiolog*"[tiab] OR
"Fluoroscopy"[Mesh] OR fluoroscop*[tiab])
AND
(Child*[tiab] OR Pediatric*[tiab] OR Paediatric*[tiab] OR infant*[tiab] OR newborn*[tiab] OR neonat*[tiab] OR adolescent*[tiab] OR youth[tiab] OR "young adult"*[tiab] OR juvenile*[tiab] OR "0-18 years"[tiab] OR "under 18"[tiab] OR "under 21"[tiab])
AND
(implement*[tiab] OR evaluat*[tiab] OR propos*[tiab] OR develop*[tiab] OR "user experience"[tiab] OR usability[tiab] OR acceptab*[tiab] OR satisf*[tiab] OR adoption[tiab] OR efficac*[tiab] OR "clinical outcome"[tiab] OR "diagnostic accuracy"[tiab] OR sensitiv*[tiab] OR specif*[tiab])
```

### Filters to Apply:
- Language: English
- Date range: Last 10 years (2014-2024) *optional, can adjust*
- Article types: Journal Articles, Reviews, Clinical Trials, Observational Studies

---

## Modular Query (For Focused Searches)

If the comprehensive query is too broad, use these modular searches and combine results:

### Query 1: Core CDSS + Pediatric Radiology

```
("clinical decision support" OR CDSS OR "computer-aided detection" OR CAD OR "artificial intelligence" OR "machine learning")
AND
(radiology OR "diagnostic imaging" OR CT OR MRI OR ultrasound)
AND
(child* OR pediatric* OR paediatric* OR infant*)
```

### Query 2: AI/ML Implementation in Pediatric Radiology

```
("machine learning" OR "deep learning" OR "neural network" OR "artificial intelligence" OR AI)
AND
(radiology OR imaging OR "diagnostic imaging")
AND
(child* OR pediatric* OR paediatric*)
AND
(implement* OR evaluat* OR develop* OR clinical OR diagnosis*)
```

### Query 3: Specific Modalities with CDSS

**For CT-specific:**
```
("clinical decision support" OR CDSS OR "computer-aided detection" OR AI OR "machine learning")
AND
("computed tomography" OR CT scan)
AND
(child* OR pediatric*)
AND
(implement* OR evaluate* OR diagnosis*)
```

**For MRI-specific:**
```
("clinical decision support" OR CDSS OR "machine learning")
AND
(MRI OR "magnetic resonance imaging")
AND
(child* OR pediatric*)
AND
(implement* OR diagnos* OR detect*)
```

**For Ultrasound-specific:**
```
("clinical decision support" OR CDSS OR "computer-aided")
AND
(ultrasound OR sonography)
AND
(child* OR pediatric*)
```

**For Interventional Radiology:**
```
("clinical decision support" OR CDSS OR decision-support)
AND
("interventional radiology" OR "image-guided intervention")
AND
(child* OR pediatric*)
```

---

## Extended Filters

### Include These MeSH Terms (via Advanced Search):

**Disease/Condition Terms:**
- Common pediatric imaging indications:
  - "Neoplasms" (cancer screening/diagnosis)
  - "Trauma" or "Wounds and Injuries"
  - "Appendicitis"
  - "Acute Abdomen"
  - "Intussusception"
  - "Pneumonia"
  - Any condition requiring imaging in children

**Study Design (if available):**
- Randomized Controlled Trial (RCT)
- Observational Study
- Cross-Sectional Study
- Implementation Science Study
- Usability Study
- User Experience Study

### Exclude These (via NOT operator):

```
NOT (adult* OR geriatric* OR aging OR elderly OR "adult only")
NOT (animal OR veterinary OR preclinical)
NOT (physics OR reconstruction OR algorithm* OR "image processing" NOT clinical)
```

---

## Refined Query with Exclusions

```
("Decision Support Systems, Clinical"[Mesh] OR "clinical decision support"[tiab] OR CDSS[tiab] OR CAD[tiab] OR "computer-aided detection"[tiab] OR "artificial intelligence"[tiab] OR "machine learning"[tiab] OR "deep learning"[tiab])
AND
(radiology[tiab] OR "diagnostic imaging"[tiab] OR imaging[tiab] OR CT[tiab] OR MRI[tiab] OR ultrasound[tiab] OR "x-ray"[tiab] OR radiograph*[tiab] OR fluoroscop*[tiab] OR "interventional radiology"[tiab] OR PET[tiab] OR "magnetic resonance"[tiab])
AND
(child*[tiab] OR pediatric*[tiab] OR paediatric*[tiab] OR infant*[tiab] OR newborn*[tiab] OR neonat*[tiab] OR adolescent*[tiab] OR "young adult"*[tiab])
AND
(implement*[tiab] OR evaluat*[tiab] OR propos*[tiab] OR develop*[tiab] OR "user experience"[tiab] OR usability[tiab] OR acceptab*[tiab] OR efficac*[tiab] OR "diagnostic accuracy"[tiab])
NOT
(adult*[tiab] OR geriatric*[tiab] OR elderly[tiab] OR animal*[tiab] OR veterinary[tiab] OR "physics of"[tiab])
```

**With filters:**
- Language: English
- Year: 2014-2024
- Article types: Journal Articles, Clinical Trials, Reviews
- Human subjects

---

## Alternative Query (More Restrictive - High Precision)

Use if the above returns too many results:

```
("clinical decision support" OR CDSS)
AND
(CT OR MRI OR ultrasound OR radiology)
AND
(pediatric* OR paediatric* OR child*)
AND
(implement* OR evaluate* OR clinical)
```

---

## Alternative Query (More Sensitive - Broader)

Use if you're not finding enough articles:

```
(CDSS OR "decision support" OR AI OR "machine learning")
AND
(imaging OR radiology)
AND
(child* OR pediatric* OR adolescent*)
```

---

## Query Optimization Tips

### For Maximum Recall (Find All Relevant Articles):
1. Use the comprehensive query
2. Combine with modular queries
3. Include both MeSH and free text terms
4. Lower specificity filters (earlier years)
5. Manual review of "uncertain" articles during screening

### For Maximum Precision (Find Highly Relevant Articles):
1. Use the restrictive query
2. Include implementation/evaluation keywords
3. Use recent years only (2020-2024)
4. Focus on specific modalities
5. Exclude uncertain or tangential articles early

---

## Search Strategy Examples

### Strategy 1: Conservative (Fewer but Highly Relevant)
```
("clinical decision support" OR CDSS)
AND
(CT OR MRI OR ultrasound)
AND
(pediatric* OR child*)
AND
(implement* OR evaluate* OR clinical outcome*)
```
**Expected results:** 50-150 articles

### Strategy 2: Balanced (Moderate sensitivity and specificity)
```
("clinical decision support" OR CDSS OR "computer-aided detection" OR "machine learning")
AND
(radiology OR imaging OR CT OR MRI OR ultrasound)
AND
(child* OR pediatric*)
AND
(implement* OR evaluat* OR clinical*)
```
**Expected results:** 150-400 articles

### Strategy 3: Comprehensive (More articles to review)
```
("Decision Support Systems, Clinical"[Mesh] OR CDSS OR "machine learning" OR AI OR "artificial intelligence")
AND
(radiology OR imaging OR "diagnostic imaging")
AND
(child* OR pediatric* OR infant* OR adolescent*)
```
**Expected results:** 300-800+ articles

---

## Implementation Steps in PubMed

### Step 1: Use Advanced Search
1. Go to https://pubmed.ncbi.nlm.nih.gov/advanced
2. Copy one of the queries above
3. Paste into search box

### Step 2: Apply Filters

In the left sidebar:

**Years:**
- Click "Year" → Select 2014:2024

**Article Types:**
- Journal Article ✓
- Clinical Trial ✓
- Review ✓
- Meta-Analysis ✓
- Systematic Review ✓

**Language:**
- English ✓

**Species:**
- Humans ✓

### Step 3: Review Results

Check:
- Number of results
- Titles for relevance
- Abstract sampling for quality

### Step 4: Export Results

1. Select all results
2. Send to → File
3. Format: MEDLINE or CSV
4. Create file

---

## Expected Results by Query

| Query | Results | Relevance | Note |
|-------|---------|-----------|------|
| Conservative | 50-150 | Very High | Focused on implementation/evaluation |
| Balanced | 150-400 | High | Good mix of modalities and study types |
| Comprehensive | 300-800+ | Moderate-High | Includes broader topics, more screening needed |

---

## Screening Strategy

For your systematic review, suggest this 2-stage screening:

### Stage 1: Title & Abstract Screening
Use the LLM pipeline with these inclusion criteria:

**INCLUDE if:**
- Clearly about CDSS/AI in medical imaging
- Involves pediatric population
- Describes implementation, evaluation, or user experience
- Contains clinical data or outcomes

**EXCLUDE if:**
- Pure technical/algorithmic papers (no clinical application)
- Not about CDSS specifically
- Adult-only population
- No original data or outcomes
- Non-English

**UNCERTAIN:** Mark for full-text review

### Stage 2: Full-Text Review
Manual review for:
- Complete study design clarity
- Pediatric population inclusion (0-18 or 18-24)
- CDSS implementation details
- Relevant outcomes measured
- Methodological quality

---

## Key Search Terms Summary

### CDSS/AI Concepts:
- clinical decision support
- CDSS
- computer-aided detection / CAD
- artificial intelligence / AI
- machine learning
- deep learning
- intelligent systems

### Imaging Modalities:
- radiology / radiological
- diagnostic imaging
- computed tomography / CT
- magnetic resonance imaging / MRI
- ultrasound / sonography
- radiography / x-ray
- PET-CT / PET scan
- interventional radiology
- fluoroscopy

### Pediatric Population:
- child / children / childhood
- pediatric / paediatric
- infant / infants / infancy
- newborn / neonatal
- adolescent / adolescence
- youth
- young adult
- juvenile

### Implementation/Evaluation:
- implement / implementation
- evaluat / evaluation
- propos / proposal
- develop / development
- user experience / UX
- usability
- acceptability
- adoption
- clinical outcome
- diagnostic accuracy
- effectiveness

---

## Final Recommendations

### Recommended Approach:
1. **Start with Balanced Query** (Strategy 2)
   - Good coverage without overwhelming volume
   - Expected 150-400 articles

2. **Apply Filters:**
   - Language: English
   - Years: 2014-2024
   - Species: Humans
   - Article types: Journal articles, trials, reviews

3. **Use LLM Screening Pipeline:**
   - Title/abstract screening with LLM
   - Manual full-text review for uncertain cases

4. **Document Search:**
   - Save the exact PubMed URL
   - Record date of search
   - Note number of results at each stage

5. **Follow PRISMA-P 2015:**
   - Pre-register protocol (PROSPERO)
   - Document all deviations
   - Report all screening numbers

---

## PRISMA Search String to Report

For your methods section:

> "We searched PubMed with the following strategy on [DATE]: [INSERT FINAL QUERY]. Search was limited to English-language articles published between 2014-2024 involving human subjects. Results were combined with [CITE ANY ADDITIONAL SOURCES]. No date or language restrictions were applied to [MENTION IF APPLICABLE]. The search strategy was developed iteratively by [TEAM MEMBERS] with input from [LIBRARIAN/EXPERT]."

---

## Additional Considerations

### For Missing Articles:
1. Check PubMed Central (PMC) for open access
2. Search Google Scholar for preprints
3. Check relevant journals:
   - Radiology
   - Pediatric Radiology
   - Journal of Digital Imaging
   - RadioGraphics
   - European Radiology
   - Pediatrics
   - Journal of Medical Systems

### Citation Tracking:
- Use "Related articles" in PubMed
- Manual backward citation searching
- Forward citation searching via Web of Science

### Gray Literature:
- Conference proceedings (RSNA, SPR, ASER)
- Technical reports
- Theses/dissertations
- Industry white papers

---

## Testing Your Query

Before committing to the search, test with smaller versions:

```bash
# Quick test 1 (most restrictive)
CDSS AND pediatric* AND radiology

# Quick test 2 (moderate)
("clinical decision support" OR "machine learning") 
AND (radiology OR imaging) 
AND (pediatric* OR child*)

# Quick test 3 (full query)
[Use the balanced query above]
```

Check results at each level to ensure:
- Reasonable number of results
- High proportion of relevant titles
- Coverage of all modalities
- Good mix of study types

---

## Questions to Refine Further

Do you want to:
1. **Narrow by specific conditions?** (e.g., cancer detection, trauma assessment)
2. **Include specific imaging findings?** (e.g., fractures, tumors, infections)
3. **Focus on specific outcomes?** (e.g., diagnostic accuracy, time saved, workflow impact)
4. **Include economic/cost analyses?**
5. **Exclude certain study types?** (e.g., only case reports)

---

## Next Steps

1. **Choose a query strategy** (Conservative/Balanced/Comprehensive)
2. **Test in PubMed Advanced Search** (https://pubmed.ncbi.nlm.nih.gov/advanced)
3. **Review first 50 results** for relevance
4. **Refine if needed** based on what you find
5. **Export results** in MEDLINE or CSV format
6. **Run through the pipeline** for systematic screening

Ready to run the query? 🎯
