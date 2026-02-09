#!/usr/bin/env python3
"""
PRISMA 2020 Flow Diagram Generator

Creates publication-ready PRISMA flow diagrams from screening results.
Generates SVG, PNG, and PowerPoint formats.

Supports:
- PRISMA 2020 (recommended)
- PRISMA 2009 (legacy)

Usage:
    python prisma_flow_diagram.py screening_results.json
    python prisma_flow_diagram.py screening_results.json --format png
    python prisma_flow_diagram.py screening_results.json --format all

Project: SystematicReviewAssistant
Author: Costin Stroie <costinstroie@eridu.eu.org>
GitHub: https://github.com/cstroie/SystematicReviewAssistant
Year: 2026
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class DiagramNumbers:
    """PRISMA flow diagram data"""
    # Identification phase
    records_identified: int
    
    # Screening phase
    records_screened: int
    records_excluded: int
    
    # Eligibility phase
    full_text_retrieved: int
    full_text_excluded: int
    # Inclusion phase
    studies_included_qualitative: int
    
    # Fields with default values must come after non-default fields
    full_text_exclude_reasons: Dict[str, int] = None
    studies_included_quantitative: int = None
    
    # Optional
    database_count: int = 1
    register_count: int = 0
    other_sources_count: int = 0
    duplicates_removed: int = 0


class PRISMADiagramSVG:
    """Generate PRISMA 2020 flow diagram as SVG"""
    
    # SVG dimensions and styling
    WIDTH = 800
    HEIGHT = 1200
    MARGIN = 40
    BOX_WIDTH = 400
    BOX_HEIGHT = 80
    COLORS = {
        'identification': '#E8F4F8',
        'screening': '#D4E8F0',
        'eligibility': '#C0DCE8',
        'inclusion': '#ACE0E0',
        'border': '#2C3E50',
        'text': '#1A1A1A',
        'arrow': '#34495E'
    }
    
    def __init__(self, numbers: DiagramNumbers):
        self.numbers = numbers
        self.svg_elements = []
        
    def generate(self) -> str:
        """Generate complete SVG diagram"""
        self.svg_elements = []
        self._add_svg_header()
        self._draw_identification_phase()
        self._draw_screening_phase()
        self._draw_eligibility_phase()
        self._draw_inclusion_phase()
        self._add_svg_footer()
        
        return ''.join(self.svg_elements)
    
    def _add_svg_header(self):
        """Add SVG document header"""
        self.svg_elements.append(f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{self.WIDTH}" height="{self.HEIGHT}" xmlns="http://www.w3.org/2000/svg">
  <style>
    .phase-title {{ font-size: 14px; font-weight: bold; fill: {self.COLORS['text']}; }}
    .box-title {{ font-size: 13px; font-weight: bold; fill: {self.COLORS['text']}; }}
    .box-number {{ font-size: 16px; font-weight: bold; fill: {self.COLORS['text']}; }}
    .box-label {{ font-size: 11px; fill: {self.COLORS['text']}; }}
    .arrow {{ stroke: {self.COLORS['arrow']}; stroke-width: 2; fill: none; }}
    .arrow-head {{ fill: {self.COLORS['arrow']}; }}
  </style>
''')
    
    def _add_svg_footer(self):
        """Close SVG document"""
        self.svg_elements.append('</svg>')
    
    def _draw_box(self, x: int, y: int, title: str, number: int, 
                  subtitle: str = None, color: str = '#FFFFFF') -> int:
        """Draw a single box with text
        
        Returns: y position after box
        """
        # Box background
        self.svg_elements.append(f'''
  <rect x="{x}" y="{y}" width="{self.BOX_WIDTH}" height="{self.BOX_HEIGHT}" 
        fill="{color}" stroke="{self.COLORS['border']}" stroke-width="2" rx="4"/>
''')
        
        # Main title
        self.svg_elements.append(f'''
  <text x="{x + 20}" y="{y + 25}" class="box-title">{title}</text>
  <text x="{x + 20}" y="{y + 50}" class="box-number">n = {number}</text>
''')
        
        # Subtitle if provided
        if subtitle:
            self.svg_elements.append(f'''
  <text x="{x + 20}" y="{y + 70}" class="box-label">{subtitle}</text>
''')
        
        return y + self.BOX_HEIGHT + 30
    
    def _draw_arrow(self, x1: int, y1: int, x2: int, y2: int, label: str = None):
        """Draw arrow between boxes"""
        # Arrow line
        self.svg_elements.append(f'''
  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="arrow"/>
  <polygon points="{x2},{y2} {x2-5},{y2-10} {x2+5},{y2-10}" class="arrow-head"/>
''')
        
        # Label if provided
        if label:
            mid_x = (x1 + x2) // 2 + 20
            mid_y = (y1 + y2) // 2
            self.svg_elements.append(f'''
  <text x="{mid_x}" y="{mid_y}" class="box-label">{label}</text>
''')
    
    def _draw_identification_phase(self):
        """Draw identification phase (top of diagram)"""
        x = self.MARGIN
        y = 20
        
        # Phase title
        self.svg_elements.append(f'''
  <text x="{x}" y="{y}" class="phase-title">IDENTIFICATION</text>
''')
        
        y = 50
        
        # Records identified
        sources = []
        if self.numbers.database_count > 0:
            sources.append(f"PubMed (n = {self.numbers.records_identified})")
        if self.numbers.register_count > 0:
            sources.append(f"Trial registers (n = {self.numbers.register_count})")
        if self.numbers.other_sources_count > 0:
            sources.append(f"Other sources (n = {self.numbers.other_sources_count})")
        
        subtitle = ", ".join(sources) if sources else ""
        y = self._draw_box(x, y, "Records identified", 
                          self.numbers.records_identified, subtitle, 
                          self.COLORS['identification'])
        
        # Arrow to screening
        self._draw_arrow(x + self.BOX_WIDTH // 2, y - 30, 
                        x + self.BOX_WIDTH // 2, y, "")
        
        return y
    
    def _draw_screening_phase(self):
        """Draw screening phase"""
        x = self.MARGIN
        y = self._draw_identification_phase() + 20
        
        # Phase title
        self.svg_elements.append(f'''
  <text x="{x}" y="{y}" class="phase-title">SCREENING</text>
''')
        
        y += 30
        
        # Records screened
        y = self._draw_box(x, y, "Records screened", 
                          self.numbers.records_screened,
                          "", self.COLORS['screening'])
        
        # Records excluded (side by side)
        exclude_x = x + self.BOX_WIDTH + 100
        exclude_y = y - self.BOX_HEIGHT - 30
        
        self.svg_elements.append(f'''
  <text x="{exclude_x}" y="{exclude_y - 10}" class="phase-title">EXCLUSIONS</text>
''')
        
        exclude_y = self._draw_box(exclude_x, exclude_y, "Records excluded",
                                  self.numbers.records_excluded,
                                  "", self.COLORS['screening'])
        
        # Arrow from screened to excluded
        self._draw_arrow(x + self.BOX_WIDTH, y - self.BOX_HEIGHT - 30,
                        exclude_x, exclude_y - self.BOX_HEIGHT - 30)
        
        # Arrow down to eligibility
        self._draw_arrow(x + self.BOX_WIDTH // 2, y,
                        x + self.BOX_WIDTH // 2, y + 20)
        
        return y
    
    def _draw_eligibility_phase(self):
        """Draw eligibility phase (full-text review)"""
        x = self.MARGIN
        y = self._draw_screening_phase() + 20
        
        # Phase title
        self.svg_elements.append(f'''
  <text x="{x}" y="{y}" class="phase-title">ELIGIBILITY</text>
''')
        
        y += 30
        
        # Full-text articles retrieved
        y = self._draw_box(x, y, "Full-text articles assessed",
                          self.numbers.full_text_retrieved,
                          "", self.COLORS['eligibility'])
        
        # Excluded with reasons (side)
        exclude_x = x + self.BOX_WIDTH + 100
        exclude_y = y - self.BOX_HEIGHT - 30
        
        self.svg_elements.append(f'''
  <text x="{exclude_x}" y="{exclude_y - 10}" class="phase-title">EXCLUSIONS</text>
''')
        
        exclude_reasons = ""
        if self.numbers.full_text_exclude_reasons:
            reasons_list = []
            for reason, count in self.numbers.full_text_exclude_reasons.items():
                reasons_list.append(f"{reason} (n={count})")
            exclude_reasons = "; ".join(reasons_list[:3])  # Max 3 reasons shown
        
        exclude_y = self._draw_box(exclude_x, exclude_y, "Full-text articles excluded",
                                  self.numbers.full_text_excluded,
                                  exclude_reasons if exclude_reasons else "",
                                  self.COLORS['eligibility'])
        
        # Arrow from retrieved to excluded
        self._draw_arrow(x + self.BOX_WIDTH, y - self.BOX_HEIGHT - 30,
                        exclude_x, exclude_y - self.BOX_HEIGHT - 30)
        
        # Arrow down to inclusion
        self._draw_arrow(x + self.BOX_WIDTH // 2, y,
                        x + self.BOX_WIDTH // 2, y + 20)
        
        return y
    
    def _draw_inclusion_phase(self):
        """Draw inclusion phase (final studies)"""
        x = self.MARGIN
        y = self._draw_eligibility_phase() + 20
        
        # Phase title
        self.svg_elements.append(f'''
  <text x="{x}" y="{y}" class="phase-title">INCLUSION</text>
''')
        
        y += 30
        
        # Studies included in qualitative synthesis
        y = self._draw_box(x, y, "Studies included in qualitative synthesis",
                          self.numbers.studies_included_qualitative,
                          "", self.COLORS['inclusion'])
        
        # Studies included in quantitative synthesis (if provided)
        if self.numbers.studies_included_quantitative is not None:
            y = self._draw_box(x, y, "Studies included in quantitative synthesis",
                              self.numbers.studies_included_quantitative,
                              "(meta-analysis)", self.COLORS['inclusion'])


class PRISMADiagramTikZ:
    """Generate PRISMA 2020 flow diagram as TikZ code for LaTeX"""
    
    def __init__(self, numbers: DiagramNumbers):
        self.numbers = numbers
        self.tikz_elements = []
        
    def generate(self) -> str:
        """Generate complete TikZ diagram code"""
        self.tikz_elements = [
            "% PRISMA 2020 Flow Diagram (TikZ version)",
            "% Generated by SystematicReviewAssistant",
            "% https://github.com/cstroie/SystematicReviewAssistant\n",
            "\\documentclass[tikz]{standalone}",
            "\\usepackage{geometry}",
            "\\usepackage{tikz}",
            "\\usetikzlibrary{positioning, arrows.meta, shapes.geometric}",    
            "\\begin{document}\n",
            "\\begin{tikzpicture}[",
            "    node distance=30pt and 10pt,",
            "    title/.style={font=\\bfseries, anchor=west},",
            "    box/.style={",
            "        draw,",
            "        thick,",
            "        rectangle,",
            "        minimum width=9cm,",
            "        minimum height=1.2cm,",
            "        fill=white,",
            "        align=center,",
            "        text width=8.5cm",
            "    },",
            "    sidebox/.style={",
            "        draw,",
            "        thick,",
            "        rectangle,",
            "        minimum width=6cm,",
            "        minimum height=1.2cm,",
            "        fill=white,",
            "        align=center,",
            "        text width=5.5cm",
            "    },",
            "    arrow/.style={",
            "        -Stealth[scale=1.2],",
            "        thick,",
            "        shorten >=3pt,",
            "        shorten <=3pt",
            "    },",
            "    exclusiontitle/.style={",
            "        font=\\bfseries,",
            "        anchor=center,",
            "        fill=white,",
            "        inner sep=3pt",
            "    }\n",
            "]\n"
        ]
        
        # Layout coordinates
        x_main = 0
        x_exclude = 11
        y_step = -2.5
        current_y = 0
        
        # Draw phases
        current_y = self._draw_identification_phase(x_main, current_y)
        current_y += y_step
        current_y = self._draw_screening_phase(x_main, current_y, x_exclude)
        current_y += y_step
        current_y = self._draw_eligibility_phase(x_main, current_y, x_exclude)
        current_y += y_step
        self._draw_inclusion_phase(x_main, current_y)
        
        self.tikz_elements.append("\\end{tikzpicture}")
        self.tikz_elements.append("\\end{document}")
        
        return '\n'.join(self.tikz_elements)
    
    def _draw_box(self, x, y, title, number, subtitle, style="box", name_prefix=""):
        """Draw a TikZ box node"""
        content = f"\\textbf{{{title}}} \\\\ n = {number}"
        if subtitle:
            content += f" \\\\ \\footnotesize {subtitle}"
        
        name = f"{name_prefix}{int(abs(y))}"
        self.tikz_elements.append(f"\\node[{style}] ({name}) at ({x},{y}) {{{content}}};")
        return y - 2.8  # Return new y position
    
    def _draw_arrow(self, from_node, to_node, label=None, bend=None):
        """Draw an arrow between nodes with optional label and bend"""
        bend_cmd = f" to [bend left={bend}] " if bend else "--"
        arrow = f"\\draw[arrow] ({from_node}) {bend_cmd} ({to_node});"
        if label:
            arrow += f" node[midway, right=2pt] {{\\footnotesize {label}}}"
        self.tikz_elements.append(arrow)
    
    def _draw_exclusion_title(self, x, y, text):
        """Draw exclusion phase title"""
        self.tikz_elements.append(f"\\node[exclusiontitle] at ({x},{y + 0.8}) {{{text}}};")
    
    def _draw_identification_phase(self, x, y):
        """Draw identification phase"""
        self.tikz_elements.append(f"\\node[title] at ({x},{y + 0.5}) {{IDENTIFICATION}};")
        
        # Records identified
        sources = []
        if self.numbers.database_count > 0:
            sources.append(f"PubMed (n = {self.numbers.records_identified})")
        if self.numbers.register_count > 0:
            sources.append(f"Trial registers (n = {self.numbers.register_count})")
        if self.numbers.other_sources_count > 0:
            sources.append(f"Other sources (n = {self.numbers.other_sources_count})")
        
        subtitle = ", ".join(sources) if sources else ""
        new_y = self._draw_box(x, y, "Records identified", 
                              self.numbers.records_identified, subtitle, 
                              style="box", name_prefix="ident")
        
        return new_y
    
    def _draw_screening_phase(self, x, y, exclude_x):
        """Draw screening phase"""
        self.tikz_elements.append(f"\\node[title] at ({x},{y + 0.5}) {{SCREENING}};")
        self._draw_exclusion_title(exclude_x, y - 0.3, "EXCLUSIONS")
        
        # Records screened
        screened_y = self._draw_box(x, y, "Records screened", 
                                   self.numbers.records_screened, "", 
                                   style="box", name_prefix="screen")
        
        # Records excluded (right side)
        excluded_y = self._draw_box(exclude_x, y, "Records excluded",
                                   self.numbers.records_excluded, "",
                                   style="sidebox", name_prefix="excluded_screen")
        
        # Arrow from screened to excluded
        self._draw_arrow("screen0.east", "excluded_screen0.west", bend=30)
        
        # Arrow from identification to screening
        self._draw_arrow("ident0", "screen0", "Duplicates removed")
        
        return screened_y
    
    def _draw_eligibility_phase(self, x, y, exclude_x):
        """Draw eligibility phase"""
        self.tikz_elements.append(f"\\node[title] at ({x},{y + 0.5}) {{ELIGIBILITY}};")
        self._draw_exclusion_title(exclude_x, y - 0.3, "EXCLUSIONS")
        
        # Full-text articles
        eligibility_y = self._draw_box(x, y, "Full-text articles assessed",
                                      self.numbers.full_text_retrieved, "",
                                      style="box", name_prefix="eligibility")
        
        # Excluded with reasons
        excluded_text = ""
        if self.numbers.full_text_exclude_reasons:
            reasons = ["• " + f"{k} (n={v})" for k, v in self.numbers.full_text_exclude_reasons.items()]
            excluded_text = " \\\\ ".join(reasons[:3] if len(reasons) > 3 else reasons)
        excluded_y = self._draw_box(exclude_x, y, "Full-text articles excluded",
                                   self.numbers.full_text_excluded, excluded_text,
                                   style="sidebox", name_prefix="excluded_eligibility")
        
        # Draw arrows
        self._draw_arrow("screen0", "eligibility0", "Full-text articles retrieved")
        self._draw_arrow("eligibility0.east", "excluded_eligibility0.west", bend=30)
        
        return eligibility_y
    
    def _draw_inclusion_phase(self, x, y):
        """Draw inclusion phase"""
        self.tikz_elements.append(f"\\node[title] at ({x},{y + 0.5}) {{INCLUSION}};")
        
        # Studies included
        inclusion_y = self._draw_box(x, y, "Studies included in qualitative synthesis",
                                    self.numbers.studies_included_qualitative, "",
                                    style="box", name_prefix="included")
        
        # Quantitative studies if available
        if self.numbers.studies_included_quantitative is not None:
            quant_y = self._draw_box(x, inclusion_y - 2.8, 
                                    "Studies included in quantitative synthesis",
                                    self.numbers.studies_included_quantitative, 
                                    "(meta-analysis)",
                                    style="box", name_prefix="included_quant")
        
        # Connect eligibility to inclusion
        self._draw_arrow("eligibility0", "included0", 
                        f"Included studies (n={self.numbers.studies_included_qualitative})")


class PRISMADiagramHTML:
    """Generate PRISMA 2020 flow diagram as interactive HTML"""
    
    def __init__(self, numbers: DiagramNumbers, title: str = "PRISMA 2020 Flow Diagram"):
        self.numbers = numbers
        self.title = title
    
    def generate(self) -> str:
        """Generate HTML with embedded visualization"""
        svg_generator = PRISMADiagramSVG(self.numbers)
        svg_content = svg_generator.generate()
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{
            text-align: center;
            color: #2C3E50;
            margin-bottom: 30px;
        }}
        .diagram {{
            text-align: center;
            margin: 20px 0;
        }}
        svg {{
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        .summary {{
            margin-top: 30px;
            padding: 15px;
            background-color: #f9f9f9;
            border-left: 4px solid #2C3E50;
        }}
        .summary h3 {{
            margin-top: 0;
            color: #2C3E50;
        }}
        .summary-item {{
            margin: 10px 0;
            font-size: 14px;
        }}
        .download-buttons {{
            text-align: center;
            margin: 20px 0;
        }}
        button {{
            padding: 10px 20px;
            margin: 5px;
            background-color: #2C3E50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }}
        button:hover {{
            background-color: #34495E;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{self.title}</h1>
        
        <div class="diagram">
            {svg_content}
        </div>
        
        <div class="summary">
            <h3>Search and Selection Summary</h3>
            <div class="summary-item"><strong>Records identified:</strong> {self.numbers.records_identified}</div>
            <div class="summary-item"><strong>Records screened:</strong> {self.numbers.records_screened}</div>
            <div class="summary-item"><strong>Records excluded:</strong> {self.numbers.records_excluded}</div>
            <div class="summary-item"><strong>Full-text articles retrieved:</strong> {self.numbers.full_text_retrieved}</div>
            <div class="summary-item"><strong>Full-text articles excluded:</strong> {self.numbers.full_text_excluded}</div>
            <div class="summary-item"><strong>Studies included (qualitative):</strong> {self.numbers.studies_included_qualitative}</div>
            {f'<div class="summary-item"><strong>Studies included (quantitative):</strong> {self.numbers.studies_included_quantitative}</div>' if self.numbers.studies_included_quantitative else ''}
        </div>
        
        <div class="download-buttons">
            <button onclick="downloadSVG()">Download as SVG</button>
            <button onclick="downloadPNG()">Download as PNG</button>
            <button onclick="window.print()">Print</button>
        </div>
    </div>
    
    <script>
        function downloadSVG() {{
            const svg = document.querySelector('svg');
            const serializer = new XMLSerializer();
            const svgString = serializer.serializeToString(svg);
            const blob = new Blob([svgString], {{ type: 'image/svg+xml' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'prisma_flow_diagram.svg';
            a.click();
        }}
        
        function downloadPNG() {{
            alert('To download as PNG, right-click the diagram and select "Save image as..."\\nOr use an online SVG to PNG converter.');
        }}
    </script>
</body>
</html>
'''
        return html


def calculate_numbers_from_screening(screening_results: List[Dict]) -> DiagramNumbers:
    """Calculate PRISMA numbers from screening results JSON
    
    Expected JSON structure from pipeline:
    [
        {
            "pmid": "12345678",
            "decision": "INCLUDE|EXCLUDE|UNCERTAIN",
            "confidence": 0.95,
            "reasoning": "..."
        }
    ]
    """
    
    total_records = len(screening_results)
    included = sum(1 for r in screening_results if r.get('decision') == 'INCLUDE')
    excluded = sum(1 for r in screening_results if r.get('decision') == 'EXCLUDE')
    uncertain = sum(1 for r in screening_results if r.get('decision') == 'UNCERTAIN')
    
    return DiagramNumbers(
        records_identified=total_records,
        records_screened=total_records,
        records_excluded=excluded + uncertain,  # uncertain go to full-text review
        full_text_retrieved=included + uncertain,
        full_text_excluded=uncertain,  # These are the ones needing manual review
        studies_included_qualitative=included
    )


def create_diagram_from_results(
    screening_results_json: str,
    output_dir: str = ".",
    formats: List[str] = None) -> Dict[str, str]:
    """Create PRISMA diagram from pipeline screening results
    
    Args:
        screening_results_json: Path to 02_screening_results.json from pipeline
        output_dir: Directory to save outputs
        formats: List of formats to generate ('svg', 'html', 'png', 'all')
    
    Returns:
        Dictionary with paths to generated files
    """
    
    if formats is None:
        formats = ['svg', 'html']
    
    if 'all' in formats:
        formats = ['svg', 'html', 'png', 'tikz']
    
    # Load screening results
    with open(screening_results_json, 'r') as f:
        results = json.load(f)
    
    # Calculate numbers
    numbers = calculate_numbers_from_screening(results)
    
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    output_files = {}
    
    # Generate SVG
    if 'svg' in formats:
        svg_generator = PRISMADiagramSVG(numbers)
        svg_content = svg_generator.generate()
        svg_file = output_dir / 'prisma_flow_diagram.svg'
        with open(svg_file, 'w') as f:
            f.write(svg_content)
        output_files['svg'] = str(svg_file)
        print(f"✓ SVG diagram saved: {svg_file}")
    
    # Generate TikZ (LaTeX)
    if 'tikz' in formats:
        tikz_generator = PRISMADiagramTikZ(numbers)
        tikz_content = tikz_generator.generate()
        tex_file = output_dir / 'prisma_flow_diagram.tex'
        with open(tex_file, 'w') as f:
            f.write(tikz_content)
        output_files['tikz'] = str(tex_file)
        print(f"✓ TikZ diagram saved: {tex_file}")
    
    # Generate HTML
    if 'html' in formats:
        html_generator = PRISMADiagramHTML(numbers)
        html_content = html_generator.generate()
        html_file = output_dir / 'prisma_flow_diagram.html'
        with open(html_file, 'w') as f:
            f.write(html_content)
        output_files['html'] = str(html_file)
        print(f"✓ HTML diagram saved: {html_file}")
    
    # PNG generation requires external tool
    if 'png' in formats:
        print("ℹ PNG generation: Use SVG converter")
        print("  - Online: https://convertio.co/svg-png/")
        print("  - Or use 'inkscape prisma_flow_diagram.svg --export-png=diagram.png'")
    
    return output_files


def main():
    """Command-line interface"""
    
    if len(sys.argv) < 2:
        print("PRISMA 2020 Flow Diagram Generator")
        print("\nUsage:")
        print("  python prisma_flow_diagram.py <screening_results.json>")
        print("  python prisma_flow_diagram.py <screening_results.json> --format svg")
        print("  python prisma_flow_diagram.py <screening_results.json> --format all")
        print("\nFormats: svg (default), html, png, tikz, all")
        print("\nExample:")
        print("  python prisma_flow_diagram.py output/02_screening_results.json --format all")
        sys.exit(1)
    
    results_file = sys.argv[1]
    
    # Parse format argument
    formats = ['svg', 'html']
    if '--format' in sys.argv:
        idx = sys.argv.index('--format')
        if idx + 1 < len(sys.argv):
            formats = [sys.argv[idx + 1]]
    
    # Validate file exists
    if not Path(results_file).exists():
        print(f"Error: File not found: {results_file}")
        sys.exit(1)
    
    # Get output directory
    output_dir = Path(results_file).parent
    
    # Generate diagrams
    print(f"\nGenerating PRISMA flow diagrams...")
    print(f"Input: {results_file}")
    
    output_files = create_diagram_from_results(
        results_file,
        output_dir=output_dir,
        formats=formats
    )
    
    print(f"\n✓ Diagrams created successfully!")
    for fmt, path in output_files.items():
        print(f"  - {fmt.upper()}: {Path(path).name}")


if __name__ == '__main__':
    main()
