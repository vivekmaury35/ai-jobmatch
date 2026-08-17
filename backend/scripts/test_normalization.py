import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.skill_normalizer import SkillNormalizerService

def test_normalization():
    db: Session = SessionLocal()
    normalizer = SkillNormalizerService(db)

    print("=== Testing Database Preloading ===")
    print(f"Loaded {len(normalizer.searchable_strings)} searchable strings from DB into fuzzy dictionary.")

    print("\n=== Testing Normalization Cases ===")

    test_cases = [
        "python",        # 1. Exact canonical name match
        "postgres",      # 2. Exact alias match
        "Postgre SQL",   # 3. Fuzzy match (spelling variation mapping to an alias)
        "next js",       # 4. Fuzzy match
        "random stuff",  # 5. Free-text fallback (No DB Match)
    ]

    for raw in test_cases:
        skill_obj, match_type = normalizer.normalize(raw)

        print(f"Raw Input: '{raw}'")
        if skill_obj:
            print(f"  -> Match Type: {match_type}")
            print(f"  -> Canonical Value: '{skill_obj.canonical_name}' (Display: {skill_obj.display_name})")
        else:
            print(f"  -> Match Type: {match_type}")
            print(f"  -> Saved as raw unassociated text.")
        print("-" * 30)

    db.close()

if __name__ == "__main__":
    test_normalization()
