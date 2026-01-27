"""LLM prompts for resume screening pipeline."""

EXTRACT_CANDIDATE_DETAILS = """
<role>
You are an expert HR data extraction specialist. Extract structured candidate information from resumes with precision.
</role>

<task>
Parse the resume text and extract candidate details into a JSON object.
</task>

<extraction_rules>
- name: Full name. Use "Unknown" if not found.
- email: Primary email. Use null if not found or invalid format.
- phone: Phone number with country code if present. Use null if not found.
- education: Highest degree and institution. Use null if not found.
- work_experience: Total years of professional experience (integer). Calculate from employment dates if not stated explicitly. Use null if unable to determine.
- skills: Technical and professional skills. Normalize variations (e.g., "ReactJS" → "React"). Extract from skills section, job descriptions, and projects.
- certifications: Professional certifications only (not courses or training). Use empty array if none.
</extraction_rules>

<experience_calculation>
- Sum all non-overlapping employment periods
- Round to nearest integer
- Exclude internships unless explicitly professional
- For current roles, calculate up to current date
</experience_calculation>

<output_schema>
{{
  "name": "string (required)",
  "email": "string|null (valid email format)",
  "phone": "string|null",
  "education": "string|null",
  "work_experience": "integer|null (years)",
  "skills": ["string"] (normalized, deduplicated),
  "certifications": ["string"]
}}
</output_schema>

<examples>
Input: "John Smith\njohn@email.com\nSoftware Engineer at Tech Corp (2020-present)\nSkills: Python, JS, React.js"
Output: {{"name": "John Smith", "email": "john@email.com", "phone": null, "education": null, "work_experience": 5, "skills": ["Python", "JavaScript", "React"], "certifications": []}}

Input: "Jane Doe\nExperience: 7+ years in DevOps\nAWS Certified Solutions Architect"
Output: {{"name": "Jane Doe", "email": null, "phone": null, "education": null, "work_experience": 7, "skills": ["DevOps", "AWS"], "certifications": ["AWS Certified Solutions Architect"]}}
</examples>

<resume>
{resume_text}
</resume>

Return only the JSON object, no additional text.
"""


EXTRACT_JD_DETAILS = """
<role>
You are an expert HR requirements analyst. Extract structured job requirements from job descriptions.
</role>

<task>
Parse the job description and extract requirements into a JSON object.
</task>

<experience_rules>
| JD Pattern | min_work_experience | max_work_experience |
|------------|---------------------|---------------------|
| "5-7 years" | 5 | 7 |
| "5+ years" | 5 | 8 (min + 3) |
| "minimum 5 years" | 5 | 8 (min + 3) |
| "up to 5 years" | 0 | 5 |
| "Senior level" | 5 | 8 |
| "Mid-level" | 2 | 5 |
| "Entry level/Junior" | 0 | 2 |
| Not mentioned | null | null |
</experience_rules>

<skill_extraction>
- Extract ALL technical skills mentioned (required and preferred)
- Normalize skill names (e.g., "JS" → "JavaScript")
- Include both explicit skills and implied skills from responsibilities
- Deduplicate the list
</skill_extraction>

<output_schema>
{{
  "min_work_experience": "integer|null (years)",
  "max_work_experience": "integer|null (years)",
  "skills": ["string"] (normalized, deduplicated)
}}
</output_schema>

<examples>
Input: "Senior Python Developer\n5+ years experience\nRequired: Python, Django, PostgreSQL\nNice to have: Docker, K8s"
Output: {{"min_work_experience": 5, "max_work_experience": 8, "skills": ["Python", "Django", "PostgreSQL", "Docker", "Kubernetes"]}}

Input: "Frontend Developer (2-4 years)\nReact, TypeScript, CSS"
Output: {{"min_work_experience": 2, "max_work_experience": 4, "skills": ["React", "TypeScript", "CSS"]}}
</examples>

<job_description>
{jd_text}
</job_description>

Return only the JSON object, no additional text.
"""


