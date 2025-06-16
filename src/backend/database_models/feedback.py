from sqlalchemy import CheckConstraint, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from backend.database_models.base import Base


class MessageFeedback(Base):
    __tablename__ = "message_feedback"

    message_id: Mapped[str] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    start_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    end_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    __table_args__ = (
        CheckConstraint("start_index >= 0", name="check_start_index_positive"),
        CheckConstraint("end_index >= start_index", name="check_end_index_gte_start_index"),
    )
