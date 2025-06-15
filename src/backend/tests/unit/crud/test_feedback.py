import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.crud import feedback as feedback_crud
from backend.database_models import Message, User
from backend.database_models.feedback import MessageFeedback
from backend.tests.unit.factories import get_factory


@pytest.fixture(autouse=True)
def message(session: Session, user: User) -> Message:
    conversation = get_factory("Conversation", session).create(
        id="1", user_id=user.id,
    )

    return get_factory("Message", session).create(
        id="1", text="Hello, World!", user_id=user.id, conversation_id=conversation.id,
    )


def test_create_message_feedback(
    session: Session, message: Message, user: User
) -> None:
    message_feedback = MessageFeedback(
        message_id=message.id,
        user_id=user.id,
        start_index=0,
        end_index=5,
        rating=4
    )

    created_message_feedback = feedback_crud.create_message_feedback(session, message_feedback)

    assert created_message_feedback.message_id == message_feedback.message_id
    assert created_message_feedback.user_id == message_feedback.user_id
    assert created_message_feedback.start_index == message_feedback.start_index
    assert created_message_feedback.end_index == message_feedback.end_index
    assert created_message_feedback.rating == message_feedback.rating

    session.expunge(created_message_feedback)

    assert session.get(MessageFeedback, created_message_feedback.id) is not None


def test_fail_create_message_feedback_with_invalid_indices(
    session: Session, message: Message, user: User
) -> None:
    message_feedback = MessageFeedback(
        message_id=message.id,
        user_id=user.id,
        start_index=10,
        end_index=5,
        rating=4
    )

    with pytest.raises(IntegrityError):
        feedback_crud.create_message_feedback(session, message_feedback)


def test_fail_create_message_feedback_with_negative_start_index(
    session: Session, message: Message, user: User
) -> None:
    message_feedback = MessageFeedback(
        message_id=message.id,
        user_id=user.id,
        start_index=-1,
        end_index=5,
        rating=1,
    )

    with pytest.raises(IntegrityError):
        feedback_crud.create_message_feedback(session, message_feedback)


def test_fail_create_message_feedback_with_nonexistent_message(
    session: Session, user: User
) -> None:
    message_feedback = MessageFeedback(
        message_id="nonexistent_message",
        user_id=user.id,
        start_index=0,
        end_index=5,
        rating=3,
    )

    with pytest.raises(IntegrityError):
        feedback_crud.create_message_feedback(session, message_feedback)


def test_fail_create_message_feedback_with_nonexistent_user(
    session: Session, message: Message
) -> None:
    message_feedback = MessageFeedback(
        message_id=message.id,
        user_id="nonexistent_user",
        start_index=0,
        end_index=5,
        rating=3,
    )

    with pytest.raises(IntegrityError):
        feedback_crud.create_message_feedback(session, message_feedback)
