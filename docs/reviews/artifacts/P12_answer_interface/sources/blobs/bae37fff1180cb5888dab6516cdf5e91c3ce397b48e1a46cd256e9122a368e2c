"""Strict, recursively immutable JSON boundaries using the standard library."""
from dataclasses import fields, is_dataclass
from math import isfinite
from types import UnionType
from typing import Literal, get_args, get_origin, get_type_hints
import json
from pathlib import Path


def convert(kind, value):
    origin, args = get_origin(kind), get_args(kind)
    if origin is UnionType:
        for option in args:
            try:
                return convert(option, value)
            except (ValueError, TypeError):
                pass
        raise ValueError("value does not match permitted types")
    if origin is Literal:
        if value not in args or type(value) is not type(args[0]):
            raise ValueError("invalid choice")
        return value
    if origin is tuple:
        if not isinstance(value, (list, tuple)):
            raise ValueError("expected array")
        return tuple(convert(args[0], item) for item in value)
    if is_dataclass(kind):
        if type(value) is kind:
            return value
        if type(value) is not dict:
            raise ValueError("expected object")
        hints = get_type_hints(kind)
        if value.keys() - hints.keys():
            raise ValueError("unknown fields: " + ", ".join(sorted(value.keys() - hints.keys())))
        try:
            return kind(**{key: convert(hints[key], item) for key, item in value.items()})
        except TypeError as exc:
            raise ValueError("missing required fields") from exc
    if kind is float:
        if type(value) not in (int, float) or not isfinite(value):
            raise ValueError("expected finite number")
        return float(value)
    if type(value) is not kind:
        raise ValueError(f"expected {kind.__name__}")
    if kind is str and not value.strip():
        raise ValueError("empty string")
    return value


class StrictFrozen:
    def __post_init__(self):
        hints = get_type_hints(type(self))
        for field in fields(self):
            object.__setattr__(self, field.name, convert(hints[field.name], getattr(self, field.name)))


def load_json(path: Path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)
