"""Jieba-based Chinese tokenizer for PG tsvector full-text search."""
import re
import threading
from typing import Iterable, Optional

try:
    import jieba  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - exercised in envs without jieba
    jieba = None


# Punctuation & whitespace stripped from tokens before joining
_PUNCT_RE = re.compile(r"[\s，。！？、；：「」『』（）()【】\[\]《》<>\"'`~!@#$%^&*+=|\\/.\-_]+")
_ALNUM_RE = re.compile(r"[a-zA-Z0-9]+")
_CJK_RE = re.compile(r"[\u4e00-\u9fff]+")


class JiebaTokenizer:
    """Wraps jieba.cut_for_search; lazy-init and thread-safe.

    Output is a single whitespace-joined token string suitable for
    `to_tsvector('simple', :tokens)` — Chinese is pre-segmented in Python
    so we don't depend on a server-side parser like zhparser.
    """

    _initialized = False
    _init_lock = threading.Lock()

    def __init__(self, userdict: Optional[Iterable[str]] = None) -> None:
        with self._init_lock:
            if jieba is not None and not JiebaTokenizer._initialized:
                jieba.initialize()
                JiebaTokenizer._initialized = True
            if jieba is not None and userdict:
                for term in userdict:
                    jieba.add_word(term)

    def tokenize(self, text: str) -> str:
        if not text:
            return ""
        if jieba is None:
            return self._fallback_tokenize(text)
        tokens: list[str] = []
        for raw in jieba.cut_for_search(text):
            cleaned = _PUNCT_RE.sub("", raw).strip()
            if not cleaned or len(cleaned) < 2:
                # Skip 1-char tokens (mostly noise after punctuation strip).
                # Single Chinese chars are kept by cut_for_search but rarely
                # carry standalone meaning for retrieval; full terms still
                # reach the index because cut_for_search emits both fine and
                # coarse segments.
                continue
            tokens.append(cleaned.lower())
        return " ".join(tokens)

    def _fallback_tokenize(self, text: str) -> str:
        """Best-effort segmentation when jieba is unavailable.

        Keeps behavior compatible enough for testing/local runs by:
        - extracting alnum words
        - extracting CJK sequences and adding both full sequence + bigrams
        """
        lowered = text.lower()
        tokens: list[str] = []
        tokens.extend(_ALNUM_RE.findall(lowered))
        for seg in _CJK_RE.findall(text):
            if len(seg) >= 2:
                tokens.append(seg)
            for i in range(max(0, len(seg) - 1)):
                bigram = seg[i : i + 2]
                if len(bigram) == 2:
                    tokens.append(bigram)
        cleaned_tokens = []
        for token in tokens:
            cleaned = _PUNCT_RE.sub("", token).strip()
            if len(cleaned) >= 2:
                cleaned_tokens.append(cleaned)
        return " ".join(cleaned_tokens)
