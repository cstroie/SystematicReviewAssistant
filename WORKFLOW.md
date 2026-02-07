# LLM-Based Literature Review Processing Workflow
## Clinical Decision Support Systems in Medical Imaging/Radiology

---

## 1. OVERVIEW & ARCHITECTURE

This workflow automates screening, data extraction, and synthesis of PubMed articles using Claude API in a structured pipeline:

1. **Data Collection** → PubMed export
2. **Screening** → LLM filters articles by relevance
3. **Data Extraction** → LLM extracts structured information
4. **Quality Assessment** → LLM applies quality frameworks
5. **Synthesis** → Organize and identify themes
6. **Output** → Structured tables and narrative summaries

---

## 2. STAGE 1: DATA COLLECTION & PREPARATION

### 2.1 PubMed Export

Execute your search in PubMed and export results:
- Use the refined query provided earlier
- Export format: **MEDLINE** or **CSV** (PubMed/NCBI format)
- Include: PMID, Title, Abstract, Authors, Publication Date, Journal

### 2.2 Parse Export File

Convert PubMed export to JSON for processing:

```python
import json
import csv
from datetime import datetime

def parse_pubmed_csv(csv_file):
    """Parse PubMed CSV export into standardized format"""
    articles = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            article = {
                'pmid': row.get('PMID', '').strip(),
                'title': row.get('Title', '').strip(),
                'abstract': row.get('Abstract', '').strip(),
                'authors': row.get('Authors', '').strip(),
                'journal': row.get('Journal', '').strip(),
                'pub_date': row.get('Publication Date', '').strip(),
                'doi': row.get('DOI', '').strip(),
                'screening_status': 'pending',  # Will be filled during screening
                'screening_reason': None,
                'data_extraction': None,
                'quality_score': None
            }
            articles.append(article)
    
    return articles

def save_articles_json(articles, output_file):
    """Save articles as JSON for LLM processing"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(articles)} articles to {output_file}")
```

---

## 3. STAGE 2: TITLE & ABSTRACT SCREENING

### 3.1 Screening Prompts

This stage uses a 3-category classification system:

**INCLUDE** - Clearly relevant to CDSS in medical imaging
**EXCLUDE** - Clearly not relevant
**UNCERTAIN** - Needs full-text review

```
System prompt:
You are a systematic review screener for a literature review on "Clinical Decision 
Support Systems in Medical Imaging/Radiology".

Your task is to classify articles as INCLUDE, EXCLUDE, or UNCERTAIN based on title 
and abstract. Use these criteria:

INCLUDE if the article:
- Describes or evaluates a clinical decision support system/tool
- Applied to medical imaging (radiology, CT, MRI, ultrasound, pathology imaging, etc.)
- Reports clinical outcomes, diagnostic accuracy, or user satisfaction

EXCLUDE if:
- Focus is on imaging physics/reconstruction (not clinical application)
- CDSS applied to non-imaging domains
- Pure literature review with no primary research
- Opinion pieces without data
- Not in English or unavailable abstracts

UNCERTAIN if:
- Abstract unclear about relevance
- Borderline between imaging/non-imaging
- Unclear if CDSS or just image analysis algorithm

Respond in JSON format:
{
  "decision": "INCLUDE|EXCLUDE|UNCERTAIN",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation",
  "key_terms_found": ["list", "of", "keywords"]
}
```

### 3.2 Batch Processing Implementation

