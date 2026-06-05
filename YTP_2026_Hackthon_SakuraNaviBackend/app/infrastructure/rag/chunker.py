"""Markdown chunker — splits documents at H2 boundaries with size guard."""
import re
from dataclasses import dataclass
from typing import Optional


_H1_RE = re.compile(r"^\s*#\s+(.+?)\s*$")
_H2_RE = re.compile(r"^\s*##\s+(.+?)\s*$")
_H3_RE = re.compile(r"^\s*###\s+(.+?)\s*$")


@dataclass(frozen=True)
class RawChunk:
    """An intermediate chunk record produced before embedding."""
    chunk_index: int
    heading: Optional[str]
    content: str
    token_count: int


# Chinese counts as ~1 token per char with Gemini; English ~0.25. Use a
# conservative average of 0.6 tokens per char so a 500-token cap maps to
# ~830 chars, which lines up with the typical H2 section length in rag_docs.
_TOKENS_PER_CHAR = 0.6


def _estimate_tokens(text: str) -> int:
    return max(1, int(len(text) * _TOKENS_PER_CHAR))


def chunk_markdown(text: str, max_tokens: int = 500) -> list[RawChunk]:
    """Split a markdown document into chunks aligned to H2 (and H3 fallback) boundaries.

    Algorithm:
      1. Strip the H1 title and the blockquote metadata block at the top
         (these are recorded on the parent document, not in chunks).
      2. Slice at every H2 line. Within an H2 section, if the section
         exceeds max_tokens, fall back to H3, and finally to paragraph splits.
      3. Each chunk records the most recent heading (H2 preferred, else H3).
    """
    lines = text.splitlines()

    # Skip leading H1 + blockquote metadata until first non-meta non-blank line.
    body_start = 0
    seen_h1 = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not seen_h1 and _H1_RE.match(line):
            seen_h1 = True
            continue
        if seen_h1:
            if stripped.startswith(">") or stripped == "" or stripped == "---":
                continue
            body_start = i
            break
    body_lines = lines[body_start:]

    # Split into H2 sections
    sections: list[tuple[Optional[str], list[str]]] = []
    current_heading: Optional[str] = None
    current_buf: list[str] = []
    for line in body_lines:
        h2 = _H2_RE.match(line)
        if h2:
            if current_buf:
                sections.append((current_heading, current_buf))
            current_heading = h2.group(1).strip()
            current_buf = []
        else:
            current_buf.append(line)
    if current_buf:
        sections.append((current_heading, current_buf))

    chunks: list[RawChunk] = []
    for heading, buf in sections:
        body = "\n".join(buf).strip()
        if not body:
            continue
        for sub_heading, sub_text in _split_oversized(heading, body, max_tokens):
            chunks.append(
                RawChunk(
                    chunk_index=len(chunks),
                    heading=sub_heading,
                    content=sub_text,
                    token_count=_estimate_tokens(sub_text),
                )
            )

    return chunks


def _split_oversized(
    heading: Optional[str], body: str, max_tokens: int
) -> list[tuple[Optional[str], str]]:
    """If a section is over budget, split by H3, then by paragraph as a last resort."""
    if _estimate_tokens(body) <= max_tokens:
        return [(heading, body)]

    # Try H3 splits first
    pieces: list[tuple[Optional[str], str]] = []
    current_h3: Optional[str] = None
    buf: list[str] = []
    found_h3 = False
    for line in body.splitlines():
        h3 = _H3_RE.match(line)
        if h3:
            found_h3 = True
            if buf:
                pieces.append((_compose_heading(heading, current_h3), "\n".join(buf).strip()))
            current_h3 = h3.group(1).strip()
            buf = []
        else:
            buf.append(line)
    if buf:
        pieces.append((_compose_heading(heading, current_h3), "\n".join(buf).strip()))

    if not found_h3:
        return _paragraph_split(heading, body, max_tokens)

    out: list[tuple[Optional[str], str]] = []
    for sub_heading, sub_body in pieces:
        if not sub_body:
            continue
        if _estimate_tokens(sub_body) <= max_tokens:
            out.append((sub_heading, sub_body))
        else:
            out.extend(_paragraph_split(sub_heading, sub_body, max_tokens))
    return out


def _paragraph_split(
    heading: Optional[str], body: str, max_tokens: int
) -> list[tuple[Optional[str], str]]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    out: list[tuple[Optional[str], str]] = []
    cur: list[str] = []
    cur_tokens = 0
    for p in paragraphs:
        p_tokens = _estimate_tokens(p)
        if cur and cur_tokens + p_tokens > max_tokens:
            out.append((heading, "\n\n".join(cur)))
            cur = [p]
            cur_tokens = p_tokens
        else:
            cur.append(p)
            cur_tokens += p_tokens
    if cur:
        out.append((heading, "\n\n".join(cur)))
    return out


def _compose_heading(h2: Optional[str], h3: Optional[str]) -> Optional[str]:
    if h2 and h3:
        return f"{h2} / {h3}"
    return h2 or h3
