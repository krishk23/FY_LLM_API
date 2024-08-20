import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import json

# Load environment variables
load_dotenv()

# Configure the API key for generative AI
genai.configure(api_key=("AIzaSyDziGvuT1woHnH4_S3L_zQZV55Yj-123A8"))

# Initialize FastAPI
app = FastAPI()

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Convert PDF to text
def input_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page in range(len(reader.pages)):
        page = reader.pages[page]
        text += str(page.extract_text())
    return text

# Define skill level prompts for Can Do list
can_do_prompts = {
    "Beginner": """
        Evaluate the candidate's listed skills for initial exposure, basic understanding, and limited practical experience. This level is for those who need substantial guidance to use the skill in professional scenarios. Assign this level as Beginner.
    """,
    "Competent": """
        Evaluate the candidate's skills for solid understanding and ability to independently perform tasks under standard conditions. They should handle common problems competently but might need assistance with complex tasks. Assign this level as Competent.
    """,
    "Intermediate": """
        Evaluate the candidate's skills for extensive experience, deep understanding, and proficiency in applying the skill across various situations, including complex ones. They adapt to new challenges with minimal supervision. Assign this level as Intermediate.
    """,
    "Expert": """
        Evaluate the candidate's skills for mastery, applying the skill effectively in all situations, including highly complex contexts. They are recognized as an authority, often mentoring others and shaping best practices. Assign this level as Expert.
    """
}

# Define skill level prompts for Should Do list
should_do_prompts = {
    "Beginner": """
        Evaluate the job description to identify skills that require basic familiarity, primarily through coursework, introductory projects, or basic training. The candidate should have initial exposure but will likely need significant guidance. Assign this level as Beginner.
    """,
    "Competent": """
        Evaluate the job description to identify skills requiring solid understanding, demonstrated through practical experience such as internships, relevant projects, or professional work. The candidate should be able to apply the skill independently in routine situations. Assign this level as Competent.
    """,
    "Intermediate": """
        Evaluate the job description to identify skills requiring extensive experience and deep understanding, reflected by significant professional work, complex projects, or major achievements. The candidate should apply the skill across diverse and complex situations. Assign this level as Intermediate.
    """,
    "Expert": """
        Evaluate the job description to identify skills requiring mastery, evidenced by high-level roles, leadership positions, or groundbreaking projects. The candidate should be able to apply the skill in all situations, including highly complex contexts. Assign this level as Expert.
    """
}

# Mapping levels to scores
level_scores = {
    "Beginner": 1,
    "Competent": 2,
    "Intermediate": 3,
    "Expert": 4
}

# Updated prompt template
input_prompt = """
### As an advanced Application Tracking System (ATS) with expertise in technology and data science, evaluate the candidate's resume against the provided job description.

### Steps:
1. **Parse the job description** and create a 'Should Do' list, categorizing required skills into levels: Beginner, Competent, Intermediate, Expert, using the following definitions: 
{should_do_prompts}
2. **Parse the candidate's resume** and create a 'Can Do' list, categorizing listed skills into the same levels: Beginner, Competent, Intermediate, Expert, using the following definitions:
{can_do_prompts}
3. **Compare the 'Can Do' list with the 'Should Do' list** and generate a matching score based on how well the skill levels align.
4. **Generate a detailed report** that includes the 'Can Do' list, 'Should Do' list, matching score, analysis of strengths and weaknesses, missing skills, and recommendations for improvement.

resume = {text}
jd = {jd}
"""

# Function to get the response from the Gemini AI model
def get_gemini_response(input):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(input)
    return response

# API endpoint to generate the report
@app.post("/generate-report/")
async def generate_report(
    jd: str = Form(...),
    resume: UploadFile = File(...)
):
    text = input_pdf_text(resume.file)
    
    # Inject the appropriate prompts into the template
    response = get_gemini_response(
        input_prompt.format(
            text=text,
            jd=jd,
            can_do_prompts=json.dumps(can_do_prompts, indent=4),
            should_do_prompts=json.dumps(should_do_prompts, indent=4)
        )
    )
    
    # Extract the raw content from the LLM response
    candidate_content = response.candidates[0].content.parts[0].text

    # Process the response to extract key-value pairs for Can Do and Should Do lists
    can_do_list = []
    should_do_list = []

    # Example of extracting and formatting skills and levels (This should be tailored to the actual LLM response format)
    for line in candidate_content.splitlines():
        if "Can Do:" in line:
            skill, level = line.replace("Can Do:", "").split(" - ")
            can_do_list.append({"skill": skill.strip(), "level": level.strip()})
        elif "Should Do:" in line:
            skill, level = line.replace("Should Do:", "").split(" - ")
            should_do_list.append({"skill": skill.strip(), "level": level.strip()})

    # Calculate the total possible score
    max_score_per_skill = 100
    total_max_score = len(should_do_list) * max_score_per_skill

    # Generate the matching score based on the comparison of Can Do and Should Do lists
    total_matching_score = 0
    
    for should_do in should_do_list:
        for can_do in can_do_list:
            if should_do["skill"] == can_do["skill"]:
                # Calculate the match percentage based on the difference in levels
                level_difference = abs(level_scores[should_do["level"]] - level_scores[can_do["level"]])
                
                if level_difference == 0:
                    match_percentage = 100  # Exact match
                elif level_difference == 1:
                    match_percentage = 75   # One level difference
                elif level_difference == 2:
                    match_percentage = 50   # Two levels difference
                elif level_difference == 3:
                    match_percentage = 25   # Three levels difference
                
                total_matching_score += match_percentage
                break

    # Convert the total matching score to a percentage out of 100
    matching_percentage = (total_matching_score / total_max_score) * 100

    # Format the output to show the skills with levels side by side
    formatted_output = "Comparison of 'Can Do' and 'Should Do' Lists:\n"
    formatted_output += f"{'Skill':<30} {'Can Do Level':<20} {'Should Do Level':<20}\n"
    formatted_output += "-" * 70 + "\n"
    
    for should_do in should_do_list:
        skill_name = should_do["skill"]
        should_do_level = should_do["level"]
        can_do_level = next((can_do["level"] for can_do in can_do_list if can_do["skill"] == skill_name), "N/A")
        formatted_output += f"{skill_name:<30} {can_do_level:<20} {should_do_level:<20}\n"

    # Return the processed report with lists, matching percentage, and formatted output
    return {
        "can_do_list": can_do_list,
        "should_do_list": should_do_list,
        "matching_percentage": matching_percentage,
        "report": formatted_output
    }
