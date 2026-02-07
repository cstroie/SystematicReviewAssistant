#!/usr/bin/env python3
"""
Systematic Literature Review Processing Pipeline
Automate PubMed export analysis using LLMs for screening, extraction, and synthesis

Key features:
- Supports multiple PubMed formats (CSV, MEDLINE/XML/JSON auto-detection)
- Direct HTTP API integration with 100+ LLMs via multiple providers
- Complete workflow from screening to thematic synthesis
- Configurable outputs with structured JSON/CSV reports

Usage:
    # Using Anthropic (default)
    export ANTHROPIC_API_KEY="sk-ant-..."
    python cdss_lit_review_pipeline_v3.py pubmed_export.csv
    
    # Using OpenRouter
    export OPENROUTER_API_KEY="sk-or-..."
    python cdss_lit_review_pipeline_v3.py pubmed_export.csv --provider openrouter --model meta-llama/llama-2-70b-chat-hf
    
    # Using Together.ai
    export TOGETHER_API_KEY="..."
    python cdss_lit_review_pipeline_v3.py pubmed_export.csv --provider together --model meta-llama/Llama-2-70b-chat-hf
    
    # Using Groq
    export GROQ_API_KEY="..."
    python cdss_lit_review_pipeline_v3.py pubmed_export.csv --provider groq --model mixtral-8x7b-32768
    
    # Using local Ollama
    python cdss_lit_review_pipeline_v3.py pubmed_export.csv --provider local --model llama2
"""

import json
import csv
import time
import sys
import os
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import re

try:
    import pandas as pd
except ImportError:
    pd = None


# API Configuration for different providers
API_CONFIGS = {
    'anthropic': {
        'base_url': 'https://api.anthropic.com/v1',
        'endpoint': '/messages',
        'api_key_env': 'ANTHROPIC_API_KEY',
        'default_model': 'claude-opus-4-5-20251101',
        'description': 'Anthropic Claude models',
        'headers_fn': lambda key, model: {
            'Content-Type': 'application/json',
            'x-api-key': key,
            'anthropic-version': '2023-06-01'
        },
        'body_fn': lambda prompt, model: {
            'model': model,
            'max_tokens': 4096,
            'messages': [
                {'role': 'user', 'content': prompt}
            ]
        },
        'response_fn': lambda resp: resp.get('content', [{}])[0].get('text', '')
    },
    'openrouter': {
        'base_url': 'https://openrouter.ai/api/v1',
        'endpoint': '/chat/completions',
        'api_key_env': 'OPENROUTER_API_KEY',
        'default_model': 'meta-llama/llama-2-70b-chat-hf',
        'description': 'OpenRouter (100+ models available)',
        'headers_fn': lambda key, model: {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {key}',
            'HTTP-Referer': 'https://github.com/user/cdss-lit-review'
        },
        'body_fn': lambda prompt, model: {
            'model': model,
            'max_tokens': 4096,
            'temperature': 0.3,
            'messages': [
                {'role': 'user', 'content': prompt}
            ]
        },
        'response_fn': lambda resp: resp.get('choices', [{}])[0].get('message', {}).get('content', '')
    },
    'together': {
        'base_url': 'https://api.together.xyz/v1',
        'endpoint': '/chat/completions',
        'api_key_env': 'TOGETHER_API_KEY',
        'default_model': 'meta-llama/Llama-2-70b-chat-hf',
        'description': 'Together.ai (various open source models)',
        'headers_fn': lambda key, model: {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {key}'
        },
        'body_fn': lambda prompt, model: {
            'model': model,
            'max_tokens': 4096,
            'temperature': 0.3,
            'messages': [
                {'role': 'user', 'content': prompt}
            ]
        },
        'response_fn': lambda resp: resp.get('choices', [{}])[0].get('message', {}).get('content', '')
    },
    'groq': {
        'base_url': 'https://api.groq.com/openai/v1',
        'endpoint': '/chat/completions',
        'api_key_env': 'GROQ_API_KEY',
        'default_model': 'mixtral-8x7b-32768',
        'description': 'Groq (very fast inference)',
        'headers_fn': lambda key, model: {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {key}'
        },
        'body_fn': lambda prompt, model: {
            'model': model,
            'max_tokens': 8192,
            'temperature': 0.3,
            'messages': [
                {'role': 'user', 'content': prompt}
            ]
        },
        'response_fn': lambda resp: resp.get('choices', [{}])[0].get('message', {}).get('content', '')
    },
    'local': {
        'base_url': 'http://localhost:11434/v1',
        'endpoint': '/chat/completions',
        'api_key_env': None,
        'default_model': 'llama2',
        'description': 'Local models via Ollama/vLLM',
        'headers_fn': lambda key, model: {
            'Content-Type': 'application/json'
        },
        'body_fn': lambda prompt, model: {
            'model': model,
            'max_tokens': 2048,
            'temperature': 0.3,
            'messages': [
                {'role': 'user', 'content': prompt}
            ]
        },
        'response_fn': lambda resp: resp.get('choices', [{}])[0].get('message', {}).get('content', '')
    }
}


