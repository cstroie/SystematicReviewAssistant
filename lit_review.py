#!/usr/bin/env python3
"""
Complete LLM-based Literature Review Processing Pipeline
For CDSS in Medical Imaging/Radiology Systematic Review

Supports any OpenAI-compatible API:
- Anthropic Claude (claude-opus-4-5, claude-sonnet-4-5)
- OpenRouter (openrouter.ai) - supports 100+ models
- Together.ai (together.xyz)
- Local models (Ollama, vLLM, etc.)

Usage:
    # Using Anthropic (default)
    export ANTHROPIC_API_KEY="sk-ant-..."
    python cdss_lit_review_pipeline.py pubmed_export.csv
    
    # Using OpenRouter
    export OPENROUTER_API_KEY="sk-or-..."
    python cdss_lit_review_pipeline.py pubmed_export.csv --provider openrouter --model meta-llama/llama-2-70b-chat-hf
    
    # Using Together.ai
    export TOGETHER_API_KEY="..."
    python cdss_lit_review_pipeline.py pubmed_export.csv --provider together --model meta-llama/Llama-2-70b-chat-hf
    
    # Using local Ollama
    python cdss_lit_review_pipeline.py pubmed_export.csv --provider local --model llama2 --api-url http://localhost:11434/v1
"""

import json
import csv
import time
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import re

try:
    from openai import OpenAI
except ImportError:
    print("Error: openai package not found. Install with: pip install openai")
    sys.exit(1)

try:
    import pandas as pd
except ImportError:
    pd = None


# API Configuration for different providers
API_CONFIGS = {
    'anthropic': {
        'base_url': 'https://api.anthropic.com/v1',
        'api_key_env': 'ANTHROPIC_API_KEY',
        'default_model': 'claude-opus-4-5-20251101',
        'description': 'Anthropic Claude models',
        'max_tokens': 4096
    },
    'openrouter': {
        'base_url': 'https://openrouter.ai/api/v1',
        'api_key_env': 'OPENROUTER_API_KEY',
        'default_model': 'meta-llama/llama-2-70b-chat-hf',
        'description': 'OpenRouter (100+ models available)',
        'max_tokens': 4096,
        'note': 'Popular models: meta-llama/llama-2-70b-chat-hf, mistralai/mistral-7b-instruct, openchat/openchat-7b'
    },
    'together': {
        'base_url': 'https://api.together.xyz/v1',
        'api_key_env': 'TOGETHER_API_KEY',
        'default_model': 'meta-llama/Llama-2-70b-chat-hf',
        'description': 'Together.ai (various open source models)',
        'max_tokens': 4096
    },
    'local': {
        'base_url': 'http://localhost:11434/v1',
        'api_key_env': None,
        'default_model': 'llama2',
        'description': 'Local models via Ollama/vLLM',
        'max_tokens': 2048,
        'note': 'Run: ollama serve (or other local server)'
    },
    'groq': {
        'base_url': 'https://api.groq.com/openai/v1',
        'api_key_env': 'GROQ_API_KEY',
        'default_model': 'mixtral-8x7b-32768',
        'description': 'Groq (very fast inference)',
        'max_tokens': 8192,
        'note': 'Models: mixtral-8x7b-32768, llama2-70b-4096'
    }
}


