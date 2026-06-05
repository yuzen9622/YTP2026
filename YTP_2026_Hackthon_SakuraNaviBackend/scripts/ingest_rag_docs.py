"""Ingest the project's `rag_docs/` markdown corpus into PostgreSQL.

Usage:
    python -m scripts.ingest_rag_docs                  # default: project rag_docs/
    python -m scripts.ingest_rag_docs --dir other/     # custom directory
    python -m scripts.ingest_rag_docs --force          # ignore content_hash, re-embed
"""
import argparse
import asyncio
import selectors
import sys
from pathlib import Path

from loguru import logger

from app.application.rag.commands import IngestDocumentCommand
from app.application.rag.service import RagApplicationService
from app.domains.rag.exceptions import RagIngestionException
from app.infrastructure.db.session import AsyncSessionFactory
from app.infrastructure.embeddings.factory import build_embedding_client
from app.infrastructure.rag.classifier import build_classifier
from app.infrastructure.rag.jieba_tokenizer import JiebaTokenizer
from app.infrastructure.repositories.rag_repository import RagRepositoryImpl


_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_DIR = _PROJECT_ROOT / "rag_docs"


async def _run(directory: Path, force: bool) -> int:
    if not directory.is_dir():
        logger.error("Directory not found: {}", directory)
        return 1

    files = sorted(directory.glob("*.md"))
    if not files:
        logger.warning("No .md files found in {}", directory)
        return 0

    embedding_client = build_embedding_client()
    tokenizer = JiebaTokenizer()
    classifier = build_classifier()

    ingested = skipped = failed = 0
    try:
        async with AsyncSessionFactory() as session:
            try:
                repo = RagRepositoryImpl(session)
                svc = RagApplicationService(
                    rag_repo=repo,
                    embedding_client=embedding_client,
                    tokenizer=tokenizer,
                    classifier=classifier,
                )
                for md_path in files:
                    raw = md_path.read_text(encoding="utf-8")
                    try:
                        result = await svc.ingest_document(
                            IngestDocumentCommand(
                                filename=md_path.name,
                                raw_content=raw,
                                force=force,
                            )
                        )
                        if result.was_ingested:
                            ingested += 1
                            logger.info(
                                "✓ ingested: {} ({} chunks)",
                                md_path.name, result.document.chunk_count,
                            )
                        else:
                            skipped += 1
                            logger.info("- skipped (unchanged): {}", md_path.name)
                    except RagIngestionException as exc:
                        failed += 1
                        logger.error("✗ failed: {} — {}", md_path.name, exc.message)
                    except Exception as exc:  # noqa: BLE001
                        failed += 1
                        logger.exception("✗ failed: {}", md_path.name)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    finally:
        await embedding_client.close()

    logger.info(
        "Done. ingested={} skipped={} failed={} total={}",
        ingested, skipped, failed, len(files),
    )
    return 0 if failed == 0 else 2


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dir",
        type=Path,
        default=_DEFAULT_DIR,
        help=f"Markdown directory to ingest (default: {_DEFAULT_DIR})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-embed and re-write even when content_hash matches.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    # psycopg async requires SelectorEventLoop on Windows (not ProactorEventLoop)
    return asyncio.run(
        _run(args.dir, args.force),
        loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()),
    )


if __name__ == "__main__":
    sys.exit(main())
