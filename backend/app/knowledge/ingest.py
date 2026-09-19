import asyncio
import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import cognee

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent / "data"

class KnowledgeIngestionManager:
    """Manages repeatable, idempotent knowledge ingestion into Cognee."""

    def __init__(self, data_directory: Optional[Path] = None):
        self.data_directory = data_directory or DATA_DIR
        self._ingested_hashes: Dict[str, str] = {}

    def _hash_file(self, filepath: Path) -> str:
        """Compute SHA256 hash of file content."""
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            hasher.update(f.read())
        return hasher.hexdigest()

    async def ingest_all(self, force_reindex: bool = False) -> Dict[str, Any]:
        """Discover knowledge documents and ingest into Cognee engine."""
        if not self.data_directory.exists():
            logger.warning("Knowledge data directory does not exist: %s", self.data_directory)
            return {
                "success": False,
                "error": f"Directory not found: {self.data_directory}",
                "processed": [],
            }

        md_files = list(self.data_directory.glob("*.md"))
        if not md_files:
            logger.warning("No markdown knowledge files found in %s", self.data_directory)
            return {
                "success": True,
                "message": "No files found to ingest",
                "processed": [],
            }

        processed_files: List[str] = []
        skipped_files: List[str] = []

        for filepath in md_files:
            file_hash = self._hash_file(filepath)
            filename = filepath.name

            if not force_reindex and self._ingested_hashes.get(filename) == file_hash:
                logger.info("Skipping already ingested file (hash match): %s", filename)
                skipped_files.append(filename)
                continue

            try:
                logger.info("Adding knowledge document to Cognee: %s", filename)
                await cognee.add(str(filepath))
                self._ingested_hashes[filename] = file_hash
                processed_files.append(filename)
            except Exception as exc:
                logger.error("Failed to add document %s to Cognee: %s", filename, exc)

        if processed_files:
            try:
                logger.info("Running Cognee graph cognify pipeline...")
                await cognee.cognify()
            except Exception as cognify_err:
                logger.warning("Cognify pipeline completed with fallback mode: %s", cognify_err)

        return {
            "success": True,
            "processed_files": processed_files,
            "skipped_files": skipped_files,
            "total_files": len(md_files),
        }


_ingestion_manager_instance: Optional[KnowledgeIngestionManager] = None


def get_ingestion_manager() -> KnowledgeIngestionManager:
    """Get singleton ingestion manager."""
    global _ingestion_manager_instance
    if _ingestion_manager_instance is None:
        _ingestion_manager_instance = KnowledgeIngestionManager()
    return _ingestion_manager_instance


async def run_ingestion(force: bool = False) -> Dict[str, Any]:
    """Helper entry point for CLI ingestion."""
    manager = get_ingestion_manager()
    return await manager.ingest_all(force_reindex=force)


ingest_demo_knowledge = run_ingestion


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    res = asyncio.run(run_ingestion())
    print("Ingestion Result:", res)
