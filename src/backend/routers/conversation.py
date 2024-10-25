from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi import File as RequestFile
from fastapi import UploadFile as FastAPIUploadFile
from starlette.responses import Response

from backend.chat.custom.utils import get_deployment
from backend.config.routers import RouterName
from backend.crud import agent as agent_crud
from backend.crud import conversation as conversation_crud
from backend.crud import message as message_crud
from backend.database_models import Conversation as ConversationModel
from backend.database_models.database import DBSessionDep
from backend.schemas.agent import Agent
from backend.schemas.context import Context
from backend.schemas.conversation import (
    ConversationPublic,
    ConversationWithoutMessages,
    DeleteConversationResponse,
    GenerateTitleResponse,
    ToggleConversationPinRequest,
    UpdateConversationRequest,
)
from backend.schemas.file import (
    ConversationFileFull,
    DeleteConversationFileResponse,
    ListConversationFile,
    UploadConversationFileResponse,
)
from backend.services.agent import validate_agent_exists
from backend.services.context import get_context
from backend.services.conversation import (
    filter_conversations,
    generate_conversation_title,
    get_documents_to_rerank,
    get_messages_with_files,
    validate_conversation,
)
from backend.services.file import (
    attach_conversation_id_to_files,
    get_file_service,
    validate_file,
)
from backend.services.synthesizer import synthesize

router = APIRouter(
    prefix="/v1/conversations",
)
router.name = RouterName.CONVERSATION


# CONVERSATIONS
@router.get("/{conversation_id}", response_model=ConversationPublic)
async def get_conversation(
    conversation_id: str,
    session: DBSessionDep,
    request: Request,
    ctx: Context = Depends(get_context),
) -> ConversationPublic:
    """
    Get a conversation by ID.

    Args:
        conversation_id (str): Conversation ID.
        session (DBSessionDep): Database session.
        request (Request): Request object.

    Returns:
        ConversationPublic: Conversation with the given ID.

    Raises:
        HTTPException: If the conversation with the given ID is not found.
    """
    user_id = ctx.get_user_id()
    conversation = conversation_crud.get_conversation(
        session, conversation_id, user_id)

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation with ID: {conversation_id} not found.",
        )

    files = get_file_service().get_files_by_conversation_id(
        session, user_id, conversation.id, ctx
    )
    files_with_conversation_id = attach_conversation_id_to_files(
        conversation.id, files)
    messages = get_messages_with_files(
        session, user_id, conversation.messages, ctx)
    _ = validate_conversation(session, conversation_id, user_id)

    conversation = ConversationPublic(
        id=conversation.id,
        user_id=user_id,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        title=conversation.title,
        messages=messages,
        files=files_with_conversation_id,
        description=conversation.description,
        agent_id=conversation.agent_id,
        organization_id=conversation.organization_id,
        is_pinned=conversation.is_pinned,
    )

    _ = validate_conversation(session, conversation_id, user_id)
    return conversation


@router.get("", response_model=list[ConversationWithoutMessages])
async def list_conversations(
    *,
    offset: int = 0,
    limit: int = 100,
    order_by: str = None,
    agent_id: str = None,
    session: DBSessionDep,
    request: Request,
    ctx: Context = Depends(get_context),
) -> list[ConversationWithoutMessages]:
    """
    List all conversations.

    Args:
        offset (int): Offset to start the list.
        limit (int): Limit of conversations to be listed.
        order_by (str): A field by which to order the conversations.
        agent_id (str): Query parameter for agent ID to optionally filter conversations by agent.
        session (DBSessionDep): Database session.
        request (Request): Request object.

    Returns:
        list[ConversationWithoutMessages]: List of conversations.
    """
    user_id = ctx.get_user_id()

    conversations = conversation_crud.get_conversations(
        session, offset=offset, limit=limit, order_by=order_by, user_id=user_id, agent_id=agent_id
    )

    results = []
    for conversation in conversations:
        files = get_file_service().get_files_by_conversation_id(
            session, user_id, conversation.id, ctx
        )
        files_with_conversation_id = attach_conversation_id_to_files(
            conversation.id, files
        )
        results.append(
            ConversationWithoutMessages(
                id=conversation.id,
                user_id=user_id,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
                title=conversation.title,
                files=files_with_conversation_id,
                description=conversation.description,
                agent_id=conversation.agent_id,
                messages=[],
                organization_id=conversation.organization_id,
                is_pinned=conversation.is_pinned,
            )
        )

    return results


