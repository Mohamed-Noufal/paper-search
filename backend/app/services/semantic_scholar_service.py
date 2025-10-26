import httpx
from typing import List, Dict, Any, Optional
from app.services.base_source import PaperSource

class SemanticScholarService(PaperSource):
    """Semantic Scholar API service"""
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.source_name = "semantic_scholar"
        self.api_key = api_key
        self.headers = {}
        if api_key:
            self.headers["x-api-key"] = api_key
    
    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search Semantic Scholar papers"""
        url = f"{self.BASE_URL}/paper/search"
        params = {
            "query": query,
            "limit": min(limit, 100),  # API max is 100
            "fields": "paperId,title,abstract,authors,year,citationCount,venue,openAccessPdf,externalIds"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params, headers=self.headers)
                response.raise_for_status()
                
                data = response.json()
                papers = data.get("data", [])
                
                return [self.normalize_paper(paper) for paper in papers if paper]
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                print("Semantic Scholar rate limit hit")
            else:
                print(f"Semantic Scholar search error: {str(e)}")
            return []
        except Exception as e:
            print(f"Semantic Scholar search error: {str(e)}")
            return []
    
    async def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Get paper by Semantic Scholar ID"""
        url = f"{self.BASE_URL}/paper/{paper_id}"
        params = {
            "fields": "paperId,title,abstract,authors,year,citationCount,venue,openAccessPdf,externalIds"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params, headers=self.headers)
                response.raise_for_status()
                
                paper = response.json()
                return self.normalize_paper(paper)
                
        except Exception as e:
            print(f"Semantic Scholar get paper error: {str(e)}")
            return None
    
    def normalize_paper(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Semantic Scholar format to standard format"""
        # Extract external IDs
        external_ids = raw_data.get("externalIds", {}) or {}
        arxiv_id = external_ids.get("ArXiv")
        doi = external_ids.get("DOI")
        
        # Extract PDF URL
        pdf_url = None
        open_access = raw_data.get("openAccessPdf")
        if open_access and isinstance(open_access, dict):
            pdf_url = open_access.get("url")
        
        # Extract authors
        authors = []
        for author in raw_data.get("authors", []):
            if isinstance(author, dict):
                authors.append(author.get("name", "Unknown"))
            else:
                authors.append(str(author))
        
        # Parse year to date
        year = raw_data.get("year")
        pub_date = self._parse_date(f"{year}-01-01") if year else None
        
        return {
            "title": raw_data.get("title", ""),
            "abstract": raw_data.get("abstract", ""),
            "authors": authors,
            "publication_date": pub_date,
            "pdf_url": pdf_url,
            "source": "semantic_scholar",
            "source_id": raw_data.get("paperId"),
            "semantic_scholar_id": raw_data.get("paperId"),
            "arxiv_id": arxiv_id,
            "doi": doi,
            "citation_count": raw_data.get("citationCount", 0),
            "venue": raw_data.get("venue")
        }