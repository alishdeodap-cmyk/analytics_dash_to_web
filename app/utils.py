import re


def parse_iframe(iframe_html: str) -> dict | None:
    """
    Extract src and title from a raw Power BI iframe HTML string.
    Returns a dict with 'src' and 'title', or None if src not found.
    """
    if not iframe_html or '<iframe' not in iframe_html.lower():
        return None

    src_match   = re.search(r'src=["\']([^"\']+)["\']',   iframe_html, re.IGNORECASE)
    title_match = re.search(r'title=["\']([^"\']+)["\']', iframe_html, re.IGNORECASE)

    if not src_match:
        return None

    return {
        'src':   src_match.group(1).strip(),
        'title': title_match.group(1).strip() if title_match else '',
    }
