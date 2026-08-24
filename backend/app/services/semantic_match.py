"""
Lightweight semantic-similarity helper used to cross-validate the LLM's own
judgement on RESPONSIBILITY / SOFT_SKILL matches (see app/services/matching.py).

Uses the embedding model already loaded by AIService (all-MiniLM-L6-v2) so no
extra model/download is introduced. Fails safe: if embeddings can't be
computed for any reason (offline, model not cached, etc.) callers get
(None, 0.0) back and simply fall back to the LLM's own verdict.
"""
from __future__ import annotations

import logging
import re
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

_BULLET_RE = re.compile(r"[•\u2022\u25aa\u25cf\u2013\u2014\-]\s+")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")


def split_into_sentences(text: str) -> List[str]:
    """Splits resume raw text into bullet/sentence-level chunks for evidence search."""
    if not text:
        return []
    normalized = _BULLET_RE.sub("\n", text)
    parts = _SENTENCE_SPLIT_RE.split(normalized)
    return [p.strip() for p in parts if p and len(p.strip()) > 8]


def best_semantic_match(query: str, candidates: List[str], ai_service) -> Tuple[Optional[str], float]:
    """
    Returns (best_matching_sentence, cosine_similarity) for `query` against a
    list of resume sentences/bullets.
    """
    if not query or not candidates:
        return None, 0.0
    try:
        import numpy as np

        query_vec = ai_service.embed(query)
        cand_vecs = ai_service.embed_batch(candidates)

        query_norm = float(np.linalg.norm(query_vec)) or 1e-9
        cand_norms = np.linalg.norm(cand_vecs, axis=1)
        cand_norms[cand_norms == 0] = 1e-9

        sims = (cand_vecs @ query_vec) / (cand_norms * query_norm)
        best_idx = int(np.argmax(sims))
        return candidates[best_idx], float(sims[best_idx])
    except Exception as e:  # pragma: no cover - defensive, environment-dependent
        logger.warning("Semantic match unavailable, falling back to LLM-only evidence: %s", e)
        return None, 0.0
