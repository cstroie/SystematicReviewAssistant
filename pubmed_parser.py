"""
Multi-format PubMed export parser
Supports: MEDLINE (.txt), CSV (.csv), XML (.xml), JSON (.json)

This module handles automatic format detection and parsing of PubMed exports.
"""

import json
import csv
from pathlib import Path
from typing import List, Dict, Optional
import re


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
        current_field = None
        current_value = []
        
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
            if article_elem is not None:
                article = PubMedParser._parse_xml_article(article_elem)
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


# Test the parser
if __name__ == '__main__':
    # Simple command line test
    import sys
    if len(sys.argv) > 1:
        try:
            articles = PubMedParser.parse(sys.argv[1])
            if articles:
                print(f"\nFirst PMID: {articles[0].get('pmid')} - {articles[0].get('title')[:80]}...")
    
        except Exception as e:
            print(f"Error: {str(e)}")
            sys.exit(1)
