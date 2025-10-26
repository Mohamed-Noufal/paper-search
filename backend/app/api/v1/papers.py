from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.search_service import UnifiedSearchService
from app.utils.cache import CacheService
from app.core.config import settings

router = APIRouter(prefix="/papers", tags=["papers"])

# Initialize services (will be properly done in main.py)
cache_service = CacheService(settings.REDIS_URL)
search_service = UnifiedSearchService(
    cache_service=cache_service,
    semantic_scholar_api_key=getattr(settings, 'SEMANTIC_SCHOLAR_API_KEY', None),
    openalex_email=getattr(settings, 'OPENALEX_EMAIL', None)
)


# Request/Response Models
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(50, ge=1, le=100)
    sources: Optional[List[str]] = Field(None, description="Specific sources to search")
    use_cache: bool = Field(True, description="Use cached results")


class PaperResponse(BaseModel):
    id: Optional[int] = None
    title: str
    abstract: Optional[str] = None
    authors: List[str] = []
    publication_date: Optional[str] = None
    pdf_url: Optional[str] = None
    source: str
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None
    semantic_scholar_id: Optional[str] = None
    openalex_id: Optional[str] = None
    citation_count: int = 0
    venue: Optional[str] = None


class SearchResponse(BaseModel):
    papers: List[dict]
    total: int
    query: str
    sources_used: List[str]
    cached: bool


# Endpoints
@router.get("/search", response_model=SearchResponse)
async def search_papers(
    query: str = Query(..., min_length=1, max_length=500, description="Search query"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    sources: Optional[str] = Query(None, description="Comma-separated sources (arxiv,semantic_scholar,openalex)"),
    use_cache: bool = Query(True, description="Use cached results"),
    db: Session = Depends(get_db)
):
    """
    Search for papers across multiple academic databases
    
    **Sources:**
    - arxiv: arXiv.org preprints
    - semantic_scholar: Semantic Scholar corpus
    - openalex: OpenAlex open catalog
    
    **Example:**
    ```
    GET /api/v1/papers/search?query=deep%20learning&limit=20&sources=arxiv,semantic_scholar
    ```
    """
    try:
        # Parse sources
        source_list = None
        if sources:
            source_list = [s.strip() for s in sources.split(",")]
            valid_sources = {"arxiv", "semantic_scholar", "openalex"}
            if not all(s in valid_sources for s in source_list):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid sources. Valid options: arxiv, semantic_scholar, openalex"
                )
        
        # Execute search
        results = await search_service.search(
            query=query,
            limit=limit,
            sources=source_list,
            use_cache=use_cache
        )
        
        # Save new papers to database (async background task would be better)
        if results["papers"]:
            await search_service.save_papers_to_db(results["papers"], db)
        
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/paper/{source}/{paper_id}", response_model=PaperResponse)
async def get_paper_by_id(
    source: str,
    paper_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific paper by its ID from a source
    
    **Parameters:**
    - source: arxiv, semantic_scholar, or openalex
    - paper_id: Source-specific paper ID
    
    **Example:**
    ```
    GET /api/v1/papers/paper/arxiv/2301.12345
    ```
    """
    valid_sources = {"arxiv", "semantic_scholar", "openalex"}
    if source not in valid_sources:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source. Valid options: {valid_sources}"
        )
    
    try:
        paper = await search_service.get_paper_by_id(paper_id, source, db)
        
        if not paper:
            raise HTTPException(
                status_code=404,
                detail=f"Paper not found: {paper_id}"
            )
        
        return paper
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch paper: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Check if search services are operational"""
    return {
        "status": "healthy",
        "redis_connected": cache_service.is_connected(),
        "services": {
            "arxiv": "operational",
            "semantic_scholar": "operational",
            "openalex": "operational"
        }
    }


@router.delete("/cache")
async def clear_cache():
    """Clear search cache (admin endpoint - add auth later)"""
    try:
        success = await cache_service.clear_all()
        return {
            "success": success,
            "message": "Cache cleared" if success else "Failed to clear cache"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.get("/stats")
async def get_search_stats(db: Session = Depends(get_db)):
    """Get statistics about papers in the database"""
    from app.models.paper import Paper
    from sqlalchemy import func
    
    try:
        total_papers = db.query(func.count(Paper.id)).scalar()
        
        papers_by_source = db.query(
            Paper.source,
            func.count(Paper.id)
        ).group_by(Paper.source).all()
        
        return {
            "total_papers": total_papers,
            "by_source": {source: count for source, count in papers_by_source},
            "processed_papers": db.query(func.count(Paper.id)).filter(
                Paper.is_processed == True
            ).scalar()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )