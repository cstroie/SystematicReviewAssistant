# Comprehensive Prompt for LaTeX Systematic Review Article Generation

## CONTEXT & OBJECTIVES

You are generating a **peer-review-ready LaTeX academic article** reporting a systematic review and thematic synthesis on:
**"Clinical Decision Support Systems in Pediatric Radiology: A Systematic Review of Implementations, Proposals, and User Experiences (2014-2024)"**

The article must:
- Follow international journal standards (target: Radiology, JRSM, Pediatric Radiology)
- Be structured per PRISMA 2020 guidelines
- Include comprehensive thematic synthesis with deep analysis
- Present all quantitative and qualitative data systematically
- Demonstrate critical appraisal and methodological rigor
- Be suitable for high-impact peer review

---

## DATA INPUTS TO INCLUDE

### From Pipeline Output Files:

1. **02_screening_results.json**
   - Extract: Total identified, screened, excluded, included numbers
   - Calculate: Screening flow percentages and attrition rates
   - Include: PRISMA flow diagram description

2. **03_extracted_data.json**
   - Extract for each study:
     - PMID, authors, year, journal
     - Study design and methodology
     - Sample size (patients/images)
     - Clinical domain and imaging modalities
     - CDSS type and implementation details
     - Primary outcomes and metrics (sensitivity, specificity, AUC, accuracy)
     - Comparison group (radiologist alone, standard of care, etc.)
     - Main findings and clinical implications

3. **04_quality_assessment.json**
   - Extract: QUADAS-2 domain ratings for each study
   - Calculate: Overall bias distribution (Low/Moderate/High)
   - Analyze: Quality trends by year, modality, study design
   - Identify: Common methodological strengths and weaknesses

4. **05_thematic_synthesis.txt**
   - Use as foundation for thematic analysis section
   - Expand with quantitative synthesis
   - Add critical interpretation

5. **summary_characteristics_table.csv**
   - All study characteristics for Table 1
   - Organize by: modality, domain, year, design

### Derived/Calculated Metrics:

- Study distribution by year (trend analysis)
- Breakdown by imaging modality (MRI, CT, US, etc.)
- Breakdown by clinical domain (oncology, trauma, infection, etc.)
- Distribution by CDSS type (AI/ML, rule-based, hybrid)
- Performance metric ranges and medians
- Study design distribution (RCT vs observational)
- Publication bias assessment
- Heterogeneity analysis

---

## ARTICLE STRUCTURE & SECTIONS

### 1. TITLE & ABSTRACT (250-300 words)

**Title Format:**
"Clinical Decision Support Systems in Pediatric Medical Imaging: A Systematic Review of Implementations, Proposals, and User Experiences"

**Abstract Structure:**
- **Background**: Growing integration of CDSS in radiology; clinical significance in pediatrics
- **Objective**: Characterize CDSS implementations, types, and clinical outcomes in pediatric radiology
- **Methods**: Systematic search (PubMed 2014-2024), PRISMA 2020 compliance, QUADAS-2 quality assessment
- **Results**: Include key numbers (total studies, range of outcomes, quality distribution)
- **Conclusions**: Summary of findings, research gaps, clinical implications

---

### 2. INTRODUCTION (800-1200 words)

**Subsections:**

A. **Background on Clinical Decision Support Systems**
   - Definition and evolution of CDSS in healthcare
   - Historical development (1970s-present)
   - Shift from rule-based to AI/ML-based systems
   - Current landscape in diagnostic imaging

B. **Radiology and Medical Imaging Context**
   - Role of imaging in pediatric diagnosis
   - Challenges in pediatric radiology:
     - Age-specific presentations
     - Limited patient cooperation
     - Radiation dose concerns
     - Diagnostic uncertainty
     - Workload and time pressures
   - Potential of decision support systems

C. **Why Pediatric Population is Unique**
   - Different disease presentations than adults
   - Limited datasets for training algorithms
   - Specific ethical considerations
   - Developmental factors affecting imaging patterns
   - Need for age-appropriate clinical decision rules

D. **Specific Imaging Modalities in Pediatrics**
   - CT, MRI, ultrasound, radiography, interventional radiology
   - Modality-specific decision needs
   - State of CDSS implementation by modality

E. **Justification for Review**
   - Gap in literature (no recent systematic review)
   - Increasing clinical interest
   - Need for evidence on implementation and user acceptance
   - Implications for clinical practice and research

