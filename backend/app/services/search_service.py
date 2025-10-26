import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.services.arxiv_service import ArxivService
from app.services.semantic_scholar_service import SemanticScholarService
from app.services.openalex_service import OpenAlexService
from app.utils.deduplication import deduplicate_papers
from app.utils.cache import CacheService
from app.models.paper import Paper


class UnifiedSearchService:
    """Unified search service that queries multiple sources"""
    
    def __init__(
        self,
        cache_service: CacheService,
        semantic_scholar_api_key: Optional[str] = None,
        openalex_email: Optional[str] = None
    ):
        """Initialize all search services"""
        self.cache = cache_service
        
        # Initialize source services
        self.arxiv = ArxivService()
        self.semantic_scholar = SemanticScholarService(api_key=semantic_scholar_api_key)
        self.openalex = OpenAlexService(email=openalex_email)
        
        self.sources = [self.arxiv, self.semantic_scholar, self.openalex]
    
    async def search(
        self,
        query: str,
        limit: int = 50,
        sources: Optional[List[str]] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Search papers across multiple sources
        
        Args:
            query: Search query string
            limit: Maximum total results to return
            sources: List of sources to search (default: all)
            use_cache: Whether to use cache
            
        Returns:
            {
                "papers": [...],
                "total": int,
                "query": str,
                "sources_used": [...],
                "cached": bool
            }
        """
        # Check cache first
        if use_cache:
            cached = await self.cache.get_search_results(query, limit)
            if cached:
                cached["cached"] = True
                return cached
        
        # Determine which sources to use
        active_sources = self._get_active_sources(sources)
        
        # Search all sources in parallel
        results = await self._parallel_search(query, limit, active_sources)
        
        # Deduplicate papers
        deduplicated = deduplicate_papers(results)
        
        # Sort by relevance (citation count as proxy)
        sorted_papers = sorted(
            deduplicated,
            key=lambda p: p.get("citation_count", 0),
            reverse=True
        )[:limit]
        
        # Prepare response
        response = {
            "papers": sorted_papers,
            "total": len(sorted_papers),
            "query": query,
            "sources_used": [s.source_name for s in active_sources],
            "cached": False
        }
        
        # Cache results
        if use_cache:
            await self.cache.set_search_results(query, response, limit)
        
        return response
    
    async def _parallel_search(
        self,
        query: str,
        limit: int,
        sources: List[Any]
    ) -> List[Dict[str, Any]]:
        """Execute searches in parallel"""
        # Create tasks for each source
        per_source_limit = max(20, limit // len(sources))
        
        tasks = [
            source.search(query, limit=per_source_limit)
            for source in sources
        ]
        
        # Execute in parallel with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            print("Search timeout - returning partial results")
            results = []
        
        # Flatten results and filter errors
        all_papers = []
        for result in results:
            if isinstance(result, list):
                all_papers.extend(result)
            elif isinstance(result, Exception):
                print(f"Source error: {str(result)}")
        
        return all_papers
    
    def _get_active_sources(self, source_names: Optional[List[str]] = None) -> List[Any]:
        """Get active source services"""
        if not source_names:
            return self.sources
        
        source_map = {
            "arxiv": self.arxiv,
            "semantic_scholar": self.semantic_scholar,
            "openalex": self.openalex
        }
        
        return [source_map[name] for name in source_names if name in source_map]
    
    async def get_paper_by_id(
        self,
        paper_id: str,
        source: str,
        db: Session
    ) -> Optional[Dict[str, Any]]:
        """Get a specific paper by ID from a source"""
        # Check database first
        db_paper = self._get_paper_from_db(paper_id, source, db)
        if db_paper:
            return db_paper.to_dict()
        
        # Fetch from source
        source_service = self._get_active_sources([source])
        if not source_service:
            return None
        
        paper_data = await source_service[0].get_paper_by_id(paper_id)
        
        # Save to database
        if paper_data:
            db_paper = self._save_paper_to_db(paper_data, db)
            return db_paper.to_dict() if db_paper else paper_data
        
        return None
    
    def _get_paper_from_db(
        self,
        paper_id: str,
        source: str,
        db: Session
    ) -> Optional[Paper]:
        """Get paper from database"""
        id_field_map = {
            "arxiv": Paper.arxiv_id,
            "semantic_scholar": Paper.semantic_scholar_id,
            "openalex": Paper.openalex_id
        }
        
        id_field = id_field_map.get(source)
        if not id_field:
            return None
        
        return db.query(Paper).filter(id_field == paper_id).first()
    
    def _save_paper_to_db(self, paper_data: Dict[str, Any], db: Session) -> Optional[Paper]:
        """Save paper to database"""
        try:
            # Check if already exists by any ID
            existing = db.query(Paper).filter(
                (Paper.arxiv_id == paper_data.get("arxiv_id")) |
                (Paper.doi == paper_data.get("doi")) |
                (Paper.semantic_scholar_id == paper_data.get("semantic_scholar_id")) |
                (Paper.openalex_id == paper_data.get("openalex_id"))
            ).first()
            
            if existing:
                return existing
            
            # Create new paper
            paper = Paper(
                arxiv_id=paper_data.get("arxiv_id"),
                doi=paper_data.get("doi"),
                semantic_scholar_id=paper_data.get("semantic_scholar_id"),
                openalex_id=paper_data.get("openalex_id"),
                title=paper_data.get("title"),
                abstract=paper_data.get("abstract"),
                authors=paper_data.get("authors"),
                publication_date=paper_data.get("publication_date"),
                pdf_url=paper_data.get("pdf_url"),
                source=paper_data.get("source"),
                citation_count=paper_data.get("citation_count", 0),
                venue=paper_data.get("venue"),
                is_processed=False
            )
            
            db.add(paper)
            db.commit()
            db.refresh(paper)
            
            return paper
            
        except Exception as e:
            db.rollback()
            print(f"Error saving paper: {str(e)}")
            return None
    
    async def save_papers_to_db(
        self,
        papers: List[Dict[str, Any]],
        db: Session
    ) -> List[Paper]:
        """Batch save papers to database"""
        saved = []
        for paper_data in papers:
            paper = self._save_paper_to_db(paper_data, db)
            if paper:
                saved.append(paper)
        return saved