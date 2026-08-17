from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid

from app.core.database import Base

class Skill(Base):
    __tablename__ = "skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canonical_name = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String, nullable=False)
    aliases = Column(ARRAY(String), default=[])
    category = Column(String, nullable=True)