F. **Research Questions**
   1. What types of CDSS have been implemented or proposed in pediatric radiology?
   2. What are their reported diagnostic accuracy and clinical outcomes?
   3. What is the state of implementation and user acceptance?
   4. What methodological quality characterizes these studies?
   5. What are the remaining research gaps and priorities?

---

### 3. METHODS (1000-1500 words)

**Subsections:**

A. **Protocol and Registration**
   - State PROSPERO registration (if done) or pre-registration details
   - Deviation from protocol (if any)

B. **Search Strategy**
   - Exact PubMed query used (with syntax)
   - Date range: 2014-2024 (rationale: emerging AI era)
   - Databases searched: PubMed (state why only PubMed, or if others searched)
   - Search terms organized by concept:
     - CDSS/AI terminology used
     - Imaging modalities included
     - Pediatric population terms
     - Implementation/evaluation terms
   - Filters applied (language, article type, species)
   - Search conducted on [DATE]

C. **Study Selection Criteria**

   **Inclusion Criteria:**
   1. Peer-reviewed journal articles
   2. English language
   3. Published 2014-2024
   4. Describes implementation, proposal, evaluation, or user experience of CDSS
   5. Involves medical imaging (any modality)
   6. Pediatric population (0-18 years, or includes pediatric subgroup)
   7. Reports clinical data, outcomes, or diagnostic accuracy
   8. Original research (not review article)

   **Exclusion Criteria:**
   1. Purely technical/algorithmic papers (no clinical context)
   2. Animal or preclinical studies
   3. CDSS not specifically for diagnostic imaging
   4. Adult-only population studies
   5. No quantitative outcomes reported
   6. Conference abstracts, editorials, opinion pieces
   7. Duplicate publications

D. **Screening Process**
   - Two-stage screening: title/abstract, then full-text
   - Automated LLM-assisted screening (mention method)
   - Manual review of uncertain cases
   - Dual independent review methodology
   - Disagreement resolution procedures
   - Inter-rater reliability (if calculated)

E. **Data Extraction**
   - Standardized extraction form (describe fields)
   - Study characteristics:
     - Bibliographic (PMID, authors, year, journal)
     - Design (prospective/retrospective, RCT/observational)
     - Population (N, age range, demographics)
     - Setting (single center/multi-center, academic/community)
   - Intervention details:
     - CDSS name and type
     - Technology used (AI/ML algorithm, rule-based, etc.)
     - Clinical application
     - Imaging modality
   - Outcomes:
     - Primary and secondary outcomes
     - Diagnostic accuracy metrics (sensitivity, specificity, AUC, accuracy)
     - Clinical outcomes (diagnostic agreement, time, errors)
     - User experience data
   - Quality indicators
   - Sources of funding/conflict of interest

F. **Quality Assessment**
   - Tool used: QUADAS-2 (diagnostic accuracy studies)
   - Rationale for tool selection
   - Four domains assessed
   - Interpretation of overall bias rating
   - Conducted by independent reviewers
   - Disagreement resolution

G. **Data Analysis and Synthesis**

   **Quantitative Synthesis:**
   - Summary statistics:
     - Range of sensitivity/specificity/AUC
     - Median and IQR by modality/domain
     - Forest plots (if appropriate)
   - Subgroup analyses by:
     - Imaging modality
     - Clinical domain
     - CDSS type (AI/ML vs rule-based)
     - Study design
     - Study quality (low vs moderate/high bias)
   - Trend analysis over time
   - Publication bias assessment (if applicable)
   - Heterogeneity assessment

   **Qualitative Synthesis (Thematic Analysis):**
   - Thematic coding approach
   - Identification of major themes and sub-themes
   - Theme frequency analysis
   - Cross-cutting patterns and tensions
   - Integration of quantitative and qualitative findings

H. **PRISMA 2020 Compliance**
   - Checklist item mapping
   - Adherence to reporting standards

---

### 4. RESULTS (1500-2500 words)

**Subsections:**

A. **Study Selection**
   - PRISMA flow diagram description
   - Numbers at each stage with percentages
   - Reasons for exclusion at full-text stage
   - Description of included studies
   - Geographic distribution
   - Journal distribution