class DirectAPIClient:
    """Direct HTTP client for any OpenAI-compatible API (no external packages)"""
    
    def __init__(self, provider: str = 'anthropic', model: Optional[str] = None,
                 api_url: Optional[str] = None, api_key: Optional[str] = None,
                 timeout: int = 30):
        """
        Initialize API client
        
        Args:
            provider: 'anthropic', 'openrouter', 'together', 'local', 'groq'
            model: Model name (uses provider default if not specified)
            api_url: Custom API URL (overrides provider default)
            api_key: API key (uses env var if not specified)
            timeout: Request timeout in seconds
        """
        self.provider = provider.lower()
        self.timeout = timeout
        
        if self.provider not in API_CONFIGS:
            raise ValueError(f"Unknown provider: {provider}. Choose from: {list(API_CONFIGS.keys())}")
        
        config = API_CONFIGS[self.provider]
        
        # Get API endpoint
        self.base_url = api_url or config['base_url']
        self.endpoint = config['endpoint']
        self.full_url = self.base_url.rstrip('/') + self.endpoint
        
        # Get model
        self.model = model or config['default_model']
        
        # Get API key
        if config['api_key_env']:
            self.api_key = api_key or os.getenv(config['api_key_env'])
            if not self.api_key and provider != 'local':
                raise ValueError(f"API key not found. Set {config['api_key_env']} environment variable")
        else:
            self.api_key = None  # Local models don't need a key
        
        # Store config functions
        self.headers_fn = config['headers_fn']
        self.body_fn = config['body_fn']
        self.response_fn = config['response_fn']
        
        print(f"✓ Initialized {config['description']}")
        print(f"  Model: {self.model}")
        print(f"  API Endpoint: {self.full_url}")
    
    def call(self, prompt: str, max_retries: int = 3) -> str:
        """
        Call LLM API with direct HTTP request
        
        Args:
            prompt: Input prompt
            max_retries: Number of retries on failure
        
        Returns:
            Model response text
        """
        
        # Prepare request
        headers = self.headers_fn(self.api_key, self.model)
        body = self.body_fn(prompt, self.model)
        body_json = json.dumps(body).encode('utf-8')
        
        # Retry loop
        for attempt in range(max_retries):
            try:
                # Create request
                req = urllib.request.Request(
                    self.full_url,
                    data=body_json,
                    headers=headers,
                    method='POST'
                )
                
                # Make request
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    response_data = json.loads(response.read().decode('utf-8'))
                    result = self.response_fn(response_data)
                    
                    if not result:
                        raise ValueError("Empty response from API")
                    
                    return result
                
            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8')
                
                # Check for rate limiting
                if e.code == 429:
                    wait_time = 5 * (attempt + 1)
                    print(f"  Rate limited. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                
                # Check for other retryable errors
                if e.code in [500, 502, 503, 504]:
                    wait_time = 2 * (attempt + 1)
                    print(f"  Server error ({e.code}). Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                
                # Non-retryable error
                raise ValueError(f"API error {e.code}: {error_body}")
            
            except urllib.error.URLError as e:
                if attempt < max_retries - 1:
                    wait_time = 2 * (attempt + 1)
                    print(f"  Connection error: {e.reason}. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                raise ValueError(f"Connection error: {e.reason}")
            
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2
                    print(f"  Error: {str(e)}. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                raise ValueError(f"Error calling API: {str(e)}")
        
        raise ValueError("Failed after all retries")


class CDSSLitReviewProcessor:
    """Main pipeline processor for systematic literature review"""
    
    def __init__(self, llm_client: DirectAPIClient, output_dir: str = "lit_review_output",
                 log_verbose: bool = True):
        """Initialize processor with LLM client"""
        self.llm = llm_client
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.log_verbose = log_verbose
        self.start_time = datetime.now()
        
        # Initialize log file
        self.log_file = self.output_dir / "processing_log.txt"
        self._log(f"Pipeline initialized at {self.start_time}")
        self._log(f"Using {llm_client.provider} with model {llm_client.model}")
    
    def _log(self, message: str, level: str = "INFO"):
        """Log messages to file and optionally console"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {level}: {message}"
        
        # Write to log file
        with open(self.log_file, 'a') as f:
            f.write(log_message + "\n")
        
        # Print to console if verbose
        if self.log_verbose:
            print(log_message)
    
    def run_complete_pipeline(self, pubmed_csv_file: str):
        """Execute the complete workflow from CSV to synthesis"""
        
        self._log("="*70, "HEADER")
        self._log("CDSS LITERATURE REVIEW PROCESSING PIPELINE", "HEADER")
        self._log("="*70, "HEADER")
        
        try:
            # Step 1: Load from cache or parse PubMed export
            articles_file = self.output_dir / "01_parsed_articles.json"
            if articles_file.exists():
                self._log("[STEP 1/6] Loading parsed articles from cache...")
                try:
                    articles = self._load_json(articles_file)
                    self._log(f"✓ Loaded {len(articles)} articles from {articles_file.name}")
                except Exception as e:
                    self._log(f"Cache read error: {str(e)}, re-parsing file", "WARN")
                    articles = self._parse_pubmed_export(pubmed_csv_file)
                    self._save_json(articles, articles_file)
            else:
                self._log("[STEP 1/6] Parsing PubMed export...")
                articles = self._parse_pubmed_export(pubmed_csv_file)
                self._save_json(articles, articles_file)
                self._log(f"✓ Parsed {len(articles)} articles from {pubmed_csv_file}")
            
            # Step 2: Screen articles (cache-aware)
            screening_file = self.output_dir / "02_screening_results.json"
            if screening_file.exists():
                self._log("[STEP 2/6] Loading screening cache...")
                try:
                    cached_screening = self._load_json(screening_file)
                    cached_pmids = {r['pmid'] for r in cached_screening}
                    
                    # Find articles not in cache
                    new_articles = [a for a in articles if a['pmid'] not in cached_pmids]
                    
                    if new_articles:
                        self._log(f"  Found {len(cached_screening)} cached decisions")
                        self._log(f"  Screening {len(new_articles)} new articles...")
                        new_screening = self._screen_articles(new_articles)
                        screening_results = cached_screening + new_screening
                    else:
                        screening_results = cached_screening
                        self._log("✓ All articles already have screening decisions")
                    
                except Exception as e:
                    self._log(f"Cache error: {str(e)}, re-screening all", "WARN")
                    screening_results = self._screen_articles(articles)
            else:
                self._log("[STEP 2/6] Screening titles and abstracts...")
                screening_results = self._screen_articles(articles)
            
            # Always save updated screening results
            self._save_json(screening_results, screening_file)
            
            include_count = sum(1 for r in screening_results if r['decision'] == 'INCLUDE')
            exclude_count = sum(1 for r in screening_results if r['decision'] == 'EXCLUDE')
            uncertain_count = sum(1 for r in screening_results if r['decision'] == 'UNCERTAIN')
            
            self._log(f"✓ Screening complete:")
            self._log(f"  - INCLUDE: {include_count}")
            self._log(f"  - EXCLUDE: {exclude_count}")
            self._log(f"  - UNCERTAIN: {uncertain_count}")
            
            # Step 3: Extract data from included articles (with cache merging)
            extraction_file = self.output_dir / "03_extracted_data.json"
            included_pmids = {r['pmid'] for r in screening_results if r['decision'] == 'INCLUDE'}
            included_articles = [a for a in articles if a['pmid'] in included_pmids]
            
            if not included_articles:
                self._log("ERROR: No articles included after screening. Aborting.", "ERROR")
                return
                
            if extraction_file.exists():
                self._log("[STEP 3/6] Loading extracted data cache...")
                try:
                    cached_data = self._load_json(extraction_file)
                    cached_pmids = {d['pmid'] for d in cached_data if 'pmid' in d}
                    
                    # Find articles not in cache
                    new_articles = [a for a in included_articles if a['pmid'] not in cached_pmids]
                    
                    if new_articles:
                        self._log(f"  Found {len(cached_data)} cached extractions")
                        self._log(f"  Extracting data from {len(new_articles)} new articles...")
                        new_data = self._extract_article_data(new_articles)
                        extracted_data = cached_data + new_data
                    else:
                        extracted_data = cached_data
                        self._log("✓ All included articles already have extracted data")
                    
                except Exception as e:
                    self._log(f"Cache error: {str(e)}, re-extracting all", "WARN")
                    extracted_data = self._extract_article_data(included_articles)
            else:
                self._log("[STEP 3/6] Extracting data from included articles...")
                extracted_data = self._extract_article_data(included_articles)
            
            # Always save updated extracted data
            self._save_json(extracted_data, extraction_file)
            self._log(f"✓ Extracted data from {len(extracted_data)} articles")
            
            # Step 4: Assess quality (with cache merging)
            quality_file = self.output_dir / "04_quality_assessment.json"
            if quality_file.exists():
                self._log("[STEP 4/6] Loading quality assessment cache...")
                try:
                    cached_assessments = self._load_json(quality_file)
                    cached_pmids = {a['pmid'] for a in cached_assessments if 'pmid' in a}
                    
                    # Find articles not in cache
                    new_articles = [a for a in extracted_data if a['pmid'] not in cached_pmids]
                    
                    if new_articles:
                        self._log(f"  Found {len(cached_assessments)} cached assessments")
                        self._log(f"  Assessing quality for {len(new_articles)} new articles...")
                        new_included_articles = [a for a in included_articles if a['pmid'] not in cached_pmids]
                        new_assessments = self._assess_quality(new_articles, new_included_articles)
                        quality_assessments = cached_assessments + new_assessments
                    else:
                        quality_assessments = cached_assessments
                        self._log("✓ All included articles already have quality assessments")
                    
                except Exception as e:
                    self._log(f"Cache error: {str(e)}, re-assessing all", "WARN")
                    quality_assessments = self._assess_quality(extracted_data, included_articles)
            else:
                self._log("[STEP 4/6] Assessing study quality (QUADAS-2)...")
                quality_assessments = self._assess_quality(extracted_data, included_articles)
            
            # Always save updated assessments
            self._save_json(quality_assessments, quality_file)
            self._log(f"✓ Quality assessment complete for {len(quality_assessments)} studies")
            
            # Step 5: Synthesis
            self._log("[STEP 5/6] Performing thematic synthesis...")
            synthesis = self._perform_synthesis(extracted_data)
            # Save as LaTeX document
            synthesis_file = self.output_dir / "05_thematic_synthesis.tex"
            latex_doc = """\\documentclass{article}
\\title{Systematic Review Thematic Synthesis}
\\author{Auto-generated by Literature Review Pipeline}
\\date{\\today}

\\begin{document}

\\maketitle

%s
\\end{document}""" % synthesis.replace('%', '\\%').replace('_', '\\_')
            
            synthesis_file.write_text(latex_doc)
            self._log(f"✓ LaTeX synthesis document saved - {len(latex_doc)} characters")
            
            # Step 6: Generate summary table
            self._log("[STEP 6/6] Generating summary table...")
            self._generate_summary_table(extracted_data)
            
            # Final summary
            elapsed = (datetime.now() - self.start_time).total_seconds()
            self._log("\n" + "="*70, "HEADER")
            self._log("PIPELINE COMPLETE", "HEADER")
            self._log(f"Results saved to: {self.output_dir}", "HEADER")
            self._log(f"Total time: {elapsed:.1f} seconds", "HEADER")
            self._log("="*70, "HEADER")
            
        except Exception as e:
            self._log(f"FATAL ERROR: {str(e)}", "ERROR")
            import traceback
            self._log(traceback.format_exc(), "ERROR")
            raise
    
    def _parse_pubmed_export(self, file_path: str) -> List[Dict]:
        """
        Parse PubMed export file (auto-detects format)
        
        Supports: CSV, MEDLINE (.txt), XML, JSON
        """
        try:
            from pubmed_parser import PubMedParser
        except ImportError:
            self._log("ERROR: pubmed_parser module not found in same directory", "ERROR")
            self._log("Make sure pubmed_parser.py is in the same folder as this script")
            raise
        
        # Parse file with auto-detection
        try:
            articles = PubMedParser.parse(file_path)
            self._log(f"✓ Parsed {len(articles)} articles from {Path(file_path).name}")
            
            if not articles:
                raise ValueError("No articles found in the file")
            
            
            return articles
            
        except Exception as e:
            self._log(f"Error parsing file: {str(e)}", "ERROR")
            raise
    
    def _screen_articles(self, articles: List[Dict]) -> List[Dict]:
        """Screen articles for inclusion based on title and abstract"""
        results = []
        
        screening_prompt_template = """You are screening articles for a systematic review on:
"Clinical Decision Support Systems in Medical Imaging/Radiology"

INCLUSION CRITERIA:
- Describes or evaluates a clinical decision support system/tool
- Applied to medical imaging (radiology, CT, MRI, ultrasound, pathology imaging, etc.)
- Reports clinical outcomes, diagnostic accuracy, or user satisfaction

EXCLUSION CRITERIA:
- Focus on imaging physics/reconstruction without clinical application
- CDSS applied to non-imaging domains
- Literature reviews without primary research
- Opinion pieces without data or methods
- Not available in English

PMID: {pmid}
TITLE: {title}
ABSTRACT: {abstract}

Classify as:
- INCLUDE: Meets all inclusion criteria
- EXCLUDE: Meets exclusion criteria
- UNCERTAIN: Unclear or borderline - needs full-text review

Respond ONLY in this JSON format:
{{
  "pmid": "{pmid}",
  "decision": "INCLUDE|EXCLUDE|UNCERTAIN",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation",
  "key_terms": ["relevant", "keywords"]
}}"""
        
        for i, article in enumerate(articles):
            prompt = screening_prompt_template.format(
                pmid=article['pmid'],
                title=article['title'],
                abstract=article['abstract']
            )
            
            try:
                response_text = self.llm.call(prompt)
                
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    result = json.loads(response_text)
                
                results.append(result)
                
                if (i + 1) % 10 == 0:
                    self._log(f"  Screened {i+1}/{len(articles)} articles...")
                    time.sleep(1)  # Rate limiting
                    
            except (json.JSONDecodeError, Exception) as e:
                self._log(f"Error screening {article['pmid']}: {str(e)}", "WARN")
                results.append({
                    'pmid': article['pmid'],
                    'decision': 'UNCERTAIN',
                    'confidence': 0.0,
                    'reasoning': 'Processing error',
                    'key_terms': []
                })
        
        return results
    
    def _extract_article_data(self, articles: List[Dict]) -> List[Dict]:
        """Extract structured data from included articles"""
        extracted = []
        
        extraction_prompt_template = """Extract structured information from this research article.
Return ONLY valid JSON with no markdown formatting.

ARTICLE:
PMID: {pmid}
TITLE: {title}
ABSTRACT: {abstract}

Extract and return this JSON structure (use null for unavailable data):
{{
  "pmid": "{pmid}",
  "title": "{title}",
  "year": "publication year (integer)",
  "study_design": "RCT|Retrospective|Prospective|Case Series|Cross-sectional|Other",
  "sample_size": {{
    "total_patients": "number or null",
    "total_images": "number or null"
  }},
  "clinical_domain": "specific clinical application (e.g., 'Breast Cancer Detection')",
  "imaging_modality": ["list", "of", "modalities"],
  "cdss_type": "AI/ML-based|Rule-based|Hybrid|Statistical",
  "cdss_name": "system name or 'Not specified'",
  "primary_outcomes": ["list", "of", "outcome", "measures"],
  "key_metrics": {{
    "sensitivity": "value or null",
    "specificity": "value or null",
    "auc": "value or null",
    "accuracy": "value or null"
  }},
  "comparison": "compared against what? (e.g., radiologist alone, standard of care)",
  "main_findings": "1-2 sentence summary of key results",
  "limitations": ["list", "of", "limitations"],
  "clinical_implications": "stated implications or clinical impact"
}}"""
        
        for i, article in enumerate(articles):
            prompt = extraction_prompt_template.format(
                pmid=article['pmid'],
                title=article['title'],
                abstract=article['abstract']
            )
            
            try:
                response_text = self.llm.call(prompt)
                
                # Extract JSON
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    data = json.loads(response_text)
                
                extracted.append(data)
                
                if (i + 1) % 5 == 0:
                    self._log(f"  Extracted {i+1}/{len(articles)} articles...")
                    time.sleep(1)
                    
            except (json.JSONDecodeError, Exception) as e:
                self._log(f"Error extracting {article['pmid']}: {str(e)}", "WARN")
                extracted.append({
                    'pmid': article['pmid'],
                    'title': article['title'],
                    'extraction_error': True
                })
        
        return extracted
    
    def _assess_quality(self, extracted_data: List[Dict], articles: List[Dict]) -> List[Dict]:
        """Assess study quality using QUADAS-2 framework"""
        quality_results = []
        
        quadas2_prompt_template = """Assess the quality of this diagnostic study using QUADAS-2 framework.

PMID: {pmid}
TITLE: {title}
ABSTRACT: {abstract}

Evaluate these QUADAS-2 domains (answer: Yes|No|Unclear for each):

1. PATIENT SELECTION
   - Was a consecutive/random sample enrolled?
   - Was case-control design avoided?

2. INDEX TEST  
   - Were index test results blinded to reference standard?
   - Were cutoffs pre-specified?

3. REFERENCE STANDARD
   - Is reference standard appropriate?
   - Were results blinded to index test?

4. FLOW AND TIMING
   - Was interval between tests appropriate?
   - Did all patients receive reference standard?

Return ONLY JSON:
{{
  "pmid": "{pmid}",
  "domains": {{
    "patient_selection": "Yes|No|Unclear",
    "index_test": "Yes|No|Unclear", 
    "reference_standard": "Yes|No|Unclear",
    "flow_timing": "Yes|No|Unclear"
  }},
  "overall_bias": "Low|Moderate|High",
  "applicability": "Low|Moderate|High",
  "notes": "brief justification"
}}"""
        
        for i, article in enumerate(articles):
            prompt = quadas2_prompt_template.format(
                pmid=article['pmid'],
                title=article['title'],
                abstract=article['abstract']
            )
            
            try:
                response_text = self.llm.call(prompt)
                
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    result = json.loads(response_text)
                
                quality_results.append(result)
                
                if (i + 1) % 5 == 0:
                    self._log(f"  Quality assessed {i+1}/{len(articles)} articles...")
                    
            except Exception as e:
                self._log(f"Error assessing {article['pmid']}: {str(e)}", "WARN")
                quality_results.append({
                    'pmid': article['pmid'],
                    'assessment_error': True
                })
        
        return quality_results
    
    def _perform_synthesis(self, extracted_data: List[Dict]) -> str:
        """Perform thematic synthesis and identify patterns"""
        
        # Prepare summary of extracted data
        summary_dict = {
            'total_studies': len(extracted_data),
            'studies_sample': extracted_data[:3],
            'total_count': len(extracted_data)
        }
        
        synthesis_prompt = f"""You are writing a thematic synthesis section for a systematic review on 
"Clinical Decision Support Systems in Medical Imaging/Radiology".

We have analyzed {len(extracted_data)} studies. Here's a sample of the extracted data:

{json.dumps(summary_dict, indent=2)}

Based on this analysis and typical patterns in this field, provide a comprehensive synthesis with these sections:

1. STUDY CHARACTERISTICS
   - Range of years, study designs, sample sizes
   - Imaging modalities covered
   - Clinical domains studied

2. TYPES OF CDSS SYSTEMS
   - Distribution by type (AI/ML vs rule-based)
   - Technology trends over time

3. CLINICAL PERFORMANCE
   - Range of reported metrics (sensitivity, specificity, AUC)
   - Best and worst performing systems
   - Performance by clinical domain

4. THEMATIC ANALYSIS
   - Common themes across studies
   - Key findings and consistencies
   - Important variations and contradictions

5. METHODOLOGICAL ASSESSMENT  
   - Common strengths
   - Prevalent limitations
   - Quality trends

6. CLINICAL IMPLICATIONS
   - Evidence for clinical implementation
   - Adoption barriers
   - Impact on clinical workflows

7. RESEARCH GAPS AND RECOMMENDATIONS
   - Underrepresented clinical domains
   - Methodological gaps
   - Recommendations for future research

Write in clear, structured prose suitable for a systematic review report."""
        
        try:
            synthesis_text = self.llm.call(synthesis_prompt)
            return synthesis_text
            
        except Exception as e:
            self._log(f"Error performing synthesis: {str(e)}", "ERROR")
            return "Error generating synthesis"
    
    def _generate_summary_table(self, extracted_data: List[Dict]):
        """Generate CSV summary table with or without pandas"""
        
        rows = []
        for item in extracted_data:
            if 'extraction_error' in item:
                continue
            
            # Handle imaging_modality - could be list, string, or missing
            modality = item.get('imaging_modality', [])
            if isinstance(modality, list):
                modality_str = ', '.join(str(m) for m in modality) if modality else ''
            else:
                modality_str = str(modality) if modality else ''
            
            # Handle sample size
            sample_size = item.get('sample_size', {})
            if isinstance(sample_size, dict):
                n_patients = sample_size.get('total_patients', '')
            else:
                n_patients = ''
            
            # Handle key metrics
            key_metrics = item.get('key_metrics', {})
            if isinstance(key_metrics, dict):
                sensitivity = key_metrics.get('sensitivity', '')
                specificity = key_metrics.get('specificity', '')
                auc = key_metrics.get('auc', '')
                accuracy = key_metrics.get('accuracy', '')
            else:
                sensitivity = specificity = auc = accuracy = ''
            
            rows.append({
                'PMID': item.get('pmid', ''),
                'Year': item.get('year', ''),
                'Study Design': item.get('study_design', ''),
                'Clinical Domain': item.get('clinical_domain', ''),
                'Imaging Modality': modality_str,
                'CDSS Type': item.get('cdss_type', ''),
                'Sample Size (N)': n_patients,
                'Sensitivity': sensitivity,
                'Specificity': specificity,
                'AUC': auc,
                'Accuracy': accuracy,
                'Main Findings': str(item.get('main_findings', ''))[:100]
            })
        
        if not rows:
            self._log("No valid data to create summary table", "WARN")
            return
        
        # Try using pandas if available
        if pd is not None:
            try:
                df = pd.DataFrame(rows)
                output_file = self.output_dir / "summary_characteristics_table.csv"
                df.to_csv(output_file, index=False)
                self._log(f"Summary table saved ({len(rows)} studies) - CSV format")
                return
            except Exception as e:
                self._log(f"Error creating pandas DataFrame: {str(e)}", "WARN")
        
        # Fall back to manual CSV creation without pandas
        try:
            output_file = self.output_dir / "summary_characteristics_table.csv"
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                if rows:
                    # Write header
                    headers = list(rows[0].keys())
                    f.write(','.join(f'"{h}"' for h in headers) + '\n')
                    
                    # Write rows
                    for row in rows:
                        values = [str(row.get(h, '')).replace('"', '""') for h in headers]
                        f.write(','.join(f'"{v}"' for v in values) + '\n')
            
            self._log(f"Summary table saved ({len(rows)} studies) - Manual CSV creation (no pandas)")
        except Exception as e:
            self._log(f"Error creating summary table: {str(e)}", "ERROR")
    
    def _save_json(self, data: any, filepath: Path):
        """Save data as formatted JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
    def _load_json(self, filepath: Path) -> any:
        """Load data from JSON"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)


def create_parser():
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        description='Systematic Literature Review Processor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with Anthropic Claude (needs API key):
  %(prog)s pubmed_results.csv
  
  # Use OpenRouter's LLaMA 2 (specify model):
  %(prog)s pubmed.txt --provider openrouter --model meta-llama/llama-2-70b-chat-hf
  
  # Local Ollama model (http://localhost:11434):
  %(prog)s pubmed.xml --provider local --model llama2
  
Supported Providers:
  anthropic   - Anthropic Claude (default)
  openrouter  - OpenRouter (100+ models)
  together    - Together.ai
  groq        - Groq (fast inference)
  local       - Local models (Ollama/vLLM)
        """
    )
    
    parser.add_argument('input_file', help='PubMed export file (CSV/XML/MEDLINE/TXT/JSON)')
    parser.add_argument('--provider', choices=list(API_CONFIGS.keys()),
                       default='anthropic', help='LLM provider')
    parser.add_argument('--model', help='Model name (uses provider default if not specified)')
    parser.add_argument('--api-url', help='Custom API URL (overrides provider default)')
    parser.add_argument('--api-key', help='API key (uses env var if not specified)')
    parser.add_argument('--output-dir', default='lit_review_output', help='Output directory')
    parser.add_argument('--quiet', action='store_true', help='Suppress log output')
    
    return parser


def show_provider_info():
    """Show information about available providers"""
    print("\n" + "="*70)
    print("AVAILABLE LLM PROVIDERS (Direct HTTP - No External Packages)")
    print("="*70 + "\n")
    
    for provider_name, config in API_CONFIGS.items():
        print(f"Provider: {provider_name.upper()}")
        print(f"  Description: {config['description']}")
        print(f"  Default Model: {config['default_model']}")
        if config['api_key_env']:
            print(f"  API Key Env Var: {config['api_key_env']}")
        print()


def main():
    """Systematic literature review processing pipeline"""
    parser = create_parser()
    
    # Show help if no args
    if len(sys.argv) == 1:
        parser.print_help()
        show_provider_info()
        sys.exit(0)
    
    args = parser.parse_args()
    
    # Validate CSV file exists
    if not Path(args.csv_file).exists():
        print(f"Error: CSV file '{args.csv_file}' not found")
        sys.exit(1)
    
    # Show provider info if requested
    if args.provider not in API_CONFIGS:
        print(f"Error: Unknown provider '{args.provider}'")
        show_provider_info()
        sys.exit(1)
    
    try:
        # Initialize LLM client
        print(f"\nInitializing LLM client...")
        llm_client = DirectAPIClient(
            provider=args.provider,
            model=args.model,
            api_url=args.api_url,
            api_key=args.api_key
        )
        
        # Run pipeline
        print(f"\nStarting pipeline...\n")
        processor = CDSSLitReviewProcessor(
            llm_client=llm_client,
            output_dir=args.output_dir,
            log_verbose=not args.quiet
        )
        processor.run_complete_pipeline(args.csv_file)
        
    except KeyError as e:
        print(f"Error: Missing API key - {str(e)}")
        show_provider_info()
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
