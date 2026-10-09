"""FAISS (CPU) IndexFlatIP wrapper that maps FAISS positions to PostgreSQL product IDs.

Vectors are L2-normalised, so inner product == cosine similarity.
The index is serialised through NumPy so Windows paths with non-ASCII characters work.
"""
import json
import logging
import os
import threading
from pathlib import Path

import faiss
import numpy as np

logger = logging.getLogger(__name__)


class FaissIndex:
    def __init__(self, index_path: Path, mapping_path: Path) -> None:
        self.index_path = Path(index_path)
        self.mapping_path = Path(mapping_path)
        self._index: faiss.Index | None = None
        self._ids: list[int] = []
        self._id_to_pos: dict[int, int] = {}
        self._mtime: int | None = None
        self._lock = threading.RLock()

    @property
    def loaded(self) -> bool:
        return self._index is not None

    @property
    def size(self) -> int:
        return int(self._index.ntotal) if self._index is not None else 0

    def load(self) -> bool:
        """Load index + mapping from disk. Keeps the previous index if loading fails."""
        with self._lock:
            try:
                self._mtime = self.index_path.stat().st_mtime_ns
            except FileNotFoundError:
                return False
            try:
                index = faiss.deserialize_index(np.fromfile(self.index_path, dtype=np.uint8))
                mapping = json.loads(self.mapping_path.read_text(encoding="utf-8"))
                ids = [int(mapping[str(i)]) for i in range(index.ntotal)]
            except Exception as exc:  # corrupt/mismatched files must not crash the API
                logger.warning("Could not load FAISS index: %s", type(exc).__name__)
                return False
            self._index = index
            self._ids = ids
            self._id_to_pos = {pid: pos for pos, pid in enumerate(ids)}
            logger.info("FAISS index loaded: %d vectors", index.ntotal)
            return True

    def refresh_if_changed(self) -> None:
        """Pick up a re-created index without restarting the server."""
        try:
            mtime = self.index_path.stat().st_mtime_ns
        except FileNotFoundError:
            return
        if mtime != self._mtime:
            self.load()

    def build(self, embeddings: np.ndarray, product_ids: list[int]) -> None:
        emb = np.ascontiguousarray(embeddings, dtype="float32")
        if emb.ndim != 2 or emb.shape[0] != len(product_ids) or emb.shape[0] == 0:
            raise ValueError("embeddings must be a non-empty 2D array matching product_ids")
        faiss.normalize_L2(emb)
        index = faiss.IndexFlatIP(emb.shape[1])
        index.add(emb)

        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        mapping = {str(pos): int(pid) for pos, pid in enumerate(product_ids)}
        map_tmp = self.mapping_path.with_name(self.mapping_path.name + ".tmp")
        idx_tmp = self.index_path.with_name(self.index_path.name + ".tmp")
        map_tmp.write_text(json.dumps(mapping), encoding="utf-8")
        faiss.serialize_index(index).tofile(idx_tmp)
        os.replace(map_tmp, self.mapping_path)
        os.replace(idx_tmp, self.index_path)  # index last: its mtime triggers reloads
        self.load()

    def add_single(self, embedding: np.ndarray, product_id: int) -> None:
        """Add a single product vector to the index and persist to disk."""
        with self._lock:
            emb = np.ascontiguousarray(embedding.reshape(1, -1), dtype="float32")
            faiss.normalize_L2(emb)
            if self._index is None:
                self._index = faiss.IndexFlatIP(emb.shape[1])
                self._ids = []
                self._id_to_pos = {}

            pos = len(self._ids)
            self._index.add(emb)
            self._ids.append(product_id)
            self._id_to_pos[product_id] = pos

            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            mapping = {str(i): int(pid) for i, pid in enumerate(self._ids)}
            map_tmp = self.mapping_path.with_name(self.mapping_path.name + ".tmp")
            idx_tmp = self.index_path.with_name(self.index_path.name + ".tmp")
            map_tmp.write_text(json.dumps(mapping), encoding="utf-8")
            faiss.serialize_index(self._index).tofile(idx_tmp)
            os.replace(map_tmp, self.mapping_path)
            os.replace(idx_tmp, self.index_path)
            self._mtime = self.index_path.stat().st_mtime_ns
            logger.info("Added product %d to FAISS index. Total vectors: %d", product_id, self._index.ntotal)

    def search(self, vector: np.ndarray, k: int) -> list[tuple[int, float]]:
        """Return [(product_id, score)] sorted by descending score."""
        with self._lock:
            if self._index is None or self._index.ntotal == 0:
                return []
            k = max(1, min(k, self._index.ntotal))
            query = np.ascontiguousarray(vector.reshape(1, -1), dtype="float32")
            scores, positions = self._index.search(query, k)
            return [
                (self._ids[pos], float(score))
                for score, pos in zip(scores[0], positions[0])
                if pos >= 0
            ]

    def get_vector(self, product_id: int) -> np.ndarray | None:
        with self._lock:
            pos = self._id_to_pos.get(product_id)
            if self._index is None or pos is None:
                return None
            return self._index.reconstruct(pos)