```python
import json
import time
from anthropic import Anthropic

def screen_articles_batch(articles_json_file, output_file, batch_size=10):
    """
    Screen articles in batches using Claude API
    
    Args:
        articles_json_file: Path to JSON file with articles
        output_file: Path to save screening results
        batch_size: Process articles in batches to manage API usage
    """
    
    with open(articles_json_file, 'r') as f:
        articles = json.load(f)
    
    client = Anthropic()
    screened_results = []
    
    screening_prompt_template = """
You are a systematic review screener for: "Clinical Decision Support Systems in Medical Imaging/Radiology"

INCLUSION CRITERIA:
- Describes or evaluates a clinical decision support system/tool
- Applied to medical imaging (radiology, CT, MRI, ultrasound, pathology imaging, etc.)
- Reports clinical outcomes, diagnostic accuracy, or user satisfaction

EXCLUSION CRITERIA:
- Focus on imaging physics/reconstruction without clinical application
- CDSS applied to non-imaging domains
- Literature reviews without primary research
- Opinion pieces without data

Please classify this article:

PMID: {pmid}
TITLE: {title}
ABSTRACT: {abstract}

Respond ONLY in this JSON format:
{{
  "pmid": "{pmid}",
  "decision": "INCLUDE|EXCLUDE|UNCERTAIN",
  "confidence": 0.0-1.0,
  "reasoning": "Your brief reasoning",
  "key_terms_found": ["term1", "term2"]
}}
"""
    
    total = len(articles)
    
    for i, article in enumerate(articles):
        # Rate limiting
        if i > 0 and i % batch_size == 0:
            print(f"Processed {i}/{total} articles. Pausing...")
            time.sleep(2)
        
        prompt = screening_prompt_template.format(
            pmid=article['pmid'],
            title=article['title'],
            abstract=article['abstract']
        )
        
        try:
            response = client.messages.create(
                model="claude-opus-4-5-20251101",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result_text = response.content[0].text
            # Parse JSON response
            result = json.loads(result_text)
            screened_results.append(result)
            
            # Print progress
            print(f"[{i+1}/{total}] {article['pmid']}: {result['decision']}")
            
        except json.JSONDecodeError:
            print(f"Error parsing response for PMID {article['pmid']}")
            screened_results.append({
                'pmid': article['pmid'],
                'decision': 'UNCERTAIN',
                'confidence': 0.0,
                'reasoning': 'Error processing response',
                'key_terms_found': []
            })
        except Exception as e:
            print(f"API error for PMID {article['pmid']}: {str(e)}")
            time.sleep(5)
    
    # Save results
    with open(output_file, 'w') as f:
        json.dump(screened_results, f, indent=2)
    
    # Print summary
    include_count = sum(1 for r in screened_results if r['decision'] == 'INCLUDE')
    exclude_count = sum(1 for r in screened_results if r['decision'] == 'EXCLUDE')
    uncertain_count = sum(1 for r in screened_results if r['decision'] == 'UNCERTAIN')
    
    print(f"\n=== SCREENING SUMMARY ===")
    print(f"INCLUDE: {include_count}")
    print(f"EXCLUDE: {exclude_count}")
    print(f"UNCERTAIN: {uncertain_count}")
    print(f"Total: {total}")

# Usage
screen_articles_batch('articles.json', 'screening_results.json')
```

---

## 4. STAGE 3: DATA EXTRACTION

### 4.1 Extraction Schema

Define the structured data you want to extract:

```json
{
  "pmid": "string",
  "title": "string",
  "year": "integer",
  "study_design": "RCT|Retrospective|Prospective|Case Series|Other",
  "sample_size": {
    "total_patients": "integer or null",
    "total_images": "integer or null"
  },
  "clinical_domain": "string (e.g., Breast Cancer Detection, Lung Nodule Classification)",
  "imaging_modality": ["string"] (e.g., ["CT", "Mammography"]),
  "cdss_type": "string (e.g., AI/ML-based, Rule-based, Hybrid)",
  "cdss_name": "string (name of the system if available)",
  "primary_outcomes": ["string"],
  "key_metrics": {
    "sensitivity": "float or null",
    "specificity": "float or null",
    "auc": "float or null",
    "accuracy": "float or null",
    "other_metrics": {}
  },
  "comparison": "string (e.g., vs radiologist alone, vs current standard)",
  "main_findings": "string",
  "limitations_noted": ["string"],
  "clinical_implications": "string",
  "funding_source": "string or null"
}
```

### 4.2 Extraction Prompt & Implementation

