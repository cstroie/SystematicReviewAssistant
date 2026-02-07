# Systematic Literature Review Tool

A tool for automating systematic literature reviews using PubMed exports and LLM processing.

## Key Features

- PubMed export parsing (CSV, MEDLINE, XML, JSON)
- Direct API integration with multiple LLM providers
- Pipeline for screening, extraction, quality assessment and synthesis
- Customizable LLM prompts and parameters

## Quick Start

1. Install requirements:  
   ```bash
   pip install -r requirements.txt
   ```
2. Configure your API keys (see `DIRECT_API_SETUP.md`)
3. Run a review:  
   ```bash
   python lit_review.py pubmed_export.csv
   ```

## Documentation

- [QUICKSTART.md](QUICKSTART.md) - Detailed getting started guide
- [PUBMED_QUERY.md](PUBMED_QUERY.md) - Creating effective PubMed searches
- [MULTI_PROVIDER_GUIDE.md](MULTI_PROVIDER_GUIDE.md) - Using different LLM providers  
- [WORKFLOW.md](WORKFLOW.md) - Pipeline architecture overview

## Output Files

Results are saved in `lit_review_output/` with timestamps:
- `screened_articles.json`
- `extracted_data.json`
- `quality_assessments.json`
- `synthesis_report.md`
- `summary_table.csv`

## Support

For issues and feature requests, please open an issue on GitHub.
