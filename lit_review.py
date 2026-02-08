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
import re
import random
from typing import Dict, Any
import html

MAX_PROMPT_SIZE = 1 * 1024 * 1024  # 1MB
MAX_INPUT_SIZE = 10 * 1024 * 1024  # 10MB

def validate_file_path(path: str, max_size: Optional[int] = None) -> Path:
    """Validate and normalize file path to prevent directory traversal"""
    path_obj = Path(path).resolve()
    
    if not path_obj.exists():
        raise ValueError(f"File does not exist: {path}")
    if path_obj.is_dir():
        raise ValueError(f"Path is a directory: {path}")
    
    # Check file size limit if specified
    if max_size is not None:
        file_size = path_obj.stat().st_size
        if file_size > max_size:
            raise ValueError(f"File {path} size {file_size} exceeds maximum allowed {max_size} bytes")
    
    return path_obj

def sanitize_filename(name: str) -> str:
    """Sanitize filename to prevent path traversal"""
    # Remove any path separators and other dangerous characters
    cleaned = re.sub(r'[\\/:\*\?"<>\|\s]', '_', name)
    return cleaned[:200]  # Prevent excessively long filenames

def sanitize_api_input(text: str) -> str:
    """Basic sanitization for text used in API calls"""
    # Remove control characters and limit length
    sanitized = re.sub(r'[\x00-\x1F\x7F]', '', text)
    return sanitized[:10000]  # Limit to reasonable length

class APIKeyError(Exception):
    """Custom exception for missing API keys"""
    def __init__(self, env_var):
        super().__init__()
        self.env_var = env_var
