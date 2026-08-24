import sys
import os
import pytest
import uuid
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.resume import Resume
from app.models.job import Job
from app.services.matching import MatchingEngine

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

TEST_RESUME = """
Rahul Mehta
Noida, Uttar Pradesh | +91 98765 43210 | rahul.mehta.testing@example.com | linkedin.com/in/rahulmehta-dev | github.com/rahulmehta-dev
FULL STACK DEVELOPER INTERN - FRESHER
Final-year BCA student and fresher with hands-on full-stack web development experience through academic and personal projects. Strong working knowledge of HTML5, CSS3, JavaScript, Bootstrap, PHP, MySQL, WordPress, GitHub, and VS Code. Experienced in creating responsive and mobile-friendly web pages, developing basic backend features, working with databases, fixing bugs, improving website performance, maintaining clean code, and writing basic documentation. Comfortable using ChatGPT, Claude, Cursor AI, and GitHub Copilot for coding, debugging, documentation, and AI-assisted development. Ready for an in-person internship in Noida.

TECHNICAL SKILLS
Frontend: HTML5, CSS3, JavaScript, Bootstrap, Responsive Web Design, Mobile-Friendly Web Pages | Backend: PHP | Database: MySQL | CMS: WordPress, WordPress Basics, WordPress Website Updates and Customization | Tools: GitHub, VS Code | AI-Assisted Development: ChatGPT, Claude, Cursor AI, GitHub Copilot | Practices: Debugging, Bug Fixing, Website Performance Improvement, Clean Code, Basic Documentation

PROJECT EXPERIENCE
Full Stack Website and Admin Portal - Academic Project | Noida | 2025-2026
- Created responsive and mobile-friendly web pages using HTML5, CSS3, JavaScript, and Bootstrap with layouts optimized for desktop and mobile devices.
- Developed basic backend features using PHP and connected application workflows to a MySQL database for CRUD operations, forms, authentication, and data management.
- Used GitHub for version control and VS Code for development, debugging, source-code organization, and project documentation.
- Fixed UI and backend bugs, improved website performance through cleaner code and optimized queries, and maintained basic technical documentation.

WordPress Business Website - Personal Project | Noida | 2025
- Built and customized a WordPress website, updated pages and content, adjusted themes and layouts, and applied basic WordPress website customization practices.
- Used HTML, CSS, JavaScript, and Bootstrap concepts to improve page presentation and responsiveness while troubleshooting website issues.

AI-Assisted Web Development Workflow - Personal Project | 2025
- Used ChatGPT, Claude, Cursor AI, and GitHub Copilot for coding assistance, debugging, refactoring, documentation, and learning full-stack development concepts.
- Reviewed AI-generated code before implementation, corrected errors, tested changes, and maintained clean, understandable code and basic documentation.

EDUCATION
Bachelor of Computer Applications (BCA) - Final Year | Galgotias University | 2023-2026
Eligibility: BCA fresher / final-year student | Relevant coursework: Web Development, Database Management Systems, Software Engineering

SOFT SKILLS
Problem-solving attitude | Good communication skills | Attention to detail | Teamwork | Time management | Eagerness to learn

ADDITIONAL INFORMATION
Availability: Available for a 4-month internship and ready to work from the Noida office in person. Location: Noida, Uttar Pradesh.
"""

@pytest.mark.asyncio
async def test_aryson_jd_full_match():
    resume = Resume(id=uuid.uuid4(), session_id=uuid.uuid4(), filename="resume.pdf", raw_text=TEST_RESUME)
    job = Job(id=uuid.uuid4(), session_id=uuid.uuid4(), title="Full Stack Developer Intern", raw_text=ARYSON_JD)

    engine = MatchingEngine()
    result = await engine.calculate_match_expert_llm(resume, job)

    # 1. Technical Skills Score
    assert result["sub_scores"]["skill_score"] >= 90.0, f"Technical skills score should be ~100%, got {result['sub_scores']['skill_score']}"

    # 2. Soft Skills Classification
    matched_soft = [m for m in result["matched_skills"] if m.get("category") == "SOFT"]
    missing_soft = [m for m in result["missing_skills"] if m.get("category") == "SOFT"]
    assert len(matched_soft) >= 4, f"Soft skills should be classified under SOFT category, found {len(matched_soft)} matched"
    assert len(missing_soft) == 0, f"No soft skills should be erroneously reported missing, got {missing_soft}"

    # 3. Education ANY_OF Logic (BCA satisfies B.Tech / BCA / MCA)
    matched_edu = [m for m in result["matched_skills"] if m.get("category") == "ELIGIBILITY" or "bca" in m["skill"].lower()]
    assert len(matched_edu) > 0, "BCA degree requirement should be satisfied"

    # 4. Career Stage (Fresher / Final Year)
    assert result["metrics"]["education_gate"] == "met"

    # 5. Location & Work Arrangement (Noida / In-person)
    matched_loc = [m for m in result["matched_skills"] if m.get("category") in ["LOCATION", "WORK_ARRANGEMENT"]]
    assert len(matched_loc) > 0, "Location & work arrangement requirements should be satisfied"

    # 6. AI Tools (GitHub Copilot / ChatGPT satisfies illustrative AI tool requirement)
    matched_ai = [m for m in result["matched_skills"] if m.get("category") == "AI_TOOL"]
    assert len(matched_ai) > 0, "AI tools requirement should be satisfied"

    # 7. Informational Job Data Excluded
    missing_info = [m for m in result["missing_skills"] if m.get("category") == "INFORMATIONAL"]
    assert len(missing_info) == 0, "Job metadata like stipend/duration must not appear under missing skills"

    # 8. Overall match score
    assert result["overall_score"] >= 90.0, f"Overall match score should be near 100%, got {result['overall_score']}"