B. **Study Characteristics**

   **Table 1: Summary Characteristics of Included Studies**
   - All studies in systematic format
   - Columns: Author (year), Design, N, Age, Modality, Domain, CDSS Type, Outcomes
   - Sorted by year (most recent first) or by modality

   **Descriptive Analysis:**
   - Number of studies by year (trend graph)
   - Geographic distribution (countries represented)
   - Journal distribution (top 10 journals)
   - Study design breakdown (% RCT vs observational)
   - Sample size: range, median (number of patients, images)
   - Age group representation

C. **CDSS Characteristics**

   **By Type:**
   - AI/ML-based systems: number, types of algorithms (deep learning, machine learning, etc.)
   - Rule-based systems: number, types of rules
   - Hybrid systems: number, combinations
   - Distribution by type (pie chart or percentage)

   **By Modality (Major Section):**
   
   For each modality (CT, MRI, Ultrasound, Radiography, PET-CT, Interventional, Fluoroscopy):
   - Number of studies
   - CDSS types used
   - Clinical domains addressed
   - Performance range
   - Implementation status
   - User acceptance data (if available)

   **By Clinical Domain (Major Section):**
   
   For each domain (Oncology, Trauma, Infection, Cardiac, Abdominal, Neuro, Other):
   - Number of studies
   - Imaging modalities used
   - Performance metrics
   - Clinical significance
   - Implementation challenges mentioned

D. **Diagnostic Accuracy and Clinical Outcomes**

   **Sensitivity and Specificity:**
   - Range across all studies
   - Median and IQR by modality
   - Median and IQR by domain
   - Highest and lowest reported values
   - Comparison: CDSS vs radiologist alone (if reported)
   - Comparison: CDSS + radiologist vs radiologist alone

   **Area Under ROC Curve (AUC):**
   - Range of reported AUC values
   - Median by modality/domain
   - Interpretation of performance

   **Other Outcomes:**
   - Diagnostic accuracy percentage
   - Agreement rates
   - Inter-observer agreement
   - Time to diagnosis
   - Error rates
   - Workflow impact

   **Comparative Effectiveness:**
   - Studies directly comparing CDSS to standard practice
   - Studies comparing different CDSS types
   - Superiority/non-inferiority findings

E. **Implementation and Deployment**

   **Implementation Status:**
   - Number of studies reporting deployed/operational systems
   - Number of studies proposing systems not yet deployed
   - Number of pilot/proof-of-concept studies

   **Implementation Challenges Identified:**
   - Technical barriers (system integration, data standardization)
   - Workflow integration issues
   - Data privacy and security concerns
   - Training and adoption requirements
   - Cost and resource barriers

F. **User Experience and Acceptance**

   **Quantitative User Data:**
   - Studies measuring user satisfaction/acceptance
   - Survey response rates and sample sizes
   - Key metrics (usability scores, acceptance rates)
   - Satisfaction levels by user type (radiologist vs technician, etc.)

   **Qualitative User Themes:**
   - Perceived benefits
   - Concerns and barriers
   - Workflow integration experiences
   - Recommendations for improvement

G. **Quality Assessment Results**

   **Overall Quality Distribution:**
   - Low risk of bias: n studies (%)
   - Moderate risk: n studies (%)
   - High risk: n studies (%)
   - Common sources of bias by domain

   **QUADAS-2 Domain Breakdown:**
   - Patient selection: % adequate
   - Index test conduct: % adequate
   - Reference standard: % adequate
   - Flow and timing: % adequate
   - Summary table of bias ratings

   **Quality by Study Characteristics:**
   - Quality by year (improving over time?)
   - Quality by modality
   - Quality by study design (RCT vs observational)
   - Quality vs journal impact factor

H. **Publication Bias**
   - Funnel plot assessment (if meta-analysis)
   - Discussion of potential bias
   - Assessment of gray literature gap

I. **Heterogeneity Analysis**
   - Sources of clinical heterogeneity
   - Sources of methodological heterogeneity
   - Impact on synthesis conclusions

---

### 5. THEMATIC SYNTHESIS & QUALITATIVE ANALYSIS (1500-2000 words)

**Subsections:**

A. **Overall Thematic Framework**
   - Description of thematic analysis approach
   - Number of codes/themes identified
   - Coding process (data-driven vs framework approach)
   - Inter-coder reliability (if applicable)