NORMALIZE_SKILLS = """
<role>
You are an expert skill ontology specialist. Normalize and match skills using semantic understanding.
</role>

<task>
Given candidate skills and job description skills, normalize them to standard forms and identify matches.
</task>

<normalization_rules>
- Map variations to canonical names (e.g., "JS", "Javascript", "ECMAScript" → "JavaScript")
- Recognize skill families (React, React Native → React ecosystem)
- Group related technologies (AWS, EC2, S3 → AWS/Cloud)
- Identify implied skills (Full Stack → Frontend + Backend)
- Handle acronyms and abbreviations
</normalization_rules>

<skill_categories>
- programming: Programming languages (Python, Java, JavaScript)
- framework: Frameworks and libraries (React, Django, Spring)
- tool: Development tools (Git, Docker, Jenkins)
- database: Databases (PostgreSQL, MongoDB, Redis)
- cloud: Cloud platforms and services (AWS, GCP, Azure)
- methodology: Methodologies (Agile, Scrum, DevOps)
- soft_skill: Soft skills (Leadership, Communication)
- other: Uncategorized skills
</skill_categories>

<matching_rules>
Skills match if:
1. Exact match (case-insensitive)
2. Same normalized form
3. Related technology in same ecosystem (React/React Native, AWS/EC2)
4. Broader skill implies specific (Full Stack implies Frontend)
5. Semantic similarity ≥ 0.8
</matching_rules>

<output_schema>
{{
  "candidate_skills": [
    {{"raw_skill": "string", "normalized_skill": "string", "confidence": 0.0-1.0, "category": "string"}}
  ],
  "jd_skills": [
    {{"raw_skill": "string", "normalized_skill": "string", "confidence": 0.0-1.0, "category": "string"}}
  ],
  "matched_pairs": [["candidate_skill", "jd_skill"]],
  "match_scores": {{"candidate_skill:jd_skill": 0.0-1.0}},
  "skill_match_percentage": 0-100,
  "reasoning": "string explaining normalization and matching logic"
}}
</output_schema>

<candidate_skills>
{candidate_skills}
</candidate_skills>

<jd_skills>
{jd_skills}
</jd_skills>

Return only the JSON object, no additional text.
"""


VERIFY_EXPERIENCE = """
<role>
You are an expert HR verification specialist. Analyze work history for accuracy and consistency.
</role>

<task>
Extract and verify work experience entries from resume text. Calculate total experience and assess confidence.
</task>

<extraction_rules>
- Extract each distinct employment period
- Parse start/end dates to YYYY-MM format
- Handle "present" or "current" as ongoing roles
- Mark dates as "unknown" if not determinable
- Calculate duration in months for each entry
- Detect gaps (> 3 months between roles)
- Detect overlaps (concurrent employment)
</extraction_rules>

<verification_checks>
- Date format consistency
- Reasonable job durations (flag if < 3 months or > 15 years single role)
- Career progression logic
- Title/seniority progression
- Gap explanations (if any)
</verification_checks>

<confidence_levels>
- high: All dates clear, no gaps, logical progression
- medium: Some dates unclear OR minor gaps OR unusual pattern
- low: Multiple unknown dates OR major gaps OR inconsistencies
</confidence_levels>

<experience_fit_scoring>
Given JD requirements (min_exp, max_exp):
- Perfect fit (within range): 100
- Within ±1 year of range: 80
- Within ±2 years of range: 60
- Within ±3 years of range: 40
- Beyond ±3 years: 20
- Unknown experience: 30
</experience_fit_scoring>

<output_schema>
{{
  "entries": [
    {{
      "company": "string",
      "role": "string",
      "start_date": "YYYY-MM or unknown",
      "end_date": "YYYY-MM, present, or unknown",
      "duration_months": integer|null,
      "is_verified": boolean,
      "notes": "string|null"
    }}
  ],
  "total_experience_months": integer,
  "total_experience_years": integer,
  "has_gaps": boolean,
  "gap_details": ["string"],
  "has_overlaps": boolean,
  "verification_confidence": "high|medium|low",
  "confidence_reason": "string",
  "experience_fit_score": 0-100,
  "reasoning": "string"
}}
</output_schema>

<resume_text>
{resume_text}
</resume_text>

<jd_requirements>
min_experience: {min_experience}
max_experience: {max_experience}
</jd_requirements>

Return only the JSON object, no additional text.
"""


