import uuid
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from app.models.input import (
    BusinessInput,
    InputErrorCode,
    InputStatus,
)
from app.schemas.input import (
    InputDetailResponse,
    InputProcessResponse,
    InputUploadResponse,
    TaskInputsResponse,
)
from app.services.input_processor import get_input_processor
from app.services.input_store import get_input_store
from app.services.storage import StorageError, get_storage_service
from app.services.task_store import get_task_store

router = APIRouter()


@router.post(
    "/upload",
    response_model=InputUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a business input file (Text, PDF, CSV, DOCX, Image, Audio)",
)
async def upload_input(
    file: UploadFile = File(..., description="Business input file to upload"),
    task_id: Optional[str] = Form(None, description="Optional task ID to associate with the input"),
) -> InputUploadResponse:
    """Accept and validate a business file upload, store securely, and process extracted context."""
    storage = get_storage_service()
    input_store = get_input_store()
    processor = get_input_processor()

    filename = file.filename or "uploaded_file"
    try:
        content = await file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(exc)}",
        )

    # Validate and save to storage service
    try:
        content_ref, input_type, clean_name, size_bytes = await storage.save_file(
            filename=filename,
            content=content,
            mime_type=file.content_type,
        )
    except StorageError as se:
        status_code = status.HTTP_400_BAD_REQUEST
        if se.code == InputErrorCode.FILE_TOO_LARGE:
            status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        elif se.code == InputErrorCode.UNSUPPORTED_FILE_TYPE:
            status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        raise HTTPException(status_code=status_code, detail=f"[{se.code.value}] {se.message}")

    input_id = f"inp_{uuid.uuid4().hex[:12]}"
    business_input = BusinessInput(
        input_id=input_id,
        type=input_type,
        filename=clean_name,
        content_reference=content_ref,
        size_bytes=size_bytes,
        mime_type=file.content_type,
        task_id=task_id,
        status=InputStatus.UPLOADED,
    )

    # Process immediately
    business_input = await processor.process_input(business_input)
    await input_store.save_input(business_input)

    return InputUploadResponse(
        input_id=business_input.input_id,
        type=business_input.type,
        filename=business_input.filename,
        size_bytes=business_input.size_bytes,
        mime_type=business_input.mime_type,
        status=business_input.status,
        metadata=business_input.metadata,
        task_id=business_input.task_id,
        created_at=business_input.created_at,
    )


@router.get(
    "/{input_id}",
    response_model=InputDetailResponse,
    summary="Get business input details and extracted context",
)
async def get_input(input_id: str) -> InputDetailResponse:
    """Retrieve full processing details, status, and extracted context for a business input."""
    input_store = get_input_store()
    business_input = await input_store.get_input(input_id)
    if not business_input:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business input '{input_id}' not found.",
        )

    return InputDetailResponse(
        input_id=business_input.input_id,
        type=business_input.type,
        filename=business_input.filename,
        content_reference=business_input.content_reference,
        size_bytes=business_input.size_bytes,
        mime_type=business_input.mime_type,
        extracted_text=business_input.extracted_text,
        structured_data=business_input.structured_data,
        metadata=business_input.metadata,
        status=business_input.status,
        error_code=business_input.error_code,
        error_message=business_input.error_message,
        task_id=business_input.task_id,
        created_at=business_input.created_at,
        updated_at=business_input.updated_at,
    )


@router.post(
    "/{input_id}/process",
    response_model=InputProcessResponse,
    summary="Process or re-extract an uploaded business input",
)
async def process_input(input_id: str) -> InputProcessResponse:
    """Run extraction pipeline on the specified input."""
    input_store = get_input_store()
    processor = get_input_processor()

    business_input = await input_store.get_input(input_id)
    if not business_input:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business input '{input_id}' not found.",
        )

    business_input = await processor.process_input(business_input)
    await input_store.save_input(business_input)

    return InputProcessResponse(
        input_id=business_input.input_id,
        type=business_input.type,
        status=business_input.status,
        extracted_text=business_input.extracted_text,
        structured_data=business_input.structured_data,
        error_code=business_input.error_code,
        error_message=business_input.error_message,
        metadata=business_input.metadata,
    )