B. **Major Themes Identified**

   **Theme 1: Technology Evolution and Diversity**
   - Shift from rule-based to AI/ML systems
   - Increasing use of deep learning
   - Algorithm types across modalities
   - Customization by clinical domain
   - Supporting data: frequency analysis across studies

   **Theme 2: Clinical Performance and Diagnostic Value**
   - Strong diagnostic accuracy across modalities
   - Variability by modality and domain
   - CDSS as supplementary tool vs standalone
   - Comparison to radiologist performance
   - Key studies exemplifying findings

   **Theme 3: Implementation Challenges and Barriers**
   - Technical integration barriers
   - Workflow disruption concerns
   - Regulatory and liability issues
   - Data governance challenges
   - Cost-benefit considerations
   - Evidence from implementation studies

   **Theme 4: User Acceptance and Human Factors**
   - Radiologist acceptance varies
   - Trust in system output crucial
   - Training requirements
   - Concern about "deskilling"
   - Integration with clinical judgment
   - Studies reporting user feedback

   **Theme 5: Pediatric-Specific Considerations**
   - Limited training data
   - Age-specific algorithm adaptation
   - Radiation dose optimization
   - Developmental factors
   - Few studies specifically designed for pediatrics

   **Theme 6: Evidence Gaps and Research Needs**
   - Lack of prospective studies
   - Few implementation science studies
   - Limited long-term follow-up
   - Insufficient health economic analyses
   - Minimal data on patient outcomes
   - Publication bias toward positive results

C. **Cross-Cutting Patterns and Tensions**
   - Paradox: High technical performance but slow clinical adoption
   - Evidence-practice gap: Why haven't systems been widely implemented despite good evidence?
   - Pediatric paradox: High potential but limited research
   - Modality differences: Why some modalities more advanced than others
   - Comparison: Academic centers vs community practice
   - Geographic variations: Differential adoption globally

D. **Synthesis of Evidence Quality**
   - Which themes are supported by high-quality evidence?
   - Which rely on lower-quality or limited evidence?
   - Confidence in thematic conclusions
   - Limitations of evidence base

---

### 6. DISCUSSION (1500-2000 words)

**Subsections:**

A. **Principal Findings Summary**
   - Summary of main results in context of research questions
   - How findings compare to previous knowledge
   - Unexpected findings
   - Clinical significance of findings

B. **Interpretation of Findings**

   **For Each Major Theme:**
   - What does it mean?
   - Why is it important?
   - How does it compare to existing literature?
   - Clinical and research implications

C. **Strengths of Included Evidence**
   - Breadth of coverage (modalities, domains, countries)
   - Generally adequate sample sizes
   - Variety of CDSS types examined
   - Integration of quantitative and qualitative data
   - Recognition of methodological rigor in best studies

D. **Limitations of Evidence Base**

   **Study-Level Limitations:**
   - Heterogeneity in design and outcomes
   - Publication bias (only positive results reported)
   - Limited prospective studies
   - Few direct comparisons between systems
   - Insufficient long-term follow-up

   **Population/Setting Limitations:**
   - Predominantly single-center studies
   - Academic medical center bias
   - Geographic concentration (developed countries)
   - Lack of diverse populations
   - Limited community/rural practice representation

   **CDSS-Specific Limitations:**
   - Insufficient pediatric-specific research
   - Limited implementation research
   - Few health economic evaluations
   - Minimal data on workflow impact
   - Limited user experience research

   **Evidence Quality Limitations:**
   - Risk of bias in some studies (primarily patient selection)
   - Inconsistent outcome reporting
   - No standardized quality metrics
   - Limited transparency in algorithm development

E. **Why Implementation Has Not Progressed Despite Promising Evidence**

   **Technical Barriers:**
   - Integration with existing EHR/PACS systems
   - Data standardization and interoperability
   - Regulatory approval processes
   - Data privacy and security requirements
   - Need for continuous validation with new data

   **Organizational Barriers:**
   - Cost of implementation and maintenance
   - Need for staff training and retraining
   - Disruption of established workflows
   - Institutional inertia
   - Lack of reimbursement models

   **Human Factors:**
   - Radiologist skepticism and trust issues
   - Concern about job displacement
   - Variable perceived need
   - Preference for human judgment
   - Generational differences in acceptance

   **Healthcare System Factors:**
   - Regulatory uncertainty
   - Liability and medico-legal concerns
   - Lack of clear clinical practice guidelines
   - Limited health economic data
   - Competing priorities in resource allocation

