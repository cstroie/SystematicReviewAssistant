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

class APIKeyError(Exception):
    """Custom exception for missing API keys"""
    def __init__(self, env_var):
        super().__init__()
        self.env_var = env_var
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
                raise APIKeyError(config['api_key_env'])
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


class PubMedQueryGenerator:
    """Generates PubMed query and review metadata from free-text task description"""
    
    def __init__(self, llm_client: DirectAPIClient, output_dir: Path):
        self.llm = llm_client
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.prompt = self._load_prompt('pubmed_query_gen')
    
    def _load_prompt(self, name: str) -> str:
        """Load prompt template from prompts directory"""
        prompt_path = Path(__file__).parent / 'prompts' / f'{name}.txt'
        try:
            return prompt_path.read_text(encoding='utf-8').strip()
        except IOError as e:
            raise ValueError(f"Failed to load prompt '{name}': {str(e)}") from e
    
    def generate(self, task_description: str):
        """Generate and save PubMed query components"""
        try:
            # Call LLM to generate components
            prompt = self.prompt.format(task_description=task_description)
            response_text = self.llm.call(prompt)
            
            # Extract JSON response
            json_match = re.search(r'{.*}', response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in LLM response")
            components = json.loads(json_match.group())
            
            # Validate components
            required_keys = ['query', 'topic', 'title']
            if not all(key in components for key in required_keys):
                missing = [key for key in required_keys if key not in components]
                raise ValueError(f"Missing required keys in response: {missing}")
            
            # Save outputs
            (self.output_dir / 'QUERY.txt').write_text(components['query'])
            (self.output_dir / 'TOPIC.txt').write_text(components['topic'])
            (self.output_dir / 'TITLE.txt').write_text(components['title'])
            
            print(f"✓ Generated PubMed query components:")
            print(f"  Query saved to: {self.output_dir/'QUERY.txt'}")
            print(f"  Topic saved to: {self.output_dir/'TOPIC.txt'}")
            print(f"  Title saved to: {self.output_dir/'TITLE.txt'}")
        except Exception as e:
            print(f"❌ Error generating PubMed components: {str(e)}")
            raise

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
        print(f"Pipeline initialized at {self.start_time}")
        print(f"Using {llm_client.provider} with model {llm_client.model}")
    
    def _load_prompt(self, name: str) -> str:
        """Load prompt template from prompts directory"""
        prompt_path = Path(__file__).parent / 'prompts' / f'{name}.txt'
        try:
            return prompt_path.read_text(encoding='utf-8').strip()
        except IOError as e:
            raise ValueError(f"Failed to load prompt '{name}': {str(e)}") from e
    
    def run_complete_pipeline(self, pubmed_file: str):
        """Execute the complete workflow from CSV to synthesis"""
        
        print("="*70)
        print("CDSS LITERATURE REVIEW PROCESSING PIPELINE")
        print("="*70)
        
        try:
            # Step 1: Load from cache or parse PubMed export
            articles_file = self.output_dir / "01_parsed_articles.json"
            if articles_file.exists():
                print("\n[STEP 1/6] Loading parsed articles from cache...")
                try:
                    articles = self._load_json(articles_file)
                    print(f"✓ Loaded {len(articles)} articles from {articles_file.name}")
                except Exception as e:
                    print(f"Cache read error: {str(e)}, re-parsing file", "WARN")
                    articles = self._parse_pubmed_export(pubmed_file)
                    self._save_json(articles, articles_file)
            else:
                print("\n[STEP 1/6] Parsing PubMed export...")
                articles = self._parse_pubmed_export(pubmed_file)
                self._save_json(articles, articles_file)
                print(f"✓ Parsed {len(articles)} articles from {pubmed_file}")
            
            # Step 2: Screen articles (cache-aware)
            screening_file = self.output_dir / "02_screening_results.json"
            if screening_file.exists():
                print("\n[STEP 2/6] Loading screening cache...")
                try:
                    cached_screening = self._load_json(screening_file)
                    cached_pmids = {r['pmid'] for r in cached_screening}
                    
                    # Find articles not in cache
                    new_articles = [a for a in articles if a['pmid'] not in cached_pmids]
                    
                    if new_articles:
                        print(f"  Found {len(cached_screening)} cached decisions")
                        print(f"  Screening {len(new_articles)} new articles...")
                        new_screening = self._screen_articles(new_articles)
                        screening_results = cached_screening + new_screening
                    else:
                        screening_results = cached_screening
                        print("✓ All articles already have screening decisions")
                    
                except Exception as e:
                    print(f"Cache error: {str(e)}, re-screening all", "WARN")
                    screening_results = self._screen_articles(articles)
            else:
                print("\n[STEP 2/6] Screening titles and abstracts...")
                screening_results = self._screen_articles(articles)
            
            # Always save updated screening results
            self._save_json(screening_results, screening_file)
            
            include_count = sum(1 for r in screening_results if r['decision'] == 'INCLUDE')
            exclude_count = sum(1 for r in screening_results if r['decision'] == 'EXCLUDE')
            uncertain_count = sum(1 for r in screening_results if r['decision'] == 'UNCERTAIN')
            
            print(f"✓ Screening complete:")
            print(f"  - INCLUDE: {include_count}")
            print(f"  - EXCLUDE: {exclude_count}")
            print(f"  - UNCERTAIN: {uncertain_count}")
            
            # Step 3: Extract data from included articles (with cache merging)
            extraction_file = self.output_dir / "03_extracted_data.json"
            included_pmids = {r['pmid'] for r in screening_results if r['decision'] == 'INCLUDE'}
            included_articles = [a for a in articles if a['pmid'] in included_pmids]
            
            if not included_articles:
                print("ERROR: No articles included after screening. Aborting.", "ERROR")
                return
                
            if extraction_file.exists():
                print("\n[STEP 3/6] Loading extracted data cache...")
                try:
                    cached_data = self._load_json(extraction_file)
                    cached_pmids = {d['pmid'] for d in cached_data if 'pmid' in d}
                    
                    # Find articles not in cache
                    new_articles = [a for a in included_articles if a['pmid'] not in cached_pmids]
                    
                    if new_articles:
                        print(f"  Found {len(cached_data)} cached extractions")
                        print(f"  Extracting data from {len(new_articles)} new articles...")
                        new_data = self._extract_article_data(new_articles)
                        extracted_data = cached_data + new_data
                    else:
                        extracted_data = cached_data
                        print("✓ All included articles already have extracted data")
                    
                except Exception as e:
                    print(f"Cache error: {str(e)}, re-extracting all", "WARN")
                    extracted_data = self._extract_article_data(included_articles)
            else:
                print("\n[STEP 3/6] Extracting data from included articles...")
                extracted_data = self._extract_article_data(included_articles)
            
            # Always save updated extracted data
            self._save_json(extracted_data, extraction_file)
            print(f"✓ Extracted data from {len(extracted_data)} articles")
            
            # Step 4: Assess quality (with cache merging)
            quality_file = self.output_dir / "04_quality_assessment.json"
            if quality_file.exists():
                print("\n[STEP 4/6] Loading quality assessment cache...")
                try:
                    cached_assessments = self._load_json(quality_file)
                    cached_pmids = {a['pmid'] for a in cached_assessments if 'pmid' in a}
                    
                    # Find articles not in cache
                    new_articles = [a for a in extracted_data if a['pmid'] not in cached_pmids]
                    
                    if new_articles:
                        print(f"  Found {len(cached_assessments)} cached assessments")
                        print(f"  Assessing quality for {len(new_articles)} new articles...")
                        new_included_articles = [a for a in included_articles if a['pmid'] not in cached_pmids]
                        new_assessments = self._assess_quality(new_articles, new_included_articles)
                        quality_assessments = cached_assessments + new_assessments
                    else:
                        quality_assessments = cached_assessments
                        print("✓ All included articles already have quality assessments")
                    
                except Exception as e:
                    print(f"Cache error: {str(e)}, re-assessing all", "WARN")
                    quality_assessments = self._assess_quality(extracted_data, included_articles)
            else:
                print("\n[STEP 4/6] Assessing study quality (QUADAS-2)...")
                quality_assessments = self._assess_quality(extracted_data, included_articles)
            
            # Always save updated assessments
            self._save_json(quality_assessments, quality_file)
            print(f"✓ Quality assessment complete for {len(quality_assessments)} studies")
            
            # Step 5: Synthesis
            print("\n[STEP 5/6] Performing thematic synthesis...")
            synthesis = self._perform_synthesis(extracted_data)
            synthesis_file = self.output_dir / "05_thematic_synthesis.txt"
            synthesis_file.write_text(synthesis)
            print(f"✓ Synthesis complete - {len(synthesis)} characters written")
            
            # Step 6: Generate summary table
            print("\n[STEP 6/6] Generating summary table...")
            self._generate_summary_table(extracted_data)
            
            # Final summary
            elapsed = (datetime.now() - self.start_time).total_seconds()
            print("="*70)
            print("PIPELINE COMPLETE")
            print(f"Results saved to: {self.output_dir}")
            print(f"Total time: {elapsed:.1f} seconds")
            print("="*70)
            
        except Exception as e:
            print(f"FATAL ERROR: {str(e)}", "ERROR")
            import traceback
            print(traceback.format_exc(), "ERROR")
            raise
    
    def _parse_pubmed_export(self, file_path: str) -> List[Dict]:
        """
        Parse PubMed export file (auto-detects format)
        
        Supports: CSV, MEDLINE (.txt), XML, JSON
        """
        try:
            from pubmed_parser import PubMedParser
        except ImportError:
            print("ERROR: pubmed_parser module not found in same directory", "ERROR")
            print("Make sure pubmed_parser.py is in the same folder as this script")
            raise
        
        # Parse file with auto-detection
        try:
            articles = PubMedParser.parse(file_path)
            print(f"✓ Parsed {len(articles)} articles from {Path(file_path).name}")
            
            if not articles:
                raise ValueError("No articles found in the file")
            
            
            return articles
            
        except Exception as e:
            print(f"Error parsing file: {str(e)}", "ERROR")
            raise
    
    def _screen_articles(self, articles: List[Dict]) -> List[Dict]:
        """Screen articles for inclusion based on title and abstract"""
        results = []
        
        screening_prompt = self._load_prompt('screening')
        
        for i, article in enumerate(articles):
            prompt = screening_prompt.format(
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
                    print(f"  Screened {i+1}/{len(articles)} articles...")
                    time.sleep(1)  # Rate limiting
                    
            except (json.JSONDecodeError, Exception) as e:
                print(f"Error screening {article['pmid']}: {str(e)}", "WARN")
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
        
        extraction_prompt = self._load_prompt('extraction')
        
        for i, article in enumerate(articles):
            prompt = extraction_prompt.format(
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
                    print(f"  Extracted {i+1}/{len(articles)} articles...")
                    time.sleep(1)
                    
            except (json.JSONDecodeError, Exception) as e:
                print(f"Error extracting {article['pmid']}: {str(e)}", "WARN")
                extracted.append({
                    'pmid': article['pmid'],
                    'title': article['title'],
                    'extraction_error': True
                })
        
        return extracted
    
    def _assess_quality(self, extracted_data: List[Dict], articles: List[Dict]) -> List[Dict]:
        """Assess study quality using QUADAS-2 framework"""
        quality_results = []
        
        quadas2_prompt = self._load_prompt('quality_assessment')
        
        for i, article in enumerate(articles):
            prompt = quadas2_prompt.format(
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
                    print(f"  Quality assessed {i+1}/{len(articles)} articles...")
                    
            except Exception as e:
                print(f"Error assessing {article['pmid']}: {str(e)}", "WARN")
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
            'studies_sample': extracted_data[:3],  # First 3 for context
            'total_count': len(extracted_data)
        }
        
        synthesis_template = self._load_prompt('synthesis')
        synthesis_prompt = synthesis_template.format(
            total_studies=len(extracted_data),
            data_sample=json.dumps(summary_dict, indent=2)
        )
        
        try:
            response_text = self.llm.call(synthesis_prompt)
            synthesis_text = response_text.strip()
            return synthesis_text
            
        except Exception as e:
            print(f"Error performing synthesis: {str(e)}", "ERROR")
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
            print("No valid data to create summary table", "WARN")
            return
        
        # Try using pandas if available
        if pd is not None:
            try:
                df = pd.DataFrame(rows)
                output_file = self.output_dir / "summary_characteristics_table.csv"
                df.to_csv(output_file, index=False)
                print(f"Summary table saved ({len(rows)} studies) - CSV format")
                return
            except Exception as e:
                print(f"Error creating pandas DataFrame: {str(e)}", "WARN")
        
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
            
            print(f"Summary table saved ({len(rows)} studies) - Manual CSV creation (no pandas)")
        except Exception as e:
            print(f"Error creating summary table: {str(e)}", "ERROR")
    
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
    parser.add_argument('--task', help='Free-text research topic description (generates PubMed query and metadata)')
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
    
    # Validate input file exists
    if not Path(args.input_file).exists():
        print(f"Error: Input file '{args.input_file}' not found")
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
        
        # Generate PubMed query components if task description provided
        output_dir = Path(args.output_dir)
        if args.task:
            print("\n" + "="*70)
            print("GENERATING PUBMED QUERY COMPONENTS")
            print("="*70)
            output_dir.mkdir(exist_ok=True, parents=True)
            generator = PubMedQueryGenerator(llm_client, output_dir)
            generator.generate(args.task)
            print("\n✓ PubMed query generation complete\n")
            return  # Stop after generating query components
        
        # Run full pipeline
        print(f"\nStarting full pipeline...\n")
        processor = CDSSLitReviewProcessor(
            llm_client=llm_client,
            output_dir=args.output_dir,
            log_verbose=not args.quiet
        )
        processor.run_complete_pipeline(args.input_file)
        
    except APIKeyError as e:
        print("\n" + "="*50)
        print("API KEY NOT FOUND!")
        print("="*50)
        print(f"You need to set the environment variable: {e.env_var}")
        print("\nTo set it temporarily for this session:")
        print(f"  export {e.env_var}=\"your-api-key-here\"")
        print("\nTo set it permanently, add the export to your ~/.bashrc or ~/.zshrc")
        show_provider_info()
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
