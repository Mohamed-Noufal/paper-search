from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

class PaperSource(ABC):
    """Abstract base class for paper search sources"""
    
    def __init__(self):
        self.source_name = self.__class__.__name__.replace('Service', '').lower()
    
    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search papers from the source
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of paper dictionaries with standardized schema
        """
        pass
    
    @abstractmethod
    async def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single paper by its ID
        
        Args:
            paper_id: Source-specific paper identifier
            
        Returns:
            Paper dictionary or None if not found
        """
        pass
    
    def normalize_paper(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert source-specific format to standardized format
        
        Standard schema:
        {
            "title": str,
            "abstract": str,
            "authors": List[str],
            "publication_date": datetime or None,
            "pdf_url": str or None,
            "source": str,
            "source_id": str,
            "doi": str or None,
            "citation_count": int,
            "venue": str or None
        }
        """
        raise NotImplementedError("Each source must implement normalize_paper")
    
    def _safe_get(self, data: Dict, *keys, default=None):
        """Safely get nested dictionary values"""
        for key in keys:
            if isinstance(data, dict):
                data = data.get(key, default)
            else:
                return default
        return data if data is not None else default
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse various date formats to datetime"""
        if not date_str:
            return None
        
        try:
            # Try common formats
            for fmt in ["%Y-%m-%d", "%Y-%m", "%Y"]:
                try:
                    return datetime.strptime(str(date_str)[:10], fmt)
                except ValueError:
                    continue
            return None
        except Exception:
            return None