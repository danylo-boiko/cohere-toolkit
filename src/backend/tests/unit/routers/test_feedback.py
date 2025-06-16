import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.database_models import Message
from backend.database_models.user import User
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
    session_client: TestClient, session: Session, message: Message
) -> None:
    request_json = {
        "message_id": message.id,
        "start_index": 0,
        "end_index": 10,
        "rating": 5,
    }

    response = session_client.post(
        "/v1/feedback/message",
        json=request_json,
        headers={"User-Id": message.user_id}
    )

    assert response.status_code == 200

    message_feedback = response.json()

    assert message_feedback["message_id"] == request_json["message_id"]
    assert message_feedback["start_index"] == request_json["start_index"]
    assert message_feedback["end_index"] == request_json["end_index"]
    assert message_feedback["rating"] == request_json["rating"]


def test_fail_create_message_feedback_message_not_found(
    session_client: TestClient, user: User
) -> None:
    request_json = {
        "message_id": "nonexistent_message",
        "start_index": 0,
        "end_index": 10,
        "rating": 5,
    }

    response = session_client.post(
        "/v1/feedback/message",
        json=request_json,
        headers={"User-Id": user.id},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "The message does not exist or belongs to another user."


def test_fail_create_message_feedback_end_index_out_of_range(
    session_client: TestClient, session: Session, message: Message
) -> None:
    request_json = {
        "message_id": message.id,
        "start_index": 0,
        "end_index": 100,
        "rating": 5,
    }

    response = session_client.post(
        "/v1/feedback/message",
        json=request_json,
        headers={"User-Id": message.user_id}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "The end index is out of range."


def test_fail_create_message_feedback_invalid_payload(
    session_client: TestClient, user: User
) -> None:
    request_json = {
        "message_id": "1",
        "start_index": 0,
        "end_index": 10,
    }

    response = session_client.post(
        "/v1/feedback/message",
        json=request_json,
        headers={"User-Id": user.id},
    )

    assert response.status_code == 422
