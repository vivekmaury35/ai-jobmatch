import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.ai import AIService
from app.schemas.job import JobParsedData

jd_text = """
Role Summary
...
Required Skills & Qualifications
Tech / MCA (Computer Science or related fields), Batch 2026
Basic understanding of programming languages such as Java, Python, or JavaScript , tyescript
Knowledge of data structures and algorithms
Familiarity with databases (SQL/NoSQL) is a plus
Understanding of web technologies (HTML, CSS, JavaScript) is an advantage
Strong problem-solving and analytical skills
Good communication and teamwork abilities
"""

async def test():
    service = AIService()
    result = await service.extract_structured(jd_text, JobParsedData, "Job Description")
    print(result.model_dump_json())

asyncio.run(test())
