"""Rewrite user queries to improve embedding retrieval."""

import re


def enhance_query_for_retrieval(query: str) -> str:
    q = query.strip()
    if not q:
        return q

    lower = q.lower()
    extras: list[str] = []

    if re.search(r"\bactors?\b", lower):
        q = re.sub(r"\bactors?\b", "characters", q, flags=re.I)
        lower = q.lower()

    if re.search(r"\b(main|primary)\s+(actor|character|person)\b", lower):
        extras.extend(["protagonist", "main character"])

    if re.search(r"\blist all\b", lower) and re.search(r"\b(characters?|actors?|names?)\b", lower):
        extras.extend(["character names", "people", "roles"])

    if re.search(r"\bwho is\b", lower):
        extras.append("character name identity")

    if re.search(r"\bcharacters?\b", lower):
        extras.extend(["named characters", "people"])

    if extras:
        seen: set[str] = set()
        unique = []
        for item in extras:
            if item not in seen:
                seen.add(item)
                unique.append(item)
        return f"{q} {' '.join(unique)}"

    return q
