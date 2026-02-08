#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Systematic Literature Review Processing Pipeline
# Automate PubMed export analysis using LLMs for screening, extraction, and synthesis
#
# Copyright (C) 2026  Costin Stroie <costinstroie@eridu.eu.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Author: Costin Stroie <costinstroie@eridu.eu.org>
# GitHub: https://github.com/cstroie/SystematicReviewAssistant

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
    python systematic_review_assistant.py --provider anthropic --model claude-2

    # Using OpenRouter
    export OPENROUTER_API_KEY="sk-or-..."
    python systematic_review_assistant.py --provider openrouter --model meta-llama/llama-2-70b-chat-hf

    # Using Together.ai
    export TOGETHER_API_KEY="..."
    python systematic_review_assistant.py --provider together --model meta-llama/Llama-2-70b-chat-hf

    # Using Groq
    export GROQ_API_KEY="..."
    python systematic_review_assistant.py --provider groq --model mixtral-8x7b-32768

    # Using local Ollama
    python systematic_review_assistant.py --provider local --model llama2
"""

import json
import yaml
import csv
import time
import sys
import os
import argparse
import urllib.request
import urllib.error
import re
import random
from typing import List, Dict, Any, Optional
from pathlib import Path
import html
from datetime import datetime
import urllib.parse

try:
    import pandas as pd
except ImportError:
    pd = None

MAX_PROMPT_SIZE =  1 * 1024 * 1024  #  1MB
MAX_INPUT_SIZE  = 50 * 1024 * 1024  # 50MB

def validate_file_path(path: str, max_size: Optional[int] = None) -> Path:
    """
    Validate and normalize file path to prevent directory traversal

    Args:
        path: Input file path to validate
        max_size: Optional maximum file size in bytes

    Returns:
        Normalized Path object

    Raises:
        ValueError: If path doesn't exist, is directory, or exceeds max_size
    """
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
    """
    Sanitize filename to prevent path traversal and injection attacks

    Args:
        name: Input filename to sanitize

    Returns:
        Safe filename with dangerous characters replaced and length limited

    Removes all path separators and special characters then truncates to
    200 characters to prevent excessively long filenames.
    """
    # Remove any path separators and other dangerous characters
    cleaned = re.sub(r'[\\/:\*\?"<>\|\s]', '_', name)
    return cleaned[:200]  # Prevent excessively long filenames

def sanitize_error_message(msg: str) -> str:
    """Sanitize error messages to prevent leaking sensitive information"""
    # Remove potential paths and API keys
    msg = re.sub(r'/[\w/.-]+', '[PATH]', msg)  # Paths
    msg = re.sub(r'\b[A-Za-z0-9]{32,64}\b', '[API_KEY]', msg)  # Long hex strings
    msg = re.sub(r'\b\d{4,}-\w+\b', '[MODEL_ID]', msg)  # Model IDs
    return msg

def validate_llm_json_response(json_data: Dict[str, Any], required_keys: list,
                             key_types: Dict[str, type]) -> Dict[str, Any]:
    """Validate structure and content of LLM JSON response"""
    # Check required keys
    missing_keys = [key for key in required_keys if key not in json_data]
    if missing_keys:
        raise ValueError(f"Missing required keys: {missing_keys}")

    # Check types
    type_mismatches = []
    for key, expected_type in key_types.items():
        if key in json_data:
            # Handle tuple of allowed types
            if isinstance(expected_type, tuple):
                if not isinstance(json_data[key], expected_type):
                    type_names = [t.__name__ for t in expected_type]
                    actual_type = type(json_data[key])
                    type_mismatches.append(f"{key}: {actual_type.__name__} instead of {' or '.join(type_names)}")
            else:
                if not isinstance(json_data[key], expected_type):
                    actual_type = type(json_data[key])
                    type_mismatches.append(f"{key}: {actual_type.__name__} instead of {expected_type.__name__}")

    if type_mismatches:
        raise TypeError(f"Type mismatches:\n" + "\n".join(type_mismatches))

    # Check for empty values
    empty_fields = [key for key in required_keys if json_data.get(key) in ['', None]]
    if empty_fields:
        raise ValueError(f"Empty values: {empty_fields}")

    return json_data

def sanitize_api_input(text: str) -> str:
    """Basic sanitization for text used in API calls"""
    # Remove control characters and limit length
    sanitized = re.sub(r'[\x00-\x1F\x7F]', '', text)
    return sanitized[:10000]  # Limit to reasonable length


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
            'HTTP-Referer': 'https://github.com/cstroie/lit-review'
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

# Custom exceptions
class APIKeyError(Exception):
    """
    Custom exception for missing API keys

    Attributes:
        env_var: Name of environment variable that should contain API key
    """
    def __init__(self, env_var):
        super().__init__()
        self.env_var = env_var


class PubMedDownloader:
    """Download PubMed articles in MEDLINE format using NCBI E-utilities"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    def download_medline(self, pmids: List[str], output_file: str, batch_size: int = 200) -> None:
        """
        Download PubMed articles in MEDLINE format
        
        Args:
            pmids: List of PubMed IDs to download
            output_file: Path to save MEDLINE file
            batch_size: Number of PMIDs per request (max 200)
        """
        # Split into batches
        batches = [pmids[i:i + batch_size] for i in range(0, len(pmids), batch_size)]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, batch in enumerate(batches):
                print(f"Downloading batch {i+1}/{len(batches)} ({len(batch)} PMIDs)...")
                self._download_batch(batch, f)
                time.sleep(0.5)  # Rate limiting
        
        print(f"✓ Downloaded {len(pmids)} articles to {output_file}")
    
    def _download_batch(self, pmids: List[str], file_handle) -> None:
        """Download a single batch of PMIDs"""
        pmid_str = ",".join(pmids)
        
        params = {
            'db': 'pubmed',
            'id': pmid_str,
            'rettype': 'medline',
            'retmode': 'text'
        }
        
        if self.api_key:
            params['api_key'] = self.api_key
        
        # Build URL
        query = urllib.parse.urlencode(params)
        url = f"{self.base_url}/efetch.fcgi?{query}"
        
        try:
            with urllib.request.urlopen(url) as response:
                content = response.read().decode('utf-8')
                file_handle.write(content)
        except urllib.error.HTTPError as e:
            print(f"Error downloading batch: {e}")
            raise
    
    def search_pubmed(self, query: str, retmax: int = 10000) -> List[str]:
        """Search PubMed and return list of PMIDs"""
        params = {
            'db': 'pubmed',
            'term': query,
            'retmax': retmax,
            'retmode': 'json'
        }
        
        if self.api_key:
            params['api_key'] = self.api_key
        
        query = urllib.parse.urlencode(params)
        url = f"{self.base_url}/esearch.fcgi?{query}"
        
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data['esearchresult']['idlist']


