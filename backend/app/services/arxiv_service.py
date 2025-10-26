import httpx
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.services.base_source import PaperSource

class ArxivService(PaperSource):
    """arXiv API service for searching papers"""
    
    BASE_URL = "http://export.arxiv.org/api/query"
    
    def __init__(self):
        super().__init__()
        self.source_name = "arxiv"
    
    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search arXiv papers"""
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": min(limit, 50),  # arXiv max per request
            "sortBy": "relevance",
            "sortOrder": "descending"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                
                papers = self._parse_arxiv_xml(response.text)
                return [self.normalize_paper(paper) for paper in papers]
                
        except Exception as e:
            print(f"arXiv search error: {str(e)}")
            return []
    
    async def get_paper_by_id(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """Get paper by arXiv ID"""
        params = {
            "id_list": arxiv_id,
            "max_results": 1
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                
                papers = self._parse_arxiv_xml(response.text)
                if papers:
                    return self.normalize_paper(papers[0])
                return None
                
        except Exception as e:
            print(f"arXiv get paper error: {str(e)}")
            return None
    
    def _parse_arxiv_xml(self, xml_content: str) -> List[Dict[str, Any]]:
        """Parse arXiv API XML response"""
        papers = []
        
        try:
            root = ET.fromstring(xml_content)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            for entry in root.findall('atom:entry', ns):
                paper = {
                    'id': entry.find('atom:id', ns).text.split('/abs/')[-1],
                    'title': entry.find('atom:title', ns).text.strip().replace('\n', ' '),
                    'summary': entry.find('atom:summary', ns).text.strip().replace('\n', ' '),
                    'authors': [
                        author.find('atom:name', ns).text 
                        for author in entry.findall('atom:author', ns)
                    ],
                    'published': entry.find('atom:published', ns).text,
                    'updated': entry.find('atom:updated', ns).text,
                    'pdf_url': None,
                    'doi': None
                }
                
                # Get PDF link
                for link in entry.findall('atom:link', ns):
                    if link.get('title') == 'pdf':
                        paper['pdf_url'] = link.get('href')
                    elif link.get('title') == 'doi':
                        paper['doi'] = link.get('href')
                
                papers.append(paper)
                
        except Exception as e:
            print(f"XML parsing error: {str(e)}")
        
        return papers
    
    def normalize_paper(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert arXiv format to standard format"""
        return {
            "title": raw_data.get("title", ""),
            "abstract": raw_data.get("summary", ""),
            "authors": raw_data.get("authors", []),
            "publication_date": self._parse_date(raw_data.get("published")),
            "pdf_url": raw_data.get("pdf_url"),
            "source": "arxiv",
            "source_id": raw_data.get("id"),
            "arxiv_id": raw_data.get("id"),
            "doi": raw_data.get("doi"),
            "citation_count": 0,  # arXiv doesn't provide citation counts
            "venue": None
        }