CHECK_BIAS_COMPLIANCE = """
<role>
You are an expert HR compliance specialist focused on fair hiring practices and bias prevention.
</role>

<task>
Scan resume text for protected attributes that should NOT influence hiring decisions.
</task>

<protected_attributes>
- age: Birth date, graduation years implying age, age-related phrases
- gender: Pronouns, gendered titles, gender-specific organizations
- ethnicity: Nationality, ethnicity mentions, ethnic organizations
- religion: Religious affiliations, faith-based activities
- disability: Disability mentions, accommodation needs
- location: Address, city, country (unless job requires specific location)
- other: Marital status, family status, political affiliation
</protected_attributes>

<compliance_rules>
1. Flag any protected attribute found in text
2. Determine if attribute is job-relevant (location may be relevant for on-site roles)
3. List attributes that MUST be ignored in evaluation
4. Assess risk level of bias entering evaluation
</compliance_rules>

<risk_levels>
- none: No protected attributes detected
- low: Protected attributes detected but clearly job-irrelevant
- medium: Some attributes could unconsciously influence evaluation
- high: Significant bias risk, manual review recommended
</risk_levels>

<output_schema>
{{
  "is_compliant": boolean,
  "flags": [
    {{
      "attribute_type": "age|gender|ethnicity|religion|disability|location|other",
      "detected_text": "string",
      "is_relevant": boolean,
      "recommendation": "string"
    }}
  ],
  "must_ignore_attributes": ["string"],
  "location_relevant": boolean,
  "compliance_notes": "string",
  "risk_level": "none|low|medium|high"
}}
</output_schema>

<resume_text>
{resume_text}
</resume_text>

<is_location_required>
{is_location_required}
</is_location_required>

Return only the JSON object, no additional text.
"""


ENHANCED_CANDIDATE_EVALUATION = """
<role>
You are a senior HR evaluator making data-driven hiring decisions with detailed scoring.
</role>

<task>
Evaluate candidate fit using normalized skill data and verified experience. Produce detailed scoring.
</task>

<scoring_formula>
skill_match_score: Use provided normalized skill match percentage (0-100)
experience_fit_score: Use provided verified experience fit score (0-100)
overall_fit_score: (skill_match_score * 0.6) + (experience_fit_score * 0.4)
</scoring_formula>

<recommendation_levels>
- Strong Hire: overall_score ≥ 85, high confidence, no compliance issues
- Hire: overall_score 70-84, good confidence
- Maybe: overall_score 50-69 OR compliance flagged
- No Hire: overall_score 30-49
- Strong No Hire: overall_score < 30 OR compliance violations
</recommendation_levels>

<decision_rules>
SELECTION CRITERIA (for Selected/Rejected status):
1. SKILL MATCH: At least 50% skill match required
2. EXPERIENCE: Must be within acceptable range (±2 years tolerance)
3. COMPLIANCE: No high-risk compliance issues

RESULT:
- "Selected": Meets minimum criteria (could still be Maybe/Hire/Strong Hire)
- "Rejected": Fails minimum criteria (No Hire/Strong No Hire)
</decision_rules>

<output_schema>
{{
  "candidate_status": "Selected|Rejected",
  "recommendation": "Strong Hire|Hire|Maybe|No Hire|Strong No Hire",
  "skill_match_score": 0-100,
  "experience_fit_score": 0-100,
  "overall_fit_score": 0-100,
  "matched_skills": ["string"],
  "missing_skills": ["string"],
  "experience_years": integer|null,
  "experience_in_range": boolean,
  "scoring_breakdown": "string explaining calculation",
  "decision_reasoning": "string explaining decision"
}}
</output_schema>

<candidate_profile>
{candidate_json}
</candidate_profile>

<job_requirements>
{jd_json}
</job_requirements>

<normalized_skills>
skill_match_percentage: {skill_match_percentage}
matched_skills: {matched_skills}
</normalized_skills>

<verified_experience>
experience_years: {experience_years}
experience_fit_score: {experience_fit_score}
verification_confidence: {verification_confidence}
</verified_experience>

<compliance_status>
is_compliant: {is_compliant}
risk_level: {risk_level}
</compliance_status>

Return only the JSON object, no additional text.
"""


