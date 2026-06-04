"""Detect programming languages in a repository."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from zea.discovery.models import Language, LanguageStats

EXTENSION_MAP: dict[str, Language] = {
    ".py": Language.PYTHON,
    ".ts": Language.TYPESCRIPT,
    ".tsx": Language.TYPESCRIPT,
    ".js": Language.JAVASCRIPT,
    ".jsx": Language.JAVASCRIPT,
    ".mjs": Language.JAVASCRIPT,
    ".cjs": Language.JAVASCRIPT,
    ".java": Language.JAVA,
    ".kt": Language.KOTLIN,
    ".kts": Language.KOTLIN,
    ".go": Language.GO,
    ".cs": Language.CSHARP,
    ".rs": Language.RUST,
    ".php": Language.PHP,
    ".rb": Language.RUBY,
}


def detect_languages(files: list[Path]) -> list[LanguageStats]:
    """Count files by language and return sorted stats."""
    language_extensions: dict[Language, list[str]] = {}
    counts: Counter[Language] = Counter()

    for f in files:
        lang = EXTENSION_MAP.get(f.suffix.lower())
        if lang:
            counts[lang] += 1
            if lang not in language_extensions:
                language_extensions[lang] = []
            ext = f.suffix.lower()
            if ext not in language_extensions[lang]:
                language_extensions[lang].append(ext)

    return [
        LanguageStats(
            language=lang,
            file_count=count,
            extensions=sorted(language_extensions.get(lang, [])),
        )
        for lang, count in counts.most_common()
    ]


def primary_language(stats: list[LanguageStats]) -> Language:
    return stats[0].language if stats else Language.UNKNOWN