class LLMClient:
    """Wrapper for any OpenAI-compatible LLM API"""
    
    def __init__(self, provider: str = 'anthropic', model: Optional[str] = None, 
                 api_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize LLM client
        
        Args:
            provider: 'anthropic', 'openrouter', 'together', 'local', 'groq'
            model: Model name (uses provider default if not specified)
            api_url: Custom API URL (overrides provider default)
            api_key: API key (uses env var if not specified)
        """
        self.provider = provider.lower()
        
        if self.provider not in API_CONFIGS:
            raise ValueError(f"Unknown provider: {provider}. Choose from: {list(API_CONFIGS.keys())}")
        
        config = API_CONFIGS[self.provider]
        
        # Get API URL
        self.base_url = api_url or config['base_url']
        
        # Get model
        self.model = model or config['default_model']
        
        # Get API key
        if config['api_key_env']:
            self.api_key = api_key or os.getenv(config['api_key_env'])
            if not self.api_key and provider != 'local':
                raise ValueError(f"API key not found. Set {config['api_key_env']} environment variable")
        else:
            self.api_key = 'not-needed'  # Local models don't need a key
        
        # Initialize OpenAI client with custom base URL
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        self.max_tokens = config.get('max_tokens', 4096)
        
        print(f"✓ Initialized {config['description']}")
        print(f"  Model: {self.model}")
        print(f"  Base URL: {self.base_url}")
    
    def call(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """
        Call LLM with prompt
        
        Args:
            prompt: Input prompt
            max_tokens: Max tokens (uses default if not specified)
        
        Returns:
            Model response text
        """
        max_tokens = max_tokens or self.max_tokens
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.3  # Lower temperature for more consistent results
        )
        
        return response.choices[0].message.content


class CDSSLitReviewProcessor:
    """Main pipeline processor for systematic literature review"""
    
    def __init__(self, llm_client: LLMClient, output_dir: str = "lit_review_output", 
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
            # Step 1: Parse CSV
            self._log("\n[STEP 1/6] Parsing PubMed export...")
            articles = self._parse_pubmed_csv(pubmed_csv_file)
            articles_file = self.output_dir / "01_parsed_articles.json"
            self._save_json(articles, articles_file)
            self._log(f"✓ Parsed {len(articles)} articles from {pubmed_csv_file}")
            
            # Step 2: Screen articles
            self._log("\n[STEP 2/6] Screening titles and abstracts...")
            screening_results = self._screen_articles(articles)
            screening_file = self.output_dir / "02_screening_results.json"
            self._save_json(screening_results, screening_file)
            
            include_count = sum(1 for r in screening_results if r['decision'] == 'INCLUDE')
            exclude_count = sum(1 for r in screening_results if r['decision'] == 'EXCLUDE')
            uncertain_count = sum(1 for r in screening_results if r['decision'] == 'UNCERTAIN')
            
            self._log(f"✓ Screening complete:")
            self._log(f"  - INCLUDE: {include_count}")
            self._log(f"  - EXCLUDE: {exclude_count}")
            self._log(f"  - UNCERTAIN: {uncertain_count}")
            
            # Step 3: Extract data from included articles
            self._log("\n[STEP 3/6] Extracting data from included articles...")
            included_pmids = {r['pmid'] for r in screening_results if r['decision'] == 'INCLUDE'}
            included_articles = [a for a in articles if a['pmid'] in included_pmids]
            
            if not included_articles:
                self._log("ERROR: No articles included after screening. Aborting.", "ERROR")
                return
            
            extracted_data = self._extract_article_data(included_articles)
            extraction_file = self.output_dir / "03_extracted_data.json"
            self._save_json(extracted_data, extraction_file)
            self._log(f"✓ Extracted data from {len(extracted_data)} articles")
            
            # Step 4: Assess quality
            self._log("\n[STEP 4/6] Assessing study quality (QUADAS-2)...")
            quality_assessments = self._assess_quality(extracted_data, included_articles)
            quality_file = self.output_dir / "04_quality_assessment.json"
            self._save_json(quality_assessments, quality_file)
            self._log(f"✓ Quality assessment complete for {len(quality_assessments)} studies")
            
            # Step 5: Synthesis
            self._log("\n[STEP 5/6] Performing thematic synthesis...")
            synthesis = self._perform_synthesis(extracted_data)
            synthesis_file = self.output_dir / "05_thematic_synthesis.txt"
            synthesis_file.write_text(synthesis)
            self._log(f"✓ Synthesis complete - {len(synthesis)} characters written")
            
            # Step 6: Generate summary table
            self._log("\n[STEP 6/6] Generating summary table...")
            if pd is not None:
                self._generate_summary_table(extracted_data)
                self._log(f"✓ Summary table created (CSV format)")
            else:
                self._log("⚠ Skipping summary table (pandas not installed)")
            
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
    
    def _parse_pubmed_csv(self, csv_file: str) -> List[Dict]:
        """Parse PubMed CSV export format"""
        articles = []
        
        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
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
                    if article['pmid']:  # Only include if PMID exists
                        articles.append(article)
            
            self._log(f"Successfully parsed {len(articles)} articles from CSV")
            return articles
            
        except Exception as e:
            self._log(f"Error parsing CSV: {str(e)}", "ERROR")
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
                response_text = self.llm.call(prompt, max_tokens=300)
                
                # Extract JSON from response (handles potential markdown formatting)
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
                response_text = self.llm.call(prompt, max_tokens=1500)
                
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
                # Add placeholder
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
                response_text = self.llm.call(prompt, max_tokens=500)
                
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
            'studies_sample': extracted_data[:3],  # First 3 for context
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

Write in clear, structured prose suitable for a systematic review report. Use concrete examples 
from the studies where possible."""
        
        try:
            synthesis_text = self.llm.call(synthesis_prompt, max_tokens=3000)
            return synthesis_text
            
        except Exception as e:
            self._log(f"Error performing synthesis: {str(e)}", "ERROR")
            return "Error generating synthesis"
    
    def _generate_summary_table(self, extracted_data: List[Dict]):
        """Generate CSV summary table"""
        if pd is None:
            self._log("Pandas not available, skipping summary table", "WARN")
            return
        
        rows = []
        for item in extracted_data:
            if 'extraction_error' in item:
                continue
            
            rows.append({
                'PMID': item.get('pmid', ''),
                'Year': item.get('year', ''),
                'Study Design': item.get('study_design', ''),
                'Clinical Domain': item.get('clinical_domain', ''),
                'Imaging Modality': ', '.join(item.get('imaging_modality', [])),
                'CDSS Type': item.get('cdss_type', ''),
                'Sample Size (N)': item.get('sample_size', {}).get('total_patients', ''),
                'Sensitivity': item.get('key_metrics', {}).get('sensitivity', ''),
                'Specificity': item.get('key_metrics', {}).get('specificity', ''),
                'AUC': item.get('key_metrics', {}).get('auc', ''),
                'Accuracy': item.get('key_metrics', {}).get('accuracy', ''),
                'Main Findings': item.get('main_findings', '')[:100]
            })
        
        df = pd.DataFrame(rows)
        output_file = self.output_dir / "summary_characteristics_table.csv"
        df.to_csv(output_file, index=False)
        self._log(f"Summary table saved ({len(rows)} studies)")
    
    def _save_json(self, data: any, filepath: Path):
        """Save data as formatted JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def create_parser():
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        description='LLM-based Literature Review Processing Pipeline for CDSS in Radiology',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
PROVIDERS:
  anthropic   - Anthropic Claude models (default)
  openrouter  - OpenRouter (100+ models)
  together    - Together.ai
  groq        - Groq (very fast)
  local       - Local models via Ollama/vLLM

EXAMPLES:
  # Anthropic (requires ANTHROPIC_API_KEY)
  %(prog)s pubmed.csv
  
  # OpenRouter (requires OPENROUTER_API_KEY)
  %(prog)s pubmed.csv --provider openrouter --model meta-llama/llama-2-70b-chat-hf
  
  # Together.ai (requires TOGETHER_API_KEY)
  %(prog)s pubmed.csv --provider together --model meta-llama/Llama-2-70b-chat-hf
  
  # Local Ollama
  %(prog)s pubmed.csv --provider local --model llama2
  
  # Groq (requires GROQ_API_KEY)
  %(prog)s pubmed.csv --provider groq --model mixtral-8x7b-32768
        """
    )
    
    parser.add_argument('csv_file', help='PubMed CSV export file')
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
    print("AVAILABLE LLM PROVIDERS")
    print("="*70 + "\n")
    
    for provider_name, config in API_CONFIGS.items():
        print(f"Provider: {provider_name.upper()}")
        print(f"  Description: {config['description']}")
        print(f"  Default Model: {config['default_model']}")
        if 'api_key_env' in config and config['api_key_env']:
            print(f"  API Key Env Var: {config['api_key_env']}")
        if 'note' in config:
            print(f"  Note: {config['note']}")
        print()


def main():
    """Main entry point"""
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
        llm_client = LLMClient(
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
