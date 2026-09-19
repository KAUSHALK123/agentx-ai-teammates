import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import cognee

TEST_QUERIES = [
    "What is the refund policy for a delayed order?",
    "When does a refund require human approval?",
    "When should a high-severity complaint be escalated?",
    "What information is required before processing a refund?",
    "What are the lead qualification rules?",
    "How should an enterprise lead be handled?",
    "What are the return conditions?",
    "What operational issues require escalation?",
    "What is the response policy for serious complaints?",
    "What products are available?",
]

async def main():
    data_dir = Path(__file__).parent.parent / "app" / "knowledge" / "data"
    files = list(data_dir.glob("*.md"))
    print(f"Discovered {len(files)} knowledge files in {data_dir}")

    for f in files:
        print(f"Adding document to Cognee: {f.name}")
        await cognee.add(str(f))

    try:
        print("Attempting cognify graph enrichment...")
        await cognee.cognify()
    except Exception as exc:
        print(f"Cognify skipped (no external LLM key set; using vector chunk index): {exc}")

    print("\n--- Running 10 Retrieval Test Queries ---")
    for i, q in enumerate(TEST_QUERIES, 1):
        print(f"\nQuery #{i}: {q}")
        try:
            results = await cognee.search(q, cognee.SearchType.CHUNKS)
            print(f"Found {len(results) if results else 0} chunks")
            if results:
                first = results[0]
                text = getattr(first, 'text', str(first))
                print(f"Sample chunk: {text[:250]}")
        except Exception as err:
            print(f"Search query error: {err}")

if __name__ == "__main__":
    asyncio.run(main())

