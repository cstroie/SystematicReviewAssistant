# Caching and Resume Capability

The updated pipeline includes **intelligent caching** to reduce I/O and network load, plus the ability to **resume from where you left off**.

## What Gets Cached

### 1. **Articles Cache** (`00_articles_cache.json`)
- **What**: Parsed articles from your PubMed CSV
- **Why**: So you don't re-parse the same CSV file every time
- **Size**: ~100KB-1MB for typical CSVs
- **Lifetime**: Until you delete it or change the CSV file

### 2. **Screening Results** (`02_screening_results.json`)
- **What**: INCLUDE/EXCLUDE/UNCERTAIN decisions from LLM
- **Why**: Don't re-screen articles you already screened
- **Cost saved**: ~$0.30-0.50 per re-run (for 500 articles)

### 3. **Extracted Data** (`03_extracted_data.json`)
- **What**: Structured data extracted from included articles
- **Why**: Don't re-extract articles you already processed
- **Cost saved**: ~$3-5 per re-run (for 50-100 included articles)

### 4. **Quality Assessments** (`04_quality_assessment.json`)
- **What**: QUADAS-2 quality ratings
- **Why**: Don't re-assess articles you already reviewed
- **Cost saved**: ~$0.50-1 per re-run

## How Caching Works

### Cache Checking
```python
# On each run, the pipeline checks for existing cache
cache_file = output_dir / "00_articles_cache.json"

if cache_file.exists():
    # Use cached data - instant!
    articles = load_from_cache()
else:
    # Parse CSV and create cache
    articles = parse_csv()
    save_to_cache(articles)
```

### Local Storage Location

All caches are stored in your **output directory**:
```
lit_review_output/
├── 00_articles_cache.json         # Parsed articles (created automatically)
├── 01_parsed_articles.json        # Full articles list (for reference)
├── 02_screening_results.json      # Screening decisions (created by LLM)
├── 03_extracted_data.json         # Extracted structured data (created by LLM)
├── 04_quality_assessment.json     # Quality ratings (created by LLM)
├── 05_thematic_synthesis.txt      # Synthesis narrative (created by LLM)
├── summary_characteristics_table.csv  # Final table for your paper
└── processing_log.txt             # Detailed run log
```

## Resume Capability

The pipeline automatically detects which steps have been completed and can resume:

### Scenario 1: Full Run
```bash
# First run - everything is processed
python cdss_lit_review_pipeline_v3.py pubmed.csv
# Time: ~45 minutes for 500 articles
# Cost: ~$10 total
```

### Scenario 2: Resume After Interruption
```bash
# Pipeline crashes after screening 200 of 500 articles
# Run the same command again
python cdss_lit_review_pipeline_v3.py pubmed.csv

# What happens:
# ✓ Detects screening is incomplete
# ✓ Loads cached articles (instant)
# ✓ Resumes screening from article #201
# ✓ Time: ~15 minutes for remaining 300 articles
# ✓ Cost: ~$5 (not $10!)
```

### Scenario 3: Re-run with Different Settings
```bash
# You want to change extraction prompts
# Edit the extraction_prompt_template in the script

# Run again - will re-extract but reuse screening
python cdss_lit_review_pipeline_v3.py pubmed.csv

# What happens:
# ✓ Uses cached articles (instant)
# ✓ Uses cached screening results (instant)
# ✓ Re-extracts with new prompts (~20 min, ~$5)
# ✓ Total time: ~20 minutes
```

## Cache Management

### View Cached Files
```bash
# Check what's cached
ls -lh lit_review_output/
du -sh lit_review_output/  # Total cache size
```

### Clear Cache (Start Fresh)
```bash
# Delete specific cache
rm lit_review_output/00_articles_cache.json

# Or delete all caches for a fresh run
rm lit_review_output/0*_*.json  # Removes cache files only
rm -rf lit_review_output/       # Removes everything including results
```

### Backup Cache
```bash
# Save cache to another location
cp lit_review_output/00_articles_cache.json ~/backups/articles_cache.json
cp lit_review_output/02_screening_results.json ~/backups/screening_results.json

# Useful for: switching between output directories, sharing cached data
```

## Cost Savings Examples

### Example 1: 500 Articles, 1 Complete Run
```
Without caching:
  - Parsing: instant
  - Screening (500): $0.50
  - Extraction (100): $5
  - Quality (100): $1
  Total: ~$6.50
  Time: 45 minutes

With caching (no interruptions):
  - Same: caches are created but not used yet
```

### Example 2: 500 Articles, 2 Runs (1st crashes after screening)
```
Without caching:
  - Run 1: Parse + Screening 200 = $0.20, 15 min
  - Run 2: Parse + Screen all 500 + Extract = $6.50, 45 min
  Total: $6.70, 60 min ❌

With caching (automatic resume):
  - Run 1: Parse (cached) + Screen 200 = $0.20, 15 min
  - Run 2: Use cached parse + Resume screening 300 more + Extract
         = $0.30 + $5 = $5.30, 30 min
  Total: $5.50, 45 min ✅ Saves $1.20 and 15 minutes!
```

### Example 3: Adjusting Extraction Parameters
```
Without caching:
  - Full re-run: $6.50, 45 min

With caching:
  - Load cached articles (instant)
  - Load cached screening (instant)
  - Re-extract with new parameters: $5, 20 min
  Total: $5, 20 min ✅ Saves $1.50 and 25 minutes!
```