```python
def extract_article_data(full_text_or_abstract, pmid, title):
    """
    Extract structured data from article
    full_text_or_abstract: The article content (ideally full text, but abstract works)
    """
    
    client = Anthropic()
    
    extraction_prompt = f"""
You are systematically extracting data from a medical research article for a literature review 
on "Clinical Decision Support Systems in Medical Imaging/Radiology".

ARTICLE:
PMID: {pmid}
TITLE: {title}

CONTENT:
{full_text_or_abstract}

Extract the following information in JSON format. Use null for unavailable data:

{{
  "pmid": "{pmid}",
  "title": "{title}",
  "year": "publication year as integer",
  "study_design": "RCT, Retrospective, Prospective, Case Series, or Other",
  "sample_size": {{
    "total_patients": "number or null",
    "total_images": "number or null"
  }},
  "clinical_domain": "specific clinical application (e.g., 'Breast Cancer Detection')",
  "imaging_modality": ["list of imaging types, e.g. CT, MRI, Mammography"],
  "cdss_type": "AI/ML-based, Rule-based, Hybrid, or Other",
  "cdss_name": "name of the system if mentioned, or 'Not specified'",
  "primary_outcomes": ["list of primary outcome measures"],
  "key_metrics": {{
    "sensitivity": "value or null",
    "specificity": "value or null",
    "auc": "value or null",
    "accuracy": "value or null",
    "other_metrics": {{"metric_name": "value"}}
  }},
  "comparison": "what was the CDSS compared against?",
  "main_findings": "1-2 sentences summarizing key results",
  "limitations_noted": ["list of limitations mentioned by authors"],
  "clinical_implications": "stated clinical implications or impact",
  "funding_source": "funding source if mentioned, or null"
}}

IMPORTANT:
- Be precise with numeric values
- Extract metrics as they appear (don't round unless stated)
- If metrics are ranges, use notation like "0.85-0.92"
- Keep text fields concise but complete
- Use null for truly unavailable data, not "N/A" or "Unknown"
"""
    
    response = client.messages.create(
        model="claude-opus-4-5-20251101",
        max_tokens=1500,
        messages=[{"role": "user", "content": extraction_prompt}]
    )
    
    result_text = response.content[0].text
    extracted_data = json.loads(result_text)
    return extracted_data

def batch_extract_articles(included_articles_json, full_text_dir, output_file):
    """
    Extract data from all included articles
    
    Args:
        included_articles_json: JSON file with articles that passed screening
        full_text_dir: Directory containing full-text PDFs (optional - uses abstract if not available)
        output_file: Path to save extraction results
    """
    
    with open(included_articles_json, 'r') as f:
        articles = json.load(f)
    
    extracted_data = []
    total = len(articles)
    
    for i, article in enumerate(articles):
        # Here you'd load full text if available, or use abstract
        content_to_extract = article.get('abstract', '')
        
        try:
            data = extract_article_data(
                content_to_extract,
                article['pmid'],
                article['title']
            )
            extracted_data.append(data)
            print(f"[{i+1}/{total}] Extracted {article['pmid']}")
            
            # Rate limiting
            if (i + 1) % 5 == 0:
                time.sleep(2)
                
        except Exception as e:
            print(f"Error extracting {article['pmid']}: {str(e)}")
    
    with open(output_file, 'w') as f:
        json.dump(extracted_data, f, indent=2)
    
    print(f"\nExtracted data from {len(extracted_data)}/{total} articles")

# Usage
batch_extract_articles('included_articles.json', None, 'extracted_data.json')
```

---

## 5. STAGE 4: QUALITY ASSESSMENT

### 5.1 QUADAS-2 Implementation (for diagnostic accuracy studies)

