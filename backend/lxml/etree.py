from __future__ import annotations

from xml.etree import ElementTree as _ElementTree

_Element = _ElementTree.Element


class XMLSyntaxError(ValueError):
    pass


def fromstring(xml_input: bytes | str) -> _Element:
    try:
        return _ElementTree.fromstring(xml_input)
    except _ElementTree.ParseError as exc:  # pragma: no cover - wrapper
        raise XMLSyntaxError(str(exc)) from exc


def tostring(element: _Element, encoding: str = "unicode") -> str:
    return _ElementTree.tostring(element, encoding=encoding)  # type: ignore[no-any-return]
