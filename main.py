



import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import json
import re

load_dotenv()

genai.configure(api_key=("AIzaSyDziGvuT1woHnH4_S3L_zQZV55Yj-123A8"))

app = FastAPI()

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

# Prompt template
input_prompt = """
### As a skilled Application Tracking System(ATS) with advanced knowledge in technology and data science . your role is to meticulously evaluate a candidate's resume based on the provided job description.

### Your evaluation will involve analyzing the resume for relevant skills , experiences, and qualifications that align with the job requirements.Look for key buzzwords and specific criteria outlined in the  job description to determine the  candidate's suitability for the position.

### Provide a detailed assessment of how well the resume matches the job requiremnets ,highlighting strengths , weaknesses and any potential area of concern. Offer constructive feedback on how the condidate can enhance their resume to better align with the job description and improve their chances of securing the position.

### Your evaluation should be through, precise and objective,ensuring that the most qualified candidates are accurately identified based on their resume content in relation to the job criteria.

### Remember to utilize your expertise in technology and data science to conduct a comprehensive evaluation that optimizes the recruitment process for the hiring company. your insights will play a crucial role in determining the candidate's compatibility with the job role.

### parse data of job description and then make one list called Should do that is what candidate should do for that particular position. 

### parse all CV of all candidates one time uploaded and then create one list called can do that is what candidate do. 

### Now You should match all candidates can do generated list with should do list and give the report of each candidate with it's score and reasons of that score. 

### Generate one text report which contains Candidate name ,matching score ,can do list , should do list,matching and missing from resume,highlighting strengths,Offer constructive feedback on how the condidate can enhance their resume to better align with the job description and improve their chances of securing the position and it should be the sequence of score card content.
resume = {text}
jd = {jd}
"""

def get_gemini_response(input):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(input)
    return response

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
