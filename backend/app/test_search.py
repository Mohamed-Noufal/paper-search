"""
Test script for Week 3 - Paper Search System
Run this to verify all components work correctly
"""
import asyncio
import sys
from app.services.arxiv_service import ArxivService
from app.services.semantic_scholar_service import SemanticScholarService
from app.services.openalex_service import OpenAlexService
from app.utils.deduplication import deduplicate_papers
from app.utils.cache import CacheService
from app.services.search_service import UnifiedSearchService


async def test_arxiv():
    """Test arXiv service"""
    print("\n" + "="*60)
    print("TEST 1: arXiv Service")
    print("="*60)
    
    arxiv = ArxivService()
    results = await arxiv.search("machine learning", limit=5)
    
    print(f"✅ Found {len(results)} papers from arXiv")
    if results:
        paper = results[0]
        print(f"\nSample paper:")
        print(f"  Title: {paper['title'][:80]}...")
        print(f"  Authors: {', '.join(paper['authors'][:3])}")
        print(f"  Source ID: {paper['arxiv_id']}")
    
    return len(results) > 0


async def test_semantic_scholar():
    """Test Semantic Scholar service"""
    print("\n" + "="*60)
    print("TEST 2: Semantic Scholar Service")
    print("="*60)
    
    ss = SemanticScholarService()
    results = await ss.search("deep learning", limit=5)
    
    print(f"✅ Found {len(results)} papers from Semantic Scholar")
    if results:
        paper = results[0]
        print(f"\nSample paper:")
        print(f"  Title: {paper['title'][:80]}...")
        print(f"  Authors: {', '.join(paper['authors'][:3])}")
        print(f"  Citations: {paper.get('citation_count', 0)}")
    
    return len(results) > 0


async def test_openalex():
    """Test OpenAlex service"""
    print("\n" + "="*60)
    print("TEST 3: OpenAlex Service")
    print("="*60)
    
    openalex = OpenAlexService()
    results = await openalex.search("neural networks", limit=5)
    
    print(f"✅ Found {len(results)} papers from OpenAlex")
    if results:
        paper = results[0]
        print(f"\nSample paper:")
        print(f"  Title: {paper['title'][:80]}...")
        print(f"  Authors: {', '.join(paper['authors'][:3])}")
        print(f"  Citations: {paper.get('citation_count', 0)}")
    
    return len(results) > 0


async def test_deduplication():
    """Test deduplication logic"""
    print("\n" + "="*60)
    print("TEST 4: Deduplication")
    print("="*60)
    
    # Create duplicate papers
    papers = [
        {"title": "Deep Learning", "arxiv_id": "1234", "source": "arxiv", "doi": None},
        {"title": "Deep Learning", "doi": "10.1234/test", "source": "semantic_scholar", "arxiv_id": "1234"},
        {"title": "Machine Learning Basics", "doi": "10.5678/test", "source": "openalex", "arxiv_id": None},
    ]
    
    deduplicated = deduplicate_papers(papers)
    
    print(f"✅ Original: {len(papers)} papers")
    print(f"✅ After deduplication: {len(deduplicated)} papers")
    print(f"✅ Duplicates removed: {len(papers) - len(deduplicated)}")
    
    return len(deduplicated) == 2


async def test_cache():
    """Test Redis cache"""
    print("\n" + "="*60)
    print("TEST 5: Redis Cache")
    print("="*60)
    
    try:
        cache = CacheService("redis://localhost:6379")
        
        if results['papers']:
            print(f"\nSample results:")
            for i, paper in enumerate(results['papers'][:3], 1):
                print(f"  {i}. {paper['title'][:60]}...")
                print(f"     Source: {paper['source']}, Citations: {paper.get('citation_count', 0)}")
        
        return results['total'] > 0
        
    except Exception as e:
        print(f"❌ Unified search error: {str(e)}")
        return False


async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 WEEK 3 TEST SUITE - PAPER SEARCH SYSTEM")
    print("="*60)
    
    results = {
        "arXiv Service": await test_arxiv(),
        "Semantic Scholar Service": await test_semantic_scholar(),
        "OpenAlex Service": await test_openalex(),
        "Deduplication": await test_deduplication(),
        "Redis Cache": await test_cache(),
        "Unified Search": await test_unified_search()
    }
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test}")
    
    print("\n" + "="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("\n🎉 All tests passed! Week 3 is complete!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code) not cache.is_connected():
            print("❌ Redis not connected - make sure Redis is running")
            return False
        
        print("✅ Redis connected")
        
        # Test set/get
        test_data = {"papers": [], "total": 0, "query": "test"}
        await cache.set_search_results("test query", test_data)
        cached = await cache.get_search_results("test query")
        
        if cached:
            print("✅ Cache set/get working")
            return True
        else:
            print("❌ Cache not working")
            return False
            
    except Exception as e:
        print(f"❌ Cache error: {str(e)}")
        return False


async def test_unified_search():
    """Test unified search service"""
    print("\n" + "="*60)
    print("TEST 6: Unified Search Service")
    print("="*60)
    
    try:
        cache = CacheService("redis://localhost:6379")
        search = UnifiedSearchService(cache_service=cache)
        
        results = await search.search(
            query="transformer models",
            limit=10,
            use_cache=False
        )
        
        print(f"✅ Unified search completed")
        print(f"  Total papers: {results['total']}")
        print(f"  Sources used: {', '.join(results['sources_used'])}")
        print(f"  Cached: {results['cached']}")
        
        if