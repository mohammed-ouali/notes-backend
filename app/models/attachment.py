from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(primary_key=True)

    note_id: Mapped[int] = mapped_column(ForeignKey("notes.id", ondelete="CASCADE"), index = True)

    file_name: Mapped[str] = mapped_column(String(255))

    object_key: Mapped[str] = mapped_column(String(255), unique=True)

    content_type: Mapped[str] = mapped_column(String(255))

    size_bytes: Mapped[int] = mapped_column()

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    note: Mapped["Note"] = relationship(back_populates="attachments")