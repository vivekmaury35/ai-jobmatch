import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pymupdf as fitz
import json
from app.models.resume import Resume
from app.models.job import Job
from app.services.matching import MatchingEngine
import uuid

ARYSON_JD = """
Job Title: Full Stack Developer Intern - Fresher

Company: Aryson Technologies
Location: Noida
Duration: 4 Months
Stipend: Up to ₹8,000 per month
Eligibility: B.Tech / BCA / MCA freshers or final-year students

About Aryson Technologies

Aryson Technologies is a Noida-based software company working in data recovery, email migration, cloud migration, database backup, and email backup solutions. Our products are used by customers worldwide.

Full Stack Developer Intern

Job Summary

We are looking for a full stack developer intern who has basic knowledge of web development and wants to work on real software and website projects.

This role is suitable for freshers who are eager to learn frontend, backend, database, WordPress, and AI-assisted development.

Key Responsibilities

* Create responsive and mobile-friendly web pages
* Work with HTML, CSS, JavaScript, and Bootstrap
* Develop basic backend features using PHP
* Work with MySQL databases
* Assist in WordPress website updates and customization
* Fix bugs and improve website performance
* Use GitHub and VS Code for development work
* Use AI tools like ChatGPT, Claude, Cursor AI, or GitHub Copilot for coding, debugging, and documentation
* Maintain clean code and basic documentation

Required Skills

* HTML5
* CSS3
* JavaScript
* Bootstrap
* PHP
* MySQL
* WordPress basics
* GitHub
* VS Code

Soft Skills

* Problem-solving attitude
* Good communication skills
* Attention to detail
* Teamwork
* Time management
* Eagerness to learn

Who Should Apply

* Freshers who have basic coding knowledge
* Candidates who want to become Full Stack Developers
* Candidates ready to work from the Noida office

Work Location: In person
"""

async def run_test():
    pdf_path = r"C:\Users\91991\Downloads\Aryson_Full_Stack_Developer_Intern_ATS_Test_Resume.pdf"
    doc = fitz.open(pdf_path)
    resume_text = "".join(p.get_text() for p in doc)
    
    resume = Resume(
        id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        filename="Aryson_Test_Resume.pdf",
        raw_text=resume_text
    )
    
    job = Job(
        id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        title="Full Stack Developer Intern",
        raw_text=ARYSON_JD
    )
    
    engine = MatchingEngine()
    result = await engine.calculate_match_expert_llm(resume, job)
    
    print("=== RESULT START ===")
    print(json.dumps(result, indent=2))
    print("=== RESULT END ===")

if __name__ == "__main__":
    asyncio.run(run_test())