@router.put("/{conversation_id}", response_model=ConversationPublic)
async def update_conversation(
    conversation_id: str,
    new_conversation: UpdateConversationRequest,
    session: DBSessionDep,
    ctx: Context = Depends(get_context),
) -> ConversationPublic:
    """
    Update a conversation by ID.

    Args:
        conversation_id (str): Conversation ID.
        new_conversation (UpdateConversationRequest): New conversation data.
        session (DBSessionDep): Database session.
        ctx (Context): Context object.

    Returns:
        ConversationPublic: Updated conversation.

    Raises:
        HTTPException: If the conversation with the given ID is not found.
    """
    user_id = ctx.get_user_id()
    conversation = validate_conversation(session, conversation_id, user_id)
    conversation = conversation_crud.update_conversation(
        session, conversation, new_conversation
    )

    files = get_file_service().get_files_by_conversation_id(
        session, user_id, conversation.id, ctx
    )
    messages = get_messages_with_files(
        session, user_id, conversation.messages, ctx)
    files_with_conversation_id = attach_conversation_id_to_files(
        conversation.id, files)
    return ConversationPublic(
        id=conversation.id,
        user_id=user_id,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        title=conversation.title,
        messages=messages,
        files=files_with_conversation_id,
        description=conversation.description,
        agent_id=conversation.agent_id,
        organization_id=conversation.organization_id,
        is_pinned=conversation.is_pinned,
    )


@router.put("/{conversation_id}/toggle-pin", response_model=ConversationWithoutMessages)
async def toggle_conversation_pin(
    conversation_id: str,
    new_conversation_pin: ToggleConversationPinRequest,
    session: DBSessionDep,
    ctx: Context = Depends(get_context),
) -> ConversationWithoutMessages:
    user_id = ctx.get_user_id()
    conversation = validate_conversation(session, conversation_id, user_id)
    conversation = conversation_crud.toggle_conversation_pin(
        session, conversation, new_conversation_pin
    )
    files = get_file_service().get_files_by_conversation_id(
        session, user_id, conversation.id, ctx
    )
    files_with_conversation_id = attach_conversation_id_to_files(
        conversation.id, files
    )
    return ConversationWithoutMessages(
        id=conversation.id,
        user_id=user_id,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        title=conversation.title,
        files=files_with_conversation_id,
        description=conversation.description,
        agent_id=conversation.agent_id,
        messages=[],
        organization_id=conversation.organization_id,
        is_pinned=conversation.is_pinned,
    )


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str, session: DBSessionDep, ctx: Context = Depends(get_context)
) -> DeleteConversationResponse:
    """
    Delete a conversation by ID.

    Args:
        conversation_id (str): Conversation ID.
        session (DBSessionDep): Database session.
        ctx (Context): Context object.

    Returns:
        DeleteConversationResponse: Empty response.

    Raises:
        HTTPException: If the conversation with the given ID is not found.
    """
    user_id = ctx.get_user_id()
    conversation = validate_conversation(session, conversation_id, user_id)

    get_file_service().delete_all_conversation_files(
        session, conversation.id, conversation.file_ids, user_id, ctx
    )
    conversation_crud.delete_conversation(session, conversation_id, user_id)

    return DeleteConversationResponse()