```python
def assess_quality_quadas2(article_data, abstract_or_fulltext):
    """
    Assess study quality using QUADAS-2 framework
    For diagnostic accuracy studies (sensitivity/specificity reported)
    """
    
    client = Anthropic()
    
    quadas2_prompt = f"""
You are assessing the quality of a diagnostic accuracy study using QUADAS-2.

ARTICLE: {article_data['title']}
PMID: {article_data['pmid']}

CONTENT:
{abstract_or_fulltext}

Assess the following QUADAS-2 domains (Yes/No/Unclear for each):

1. PATIENT SELECTION
   - Was a consecutive or random sample of patients enrolled?
   - Was a case-control design avoided?

2. INDEX TEST
   - Were the index test results interpreted without knowledge of reference standard?
   - If cutoffs were used, were they pre-specified?

3. REFERENCE STANDARD
   - Is the reference standard likely to correctly classify the target condition?
   - Were the reference standard results interpreted without knowledge of index test?

4. FLOW & TIMING
   - Was there an appropriate interval between index and reference tests?
   - Did all patients receive the reference standard?

Respond in JSON:
{{
  "pmid": "{article_data['pmid']}",
  "quadas2_domains": {{
    "patient_selection": "Yes|No|Unclear",
    "index_test": "Yes|No|Unclear",
    "reference_standard": "Yes|No|Unclear",
    "flow_timing": "Yes|No|Unclear"
  }},
  "overall_risk_of_bias": "Low|Moderate|High",
  "concerns_applicability": "Low|Moderate|High",
  "justification": "brief explanation of risk assessment"
}}
"""
    
    response = client.messages.create(
        model="claude-opus-4-5-20251101",
        max_tokens=500,
        messages=[{"role": "user", "content": quadas2_prompt}]
    )
    
    return json.loads(response.content[0].text)
```

---

## 6. STAGE 5: SYNTHESIS & THEMATIC ANALYSIS

### 6.1 Identify Themes

```python
def identify_themes(extracted_data_json):
    """
    Use LLM to identify common themes, trends, and gaps
    """
    
    with open(extracted_data_json, 'r') as f:
        data = json.load(f)
    
    # Create summary of all studies
    studies_summary = json.dumps(data, indent=2)
    
    client = Anthropic()
    
    themes_prompt = f"""
You are synthesizing a systematic review on "Clinical Decision Support Systems in Medical Imaging/Radiology".

Here are the key characteristics of {len(data)} included studies:

{studies_summary}

Please provide:

1. THEMATIC ORGANIZATION
   - Group studies by: imaging modality, clinical domain, CDSS type, study design
   - Identify 3-5 major research themes/trends

2. KEY FINDINGS
   - What are the most consistent findings across studies?
   - What outcomes are most commonly reported?
   - What are average performance metrics by domain?

3. GAPS & LIMITATIONS
   - What clinical domains lack adequate CDSS research?
   - What methodological gaps exist?
   - What are the most commonly cited limitations?

4. FUTURE DIRECTIONS
   - What does the literature suggest as next research priorities?
   - What unmet clinical needs are mentioned?

5. CLINICAL IMPLICATIONS
   - Is there evidence for clinical implementation?
   - What barriers to adoption are mentioned?

Organize your response in clear sections suitable for inclusion in a systematic review report.
"""
    
    response = client.messages.create(
        model="claude-opus-4-5-20251101",
        max_tokens=3000,
        messages=[{"role": "user", "content": themes_prompt}]
    )
    
    synthesis = response.content[0].text
    return synthesis
```

### 6.2 Generate Summary Tables

```python
def generate_summary_table(extracted_data_json, output_csv):
    """
    Create a summary characteristics table in CSV format
    """
    
    with open(extracted_data_json, 'r') as f:
        data = json.load(f)
    
    import pandas as pd
    
    # Convert to DataFrame
    df = pd.DataFrame([
        {
            'PMID': item['pmid'],
            'Year': item.get('year', ''),
            'Study Design': item.get('study_design', ''),
            'Clinical Domain': item.get('clinical_domain', ''),
            'Imaging Modality': ', '.join(item.get('imaging_modality', [])),
            'CDSS Type': item.get('cdss_type', ''),
            'Sample Size': item.get('sample_size', {}).get('total_patients', ''),
            'Sensitivity': item.get('key_metrics', {}).get('sensitivity', ''),
            'Specificity': item.get('key_metrics', {}).get('specificity', ''),
            'AUC': item.get('key_metrics', {}).get('auc', ''),
            'Main Finding': item.get('main_findings', '')[:100]  # First 100 chars
        }
        for item in data
    ])
    
    df.to_csv(output_csv, index=False)
    print(f"Summary table saved to {output_csv}")
    
    return df
```

