"""
Text processing utilities.
Handles route cleaning, text truncation, and ATIS formatting."""

import re
from typing import List

def clean_route(route: str) -> str:
    """Clean flight route by removing coordinates and DCT."""
    if not route or route == "No route":
        return route
    
    # Regex for coordinates
    coord_regex = re.compile(
        r"^(\d{2,4}[NS]\d{3,5}[EW]|\d{1,2}[NS]\d{1,3}[EW]|-?\d+(\.\d+)?,-?\d+(\.\d+)?)$",
        re.VERBOSE
    )
    
    # Filter out DCT and coordinates
    route_segments = [
        seg.split("/", 1)[0]
        for seg in route.split()
        if seg.split("/", 1)[0].upper() != "DCT" and not coord_regex.match(seg.upper())
    ]
    
    if not route_segments:
        return "DCT"
    
    # Truncate if too long
    if len(route_segments) > 4:
        return " ".join(route_segments[:2]) + "..." + " ".join(route_segments[-2:])
    else:
        return " ".join(route_segments)

def join_with_limit(items: List[str], sep: str = "/", limit: int = 1024, suffix: str = "...") -> str:
    """Join items with separator, respecting character limit."""
    result = []
    length = 0
    
    for item in items:
        extra = (len(sep) if result else 0) + len(item)
        if length + extra + len(suffix) > limit:
            return sep.join(result) + suffix
        result.append(item)
        length += extra
    
    return sep.join(result)

def clean_dependency(text: str) -> str:
    """Clean ATIS dependency text by removing flight levels and remarks."""
    if not text:
        return ""
    
    tokens = text.split()
    dep = []
    
    for t in tokens:
        if (
            re.search(r"\d", t) or
            "/" in t or
            "//" in t or
            t.upper() in {
                "FL", "TL", "TA", "RMK", "ATC", "CPDLC", "FIS",
                "INFO", "INFORMATION", "ABOVE", "BELOW", "ONLY", "UNL"
            }
        ):
            break
        dep.append(t)
    
    return " ".join(dep).strip()

def move_garbage_to_detail(original: str, cleaned: str, atis_text: str) -> str:
    """Move extra text from dependency to detail section."""
    if not original or original == cleaned:
        return atis_text
    
    garbage = original[len(cleaned):].strip()
    if garbage:
        return f" - {garbage}{atis_text}"
    
    return atis_text

def parse_atis(atis_data: dict) -> dict:
    """Parse ATIS data into dependency and text components."""
    if not atis_data or not isinstance(atis_data, dict):
        return {"dependency": "", "text": ""}
        
    raw_lines = atis_data.get("lines", [])
    if not raw_lines:
        return {"dependency": "", "text": ""}

    parts = []
    for line in raw_lines[1:]:  # Skip first line
        # Clean up line
        line = re.sub(r"\s*recorded at \d{4}z", "", line, flags=re.IGNORECASE)
        line = re.sub(
            r"\s*CONFIRM\s+ATIS\s+INFO\s+[A-Z]+\s*(ON\s+INITIAL\s+CONTACT)?\s*",
            "",
            line,
            flags=re.IGNORECASE
        )
        line = re.sub(r"(?<!\s)(CPDLC)", r" \1", line, flags=re.IGNORECASE)
        line = line.strip()
        if line:
            parts.append(line)
    
    combined = " ".join(parts)
    dependency = ""
    atis_text = ""
    
    if combined:
        # Parse ATIS structure
        if re.search(r"\binformation\b", combined, re.IGNORECASE) and not combined.lower().startswith("information"):
            m = re.split(r"\binformation\b", combined, maxsplit=1, flags=re.IGNORECASE)
            dependency = m[0].strip()
            rest = m[1].strip() if len(m) > 1 else ""
            rest = re.sub(r"\b\d{3}\.\d\b", "", rest).strip()
            atis_text = f" - Information {rest}"
        elif combined.lower().startswith("information"):
            # dependency will be callsign (handled by caller if empty)
            rest = combined[len("information"):].strip()
            rest = re.sub(r"\b\d{3}\.\d\b", "", rest).strip()
            atis_text = f" - Information {rest}"
        elif re.search(r"\brmk\b", combined, re.IGNORECASE):
            m = re.split(r"\brmk\b", combined, maxsplit=1, flags=re.IGNORECASE)
            dependency = m[0].strip()
            atis_text = f" - RMK {m[1].strip()}" if len(m) > 1 else ""
        else:
            dependency = parts[0] if parts else ""
            rest = " ".join(parts[1:]).strip()
            if rest:
                atis_text = f" - {rest}"
                
    # Clean dependency
    if dependency:
        dep_clean = clean_dependency(dependency)
        atis_text = move_garbage_to_detail(dependency, dep_clean, atis_text)
        dependency = dep_clean
        
    return {"dependency": dependency, "text": atis_text}
