from __future__ import annotations


def parse_options_header(header: str | bytes) -> tuple[str, dict[str, str]]:
    if isinstance(header, bytes):
        header = header.decode("latin-1")
    parts = [part.strip() for part in header.split(";") if part.strip()]
    if not parts:
        return "", {}
    main = parts[0]
    params: dict[str, str] = {}
    for piece in parts[1:]:
        if "=" in piece:
            key, value = piece.split("=", 1)
            params[key.strip()] = value.strip().strip('"')
    return main, params
