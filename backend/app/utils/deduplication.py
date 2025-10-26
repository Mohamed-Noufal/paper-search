from typing import List, Dict, Any
from difflib import SequenceMatcher

def deduplicate_papers(papers: List[Dict[str, Any]], similarity_threshold: float = 0.85) -> List[Dict[str, Any]]:
    """
    Deduplicate papers from multiple sources
    
    Strategy:
    1. Group by exact ID matches (DOI, arXiv ID)
    2. Group by similar titles (fuzzy matching)
    3. Merge metadata from multiple sources
    4. Prioritize: Semantic Scholar > arXiv > OpenAlex (for metadata quality)
    
    Args:
        papers: List of paper dictionaries
        similarity_threshold: Title similarity threshold (0-1)
        
    Returns:
        Deduplicated list of papers
    """
    if not papers:
        return []
    
    # Track seen papers
    seen_ids = {}
    seen_titles = {}
    deduplicated = []
    
    # Source priority for metadata merging
    source_priority = {"semantic_scholar": 3, "arxiv": 2, "openalex": 1}
    
    for paper in papers:
        # Check for ID matches
        matching_paper = None
        
        # Check DOI
        if paper.get("doi"):
            doi_key = paper["doi"].lower().strip()
            if doi_key in seen_ids:
                matching_paper = seen_ids[doi_key]
        
        # Check arXiv ID
        if not matching_paper and paper.get("arxiv_id"):
            arxiv_key = paper["arxiv_id"].lower().strip()
            if arxiv_key in seen_ids:
                matching_paper = seen_ids[arxiv_key]
        
        # Check Semantic Scholar ID
        if not matching_paper and paper.get("semantic_scholar_id"):
            ss_key = paper["semantic_scholar_id"].lower().strip()
            if ss_key in seen_ids:
                matching_paper = seen_ids[ss_key]
        
        # Check OpenAlex ID
        if not matching_paper and paper.get("openalex_id"):
            oa_key = paper["openalex_id"].lower().strip()
            if oa_key in seen_ids:
                matching_paper = seen_ids[oa_key]
        
        # Check title similarity
        if not matching_paper:
            title = paper.get("title", "").lower().strip()
            if title:
                for existing_title, existing_paper in seen_titles.items():
                    similarity = _title_similarity(title, existing_title)
                    if similarity >= similarity_threshold:
                        matching_paper = existing_paper
                        break
        
        # If duplicate found, merge metadata
        if matching_paper:
            merged = _merge_papers(matching_paper, paper, source_priority)
            # Update in place
            idx = deduplicated.index(matching_paper)
            deduplicated[idx] = merged
            
            # Update tracking dictionaries
            _update_tracking(merged, seen_ids, seen_titles)
        else:
            # New unique paper
            deduplicated.append(paper)
            _update_tracking(paper, seen_ids, seen_titles)
    
    return deduplicated


def _title_similarity(title1: str, title2: str) -> float:
    """Calculate similarity between two titles"""
    return SequenceMatcher(None, title1, title2).ratio()


def _merge_papers(paper1: Dict[str, Any], paper2: Dict[str, Any], source_priority: Dict[str, int]) -> Dict[str, Any]:
    """
    Merge two papers, preferring higher quality metadata
    
    Priority:
    - IDs: Collect all unique IDs
    - Title: From higher priority source
    - Abstract: Longest non-empty abstract
    - Authors: From higher priority source (more complete)
    - PDF URL: First available
    - Citation count: Maximum
    """
    # Determine priority
    p1_priority = source_priority.get(paper1.get("source", ""), 0)
    p2_priority = source_priority.get(paper2.get("source", ""), 0)
    
    primary = paper1 if p1_priority >= p2_priority else paper2
    secondary = paper2 if p1_priority >= p2_priority else paper1
    
    merged = primary.copy()
    
    # Merge IDs (collect all)
    for id_field in ["arxiv_id", "doi", "semantic_scholar_id", "openalex_id"]:
        if not merged.get(id_field) and secondary.get(id_field):
            merged[id_field] = secondary[id_field]
    
    # Use longest abstract
    if len(secondary.get("abstract", "")) > len(merged.get("abstract", "")):
        merged["abstract"] = secondary["abstract"]
    
    # Use PDF URL if primary doesn't have one
    if not merged.get("pdf_url") and secondary.get("pdf_url"):
        merged["pdf_url"] = secondary["pdf_url"]
    
    # Use max citation count
    merged["citation_count"] = max(
        merged.get("citation_count", 0),
        secondary.get("citation_count", 0)
    )
    
    # Use venue if not present
    if not merged.get("venue") and secondary.get("venue"):
        merged["venue"] = secondary["venue"]
    
    # Combine sources
    sources = [merged.get("source")]
    if secondary.get("source") and secondary["source"] not in sources:
        sources.append(secondary["source"])
    merged["sources"] = sources
    
    return merged


def _update_tracking(paper: Dict[str, Any], seen_ids: Dict, seen_titles: Dict):
    """Update tracking dictionaries with paper IDs and title"""
    # Track by IDs
    if paper.get("doi"):
        seen_ids[paper["doi"].lower().strip()] = paper
    if paper.get("arxiv_id"):
        seen_ids[paper["arxiv_id"].lower().strip()] = paper
    if paper.get("semantic_scholar_id"):
        seen_ids[paper["semantic_scholar_id"].lower().strip()] = paper
    if paper.get("openalex_id"):
        seen_ids[paper["openalex_id"].lower().strip()] = paper
    
    # Track by title
    title = paper.get("title", "").lower().strip()
    if title:
        seen_titles[title] = paper