import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

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
        Consider a candidate who shows initial exposure to the skill or concept, with basic understanding and limited practical experience. They require substantial guidance and additional training to effectively use the skill in professional scenarios. This level is called Beginner.
    """,
    "Competent": """
        Evaluate a candidate who possesses a solid understanding of the skill and can independently perform tasks under standard conditions. They apply the skill effectively in routine situations, handling common problems competently, though they may need assistance with complex tasks. This level is called Competent.
    """,
    "Intermediate": """
        Assess a candidate with extensive experience and a deep understanding of the skill, proficiently applying it across various situations, including complex ones. They adapt to new challenges and solve problems with minimal supervision, though they may still encounter limitations in highly specialized areas. This level is called Intermediate.
    """,
    "Expert": """
        Identify a candidate who has mastered the skill, applying it effectively in all situations, including highly complex or specialized contexts. They are recognized as an authority, often mentoring others and shaping best practices. Their problem-solving and innovation skills are exceptional, and they require no guidance. This level is called Expert.
    """
}

# Define skill level prompts for Should Do list
should_do_prompts = {
    "Beginner": """
        Evaluate a candidate who demonstrates basic familiarity with the skill, primarily through coursework, introductory projects, or basic training. Consider any certifications or projects that indicate initial exposure. However, the candidate lacks substantial hands-on experience and requires significant guidance to effectively apply the skill in a professional setting. This level is called Beginner.
    """,
    "Competent": """
        Consider a candidate who possesses a solid understanding of the skill, demonstrated through practical experience such as internships, relevant projects, or professional work. Look for certificates, achievements, or completed projects that show their ability to apply the skill independently in routine situations. They may still require assistance with complex or unfamiliar tasks. This level is called Competent.
    """,
    "Intermediate": """
        Assess a candidate with extensive experience and a deep understanding of the skill, evidenced by significant professional experience, complex projects, or major achievements. Consider any advanced certifications, research contributions, or leadership roles that reflect their proficiency. They apply the skill across diverse and complex situations, adapting to new challenges with minimal supervision. This level is called Intermediate.
    """,
    "Expert": """
        Identify a candidate who has mastered the skill, with extensive experience in high-level roles, leadership positions, or groundbreaking projects. Look for authored research papers, prestigious awards, or contributions to best practices that signify their authority in the field. They excel in applying the skill in all situations, including highly complex contexts, often mentoring others and shaping industry standards. This level is called Expert.
    """
}

# Updated prompt template
input_prompt = """
### As a skilled Application Tracking System (ATS) with advanced knowledge in technology and data science, your role is to meticulously evaluate a candidate's resume based on the provided job description.

### Your evaluation will involve analyzing the resume for relevant skills, experiences, and qualifications that align with the job requirements. Look for key buzzwords and specific criteria outlined in the job description to determine the candidate's suitability for the position.

### Provide a detailed assessment of how well the resume matches the job requirements, highlighting strengths, weaknesses, and any potential areas of concern. Offer constructive feedback on how the candidate can enhance their resume to better align with the job description and improve their chances of securing the position.

### Your evaluation should be thorough, precise, and objective, ensuring that the most qualified candidates are accurately identified based on their resume content in relation to the job criteria.

### Remember to utilize your expertise in technology and data science to conduct a comprehensive evaluation that optimizes the recruitment process for the hiring company. Your insights will play a crucial role in determining the candidate's compatibility with the job role.

### Parse the job description and then make a list called 'Should Do' that contains what the candidate should do for that particular position, using the following levels: Beginner, Competent, Intermediate, Expert. Use the provided definitions to assign these levels.

### Parse the candidate's resume and then make a list called 'Can Do' that contains what the candidate can do, also using the following levels: Beginner, Competent, Intermediate, Expert. Use the provided definitions to assign these levels.

### Now match the candidate's 'Can Do' list with the 'Should Do' list and generate a detailed report of the fitment, including the matching score, analysis of strengths and weaknesses, missing skills, and recommendations for improvements.
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
    response = get_gemini_response(input_prompt.format(text=text, jd=jd))
    
    # Extract the raw content from the LLM response
    candidate_content = response.candidates[0].content.parts[0].text

    # Remove ** and \n from the content
    processed_content = candidate_content.replace("**", "")  # Remove bold markers
    processed_content = processed_content.replace("\\n", "\n")  # Replace escaped new lines with actual new lines
    processed_content = processed_content.replace("\n", " ")  # Remove new lines by replacing them with spaces

    return {"report": processed_content}
