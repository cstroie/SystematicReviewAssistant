#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# LaTeX Article Generator for Systematic Review
# Generates a publication-ready LaTeX article from systematic review data.
# Uses direct HTTP API calls to LLM for article generation.
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
LaTeX Article Generator for Systematic Review

Generates a publication-ready LaTeX article from systematic review data using
Large Language Model (LLM) APIs. This tool automates the creation of comprehensive
systematic review articles that follow PRISMA 2020 guidelines and include
thematic synthesis, quality assessment, and statistical analysis.

The system processes pipeline outputs from systematic review workflows,
including screening results, extracted data, quality assessments, and
thematic synthesis. It then generates a complete LaTeX document suitable
for submission to high-impact medical imaging or AI-in-healthcare journals.

Key Features:
- PRISMA 2020 compliant article structure
- Integration of quantitative and qualitative data
- Support for multiple LLM providers (Anthropic, OpenRouter, Together, Groq, Local)
- Streaming mode for large document generation
- Automatic BibTeX reference generation
- Comprehensive error handling and retry logic
- Detailed progress reporting and debugging capabilities

Technical Architecture:
- DataCollector: Gathers and processes pipeline outputs
- LaTeXArticleGenerator: Constructs prompts and manages LLM API interactions
- Modular prompt system with external template files
- Robust data formatting and validation
- Support for both streaming and non-streaming API modes

Usage Examples:
    # Basic usage with default settings
    python generate_latex_article.py /path/to/workdir

    # Specify LLM provider and model
    python generate_latex_article.py /path/to/workdir --provider anthropic

    # Use streaming mode for large articles
    python generate_latex_article.py /path/to/workdir --stream --verbose

    # Custom model and temperature
    python generate_latex_article.py /path/to/workdir --model claude-3-opus-20240229 --temperature 0.7

    # Debug mode for troubleshooting
    python generate_latex_article.py /path/to/workdir --debug

Required Pipeline Outputs:
- 00_plan.json: Study protocol and research design
- 01_parsed_articles.json: Original parsed articles from databases
- 02_screening_results.json: Screening decisions and PRISMA flow data
- 03_extracted_data.json: Structured extracted study data
- 04_quality_assessment.json: Quality assessment results
- 05_thematic_synthesis.txt: Qualitative synthesis findings
- 06_summary_characteristics.csv: Study characteristics matrix

Generated Outputs:
- 07_review.tex: Complete LaTeX article document
- references.bib: BibTeX entries for all included studies
- debug/prompt_*.txt: Prompt templates for debugging (when debug=True)

Dependencies:
- Python 3.8+
- Standard library modules: json, csv, urllib, argparse, os, time
- No external dependencies required for core functionality