---

## 7. COMPLETE WORKFLOW SCRIPT

```python
#!/usr/bin/env python3
"""
Complete LLM-based Literature Review Processing Pipeline
For CDSS in Medical Imaging/Radiology Systematic Review
"""

import json
import csv
import time
import sys
from pathlib import Path
from anthropic import Anthropic

class CDSSLitReviewProcessor:
    def __init__(self, output_dir="lit_review_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.client = Anthropic()
    
    def run_complete_pipeline(self, pubmed_csv_file):
        """Execute the complete workflow"""
        
        print("="*60)
        print("CDSS LITERATURE REVIEW PROCESSING PIPELINE")
        print("="*60)
        
        # Step 1: Parse CSV
        print("\n[STEP 1] Parsing PubMed export...")
        articles = self._parse_pubmed_csv(pubmed_csv_file)
        articles_file = self.output_dir / "01_parsed_articles.json"
        self._save_json(articles, articles_file)
        print(f"✓ Parsed {len(articles)} articles")
        
        # Step 2: Screen articles
        print("\n[STEP 2] Screening titles and abstracts...")
        screening_results = self._screen_articles(articles)
        screening_file = self.output_dir / "02_screening_results.json"
        self._save_json(screening_results, screening_file)
        
        include_count = sum(1 for r in screening_results if r['decision'] == 'INCLUDE')
        print(f"✓ Screening complete: {include_count} included for full-text review")
        
        # Step 3: Filter for included articles and extract data
        print("\n[STEP 3] Extracting data from included articles...")
        included_pmids = {r['pmid'] for r in screening_results if r['decision'] == 'INCLUDE'}
        included_articles = [a for a in articles if a['pmid'] in included_pmids]
        
        extracted_data = self._extract_article_data(included_articles)
        extraction_file = self.output_dir / "03_extracted_data.json"
        self._save_json(extracted_data, extraction_file)
        print(f"✓ Extracted data from {len(extracted_data)} articles")
        
        # Step 4: Assess quality
        print("\n[STEP 4] Assessing study quality...")
        quality_assessments = self._assess_quality(extracted_data, included_articles)
        quality_file = self.output_dir / "04_quality_assessment.json"
        self._save_json(quality_assessments, quality_file)
        print(f"✓ Quality assessment complete")
        
        # Step 5: Synthesis
        print("\n[STEP 5] Performing thematic synthesis...")
        synthesis = self._perform_synthesis(extracted_data)
        synthesis_file = self.output_dir / "05_thematic_synthesis.txt"
        synthesis_file.write_text(synthesis)
        print(f"✓ Synthesis complete")
        
        # Step 6: Generate summary table
        print("\n[STEP 6] Generating summary table...")
        self._generate_summary_table(extracted_data)
        print(f"✓ Summary table created")
        
        print("\n" + "="*60)
        print("PIPELINE COMPLETE")
        print(f"Results saved to: {self.output_dir}")
        print("="*60)
    
    def _parse_pubmed_csv(self, csv_file):
        articles = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                article = {
                    'pmid': row.get('PMID', '').strip(),
                    'title': row.get('Title', '').strip(),
                    'abstract': row.get('Abstract', '').strip(),
                    'authors': row.get('Authors', '').strip(),
                    'journal': row.get('Journal', '').strip(),
                    'pub_date': row.get('Publication Date', '').strip(),
                }
                if article['pmid']:  # Only include if PMID exists
                    articles.append(article)
        return articles
    
    def _screen_articles(self, articles):
        results = []
        for i, article in enumerate(articles):
            prompt = f"""You are screening articles for a systematic review on Clinical Decision Support Systems in Medical Imaging.

PMID: {article['pmid']}
TITLE: {article['title']}
ABSTRACT: {article['abstract']}

INCLUDE if: describes/evaluates CDSS in medical imaging with clinical outcomes
EXCLUDE if: not about CDSS, not about medical imaging, or no primary research
UNCERTAIN if: unclear or borderline relevance

Respond in JSON only:
{{"pmid": "{article['pmid']}", "decision": "INCLUDE|EXCLUDE|UNCERTAIN", "confidence": 0.0-1.0, "reasoning": "brief reason"}}"""
            
            try:
                response = self.client.messages.create(
                    model="claude-opus-4-5-20251101",
                    max_tokens=200,
                    messages=[{"role": "user", "content": prompt}]
                )
                result = json.loads(response.content[0].text)
                results.append(result)
                print(f"[{i+1}/{len(articles)}] {article['pmid']}: {result['decision']}")
                
                if (i + 1) % 10 == 0:
                    time.sleep(2)
            except Exception as e:
                print(f"Error screening {article['pmid']}: {e}")
                results.append({
                    'pmid': article['pmid'],
                    'decision': 'UNCERTAIN',
                    'confidence': 0.0,
                    'reasoning': 'Processing error'
                })
        return results
    
    def _extract_article_data(self, articles):
        extracted = []
        for i, article in enumerate(articles):
            prompt = f"""Extract structured data from this article. Return ONLY valid JSON.

PMID: {article['pmid']}
TITLE: {article['title']}
ABSTRACT: {article['abstract']}

{{
  "pmid": "{article['pmid']}",
  "title": "{article['title']}",
  "year": "publication year",
  "study_design": "type",
  "clinical_domain": "domain",
  "imaging_modality": ["modalities"],
  "cdss_type": "type",
  "sample_size": {{"total_patients": "number"}},
  "key_metrics": {{"sensitivity": null, "specificity": null, "auc": null}},
  "main_findings": "summary"
}}"""
            
            try:
                response = self.client.messages.create(
                    model="claude-opus-4-5-20251101",
                    max_tokens=800,
                    messages=[{"role": "user", "content": prompt}]
                )
                data = json.loads(response.content[0].text)
                extracted.append(data)
                print(f"[{i+1}/{len(articles)}] Extracted {article['pmid']}")
                
                if (i + 1) % 5 == 0:
                    time.sleep(1)
            except Exception as e:
                print(f"Error extracting {article['pmid']}: {e}")
        return extracted
    
    def _assess_quality(self, extracted_data, articles):
        # Placeholder for quality assessment
        # In full implementation, would call assess_quality_quadas2
        return extracted_data  # Simplified for this template
    
    def _perform_synthesis(self, extracted_data):
        prompt = f"""Synthesize findings from {len(extracted_data)} studies on Clinical Decision Support Systems in Medical Imaging.

Data summary:
{json.dumps(extracted_data[:5], indent=2)}... [and {len(extracted_data)-5} more studies]

Provide:
1. Key themes and trends
2. Most common clinical domains
3. Range of performance metrics
4. Methodological gaps
5. Clinical implications

Write suitable for a systematic review report."""
        
        response = self.client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    
    def _generate_summary_table(self, extracted_data):
        import pandas as pd
        
        rows = []
        for item in extracted_data:
            rows.append({
                'PMID': item.get('pmid', ''),
                'Year': item.get('year', ''),
                'Design': item.get('study_design', ''),
                'Domain': item.get('clinical_domain', ''),
                'Modality': ', '.join(item.get('imaging_modality', [])),
                'CDSS Type': item.get('cdss_type', ''),
                'N': item.get('sample_size', {}).get('total_patients', ''),
                'Sensitivity': item.get('key_metrics', {}).get('sensitivity', ''),
                'Specificity': item.get('key_metrics', {}).get('specificity', ''),
                'AUC': item.get('key_metrics', {}).get('auc', '')
            })
        
        df = pd.DataFrame(rows)
        output_file = self.output_dir / "summary_table.csv"
        df.to_csv(output_file, index=False)
    
    def _save_json(self, data, filepath):
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

# Main execution
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <pubmed_export.csv>")
        sys.exit(1)
    
    processor = CDSSLitReviewProcessor()
    processor.run_complete_pipeline(sys.argv[1])
```

