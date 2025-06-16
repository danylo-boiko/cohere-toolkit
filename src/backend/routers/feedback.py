from fastapi import APIRouter, Depends, HTTPException

from backend.config.routers import RouterName
from backend.crud import feedback as feedback_crud
from backend.crud import message as message_crud
from backend.database_models import DBSessionDep, MessageFeedback
from backend.schemas.context import Context
from backend.schemas.feedback import CreateMessageFeedbackRequest
from backend.schemas.feedback import MessageFeedback as MessageFeedbackSchema
from backend.services.context import get_context

router = APIRouter(
    prefix="/v1/feedback",
    tags=[RouterName.FEEDBACK],
)

router.name = RouterName.FEEDBACK


@router.post("/message", response_model=MessageFeedbackSchema)
def create_message_feedback(
    request: CreateMessageFeedbackRequest,
    session: DBSessionDep,
    ctx: Context = Depends(get_context),
) -> MessageFeedbackSchema:
    """
    Create a new message feedback.

    Raises:
        HTTPException: If the message with the given ID does not exist or belongs to another user.
    """
    user_id = ctx.get_user_id()

    message = message_crud.get_message(session, request.message_id, user_id)

    if not message:
        raise HTTPException(status_code=404, detail="The message does not exist or belongs to another user.")

    if request.end_index >= len(message.text):
        raise HTTPException(status_code=400, detail="The end index is out of range.")

    message_feedback = MessageFeedback(
        message_id=message.id,
        user_id=ctx.get_user_id(),
        start_index=request.start_index,
        end_index=request.end_index,
        rating=request.rating,
    )

    return feedback_crud.create_message_feedback(session, message_feedback)
