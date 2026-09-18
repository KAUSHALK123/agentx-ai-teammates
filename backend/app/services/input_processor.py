import csv
import io
import logging
import os
import xml.etree.ElementTree as ET
import zipfile
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image
from pypdf import PdfReader
from app.models.input import (
    BusinessInput,
    InputErrorCode,
    InputStatus,
    InputType,
)
from app.services.storage import get_storage_service
from app.services.transcription import TranscriptionError, get_transcription_provider

logger = logging.getLogger("agentx.input_processor")


class InputProcessorService:
    """Extracts structured business information from diverse multimodal inputs."""

    def __init__(self):
        self.storage = get_storage_service()

    async def process_input(self, business_input: BusinessInput) -> BusinessInput:
        """Process raw input according to its type, extract context, and update status."""
        business_input.status = InputStatus.PROCESSING
        try:
            raw_bytes = await self.storage.get_file(business_input.content_reference)
        except Exception as exc:
            logger.error("Failed to retrieve file %s: %s", business_input.content_reference, exc)
            business_input.mark_failed(
                InputErrorCode.INVALID_FILE,
                f"Failed to access file in storage: {str(exc)}",
            )
            return business_input

        try:
            if business_input.type == InputType.TEXT:
                self._process_text(business_input, raw_bytes)
            elif business_input.type == InputType.PDF:
                self._process_pdf(business_input, raw_bytes)
            elif business_input.type == InputType.CSV:
                self._process_csv(business_input, raw_bytes)
            elif business_input.type == InputType.DOCX:
                self._process_docx(business_input, raw_bytes)
            elif business_input.type == InputType.IMAGE:
                self._process_image(business_input, raw_bytes)
            elif business_input.type == InputType.AUDIO:
                await self._process_audio(business_input, raw_bytes)
            else:
                business_input.mark_failed(
                    InputErrorCode.UNSUPPORTED_FILE_TYPE,
                    f"Unsupported input type: {business_input.type}",
                )
        except TranscriptionError as te:
            business_input.mark_failed(te.code, te.message)
        except Exception as exc:
            logger.error("Extraction failed for input %s (%s): %s", business_input.input_id, business_input.filename, exc)
            business_input.mark_failed(
                InputErrorCode.EXTRACTION_FAILED,
                f"Failed to extract content: {str(exc)}",
            )

        return business_input

    def _process_text(self, business_input: BusinessInput, content: bytes) -> None:
        """Process plain text business input."""
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("latin-1", errors="replace")

        clean_text = text.strip()
        lines = clean_text.splitlines()
        word_count = len(clean_text.split())

        structured_data = {
            "type": "business_document",
            "format": "text",
            "line_count": len(lines),
            "word_count": word_count,
            "char_count": len(clean_text),
            "preview": clean_text[:200] if clean_text else "",
        }

        business_input.mark_processed(
            extracted_text=clean_text,
            structured_data=structured_data,
            metadata_updates={"word_count": word_count, "line_count": len(lines)},
        )

    def _process_pdf(self, business_input: BusinessInput, content: bytes) -> None:
        """Extract text and metadata from PDF using pypdf. Detect scanned PDFs for OCR_REQUIRED."""
        stream = io.BytesIO(content)
        try:
            reader = PdfReader(stream)
            page_count = len(reader.pages)
        except Exception as exc:
            raise ValueError(f"Malformed or unreadable PDF: {str(exc)}")

        if page_count == 0:
            raise ValueError("PDF document contains 0 pages.")

        extracted_pages: List[str] = []
        for idx, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text() or ""
                extracted_pages.append(page_text.strip())
            except Exception as page_exc:
                logger.warning("Error extracting text from PDF page %d: %s", idx + 1, page_exc)
                extracted_pages.append("")

        full_text = "\n\n".join([p for p in extracted_pages if p]).strip()

        # Check if the PDF has virtually no extractable text (e.g. scanned image-only PDF)
        # We require at least 5 alphanumeric characters to consider it text-extractable
        alnum_chars = sum(c.isalnum() for c in full_text)
        if alnum_chars < 5:
            # Scanned or image-only PDF
            business_input.mark_ocr_required(
                page_count=page_count,
                metadata_updates={
                    "page_count": page_count,
                    "is_scanned": True,
                    "extracted_chars": alnum_chars,
                },
            )
            return

        # Extract basic PDF metadata if present
        pdf_meta = {}
        if reader.metadata:
            for k, v in reader.metadata.items():
                if v:
                    pdf_meta[str(k).replace("/", "")] = str(v)

        structured_data = {
            "type": "business_document",
            "format": "pdf",
            "page_count": page_count,
            "char_count": len(full_text),
            "preview": full_text[:250],
            "metadata": pdf_meta,
        }

        business_input.mark_processed(
            extracted_text=full_text,
            structured_data=structured_data,
            metadata_updates={"page_count": page_count, "pdf_metadata": pdf_meta},
        )

    def _process_csv(self, business_input: BusinessInput, content: bytes) -> None:
        """Ingest CSV, detect columns, validate rows, capture malformed lines without discarding them."""
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("latin-1", errors="replace")

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            raise ValueError("CSV file is completely empty.")

        stream = io.StringIO(text)
        reader = csv.reader(stream)
        
        try:
            header_row = next(reader)
        except StopIteration:
            raise ValueError("CSV contains no rows.")

        # Clean header column names
        columns = [col.strip() for col in header_row if col.strip()]
        if not columns:
            raise ValueError("CSV contains no valid column headers.")
        
        expected_cols = len(columns)

        valid_records: List[Dict[str, Any]] = []
        invalid_rows: List[Dict[str, Any]] = []
        total_data_rows = 0

        for row_idx, row in enumerate(reader, start=2):
            total_data_rows += 1
            if len(row) != expected_cols:
                invalid_rows.append({
                    "row_number": row_idx,
                    "raw_content": row,
                    "reason": f"Expected {expected_cols} columns but found {len(row)}",
                })
            else:
                record = {}
                for col_name, val in zip(columns, row):
                    record[col_name] = val.strip()
                valid_records.append(record)

        structured_data = {
            "type": "tabular_data",
            "filename": business_input.filename,
            "rows": total_data_rows,
            "columns": columns,
            "valid_rows": len(valid_records),
            "invalid_rows": len(invalid_rows),
            "invalid_samples": invalid_rows[:5] if invalid_rows else [],
            "records": valid_records,
        }

        # Human-readable summary for extracted_text
        summary_text = (
            f"CSV Data Summary for {business_input.filename}:\n"
            f"- Total Rows: {total_data_rows}\n"
            f"- Valid Records: {len(valid_records)}\n"
            f"- Invalid/Malformed Rows: {len(invalid_rows)}\n"
            f"- Columns: {', '.join(columns)}\n"
        )
        if valid_records:
            summary_text += f"\nSample Record: {valid_records[0]}"

        business_input.mark_processed(
            extracted_text=summary_text,
            structured_data=structured_data,
            metadata_updates={
                "row_count": total_data_rows,
                "column_count": len(columns),
                "columns": columns,
                "valid_rows": len(valid_records),
                "invalid_rows": len(invalid_rows),
            },
        )

    def _process_docx(self, business_input: BusinessInput, content: bytes) -> None:
        """Extract text and metadata from DOCX using standard zipfile and XML parsing."""
        stream = io.BytesIO(content)
        
        try:
            with zipfile.ZipFile(stream) as zf:
                if "word/document.xml" not in zf.namelist():
                    raise ValueError("Not a valid DOCX package (missing word/document.xml).")
                
                doc_xml = zf.read("word/document.xml")
                root = ET.fromstring(doc_xml)
                
                # Namespace for WordprocessingML
                ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                
                paragraphs: List[str] = []
                for p in root.findall(".//w:p", ns):
                    texts = [node.text for node in p.findall(".//w:t", ns) if node.text]
                    para_text = "".join(texts).strip()
                    if para_text:
                        paragraphs.append(para_text)
                        
                full_text = "\n\n".join(paragraphs).strip()
        except zipfile.BadZipFile:
            # Check if it's a legacy or plain document
            try:
                full_text = content.decode("utf-8", errors="ignore").strip()
                paragraphs = [line.strip() for line in full_text.splitlines() if line.strip()]
            except Exception:
                raise ValueError("Could not parse DOC/DOCX document.")

        if not full_text:
            raise ValueError("DOC/DOCX file contains no extractable text.")

        structured_data = {
            "type": "business_document",
            "format": "docx",
            "paragraph_count": len(paragraphs),
            "char_count": len(full_text),
            "preview": full_text[:250],
        }

        business_input.mark_processed(
            extracted_text=full_text,
            structured_data=structured_data,
            metadata_updates={"paragraph_count": len(paragraphs), "char_count": len(full_text)},
        )

    def _process_image(self, business_input: BusinessInput, content: bytes) -> None:
        """Validate image and extract dimensions, format, and prepare visual record."""
        stream = io.BytesIO(content)
        try:
            with Image.open(stream) as img:
                img_format = img.format or "UNKNOWN"
                width, height = img.size
                mode = img.mode
        except Exception as exc:
            raise ValueError(f"Malformed or corrupted image file: {str(exc)}")

        summary = f"Image ({img_format}, {width}x{height}px, mode {mode})"
        structured_data = {
            "type": "visual_record",
            "format": img_format.lower(),
            "width": width,
            "height": height,
            "mode": mode,
            "visual_summary": summary,
        }

        extracted_text = (
            f"[Visual Input Attached: {business_input.filename}]\n"
            f"Image Format: {img_format}\n"
            f"Resolution: {width} x {height} px\n"
        )

        business_input.mark_processed(
            extracted_text=extracted_text,
            structured_data=structured_data,
            metadata_updates={"width": width, "height": height, "format": img_format},
        )

    async def _process_audio(self, business_input: BusinessInput, content: bytes) -> None:
        """Transcribe audio using pluggable BaseTranscriptionProvider."""
        provider = get_transcription_provider()
        res = await provider.transcribe(content, business_input.filename)
        
        structured_data = {
            "type": "voice_memo",
            "transcript": res.transcript,
            "confidence": res.confidence,
            "duration_seconds": res.duration_seconds,
            "language": res.language,
            "metadata": res.metadata,
        }

        business_input.mark_processed(
            extracted_text=res.transcript,
            structured_data=structured_data,
            metadata_updates={
                "duration_seconds": res.duration_seconds,
                "confidence": res.confidence,
                "language": res.language,
            },
        )


_input_processor: Optional[InputProcessorService] = None


def get_input_processor() -> InputProcessorService:
    """Return singleton instance of InputProcessorService."""
    global _input_processor
    if _input_processor is None:
        _input_processor = InputProcessorService()
    return _input_processor
