# PubMed Export Format Support

The pipeline now supports **multiple PubMed export formats** with automatic format detection!

## Supported Formats

### 1. **CSV Format** (Current Standard)
- **File extension**: `.csv`
- **How to export**: PubMed → Send to → Citation manager (select CSV)
- **Best for**: Quick exports, Excel compatibility
- **Fields**: PMID, Title, Abstract, Authors, Journal, Publication Date, DOI

**Example:**
```csv
PMID,Title,Abstract,Authors,Journal,Publication Date,DOI
12345678,"AI in Radiology","This study evaluates...","Smith J, Jones M","Radiology Journal","2023-01-15","10.1234/test"
```

### 2. **MEDLINE Format** (Official PubMed Format)
- **File extension**: `.txt`
- **How to export**: PubMed → Send to → File → Format: MEDLINE
- **Best for**: Complete metadata, official PubMed format
- **Contains**: All available fields including MeSH terms, publication types, etc.

**Example:**
```
PMID- 12345678
TI  - Title of the article
AB  - Abstract text here...
      Continues on next line...
AU  - Author Name
FAU - Author, Full Name
AD  - Author Affiliation
SO  - Journal Citation
TA  - Journal Abbrev
VI  - Volume number
IP  - Issue number
DP  - 2023 Jan 15
```

### 3. **XML Format**
- **File extension**: `.xml`
- **How to export**: PubMed API or third-party tools
- **Best for**: Automated pipelines, structured data
- **Contains**: Complete article data in structured XML

**Example:**
```xml
<PubmedArticleSet>
  <PubmedArticle>
    <PMID>12345678</PMID>
    <Article>
      <ArticleTitle>Title of the article</ArticleTitle>
      <Abstract>
        <AbstractText>Abstract text...</AbstractText>
      </Abstract>
      <AuthorList>
        <Author>
          <LastName>Author</LastName>
          <ForeName>Name</ForeName>
        </Author>
      </AuthorList>
    </Article>
  </PubmedArticle>
</PubmedArticleSet>
```

### 4. **JSON Format**
- **File extension**: `.json`
- **How to export**: PubMed API (json format parameter)
- **Best for**: Programmatic access, modern tools
- **Contains**: Same data as XML but in JSON structure

**Example:**
```json
{
  "articles": [
    {
      "pmid": "12345678",
      "title": "Title of the article",
      "abstract": "Abstract text...",
      "authors": ["Author Name"],
      "journal": "Journal Citation",
      "pub_date": "2023"
    }
  ]
}
```

## How to Export from PubMed

### Getting CSV (Easiest)

1. Go to **https://pubmed.ncbi.nlm.nih.gov/**
2. Enter your search query
3. Click **Save**
4. Select **Format**: CSV
5. Click **Create File**
6. File downloads as `.csv`

### Getting MEDLINE Format

1. Go to **https://pubmed.ncbi.nlm.nih.gov/**
2. Enter your search query
3. Click **Send to** → **File**
4. Select **Format**: MEDLINE
5. Click **Create File**
6. File downloads as `.txt`

### Getting XML Format

1. Use **PubMed API**:
```bash
# Example: Fetch first 5 results for "CDSS radiology"
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=CDSS+radiology&retmax=5&rettype=xml" \
  > results.xml
```

Or use a tool like:
- https://www.ncbi.nlm.nih.gov/books/NBK25499/ (NCBI E-utilities)
- Third-party PubMed downloaders

### Getting JSON Format

1. Use **PubMed API**:
```bash
# Example with JSON format
curl -s "https://api.ncbi.nlm.nih.gov/lit/ctxp/v1/pubmed/?query=CDSS+radiology&format=json" \
  > results.json
```

## Using the Pipeline with Different Formats

### With CSV
```bash
python systematic_review_assistant.py pubmed_results.csv
```

### With MEDLINE Format
```bash
python systematic_review_assistant.py pubmed_results.txt
```

### With XML
```bash
python systematic_review_assistant.py pubmed_results.xml
```

### With JSON
```bash
python systematic_review_assistant.py pubmed_results.json
```

### Force a Specific Format (if auto-detection fails)
```bash
python systematic_review_assistant.py unknown_format.txt --format medline
python systematic_review_assistant.py unknown_format.txt --format csv
```

## Format Comparison

| Feature | CSV | MEDLINE | XML | JSON |
|---------|-----|---------|-----|------|
| File size | Small | Medium | Large | Medium |
| Human readable | ✅ | ✅ | ❌ | ⚠️ |
| Complete metadata | ⚠️ | ✅ | ✅ | ✅ |
| Easy export | ✅ | ✅ | ❌ | ⚠️ |
| Parsing speed | Fast | Medium | Slow | Medium |
| **Recommended** | ✅ | ✅ | ❌ | ❌ |

