from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class InputType(str, Enum):
    """Supported multimodal business input formats."""
    TEXT = "TEXT"
    PDF = "PDF"
    CSV = "CSV"
    DOCX = "DOCX"
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"


class InputStatus(str, Enum):
    """Lifecycle processing status of an input."""
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    OCR_REQUIRED = "OCR_REQUIRED"
    FAILED = "FAILED"


class InputErrorCode(str, Enum):
    """Structured error codes for input handling."""
    UNSUPPORTED_FILE_TYPE = "UNSUPPORTED_FILE_TYPE"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    INVALID_FILE = "INVALID_FILE"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    OCR_REQUIRED = "OCR_REQUIRED"
    TRANSCRIPTION_FAILED = "TRANSCRIPTION_FAILED"
    TRANSCRIPTION_NOT_CONFIGURED = "TRANSCRIPTION_NOT_CONFIGURED"
    PROCESSING_FAILED = "PROCESSING_FAILED"


class BusinessInput(BaseModel):
    """Common representation for any business input provided to AgentX."""
    input_id: str
    type: InputType
    filename: str
    content_reference: str
    size_bytes: int = 0
    mime_type: Optional[str] = None
    extracted_text: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    status: InputStatus = InputStatus.UPLOADED
    error_code: Optional[InputErrorCode] = None
    error_message: Optional[str] = None
    task_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def mark_processed(
        self,
        extracted_text: Optional[str] = None,
        structured_data: Optional[Dict[str, Any]] = None,
        metadata_updates: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update input to PROCESSED status with extracted content."""
        self.status = InputStatus.PROCESSED
        if extracted_text is not None:
            self.extracted_text = extracted_text
        if structured_data is not None:
            self.structured_data = structured_data
        if metadata_updates:
            self.metadata.update(metadata_updates)
        self.updated_at = datetime.now(timezone.utc)

    def mark_ocr_required(
        self,
        page_count: int,
        metadata_updates: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Mark scanned document where no text was extracted."""
        self.status = InputStatus.OCR_REQUIRED
        self.error_code = InputErrorCode.OCR_REQUIRED
        self.error_message = f"Scanned or image-only PDF detected ({page_count} pages). Optical Character Recognition (OCR) is required."
        self.metadata["page_count"] = page_count
        if metadata_updates:
            self.metadata.update(metadata_updates)
        self.updated_at = datetime.now(timezone.utc)

    def mark_failed(
        self,
        error_code: InputErrorCode,
        error_message: str,
    ) -> None:
        """Update input to FAILED status with structured error."""
        self.status = InputStatus.FAILED
        self.error_code = error_code
        self.error_message = error_message
        self.updated_at = datetime.now(timezone.utc)