Author: Costin Stroie <costinstroie@eridu.eu.org>
GitHub: https://github.com/cstroie/SystematicReviewAssistant
Version: 1.0.0
"""

import json
import csv
import urllib.request
import urllib.error
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse
import os
import time


class DataCollector:
    """Collects and prepares systematic review data from pipeline outputs.

    This class orchestrates the complete data collection and preparation process
    for systematic review article generation. It loads, validates, and processes
    outputs from all stages of the systematic review pipeline, transforming
    raw data into a structured format suitable for LaTeX article generation.

    The collector implements robust error handling to gracefully manage missing
    or corrupted files, allowing the pipeline to continue processing with
    available data. It performs data type conversion, statistical analysis,
    and organization of information into logical categories for efficient
    access during article generation.

    The class processes multiple data types including JSON files for structured
    data, CSV files for tabular information, and text files for qualitative
    synthesis. It calculates summary statistics and organizes data into
    a hierarchical structure that facilitates easy access during the
    article generation process.

    Attributes:
        workdir (str): Path to the pipeline output directory containing all
                      generated files from the systematic review pipeline.
                      This directory should contain outputs from all previous
                      stages including screening, extraction, quality assessment,
                      and synthesis.
        data (dict): Comprehensive dictionary containing all collected and
                    processed data, organized by category:
                    - workdir: Path to working directory
                    - plan: Study protocol and research design metadata
                    - screening: PRISMA flow statistics and screening decisions
                    - extracted: Structured extracted study data
                    - quality: Quality assessment results and risk of bias
                    - synthesis: Thematic synthesis text content
                    - original_articles: Original parsed article metadata
                    - characteristics_table: Study characteristics matrix
                    - statistics: Computed summary statistics and patterns

    Example:
        collector = DataCollector('/path/to/pipeline/output')
        data = collector.collect_all_data()
        # data now contains all processed information ready for article generation
    """

    def __init__(self, workdir: str):
        """Initialize data collector with output directory.

        Sets up the data collector with the specified working directory and
        initializes the data structure for storing collected information.

        Args:
            workdir (str): Path to directory containing pipeline output files.
                This directory should contain all generated files from the
                systematic review pipeline, including JSON, CSV, and text files
                from screening, extraction, quality assessment, and synthesis
                stages.

        Example:
            collector = DataCollector('/path/to/systematic/review/output')
        """
        self.workdir = Path(workdir)
        self.data = {
            'original_articles': []
        }

    def collect_all_data(self) -> Dict:
        """Collect and organize all data from pipeline outputs.

        This method orchestrates the complete data collection process by calling
        individual loaders for each type of pipeline output. It processes files
        in a specific order to ensure dependencies are met, calculates summary
        statistics from the extracted data, and organizes everything into a
        structured dictionary ready for article generation.

        The method follows a sequential processing order:
        1. Study plan (00_plan.json) - provides research context and metadata
        2. Screening results (02_screening_results.json) - PRISMA flow data
        3. Extracted data (03_extracted_data.json) - structured study information
        4. Quality assessment (04_quality_assessment.json) - risk of bias evaluation
        5. Original articles (01_parsed_articles.json) - reference metadata
        6. Thematic synthesis (05_thematic_synthesis.txt) - qualitative findings
        7. Characteristics table (06_summary_characteristics.csv) - study matrix
        8. Statistics calculation - summary metrics and patterns

        The method handles various file formats including JSON, CSV, and text
        files, with appropriate error handling for each type. Missing files
        generate warnings but don't halt processing, ensuring robustness against
        incomplete pipeline outputs.

        Returns:
            dict: A comprehensive dictionary containing all collected data,
                  organized into the following sections:
                  - workdir: Path to the working directory
                  - plan: Study plan metadata including title, topic, search strategy
                  - screening: Screening statistics and PRISMA flow counts
                  - extracted: List of extracted study data with validated fields
                  - quality: List of quality assessment results and risk of bias
                  - synthesis: Thematic synthesis text content
                  - original_articles: Original parsed article metadata
                  - characteristics_table: Study characteristics matrix with organized fields
                  - statistics: Computed summary statistics including modalities, domains, designs

        Note:
            Missing files will generate warnings but not fatal errors. The
            method will continue processing with available data, ensuring
            robustness against incomplete pipeline outputs.

        Example:
            collector = DataCollector('/path/to/pipeline/output')
            data = collector.collect_all_data()
            print(f"Collected data for {data['statistics']['total_studies']} studies")
        """

        print("Collecting data from pipeline outputs...")
        self.data['workdir'] = str(self.workdir)

        # Load the study plan
        self._load_plan()

        # Load screening results
        self._load_screening_results()

        # Load extracted data
        self._load_extracted_data()

        # Load quality assessment
        self._load_quality_assessment()

        # Load original articles for reference data
        self._load_original_articles()

        # Load thematic synthesis
        self._load_thematic_synthesis()

        # Load summary characteristics
        self._load_summary_characteristics()

        # Calculate statistics
        self._calculate_statistics()

        print("Data collection complete")
        return self.data

    def _load_screening_results(self) -> None:
        """Load and process screening results from JSON file.

        This method loads screening results from the standard pipeline output
        file '02_screening_results.json' and processes them to calculate
        PRISMA 2020 compliant statistics. It handles various screening
        decisions (INCLUDE, EXCLUDE, UNCERTAIN) and computes the flow
        diagram numbers required for systematic review reporting.

        The method calculates and stores:
        - Total articles identified and screened
        - Number of articles excluded at screening stage
        - Number of articles requiring full-text assessment
        - Final inclusion numbers

        The screening results are essential for generating the PRISMA flow
        diagram and reporting the systematic review's selection process.

        Populates:
            self.data['screening'] (dict): Dictionary containing screening statistics
                with keys:
                - total_identified: Total articles found in search
                - total_screened: Articles that underwent screening
                - included: Articles marked for inclusion
                - excluded: Articles excluded at screening
                - uncertain: Articles needing full-text review
                - excluded_total: Total excluded (excluded + uncertain)
                - full_text_assessed: Articles that went to full-text
                - full_text_excluded: Articles excluded at full-text
                - final_included: Final number of included studies

        Note:
            If the file doesn't exist or contains invalid JSON, warnings are
            printed and an empty screening dictionary is stored to allow
            the pipeline to continue.

        Example:
            # After loading, screening data will be available as:
            screening_data = collector.data['screening']
            print(f"Final included: {screening_data['final_included']}")
        """
        file_path = self.workdir / "02_screening_results.json"

        if not file_path.exists():
            print(f"Warning: {file_path} not found")
            self.data['screening'] = {}
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                results = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {file_path}: {str(e)}")
            self.data['screening'] = {}
            return
        except IOError as e:
            print(f"Error: Cannot read {file_path}: {str(e)}")
            self.data['screening'] = {}
            return

        total = len(results)
        included = sum(1 for r in results if r.get('decision') == 'INCLUDE')
        excluded = sum(1 for r in results if r.get('decision') == 'EXCLUDE')
        uncertain = sum(1 for r in results if r.get('decision') == 'UNCERTAIN')

        self.data['screening'] = {
            'total_identified': total,
            'total_screened': total,
            'included': included,
            'excluded': excluded,
            'uncertain': uncertain,
            'excluded_total': excluded + uncertain,
            'full_text_assessed': included + uncertain,
            'full_text_excluded': uncertain,
            'final_included': included
        }

        print(f"  Screening: {included} included, {excluded} excluded, {uncertain} uncertain")

    def _load_extracted_data(self) -> None:
        """Load extracted study data from JSON file.

        This method loads the extracted study data from the pipeline output
        file '03_extracted_data.json'. The extracted data contains detailed
        information about each included study, including methodology,
        results, and metadata collected during the data extraction phase.

        The method filters out any studies that encountered extraction
        errors, ensuring only valid data is included in the final article.
        This validation step prevents corrupted or incomplete data from
        affecting the article generation process.

        The extracted data forms the core content of the systematic review,
        providing the material for the results, discussion, and thematic
        synthesis sections.

        Populates:
            self.data['extracted'] (list): List of dictionaries containing
                extracted study data. Each dictionary represents one study
                and contains fields such as:
                - title: Study title
                - authors: List of authors
                - journal: Publication journal
                - year: Publication year
                - study_design: Study methodology type
                - imaging_modality: Imaging techniques used
                - clinical_domain: Medical specialty area
                - sample_size: Patient numbers
                - key_metrics: Performance metrics
                - key_findings: Main findings and conclusions
                - And other extracted fields based on the extraction form

        Note:
            Missing files or invalid JSON will generate warnings and result
            in an empty extracted data list, allowing the pipeline to continue
            with available data.

        Example:
            # After loading, extracted data will be available as:
            extracted_data = collector.data['extracted']
            print(f"Loaded {len(extracted_data)} studies")
            for study in extracted_data:
                print(f"Study: {study['title']}")
        """
        file_path = self.workdir / "03_extracted_data.json"

        if not file_path.exists():
            print(f"Warning: {file_path} not found")
            self.data['extracted'] = []
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {file_path}: {str(e)}")
            self.data['extracted'] = []
            return
        except IOError as e:
            print(f"Error: Cannot read {file_path}: {str(e)}")
            self.data['extracted'] = []
            return

        # Filter out items with errors
        self.data['extracted'] = [d for d in data if 'error' not in d]

        print(f"  Extracted: {len(self.data['extracted'])} studies")

    def _load_quality_assessment(self) -> None:
        """Load quality assessment data from JSON file.

        This method loads quality assessment results from the pipeline output
        file '04_quality_assessment.json'. The quality assessment evaluates
        each study using standardized tools (typically QUADAS-2 for diagnostic
        accuracy studies) to assess risk of bias and methodological quality.

        Studies with assessment errors are filtered out to ensure only valid
        quality assessments are included in the final article. This quality
        assessment data is crucial for the discussion section, where the
        strength of evidence and risk of bias are analyzed.

        The quality assessment results are used to:
        - Generate Table 2 (Quality Assessment Summary)
        - Support risk of bias analysis in the discussion
        - Provide context for the strength of evidence
        - Identify methodological limitations across studies

        Populates:
            self.data['quality'] (list): List of dictionaries containing
                quality assessment results. Each dictionary includes:
                - study_id: Identifier for the study
                - overall_bias: Overall risk of bias (Low/Moderate/High)
                - domain_specific_ratings: Ratings for individual domains
                - risk_of_bias_details: Detailed assessment notes
                - And other quality assessment metrics based on the tool used

        Note:
            Missing files or invalid JSON will generate warnings and result
            in an empty quality assessment list, allowing the pipeline to
            continue with available data.

        Example:
            # After loading, quality data will be available as:
            quality_data = collector.data['quality']
            low_risk = sum(1 for q in quality_data if q['overall_bias'] == 'Low')
            print(f"Low risk studies: {low_risk}")
        """
        file_path = self.workdir / "04_quality_assessment.json"

        if not file_path.exists():
            print(f"Warning: {file_path} not found")
            self.data['quality'] = []
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {file_path}: {str(e)}")
            self.data['quality'] = []
            return
        except IOError as e:
            print(f"Error: Cannot read {file_path}: {str(e)}")
            self.data['quality'] = []
            return

        self.data['quality'] = [d for d in data if 'error' not in d]

        print(f"  Quality assessment: {len(self.data['quality'])} studies rated")

    def _load_thematic_synthesis(self) -> None:
        """Load thematic synthesis text from file.

        This method loads the thematic synthesis text from the pipeline output
        file '05_thematic_synthesis.txt'. The thematic synthesis represents
        the qualitative analysis of the included studies, identifying key
        themes, patterns, and insights across the literature.

        The synthesis text is used directly in the article's discussion and
        thematic synthesis sections, providing the qualitative backbone
        for the systematic review's interpretation. This qualitative analysis
        complements the quantitative results and provides deeper insights
        into the patterns and themes emerging from the literature.

        The thematic synthesis typically includes:
        - Major themes identified across studies
        - Patterns and trends in the literature
        - Contradictory findings and their explanations
        - Research gaps and future directions
        - Clinical implications and practical applications

        Populates:
            self.data['synthesis'] (str): String containing the complete
                thematic synthesis text. This text should be ready for
                inclusion in the LaTeX article and may include:
                - Major themes identified
                - Patterns across studies
                - Contradictory findings
                - Research gaps
                - Clinical implications

        Note:
            Missing files will generate warnings and result in empty
            synthesis text, allowing the pipeline to continue. The article
            generation will handle missing synthesis appropriately.

        Example:
            # After loading, synthesis data will be available as:
            synthesis_text = collector.data['synthesis']
            print(f"Synthesis length: {len(synthesis_text)} characters")
        """
        file_path = self.workdir / "05_thematic_synthesis.txt"

        if not file_path.exists():
            print(f"Warning: {file_path} not found")
            self.data['synthesis'] = ""
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.data['synthesis'] = f.read()
        except IOError as e:
            print(f"Error: Cannot read {file_path}: {str(e)}")
            self.data['synthesis'] = ""
            return

        print(f"  Synthesis: {len(self.data['synthesis'].split())} words, {len(self.data['synthesis'])} characters")

    def _load_original_articles(self) -> None:
        """Load original parsed articles from JSON file.

        This method loads the original parsed article data from the pipeline
        output file '01_parsed_articles.json'. This data contains the raw
        parsed information from PubMed or other database searches, before
        any screening or extraction was applied.

        The original articles data is used primarily for generating BibTeX
        entries and for reference when the extracted data might be missing
        certain metadata fields. This serves as a fallback for complete
        bibliographic information that may have been lost during the
        extraction process.

        The data is particularly valuable for:
        - Generating complete and accurate BibTeX entries
        - Filling missing metadata in extracted studies
        - Providing complete publication details
        - Ensuring proper citation formatting

        Populates:
            self.data['original_articles'] (list): List of dictionaries
                containing original parsed article data. Each dictionary
                includes fields such as:
                - title: Article title
                - authors: List of authors
                - journal: Journal name
                - volume, issue, pages: Publication details
                - doi: Digital Object Identifier
                - pmid: PubMed ID
                - url: Direct URL to article
                - year: Publication year
                - And other metadata extracted from the original source

        Note:
            Missing files or invalid JSON will generate warnings and result
            in an empty list, but the pipeline will continue as this data
            is primarily used for reference and BibTeX generation.

        Example:
            # After loading, original articles will be available as:
            original_articles = collector.data['original_articles']
            print(f"Loaded {len(original_articles)} original articles")
        """
        file_path = self.workdir / "01_parsed_articles.json"

        if not file_path.exists():
            print(f"Warning: {file_path} not found")
            self.data['original_articles'] = []
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.data['original_articles'] = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {file_path}: {str(e)}")
            self.data['original_articles'] = []
            return
        except IOError as e:
            print(f"Error: Cannot read {file_path}: {str(e)}")
            self.data['original_articles'] = []
            return

        print(f"  Original articles: {len(self.data['original_articles'])} loaded")

    def _load_plan(self) -> None:
        """Load plan metadata.

        This method loads the study plan metadata from the pipeline output
        file '00_plan.json'. The study plan contains the original research
        protocol information, including the review title, topic, search
        strategy, inclusion/exclusion criteria, and data extraction forms.

        This metadata is crucial for generating an accurate article that
        reflects the original research protocol and justifies the methods
        section. The study plan provides the foundation for the entire
        systematic review and ensures that the generated article is
        consistent with the original research objectives.

        The study plan typically includes:
        - Review title and research question
        - Search strategy and databases used
        - Inclusion and exclusion criteria
        - Data extraction form structure
        - Analysis approach and methodology
        - Quality assessment criteria

        Populates:
            self.data['plan'] (dict): Dictionary containing study plan
                metadata with keys such as:
                - title: Systematic review title
                - topic: Research topic description
                - search: Search strategy details
                - inclusion: Inclusion criteria
                - exclusion: Exclusion criteria
                - extract: Data extraction form structure
                - analysis: Analysis points and themes
                - And other protocol information

        Note:
            Missing files or invalid JSON will generate warnings and result
            in an empty plan dictionary. The pipeline will continue, but
            the generated article may have generic content where specific
            plan information is missing.

        Example:
            # After loading, plan data will be available as:
            plan_data = collector.data['plan']
            print(f"Review title: {plan_data['title']}")
        """
        file_path = self.workdir / "00_plan.json"

        if not file_path.exists():
            print(f"Warning: {file_path} not found")
            self.data['plan'] = {}
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.data['plan'] = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {file_path}: {str(e)}")
            self.data['plan'] = {}
            return
        except IOError as e:
            print(f"Error: Cannot read {file_path}: {str(e)}")
            self.data['plan'] = {}
            return

        print(f"  Study: {self.data['plan']['title']}")

    def _load_summary_characteristics(self) -> None:
        """Load summary characteristics CSV file.

        This method loads the summary characteristics table from the pipeline
        output file '06_summary_characteristics.csv'. This table contains
        structured data summarizing key characteristics of all included
        studies, typically organized as a matrix with studies as rows and
        characteristics as columns.

        This data is used to generate Table 1 in the systematic review,
        which provides an overview of the included studies' features. The
        characteristics table is a crucial component of the systematic review,
        providing a comprehensive summary of study features for readers.

        The method processes the raw CSV data to:
        - Convert numeric fields to appropriate types
        - Handle empty/missing values consistently
        - Clean up field names for better readability
        - Structure data in a more organized way

        The processed data is organized into logical categories:
        - basic_info: Core study information (title, year, domain, sample size)
        - methodology: Study design and technical details
        - performance: Quantitative performance metrics
        - findings: Qualitative findings and notes

        Populates:
            self.data['characteristics_table'] (list): List of dictionaries
                representing the characteristics table. Each dictionary
                corresponds to a row in the CSV and contains:
                - study_id: Unique identifier for each study (PMID or title)
                - basic_info: Dictionary with basic study information
                - methodology: Dictionary with study design and methodology details
                - performance: Dictionary with performance metrics (sensitivity, specificity, etc.)
                - findings: Dictionary with key findings and notes
                - All original fields are preserved but may be reorganized

        Note:
            Missing files or invalid CSV will generate warnings and result
            in an empty characteristics table. The pipeline will continue,
            but the generated article will reference a Table 1 that may
            not be present.

        Example:
            # After loading, characteristics data will be available as:
            characteristics = collector.data['characteristics_table']
            print(f"Loaded characteristics for {len(characteristics)} studies")
            for study in characteristics:
                print(f"Study: {study['basic_info']['title']}")
        """
        file_path = self.workdir / "06_summary_characteristics.csv"

        if not file_path.exists():
            print(f"Warning: {file_path} not found")
            self.data['characteristics_table'] = []
            return

        try:
            processed_rows = []
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Create a processed version of the row
                    processed_row = self._process_characteristics_row(row)
                    processed_rows.append(processed_row)

            self.data['characteristics_table'] = processed_rows
        except csv.Error as e:
            print(f"Error: Invalid CSV in {file_path}: {str(e)}")
            self.data['characteristics_table'] = []
            return
        except IOError as e:
            print(f"Error: Cannot read {file_path}: {str(e)}")
            self.data['characteristics_table'] = []
            return

        print(f"  Characteristics table: {len(processed_rows)} studies")

    def _process_characteristics_row(self, row: Dict) -> Dict:
        """Process a single row from characteristics table.

        This method transforms a raw CSV row into a structured dictionary
        with organized fields and proper data types. It categorizes fields
        into logical groups and handles data type conversion for better
        usability in the article generation process.

        The method processes different types of fields:
        - Basic information: Title, year, clinical domain, sample size
        - Methodology: Study design, imaging modality, algorithm type
        - Performance metrics: Sensitivity, specificity, AUC, accuracy
        - Findings: Main findings, performance metrics, notes

        Args:
            row (Dict): Dictionary representing a single row from CSV.
                Contains raw field-value pairs from the characteristics
                table CSV file.

        Returns:
            Dict: Dictionary with processed and reorganized data containing:
                - study_id: Unique identifier for the study
                - basic_info: Dictionary with basic study information
                - methodology: Dictionary with study design and methodology details
                - performance: Dictionary with performance metrics
                - findings: Dictionary with key findings and notes
                - original_fields: Raw CSV data for reference

        Example:
            # Processing a characteristics row:
            processed = collector._process_characteristics_row(raw_row)
            print(f"Study: {processed['basic_info']['title']}")
            print(f"Sample size: {processed['basic_info']['sample_size']}")
        """
        processed = {
            'study_id': row.get('PMID', row.get('Title', 'Unknown')),
            'basic_info': {},
            'methodology': {},
            'performance': {},
            'findings': {},
            'original_fields': row  # Keep original for reference
        }

        # Process basic information fields
        basic_fields = {
            'Year': 'year',
            'Title': 'title',
            'Clinical Domain': 'clinical_domain',
            'Sample Size (N)': 'sample_size'
        }

        for csv_field, processed_field in basic_fields.items():
            value = row.get(csv_field, '').strip()
            if value and value != '':
                # Convert numeric fields
                if processed_field == 'year' or processed_field == 'sample_size':
                    try:
                        processed['basic_info'][processed_field] = int(value)
                    except ValueError:
                        processed['basic_info'][processed_field] = value
                else:
                    processed['basic_info'][processed_field] = value

        # Process methodology fields
        methodology_fields = {
            'Study Design': 'study_design',
            'Imaging Modality': 'imaging_modality',
            'algorithm_type': 'algorithm_type',
            'dataset_size': 'dataset_size'
        }

        for csv_field, processed_field in methodology_fields.items():
            value = row.get(csv_field, '').strip()
            if value and value != '':
                # Convert dataset_size to int if possible
                if processed_field == 'dataset_size':
                    try:
                        processed['methodology'][processed_field] = int(value)
                    except ValueError:
                        processed['methodology'][processed_field] = value
                else:
                    processed['methodology'][processed_field] = value

        # Process performance metrics
        performance_fields = {
            'Sensitivity': 'sensitivity',
            'Specificity': 'specificity',
            'AUC': 'auc',
            'Accuracy': 'accuracy'
        }

        for csv_field, processed_field in performance_fields.items():
            value = row.get(csv_field, '').strip()
            if value and value != '':
                try:
                    processed['performance'][processed_field] = float(value)
                except ValueError:
                    processed['performance'][processed_field] = value

        # Process findings and additional info
        processed['findings']['main_findings'] = row.get('Main Findings', '').strip()
        processed['findings']['performance_metrics'] = row.get('performance_metrics', '').strip()
        processed['findings']['notes'] = row.get('Notes', '').strip()

        return processed

    def _calculate_statistics(self) -> None:
        """Compute summary statistics from extracted data.

        This method analyzes the extracted study data to compute various
        summary statistics that are used throughout the systematic review
        article. These statistics provide quantitative insights into the
        characteristics and distribution of the included studies.

        The method calculates statistics for multiple dimensions including:
        - Temporal distribution: Publication year ranges and trends
        - Imaging modalities: Types of imaging techniques used
        - Clinical domains: Medical specialties and applications
        - Study designs: Methodological approaches and types
        - Sample sizes: Patient numbers and statistical distribution
        - Performance metrics: Diagnostic accuracy and effectiveness

        These statistics are used in the results section and to inform
        the thematic synthesis, providing quantitative context for the
        qualitative analysis.

        Populates:
            self.data['statistics'] (dict): Dictionary containing computed
                summary statistics with the following structure:
                - total_studies: Total number of included studies
                - year_range: Range of publication years (e.g., "2014-2024")
                - modalities: Dictionary of imaging modalities and counts
                - domains: Dictionary of clinical domains and counts
                - study_designs: Dictionary of study designs and counts
                - sample_sizes: Dictionary with median, range, and mean
                - performance_metrics: Statistics for sensitivity, specificity, AUC

        Note:
            If no extracted data is available, the statistics dictionary
            will be empty. The pipeline handles this gracefully in the
            article generation process.

        Example:
            # After calculation, statistics will be available as:
            stats = collector.data['statistics']
            print(f"Total studies: {stats['total_studies']}")
            print(f"Year range: {stats['year_range']}")
            print(f"Modalities: {stats['modalities']}")
        """
        extracted = self.data.get('extracted', [])

        if not extracted:
            self.data['statistics'] = {}
            return

        stats = {
            'total_studies': len(extracted),
            'year_range': self._get_year_range(extracted),
            'modalities': self._get_modalities(extracted),
            'domains': self._get_domains(extracted),
            'study_designs': self._get_study_designs(extracted),
            'sample_sizes': self._get_sample_size_stats(extracted),
            'performance_metrics': self._get_performance_metrics(extracted),
        }

        self.data['statistics'] = stats

        print(f"  Statistics: {stats['total_studies']} studies analyzed")

    def _get_year_range(self, data: List[Dict]) -> str:
        years = [int(d.get('year', 0)) for d in data if d.get('year')]
        if not years:
            return "Unknown"
        return f"{min(years)}-{max(years)}"

    def _get_modalities(self, data: List[Dict]) -> Dict[str, int]:
        modalities = {}
        for d in data:
            mods = d.get('imaging_modality', [])
            if isinstance(mods, list):
                for m in mods:
                    modalities[m] = modalities.get(m, 0) + 1
            elif isinstance(mods, str) and mods:
                modalities[mods] = modalities.get(mods, 0) + 1
        return dict(sorted(modalities.items(), key=lambda x: x[1], reverse=True))

    def _get_domains(self, data: List[Dict]) -> Dict[str, int]:
        domains = {}
        for d in data:
            domain = d.get('clinical_domain', 'Unknown')
            if domain:
                domains[domain] = domains.get(domain, 0) + 1
        return dict(sorted(domains.items(), key=lambda x: x[1], reverse=True))

    def _get_study_designs(self, data: List[Dict]) -> Dict[str, int]:
        designs = {}
        for d in data:
            design = d.get('study_design', 'Unknown')
            if design:
                designs[design] = designs.get(design, 0) + 1
        return dict(sorted(designs.items(), key=lambda x: x[1], reverse=True))

    def _get_sample_size_stats(self, data: List[Dict]) -> Dict:
        sizes = []
        for d in data:
            size_dict = d.get('sample_size', {})
            if isinstance(size_dict, dict):
                n = size_dict.get('total_patients')
                if n and isinstance(n, int):
                    sizes.append(n)

        if not sizes:
            return {'median': 'N/A', 'range': 'N/A', 'mean': 'N/A'}

        sizes.sort()
        return {
            'median': sizes[len(sizes)//2],
            'range': f"{min(sizes)}-{max(sizes)}",
            'mean': round(sum(sizes) / len(sizes), 0)
        }

    def _get_performance_metrics(self, data: List[Dict]) -> Dict:
        sensitivity = []
        specificity = []
        auc = []

        for d in data:
            metrics = d.get('key_metrics', {})
            if isinstance(metrics, dict):
                sens = metrics.get('sensitivity')
                spec = metrics.get('specificity')
                a = metrics.get('auc')

                if sens and isinstance(sens, (int, float)):
                    sensitivity.append(float(sens))
                if spec and isinstance(spec, (int, float)):
                    specificity.append(float(spec))
                if a and isinstance(a, (int, float)):
                    auc.append(float(a))

        return {
            'sensitivity': self._metric_stats(sensitivity),
            'specificity': self._metric_stats(specificity),
            'auc': self._metric_stats(auc),
        }

    def _metric_stats(self, values: List[float]) -> Dict:
        if not values:
            return {'median': 'N/A', 'range': 'N/A', 'count': 0}

        values.sort()
        return {
            'median': round(values[len(values)//2], 3),
            'range': f"{round(min(values), 3)}-{round(max(values), 3)}",
            'count': len(values),
            'mean': round(sum(values) / len(values), 3)
        }

    def generate_bibtex(self) -> str:
        """Generate BibTeX entries for all included studies.

        This method creates complete BibTeX entries for all studies included
        in the systematic review. It prioritizes metadata from the original
        parsed articles when available, falling back to extracted data for
        missing fields.

        The method creates unique citation keys using a consistent format
        that works with the plainnat bibliography style and numeric citations:
        1. Uses author-year format (e.g., smith2023)
        2. Adds numeric suffix for duplicate keys (e.g., smith2023_01, smith2023_02)

        The method handles various edge cases including missing metadata,
        special characters in fields, and different author name formats.
        All BibTeX fields are properly LaTeX-escaped for compilation compatibility.

        The BibTeX entries include all relevant bibliographic information:
        - Title with proper LaTeX escaping
        - Authors formatted for BibTeX
        - Journal name with escaping
        - Publication details (volume, issue, pages)
        - Digital identifiers (DOI, PMID, URL)
        - Proper entry type (@article)
        - Consistent citation format for use with plainnat style

        Returns:
            str: Complete BibTeX entries as a string, with each entry
                separated by double newlines. Each entry includes:
                - Proper @article{} entry type
                - Unique citation key in author-year format
                - Title, author, journal, year
                - Volume, issue, pages if available
                - DOI, PMID, URL if available
                - Proper LaTeX escaping for special characters

        Note:
            Studies with missing or invalid metadata are skipped with
            warnings, but the method continues processing remaining studies.
            The returned string may be empty if no valid studies are found.

        Example:
            # Generate BibTeX entries:
            bibtex = collector.generate_bibtex()
            with open('references.bib', 'w') as f:
                f.write(bibtex)
        """
        entries = []
        extracted = self.data.get('extracted', [])
        original_articles = {art['title']: art for art in self.data.get('original_articles', [])}

        # Track citation keys to handle duplicates
        citation_keys = {}

        for i, study in enumerate(extracted):
            try:
                # Get original article details for more complete metadata
                original = original_articles.get(study.get('title'), {})

                # Merge fields preferring original parse data when available
                authors = original.get('authors', study.get('authors', 'Unknown'))
                journal = original.get('journal', study.get('journal', 'Unknown Journal'))
                volume = original.get('volume', study.get('volume', ''))
                issue = original.get('issue', study.get('issue', ''))
                pages = original.get('pages', study.get('pages', ''))
                doi = original.get('doi', study.get('doi', ''))
                pmid = original.get('pmid', study.get('pmid', ''))
                url = original.get('url', study.get('url', ''))
                year = original.get('year', study.get('year', '0000'))

                # Create citation key in author-year format
                if isinstance(authors, list) and authors:
                    first_author_last = authors[0].split()[-1]
                else:
                    first_author_last = 'Unknown'

                # Clean author name for citation key
                first_author_last = re.sub(r'[^a-zA-Z]', '', first_author_last).lower()

                # Create base citation key
                base_key = f"{first_author_last}{year}"

                # Handle duplicate keys by adding numeric suffix
                if base_key in citation_keys:
                    citation_keys[base_key] += 1
                    citation_key = f"{base_key}_{citation_keys[base_key]:02d}"
                else:
                    citation_keys[base_key] = 1
                    citation_key = base_key

                # Format authors for BibTeX
                if isinstance(authors, list):
                    formatted_authors = " and ".join(authors)
                else:
                    formatted_authors = authors

                # LaTeX escaping for BibTeX fields (except DOI/PMID/URL which shouldn't need it)
                title = study.get('title', 'Untitled').replace('&', r'\\&').replace('$', r'\\$').replace('%', r'\\%').replace('#', r'\\#')
                journal_esc = journal.replace('&', r'\\&').replace('$', r'\\$').replace('%', r'\\%').replace('#', r'\\#')
                formatted_authors_esc = formatted_authors.replace('&', r'\\&').replace('$', r'\\$').replace('%', r'\\%').replace('#', r'\\#')

                entry = f"""@article{{{citation_key},
  title     = {{{title}}},
  author    = {{{formatted_authors_esc}}},
  journal   = {{{journal_esc}}},
  year      = {{{year}}},
  volume    = {{{volume}}},
  number    = {{{issue}}},
  pages     = {{{pages}}},
  doi       = {{{doi}}},  # No escaping needed
  pmid      = {{{pmid}}},  # No escaping needed
  url       = {{{url}}}   # No escaping needed
}}"""
                entries.append(entry)
            except Exception as e:
                print(f"Warning: Could not generate BibTeX entry for study {i}: {str(e)}")
                continue

        return "\n\n".join(entries)


class LaTeXArticleGenerator:
    """Generates systematic review article in LaTeX format using LLM API.

    This class orchestrates the complete process of generating a publication-ready
    LaTeX systematic review article by leveraging Large Language Model APIs. It
    constructs comprehensive prompts, handles API communication with retry logic,
    processes streaming responses, and manages the complete document generation.

    The class supports multiple LLM providers (Anthropic, OpenRouter, Together,
    Groq, local) with appropriate authentication and request formatting for each.
    It includes robust error handling, rate limiting, and streaming capabilities
    for generating large documents efficiently.

    The generator follows a systematic approach to article generation:
    1. Data collection and organization from DataCollector
    2. Prompt construction with structured requirements and formatting
    3. API communication with retry logic and error handling
    4. Response processing for both streaming and non-streaming modes
    5. File output and reference generation

    The class is designed to be flexible and robust, handling various edge cases
    and providing comprehensive debugging capabilities through prompt saving
    and detailed error reporting.

    Attributes:
        data (dict): Dictionary containing all collected review data from
                    DataCollector, including screening results,
                    extracted studies, quality assessments, synthesis,
                    and computed statistics
        provider (str): LLM provider name ('anthropic', 'openrouter', 'together',
                       'groq', 'local') - determines API endpoint and authentication
        base_url (str): Base URL for the LLM API provider
        endpoint (str): API endpoint path for chat completions
        full_url (str): Complete API URL for making requests
        model (str): LLM model name to use for generation
        api_key (str): API authentication key (None for local provider)
        api_configs (dict): Configuration dictionary with provider-specific
                           settings including base URLs, endpoints, and
                           default model names
        verbose (bool): Whether to print streaming response content
        debug (bool): Whether to enable debug mode for troubleshooting

    Example:
        generator = LaTeXArticleGenerator(data, provider='anthropic')
        article = generator.generate_article(stream=True)
    """

    def __init__(self, data: Dict, provider: str = 'anthropic',
                 model: Optional[str] = None, api_url: Optional[str] = None,
                 api_key: Optional[str] = None, verbose: bool = False, **kwargs):
        """Initialize generator with config and collected data.

        This constructor sets up the LaTeX article generator with all necessary
        configuration for communicating with the specified LLM provider and
        accessing the collected review data.

        The method configures API settings based on the provider, including
        authentication, endpoint URLs, and default models. It validates that
        required API keys are available for cloud providers and sets up
        appropriate fallbacks for local deployments.

        The generator supports multiple LLM providers with different authentication
        methods and API formats. It automatically configures the appropriate
        headers, request formats, and response parsing for each provider.

        Args:
            data (dict): Comprehensive dictionary containing all collected review
                        data from DataCollector, including screening
                        results, extracted studies, quality assessments,
                        thematic synthesis, and computed statistics
            provider (str, optional): LLM provider name. Defaults to 'anthropic'.
                Supported providers:
                - 'anthropic': Anthropic Claude models
                - 'openrouter': OpenRouter API with various models
                - 'together': Together AI API
                - 'groq': Groq API with fast inference
                - 'local': Local Ollama deployment
            model (str, optional): Specific model name to use. If not specified,
                uses the provider's default model from api_configs
            api_url (str, optional): Custom API URL to override the provider's
                default base URL. Useful for testing or private deployments
            api_key (str, optional): API authentication key. If not specified,
                attempts to load from environment variables based on provider.
                Required for all providers except 'local'
            verbose (bool, optional): Whether to print streaming response content
            debug (bool, optional): Whether to enable debug mode for troubleshooting

        Raises:
            ValueError: If provider is not recognized in api_configs, or if
                       required API key is not found in environment variables
                       for cloud providers (except local)

        Note:
            For local provider, no API key is required. The constructor will
            succeed even if api_key is None or environment variables are missing.

        Example:
            generator = LaTeXArticleGenerator(
                data,
                provider='anthropic',
                model='claude-3-opus-20240229',
                verbose=True
            )
        """
        self.data = data
        self.provider = provider.lower()
        self.verbose = verbose
        self.debug = kwargs.get('debug', False)

        # API configuration (same as in main pipeline)
        self.api_configs = {
            'anthropic': {
                'base_url': 'https://api.anthropic.com/v1',
                'endpoint': '/messages',
                'api_key_env': 'ANTHROPIC_API_KEY',
                'default_model': 'claude-opus-4-5-20251101',
            },
            'openrouter': {
                'base_url': 'https://openrouter.ai/api/v1',
                'endpoint': '/chat/completions',
                'api_key_env': 'OPENROUTER_API_KEY',
                'default_model': 'meta-llama/llama-2-70b-chat-hf',
            },
            'together': {
                'base_url': 'https://api.together.xyz/v1',
                'endpoint': '/chat/completions',
                'api_key_env': 'TOGETHER_API_KEY',
                'default_model': 'meta-llama/Llama-2-70b-chat-hf',
            },
            'groq': {
                'base_url': 'https://api.groq.com/openai/v1',
                'endpoint': '/chat/completions',
                'api_key_env': 'GROQ_API_KEY',
                'default_model': 'mixtral-8x7b-32768',
            },
            'local': {
                'base_url': 'http://localhost:11434/v1',
                'endpoint': '/chat/completions',
                'api_key_env': None,
                'default_model': 'llama2',
            }
        }

        if self.provider not in self.api_configs:
            raise ValueError(f"Unknown provider: {provider}")

        config = self.api_configs[self.provider]

        self.base_url = api_url or config['base_url']
        self.endpoint = config['endpoint']
        self.full_url = self.base_url.rstrip('/') + self.endpoint
        self.model = model or config['default_model']

        # Get API key
        if config['api_key_env']:
            self.api_key = api_key or os.getenv(config['api_key_env'])
            if not self.api_key and provider != 'local':
                raise ValueError(f"API key not found. Set {config['api_key_env']} environment variable")
        else:
            self.api_key = None

        print(f"Initialized {provider.upper()} API client")
        print(f"  Model: {self.model}")

    def call_llm(self, prompt: str, max_retries: int = 3, stream: bool = False, temperature: float = 0.8, output_file: Optional[Path] = None, verbose: bool = False) -> str:
        """Execute LLM API call with comprehensive retry logic.

        This method handles the complete API communication flow with the LLM
        provider, including request formatting, response processing, error
        handling, and retry logic. It supports both streaming and non-streaming
        modes, with optional file output for streaming responses.

        The method implements exponential backoff for rate limiting and server
        errors, with different wait times for different error types. It
        properly formats requests for both Anthropic and OpenAI-compatible
        APIs, handling authentication and response parsing appropriately.

        The method supports two operational modes:
        1. Non-streaming mode: Returns complete response at once
        2. Streaming mode: Processes chunks as they arrive, optionally writing to file

        Args:
            prompt (str): Complete prompt string containing all instructions
                         and data for generating the LaTeX article. This should
                         be a comprehensive prompt with structured requirements
            max_retries (int, optional): Maximum number of retry attempts for
                failed API calls. Defaults to 3. The method implements
                exponential backoff between retries
            stream (bool, optional): Whether to enable streaming response mode.
                Defaults to False. When True, processes response chunks as they
                arrive and optionally writes to file
            temperature (float, optional): Temperature parameter for LLM
                generation controlling randomness. Defaults to 0.8. Range is
                typically 0.0-2.0, where 0.0 is deterministic and higher
                values increase creativity
            output_file (Path, optional): File path to write streaming output
                to. If provided and streaming is enabled, chunks are written
                to this file as they're received. File is created with parent
                directories if needed
            verbose (bool, optional): Whether to print streaming response content
                to console. Defaults to False. When True and streaming is enabled,
                prints each chunk as it's received

        Returns:
            str: Generated text content from LLM. In streaming mode with
                output_file specified, returns empty string as content is
                written directly to file. In non-streaming mode, returns
                complete generated content

        Raises:
            ValueError: If API call fails after all retry attempts exhausted.
                This can happen due to:
                - Authentication failures (invalid API key)
                - Rate limiting (after all retries)
                - Server errors (after all retries)
                - Network connectivity issues (after all retries)
                - Invalid API responses

        Note:
            The method handles different error types with appropriate retry
            strategies:
            - Rate limiting (429): Waits 5s, 10s, 15s for successive retries
            - Server errors (5xx): Waits 2s, 4s, 6s for successive retries
            - Network errors: Waits 2s, 4s, 6s for successive retries
            - Other errors: Waits 2s between retries

        Example:
            # Non-streaming call:
            response = generator.call_llm(prompt, stream=False)

            # Streaming call with file output:
            response = generator.call_llm(prompt, stream=True, output_file=Path('output.tex'))
        """

        # Prepare request based on provider
        if self.provider == 'anthropic':
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': self.api_key,
                'anthropic-version': '2023-06-01'
            }
            body = {
                'model': self.model,
                'max_tokens': 20000,  # Increased for longer articles
                'temperature': temperature,
                'messages': [{'role': 'user', 'content': prompt}]
            }
            if stream:
                body['stream'] = True
                headers['Accept'] = 'text/event-stream'
        else:  # OpenAI-compatible
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}' if self.api_key else ''
            }
            body = {
                'model': self.model,
                'max_tokens': 20000,  # Increased for longer articles
                'temperature': temperature,
                'messages': [{'role': 'user', 'content': prompt}]
            }
            if stream:
                body['stream'] = True

        # Convert body to JSON bytes
        body_json = json.dumps(body).encode('utf-8')

        # Retry loop
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(
                    self.full_url,
                    data=body_json,
                    headers=headers,
                    method='POST'
                )

                if stream:
                    # Handle streaming response
                    response = urllib.request.urlopen(req, timeout=60)
                    full_response = ""

                    # Open output file if provided
                    file_handle = None
                    if output_file:
                        output_file.parent.mkdir(parents=True, exist_ok=True)
                        file_handle = open(output_file, 'w', encoding='utf-8')

                    try:
                        for line in response:
                            data_str = line.decode('utf-8').strip()
                            if data_str.startswith('data: '):
                                data_str = data_str[6:]
                                try:
                                    chunk_data = json.loads(data_str)
                                    if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                                        delta = chunk_data["choices"][0].get("delta", {})
                                        if "content" in delta:
                                            content = delta["content"]
                                            full_response += content

                                            # Write to file and optionally print
                                            if file_handle:
                                                file_handle.write(content)
                                                # Only flush if content contains a newline
                                                if '\n' in content:
                                                    file_handle.flush()
                                            if self.verbose:
                                                print(content, end="", flush=True)
                                except json.JSONDecodeError:
                                    # Skip invalid JSON lines
                                    pass
                    finally:
                        if file_handle:
                            file_handle.close()

                    return full_response
                else:
                    # Handle non-streaming response
                    with urllib.request.urlopen(req, timeout=60) as response:
                        response_data = json.loads(response.read().decode('utf-8'))

                        # Extract response based on provider
                        if self.provider == 'anthropic':
                            result = response_data.get('content', [{}])[0].get('text', '')
                        else:
                            result = response_data.get('choices', [{}])[0].get('message', {}).get('content', '')

                        if not result:
                            raise ValueError("Empty response from API")

                        return result

            except urllib.error.HTTPError as e:
                if e.code == 429:  # Rate limit
                    wait_time = 5 * (attempt + 1)
                    print(f"  Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                elif e.code in [500, 502, 503, 504]:  # Server error
                    wait_time = 2 * (attempt + 1)
                    print(f"  Server error ({e.code}). Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise ValueError(f"API error {e.code}")

            except urllib.error.URLError as e:
                if attempt < max_retries - 1:
                    wait_time = 2 * (attempt + 1)
                    print(f"  Connection error. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                raise ValueError(f"Connection error: {e.reason}")

            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  Error: {str(e)}. Retrying...")
                    time.sleep(2)
                    continue
                raise

        raise ValueError("Failed to get response after all retries")

    def generate_article(self, output_file: str, stream: bool = False, temperature: float = 0.8) -> str:
        """Generate complete LaTeX article from collected data.

        This method orchestrates the complete article generation process by
        first building a comprehensive prompt with all review data and
        formatting instructions, then making the LLM API call to generate
        the complete LaTeX document.

        The method handles both streaming and non-streaming modes, with
        appropriate file handling for streaming output. It includes debug
        features like saving the prompt to disk for troubleshooting and
        provides clear status messages during the generation process.

        The article generation follows a structured approach:
        1. Prompt construction with all data and formatting requirements
        2. API call to LLM with specified parameters
        3. Response processing for streaming or non-streaming mode
        4. File output and reference generation

        Args:
            stream (bool, optional): Whether to enable streaming response
                mode. Defaults to False. When True, content is written directly
                to '07_review.tex' as it's received. When False, complete
                content is returned as a string
            temperature (float, optional): Temperature parameter for LLM
                generation controlling randomness. Defaults to 0.8. Higher
                values increase creativity but may reduce consistency

        Returns:
            str: Complete LaTeX document source as string. In streaming mode,
                returns empty string as content is written directly to file.
                In non-streaming mode, returns the complete generated LaTeX
                document ready for writing to file

        Note:
            This method makes a single comprehensive LLM API call with a
            detailed prompt that includes:
            - Complete review data and statistics
            - Structured article requirements (abstract, introduction, methods, etc.)
            - LaTeX formatting instructions
            - Content quality guidelines
            - Specific data to include

            For streaming mode, the output file '07_review.tex' is created
            in the working directory and written incrementally. For debugging,
            the complete prompt is saved to 'debug/' directory with
            timestamp.

            The generation process may take several minutes for large articles
            or when using models with context limits.

        Example:
            # Generate article in non-streaming mode:
            article = generator.generate_article(stream=False)

            # Generate article in streaming mode:
            article = generator.generate_article(stream=True)
        """

        print("\nGenerating LaTeX article...")

        # Build comprehensive prompt with all data
        prompt = self.build_article_prompt()

        print(f"Prompt size for LLM call: {len(prompt) / 1024:.1f} KB")

        # Save prompt to filesystem for debugging
        if self.debug:
            debug_dir = Path(self.data['workdir']) / 'debug'
            debug_dir.mkdir(exist_ok=True)
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            prompt_file = debug_dir / f'prompt_{timestamp}.txt'
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(prompt)
            print(f"  Prompt saved to: {prompt_file}")

        if stream:
            print("Streaming response from LLM...")
            # Call LLM API to generate article content with streaming to file
            article_content = self.call_llm(prompt, stream=stream, temperature=temperature, output_file=output_file)
            # Response is empty when streaming to file
            return ""
        else:
            print("Making LLM call (this may take several minutes)...")
            # Call LLM API to generate article content
            article_content = self.call_llm(prompt, stream=stream, temperature=temperature)
            # Save the generated article to file
            try:
                # Save LaTeX article
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(article_content)
            except IOError as e:
                print(f"Error: Could not save output files: {str(e)}")
                raise
            # Response is expected to be the complete LaTeX document source
            return article_content

    def build_article_prompt(self) -> str:
        """Construct the complete LLM prompt with structured content requirements.

        This method creates a comprehensive prompt that provides the LLM with
        all necessary information to generate a publication-ready systematic
        review article. The prompt includes detailed instructions for structure,
        content, formatting, and quality requirements.

        The prompt is structured to guide the LLM through generating each
        section of the article with specific requirements for content,
        length, and academic rigor. It includes all collected data formatted
        appropriately and specific guidance for LaTeX formatting.

        The prompt construction process:
        1. Gathers all data components from the collected review data
        2. Formats each component for optimal readability and usefulness
        3. Loads the external prompt template
        4. Substitutes placeholders with actual data
        5. Returns the complete formatted prompt

        Returns:
            str: Comprehensive prompt string containing:
                - Role definition and task instructions
                - Data summary overview
                - Key study examples
                - High-impact studies
                - Pattern insights
                - Characteristics table in markdown format
                - Thematic synthesis
                - Article structure and content requirements
                - Quality and style guidelines
                - LaTeX formatting instructions

        Note:
            The prompt is designed to be comprehensive and provide clear
            guidance for generating a high-quality academic article. It
            includes specific word count targets, structural requirements,
            and formatting instructions to ensure consistency.

            The prompt size can be substantial (often 100KB+), so it's
            saved to disk for debugging purposes when generating articles.

        Example:
            prompt = generator.build_article_prompt()
            print(f"Prompt length: {len(prompt)} characters")
        """
        # Get plan data
        plan = self.data.get('plan', {})
        title = plan.get('title', 'Systematic Review')
        topic = plan.get('topic', 'the research topic')
        quality_tool = plan.get('quality', 'GRADE')

        # Get data summary
        data_summary = self.get_data_summary()

        # Get key study examples
        study_examples = self.get_key_study_examples()

        # Get high-impact studies
        high_impact_studies = self.get_high_impact_studies()

        # Get pattern insights
        pattern_insights = self.extract_patterns()

        # Format characteristics table as markdown
        characteristics_table = self.format_characteristics_as_markdown()

        # Get synthesis data
        synthesis_data = self.data.get('synthesis', '')

        # Format extract fields for quality requirements
        extract = plan.get('extract', {})
        if extract:
            extract_fields = '\n'.join([f'  - {field.replace("_", " ").title()}: {desc}' for field, desc in extract.items()])
        else:
            extract_fields = "No specific fields defined"

        # Extract analysis themes from the plan
        analysis = plan.get('analysis', [])
        if analysis:
            analysis_points = '\n'.join(f'  - {point}' for point in analysis)
        else:
            analysis_points = "No specific analysis points defined"

        # Use template with placeholders
        prompt_template = self._get_prompt_template()

        # Format the prompt with data
        prompt = prompt_template.format(
            title=title,
            topic=topic,
            data_summary=data_summary,
            study_examples=study_examples,
            high_impact_studies=high_impact_studies,
            pattern_insights=pattern_insights,
            characteristics_table=characteristics_table,
            synthesis_data=synthesis_data,
            extract_fields=extract_fields,
            analysis_points=analysis_points,
            quality_tool=quality_tool
        )

        # Return the fully formatted prompt
        return prompt

    def _get_prompt_template(self) -> str:
        """Load the prompt template from file.

        This method loads the external prompt template file containing the
        structured framework for article generation. The template uses
        placeholders that are substituted with actual data during prompt
        construction.

        The template file is located at 'prompts/latex_article_template.txt'
        relative to the script directory. This externalization allows for
        easy template updates without modifying the core code.

        Returns:
            str: Template string with placeholders for dynamic content

        Raises:
            FileNotFoundError: If the prompt template file cannot be found
            IOError: If the prompt template file cannot be read

        Example:
            template = generator._get_prompt_template()
            print(f"Template loaded: {len(template)} characters")
        """
        # Get the directory containing this script
        script_dir = Path(__file__).parent
        prompt_file = script_dir / 'prompts' / 'latex_article_template.txt'

        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Prompt template file not found: {prompt_file}")
        except IOError as e:
            raise IOError(f"Error reading prompt template file {prompt_file}: {str(e)}")

    def get_key_study_examples(self, max_examples: int = 5) -> str:
        """Get a few representative study examples for the prompt.

        This method selects a subset of studies to provide concrete examples
        for the LLM during article generation. The examples help the LLM
        understand the typical structure and content of the included studies.

        The method selects studies with the most words in 'main_findings' to
        provide the most informative examples. It includes:
        - Study title and year
        - Study design and methodology
        - Imaging modality and clinical domain
        - Sample size
        - Key findings (truncated if too long)
        - Performance metrics if available

        Args:
            max_examples (int, optional): Maximum number of examples to include.
                Defaults to 5. Controls the verbosity of the examples section.

        Returns:
            str: Formatted string with key study examples, ready for
                inclusion in the prompt template.

        Example:
            examples = generator.get_key_study_examples(max_examples=3)
            print(f"Generated examples for {len(examples)} studies")
        """
        extracted = self.data.get('extracted', [])
        if not extracted:
            return "No extracted data available"

        # Sort studies by word count in main_findings (descending)
        def get_finding_word_count(study):
            findings = study.get('main_findings', '')
            if findings and findings != 'N/A':
                return len(findings.split())
            return 0

        # Sort by word count and take top N examples
        sorted_examples = sorted(extracted, key=get_finding_word_count, reverse=True)
        examples = sorted_examples[:max_examples]

        # Format the examples for the prompt
        lines = []
        for i, study in enumerate(examples, 1):
            title = study.get('title', None)
            if not title or title == 'N/A':
                continue
            lines.append(f"Study: {title}")
            lines.append(f"Year: {study.get('year', 'N/A')}")
            lines.append(f"Design: {study.get('study_design', 'N/A')}")
            modalities = study.get('imaging_modality', 'N/A')
            if isinstance(modalities, list):
                modalities = ', '.join(modalities)
            lines.append(f"Modality: {modalities}")
            lines.append(f"Domain: {study.get('clinical_domain', 'N/A')}")
            lines.append(f"Main findings: {study.get('main_findings', 'N/A')}")
            lines.append(f"Clinical implications: {study.get('clinical_implications', 'N/A')}")

            # Sample size
            sample_size = study.get('sample_size', {})
            if isinstance(sample_size, dict):
                total = sample_size.get('total_patients', None)
                if total:
                    lines.append(f"Sample: {total} patients")
            else:
                lines.append(f"Sample: {sample_size}")

            # Performance metrics if available
            metrics = study.get('key_metrics', {})
            if isinstance(metrics, dict):
                sens = metrics.get('sensitivity')
                spec = metrics.get('specificity')
                auc = metrics.get('auc')
                if sens or spec or auc:
                    lines.append("Performance:")
                    if sens:
                        lines.append(f"  - Sensitivity: {sens}")
                    if spec:
                        lines.append(f"  - Specificity: {spec}")
                    if auc:
                        lines.append(f"  - AUC: {auc}")

            # Add spacing between examples
            lines.append("")

        # Return formatted examples section
        return "\n".join(lines)

    def get_high_impact_studies(self) -> str:
        """Get studies with exceptional results or novel approaches.

        This method identifies studies that demonstrate exceptional performance
        metrics or introduce novel approaches. These studies are highlighted
        in the article's discussion and conclusions sections.

        The method identifies high-impact studies based on:
        - Exceptional performance metrics (sensitivity > 0.95, specificity > 0.95, AUC > 0.95)
        - Both sensitivity and specificity > 0.90
        - Novel approaches detected through keyword analysis in key findings

        For each identified study, the method formats:
        - Study title and year
        - Study design
        - Performance metrics (if applicable)
        - Novel approach indicators (if applicable)

        Returns:
            str: Formatted string with high-impact studies, ready for
                inclusion in the prompt template.

        Example:
            high_impact = generator.get_high_impact_studies()
            print(f"Found {len(high_impact.split('Study:')) - 1} high-impact studies")
        """
        extracted = self.data.get('extracted', [])
        if not extracted:
            return "No extracted data available"

        # Filter for studies with exceptional metrics or novel approaches
        high_impact = []

        for study in extracted:
            metrics = study.get('key_metrics', {})
            if isinstance(metrics, dict):
                # Check for exceptional performance with null checks and type conversion
                sensitivity = metrics.get('sensitivity')
                specificity = metrics.get('specificity')
                auc = metrics.get('auc')

                # Convert to float if they're strings
                try:
                    if isinstance(sensitivity, str):
                        sensitivity = float(sensitivity)
                    if isinstance(specificity, str):
                        specificity = float(specificity)
                    if isinstance(auc, str):
                        auc = float(auc)
                except (ValueError, TypeError):
                    # If conversion fails, treat as None
                    sensitivity = None
                    specificity = None
                    auc = None

                # Consider study high impact if any metric is exceptional
                is_high_impact = False
                if sensitivity is not None and (sensitivity > 0.95 or sensitivity > 0.90):
                    is_high_impact = True
                if specificity is not None and (specificity > 0.95 or specificity > 0.90):
                    is_high_impact = True
                if auc is not None and auc > 0.95:
                    is_high_impact = True
                if sensitivity is not None and specificity is not None and sensitivity > 0.90 and specificity > 0.90:
                    is_high_impact = True

                # Add to high impact list if criteria met
                if is_high_impact:
                    high_impact.append((study, metrics))

        # Also check for novel approaches based on key findings
        for study in extracted:
            findings = study.get('main_findings', '')
            if findings and 'novel' in findings.lower() and 'first' in findings.lower():
                # Check if already included
                already_included = any(s[0]['title'] == study['title'] for s in high_impact)
                if not already_included:
                    high_impact.append((study, {'novel_approach': True}))

        if not high_impact:
            return "No studies with exceptional performance metrics or novel approaches found"

        # Format the high-impact studies section
        lines = []
        for study, metrics in high_impact[:3]:  # Top 3
            title = study.get('title', None)
            if not title or title == 'N/A':
                continue
            lines.append(f"Study: {title}")
            lines.append(f"Year: {study.get('year', 'N/A')}")
            lines.append(f"Design: {study.get('study_design', 'N/A')}")
            # Highlight novel approaches or exceptional metrics
            if isinstance(metrics, dict) and 'novel_approach' in metrics:
                lines.append(f"Innovation: Novel approach detected")
                lines.append(f"Main finding: {study.get('main_findings', 'N/A')}")
            else:
                lines.append("Performance:")
                sensitivity = metrics.get('sensitivity', None)
                specificity = metrics.get('specificity', None)
                auc = metrics.get('auc', None)
                if sensitivity is not None and sensitivity != 'N/A':
                    lines.append(f"  - Sensitivity: {sensitivity}")
                if specificity is not None and specificity != 'N/A':
                    lines.append(f"  - Specificity: {specificity}")
                if auc is not None and auc != 'N/A':
                    lines.append(f"  - AUC: {auc}")

            # Add spacing between studies
            lines.append("")

        # Return formatted high-impact studies section
        return "\n".join(lines)

    def extract_patterns(self) -> str:
        """Extract key patterns from extracted data for prompt inclusion.

        This method analyzes the extracted study data to identify patterns
        and trends that can inform the article's thematic synthesis and
        discussion sections. The patterns provide quantitative context
        for the qualitative analysis.

        The method identifies two types of patterns:
        1. Key findings patterns: Common words and phrases across studies
        2. Methodology insights: Distribution of study designs, modalities, and domains

        For key findings patterns, the method uses simple word frequency
        analysis to identify terms that appear across multiple studies.
        For methodology insights, it categorizes and counts studies by
        their design characteristics.

        Returns:
            str: Formatted string with key patterns and insights, ready for
                inclusion in the prompt template.

        Example:
            patterns = generator.extract_patterns()
            print(f"Identified patterns across {len(patterns.split('STUDY DESIGNS:'))} categories")
        """
        extracted = self.data.get('extracted', [])
        if not extracted:
            return "No extracted data available"

        patterns = []

        # Extract key findings patterns
        all_findings = []
        for study in extracted:
            findings = study.get('main_findings', '')
            if findings and findings != 'N/A':
                all_findings.append(findings.lower())

        if all_findings:
            patterns.append("KEY FINDINGS PATTERNS:")
            # Simple pattern detection - look for common n-grams
            from collections import Counter
            ngram_counts = Counter()

            # Common English stop words
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
                'before', 'after', 'above', 'below', 'between', 'among', 'this', 'that',
                'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me',
                'him', 'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their',
                'mine', 'yours', 'hers', 'ours', 'theirs', 'am', 'is', 'are', 'was',
                'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
                'will', 'would', 'shall', 'should', 'can', 'could', 'may', 'might', 'must',
                'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both',
                'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
                'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't',
                'can', 'will', 'just', 'don', 'should', 'now', 'within'
            }

            for finding in all_findings:
                words = finding.split()
                # Remove stop words
                filtered_words = [word for word in words if word.lower() not in stop_words]
                # Generate n-grams of different lengths
                for n in [3, 4, 5]:
                    for i in range(len(filtered_words) - n + 1):
                        ngram = ' '.join(filtered_words[i:i+n])
                        ngram_counts[ngram] += 1

            # Get most common patterns
            common_patterns = ngram_counts.most_common(10)
            for ngram, count in common_patterns:
                if count >= 2:  # Only show patterns that appear in multiple studies
                    patterns.append(f"  - '{ngram}' appears in {count} studies")
            patterns.append("")

        # Extract methodology insights
        modalities = {}
        domains = {}

        for study in extracted:
            # Use the improved characteristics data structure
            basic_info = study.get('basic_info', {})
            methodology = study.get('methodology', {})

            modality = methodology.get('imaging_modality', basic_info.get('imaging_modality', study.get('imaging_modality', 'Unknown')))
            if isinstance(modality, list):
                for m in modality:
                    m = m.lower()
                    modalities[m] = modalities.get(m, 0) + 1
            elif modality:
                modality = modality.lower()
                modalities[modality] = modalities.get(modality, 0) + 1

            domain = basic_info.get('clinical_domain', study.get('clinical_domain', 'Unknown')).lower()
            domains[domain] = domains.get(domain, 0) + 1

        patterns.append("IMAGING MODALITIES:")
        for mod, count in sorted(modalities.items(), key=lambda x: x[1], reverse=True):
            if mod != 'unknown' and count > 1:
                patterns.append(f"  - {mod}: {count} studies")
        patterns.append("")

        patterns.append("CLINICAL DOMAINS:")
        for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True):
            if domain != 'unknown' and count > 1:
                patterns.append(f"  - {domain}: {count} studies")
        patterns.append("")

        return "\n".join(patterns)

    def format_characteristics_as_markdown(self) -> str:
        """Format characteristics table as markdown table for prompt inclusion.

        This method presents the characteristics table data in a markdown format
        that's easy for the LLM to read and understand. It reads the raw CSV
        data and converts it to a properly formatted markdown table.

        The method reads the CSV file directly and formats it as a markdown table
        with proper alignment and formatting. This provides the LLM with the
        complete tabular data in a structured format.

        Returns:
            str: Markdown formatted table string with:
                - Column headers properly formatted
                - Row data aligned in columns
                - Proper markdown table syntax

        Example:
            markdown_table = generator.format_characteristics_as_markdown()
            print(f"Markdown table with {len(markdown_table.splitlines())} lines")
        """
        # Get the workdir from data
        workdir = self.data.get('workdir', '')
        if not workdir:
            return "No workdir available"

        # Path to the characteristics CSV file
        csv_file = Path(workdir) / '06_summary_characteristics.csv'

        if not csv_file.exists():
            return "No characteristics table found"

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                # Read CSV data
                reader = csv.DictReader(f)
                rows = list(reader)

                if not rows:
                    return "No data in characteristics table"

                # Get headers
                headers = reader.fieldnames or []

                # Create markdown table
                lines = []

                # Add table header
                lines.append("| " + " | ".join(headers) + " |")
                lines.append("|" + "|".join(["---"] * len(headers)) + "|")

                # Add rows
                for row in rows:
                    # Escape pipe characters and handle None values
                    row_values = []
                    for header in headers:
                        value = row.get(header, '')
                        if value is None:
                            value = ''
                        # Escape pipe characters in cell content
                        value = str(value).replace('|', '\\|')
                        row_values.append(value)
                    lines.append("| " + " | ".join(row_values) + " |")

                return "\n".join(lines)

        except (csv.Error, IOError) as e:
            print(f"Error reading characteristics CSV: {str(e)}")
            return f"Error reading characteristics table: {str(e)}"

    def get_sample_size_range(self, characteristics: List[Dict]) -> str:
        """Get the range of sample sizes from characteristics data.

        This method extracts and calculates the range of sample sizes from
        the characteristics table data. It handles various data formats
        and provides a clean range string for reporting.

        Args:
            characteristics (List[Dict]): List of study characteristics
                dictionaries from the processed characteristics table.

        Returns:
            str: String representing the sample size range in format
                "min-max", or "N/A" if no valid sample sizes are found.

        Example:
            range_str = generator.get_sample_size_range(characteristics)
            print(f"Sample size range: {range_str}")
        """
        sizes = []
        for study in characteristics:
            basic_info = study.get('basic_info', {})
            sample_size = basic_info.get('sample_size')
            if sample_size and isinstance(sample_size, int):
                sizes.append(sample_size)

        if not sizes:
            return "N/A"

        sizes.sort()
        return f"{sizes[0]}-{sizes[-1]}"

    def get_data_summary(self) -> str:
        """Create human-readable summary of collected data for inclusion in prompt.

        This method formats the collected review data into a human-readable
        summary organized by category. It presents key statistics and data
        points in a clear, structured format that's easy for the LLM to
        process and reference during article generation.

        The summary includes screening results, study statistics, quality
        assessment data, and key insights from the data. The formatting
        is designed to be both informative and concise, providing the
        LLM with the essential information needed for article generation.

        The method organizes data into logical sections:
        - Screening results: PRISMA flow statistics
        - Study statistics: Demographic and methodological overview
        - Sample sizes: Patient number statistics
        - Performance metrics: Diagnostic accuracy summaries
        - Quality assessment: Risk of bias distribution

        Returns:
            str: Formatted string containing organized data summary with
                sections for:
                - Screening results with PRISMA flow numbers
                - Study statistics including modalities, domains, designs
                - Sample size statistics
                - Performance metrics
                - Quality assessment summary
                - Key insights from characteristics table

        Note:
            This method is designed to provide the LLM with a clear overview
            of the collected data without overwhelming it with raw JSON data.
            The summary highlights key patterns and statistics that are most
            relevant for article generation.

        Example:
            data_summary = generator.get_data_summary()
            print(f"Data summary length: {len(data_summary)} characters")
        """
        lines = []

        # Screening data
        screening = self.data.get('screening', {})
        lines.append("SCREENING RESULTS:")
        lines.append(f"  - Total articles identified: {screening.get('total_identified', 0)}")
        lines.append(f"  - Articles screened: {screening.get('total_screened', 0)}")
        lines.append(f"  - Articles excluded (screening): {screening.get('excluded', 0)}")
        lines.append(f"  - Articles marked uncertain: {screening.get('uncertain', 0)}")
        lines.append(f"  - Full-text assessed: {screening.get('full_text_assessed', 0)}")
        lines.append(f"  - Full-text excluded: {screening.get('full_text_excluded', 0)}")
        lines.append(f"  - Final studies included: {screening.get('final_included', 0)}")
        lines.append("")

        # Statistics
        stats = self.data.get('statistics', {})
        lines.append("STUDY STATISTICS:")
        lines.append(f"  - Total studies: {stats.get('total_studies', 0)}")
        lines.append(f"  - Year range: {stats.get('year_range', 'N/A')}")
        lines.append("")

        lines.append("STUDY DESIGNS:")
        for design, count in stats.get('study_designs', {}).items():
            lines.append(f"  - {design}: {count}")
        lines.append("")

        # Sample sizes
        sample_stats = stats.get('sample_sizes', {})
        if sample_stats:
            lines.append("SAMPLE SIZES:")
            lines.append(f"  - Median: {sample_stats.get('median', 'N/A')}")
            lines.append(f"  - Range: {sample_stats.get('range', 'N/A')}")
            lines.append("")

        # Performance metrics
        perf = stats.get('performance_metrics', {})
        if perf:
            lines.append("PERFORMANCE METRICS:")
            if perf.get('sensitivity'):
                lines.append(f"  - Sensitivity: {perf['sensitivity']}")
            if perf.get('specificity'):
                lines.append(f"  - Specificity: {perf['specificity']}")
            if perf.get('auc'):
                lines.append(f"  - AUC: {perf['auc']}")
            lines.append("")

        # Quality assessment
        quality = self.data.get('quality', [])
        if quality:
            lines.append("QUALITY ASSESSMENT SUMMARY:")
            low_risk = sum(1 for q in quality if q.get('overall_bias') == 'Low')
            mod_risk = sum(1 for q in quality if q.get('overall_bias') == 'Moderate')
            high_risk = sum(1 for q in quality if q.get('overall_bias') == 'High')
            lines.append(f"  - Low risk: {low_risk} ({100*low_risk//len(quality)}%)")
            lines.append(f"  - Moderate risk: {mod_risk} ({100*mod_risk//len(quality)}%)")
            lines.append(f"  - High risk: {high_risk} ({100*high_risk//len(quality)}%)")
            lines.append("")

        return "\n".join(lines)


def generate_article_main(workdir: str, provider: str = 'openrouter',
                         model: Optional[str] = None, api_url: Optional[str] = None,
                         api_key: Optional[str] = None, stream: bool = False,
                         temperature: float = 0.8, verbose: bool = False, debug: bool = False) -> Path:
    """Main entry point for article generation.

    This function orchestrates the complete LaTeX article generation process,
    from data collection through final file output. It serves as the primary
    interface for generating systematic review articles from pipeline outputs.

    The function coordinates between the DataCollector for gathering
    and organizing data, and the LaTeXArticleGenerator for creating the
    actual document. It handles both streaming and non-streaming modes,
    with appropriate file management and error handling.

    The article generation process follows these steps:
    1. Data collection from pipeline outputs
    2. Article generation using LLM API
    3. File output and reference generation
    4. Success reporting and compilation instructions

    Args:
        workdir (str): Path to directory containing pipeline output files.
            This directory should contain all generated files from the
            systematic review pipeline, including:
            - 00_plan.json: Study protocol information
            - 01_parsed_articles.json: Original parsed articles
            - 02_screening_results.json: Screening statistics
            - 03_extracted_data.json: Extracted study data
            - 04_quality_assessment.json: Quality assessment results
            - 05_thematic_synthesis.txt: Thematic synthesis text
            - 06_summary_characteristics.csv: Study characteristics
        provider (str, optional): LLM provider name. Defaults to 'openrouter'.
            Supported providers: 'anthropic', 'openrouter', 'together',
            'groq', 'local'. Determines API endpoint and authentication
        model (str, optional): Specific model name to use. If not specified,
            uses the provider's default model
        api_url (str, optional): Custom API URL to override provider's default
        api_key (str, optional): API authentication key. If not specified,
            attempts to load from environment variables
        stream (bool, optional): Whether to enable streaming response mode.
            Defaults to False. When True, writes content incrementally to file
        temperature (float, optional): LLM temperature parameter controlling
            randomness. Defaults to 0.8. Range typically 0.0-2.0
        verbose (bool, optional): Whether to print streaming response content
            to console. Defaults to False
        debug (bool, optional): Whether to enable debug mode for troubleshooting

    Returns:
        Path: Path object pointing to the generated LaTeX file
            ('07_review.tex' in the workdir). Also generates 'references.bib'
            in the same directory

    Raises:
        ValueError: If data collection fails or API errors occur during
            article generation. This can happen due to:
            - Missing or invalid pipeline output files
            - API authentication failures
            - API rate limiting or server errors
            - Network connectivity issues
            - File I/O errors when saving outputs

    Note:
        The function handles both streaming and non-streaming modes differently:
        - Streaming mode: Content written incrementally to '07_review.tex'
          during API calls, with BibTeX references written separately
        - Non-streaming mode: Complete content generated then written to file

        After successful generation, prints compilation instructions for
        XeLaTeX and bibtex to create the final PDF document.

    Example:
        # Basic usage
        output_path = generate_article_main('/path/to/workdir')

        # With custom provider and streaming
        output_path = generate_article_main(
            '/path/to/workdir',
            provider='anthropic',
            stream=True,
            verbose=True
        )
    """

    workdir = Path(workdir)

    # Collect data
    collector = DataCollector(str(workdir))
    data = collector.collect_all_data()

    # Generate article
    generator = LaTeXArticleGenerator(
        data,
        provider=provider,
        model=model,
        api_url=api_url,
        api_key=api_key,
        verbose=verbose,
        debug=debug
    )

    # Determine output file path
    output_file = workdir / '07_review.tex'

    # Save BibTeX references
    bib_file = workdir / 'references.bib'
    bib_content = collector.generate_bibtex()
    with open(bib_file, 'w', encoding='utf-8') as f:
        f.write(bib_content)

    # Generate article
    article_content = generator.generate_article(output_file=output_file, stream=stream, temperature=temperature)

    # Print success message
    print(f"\nArticle generated successfully!")
    print(f"  Saved to: {output_file}")
    print(f"  References saved to: {bib_file}")
    if not stream:
        print(f"  Total size: {len(article_content) + len(bib_content)} bytes")

    # Try to compile
    print("\nNote: To compile the XeLaTeX document with references:")
    print(f"  bibtex {output_file.stem}")
    print(f"  xelatex {output_file.name}")

    # Return the output file path
    return output_file


# Command line interface
if __name__ == '__main__':
    """Command line interface for LaTeX article generator.

    This script provides a command-line interface for generating systematic
    review articles from pipeline outputs. It supports multiple LLM providers,
    streaming mode, and various configuration options.

    The command line interface offers a comprehensive set of options for
    customizing the article generation process, including provider selection,
    model configuration, output modes, and debugging capabilities.

    Usage examples:
        python generate_latex_article.py /path/to/workdir
        python generate_latex_article.py /path/to/workdir --provider anthropic
        python generate_latex_article.py /path/to/workdir --stream --verbose
        python generate_latex_article.py /path/to/workdir --model claude-3-opus-20240229
        python generate_latex_article.py /path/to/workdir --debug

    The script handles argument parsing, validates inputs, and calls the
    main article generation function with appropriate parameters. It includes
    comprehensive error handling and user-friendly error messages.

    Command line options:
        -p, --provider: LLM provider (anthropic, openrouter, together, groq, local)
        -m, --model: Specific model name
        -u, --api-url: Custom API URL
        -k, --api-key: API key
        -s, --stream: Enable streaming mode
        -t, --temperature: LLM temperature (0.0-2.0)
        -v, --verbose: Print streaming response content
        -d, --debug: Enable debug mode
        -h, --help: Show help message

    The script includes comprehensive error handling and provides clear
    error messages for common issues such as missing files, API errors,
    and invalid inputs.
    """
    parser = argparse.ArgumentParser(
        description='Generate LaTeX systematic review article from pipeline outputs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/workdir
  %(prog)s /path/to/workdir --provider anthropic
  %(prog)s /path/to/workdir --stream --verbose
  %(prog)s /path/to/workdir --model claude-3-opus-20240229 --temperature 0.7
        """
    )
    parser.add_argument('workdir', help='Directory with pipeline outputs')
    parser.add_argument('-p', '--provider', choices=['anthropic', 'openrouter', 'together', 'groq', 'local'],
                       default='openrouter', help='LLM provider')
    parser.add_argument('-m', '--model', help='Model name (uses provider default if not specified)')
    parser.add_argument('-u', '--api-url', help='Custom API URL')
    parser.add_argument('-k', '--api-key', help='API key (uses env var if not specified)')
    parser.add_argument('-s', '--stream', action='store_true', help='Enable streaming response')
    parser.add_argument('-t', '--temperature', type=float, default=0.8, help='LLM temperature (default: 0.8)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Print response content in streaming mode')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()

    try:
        generate_article_main(
            args.workdir,
            provider=args.provider,
            model=args.model,
            api_url=args.api_url,
            api_key=args.api_key,
            stream=args.stream,
            temperature=args.temperature,
            verbose=args.verbose,
            debug=args.debug
        )
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
