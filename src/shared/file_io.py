from __future__ import annotations

import json
import logging
import os
import re
import yaml

from pathlib import Path
from typing import Any

logger = logging.getLogger("file_io")

_FILTER_RE = re.compile(r"^(?P<base>[^\[]+)(\[(?P<expr>.+)\])?$")

# ----- ------ ----- ------ ------
# Core Security
# ----- ------ ----- ------ ------

def safe_join(base_dir: str, *parts: str) -> str:
    """
    Join path parts to base dir and enforce the final path stays within base_dir.
    """
    if base_dir is None: 
        raise ValueError("base_dir cannnot be None")
    candidate = os.path.join(base_dir, *[str(p) for p in parts if p is not None])
    return validate_path_safety(candidate, base_dir=base_dir)


def validate_path_safety(target_path, base_dir=None): 
    if target_path is None:
        raise ValueError("Path is None")
    if not str(target_path).strip():
        raise ValueError("Path is empty")
    
    if base_dir is None:
        base_dir = os.path.abspath(os.getcwd())
    else: 
        base_dir = os.path.abspath(base_dir)
    
    p = str(target_path)
    if os.path.isabs(p): 
        abs_target = os.path.abspath(p)
    else: 
        abs_target = os.path.abspath(os.path.join(base_dir, p))
    
    real_base = os.path.realpath(base_dir)
    real_target = os.path.realpath(abs_target)

    if os.path.commonpath([real_base, real_target]) != real_base:
        raise ValueError(
            f"Security Violation: Path '{target_path}' escapes the expected directory '{base_dir}'."
        )
    
    return real_target


# ----- ------ ----- ------ ------
# Directory functions
# ----- ------ ----- ------ ------

def ensure_dir(directory_path, base_dir=None) -> str:
    safe_dir = validate_path_safety(directory_path, base_dir=base_dir)
    os.makedirs(safe_dir, exist_ok=True)
    return safe_dir


# ----- ------ ----- ------ ------
# File Read/Write functions
# ----- ------ ----- ------ ------