F. **Pediatric-Specific Challenges and Opportunities**

   **Challenges:**
   - Smaller patient populations for algorithm training
   - Age-specific disease presentations
   - Developmental variability
   - Ethical considerations (radiation, consent)
   - Limited research funding
   - Slower commercial development

   **Opportunities:**
   - High clinical need and benefit
   - Potential for dose reduction
   - Support for diagnostic learning
   - Integration with growth/developmental data
   - Global health applications

G. **Future Directions and Research Priorities**

   **Clinical Research:**
   - Large-scale prospective validation studies
   - Comparative effectiveness trials
   - Implementation science studies
   - Long-term outcome studies
   - Health economic analyses

   **Methodological:**
   - Standardized quality frameworks
   - Consensus on outcome reporting
   - Improved risk of bias assessment for AI systems
   - Transparency in algorithm development

   **Implementation:**
   - Real-world effectiveness studies
   - Workflow integration research
   - User experience and acceptance studies
   - Scalability and generalization studies
   - Health system integration models

   **Pediatric-Specific:**
   - Algorithm development using pediatric data
   - Age-specific validation
   - Pediatric-focused implementation research
   - Ethical framework development

H. **Clinical Practice Implications**

   **For Radiologists:**
   - CDSS as tool to enhance (not replace) expertise
   - Importance of continued learning and judgment
   - Opportunity to focus on complex cases
   - Need for critical appraisal of system outputs

   **For Institutions:**
   - Evidence supports CDSS implementation in specific domains
   - Careful selection based on clinical needs and resources
   - Need for robust implementation and change management
   - Investment in training and support

   **For Patients:**
   - Potential for improved diagnostic accuracy
   - Possible radiation dose reduction
   - Faster diagnosis in some scenarios
   - Assurance of systematic review

I. **Comparison with Related Reviews**
   - How this review differs from previous reviews
   - Consistency/inconsistency with other systematic reviews
   - Evolution of field (if prior reviews exist)

J. **Study Limitations**

   **Search and Selection:**
   - PubMed-only search (may miss non-indexed journals)
   - English language only
   - Fixed time frame (2014-2024)
   - Risk of selection bias in LLM screening

   **Analysis:**
   - Narrative synthesis limited by heterogeneity
   - Unable to perform meta-analysis (heterogeneous outcomes)
   - Limited subgroup analysis due to sample size
   - Cannot establish causation
   - Dependent on quality of reporting in included studies

K. **Conclusions**

   **Summary Statement:**
   - State the most important findings in 1-2 sentences
   - Clinical significance

   **Research Gap Conclusions:**
   - Most critical gap identified
   - Why it's important to address

   **Recommendations:**
   - For clinical practice
   - For researchers
   - For policymakers/institutions
   - For future systematic reviews

---

### 7. REFERENCES

- Format: APA or journal-specific (check target journal)
- Include: All 47+ studies reviewed
- Organize: Alphabetically by first author
- Format examples with proper citations

---

## LATEX DOCUMENT STRUCTURE

```latex
\documentclass[12pt,a4paper]{article}
% Preamble with packages
\usepackage[utf8]{inputenc}
\usepackage[english]{babel}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{graphicx}
\usepackage{float}
\usepackage{booktabs}
\usepackage{array}
\usepackage{geometry}
\usepackage{setspace}
\usepackage{hyperref}
\usepackage{color}
\usepackage{xcolor}
\usepackage{cite}
\usepackage{fancyhdr}
\usepackage{lastpage}
% ... additional packages for tables, figures, etc.

\geometry{margin=1in}
\onehalfspacing

\title{...}
\author{...}
\date{...}

\begin{document}

\maketitle
\begin{abstract}
...
\end{abstract}

\section{Introduction}
...

\section{Methods}
...

\section{Results}
...

\section{Discussion}
...

\section{Conclusions}
...

\bibliographystyle{plain}
\bibliography{references}

\appendix
\section{PRISMA Checklist}
...

\end{document}
```

---

## TABLES TO INCLUDE

### Table 1: Study Characteristics
- Columns: Author (Year), Design, N, Age, Modality, Domain, CDSS Type, Primary Outcome
- Rows: All 47+ studies
- Formatted for publication

### Table 2: QUADAS-2 Quality Assessment
- Studies with bias ratings by domain
- Color coding (green/yellow/red) for Low/Moderate/High risk
- Summary statistics

### Table 3: Diagnostic Accuracy by Modality
- Modality: CT, MRI, US, Radiography, PET-CT, Other
- Sensitivity (range, median)
- Specificity (range, median)
- AUC (range, median)
- Number of studies

