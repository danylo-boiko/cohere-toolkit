import datetime

from pydantic import BaseModel, Field


class MessageFeedback(BaseModel):
    """
    Schema for message feedback.
    """
    id: str = Field(
        ...,
        title="ID",
        description="The unique identifier of the message feedback.",
    )
    created_at: datetime.datetime = Field(
        ...,
        title="Created At",
        description="The timestamp when the feedback was created.",
    )
    updated_at: datetime.datetime = Field(
        ...,
        title="Updated At",
        description="The timestamp when the feedback was last updated.",
    )
    message_id: str = Field(
        ...,
        title="Message ID",
        description="The unique identifier of the message.",
    )
    start_index: int = Field(
        ...,
        title="Start Index",
        description="The starting position (inclusive) of the rated text segment in the message.",
    )
    end_index: int = Field(
        ...,
        title="End Index",
        description="The ending position (inclusive) of the rated text segment in the message.",
    )
    rating: int = Field(
        ...,
        title="Rating",
        description="The numerical score representing the feedback for the text segment.",
    )


class CreateMessageFeedbackRequest(BaseModel):
    """
    Request schema for providing feedback on a specific part of a message.
    """
    message_id: str = Field(
        ...,
        title="Message ID",
        description="The unique identifier of the message.",
    )
    start_index: int = Field(
        ...,
        title="Start Index",
        description="The starting position (inclusive) of the rated text segment in the message.",
    )
    end_index: int = Field(
        ...,
        title="End Index",
        description="The ending position (inclusive) of the rated text segment in the message.",
    )
    rating: int = Field(
        ...,
        title="Rating",
        description="The numerical score representing the feedback for the text segment.",
    )