from pathlib import Path
from datetime import datetime
import os
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
    
    def __init__(self, provider: str = 'anthropic', model: Optional[str] = None,
                 api_url: Optional[str] = None, api_key: Optional[str] = None,
                 timeout: int = 30, max_requests: int = 60, rate_period: int = 60):
        """
        Initialize API client
        
        Args:
            provider: 'anthropic', 'openrouter', 'together', 'local', 'groq'
            model: Model name (uses provider default if not specified)
            api_url: Custom API URL (overrides provider default)
            api_key: API key (uses env var if not specified)
            timeout: Request timeout in seconds
            max_requests: Max requests per rate_period
            rate_period: Time period (seconds) for rate limiting
        """
        self.provider = provider.lower()
        self.timeout = timeout
        self.max_requests = max_requests
        self.rate_period = rate_period
        self.request_times = []
        
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
        print(f"  Rate limit: {max_requests} requests per {rate_period} seconds")

    def _enforce_rate_limit(self):
        """Enforce token bucket rate limiting"""
        now = time.time()
        
        # Remove request timestamps older than our rate period
        self.request_times = [t for t in self.request_times if now - t < self.rate_period]
        
        if len(self.request_times) >= self.max_requests:
            oldest_request = self.request_times[0]
            wait_time = self.rate_period - (now - oldest_request)
            if wait_time > 0:
                print(f"  Rate limit exceeded. Waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
        
        self.request_times.append(time.time())

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
                # Enforce rate limiting
                self._enforce_rate_limit()
                
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
                    
                    # Validate and sanitize response for security
                    validated_result = self.validate_api_response(result)
                    
                    return validated_result
                
            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8')
                status_code = e.code
                
                # Check for rate limiting
                if status_code == 429:
                    backoff = 2 ** attempt
                    jitter = 1 + random.random()
                    wait_time = min(backoff * jitter, 30)  # Cap at 30s
                    print(f"  Rate limited (HTTP 429). Waiting {wait_time:.1f}s before retry #{attempt+1}...")
                    time.sleep(wait_time)
                    continue
                
                # Check for other retryable errors
                if status_code in [408, 500, 502, 503, 504]:
                    backoff = 2 ** attempt
                    wait_time = min(backoff + random.uniform(0, 1), 10)  # Cap at 10s
                    print(f"  Server error ({status_code}). Waiting {wait_time:.1f}s before retry #{attempt+1}...")
                    time.sleep(wait_time)
                    continue
                
                # Non-retryable error
                raise ValueError(f"API error {status_code}: {error_body}")
            
            except urllib.error.URLError as e:
                if attempt < max_retries - 1:
                    backoff = 2 ** attempt
                    wait_time = min(backoff + random.uniform(0, 1), 10)
                    print(f"  Connection error: {e.reason}. Waiting {wait_time:.1f}s before retry #{attempt+1}...")
                    time.sleep(wait_time)
                    continue
                raise ValueError(f"Connection error: {e.reason}")
            
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 1 + random.uniform(0, 1)
                    print(f"  Error: {str(e)}. Waiting {wait_time:.1f}s before retry #{attempt+1}...")
                    time.sleep(wait_time)
                    continue
                raise ValueError(f"Error calling API: {str(e)}")
        
        raise ValueError(f"Failed after {max_retries} retries")

    def validate_api_response(self, content: str) -> str:
        """Validate and sanitize API response for security"""
        # Check for suspicious HTML patterns
        html_patterns = [
            r'<script.*?>',   # Script tags
            r'on\w+\s*=',     # HTML event handlers
            r'javascript:',    # JS protocols
            r'<\s*iframe\b',   # IFrames
            r'<\s*link\b',     # Link tags
            r'<\s*meta\b',     # Meta tags
            r'/\*\*/.*?/\*\*/' # Obfuscated patterns
        ]
        
        # Check for high-risk patterns first
        dangerous_count = 0
        for pattern in html_patterns:
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                dangerous_count += 1
        
        # If number of dangerous patterns exceeds threshold
        max_suspicious_patterns = 3
        if dangerous_count > max_suspicious_patterns:
            raise ValueError(f"API response contains {dangerous_count} dangerous patterns - potential injection attack detected")
        
        # Escape HTML special characters
        sanitized = html.escape(content)
        
        # Remove any remaining problematic patterns
        sanitized = re.sub(r'(\&\#(\d{1,3}\;)|\&\#x([0-9a-f]{1,4})\;)', '', sanitized)  # Remove HTML entities
        sanitized = re.sub(r'%[0-9a-f]{2}', '', sanitized, flags=re.IGNORECASE)        # Remove URL encoding
        sanitized = re.sub(r'\\u[0-9a-f]{4}', '', sanitized, flags=re.IGNORECASE)       # Remove unicode escapes
        
        # Log if significant changes were made
        if len(sanitized) < (len(content) * 0.9):  # More than 10% reduction
            print("WARN: Significant content sanitization was applied to API response")
        
        return sanitized


class PubMedQueryGenerator:
    """Generates PubMed query and review metadata from free-text task description"""
    
    def __init__(self, llm_client: DirectAPIClient, output_dir: Path):
        self.llm = llm_client
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.prompt = self._load_prompt('pubmed_query_gen')
    
    def _load_prompt(self, name: str) -> str:
        """Load prompt template from prompts directory safely"""
        safe_name = sanitize_filename(name)
        if safe_name != name:
            raise ValueError(f"Invalid prompt name: {name}")
            
        prompt_path = Path(__file__).parent / 'prompts' / f'{safe_name}.txt'
        try:
            # Double-check path safety
            prompt_path = validate_file_path(prompt_path, MAX_PROMPT_SIZE)
                
            if not prompt_path.resolve().relative_to(Path(__file__).parent.resolve()):
                raise ValueError(f"Attempted path traversal in prompt name: {name}")
                
            # Read with size validation
            return prompt_path.read_text(encoding='utf-8').strip()
        except IOError as e:
            raise ValueError(f"Failed to load prompt '{safe_name}': {str(e)}") from e
    
    def validate_llm_json_response(self, json_data: Dict[str, Any], required_keys: list,
                                 key_types: Dict[str, type]) -> Dict[str, Any]:
        """Validate structure and content of LLM JSON response"""
        # Check required keys
        missing_keys = [key for key in required_keys if key not in json_data]
        if missing_keys:
            raise ValueError(f"Missing required keys: {missing_keys}")
        
        # Check types
        type_mismatches = []
        for key, expected_type in key_types.items():
            if key in json_data and not isinstance(json_data[key], expected_type):
                actual_type = type(json_data[key])
                type_mismatches.append(f"{key}: {actual_type.__name__} instead of {expected_type.__name__}")
        
        if type_mismatches:
            raise TypeError(f"Type mismatches:\n" + "\n".join(type_mismatches))
            
        # Check for empty values
        empty_fields = [key for key in required_keys if json_data.get(key) in ['', None]]
        if empty_fields:
            raise ValueError(f"Empty values: {empty_fields}")
        
        return json_data

    def generate(self, task_description: str):
        """Generate and save PubMed query components"""
        try:
            # Sanitize user input
            safe_task = sanitize_api_input(task_description)
            prompt = self.prompt.format(task_description=safe_task)
            response_text = self.llm.call(prompt)
            
            # Extract JSON response
            json_match = re.search(r'{(?:[^{}]|(?R))*}', response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No valid JSON object found in LLM response")
            
            # Parse components with validation
            components = json.loads(json_match.group())
            
            # Validate strict schema
            self.validate_llm_json_response(
                components,
                required_keys=['query', 'topic', 'title', 'screening'],
                key_types={
                    'query': str,
                    'topic': str,
                    'title': str,
                    'screening': dict
                }
            )
            
            # Validate screening object
            if not isinstance(components['screening'], dict):
                raise TypeError("Screening criteria must be a JSON object")
                
            screening_reqs = {'inclusion', 'exclusion'}
            missing_screening = screening_reqs - set(components['screening'].keys())
            if missing_screening:
                raise ValueError(f"Missing screening criteria: {missing_screening}")
            
            # Save validated data
            output_path = self.output_dir / "00_review_topic.json"
            output_path.write_text(json.dumps(components, indent=2))
            
            print(f"✓ Generated review metadata:")
            print(f"  Saved to: {output_path}")
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
        print("LITERATURE REVIEW PROCESSING PIPELINE")
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
            print("\n[STEP 2/6] Screening titles and abstracts...")
            screening_results = self._screen_articles(articles, screening_file)
            
            include_count = sum(1 for r in screening_results if r['decision'] == 'INCLUDE')
            exclude_count = sum(1 for r in screening_results if r['decision'] == 'EXCLUDE')
            uncertain_count = sum(1 for r in screening_results if r['decision'] == 'UNCERTAIN')
            
            print(f"✓ Screening complete:")
            print(f"  - INCLUDE: {include_count}")
            print(f"  - EXCLUDE: {exclude_count}")
            print(f"  - UNCERTAIN: {uncertain_count}")
            
            # Step 3: Extract data from included articles
            extraction_file = self.output_dir / "03_extracted_data.json"
            included_pmids = {r['pmid'] for r in screening_results if r['decision'] == 'INCLUDE'}
            included_articles = [a for a in articles if a['pmid'] in included_pmids]
            
            if not included_articles:
                print("ERROR: No articles included after screening. Aborting.", "ERROR")
                return
                
            print("\n[STEP 3/6] Extracting data from included articles...")
            extracted_data = self._extract_article_data(included_articles, extraction_file)
            print(f"✓ Extracted data from {len(extracted_data)} articles")
            
            # Step 4: Assess study quality
            quality_file = self.output_dir / "04_quality_assessment.json"
            print("\n[STEP 4/6] Assessing study quality (QUADAS-2)...")
            quality_assessments = self._assess_quality(included_articles, quality_file)
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
        
        # Sanitize and validate file path with size limit
        validated_path = validate_file_path(file_path, MAX_INPUT_SIZE)
        
        # Parse file with auto-detection
        try:
            articles = PubMedParser.parse(str(validated_path))
            print(f"✓ Parsed {len(articles)} articles from {Path(file_path).name}")
            
            if not articles:
                raise ValueError("No articles found in the file")
            
            
            return articles
            
        except Exception as e:
            print(f"Error parsing file: {str(e)}", "ERROR")
            raise
    
    def _screen_articles(self, articles: List[Dict], screening_file: Path) -> List[Dict]:
        """Screen articles for inclusion with caching support"""
        # Try loading existing screening results
        cached_results = []
        if screening_file.exists():
            try:
                with open(screening_file, 'r', encoding='utf-8') as f:
                    cached_results = json.load(f)
                print(f"  Loaded {len(cached_results)} cached screening decisions")
            except Exception as e:
                print(f"  Cache load error: {str(e)} - creating new cache")
        
        # Build cached pmids set and screen only new articles
        cached_pmids = {r['pmid'] for r in cached_results}
        new_articles = [a for a in articles if a['pmid'] not in cached_pmids]
        
        if not new_articles:
            print("✓ All articles already have screening decisions")
            return cached_results
        
        # Load screening criteria from generated metadata
        topic_file = self.output_dir / "00_review_topic.json"
        if not topic_file.exists():
            raise ValueError(f"Review topic file {topic_file.name} not found - run with --task first")
            
        try:
            with open(topic_file, 'r', encoding='utf-8') as f:
                topic_data = json.load(f)
        except Exception as e:
            raise ValueError(f"Error loading review topic: {str(e)}") from e
        
        # Validate required screening criteria
        screening = topic_data.get('screening', {})
        inclusion = screening.get('inclusion', [])
        exclusion = screening.get('exclusion', [])
        
        if not inclusion:
            raise ValueError("Screening criteria missing inclusion list in topic file")
        if not exclusion:
            raise ValueError("Screening criteria missing exclusion list in topic file")
            
        # Format criteria
        inclusion_str = "\n- ".join([""] + inclusion)
        exclusion_str = "\n- ".join([""] + exclusion)
        topic = topic_data['topic']
        
        screening_prompt = self._load_prompt('screening')
        
        results = []
        total_new = len(new_articles)
        
        for i, article in enumerate(new_articles):
            # Sanitize article fields for API
            safe_title = sanitize_api_input(article.get('title', ''))
            safe_abstract = sanitize_api_input(article.get('abstract', ''))
            
            prompt = screening_prompt.format(
                topic=sanitize_api_input(topic),
                inclusion=sanitize_api_input(inclusion_str),
                exclusion=sanitize_api_input(exclusion_str),
                pmid=article['pmid'],  # PMID is numeric so safe
                title=safe_title,
                abstract=safe_abstract
            )
            
            try:
                response_text = self.llm.call(prompt)
                
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                # Extract and validate JSON
                json_match = re.search(r'{(?:[^{}]|(?R))*}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    # Validate screening response structure
                    self.validate_llm_json_response(
                        result,
                        required_keys=['pmid', 'decision', 'confidence', 'reasoning'],
                        key_types={
                            'pmid': str,
                            'decision': str,
                            'confidence': (float, int),
                            'reasoning': str,
                            'key_terms': list
                        }
                    )
                    
                    # Validate decision value
                    if result['decision'] not in ['INCLUDE', 'EXCLUDE', 'UNCERTAIN']:
                        raise ValueError(f"Invalid decision value: {result['decision']}")
                    
                    # Validate confidence range
                    if not (0 <= result['confidence'] <= 1):
                        raise ValueError(f"Confidence {result['confidence']} out of [0-1] range")
                
                    results.append(result)
                else:
                    raise ValueError("No valid JSON found in response")
                    
            except (json.JSONDecodeError, ValueError, TypeError, Exception) as e:
                print(f"Error screening {article['pmid']}: {str(e)}", "WARN")
                results.append({
                    'pmid': article['pmid'],
                    'decision': 'UNCERTAIN',
                    'confidence': 0.0,
                    'reasoning': 'Processing error',
                    'key_terms': []
                })
            
            # Save every 10 items or at end of processing
            if (i + 1) % 10 == 0 or i == total_new - 1:
                all_results = cached_results + results
                with open(screening_file, 'w', encoding='utf-8') as f:
                    json.dump(all_results, f, indent=2)
                print(f"  Saved {len(all_results)} screening results...")
                time.sleep(1)  # Rate limiting
        
        return cached_results + results
    
    def _extract_article_data(self, articles: List[Dict], extraction_file: Path) -> List[Dict]:
        """Extract article data with caching support"""
        # Try loading existing extracted data
        cached_data = []
        if extraction_file.exists():
            try:
                with open(extraction_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                print(f"  Loaded {len(cached_data)} cached extracted records")
            except Exception as e:
                print(f"  Cache load error: {str(e)} - creating new cache")

        # Build cached pmids set and extract only new articles
        cached_pmids = {d['pmid'] for d in cached_data if 'pmid' in d}
        new_articles = [a for a in articles if a['pmid'] not in cached_pmids]

        if not new_articles:
            print("✓ All articles already have extracted data")
            return cached_data
        
        extraction_prompt = self._load_prompt('extraction')
        results = []
        total_new = len(new_articles)

        topic_file = self.output_dir / "00_review_topic.json"
        extract_json = "{}"  # Default empty template
        if topic_file.exists():
            try:
                with open(topic_file, 'r', encoding='utf-8') as f:
                    topic_data = json.load(f)
                extract = topic_data.get('extract', {})
                extract_json = json.dumps(extract, indent=2)
            except Exception as e:
                print(f"Error loading extract fields: {str(e)} - using empty template")

        for i, article in enumerate(new_articles):
            # Format prompt with article data and extraction template
            # Sanitize article fields
            safe_title = sanitize_api_input(article.get('title', ''))
            safe_abstract = sanitize_api_input(article.get('abstract', ''))
            
            prompt = extraction_prompt.format(
                extract=sanitize_api_input(extract_json),
                pmid=article['pmid'],
                title=safe_title,
                abstract=safe_abstract
            )
            
            try:
                response_text = self.llm.call(prompt)
                
                # Extract JSON
                # Extract and validate JSON
                json_match = re.search(r'{(?:[^{}]|(?R))*}', response_text, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    
                    # Validate extraction structure
                    self.validate_llm_json_response(
                        data,
                        required_keys=['pmid'],
                        key_types={
                            'pmid': str,
                            'title': str,
                            'year': (str, int),
                            'study_design': str,
                            'clinical_domain': str,
                            'imaging_modality': (str, list),
                            'cdss_type': str,
                            'sample_size': (dict, int),
                            'key_metrics': dict,
                            'main_findings': str
                        }
                    )
                    
                    results.append(data)
                else:
                    raise ValueError("No valid JSON found in response")
                    
            except (json.JSONDecodeError, ValueError, TypeError, Exception) as e:
                print(f"Error extracting {article['pmid']}: {str(e)}", "WARN")
                results.append({
                    'pmid': article['pmid'],
                    'title': article['title'],
                    'extraction_error': True
                })
                        
            # Save every 10 items or at end of processing
            if (i + 1) % 10 == 0 or i == total_new - 1:
                all_results = cached_data + results
                with open(extraction_file, 'w', encoding='utf-8') as f:
                    json.dump(all_results, f, indent=2)
                print(f"  Saved {len(all_results)} extracted records...")
                time.sleep(1)  # Rate limiting

        return cached_data + results
    
    def _assess_quality(self, articles: List[Dict], quality_file: Path) -> List[Dict]:
        """Assess study quality with caching support"""
        # Try loading existing quality assessments
        cached_results = []
        if quality_file.exists():
            try:
                with open(quality_file, 'r', encoding='utf-8') as f:
                    cached_results = json.load(f)
                print(f"  Loaded {len(cached_results)} cached quality assessments")
            except Exception as e:
                print(f"  Cache load error: {str(e)} - creating new cache")
        
        # Build cached pmids set and assess only new articles
        cached_pmids = {r['pmid'] for r in cached_results}
        new_articles = [a for a in articles if a['pmid'] not in cached_pmids]
        
        if not new_articles:
            print("✓ All articles already have quality assessments")
            return cached_results
        
        quadas2_prompt = self._load_prompt('quality_assessment')
        
        results = []
        total_new = len(new_articles)
        
        for i, article in enumerate(new_articles):
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
                
                results.append(result)
                    
            except Exception as e:
                print(f"Error assessing {article['pmid']}: {str(e)}", "WARN")
                results.append({
                    'pmid': article['pmid'],
                    'assessment_error': True
                })
            
            # Save every 10 items or at end of processing
            if (i + 1) % 10 == 0 or i == total_new - 1:
                all_results = cached_results + results
                with open(quality_file, 'w', encoding='utf-8') as f:
                    json.dump(all_results, f, indent=2)
                print(f"  Saved {len(all_results)} quality assessments...")
                time.sleep(1)  # Rate limiting
        
        return cached_results + results
    
    def _perform_synthesis(self, extracted_data: List[Dict]) -> str:
        """Perform thematic synthesis and identify patterns"""
        
        # Load review topic from metadata
        topic_file = self.output_dir / "00_review_topic.json"
        if not topic_file.exists():
            raise ValueError(f"Review topic file {topic_file.name} not found - run with --task first")
        
        with open(topic_file, 'r', encoding='utf-8') as f:
            topic_data = json.load(f)
        
        topic = topic_data['topic']
        
        # Prepare summary of extracted data
        summary_dict = {
            'total_studies': len(extracted_data),
            'studies_sample': extracted_data[:3],  # First 3 for context
            'total_count': len(extracted_data)
        }
        
        synthesis_template = self._load_prompt('synthesis')
        synthesis_prompt = synthesis_template.format(
            topic=topic,
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
    
    parser.add_argument('input_file', nargs='?', help='PubMed export file (CSV/XML/MEDLINE/TXT/JSON) (required when not using --task)')
    parser.add_argument('--task', help='Free-text research topic description (generates PubMed query and metadata - requires no input file)')
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
    
    # Validate arguments
    if args.task and args.input_file:
        print("Error: Cannot specify both --task and input file")
        sys.exit(1)
    if not args.task and not args.input_file:
        print("Error: Must specify either an input file or --task")
        sys.exit(1)
    
    # Validate input file exists if required
    if not args.task and not Path(args.input_file).exists():
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