---

## 8. OUTPUT STRUCTURE

After running the complete pipeline, you'll have:

```
lit_review_output/
├── 01_parsed_articles.json          # All articles from PubMed
├── 02_screening_results.json        # Title/abstract screening decisions
├── 03_extracted_data.json           # Structured data extraction
├── 04_quality_assessment.json       # QUADAS-2 or other quality scores
├── 05_thematic_synthesis.txt        # Narrative synthesis
├── summary_table.csv                # Summary characteristics table
└── [logs and intermediate files]
```

---

## 9. BEST PRACTICES & CONSIDERATIONS

### Error Handling
- Wrap API calls in try-except blocks
- Log all errors with timestamps
- Implement rate limiting (10-50 articles per batch with 2-5s pauses)
- Add exponential backoff for API failures

### Quality Control
- Manually review a sample (10-20%) of screening decisions
- For included articles, verify LLM extractions against abstracts
- Compare LLM quality assessments against manual assessment for subset
- Run sensitivity analysis (e.g., excluding low-quality studies)

### Cost Management
- Screening (300 tokens/article): ~$0.002 per article
- Extraction (1500 tokens/article): ~$0.01 per article
- For 500 articles: ~$6-7 total

### Prompt Optimization
- Use few-shot examples in prompts (2-3 examples)
- Include explicit output format requirements (JSON)
- Test prompts on 10-20 articles before full run
- Iterate based on error patterns