@router.get(":search", response_model=list[ConversationWithoutMessages])
async def search_conversations(
    query: str,
    session: DBSessionDep,
    request: Request,
    offset: int = 0,
    limit: int = 100,
    agent_id: str = None,
    ctx: Context = Depends(get_context),
) -> list[ConversationWithoutMessages]:
    """
    Search conversations by title.

    Args:
        query (str): Query string to search for in conversation titles.
        session (DBSessionDep): Database session.
        request (Request): Request object.
        offset (int): Offset to start the list.
        limit (int): Limit of conversations to be listed.
        agent_id (str): Query parameter for agent ID to optionally filter conversations by agent.
        ctx (Context): Context object.

    Returns:
        list[ConversationWithoutMessages]: List of conversations that match the query.
    """
    user_id = ctx.get_user_id()
    deployment_name = ctx.get_deployment_name()
    model_deployment = get_deployment(deployment_name, ctx)

    agent = None
    if agent_id:
        agent = validate_agent_exists(session, agent_id, user_id)

    if agent_id:
        agent_schema = Agent.model_validate(agent)
        ctx.with_agent(agent_schema)

    conversations = conversation_crud.get_conversations(
        session, offset=offset, limit=limit, user_id=user_id, agent_id=agent_id
    )

    if not conversations:
        return []

    rerank_documents = get_documents_to_rerank(conversations)
    filtered_documents = await filter_conversations(
        query,
        conversations,
        rerank_documents,
        model_deployment,
        ctx,
    )

    results = []
    for conversation in filtered_documents:
        files = get_file_service().get_files_by_conversation_id(
            session, user_id, conversation.id, ctx
        )
        files_with_conversation_id = attach_conversation_id_to_files(
            conversation.id, files
        )
        results.append(
            ConversationWithoutMessages(
                id=conversation.id,
                user_id=user_id,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
                title=conversation.title,
                files=files_with_conversation_id,
                description=conversation.description,
                agent_id=conversation.agent_id,
                messages=[],
                organization_id=conversation.organization_id,
                is_pinned=conversation.is_pinned,
            )
        )
    return results


# FILES
@router.post("/batch_upload_file", response_model=list[UploadConversationFileResponse])
async def batch_upload_file(
    session: DBSessionDep,
    conversation_id: str = Form(None),
    files: list[FastAPIUploadFile] = RequestFile(...),
    ctx: Context = Depends(get_context),
) -> UploadConversationFileResponse:
    """
    Uploads and creates a batch of File object.
    If no conversation_id is provided, a new Conversation is created as well.

    Args:
        session (DBSessionDep): Database session.
        conversation_id (Optional[str]): Conversation ID passed from request query parameter.
        files (list[FastAPIUploadFile]): List of files to be uploaded.
        ctx (Context): Context object.

    Returns:
        list[UploadConversationFileResponse]: List of uploaded files.

    Raises:
        HTTPException: If the conversation with the given ID is not found. Status code 404.
        HTTPException: If the file wasn't uploaded correctly. Status code 500.
    """

    user_id = ctx.get_user_id()

    # Create new conversation
    if not conversation_id:
        conversation = conversation_crud.create_conversation(
            session,
            ConversationModel(user_id=user_id),
        )
    # Check for existing conversation
    else:
        conversation = conversation_crud.get_conversation(
            session, conversation_id, user_id
        )

        # Fail if user_id is not provided when conversation DNE
        if not conversation:
            if not user_id:
                raise HTTPException(
                    status_code=400,
                    detail="user_id is required if no valid conversation is provided.",
                )

            # Create new conversation
            conversation = conversation_crud.create_conversation(
                session,
                ConversationModel(user_id=user_id),
            )

    # TODO: check if file already exists in DB once we have files per agents

    try:
        uploaded_files = await get_file_service().create_conversation_files(
            session,
            files,
            user_id,
            conversation.id,
            ctx,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error while uploading file(s): {e}."
        )

    files_with_conversation_id = attach_conversation_id_to_files(
        conversation.id, uploaded_files
    )
    return files_with_conversation_id


@router.get("/{conversation_id}/files", response_model=list[ListConversationFile])
async def list_files(
    conversation_id: str, session: DBSessionDep, ctx: Context = Depends(get_context)
) -> list[ListConversationFile]:
    """
    List all files from a conversation. Important - no pagination support yet.

    Args:
        conversation_id (str): Conversation ID.
        session (DBSessionDep): Database session.
        ctx (Context): Context object.

    Returns:
        list[ListConversationFile]: List of files from the conversation.

    Raises:
        HTTPException: If the conversation with the given ID is not found.
    """
    user_id = ctx.get_user_id()
    _ = validate_conversation(session, conversation_id, user_id)

    files = get_file_service().get_files_by_conversation_id(
        session, user_id, conversation_id, ctx
    )
    files_with_conversation_id = attach_conversation_id_to_files(
        conversation_id, files)
    return files_with_conversation_id