class DirectAPIClient:
    """
    Direct HTTP client for OpenAI-compatible APIs without external dependencies

    Features:
    - Supports multiple providers (Anthropic, OpenRouter, Together, Groq, local)
    - Handles rate limiting and retries
    - Securely processes API responses
    - Automatic configuration from API_CONFIGS

    Usage:
        client = DirectAPIClient(provider='anthropic')
        response = client.call("Hello world")
    """

    def __init__(self, provider: str = 'openrouter', model: Optional[str] = None,
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
        self.request_times: List[float] = []

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
        """
        Enforce token bucket rate limiting

        Maintains sliding window of request times and sleeps when
        max_requests per rate_period is exceeded.
        """
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
        Call LLM API with direct HTTP request and retry logic

        Args:
            prompt: Input text to send to LLM
            max_retries: Number of retry attempts on failure

        Returns:
            Validated and sanitized model response text

        Raises:
            ValueError: On persistent API failures or security issues
            TypeError: If invalid response format received

        Implements exponential backoff with jitter and handles:
        - Rate limiting (429 errors)
        - Server errors (5xx)
        - Connection issues
        """

        # Prepare request with types
        headers_dict = self.headers_fn(self.api_key, self.model)
        headers = {str(k): str(v) for k,v in headers_dict.items()}
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
                raise ValueError(f"API error {status_code}: Please check your request and try again")

            except urllib.error.URLError as e:
                if attempt < max_retries - 1:
                    backoff = 2 ** attempt
                    wait_time = min(backoff + random.uniform(0, 1), 10)
                    print(f"  Connection error: {sanitize_error_message(str(e.reason))}. Waiting {wait_time:.1f}s before retry #{attempt+1}...")
                    time.sleep(wait_time)
                    continue
                raise ValueError("Connection error: Could not reach API endpoint")

            except Exception as e:
                sanitized_msg = sanitize_error_message(str(e))
                if attempt < max_retries - 1:
                    wait_time = 1 + random.uniform(0, 1)
                    print(f"  Error: {sanitized_msg}. Waiting {wait_time:.1f}s before retry #{attempt+1}...")
                    time.sleep(wait_time)
                    continue
                raise ValueError(f"API call failed: {sanitized_msg}")

        raise ValueError(f"Failed after {max_retries} attempts")

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


class PubMedParser:
    """Parse multiple PubMed export formats"""
    
    @staticmethod
    def detect_format(file_path: str) -> str:
        """Detect the format of the input file"""
        path = Path(file_path)
        
        # Check by file extension first
        if path.suffix.lower() == '.csv':
            return 'csv'
        elif path.suffix.lower() == '.xml':
            return 'xml'
        elif path.suffix.lower() == '.json':
            return 'json'
        elif path.suffix.lower() == '.txt':
            # Could be MEDLINE or other text format
            # Check file contents to distinguish
            return PubMedParser._detect_medline_format(file_path)
        else:
            # Try to detect by content
            return PubMedParser._detect_by_content(file_path)
    
    @staticmethod
    def _detect_medline_format(file_path: str) -> str:
        """Detect if text file is MEDLINE format"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_lines = f.read(1000)
                
                # MEDLINE format starts with PMID-, TI, AB, etc.
                if re.search(r'^PMID-\s*\d+', first_lines, re.MULTILINE):
                    return 'medline'
                # CSV has comma-separated headers
                elif ',' in first_lines.split('\n')[0]:
                    return 'csv'
                else:
                    return 'medline'  # Default to MEDLINE for unknown text
        except Exception as e:
            print(f"Warning: Error detecting format - {str(e)} - defaulting to MEDLINE")
            return 'medline'  # Default guess
    
    @staticmethod
    def _detect_by_content(file_path: str) -> str:
        """Detect format by examining file content"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(500)
                
                if content.strip().startswith('{'):
                    return 'json'
                elif content.strip().startswith('<'):
                    return 'xml'
                elif 'PMID-' in content or 'TI  -' in content:
                    return 'medline'
                elif ',' in content:
                    return 'csv'
                else:
                    return 'medline'  # Default
        except Exception as e:
            print(f"Warning: Content detection error - {str(e)} - defaulting to MEDLINE")
            return 'medline'
    
    @staticmethod
    def parse(file_path: str, format_hint: Optional[str] = None) -> List[Dict]:
        """
        Parse PubMed export file in any supported format with security validation
        
        Args:
            file_path: Path to the export file
            format_hint: Optional format hint ('csv', 'medline', 'xml', 'json')
        
        Returns:
            List of article dictionaries with standard fields
        """
        # Validate file path before processing
        validated_path = validate_file_path(file_path)
        
        # Detect format if not provided
        file_format = format_hint or PubMedParser.detect_format(str(validated_path))
        
        if file_format == 'csv':
            return PubMedParser.parse_csv(file_path)
        elif file_format == 'medline':
            return PubMedParser.parse_medline(file_path)
        elif file_format == 'xml':
            return PubMedParser.parse_xml(file_path)
        elif file_format == 'json':
            return PubMedParser.parse_json(file_path)
        else:
            raise ValueError(f"Unsupported format: {file_format}")
    
    @staticmethod
    def parse_csv(file_path: str) -> List[Dict]:
        """Parse PubMed CSV export"""
        validated_path = validate_file_path(file_path)
        articles = []
        
        with open(validated_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                article = {
                    'pmid': str(row.get('PMID', '')).strip(),
                    'title': row.get('Title', '').strip(),
                    'abstract': row.get('Abstract', '').strip(),
                    'authors': row.get('Authors', '').strip(),
                    'journal': row.get('Journal', '').strip(),
                    'pub_date': row.get('Publication Date', '').strip(),
                    'doi': row.get('DOI', '').strip(),
                }
                if article['pmid']:
                    articles.append(article)
        
        return articles
    
    @staticmethod
    def parse_medline(file_path: str) -> List[Dict]:
        """
        Parse MEDLINE format (.txt export from PubMed)
        
        Format example:
        PMID- 12345678
        TI  - Title of the article
        AB  - Abstract text here...
              Continues on next line...
        AU  - Author Name
        FAU - Author, Full Name
        AD  - Author Address
        SO  - Journal Citation
        """
        validated_path = validate_file_path(file_path)
        articles = []
        current_article: Dict[str, str] = {}
        current_field: Optional[str] = None
        current_value: List[str] = []
        
        with open(validated_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                # Check if this is a new field line (starts with tag and dash)
                field_match = re.match(r'^([A-Z]+)\s*-\s*(.*)', line.rstrip())
                
                if field_match:
                    # Save previous field if exists
                    if current_field:
                        value = ' '.join(current_value).strip()
                        current_article[current_field] = value
                    
                    # Start new field
                    current_field = field_match.group(1)
                    current_value = [field_match.group(2)]
                    
                    # Check if this is PMID (marks start of new article)
                    if current_field == 'PMID':
                        # Save previous article if exists
                        if current_article:
                            articles.append(PubMedParser._normalize_medline_article(current_article))
                        current_article = {}
                
                elif current_field and line.startswith(' '):
                    # Continuation of previous field (indented line)
                    current_value.append(line.strip())
            
            # Save last field and article
            if current_field:
                value = ' '.join(current_value).strip()
                current_article[current_field] = value
            if current_article:
                articles.append(PubMedParser._normalize_medline_article(current_article))
        
        return articles
    
    @staticmethod
    def _normalize_medline_article(medline_dict: Dict) -> Dict[str, str]:
        """Convert MEDLINE field names to standard format"""
        # Map MEDLINE field codes to standard names
        field_map = {
            'PMID': 'pmid',
            'TI': 'title',
            'AB': 'abstract',
            'AU': 'authors',
            'FAU': 'authors_full',
            'AD': 'affiliation',
            'SO': 'source',
            'TA': 'journal',
            'JT': 'journal_full',
            'VI': 'volume',
            'IP': 'issue',
            'DP': 'pub_date',
            'PG': 'pages',
            'AID': 'article_id',
            'DOI': 'doi',
            'PT': 'publication_type',
            'DEP': 'electronic_pub_date',
            'PL': 'publisher_location',
            'LA': 'language',
            'OT': 'keywords',
        }
        
        normalized = {}
        for medline_key, value in medline_dict.items():
            standard_key = field_map.get(medline_key, medline_key.lower())
            normalized[standard_key] = value
        
        # Ensure required fields exist
        if 'pmid' not in normalized:
            normalized['pmid'] = ''
        if 'title' not in normalized:
            normalized['title'] = ''
        if 'abstract' not in normalized:
            normalized['abstract'] = ''
        
        return normalized
    
    @staticmethod
    def parse_xml(file_path: str) -> List[Dict]:
        """
        Parse PubMed XML format (Entrez API format)
        
        Requires xml module (from stdlib in Python 3.2+)
        """
        validated_path = validate_file_path(file_path)
        try:
            import xml.etree.ElementTree as ET
        except ImportError:
            raise ImportError("XML parsing requires Python 3.2+")
        
        articles = []
        tree = ET.parse(validated_path)
        root = tree.getroot()
        
        # Handle different XML structures
        # Try PubmedArticleSet format first
        for article_elem in root.findall('.//PubmedArticle'):
            for elem in root.findall('.//PubmedArticle'):
                if elem is not None:
                    article = PubMedParser._parse_xml_article(elem)
                    if article.get('pmid'):
                        articles.append(article)
        
        return articles
    
    @staticmethod
    def _parse_xml_article(article_elem) -> Dict[str, str]:
        """Extract article data from XML element"""
        # Try different path structures
        pmid_elem = article_elem.find('.//PMID')
        pmid = pmid_elem.text if pmid_elem is not None else ''
        
        title_elem = article_elem.find('.//ArticleTitle')
        title = title_elem.text if title_elem is not None else ''
        
        abstract_elem = article_elem.find('.//Abstract/AbstractText')
        abstract = abstract_elem.text if abstract_elem is not None else ''
        
        # Join multiple abstract sections if they exist
        if not abstract:
            abstract_texts = []
            for abstract_section in article_elem.findall('.//AbstractText'):
                if abstract_section.text:
                    abstract_texts.append(abstract_section.text)
            abstract = ' '.join(abstract_texts)
        
        # Get authors
        authors = []
        for author in article_elem.findall('.//Author'):
            last_name = author.find('LastName')
            fore_name = author.find('ForeName')
            if last_name is not None and last_name.text:
                name = last_name.text
                if fore_name is not None and fore_name.text:
                    name = f"{fore_name.text} {last_name.text}"
                authors.append(name)
        authors_str = ', '.join(authors)
        
        # Get journal
        journal_elem = article_elem.find('.//Journal/Title')
        journal = journal_elem.text if journal_elem is not None else ''
        
        # Get publication date
        pub_date_elem = article_elem.find('.//PubDate/Year')
        pub_date = pub_date_elem.text if pub_date_elem is not None else ''
        
        # Get DOI
        doi = ''
        for aid in article_elem.findall('.//ArticleId'):
            if aid.get('IdType') == 'doi':
                doi = aid.text
                break
        
        return {
            'pmid': str(pmid).strip(),
            'title': str(title).strip(),
            'abstract': str(abstract).strip(),
            'authors': authors_str,
            'journal': str(journal).strip(),
            'pub_date': str(pub_date).strip(),
            'doi': str(doi).strip(),
        }
    
    @staticmethod
    def parse_json(file_path: str) -> List[Dict]:
        """
        Parse PubMed JSON format (from Entrez API)
        
        Expected structure from NCBI API
        """
        validated_path = validate_file_path(file_path)
        with open(validated_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        articles = []
        
        # Handle different JSON structures
        # Check for common NCBI API response structure
        if 'result' in data:
            results = data['result']
        elif 'articles' in data:
            results = data['articles']
        elif isinstance(data, list):
            results = data
        else:
            results = [data]
        
        for item in results:
            if isinstance(item, dict):
                article = PubMedParser._normalize_json_article(item)
                if article.get('pmid'):
                    articles.append(article)
        
        return articles
    
    @staticmethod
    def _normalize_json_article(json_article: Dict) -> Dict[str, str]:
        """Normalize JSON article to standard format"""
        
        # Try various possible field names
        pmid = (
            json_article.get('pmid') or
            json_article.get('PMID') or
            json_article.get('id') or
            json_article.get('uid', '')
        )
        
        title = (
            json_article.get('title') or
            json_article.get('Title') or
            json_article.get('ArticleTitle', '')
        )
        
        abstract = (
            json_article.get('abstract') or
            json_article.get('Abstract') or
            json_article.get('AbstractText', '')
        )
        
        # Handle abstract as list
        if isinstance(abstract, list):
            abstract = ' '.join(str(a) for a in abstract)
        
        # Get authors
        authors = json_article.get('authors', [])
        if isinstance(authors, list):
            authors_str = ', '.join(str(a) for a in authors)
        else:
            authors_str = str(authors)
        
        journal = (
            json_article.get('journal') or
            json_article.get('Journal') or
            json_article.get('source', '')
        )
        
        pub_date = (
            json_article.get('pub_date') or
            json_article.get('PubDate') or
            json_article.get('published_date', '')
        )
        
        # Handle pub_date as dict
        if isinstance(pub_date, dict):
            pub_date = pub_date.get('year', '')
        
        doi = json_article.get('doi') or json_article.get('DOI', '')
        
        return {
            'pmid': str(pmid).strip(),
            'title': str(title).strip(),
            'abstract': str(abstract).strip(),
            'authors': authors_str,
            'journal': str(journal).strip(),
            'pub_date': str(pub_date).strip(),
            'doi': str(doi).strip(),
        }


class CDSSLitReviewProcessor:
    """
    Main pipeline processor for systematic literature review workflow

    Handles complete processing pipeline:
    1. PubMed export parsing
    2. Article screening
    3. Data extraction
    4. Quality assessment
    5. Thematic synthesis
    6. Summary generation

    Features:
    - File-based caching between steps
    - Validation of LLM outputs
    - Error handling and recovery

    Attributes:
        llm: Configured DirectAPIClient instance
        workdir: Working directory for output files
        log_verbose: Enable debug logging
        start_time: Pipeline start timestamp
    """


class PlanGenerator:
    """
    Generates plan from free-text description

    Uses LLM to generate:
    - PubMed search query string
    - Systematic review metadata (title, topic, inclusion/exclusion criteria)

    Attributes:
        llm_client: Configured DirectAPIClient instance
        workdir: Path for generated files
        prompt: Loaded prompt template text
    """

    def __init__(self, llm_client: DirectAPIClient, workdir: Path):
        self.llm = llm_client
        self.workdir = workdir
        self.workdir.mkdir(exist_ok=True)
        self.prompt = self._load_prompt('plan_generator')

    def _load_prompt(self, name: str) -> str:
        """Load prompt template from prompts directory safely"""
        safe_name = sanitize_filename(name)
        if safe_name != name:
            raise ValueError(f"Invalid prompt name: {name}")

        prompt_path = Path(__file__).parent / 'prompts' / f'{safe_name}.txt'
        try:
            # Double-check path safety
            prompt_path = validate_file_path(str(prompt_path), MAX_PROMPT_SIZE)

            if not prompt_path.resolve().relative_to(Path(__file__).parent.resolve()):
                raise ValueError(f"Attempted path traversal in prompt name: {name}")

            # Read with size validation
            return prompt_path.read_text(encoding='utf-8').strip()
        except IOError as e:
            raise ValueError(f"Failed to load prompt '{safe_name}': {str(e)}") from e


    def generate(self, plan: str):
        """Generate and save plan components"""
        try:
            # Sanitize user input
            safe_plan = sanitize_api_input(plan)
            prompt = self.prompt.format(plan=safe_plan)
            response_text = self.llm.call(prompt)

            # Attempt multiple JSON extraction patterns
            json_match = re.search(r'```json\s*({.*?})\s*```', response_text, re.DOTALL)
            if not json_match:
                # Fall back to original pattern
                json_match = re.search(r'\{[\s\S]*\}', response_text)
            
            if not json_match:
                raise ValueError("No valid JSON object found in LLM response")
            
            try:
                # Get matched JSON string and unescape HTML entities
                json_str = json_match.group(1) if json_match.lastindex else json_match.group()
                clean_json = html.unescape(json_str)
                
                # Parse components with validation
                components = json.loads(clean_json)
            except json.JSONDecodeError as e:
                # Add debug information to help diagnose JSON issues
                clean_json = html.unescape(json_match.group())
                snippet_start = max(0, e.pos - 50)
                snippet_end = min(len(clean_json), e.pos + 50)
                json_snippet = clean_json[snippet_start:snippet_end]
                print(f"JSON parsing error: {e.msg}\nNear: {json_snippet}\nFull response start:\n{html.unescape(response_text[:500])}")
                raise

            # Validate strict schema
            validate_llm_json_response(
                components,
                required_keys=['query', 'topic', 'title', 'screening', 'analysis'],
                key_types={
                    'query': str,
                    'topic': str,
                    'title': str,
                    'screening': dict,
                    'analysis': list
                }
            )

            # Validate screening object
            if not isinstance(components['screening'], dict):
                raise TypeError("Screening criteria must be a JSON object")

            screening_reqs = {'inclusion', 'exclusion'}
            missing_screening = screening_reqs - set(components['screening'].keys())
            if missing_screening:
                raise ValueError(f"Missing screening criteria: {missing_screening}")

            # Save validated data in both JSON and YAML formats
            output_path_json = self.workdir / "00_plan.json"
            output_path_yaml = self.workdir / "00_plan.yaml"
            
            # Save JSON
            output_path_json.write_text(json.dumps(components, indent=2))
            
            # Save YAML
            yaml_output = yaml.dump(components, sort_keys=False, indent=2)
            output_path_yaml.write_text(yaml_output)

            print(f"✓ Generated plan:")
            print(f"  Saved to: {output_path_json} (JSON)")
            print(f"  Saved to: {output_path_yaml} (YAML)")
            print(f"\nPubMed query:\n{components['query']}")
        except Exception as e:
            sanitized_err = sanitize_error_message(str(e))
            print(f"❌ Error generating plan: {sanitized_err}")
            raise ValueError(f"Plan generation failed: {sanitized_err}") from None


class CDSSLitReviewProcessor:
    """Main pipeline processor for systematic literature review"""

    def __init__(self, llm_client: DirectAPIClient, workdir: str = "output",
                 log_verbose: bool = True):
        """Initialize processor with LLM client"""
        self.llm = llm_client
        self.workdir = Path(workdir)
        self.workdir.mkdir(exist_ok=True)
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
            articles_file = self.workdir / "01_parsed_articles.json"
            if articles_file.exists():
                print("\n[STEP 1/6] Loading parsed articles from cache...")
                try:
                    articles = self._load_file(articles_file)
                    print(f"✓ Loaded {len(articles)} articles from {articles_file.name}")
                except Exception as e:
                    print(f"Cache read error: {str(e)}, re-parsing file")
                    articles = self._parse_pubmed_export(pubmed_file)
                    self._save_file(articles, articles_file)
            else:
                print("\n[STEP 1/6] Parsing PubMed export...")
                articles = self._parse_pubmed_export(pubmed_file)
                self._save_file(articles, articles_file)

            # Step 2: Screen articles (cache-aware)
            screening_file = self.workdir / "02_screening_results.json"
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
            extraction_file = self.workdir / "03_extracted_data.json"
            included_pmids = {r['pmid'] for r in screening_results if r['decision'] == 'INCLUDE'}
            included_articles = [a for a in articles if a['pmid'] in included_pmids]

            if not included_articles:
                print("ERROR: No articles included after screening. Aborting.", "ERROR")
                return

            print("\n[STEP 3/6] Extracting data from included articles...")
            extracted_data = self._extract_article_data(included_articles, extraction_file)
            print(f"✓ Extracted data from {len(extracted_data)} articles")

            # Step 4: Assess study quality
            quality_file = self.workdir / "04_quality_assessment.json"
            print("\n[STEP 4/6] Assessing study quality (QUADAS-2)...")
            quality_assessments = self._assess_quality(included_articles, quality_file)
            print(f"✓ Quality assessment complete for {len(quality_assessments)} studies")

            # Step 5: Synthesis
            synthesis_file = self.workdir / "05_thematic_synthesis.txt"
            if synthesis_file.exists():
                print("\n[STEP 5/6] Using existing thematic synthesis")
                synthesis = synthesis_file.read_text(encoding='utf-8')
                print(f"✓ Loaded {len(synthesis)} characters from existing file")
            else:
                print("\n[STEP 5/6] Performing thematic synthesis...")
                synthesis = self._perform_synthesis(extracted_data)
                synthesis_file.write_text(synthesis)
                print(f"✓ Synthesis complete - {len(synthesis)} characters written")

            # Step 6: Generate summary table
            print("\n[STEP 6/6] Generating summary table...")
            self._generate_summary_table(extracted_data)

            # Final summary
            elapsed = (datetime.now() - self.start_time).total_seconds()
            print("="*70)
            print("PIPELINE COMPLETE")
            print(f"Results saved to: {self.workdir}")
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

        Args:
            file_path: Path to PubMed export file

        Returns:
            List of article dictionaries with parsed metadata

        Raises:
            ValueError: If no articles found or invalid format detected

        Supports:
        - CSV (PubMed default format)
        - MEDLINE (.txt with PMID tags)
        - XML (PubMed XML format)
        - JSON (PubMed JSON format)
        """

        # Sanitize and validate file path with size limit
        validated_path = validate_file_path(str(file_path), MAX_INPUT_SIZE)

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
        # Load screening criteria from generated metadata
        topic_file = self.workdir / "00_plan.json"
        if not topic_file.exists():
            raise ValueError(f"Review topic file {topic_file.name} not found - run with --plan first")

        with open(topic_file, 'r', encoding='utf-8') as f:
            topic_data = json.load(f)

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

        def process_article(article):
            # Sanitize article fields
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
            except Exception as e:
                sanitized_err = sanitize_error_message(str(e))
                print(f"Screening failed for PMID {article['pmid']}: {sanitized_err}")
                return {
                    'pmid': article['pmid'],
                    'decision': 'UNCERTAIN',
                    'confidence': 0.0,
                    'reasoning': f'Processing error: {sanitized_err[:100]}',
                    'key_terms': []
                }

            try:
                # Attempt multiple JSON extraction patterns
                json_match = re.search(r'```json\s*({.*?})\s*```', response_text, re.DOTALL)
                if not json_match:
                    json_match = re.search(r'\{[\s\S]*\}', response_text)
                
                if not json_match:
                    raise ValueError("No valid JSON found in LLM response")
                
                # Get matched JSON string and unescape HTML entities
                json_str = json_match.group(1) if json_match.lastindex else json_match.group()
                clean_json = html.unescape(json_str)
                
                # Parse JSON response
                result = json.loads(clean_json)
                
                # Validate the structure
                validate_llm_json_response(
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
                    raise ValueError(f"Confidence {result['confidence']} out of range")
                    
                return result
            except Exception as e:
                sanitized_err = sanitize_error_message(str(e))
                print(f"Screening error for PMID {article['pmid']}: {sanitized_err}")
                print(f"Response snippet: {response_text[:300]}")
                return {
                    'pmid': article['pmid'],
                    'decision': 'UNCERTAIN',
                    'confidence': 0.0,
                    'reasoning': f'Processing error: {sanitized_err[:100]}',
                    'key_terms': []
                }

        return self._process_with_caching(
            cache_file=screening_file,
            all_items=articles,
            item_key='pmid',
            process_fn=process_article,
            cache_label='screening decisions'
        )

    def _extract_article_data(self, articles: List[Dict], extraction_file: Path) -> List[Dict]:
        """Extract article data with caching support"""
        # Load extract fields template
        topic_file = self.workdir / "00_plan.json"
        extract_json = "{}"  # Default empty template
        if topic_file.exists():
            try:
                with open(topic_file, 'r', encoding='utf-8') as f:
                    topic_data = json.load(f)
                extract = topic_data.get('extract', {})
                extract_json = json.dumps(extract, indent=2)
            except Exception as e:
                print(f"Error loading extract fields: {str(e)} - using empty template")

        extraction_prompt = self._load_prompt('extraction')

        def process_article(article):
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
            except Exception as e:
                sanitized_err = sanitize_error_message(str(e))
                print(f"Extraction failed for PMID {article['pmid']}: {sanitized_err}")
                print(f"Response snippet: {response_text[:300]}")
                return {
                    'pmid': article['pmid'],
                    'title': article['title'],
                    'extraction_error': sanitized_err[:200]
                }

            try:
                # Attempt multiple JSON extraction patterns
                json_match = re.search(r'```json\s*({.*?})\s*```', response_text, re.DOTALL)
                if not json_match:
                    json_match = re.search(r'\{[\s\S]*\}', response_text)
                
                if not json_match:
                    raise ValueError("No valid JSON found in LLM response")

                # Get matched JSON string and unescape HTML entities
                json_str = json_match.group(1) if json_match.lastindex else json_match.group()
                clean_json = html.unescape(json_str)
                
                # Parse JSON response
                data = json.loads(clean_json)
                
                # Validate the structure
                validate_llm_json_response(
                    data,
                    required_keys=['pmid'],
                    key_types={
                        'pmid': str,
                        'title': str,
                        'year': (str, int, type(None)),  # Allow null/None values
                        'study_design': str,
                        'clinical_domain': str,
                        'imaging_modality': (str, list),
                        'extract': dict,
                        'sample_size': (dict, int, type(None)),  # Also allow null/None
                        'key_metrics': dict,
                        'main_findings': str
                    }
                )
                
                return data
            except Exception as e:
                sanitized_err = sanitize_error_message(str(e))
                print(f"Extraction failed for PMID {article['pmid']}: {sanitized_err}")
                print(f"Response snippet: {response_text[:300]}")
                return {
                    'pmid': article['pmid'],
                    'title': article['title'],
                    'extraction_error': sanitized_err[:200]
                }

        return self._process_with_caching(
            cache_file=extraction_file,
            all_items=articles,
            item_key='pmid',
            process_fn=process_article,
            cache_label='extracted records'
        )

    def _assess_quality(self, articles: List[Dict], quality_file: Path) -> List[Dict]:
        """Assess study quality with caching support"""
        quadas2_prompt = self._load_prompt('quality_assessment')

        def process_article(article):
            prompt = quadas2_prompt.format(
                pmid=article['pmid'],
                title=article['title'],
                abstract=article['abstract']
            )

            try:
                response_text = self.llm.call(prompt)
                
                # Attempt multiple JSON extraction patterns
                json_match = re.search(r'```json\s*({.*?})\s*```', response_text, re.DOTALL)
                if not json_match:
                    json_match = re.search(r'\{[\s\S]*\}', response_text)

                if not json_match:
                    raise ValueError("No valid JSON found in LLM response")

                # Get matched JSON string and unescape HTML entities
                json_str = json_match.group(1) if json_match.lastindex else json_match.group()
                clean_json = html.unescape(json_str)

                # Parse and validate response
                result = json.loads(clean_json)
                return result
            except Exception as e:
                sanitized_err = sanitize_error_message(str(e))
                print(f"Quality assessment failed for PMID {article['pmid']}: {sanitized_err}")
                print(f"Response snippet: {response_text[:300]}")
                return {
                    'pmid': article['pmid'],
                    'assessment_error': sanitized_err[:200]
                }

        return self._process_with_caching(
            cache_file=quality_file,
            all_items=articles,
            item_key='pmid',
            process_fn=process_article,
            cache_label='quality assessments'
        )

    def _perform_synthesis(self, extracted_data: List[Dict]) -> str:
        """Perform thematic synthesis and identify patterns"""

        # Load review topic from metadata
        topic_file = self.workdir / "00_plan.json"
        if not topic_file.exists():
            raise ValueError(f"Review topic file {topic_file.name} not found - run with --plan first")

        with open(topic_file, 'r', encoding='utf-8') as f:
            topic_data = json.load(f)

        topic = topic_data['topic']

        # Prepare summary of extracted data
        summary_dict = {
            'total_studies': len(extracted_data),
            'studies_sample': extracted_data[:3],  # First 3 for context
            'total_count': len(extracted_data)
        }

        # Load review template
        topic_file = self.workdir / "00_plan.json"
        with open(topic_file, 'r', encoding='utf-8') as f:
            topic_data = json.load(f)
        
        # Validate and prepare analysis bullets
        if 'analysis' not in topic_data:
            raise ValueError("Missing required 'analysis' field in review metadata")
        
        analysis_bullets = topic_data['analysis']
        if not isinstance(analysis_bullets, list) or len(analysis_bullets) == 0:
            raise ValueError("'analysis' field must be a non-empty list of bullet points")
        
        analysis_bullets = '\n'.join(f'   - {bullet}' for bullet in analysis_bullets)
        
        # Build synthesis prompt
        synthesis_template = self._load_prompt('synthesis')
        synthesis_prompt = synthesis_template.format(
            topic=topic,
            total_studies=len(extracted_data),
            data_sample=json.dumps(summary_dict, indent=2),
            analysis=analysis_bullets
        )

        try:
            response_text = self.llm.call(synthesis_prompt)
            synthesis_text = response_text.strip()
            return synthesis_text

        except Exception as e:
            sanitized_err = sanitize_error_message(str(e))
            print(f"Error performing synthesis: {sanitized_err}", "ERROR")
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

            # Create base row with standard fields
            row = {
                'PMID': item.get('pmid', ''),
                'Year': item.get('year', ''),
                'Study Design': item.get('study_design', ''),
                'Clinical Domain': item.get('clinical_domain', ''),
                'Imaging Modality': modality_str,
                'Sample Size (N)': n_patients,
                'Sensitivity': sensitivity,
                'Specificity': specificity,
                'AUC': auc,
                'Accuracy': accuracy,
                'Main Findings': str(item.get('main_findings', ''))[:100]
            }

            # Add any fields from the 'extract' section
            if 'extract' in item and isinstance(item['extract'], dict):
                for field_name, field_value in item['extract'].items():
                    safe_field_name = sanitize_filename(str(field_name))
                    row[safe_field_name] = str(field_value)

            rows.append(row)

        if not rows:
            print("No valid data to create summary table")
            return

        # Try using pandas if available
        if pd is not None:
            try:
                df = pd.DataFrame(rows)
                output_file = self.workdir / "summary_characteristics_table.csv"
                df.to_csv(output_file, index=False)
                print(f"Summary table saved ({len(rows)} studies) - CSV format")
                return
            except Exception as e:
                sanitized_err = sanitize_error_message(str(e))
                print(f"Error creating summary table: {sanitized_err}")

        # Fall back to manual CSV creation without pandas
        try:
            output_file = self.workdir / "summary_characteristics_table.csv"
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                if rows:
                    # Collect all headers from all rows
                    all_headers = sorted({key for row in rows for key in row.keys()})
                    
                    # Write header
                    f.write(','.join(f'"{h}"' for h in all_headers) + '\n')

                    # Write rows
                    for row in rows:
                        values = [str(row.get(h, '')).replace('"', '""') for h in all_headers]
                        f.write(','.join(f'"{v}"' for v in values) + '\n')

            print(f"Summary table saved ({len(rows)} studies) - Manual CSV creation (no pandas)")
        except Exception as e:
            print(f"Error creating summary table: {str(e)}", "ERROR")

    def _process_with_caching(self, cache_file: Path, all_items: List[Dict],
                            item_key: str, process_fn: callable,
                            cache_label: str) -> List[Dict]:
        """
        Generic processing with caching support

        Implements memoization pattern with disk persistence:
        1. Load existing cached results
        2. Identify new items needing processing
        3. Process new items in batches
        4. Combine with cached results
        5. Persist combined results

        Args:
            cache_file: Path to cache file
            all_items: Complete list of items to process
            item_key: Unique identifier key in items
            process_fn: Function to process individual items
            cache_label: Human-readable label for cache type

        Returns:
            Combined list of cached and new results
        """
        # Try loading existing cache
        cached_results = []
        if cache_file.exists():
            try:
                cached_results = self._load_file(cache_file)
                print(f"  Loaded {len(cached_results)} cached {cache_label}")
            except Exception as e:
                print(f"  Cache load error: {str(e)} - creating new cache")

        # Get new items not in cache
        cached_ids = {item[item_key] for item in cached_results if item_key in item}
        new_items = [item for item in all_items if item[item_key] not in cached_ids]

        if not new_items:
            print(f"✓ All items already have {cache_label}")
            return cached_results

        results = []
        total_new = len(new_items)

        for i, item in enumerate(new_items):
            result = process_fn(item)
            results.append(result)

            # Save periodically
            if (i + 1) % 10 == 0 or i == total_new - 1:
                all_results = cached_results + results
                self._save_file(all_results, cache_file)
                print(f"  Saved {len(all_results)} {cache_label}...")
                time.sleep(1)  # Rate limiting

        return cached_results + results

    def _load_file(self, filepath: Path) -> Any:
        """Load data from JSON"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_file(self, data: Any, filepath: Path):
        """Save data as formatted JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def create_parser():
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        description='Systematic Literature Review Processor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with Anthropic Claude (needs API key):
  %(prog)s --provider anthropic --model claude-2

  # Use OpenRouter's LLaMA 2 (specify model):
  %(prog)s --provider openrouter --model meta-llama/llama-2-70b-chat-hf

  # Local Ollama model (http://localhost:11434):
  %(prog)s --provider local --model llama2

  # Download PubMed articles (requires NCBI API key):
  %(prog)s --download

Supported Providers:
  anthropic   - Anthropic Claude (default)
  openrouter  - OpenRouter (100+ models)
  together    - Together.ai
  groq        - Groq (fast inference)
  local       - Local models (Ollama/vLLM)
        """
    )

    parser.add_argument('workdir', help='Working directory containing pipeline outputs (expects articles.txt for processing)')
    parser.add_argument('--plan', help='Free-text research topic description (generates PubMed query and metadata - requires no input file)')
    parser.add_argument('--download', action='store_true', help='Download PubMed articles matching query in file')
    parser.add_argument('--provider', choices=list(API_CONFIGS.keys()),
                       default='openrouter', help='LLM provider')
    parser.add_argument('--model', help='Model name (uses provider default if not specified)')
    parser.add_argument('--api-url', help='Custom API URL (overrides provider default)')
    parser.add_argument('--api-key', help='API key (uses env var if not specified)')
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

    # Validate workdir exists if specified
    if args.workdir and not Path(args.workdir).exists():
        print(f"Error: Work directory '{args.workdir}' not found")
        sys.exit(1)

    # Handle PubMed download
    if args.download:
        if not args.workdir:
            print("Error: --workdir required for download mode")
            sys.exit(1)
        
        # Get query from plan file in working directory
        plan_file = Path(args.workdir) / "00_plan.json"
        if not plan_file.exists():
            print(f"Error: Plan file '{plan_file}' not found in working directory")
            sys.exit(1)
        
        # Read query from plan file
        with open(plan_file, 'r', encoding='utf-8') as f:
            plan_data = json.load(f)
        
        query = plan_data.get('query', '')
        if not query:
            print("Error: No PubMed query found in plan file")
            sys.exit(1)
        
        # Check if articles.txt already exists
        output_file = Path(args.workdir) / "articles.txt"
        if output_file.exists():
            print(f"✓ Articles file already exists: {output_file}")
            print("You can now process this file with:")
            print(f"  python systematic_review_assistant.py {args.workdir}")
            sys.exit(0)
        
        # Download articles to working directory
        print(f"Downloading PubMed articles for query: {query[:100]}...")
        downloader = PubMedDownloader(api_key=os.getenv('NCBI_API_KEY'))
        pmids = downloader.search_pubmed(query)
        
        if not pmids:
            print("No articles found for this query")
            sys.exit(1)
        
        downloader.download_medline(pmids, str(output_file))
        print(f"\n✓ Download complete! {len(pmids)} articles saved to {output_file}")
        print("\nYou can now process this file with:")
        print(f"  python systematic_review_assistant.py {args.workdir}")
        sys.exit(0)

    # Validate input file exists if required
    if not args.plan:
        input_path = Path(args.workdir) / "articles.txt"
        if not input_path.exists():
            print(f"Error: Input file '{input_path}' not found in work directory")
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

        # Generate plan components if plan description provided
        workdir = Path(args.workdir)
        if args.plan:
            print("\n" + "="*70)
            print("GENERATING PLAN COMPONENTS FROM PLAN DESCRIPTION")
            print("="*70)
            workdir.mkdir(exist_ok=True, parents=True)
            generator = PlanGenerator(llm_client, workdir)
            generator.generate(args.plan)
            print("\n✓ Plan generation complete\n")
            return  # Stop after generating plan components

        # Run full pipeline
        print(f"\nStarting full pipeline...\n")
        processor = CDSSLitReviewProcessor(
            llm_client=llm_client,
            workdir=args.workdir,
            log_verbose=not args.quiet
        )
        input_path = Path(args.workdir) / "articles.txt"
        processor.run_complete_pipeline(str(input_path))

    except APIKeyError as e:
        print("\n" + "="*70)
        print("API KEY NOT FOUND!")
        print("="*70)
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
