import io
import os
import zipfile
from unittest.mock import AsyncMock, patch
import httpx
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from pypdf import PdfWriter

from app.agents.operations_agent import OperationsAgent
from app.agents.sales_agent import SalesAgent
from app.agents.support_agent import SupportAgent
from app.main import app
from app.models.approval import ApprovalStatus
from app.models.input import (
    BusinessInput,
    InputErrorCode,
    InputStatus,
    InputType,
)
from app.models.task import AgentType, Task, TaskStatus
from app.services.execution_engine import TaskExecutionEngine
from app.services.input_processor import InputProcessorService
from app.services.input_store import InputStore, get_input_store
from app.services.orchestrator import TaskOrchestrator
from app.services.storage import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE_BYTES,
    LocalStorageService,
    StorageError,
    get_storage_service,
)
from app.services.task_store import get_task_store
from app.services.transcription import (
    MockTranscriptionProvider,
    TranscriptionError,
    UnconfiguredTranscriptionProvider,
    set_transcription_provider,
)

client = TestClient(app)


# ==============================================================
# Test Fixture Helpers
# ==============================================================

def make_text_pdf_bytes(text: str = "Customer complaint for order ORD-5001 customer CUST-001") -> bytes:
    """Create a minimal valid single-page PDF containing extractable text."""
    pdf_content = f"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj
4 0 obj << /Length {len(text) + 30} >> stream
BT /F1 12 Tf 72 712 Td ({text}) Tj ET
endstream
endobj
5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000000338 00000 n 
trailer << /Size 6 /Root 1 0 R >>
startxref
407
%%EOF"""
    return pdf_content.encode("latin-1")


def make_blank_pdf_bytes() -> bytes:
    """Create a multi-page PDF with 0 extractable text (simulating scanned/image-only document)."""
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    writer.add_blank_page(width=300, height=300)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def make_docx_bytes(paragraphs: list[str]) -> bytes:
    """Create a valid DOCX package in memory containing specified paragraph text."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        body = "".join(f"<w:p><w:r><w:t>{p}</w:t></w:r></w:p>" for p in paragraphs)
        xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body>{body}</w:body>
