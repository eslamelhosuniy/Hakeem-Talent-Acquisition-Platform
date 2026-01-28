from string import Template

# System prompts for talent platform
system_prompt = Template("""
You are an AI assistant for a talent platform that helps companies find the right candidates
and helps candidates find the right opportunities. You analyze resumes, job descriptions,
and provide intelligent matching recommendations.
""")

# Resume analysis prompt
resume_analysis = Template("""
Analyze the following resume and extract key information:

Resume:
$resume_text

Please extract:
1. Skills (technical and soft skills)
2. Experience summary
3. Education
4. Key achievements
5. Suggested job categories

Respond in JSON format.
""")

# Job matching prompt
job_matching = Template("""
Given the following candidate profile and job requirements, provide a matching analysis:

Candidate Profile:
$candidate_profile

Job Requirements:
$job_requirements

Analyze:
1. Match score (0-100)
2. Matching skills
3. Missing skills
4. Overall recommendation
""")

# Semantic search query refinement
search_refinement = Template("""
Refine the following job search query for semantic search:

Original Query: $query

Provide an enhanced query that captures the intent and related concepts.
""")
