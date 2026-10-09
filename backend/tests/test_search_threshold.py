"""Unit tests for No-Match Visual Search Similarity Threshold behavior."""

from unittest.mock import MagicMock
from PIL import Image
from sqlalchemy.orm import Session

from app.config import settings
from app.schemas.product import SearchResult
from app.services.product_service import ProductFilters
from app.services.search_service import SearchService


def _dummy_image() -> Image.Image:
    return Image.new("RGB", (100, 100), color=(200, 200, 200))


def _make_mock_index() -> MagicMock:
    idx = MagicMock()
    idx.size = 2000
    idx.loaded = True
    return idx


def _make_search_result(product_id: int, similarity: float) -> SearchResult:
    return SearchResult(
        product_id=product_id,
        product_code=f"HF-BR-{product_id:06d}",
        name=f"Jewellery Item {product_id}",
        category="Bracelet",
        material="Gold",
        purity="22K",
        weight=10.0,
        price=500.0,
        image_url=f"/images/item_{product_id}.jpg",
        similarity=similarity,
    )


# A. High similarity (top_sim = 0.90, threshold = 0.80 -> results returned)
def test_threshold_high_similarity():
    service = SearchService(clip=MagicMock(), index=_make_mock_index(), similarity_threshold=0.80)
    service.index.search.return_value = [(10, 0.90), (11, 0.85)]
    
    mock_db = MagicMock(spec=Session)
    mock_results = [_make_search_result(10, 0.90), _make_search_result(11, 0.85)]
    service._rank = MagicMock(return_value=mock_results)

    results = service.search_by_image(mock_db, _dummy_image(), top_k=5, filters=ProductFilters())
    assert len(results) == 2
    assert results[0].similarity == 0.90


# B. Exactly threshold (top_sim = 0.80, threshold = 0.80 -> results returned)
def test_threshold_exact_boundary():
    service = SearchService(clip=MagicMock(), index=_make_mock_index(), similarity_threshold=0.80)
    service.index.search.return_value = [(10, 0.80)]
    
    mock_db = MagicMock(spec=Session)
    mock_results = [_make_search_result(10, 0.80)]
    service._rank = MagicMock(return_value=mock_results)

    results = service.search_by_image(mock_db, _dummy_image(), top_k=5, filters=ProductFilters())
    assert len(results) == 1
    assert results[0].similarity == 0.80


# C. Below threshold (top_sim = 0.79, threshold = 0.80 -> no-match / empty list returned)
def test_threshold_below_cutoff():
    service = SearchService(clip=MagicMock(), index=_make_mock_index(), similarity_threshold=0.80)
    service.index.search.return_value = [(10, 0.79)]
    
    mock_db = MagicMock(spec=Session)
    mock_results = [_make_search_result(10, 0.79)]
    service._rank = MagicMock(return_value=mock_results)

    results = service.search_by_image(mock_db, _dummy_image(), top_k=5, filters=ProductFilters())
    assert results == []


# D. Empty FAISS result (returns empty list)
def test_threshold_empty_faiss_result():
    service = SearchService(clip=MagicMock(), index=_make_mock_index(), similarity_threshold=0.80)
    service.index.search.return_value = []
    
    mock_db = MagicMock(spec=Session)
    service._rank = MagicMock(return_value=[])

    results = service.search_by_image(mock_db, _dummy_image(), top_k=5, filters=ProductFilters())
    assert results == []


# E. Existing normal search (default threshold configured from settings)
def test_threshold_default_config_setting():
    service = SearchService(clip=MagicMock(), index=_make_mock_index())
    assert service.similarity_threshold == settings.visual_search_similarity_threshold
    assert service.similarity_threshold == 0.80


# F. Duplicate/equivalent products (preserves existing ranking & duplicate product items)
def test_threshold_duplicate_products_preserves_ranking():
    service = SearchService(clip=MagicMock(), index=_make_mock_index(), similarity_threshold=0.80)
    service.index.search.return_value = [(1037, 0.95), (25, 0.95)]
    
    mock_db = MagicMock(spec=Session)
    mock_results = [_make_search_result(1037, 0.95), _make_search_result(25, 0.95)]
    service._rank = MagicMock(return_value=mock_results)

    results = service.search_by_image(mock_db, _dummy_image(), top_k=5, filters=ProductFilters())
    assert len(results) == 2
    assert results[0].product_id == 1037
    assert results[1].product_id == 25
