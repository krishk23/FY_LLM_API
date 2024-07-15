# main.py

import os
import tempfile
import re
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import PyPDF2 as pdf
from fpdf import FPDF
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=("AIzaSyDziGvuT1woHnH4_S3L_zQZV55Yj-123A8"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend origin if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class JDInput(BaseModel):
    jd: str

def get_gemini_response(input):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(input)
    return response

def input_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page in range(len(reader.pages)):
        page = reader.pages[page]
        text += str(page.extract_text())
    return text

input_prompt_template = """
### As a skilled Application Tracking System (ATS) with advanced knowledge in technology and data science, your role is to meticulously evaluate a candidate's resume based on the provided job description.

### Your evaluation will involve analyzing the resume for relevant skills, experiences, and qualifications that align with the job requirements. Look for key buzzwords and specific criteria outlined in the job description to determine the candidate's suitability for the position.

### Provide a detailed assessment of how well the resume matches the job requirements, highlighting strengths, weaknesses, and any potential areas of concern. Offer constructive feedback on how the candidate can enhance their resume to better align with the job description and improve their chances of securing the position.

### Your evaluation should be thorough, precise, and objective, ensuring that the most qualified candidates are accurately identified based on their resume content in relation to the job criteria.

### Parse the data of the job description and then create a list called Should do, which outlines what candidates should do for that particular position.

### Parse all CVs uploaded by candidates and create a list called Can do, which details what candidates can do.

### Now, match each candidate's Can do list with the Should do list and generate a report for each candidate, including their score and reasons for that score.

### Generate a PDF report that includes the candidate's name, matching score, Can do list, Should do list, matching and missing items from the resume, strengths highlighted, and constructive feedback on how the candidate can enhance their resume to better align with the job description and improve their chances of securing the position.

Resume: {text}
JD: {jd}
"""

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Career Metaverse Smart ATS - Evaluation Report', 0, 1, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(10)

    def chapter_body(self, body):
        for line in body.split('\n'):
            if line.startswith("**"):
                self.set_font('Arial', 'B', 12)
                self.multi_cell(0, 10, line.replace("**", "").strip())
            else:
                self.set_font('Arial', '', 12)
                self.multi_cell(0, 10, line)
        self.ln()

    def add_chapter(self, title, body):
        self.add_page()
        self.chapter_title(title)
        self.chapter_body(body)

def generate_pdf(response_content, candidate_name):
    pdf = PDF()
    pdf.add_chapter('Evaluation Output', response_content)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        pdf_output = tmp_file.name
        pdf.output(pdf_output)
    
    return pdf_output

def extract_candidate_name(response_content):
    match = re.search(r"Candidate Name:\s*(\w+\s*\w*)", response_content)
    if match:
        return match.group(1).strip()
    else:
        return "Candidate"

@app.post("/generate-report/")
async def generate_report(jd: str = Form(...), resume: UploadFile = File(...)):
    text = input_pdf_text(resume.file)
    response = get_gemini_response(input_prompt_template.format(text=text, jd=jd))
    
    response_content = response.candidates[0].content.parts[0].text
    candidate_name = extract_candidate_name(response_content)
    
    pdf_path = generate_pdf(response_content, candidate_name)
    
    return {"filename": pdf_path}