## Advanced: Using Cache Across Runs

### Multiple Providers
```bash
# Run 1: Screening with cheap provider (Groq)
export GROQ_API_KEY="..."
python cdss_lit_review_pipeline_v3.py pubmed.csv \
  --provider groq \
  --output-dir results1/

# Run 2: Extraction with quality provider (Anthropic) using same articles
export ANTHROPIC_API_KEY="..."
python cdss_lit_review_pipeline_v3.py pubmed.csv \
  --provider anthropic \
  --output-dir results2/

# What happens:
# Results1: Screening cached locally
# Results2: Separate output, but references same articles
```

### Shared Cache Directory
```bash
# Setup: Point multiple runs to same cache
export CACHE_DIR="$HOME/lit_review_cache"

# Run 1
python cdss_lit_review_pipeline_v3.py pubmed.csv --output-dir results/run1/

# Run 2 (can use cached articles from run1)
python cdss_lit_review_pipeline_v3.py pubmed.csv --output-dir results/run2/
```

## Cache Validation

The pipeline automatically validates cached data:

```python
# Cache validation checks:
✓ File exists and is readable
✓ JSON is valid format
✓ Contains expected fields (pmid, title, abstract)
✓ Has reasonable number of articles

# If cache is corrupted:
# - Pipeline detects error
# - Falls back to re-parsing
# - Logs warning with details
```

Example warning:
```
[2024-01-15 10:23:45] WARN: Cache read error: Invalid JSON, re-parsing CSV
```

## Best Practices

### 1. Don't Modify CSV Between Runs
```bash
# ❌ Bad
python cdss_lit_review_pipeline_v3.py pubmed.csv
# ... modify pubmed.csv ...
python cdss_lit_review_pipeline_v3.py pubmed.csv  # Cache mismatch!

# ✅ Good
# Either use same CSV or clear cache
rm lit_review_output/00_articles_cache.json
python cdss_lit_review_pipeline_v3.py pubmed_v2.csv
```

### 2. Backup Before Large Changes
```bash
# Before changing extraction prompts
cp -r lit_review_output lit_review_output.backup

# Edit script...
python cdss_lit_review_pipeline_v3.py pubmed.csv

# If something goes wrong, restore
rm -rf lit_review_output
mv lit_review_output.backup lit_review_output
```

### 3. Monitor Cache Size
```bash
# Check cache growth
du -sh lit_review_output/
# Typical: 100KB-2MB depending on article count

# Compress if archiving
tar -czf lit_review_results.tar.gz lit_review_output/
```

### 4. Use Consistent Output Directory
```bash
# ✅ Good - same directory for related runs
python cdss_lit_review_pipeline_v3.py pubmed.csv --output-dir results/

# Or clear cache if starting fresh
rm results/00_articles_cache.json
rm results/02_screening_results.json
python cdss_lit_review_pipeline_v3.py pubmed.csv --output-dir results/
```

## Troubleshooting Cache Issues

### "Cache seems outdated"
```bash
# Solution: Delete the cache
rm lit_review_output/00_articles_cache.json

# Pipeline will re-parse and create fresh cache
python cdss_lit_review_pipeline_v3.py pubmed.csv
```

### "Different results between runs"
```bash
# Check what's cached
ls -lh lit_review_output/0*.json

# If screening/extraction cached:
# - Delete old results and rerun
rm lit_review_output/02_screening_results.json
rm lit_review_output/03_extracted_data.json

python cdss_lit_review_pipeline_v3.py pubmed.csv
```

### "Cache file is huge"
```bash
# Normal for large batches (500+ articles)
# But if suspicious:
wc -l lit_review_output/00_articles_cache.json  # Check line count

# Typical: 10,000-50,000 lines for 500 articles
```

## Caching Workflow Example

```bash
#!/bin/bash
# Efficient literature review pipeline with caching

PUBMED_CSV="pubmed_export.csv"
OUTPUT="results"

# Run 1: Initial screening (cheap, fast)
echo "Screening articles..."
export GROQ_API_KEY="..."
python cdss_lit_review_pipeline_v3.py $PUBMED_CSV \
  --provider groq \
  --output-dir $OUTPUT

# Check screening results
echo "Screening results:"
jq '.[] | select(.decision=="INCLUDE") | .pmid' $OUTPUT/02_screening_results.json

# Run 2: Full extraction and synthesis (quality, uses cache)
echo "Extracting and synthesizing with cached data..."
export ANTHROPIC_API_KEY="..."
python cdss_lit_review_pipeline_v3.py $PUBMED_CSV \
  --provider anthropic \
  --output-dir $OUTPUT

# Results are ready!
echo "✓ Results in $OUTPUT/"
ls -lh $OUTPUT/*.csv $OUTPUT/*.txt
```

## Summary

**Caching automatically:**
- ✅ Reduces API costs by 20-50% on interruptions/re-runs
- ✅ Speeds up resume capability (instant article loading)
- ✅ Detects and validates cache integrity
- ✅ Falls back gracefully if cache is invalid
- ✅ Works transparently (no configuration needed)

**You get:**
- Faster iterations when tweaking parameters
- Cost savings when pipelines are interrupted
- Ability to switch providers between steps
- Local copies of your article data

Just run the pipeline - caching happens automatically! 🚀