GENERATE_EXPLANATION = """
<role>
You are an expert HR communicator. Generate clear, professional explanations for hiring decisions.
</role>

<task>
Create a human-readable explanation of the evaluation decision suitable for hiring managers.
</task>

<explanation_requirements>
- Write a clear one-paragraph summary
- List 3-5 key strengths
- List 2-4 gaps or concerns
- Explain the scoring breakdown in plain language
- Highlight the top factors that influenced the decision
- Provide rationale for the recommendation level
</explanation_requirements>

<tone>
- Professional and objective
- Focus on job-relevant factors only
- No mention of protected attributes
- Constructive when discussing gaps
- Confident but not absolute
</tone>

<output_schema>
{{
  "summary": "string (one paragraph)",
  "strengths": ["string"],
  "gaps": ["string"],
  "score_breakdown": {{
    "skill_match_score": 0-100,
    "skill_match_weight": 0.6,
    "skill_match_details": "string",
    "experience_fit_score": 0-100,
    "experience_fit_weight": 0.4,
    "experience_fit_details": "string",
    "overall_fit_score": 0-100,
    "calculation_formula": "string"
  }},
  "key_factors": ["string"],
  "recommendation_rationale": "string"
}}
</output_schema>

<candidate_profile>
{candidate_json}
</candidate_profile>

<job_requirements>
{jd_json}
</job_requirements>

<evaluation_result>
{evaluation_json}
</evaluation_result>

Return only the JSON object, no additional text.
"""


AGGREGATE_FINAL_RECOMMENDATION = """
<role>
You are a senior hiring decision aggregator. Synthesize all agent signals into a final recommendation.
</role>

<task>
Aggregate signals from all pipeline agents into a coherent final hiring recommendation.
</task>

<aggregation_rules>
1. Collect key findings from each agent
2. Identify consensus and conflicts
3. Weight signals by confidence level (high=1.0, medium=0.7, low=0.4)
4. Flag any compliance concerns
5. Generate final recommendation with confidence
</aggregation_rules>

<recommendation_levels>
- Strong Hire: Clear fit, high confidence across agents, no concerns
- Hire: Good fit, positive signals, minor gaps acceptable
- Maybe: Mixed signals, needs further evaluation, OR compliance review needed
- No Hire: Does not meet requirements, significant gaps
- Strong No Hire: Major disqualifiers, compliance violations, or clear misfit
</recommendation_levels>

<next_steps_by_recommendation>
- Strong Hire: ["Schedule final interview", "Prepare offer package"]
- Hire: ["Schedule technical interview", "Reference check"]
- Maybe: ["Additional screening", "Clarify specific concerns", "Team interview"]
- No Hire: ["Send rejection with feedback", "Consider for other roles"]
- Strong No Hire: ["Send standard rejection"]
</next_steps_by_recommendation>

<output_schema>
{{
  "recommendation": "Strong Hire|Hire|Maybe|No Hire|Strong No Hire",
  "overall_score": 0-100,
  "confidence": "high|medium|low",
  "candidate_name": "string",
  "candidate_email": "string|null",
  "skill_match_score": 0-100,
  "experience_fit_score": 0-100,
  "agent_signals": [
    {{
      "agent_name": "string",
      "score": 0-100|null,
      "confidence": "high|medium|low",
      "key_findings": ["string"],
      "concerns": ["string"]
    }}
  ],
  "summary": "string (executive summary)",
  "strengths": ["string"],
  "gaps": ["string"],
  "compliance_status": "string",
  "next_steps": ["string"],
  "reasoning": "string (detailed reasoning)"
}}
</output_schema>

<candidate_profile>
{candidate_json}
</candidate_profile>

<skill_normalization_result>
{skill_normalization_json}
</skill_normalization_result>

<experience_verification_result>
{experience_verification_json}
</experience_verification_result>

<compliance_result>
{compliance_json}
</compliance_result>

<evaluation_result>
{evaluation_json}
</evaluation_result>

<explanation>
{explanation_json}
</explanation>

Return only the JSON object, no additional text.
"""
