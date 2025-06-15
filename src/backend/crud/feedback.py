from sqlalchemy.orm import Session

from backend.database_models import MessageFeedback
from backend.services.transaction import validate_transaction


@validate_transaction
def create_message_feedback(db: Session, message_feedback: MessageFeedback) -> MessageFeedback:
    """
    Create a new message feedback.

    Args:
        db (Session): Database session.
        message_feedback (MessageFeedback): Message feedback to be created.

    Returns:
        MessageFeedback: Created message feedback.
    """
    db.add(message_feedback)
    db.commit()
    db.refresh(message_feedback)
    return message_feedback