---

## 10. VALIDATION & VERIFICATION STEPS

```python
def validate_screening_decisions(original_articles, screening_results, sample_size=20):
    """
    Manually verify a random sample of screening decisions
    """
    import random
    sample_pmids = random.sample([r['pmid'] for r in screening_results], sample_size)
    
    print("Manual Verification Sample:")
    for pmid in sample_pmids:
        article = next(a for a in original_articles if a['pmid'] == pmid)
        screening = next(r for r in screening_results if r['pmid'] == pmid)
        
        print(f"\nPMID: {pmid}")
        print(f"Title: {article['title'][:80]}...")
        print(f"LLM Decision: {screening['decision']} (confidence: {screening['confidence']})")
        print(f"Reasoning: {screening['reasoning']}")
        print("Your decision (INCLUDE/EXCLUDE/UNCERTAIN)?")

def calculate_agreement_metrics(manual_verification, llm_results):
    """
    Calculate Cohen's kappa, sensitivity, specificity of LLM screening
    """
    from sklearn.metrics import cohen_kappa_score, confusion_matrix
    
    # Compare manual vs LLM decisions
    kappa = cohen_kappa_score(manual_verification, llm_results)
    cm = confusion_matrix(manual_verification, llm_results)
    
    print(f"Cohen's Kappa: {kappa:.3f}")
    print(f"Confusion Matrix:\n{cm}")
    
    # Interpret kappa
    if kappa > 0.81:
        print("Excellent agreement")
    elif kappa > 0.61:
        print("Good agreement")
    elif kappa > 0.41:
        print("Moderate agreement")
    else:
        print("Fair/Poor agreement - consider refining prompts")
```

---

## 11. NEXT STEPS

1. **Prepare**: Refine your PubMed search and export CSV
2. **Configure**: Adjust extraction schema for your specific needs
3. **Test**: Run screening on 50-100 articles first
4. **Validate**: Manually verify screening and extraction on sample
5. **Scale**: Run complete pipeline on full dataset
6. **Analyze**: Synthesize results and write narrative
7. **Report**: Follow PRISMA 2020 guidelines for final report

---

## 12. REFERENCES FOR IMPLEMENTATION

- **PRISMA 2020**: http://www.prisma-statement.org/
- **QUADAS-2**: Quality Assessment of Diagnostic Accuracy Studies
- **Claude API Documentation**: https://docs.anthropic.com
- **MEDLINE/PubMed Format**: https://www.nlm.nih.gov/bsd/medline.html