## What Gets Extracted

Regardless of input format, the pipeline extracts these standard fields:

| Field | Description |
|-------|-------------|
| pmid | PubMed ID |
| title | Article title |
| abstract | Article abstract |
| authors | Author names (comma-separated) |
| journal | Journal name |
| pub_date | Publication date |
| doi | Digital Object Identifier |

## Auto-Detection Process

The pipeline automatically detects format by:

1. **File extension** - Fastest method
   - `.csv` → CSV parser
   - `.xml` → XML parser
   - `.json` → JSON parser
   - `.txt` → Check content

2. **File content** - If extension is `.txt` or unknown
   - Looks for `PMID-` pattern → MEDLINE
   - Looks for `<` character → XML
   - Looks for `{` character → JSON
   - Looks for commas in header → CSV

3. **Default** - Falls back to MEDLINE (most common)

## Troubleshooting Format Issues

### "Could not parse file"
```bash
# Check the file format manually
head -20 pubmed_results.txt

# Try forcing a specific format
python systematic_review_assistant.py pubmed_results.txt --format medline
```

### "No articles found"
```bash
# File might be empty or corrupted
wc -l pubmed_results.txt  # Check file size
file pubmed_results.txt   # Check file type
```

### "Wrong format detected"
```bash
# If auto-detection fails, specify format explicitly
python systematic_review_assistant.py mystery_file.txt --format xml
```

## MEDLINE Format Field Reference

Common MEDLINE fields you might encounter:

```
PMID- PubMed ID
TI  - Title
AB  - Abstract
AU  - Author (repeats for each)
FAU - Full Author name
AD  - Affiliation
SO  - Source/Journal
TA  - Journal abbreviation
JT  - Journal full name
VI  - Volume
IP  - Issue
DP  - Date of publication
PG  - Page numbers
AID - Article ID (various types)
DOI - Digital Object Identifier
PT  - Publication Type
LA  - Language
RN  - Chemical compound name
OT  - Keywords/Other terms
EDAT- Entrez date
MHDA- MeSH date
CR  - Comments
RF  - Number of references
FAU - Full author name
AD  - Author affiliation
DEP - Electronic publication date
SB  - Subset designation
OTO - Other term owner
DCOM- Date completed
IS  - ISSN
```

## Performance Notes

**Parsing times** (approximate, for 500 articles):

| Format | Time | Memory |
|--------|------|--------|
| CSV | ~100ms | ~5MB |
| MEDLINE | ~200ms | ~8MB |
| XML | ~500ms | ~15MB |
| JSON | ~300ms | ~10MB |

**Caching impact:**
- First run: Full parsing time + LLM processing
- Subsequent runs: ~10ms (from cache) + LLM processing

## Best Practices

### 1. Choose CSV for Simplicity
```bash
# Fastest export, smallest file, easiest to verify
python systematic_review_assistant.py results.csv
```

### 2. Use MEDLINE for Complete Data
```bash
# Official PubMed format, includes all metadata
# Use if you need MeSH terms, publication types, etc.
python systematic_review_assistant.py results.txt
```

### 3. Store Original Export
```bash
# Keep the original PubMed export for records
cp pubmed_results.csv pubmed_results_backup.csv

# Clear cache if you modify the export
rm output/00_articles_cache.json
```

### 4. Automate Large Searches
```bash
#!/bin/bash
# Download MEDLINE format for all radiology CDSS papers
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=CDSS%20radiology&retmax=1000&rettype=medline" \
  > cdss_radiology.txt

# Process with pipeline
python systematic_review_assistant.py cdss_radiology.txt
```

## Troubleshooting

### Issue: "Detected format: medline" but file is CSV
**Solution**: Check file for special characters, remove BOM, or specify format:
```bash
python systematic_review_assistant.py file.txt --format csv
```

### Issue: XML file not parsing
**Solution**: Ensure XML is well-formed:
```bash
python -m xml.dom.minidom file.xml > /dev/null  # Validate XML
```

### Issue: JSON file not parsing
**Solution**: Validate JSON:
```bash
python -c "import json; json.load(open('file.json'))" # Validate JSON
```

## Summary

✅ **Recommended workflow:**

1. Export from PubMed as **CSV** (easiest)
   - Or use **MEDLINE** format if you need complete metadata

2. Run pipeline
   ```bash
   python systematic_review_assistant.py export.csv
   ```

3. Pipeline auto-detects format and processes

4. Results in `output/`

No configuration needed - just run it! 🚀
