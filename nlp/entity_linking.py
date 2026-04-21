from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"

DEFAULT_ENTITY_FILES = [
    DATA_DIR / "entities.csv",
    DATA_DIR / "entities_auto.csv",
]
ALIAS_MAP_PATH = CONFIG_DIR / "alias_map.json"

TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
ARTICLE_RE = re.compile(r"^(?:the|a|an)\s+", flags=re.IGNORECASE)


def _tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def _cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    if not vec_a or not vec_b:
        return 0.0
    shared = set(vec_a) & set(vec_b)
    numerator = sum(vec_a[token] * vec_b[token] for token in shared)
    denominator_a = math.sqrt(sum(value * value for value in vec_a.values()))
    denominator_b = math.sqrt(sum(value * value for value in vec_b.values()))
    if denominator_a == 0 or denominator_b == 0:
        return 0.0
    return numerator / (denominator_a * denominator_b)


def _build_tfidf_vectors(texts: list[str]) -> list[dict[str, float]]:
    tokenized = [_tokenize(text) for text in texts]
    doc_count = len(texts)
    document_frequency: Counter[str] = Counter()
    for tokens in tokenized:
        document_frequency.update(set(tokens))

    vectors = []
    for tokens in tokenized:
        term_frequency = Counter(tokens)
        vector: dict[str, float] = {}
        token_total = max(len(tokens), 1)
        for token, count in term_frequency.items():
            tf = count / token_total
            idf = math.log((1 + doc_count) / (1 + document_frequency[token])) + 1
            vector[token] = tf * idf
        vectors.append(vector)
    return vectors


def _read_csv_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _load_alias_map(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return {str(key).strip(): str(value).strip() for key, value in raw.items()}


def normalize_mention(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", str(text)).strip(" .,:;!?\"'")
    cleaned = ARTICLE_RE.sub("", cleaned)
    return cleaned.strip()


class EntityLinker:
    def __init__(
        self,
        entity_files: list[Path] | None = None,
        alias_map_path: Path = ALIAS_MAP_PATH,
        threshold: float = 0.35,
    ) -> None:
        self.entity_files = entity_files or DEFAULT_ENTITY_FILES
        self.alias_map = _load_alias_map(alias_map_path)
        self.threshold = threshold
        self.entities: dict[str, dict] = {}
        self.alias_index: dict[str, str] = {}
        self._load_entities()

    def _load_entities(self) -> None:
        for path in self.entity_files:
            default_source = "auto" if "auto" in path.stem else "manual"
            for row in _read_csv_rows(path):
                name = normalize_mention(row.get("name", ""))
                if not name:
                    continue
                current = self.entities.get(name)
                incoming = {
                    "name": name,
                    "type": row.get("type", "Entity") or "Entity",
                    "source": row.get("source", default_source) or default_source,
                }
                if current and current.get("source") == "manual" and incoming["source"] != "manual":
                    continue
                self.entities[name] = incoming

        for alias, canonical in self.alias_map.items():
            alias_key = normalize_mention(alias).casefold()
            canonical_name = normalize_mention(canonical)
            if canonical_name:
                self.alias_index[alias_key] = canonical_name

        for name in self.entities:
            self.alias_index.setdefault(name.casefold(), name)

    def known_entity_names(self) -> list[str]:
        return list(self.entities.keys())

    def _candidate_rows(self, entity_type: str | None) -> list[dict]:
        rows = list(self.entities.values())
        if entity_type:
            typed = [row for row in rows if row.get("type") == entity_type]
            if typed:
                return typed
        return rows

    def _score_candidates(self, mention: str, context: str, candidates: list[dict]) -> tuple[dict | None, float]:
        mention_doc = f"{mention} {context}".strip()
        candidate_docs = [
            " ".join(
                filter(
                    None,
                    [
                        candidate["name"],
                        candidate.get("type", ""),
                        " ".join(
                            alias for alias, canonical in self.alias_map.items()
                            if normalize_mention(canonical) == candidate["name"]
                        ),
                    ],
                )
            )
            for candidate in candidates
        ]
        vectors = _build_tfidf_vectors([mention_doc] + candidate_docs)
        mention_vector = vectors[0]
        best_candidate = None
        best_score = 0.0
        for candidate, vector in zip(candidates, vectors[1:]):
            score = _cosine_similarity(mention_vector, vector)
            if normalize_mention(mention).casefold() == candidate["name"].casefold():
                score = max(score, 0.99)
            if score > best_score:
                best_score = score
                best_candidate = candidate
        return best_candidate, best_score

    def register_entity(self, name: str, entity_type: str, source: str = "auto") -> dict:
        canonical_name = normalize_mention(name)
        row = {
            "name": canonical_name,
            "type": entity_type or "Entity",
            "source": source,
        }
        self.entities[canonical_name] = row
        self.alias_index.setdefault(canonical_name.casefold(), canonical_name)
        return row

    def resolve_entity(self, mention: str, context: str = "", entity_type: str | None = None) -> dict:
        cleaned = normalize_mention(mention)
        alias_hit = self.alias_index.get(cleaned.casefold())
        if alias_hit and alias_hit in self.entities:
            row = self.entities[alias_hit].copy()
            row["score"] = 1.0
            row["created"] = False
            return row

        candidates = self._candidate_rows(entity_type)
        best_candidate, best_score = self._score_candidates(cleaned, context, candidates)
        if best_candidate and best_score >= self.threshold:
            row = best_candidate.copy()
            row["score"] = round(best_score, 4)
            row["created"] = False
            return row

        row = self.register_entity(cleaned, entity_type or "Entity", source="auto").copy()
        row["score"] = round(best_score, 4)
        row["created"] = True
        return row


_DEFAULT_LINKER: EntityLinker | None = None


def get_default_linker() -> EntityLinker:
    global _DEFAULT_LINKER
    if _DEFAULT_LINKER is None:
        _DEFAULT_LINKER = EntityLinker()
    return _DEFAULT_LINKER


def resolve_entity(mention: str, context: str) -> str:
    linker = get_default_linker()
    return linker.resolve_entity(mention, context)["name"]