### Table 4: Diagnostic Accuracy by Clinical Domain
- Domain: Oncology, Trauma, Infection, etc.
- Performance metrics by domain
- Number of studies

### Table 5: CDSS Types and Characteristics
- Type: AI/ML, Rule-based, Hybrid
- Subtypes and algorithms
- Frequency
- Modalities used
- Performance range

### Table 6: Implementation Status
- Studies by implementation stage
- Deployed vs proposed systems
- Clinical domain differences

---

## FIGURES TO INCLUDE

### Figure 1: PRISMA 2020 Flow Diagram
- Generated from screening results
- Professional quality

### Figure 2: Study Distribution Over Time
- Line graph 2014-2024
- Shows growth in research

### Figure 3: CDSS Distribution by Type
- Pie chart or stacked bar
- AI/ML vs Rule-based vs Hybrid

### Figure 4: Studies by Imaging Modality
- Bar chart
- Most common modalities

### Figure 5: Studies by Clinical Domain
- Bar chart
- Most studied domains

### Figure 6: Quality Assessment Summary
- Risk of bias visualization
- Bar chart of bias distribution
- QUADAS-2 domain summary

### Figure 7: Sensitivity/Specificity by Modality
- Forest plot or scatter plot
- Range and median

### Figure 8: Thematic Map
- Thematic network diagram
- Relationships between major themes

---

## CONTENT DENSITY & ANALYSIS DEPTH

**For Peer Review Success:**

1. **Quantitative Depth:**
   - Report all key metrics (sensitivity, specificity, AUC, accuracy)
   - Calculate medians, ranges, IQR for each metric by subgroup
   - Perform trend analysis (studies over time, bias over time)
   - Compare performance across modalities and domains systematically

2. **Qualitative Depth:**
   - Extract and analyze implementation challenges from all studies
   - Synthesize user experience findings
   - Identify cross-cutting patterns and tensions
   - Explain WHY findings have meaning

3. **Critical Analysis:**
   - Deep discussion of why implementation hasn't advanced despite good evidence
   - Detailed analysis of methodological limitations
   - Honest assessment of evidence gaps
   - Specific, actionable recommendations

4. **Pediatric Focus:**
   - Highlight unique aspects of pediatric imaging
   - Identify specific gaps in pediatric CDSS research
   - Discuss age-related considerations throughout
   - Emphasize pediatric-specific clinical significance

5. **Novelty & Impact:**
   - First comprehensive review specifically focused on pediatric radiology CDSS
   - Integration of implementation science perspective
   - User experience emphasis (often missing from technical reviews)
   - Actionable recommendations for practice and research

---

## WRITING GUIDELINES FOR PEER REVIEW SUCCESS

1. **Clarity:** Clear, direct language; avoid jargon where possible
2. **Structure:** Logical flow; clear topic sentences; explicit transitions
3. **Evidence:** All claims supported by cited evidence or analysis
4. **Transparency:** Acknowledge limitations; avoid overstating findings
5. **Balance:** Present both positive and negative findings
6. **Significance:** Explicitly state clinical and research significance
7. **Actionability:** Provide specific, implementable recommendations
8. **Originality:** Clearly distinguish novel findings from known knowledge
9. **Rigor:** Follow PRISMA guidelines; transparent methodology
10. **Impact:** Write for broad audience; explain why findings matter

---

## TARGET JOURNAL CONSIDERATIONS

**Suitable High-Impact Journals:**
1. **Radiology** - Highest impact, rigorous peer review
2. **Pediatric Radiology** - Specialty journal, good fit
3. **Journal of Medical Systems** - CDSS focus
4. **JRSM** - Open access, good for systematic reviews
5. **American Journal of Roentgenology** - Strong radiology journal

**Tailor to journal:**
- Check author guidelines
- Match word count limits
- Follow reference style
- Review recently published systematic reviews
- Match scope and audience

---

## SUMMARY

This prompt guides generation of a **comprehensive, deep-analysis systematic review article** that:

✅ Follows PRISMA 2020 guidelines completely  
✅ Includes extensive quantitative and qualitative data  
✅ Provides critical, thoughtful analysis  
✅ Identifies implementation barriers and future directions  
✅ Has strong clinical and research significance  
✅ Uses professional academic writing and structure  
✅ Has genuine chance of peer-review success  

The resulting LaTeX document will be **publication-ready** and suitable for submission to high-impact journals.