@router.get("/{conversation_id}/files/{file_id}", response_model=ConversationFileFull)
async def get_file(
    conversation_id: str, file_id: str, session: DBSessionDep, ctx: Context = Depends(get_context)
) -> ConversationFileFull:
    """
    Get a file by ID.

    Args:
        conversation_id (str): Conversation ID.
        file_id (str): File ID.
        session (DBSessionDep): Database session.
        ctx (Context): Context object.

    Returns:
        ConversationFileFull: File with the given ID.

    Raises:
        HTTPException: If the conversation or file with the given ID is not found, or if the file does not belong to the conversation.
    """
    user_id = ctx.get_user_id()

    conversation = validate_conversation(session, conversation_id, user_id)

    if file_id not in conversation.file_ids:
        raise HTTPException(
            status_code=404,
            detail=f"File with ID: {file_id} does not belong to the conversation with ID: {conversation.id}."
        )

    file = validate_file(session, file_id, user_id)

    return ConversationFileFull(
        id=file.id,
        conversation_id=conversation.id,
        file_name=file.file_name,
        file_content=file.file_content,
        file_size=file.file_size,
        user_id=file.user_id,
        created_at=file.created_at,
        updated_at=file.updated_at,
    )


@router.delete("/{conversation_id}/files/{file_id}")
async def delete_file(
    conversation_id: str,
    file_id: str,
    session: DBSessionDep,
    ctx: Context = Depends(get_context),
) -> DeleteConversationFileResponse:
    """
    Delete a file by ID.

    Args:
        conversation_id (str): Conversation ID.
        file_id (str): File ID.
        session (DBSessionDep): Database session.

    Returns:
        DeleteFile: Empty response.

    Raises:
        HTTPException: If the conversation with the given ID is not found.
    """
    user_id = ctx.get_user_id()
    _ = validate_conversation(session, conversation_id, user_id)
    validate_file(session, file_id, user_id)
    # Delete the File DB object
    get_file_service().delete_conversation_file_by_id(
        session, conversation_id, file_id, user_id, ctx
    )

    return DeleteConversationFileResponse()


# MISC
@router.post("/{conversation_id}/generate-title", response_model=GenerateTitleResponse)
async def generate_title(
    conversation_id: str,
    session: DBSessionDep,
    request: Request,
    model: Optional[str] = "command-r",
    ctx: Context = Depends(get_context),
) -> GenerateTitleResponse:
    """
    Generate a title for a conversation and update the conversation with the generated title.

    Args:
        conversation_id (str): Conversation ID.
        session (DBSessionDep): Database session.
        request (Request): Request object.
        ctx (Context): Context object.

    Returns:
        str: Generated title for the conversation.

    Raises:
        HTTPException: If the conversation with the given ID is not found.
    """
    user_id = ctx.get_user_id()
    ctx.with_deployment_config()
    ctx.with_model(model)

    conversation = validate_conversation(session, conversation_id, user_id)
    agent_id = conversation.agent_id if conversation.agent_id else None

    if agent_id:
        agent = agent_crud.get_agent_by_id(session, agent_id, user_id)
        agent_schema = Agent.model_validate(agent)
        ctx.with_agent(agent_schema)

    title, error = await generate_conversation_title(
        session,
        conversation,
        agent_id,
        ctx,
        model,
    )

    conversation_crud.update_conversation(
        session, conversation, UpdateConversationRequest(title=title)
    )

    return GenerateTitleResponse(
        title=title,
        error=error,
    )


# SYNTHESIZE
@router.get("/{conversation_id}/synthesize/{message_id}")
async def synthesize_message(
    conversation_id: str,
    message_id: str,
    session: DBSessionDep,
    ctx: Context = Depends(get_context),
) -> Response:
    """
    Generate a synthesized audio for a specific message in a conversation.

    Args:
        conversation_id (str): Conversation ID.
        message_id (str): Message ID.
        session (DBSessionDep): Database session.
        ctx (Context): Context object.

    Returns:
        Response: Synthesized audio file.

    Raises:
        HTTPException: If the message with the given ID is not found or synthesis fails.
    """
    user_id = ctx.get_user_id()
    message = message_crud.get_conversation_message(session, conversation_id, message_id, user_id)

    if not message:
        raise HTTPException(
            status_code=404,
            detail=f"Message with ID: {message_id} not found.",
        )

    try:
        synthesized_audio = synthesize(message.text)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error while message synthesis: {e}"
        )

    return Response(synthesized_audio, media_type="audio/mp3")