</w:document>"""
        zf.writestr("word/document.xml", xml)
    return buf.getvalue()


def make_image_bytes(fmt: str = "PNG", width: int = 150, height: int = 100) -> bytes:
    """Create a valid in-memory image byte stream."""
    img = Image.new("RGB", (width, height), color=(73, 109, 137))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


# ==============================================================
# 1. Storage & Security Tests
# ==============================================================

@pytest.mark.asyncio
async def test_storage_abstraction_save_and_retrieve(tmp_path):
    """Verify LocalStorageService saves files safely outside code and retrieves raw bytes."""
    service = LocalStorageService(base_dir=str(tmp_path / "uploads"))
    ref, in_type, clean_name, size = await service.save_file(
        filename="test_file.txt",
        content=b"Sample business content",
        mime_type="text/plain",
    )
    assert in_type == InputType.TEXT
    assert clean_name == "test_file.txt"
    assert size == len(b"Sample business content")
    assert (tmp_path / "uploads" / ref).exists()

    retrieved = await service.get_file(ref)
    assert retrieved == b"Sample business content"


@pytest.mark.asyncio
async def test_storage_rejects_unsupported_file_type(tmp_path):
    """Verify security validation rejects unsupported extensions like .exe or .sh."""
    service = LocalStorageService(base_dir=str(tmp_path / "uploads"))
    with pytest.raises(StorageError) as exc_info:
        await service.save_file("malicious_script.sh", b"#!/bin/bash\necho hack")
    assert exc_info.value.code == InputErrorCode.UNSUPPORTED_FILE_TYPE


@pytest.mark.asyncio
async def test_storage_rejects_oversized_file(tmp_path):
    """Verify file size limit enforcement rejects files > MAX_FILE_SIZE_BYTES (10MB)."""
    service = LocalStorageService(base_dir=str(tmp_path / "uploads"))
    oversized = b"0" * (MAX_FILE_SIZE_BYTES + 1024)
    with pytest.raises(StorageError) as exc_info:
        await service.save_file("big_data.csv", oversized)
    assert exc_info.value.code == InputErrorCode.FILE_TOO_LARGE


@pytest.mark.asyncio
async def test_storage_rejects_empty_file(tmp_path):
    """Verify 0-byte files are rejected with INVALID_FILE."""
    service = LocalStorageService(base_dir=str(tmp_path / "uploads"))
    with pytest.raises(StorageError) as exc_info:
        await service.save_file("empty.txt", b"")
    assert exc_info.value.code == InputErrorCode.INVALID_FILE


@pytest.mark.asyncio
async def test_storage_path_traversal_sanitization(tmp_path):
    """Verify path traversal filenames (../../etc/passwd) are sanitized safely."""
    service = LocalStorageService(base_dir=str(tmp_path / "uploads"))
    ref, in_type, clean_name, size = await service.save_file(
        filename="../../../secret_doc.pdf",
        content=make_text_pdf_bytes(),
    )
    assert ".." not in ref
    assert clean_name == "secret_doc.pdf"
    # Ensure it's strictly inside the base directory
    target_path = await service.get_file_path(ref)
    assert str(tmp_path) in target_path


# ==============================================================
# 2. Input Extractor Unit Tests
# ==============================================================

@pytest.mark.asyncio
async def test_text_input_processing(tmp_path):
    """Verify plain text input extraction produces structured document data."""
    service = LocalStorageService(base_dir=str(tmp_path / "uploads"))
    ref, _, clean_name, size = await service.save_file("notes.txt", b"Invoice payment for client ACME is due on Friday.")
    
    inp = BusinessInput(
        input_id="inp_txt_1",
        type=InputType.TEXT,
        filename=clean_name,
        content_reference=ref,
        size_bytes=size,
    )
    
    processor = InputProcessorService()
    processor.storage = service
    processed = await processor.process_input(inp)
    
    assert processed.status == InputStatus.PROCESSED
    assert "ACME" in processed.extracted_text
    assert processed.structured_data["type"] == "business_document"
    assert processed.structured_data["word_count"] == 9


@pytest.mark.asyncio
async def test_pdf_text_extraction(tmp_path):
    """Verify PDF extractor parses multi-page text and metadata."""
    service = LocalStorageService(base_dir=str(tmp_path / "uploads"))
    pdf_bytes = make_text_pdf_bytes("Customer complaint ORD-5001: delivery delayed for customer CUST-001")
    ref, _, clean_name, size = await service.save_file("complaint.pdf", pdf_bytes)

    inp = BusinessInput(
        input_id="inp_pdf_1",
        type=InputType.PDF,
        filename=clean_name,
        content_reference=ref,
        size_bytes=size,
    )

    processor = InputProcessorService()
    processor.storage = service
    processed = await processor.process_input(inp)

    assert processed.status == InputStatus.PROCESSED
    assert "ORD-5001" in processed.extracted_text
    assert processed.structured_data["type"] == "business_document"
    assert processed.structured_data["page_count"] == 1


@pytest.mark.asyncio
async def test_pdf_scanned_ocr_required(tmp_path):
    """Verify scanned/blank PDF with no text triggers structured OCR_REQUIRED state."""
    service = LocalStorageService(base_dir=str(tmp_path / "uploads"))
    blank_pdf = make_blank_pdf_bytes()
    ref, _, clean_name, size = await service.save_file("scanned_receipt.pdf", blank_pdf)

    inp = BusinessInput(
        input_id="inp_pdf_scanned",
        type=InputType.PDF,
        filename=clean_name,
        content_reference=ref,
        size_bytes=size,
    )

    processor = InputProcessorService()
    processor.storage = service
    processed = await processor.process_input(inp)

    assert processed.status == InputStatus.OCR_REQUIRED
    assert processed.error_code == InputErrorCode.OCR_REQUIRED
    assert "Optical Character Recognition (OCR) is required" in processed.error_message
    assert processed.metadata["page_count"] == 2


@pytest.mark.asyncio
async def test_pdf_malformed_handling(tmp_path):
    """Verify malformed/corrupted PDF content is handled gracefully without crashing."""
    service = LocalStorageService(base_dir=str(tmp_path / "uploads"))
    ref, _, clean_name, size = await service.save_file("corrupted.pdf", b"%PDF-corrupted-garbage-bytes")

    inp = BusinessInput(
        input_id="inp_pdf_corrupt",
        type=InputType.PDF,
        filename=clean_name,
        content_reference=ref,
        size_bytes=size,
    )

    processor = InputProcessorService()
    processor.storage = service
    processed = await processor.process_input(inp)

    assert processed.status == InputStatus.FAILED
    assert processed.error_code == InputErrorCode.EXTRACTION_FAILED


@pytest.mark.asyncio
async def test_csv_parsing_valid_and_malformed_rows(tmp_path):
    """Verify CSV ingestion detects columns, counts rows, converts records, and logs invalid rows without discarding them."""
    service = LocalStorageService(base_dir=str(tmp_path / "uploads"))
    csv_content = (
        "name,email,company,status\n"
        "Rajesh Khanna,rajesh@cyberdyne.co.in,Cyberdyne Tech,qualified\n"
        "Invalid Row Missing Columns\n"
        "Sarah Connor,sarah@resistance.org,Resistance,new\n"
        "Extra,Column,Data,Row,Too,Many,Columns\n"
    ).encode("utf-8")

    ref, _, clean_name, size = await service.save_file("leads.csv", csv_content)

    inp = BusinessInput(
        input_id="inp_csv_1",
        type=InputType.CSV,
        filename=clean_name,
        content_reference=ref,
        size_bytes=size,
    )

    processor = InputProcessorService()
    processor.storage = service
    processed = await processor.process_input(inp)

    assert processed.status == InputStatus.PROCESSED
    data = processed.structured_data
    assert data["type"] == "tabular_data"
    assert data["columns"] == ["name", "email", "company", "status"]
    assert data["rows"] == 4
    assert data["valid_rows"] == 2
    assert data["invalid_rows"] == 2
    assert len(data["records"]) == 2
    assert data["records"][0]["company"] == "Cyberdyne Tech"
    assert len(data["invalid_samples"]) == 2


@pytest.mark.asyncio
async def test_docx_text_extraction(tmp_path):
    """Verify DOCX text extraction parses paragraphs cleanly from XML structure."""
    service = LocalStorageService(base_dir=str(tmp_path / "uploads"))
    docx_bytes = make_docx_bytes([
        "Commercial Proposal: AgentX Integration",
        "Target client: Stark Industries",
        "Annual Contract Value: $120,000",
    ])
    ref, _, clean_name, size = await service.save_file("proposal.docx", docx_bytes)

    inp = BusinessInput(
        input_id="inp_docx_1",
        type=InputType.DOCX,
        filename=clean_name,
        content_reference=ref,
        size_bytes=size,
    )

    processor = InputProcessorService()
    processor.storage = service
    processed = await processor.process_input(inp)

    assert processed.status == InputStatus.PROCESSED
    assert "Commercial Proposal" in processed.extracted_text
    assert "Stark Industries" in processed.extracted_text
    assert processed.structured_data["paragraph_count"] == 3


@pytest.mark.asyncio
async def test_image_input_validation(tmp_path):
    """Verify image processing extracts dimensions and produces structured visual record."""
    service = LocalStorageService(base_dir=str(tmp_path / "uploads"))
    img_bytes = make_image_bytes(fmt="PNG", width=320, height=240)
    ref, _, clean_name, size = await service.save_file("complaint_screenshot.png", img_bytes)

    inp = BusinessInput(
        input_id="inp_img_1",
        type=InputType.IMAGE,
        filename=clean_name,
        content_reference=ref,
        size_bytes=size,
    )

    processor = InputProcessorService()
    processor.storage = service
    processed = await processor.process_input(inp)

    assert processed.status == InputStatus.PROCESSED
    data = processed.structured_data
    assert data["type"] == "visual_record"
    assert data["width"] == 320
    assert data["height"] == 240
    assert data["format"] == "png"


@pytest.mark.asyncio
async def test_audio_transcription_provider_mock(tmp_path):
    """Verify voice audio input is transcribed via pluggable TranscriptionProvider."""
    service = LocalStorageService(base_dir=str(tmp_path / "uploads"))
    ref, _, clean_name, size = await service.save_file("voice_memo.mp3", b"fake-audio-bytes-header-mp3")

    mock_provider = MockTranscriptionProvider(
        default_text="Customer complaint: Transaction TXN-5001 was debited but order ORD-5001 failed."
    )
    set_transcription_provider(mock_provider)

    inp = BusinessInput(
        input_id="inp_aud_1",
        type=InputType.AUDIO,
        filename=clean_name,
        content_reference=ref,
        size_bytes=size,
    )

    processor = InputProcessorService()
    processor.storage = service
    processed = await processor.process_input(inp)

    assert processed.status == InputStatus.PROCESSED
    assert "TXN-5001" in processed.extracted_text
    assert processed.structured_data["type"] == "voice_memo"
    assert processed.structured_data["confidence"] > 0.9


@pytest.mark.asyncio
async def test_audio_transcription_unconfigured_error(tmp_path):
    """Verify unconfigured transcription provider returns clear structured error without hallucinating results."""
    service = LocalStorageService(base_dir=str(tmp_path / "uploads"))
    ref, _, clean_name, size = await service.save_file("unconfigured.mp3", b"audio-bytes")

    set_transcription_provider(UnconfiguredTranscriptionProvider())

    inp = BusinessInput(
        input_id="inp_aud_unconf",
        type=InputType.AUDIO,
        filename=clean_name,
        content_reference=ref,
        size_bytes=size,
    )

    processor = InputProcessorService()
    processor.storage = service
    processed = await processor.process_input(inp)

    assert processed.status == InputStatus.FAILED
    assert processed.error_code == InputErrorCode.TRANSCRIPTION_NOT_CONFIGURED
    assert "No voice transcription service is configured" in processed.error_message


# ==============================================================
# 3. Task Context & Association Tests
# ==============================================================

@pytest.mark.asyncio
async def test_task_input_association(tmp_path):
    """Verify inputs are associated with tasks and accessible via InputStore."""
    store = InputStore()
    inp = BusinessInput(
        input_id="inp_assoc_1",
        type=InputType.PDF,
        filename="lead_brief.pdf",
        content_reference="ref_1",
        task_id="task_123",
    )
    await store.save_input(inp)

    task_inputs = await store.list_inputs_by_task("task_123")
    assert len(task_inputs) == 1
    assert task_inputs[0].filename == "lead_brief.pdf"

    # Associate new input to existing task
    inp2 = BusinessInput(
        input_id="inp_assoc_2",
        type=InputType.CSV,
        filename="leads.csv",
        content_reference="ref_2",
    )
    await store.save_input(inp2)
    success = await store.associate_task("inp_assoc_2", "task_123")
    assert success is True

    updated_inputs = await store.list_inputs_by_task("task_123")
    assert len(updated_inputs) == 2


# ==============================================================
# 4. End-to-End Business Workflows
# ==============================================================

@pytest.mark.asyncio
async def test_sales_demo_csv_leads_workflow(tmp_path):
    """SALES DEMO: User uploads leads.csv and says 'Process these leads and prepare personalized follow-ups'.
    AgentX processes CSV -> Sales Teammate -> invokes n8n lead qualification -> prepares follow-ups.
    """
    storage = LocalStorageService(base_dir=str(tmp_path / "uploads"))
    input_store = get_input_store()

    # 1. User uploads leads.csv
    csv_bytes = (
        "lead_id,name,company,email,status\n"
        "LEAD-001,Rajesh Khanna,Cyberdyne Tech,rajesh@cyberdyne.co.in,new\n"
        "LEAD-002,Priya Sharma,Wayne Enterprises,priya@wayne.com,contacted\n"
    ).encode("utf-8")

    ref, in_type, clean_name, size = await storage.save_file("leads.csv", csv_bytes)
    inp = BusinessInput(
        input_id="inp_sales_leads",
        type=in_type,
        filename=clean_name,
        content_reference=ref,
        size_bytes=size,
    )
    processor = InputProcessorService()
    processor.storage = storage
    await processor.process_input(inp)
    await input_store.save_input(inp)

    # 2. User creates task with attached leads.csv
    task = Task(
        task_id="task_sales_csv_demo",
        user_request="Process these leads and prepare personalized follow-ups.",
        selected_agent=AgentType.SALES,
        status=TaskStatus.CREATED,
        input_ids=[inp.input_id],
    )
    await input_store.associate_task(inp.input_id, task.task_id)

    sales_agent = SalesAgent()
    plan = await sales_agent.plan(task.user_request, task_id=task.task_id)
    assert any("n8n_process_lead" in step.tool_id for step in plan.steps if step.tool_id)

    # 3. Execute plan
    engine = TaskExecutionEngine()
    mock_n8n_response = {
        "success": True,
        "workflow": "sales_process_lead",
        "task_id": task.task_id,
        "lead_id": "LEAD-001",
        "lead_status": "qualified",
        "qualification": {"score": 88, "tier": "TIER_1_ENTERPRISE", "status": "qualified"},
        "actions": ["Lead retrieved and validated", "Lead evaluated as QUALIFIED", "Follow-up drafted"],
        "follow_up": {
            "prepared": True,
            "recipient_email": "rajesh@cyberdyne.co.in",
            "recipient_name": "Rajesh Khanna",
            "subject": "Tailored Solution for Cyberdyne Tech",
            "message": "Hello Rajesh, we have reviewed Cyberdyne Tech requirements...",
        },
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = httpx.Response(200, json=mock_n8n_response)
        executed_task = await engine.execute_task(task, sales_agent, plan)

    assert executed_task.status == TaskStatus.COMPLETED
    assert executed_task.result["verification"]["verified"] is True
    assert "Cyberdyne Tech" in str(executed_task.result) or "Rajesh" in str(executed_task.result) or "qualified" in str(executed_task.result).lower()


@pytest.mark.asyncio
async def test_support_demo_document_input_workflow(tmp_path):
    """SUPPORT DEMO: Customer complaint PDF attached -> Support Teammate understands issue,
    identifies customer & order, conducts investigation, and recommends resolution.
    """
    storage = LocalStorageService(base_dir=str(tmp_path / "uploads"))
    input_store = get_input_store()

    # 1. Upload complaint PDF
    pdf_bytes = make_text_pdf_bytes("Customer complaint: My order ORD-1001 for customer CUST-001 has not arrived and is delayed.")
    ref, in_type, clean_name, size = await storage.save_file("customer_complaint.pdf", pdf_bytes)
    inp = BusinessInput(
        input_id="inp_supp_pdf",
        type=in_type,
        filename=clean_name,
        content_reference=ref,
        size_bytes=size,
    )
    processor = InputProcessorService()
    processor.storage = storage
    await processor.process_input(inp)
    await input_store.save_input(inp)

    # 2. Task with attached input
    task = Task(
        task_id="task_support_pdf_demo",
        user_request="Handle this customer complaint.",
        selected_agent=AgentType.SUPPORT,
        status=TaskStatus.CREATED,
        input_ids=[inp.input_id],
    )
    await input_store.associate_task(inp.input_id, task.task_id)

    support_agent = SupportAgent()
    plan = await support_agent.plan(task.user_request, task_id=task.task_id)

    engine = TaskExecutionEngine()
    executed_task = await engine.execute_task(task, support_agent, plan)

    assert executed_task.status == TaskStatus.COMPLETED
    assert executed_task.result["customer"] == "CUST-001"
    assert executed_task.result["verification"]["verified"] is True


@pytest.mark.asyncio
async def test_operations_demo_csv_sales_data_workflow(tmp_path):
    """OPERATIONS DEMO: sales.csv uploaded -> User: 'Analyze this sales data and identify what needs attention.'
    Operations Teammate analyzes tabular data -> executes n8n operational workflow -> verification.
    """
    storage = LocalStorageService(base_dir=str(tmp_path / "uploads"))
    input_store = get_input_store()

    sales_csv = (
        "transaction_id,amount,customer_id,status\n"
        "TXN-901,1500.0,CUST-001,completed\n"
        "TXN-902,4200.0,CUST-002,failed\n"
        "TXN-903,890.0,CUST-003,completed\n"
    ).encode("utf-8")

    ref, in_type, clean_name, size = await storage.save_file("sales.csv", sales_csv)
    inp = BusinessInput(
        input_id="inp_ops_sales",
        type=in_type,
        filename=clean_name,
        content_reference=ref,
        size_bytes=size,
    )
    processor = InputProcessorService()
    processor.storage = storage
    await processor.process_input(inp)
    await input_store.save_input(inp)

    task = Task(
        task_id="task_ops_csv_demo",
        user_request="Analyze this sales data and identify what needs attention.",
        selected_agent=AgentType.OPERATIONS,
        status=TaskStatus.CREATED,
        input_ids=[inp.input_id],
    )
    await input_store.associate_task(inp.input_id, task.task_id)

    ops_agent = OperationsAgent()
    plan = await ops_agent.plan(task.user_request, task_id=task.task_id)
    assert any("n8n_operations_check" in step.tool_id for step in plan.steps if step.tool_id)

    engine = TaskExecutionEngine()
    mock_ops_result = {
        "success": True,
        "workflow": "operations_daily_business_check",
        "task_id": task.task_id,
        "records_processed": 3,
        "exceptions_found": 1,
        "requires_attention": True,
        "metrics": {"successful": 2, "failed_transactions": 1, "total_revenue": 6590.0},
        "actions": ["Loaded sales CSV records", "Flagged failed transaction TXN-902", "Operations report compiled"],
        "report": {
            "summary": "1 exception detected in uploaded sales dataset",
            "priority_items": ["TXN-902: Transaction failed requiring payment reconciliation"],
        },
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = httpx.Response(200, json=mock_ops_result)
        executed_task = await engine.execute_task(task, ops_agent, plan)

    assert executed_task.status == TaskStatus.COMPLETED
    assert executed_task.result["verification"]["verified"] is True
    assert "operations" in str(executed_task.result).lower()


# ==============================================================
# 5. REST API Integration Tests
# ==============================================================

def test_api_upload_text_file():
    """Verify POST /inputs/upload accepts and stores a file."""
    response = client.post(
        "/inputs/upload",
        files={"file": ("memo.txt", b"Strategic update for Q3 planning", "text/plain")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "TEXT"
    assert data["filename"] == "memo.txt"
    assert data["status"] == "PROCESSED"
    assert "input_id" in data


def test_api_get_input_detail():
    """Verify GET /inputs/{input_id} returns extracted structured context."""
    # First upload
    up_resp = client.post(
        "/inputs/upload",
        files={"file": ("client_notes.txt", b"Meeting notes with Cyberdyne Tech CEO", "text/plain")},
    )
    assert up_resp.status_code == 201
    input_id = up_resp.json()["input_id"]

    # Query details
    get_resp = client.get(f"/inputs/{input_id}")
    assert get_resp.status_code == 200
    detail = get_resp.json()
    assert detail["input_id"] == input_id
    assert "Cyberdyne Tech" in detail["extracted_text"]
    assert detail["structured_data"]["type"] == "business_document"


def test_api_upload_unsupported_extension_error():
    """Verify POST /inputs/upload returns structured error for unsupported file types."""
    resp = client.post(
        "/inputs/upload",
        files={"file": ("dangerous_script.exe", b"MZbinarycode", "application/octet-stream")},
    )
    assert resp.status_code == 415
    assert "UNSUPPORTED_FILE_TYPE" in resp.text


def test_api_task_inputs_association():
    """Verify GET /tasks/{task_id}/inputs returns inputs associated with a task."""
    # Create task first
    task_resp = client.post(
        "/tasks",
        json={"user_request": "Review attached documentation for client CUST-001"},
    )
    assert task_resp.status_code == 201
    task_id = task_resp.json()["task_id"]

    # Upload file with task_id
    up_resp = client.post(
        "/inputs/upload",
        data={"task_id": task_id},
        files={"file": ("cust_profile.txt", b"Customer Profile: CUST-001 Enterprise", "text/plain")},
    )
    assert up_resp.status_code == 201

    # Query task inputs
    inputs_resp = client.get(f"/tasks/{task_id}/inputs")
    assert inputs_resp.status_code == 200
    task_inputs = inputs_resp.json()
    assert task_inputs["task_id"] == task_id
    assert task_inputs["total_inputs"] >= 1
    assert any(i["filename"] == "cust_profile.txt" for i in task_inputs["inputs"])
