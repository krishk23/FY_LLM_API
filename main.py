import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
from fpdf import FPDF
import tempfile
import re
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

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

### Generate one pdf which contains Candidate name ,matching score ,can do list , should do list,matching and missing from resume,highlighting strengths,Offer constructive feedback on how the condidate can enhance their resume to better align with the job description and improve their chances of securing the position and it should be the sequence of score card content.
resume = {text}
jd = {jd}
"""

# Function to generate PDF
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

# Extract candidate's name from the response content
def extract_candidate_name(response_content):
    match = re.search(r"Candidate Name:\s*(\w+\s*\w*)", response_content)
    if match:
        return match.group(1).strip()
    else:
        return "Candidate"

@app.post("/generate-report/")
async def generate_report(
    jd: str = Form(...),
    resume: UploadFile = File(...)
):
    text = input_pdf_text(resume.file)
    response = genai.generate_content(input_prompt.format(text=text, jd=jd))
    
    response_content = response.candidates[0].content.parts[0].text
    candidate_name = extract_candidate_name(response_content)
    
    pdf_path = generate_pdf(response_content, candidate_name)
    
    return FileResponse(pdf_path, filename=f"{candidate_name}_evaluation_report.pdf")