def read_yaml(file_path, base_dir=None):
    safe_path = Path(validate_path_safety(file_path, base_dir=base_dir))
    if not os.path.exists(safe_path):
        raise FileNotFoundError(f"File not found: {safe_path}")
    
    try: 
        with open(safe_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse YAML from {safe_path}: {e}") from e


def read_json(file_path, base_dir=None):
    safe_path = validate_path_safety(file_path, base_dir=base_dir)
    if not os.path.exists(safe_path):
        raise FileNotFoundError(f"File not found: {safe_path}")
    
    try: 
        with open(safe_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to decode JSOn from {safe_path}: {e}") from e


# ----- ------ ----- ------ ------
# Query Layer for contents returned through read_yaml() and read_json()
# ----- ------ ----- ------ ------

def walk_data(data: Any, key_path: str, default: Any = None, required: bool = False) -> Any:
    """
    Exact dot-path getter for nested dict/list structures.

    Supports:
      - dict keys:  "Adventure.description"
      - list index: "users.0.name"

    Examples:
        walk_data(cards, "Adventure.description")
        walk_data(data, "users.0.name")
    """
    if data is None:
        if required:
            raise ValueError("No data was passed.")
        return default

    if not key_path:
        if required:
            raise ValueError("Empty key.path is not allowed when required=True.")
        return default

    node = data
    parts = key_path.split(".")
    walked: list[str] = []

    for part in parts:
        walked.append(part)

        if isinstance(node, dict):
            if part not in node:
                if required:
                    raise ValueError(f"Missing required key: '{key_path}'")
                return default
            node = node[part]
            continue

        if isinstance(node, list):
            try:
                index = int(part)
            except ValueError:
                if required:
                    raise ValueError(
                        f"Expected list index at '{'.'.join(walked[:-1])}', got '{part}'"
                    )
                return default

            if index < 0 or index >= len(node):
                if required:
                    raise ValueError(
                        f"Index {index} out of range for '{'.'.join(walked[:-1])}'"
                    )
                return default

            node = node[index]
            continue

        if hasattr(node, part):
            node = getattr(node, part)
            continue
        
        if required:
            raise ValueError(
                f"Data at '{'.'.join(walked[:-1])}' is not traversable; cannot access '{key_path}'."
            )
        return default

    if node is None and required and default is None:
        raise ValueError(f"Key '{key_path}' is required but is None.")

    return node


def _split_path(path: str) -> list[str]:
    """
    Split a dot-path while preserving dots inside filter brackets.

    Example:
        '*[meta.type="core"].description'
    """
    parts: list[str] = []
    current: list[str] = []
    bracket_depth = 0

    for ch in path:
        if ch == "." and bracket_depth == 0:
            parts.append("".join(current))
            current = []
            continue

        if ch == "[":
            bracket_depth += 1
        elif ch == "]":
            bracket_depth -= 1

        current.append(ch)

    if current:
        parts.append("".join(current))

    return parts


def _parse_segment(segment: str) -> tuple[str, str | None]:
    """
    Parse one path segment into:
      (base_token, optional_filter_expression)

    Examples:
        "*"                         -> ("*", None)
        '*[key^"A"]'                -> ("*", 'key^"A"')
        'Adventure'                 -> ("Adventure", None)
        '*[vector_tags~"growth"]'   -> ("*", 'vector_tags~"growth"')
    """
    match = _FILTER_RE.match(segment)
    if not match:
        raise ValueError(f"Invalid path segment: '{segment}'")

    return match.group("base"), match.group("expr")


def _parse_filter(expr: str) -> tuple[str, str, str]:
    """
    Supported operators:
      =
      ~
      ^
      $

    Examples:
      key="Adventure"
      key^"A"
      key$"ness"
      vector_tags~"growth"

    Returns:
      (field_path, operator, value)
    """
    for op in ("^", "$", "~", "="):
        if op in expr:
            left, right = expr.split(op, 1)
            field = left.strip()
            value = right.strip()

            if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
                value = value[1:-1]
            else:
                raise ValueError(f'Filter values must be quoted. Invalid filter: [{expr}]')

            return field, op, value

    raise ValueError(f"Unsupported filter expression: [{expr}]")


def _value_matches(candidate: Any, op: str, expected: str) -> bool:
    if candidate is None:
        return False

    if op == "=":
        return str(candidate) == expected

    if op == "^":
        return str(candidate).startswith(expected)

    if op == "$":
        return str(candidate).endswith(expected)

    if op == "~":
        if isinstance(candidate, list):
            return any(str(item) == expected for item in candidate)
        if isinstance(candidate, str):
            return expected in candidate
        return expected in str(candidate)

    raise ValueError(f"Unsupported operator: {op}")


def _node_matches_filter(node: Any, expr: str, key: str | None = None) -> bool:
    """
    Filter fields can refer either to:
      - key            -> dictionary key
      - nested fields  -> fields within the node itself

    Examples:
      [key^"A"]
      [pv_domain_name="Relationships"]
      [vector_tags~"growth"]
    """
    field_path, op, expected = _parse_filter(expr)

    if field_path == "key":
        candidate = key
    else:
        candidate = walk_data(node, field_path, default=None, required=False)

    return _value_matches(candidate, op, expected)


def query_items(data: Any, query_path: str) -> list[tuple[str | None, Any]]:
    """
    Query nested dict/list data and return matched (key, value) pairs.

    Supported:
      - exact keys:  Adventure.description
      - list index:  users.0.name
      - wildcard:    *.description
      - filters:
            *[pv_domain_name="Personal Growth"]
            *[vector_tags~"growth"]
            *[key^"A"]
            *[key$"ness"]

    Notes:
      - For dict wildcard expansion, keys are preserved.
      - For list wildcard expansion, keys are string indices.
      - Exact traversal also returns the last traversed key where possible.

    Examples:
        query_items(cards, '*[key^"A"]')
        query_items(cards, '*[vector_tags~"growth"]')
        query_items(cards, '*.description')
    """
    if data is None or not query_path:
        return []

    segments = _split_path(query_path)
    current_nodes: list[tuple[str | None, Any]] = [(None, data)]

    for segment in segments:
        base, filter_expr = _parse_segment(segment)
        next_nodes: list[tuple[str | None, Any]] = []

        for _, node in current_nodes:
            expanded: list[tuple[str | None, Any]] = []

            # Wildcard expansion
            if base == "*":
                if isinstance(node, dict):
                    expanded.extend((k, v) for k, v in node.items())
                elif isinstance(node, list):
                    expanded.extend((str(i), v) for i, v in enumerate(node))

            # Exact dict/list traversal
            else:
                if isinstance(node, dict):
                    if base in node:
                        expanded.append((base, node[base]))
                elif isinstance(node, list):
                    try:
                        index = int(base)
                    except ValueError:
                        continue
                    if 0 <= index < len(node):
                        expanded.append((str(index), node[index]))

            # Optional filter
            if filter_expr is not None:
                expanded = [
                    (k, v) for k, v in expanded
                    if _node_matches_filter(v, filter_expr, key=k)
                ]

            next_nodes.extend(expanded)

        current_nodes = next_nodes

    return current_nodes


def query_data(data: Any, query_path: str) -> list[Any]:
    """
    Query nested dict/list data and return matched values only.

    This is the value-only wrapper around query_items().

    Examples:
        query_data(cards, '*.description')
        query_data(cards, '*[pv_domain_name="Relationships"]')
        query_data(cards, '*[vector_tags~"growth"].description')
    """
    return [value for _, value in query_items(data, query_path)]


def query_keys(data: Any, query_path: str) -> list[str]:
    """
    Query nested dict/list data and return matched keys only.

    Examples:
        query_keys(cards, '*')
        query_keys(cards, '*[key^"A"]')
        query_keys(cards, '*[vector_tags~"growth"]')
    """
    return [key for key, _ in query_items(data, query_path) if key is not None]

