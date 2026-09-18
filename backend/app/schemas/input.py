from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.models.input import InputErrorCode, InputStatus, InputType


class InputUploadResponse(BaseModel):
    """Response returned upon uploading a business file/input."""
    input_id: str
    type: InputType
    filename: str
    size_bytes: int
    mime_type: Optional[str] = None
    status: InputStatus
    metadata: Dict[str, Any] = Field(default_factory=dict)
    task_id: Optional[str] = None
    created_at: datetime


class InputDetailResponse(BaseModel):
    """Complete detail response for a business input, including extraction."""
    input_id: str
    type: InputType
    filename: str
    content_reference: str
    size_bytes: int
    mime_type: Optional[str] = None
    extracted_text: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    status: InputStatus
    error_code: Optional[InputErrorCode] = None
    error_message: Optional[str] = None
    task_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class InputProcessResponse(BaseModel):
    """Response returned after processing/extracting an input."""
    input_id: str
    type: InputType
    status: InputStatus
    extracted_text: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    error_code: Optional[InputErrorCode] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskInputsResponse(BaseModel):
    """Response for inputs associated with a task."""
    task_id: str
    total_inputs: int
    inputs: List[InputDetailResponse]
