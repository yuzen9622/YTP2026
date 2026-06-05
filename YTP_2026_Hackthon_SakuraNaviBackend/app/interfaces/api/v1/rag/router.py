"""RAG knowledge-base API router — list / get / search / ingest / delete."""
from pathlib import Path
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger

from app.application.rag.commands import (
    DeleteDocumentCommand,
    IngestDocumentCommand,
)
from app.application.rag.queries import (
    GetDocumentQuery,
    ListDocumentsQuery,
    SearchKnowledgeBaseQuery,
)
from app.application.rag.frontend_service import RagFrontendApplicationService
from app.application.rag.service import RagApplicationService
from app.core.exceptions import ResourceNotFoundException
from app.domains.rag.exceptions import RagIngestionException
from app.interfaces.api.deps import (
    get_current_user_id,
    get_rag_app_service,
    get_rag_frontend_app_service,
)
from app.interfaces.api.v1.rag.schemas import (
    AnnouncementItem,
    AnnouncementsResponse,
    CategoryCountItem,
    CategoryListResponse,
    DeleteResponse,
    DocumentListResponse,
    DocumentResponse,
    IngestResponse,
    NewsItem,
    NewsResponse,
    SearchRequest,
    SearchResponse,
    SubsidyRecommendationItem,
    SubsidyRecommendationsRequest,
    SubsidyRecommendationsResponse,
)


router = APIRouter(prefix="/rag", tags=["rag"])


_RAG_DOCS_DIR = Path(__file__).resolve().parents[5] / "rag_docs"


