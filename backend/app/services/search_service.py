"""Search orchestration: embedding -> FAISS -> PostgreSQL -> ranked results."""
import logging
import numpy as np
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.clip_service import CLIPService
from app.ai.faiss_index import FaissIndex
from app.config import settings
from app.database.models import Product
from app.errors import AppError
from app.schemas.product import SearchResult
from app.services.product_service import ProductFilters, apply_filters, to_search_result

logger = logging.getLogger("app.services.search_service")


class SearchService:
    def __init__(
        self,
        clip: CLIPService | None,
        index: FaissIndex,
        image_weight: float = 0.6,
        text_weight: float = 0.4,
        similarity_threshold: float | None = None,
    ) -> None:
        self.clip = clip
        self.index = index
        self.image_weight = image_weight
        self.text_weight = text_weight
        self.similarity_threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else settings.visual_search_similarity_threshold
        )

    # ---- readiness -------------------------------------------------------------
    def _require_index(self) -> None:
        self.index.refresh_if_changed()
        if not self.index.loaded:
            raise AppError(
                "FAISS_UNAVAILABLE",
                "The search index is not available yet. Please try again later.",
                503,
            )

    def _require_ai(self) -> CLIPService:
        if self.clip is None:
            raise AppError(
                "AI_UNAVAILABLE", "The image search model is not available right now.", 503
            )
        return self.clip

    def _fetch_k(self, top_k: int, filters: ProductFilters) -> int:
        """FAISS cannot filter, so with filters we rank the whole (small) catalogue,
        then let PostgreSQL drop non-matching rows. Without filters, over-fetch a little
        in case some indexed products were deactivated since indexing."""
        n = self.index.size
        return n if filters.active else min(n, top_k * 4 + 5)

    # ---- ranking ---------------------------------------------------------------
    def _rank(
        self,
        db: Session,
        hits: list[tuple[int, float]],
        top_k: int,
        filters: ProductFilters,
    ) -> list[SearchResult]:
        if not hits:
            return []
        stmt = apply_filters(select(Product).where(Product.id.in_([pid for pid, _ in hits])), filters)
        products = {p.id: p for p in db.scalars(stmt)}
        results: list[SearchResult] = []
        for pid, score in hits:
            product = products.get(pid)
            if product is None:
                continue
            results.append(to_search_result(product, score))
            if len(results) == top_k:
                break
        return results

        # ---- public API ------------------------------------------------------------
    def search_by_image(
        self, db: Session, image: Image.Image, top_k: int, filters: ProductFilters
    ) -> list[SearchResult]:
        self._require_index()
        clip = self._require_ai()
        vector = clip.generate_image_embedding(image)
        hits = self.index.search(vector, self._fetch_k(top_k, filters))
        results = self._rank(db, hits, top_k, filters)
        if not results:
            return []
        top_similarity = results[0].similarity
        if top_similarity < self.similarity_threshold:
            logger.info(
                "Visual search threshold check: top_similarity=%.4f threshold=%.2f match=false",
                top_similarity,
                self.similarity_threshold,
            )
            return []
        logger.info(
            "Visual search threshold check: top_similarity=%.4f threshold=%.2f match=true",
            top_similarity,
            self.similarity_threshold,
        )
        return results

    def search_by_text(
        self, db: Session, text: str, top_k: int, filters: ProductFilters
    ) -> list[SearchResult]:
        self._require_index()
        clip = self._require_ai()
        vector = clip.generate_text_embedding(text)
        hits = self.index.search(vector, self._fetch_k(top_k, filters))
        return self._rank(db, hits, top_k, filters)

    def search_hybrid(
        self,
        db: Session,
        image: Image.Image | None,
        text: str | None,
        top_k: int,
        filters: ProductFilters,
        image_weight: float | None = None,
        text_weight: float | None = None,
    ) -> list[SearchResult]:
        text = (text or "").strip() or None
        if image is None and text is None:
            raise AppError("INVALID_REQUEST", "Provide an image, a text query, or both.", 400)
        if image is None or text is None:
            if image is not None:
                return self.search_by_image(db, image, top_k, filters)
            return self.search_by_text(db, text or "", top_k, filters)

        self._require_index()
        clip = self._require_ai()
        wi = self.image_weight if image_weight is None else image_weight
        wt = self.text_weight if text_weight is None else text_weight
        if wi < 0 or wt < 0 or (wi + wt) == 0:
            wi, wt = self.image_weight, self.text_weight
        total_w = wi + wt
        wi, wt = wi / total_w, wt / total_w

        n = self.index.size
        image_scores = dict(self.index.search(clip.generate_image_embedding(image), n))
        text_scores = dict(self.index.search(clip.generate_text_embedding(text), n))

        def minmax(scores: dict[int, float]) -> dict[int, float]:
            lo, hi = min(scores.values()), max(scores.values())
            if hi - lo < 1e-9:
                return {k: 1.0 for k in scores}
            return {k: (v - lo) / (hi - lo) for k, v in scores.items()}

        # The two modalities live on different scales, so each is rescaled to [0, 1]
        # across the catalogue before weighting. The returned score is therefore a
        # relative ranking score, not a raw cosine.
        norm_i, norm_t = minmax(image_scores), minmax(text_scores)
        combined = sorted(
            ((pid, wi * norm_i[pid] + wt * norm_t.get(pid, 0.0)) for pid in norm_i),
            key=lambda item: item[1],
            reverse=True,
        )
        return self._rank(db, combined, top_k, filters)

    def similar_to_product(self, db: Session, product_id: int, top_k: int) -> list[SearchResult]:
        self._require_index()
        vector = self.index.get_vector(product_id)
        if vector is None:
            raise AppError(
                "PRODUCT_NOT_INDEXED",
                "This product has not been added to the search index yet.",
                404,
            )
        k = min(self.index.size, top_k * 4 + 6)
        hits = [h for h in self.index.search(np.asarray(vector), k) if h[0] != product_id]
        return self._rank(db, hits, top_k, ProductFilters())
