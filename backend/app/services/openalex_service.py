import httpx
from typing import List, Dict, Any, Optional
from app.services.base_source import PaperSource

class OpenAlexService(PaperSource):
    """OpenAlex API service"""
    
    BASE_URL = "https://api.openalex.org"
    
    def __init__(self, email: Optional[str] = None):
        super().__init__()
        self.source_name = "openalex"
        self.email = email  # Polite pool access (faster rate limits)
    
    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search OpenAlex papers"""
        url = f"{self.BASE_URL}/works"
        params = {
            "search": query,
            "per_page": min(limit, 200),  # API max is 200
            "sort": "relevance_score:desc",
            "mailto": self.email  # For polite pool
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                papers = data.get("results", [])
                
                return [self.normalize_paper(paper) for paper in papers if paper]
                
        except Exception as e:
            print(f"OpenAlex search error: {str(e)}")
            return []
    
    async def get_paper_by_id(self, openalex_id: str) -> Optional[Dict[str, Any]]:
        """Get paper by OpenAlex ID"""
        # OpenAlex IDs start with 'W' followed by numbers
        if not openalex_id.startswith("W"):
            openalex_id = f"W{openalex_id}"
        
        url = f"{self.BASE_URL}/works/{openalex_id}"
        params = {"mailto": self.email}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                paper = response.json()
                return self.normalize_paper(paper)
                
        except Exception as e:
            print(f"OpenAlex get paper error: {str(e)}")
            return None
    
    def normalize_paper(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert OpenAlex format to standard format"""
        # Extract IDs
        openalex_id = raw_data.get("id", "").split("/")[-1]
        doi = raw_data.get("doi", "").replace("https://doi.org/", "") if raw_data.get("doi") else None
        
        # Extract arXiv ID from IDs array
        arxiv_id = None
        for ext_id in raw_data.get("ids", {}).values():
            if isinstance(ext_id, str) and "arxiv" in ext_id.lower():
                arxiv_id = ext_id.split("/")[-1]
                break
        
        # Extract PDF URL
        pdf_url = None
        best_oa = raw_data.get("best_oa_location")
        if best_oa and isinstance(best_oa, dict):
            pdf_url = best_oa.get("pdf_url")
        
        # Extract authors
        authors = []
        for authorship in raw_data.get("authorships", []):
            author = authorship.get("author", {})
            if author and isinstance(author, dict):
                authors.append(author.get("display_name", "Unknown"))
        
        # Extract venue/journal
        venue = None
        primary_location = raw_data.get("primary_location", {})
        if primary_location and isinstance(primary_location, dict):
            source = primary_location.get("source", {})
            if source and isinstance(source, dict):
                venue = source.get("display_name")
        
        # Parse publication date
        pub_date = self._parse_date(raw_data.get("publication_date"))
        
        return {
            "title": raw_data.get("title", ""),
            "abstract": self._safe_get(raw_data, "abstract_inverted_index") or "",  # Note: needs processing
            "authors": authors,
            "publication_date": pub_date,
            "pdf_url": pdf_url,
            "source": "openalex",
            "source_id": openalex_id,
            "openalex_id": openalex_id,
            "arxiv_id": arxiv_id,
            "doi": doi,
            "citation_count": raw_data.get("cited_by_count", 0),
            "venue": venue
        }