@router.get(
    "/categories",
    response_model=CategoryListResponse,
    summary="列出知識庫分類統計",
    description="回傳有資料的分類與其文件數量（count > 0）。",
)
async def list_categories(
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[RagApplicationService, Depends(get_rag_app_service)],
) -> CategoryListResponse:
    dto = await svc.list_categories()
    return CategoryListResponse(
        items=[CategoryCountItem(**item.__dict__) for item in dto.items],
    )


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="列出知識庫文件",
    description="分頁列出 RAG 知識庫文件，可依 category 過濾。",
)
async def list_documents(
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[RagApplicationService, Depends(get_rag_app_service)],
    category: Annotated[
        Optional[str],
        Query(
            description=(
                "分類 tag name：general / youth_subsidy / entrepreneurship / "
                "international / latest_news / policy_news"
            )
        ),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> DocumentListResponse:
    try:
        dto = await svc.list_documents(
            ListDocumentsQuery(category=category, limit=limit, offset=offset)
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return DocumentListResponse(
        items=[DocumentResponse(**d.__dict__) for d in dto.items],
        total=dto.total,
        limit=dto.limit,
        offset=dto.offset,
    )


@router.post(
    "/recommendations/subsidies",
    response_model=SubsidyRecommendationsResponse,
    summary="依履歷推薦青年補助",
    description="使用使用者履歷與可選查詢字串檢索青年補助，回傳標題、金額與局處。",
)
async def recommend_subsidies(
    body: SubsidyRecommendationsRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[RagFrontendApplicationService, Depends(get_rag_frontend_app_service)],
) -> SubsidyRecommendationsResponse:
    try:
        dto = await svc.recommend_subsidies(
            user_id=user_id,
            resume_id=body.resume_id,
            query=body.query,
            limit=body.limit,
        )
    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return SubsidyRecommendationsResponse(
        items=[SubsidyRecommendationItem(**item.__dict__) for item in dto.items]
    )


@router.get(
    "/announcements",
    response_model=AnnouncementsResponse,
    summary="前端最新公告列表",
    description="從 RAG 最新公告分類回傳 title、summary、published_at。",
)
async def list_announcements(
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[RagFrontendApplicationService, Depends(get_rag_frontend_app_service)],
    query: Annotated[Optional[str], Query(max_length=500, description="可選檢索字串")] = None,
    limit: Annotated[int, Query(ge=1, le=20)] = 5,
) -> AnnouncementsResponse:
    try:
        dto = await svc.list_announcements(query=query, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return AnnouncementsResponse(
        items=[AnnouncementItem(**item.__dict__) for item in dto.items]
    )


@router.get(
    "/news",
    response_model=NewsResponse,
    summary="前端新聞專區列表",
    description="從 RAG 新聞分類回傳 date、title、summary。",
)
async def list_news(
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[RagFrontendApplicationService, Depends(get_rag_frontend_app_service)],
    query: Annotated[Optional[str], Query(max_length=500, description="可選檢索字串")] = None,
    limit: Annotated[int, Query(ge=1, le=20)] = 5,
) -> NewsResponse:
    try:
        dto = await svc.list_news(query=query, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return NewsResponse(items=[NewsItem(**item.__dict__) for item in dto.items])


@router.get(
    "/documents/{document_id}",
    response_model=DocumentResponse,
    summary="取得文件詳情",
    description="取得指定 RAG 文件，可選擇是否回傳 chunks 與原始全文內容。",
)
async def get_document(
    document_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[RagApplicationService, Depends(get_rag_app_service)],
    include_chunks: Annotated[bool, Query(description="是否含 chunk 內容")] = True,
    include_raw_content: Annotated[bool, Query(description="是否含原始文件全文內容")] = True,
) -> DocumentResponse:
    try:
        dto = await svc.get_document(
            GetDocumentQuery(
                document_id=document_id,
                include_chunks=include_chunks,
                include_raw_content=include_raw_content,
            )
        )
    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return DocumentResponse(**dto.__dict__)


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="知識庫向量＋關鍵字混合檢索",
    description=(
        "對 RAG 知識庫進行混合檢索（pgvector cosine + tsvector keyword，RRF 融合）。"
        "回傳的 hits 已含命中片段的標題、片段標頭、節錄、source_url 與融合分數。"
    ),
)
async def search(
    body: SearchRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[RagApplicationService, Depends(get_rag_app_service)],
) -> SearchResponse:
    try:
        dto = await svc.search(
            SearchKnowledgeBaseQuery(
                query=body.query, top_k=body.top_k, category=body.category
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return SearchResponse(
        query=dto.query,
        hits=[h.__dict__ for h in dto.hits],
    )


@router.post(
    "/ingest",
    response_model=IngestResponse,
    summary="重新匯入 rag_docs 目錄",
    description=(
        "掃描伺服器專案內建的 `rag_docs/` 目錄，將 markdown 文件解析、切段、嵌入並寫入資料庫。"
        "未變更檔案（content_hash 一致）會被跳過，除非 `force=true`。"
    ),
)
async def ingest(
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[RagApplicationService, Depends(get_rag_app_service)],
    force: Annotated[bool, Query(description="忽略 content_hash，強制重新匯入")] = False,
) -> IngestResponse:
    if not _RAG_DOCS_DIR.is_dir():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"rag_docs directory not found at {_RAG_DOCS_DIR}",
        )
    ingested = skipped = 0
    failed: list[str] = []
    for md_path in sorted(_RAG_DOCS_DIR.glob("*.md")):
        try:
            raw = md_path.read_text(encoding="utf-8")
            result = await svc.ingest_document(
                IngestDocumentCommand(filename=md_path.name, raw_content=raw, force=force)
            )
            if result.was_ingested:
                ingested += 1
            else:
                skipped += 1
        except RagIngestionException as exc:
            failed.append(f"{md_path.name}: {exc.message}")
        except Exception as exc:  # noqa: BLE001
            logger.exception("[rag-api] ingest failed for {}", md_path.name)
            failed.append(f"{md_path.name}: {exc}")
    return IngestResponse(ingested=ingested, skipped=skipped, failed=failed)


@router.delete(
    "/documents/{document_id}",
    response_model=DeleteResponse,
    summary="刪除知識庫文件",
    description="刪除指定 RAG 文件（同時刪除其所有 chunks）。",
)
async def delete_document(
    document_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[RagApplicationService, Depends(get_rag_app_service)],
) -> DeleteResponse:
    try:
        await svc.delete_document(DeleteDocumentCommand(document_id=document_id))
    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return DeleteResponse(id=document_id, deleted=True)
