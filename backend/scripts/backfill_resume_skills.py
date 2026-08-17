from app.core.database import SessionLocal
from app.models.resume import Resume, ResumeSkill
from app.services.skill_normalizer import SkillNormalizerService


def backfill_resume_skills():
    db = SessionLocal()

    try:
        normalizer = SkillNormalizerService(db)

        resumes = db.query(Resume).all()

        print(f"Found {len(resumes)} resumes.")

        total_created = 0

        for resume in resumes:
            print()
            print("=" * 60)
            print(f"Resume: {resume.id}")
            print(f"Filename: {resume.filename}")

            parsed_data = resume.parsed_data or {}

            raw_skills = parsed_data.get("skills", [])

            if not raw_skills:
                print("No extracted skills found. Skipping.")
                continue

            print(f"Extracted skills: {raw_skills}")

            # Remove old normalized rows for this resume.
            deleted = (
                db.query(ResumeSkill)
                .filter(ResumeSkill.resume_id == resume.id)
                .delete(
                    synchronize_session=False
                )
            )

            if deleted:
                print(f"Deleted {deleted} old resume_skill rows.")

            # Re-create normalized rows.
            for raw_skill in set(raw_skills):
                skill, match_type = normalizer.normalize(raw_skill)

                normalizer.skill_repo.create_resume_skill(
                    resume_id=resume.id,
                    raw_text=raw_skill,
                    evidence_source="extracted_list",
                    confidence=1.0,
                    skill_id=skill.id if skill else None,
                )

                if skill:
                    print(
                        f"  {raw_skill!r}"
                        f" -> {skill.canonical_name!r}"
                        f" ({match_type})"
                    )
                else:
                    print(
                        f"  {raw_skill!r}"
                        f" -> free-text"
                    )

                total_created += 1

            db.commit()

        print()
        print("=" * 60)
        print(
            f"Backfill complete. Created "
            f"{total_created} resume skill rows."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    backfill_resume_skills()