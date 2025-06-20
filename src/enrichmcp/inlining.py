from __future__ import annotations

import inspect
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from .entity import EnrichModel

if TYPE_CHECKING:
    from .relationship import Relationship


async def inline_relationships(
    entity: EnrichModel,
    *,
    max_depth: int = 1,
    _depth: int = 0,
    only_inline: bool = False,
) -> EnrichModel:
    """Recursively resolve and inline relationships on an entity.

    Args:
        entity: The entity instance to enrich.
        max_depth: Maximum recursion depth for inlining relationships.
        _depth: Internal parameter used for recursion tracking.

    Returns:
        The entity with relationships populated up to ``max_depth``.
    """
    if _depth >= max_depth:
        return entity

    for field in entity.__class__.relationship_fields():
        rel_field = entity.__class__.model_fields[field]
        relationship: Relationship = rel_field.default
        if only_inline and not getattr(relationship, "inline", False):
            continue
        if not relationship.resolvers:
            continue
        name, resolver = relationship.resolvers[0]
        kwargs: dict[str, Any] = {}
        sig = inspect.signature(resolver)
        for param in sig.parameters.values():
            if hasattr(entity, param.name):
                kwargs[param.name] = getattr(entity, param.name)
            elif param.name == f"{entity.__class__.__name__.lower()}_id" and hasattr(entity, "id"):
                kwargs[param.name] = entity.id
        result = resolver(**kwargs)
        if inspect.iscoroutine(result):
            result = await result
        result = await _process_result(result, max_depth, _depth + 1, only_inline)
        setattr(entity, field, result)
    return entity


async def _process_result(value: Any, max_depth: int, depth: int, only_inline: bool) -> Any:
    if isinstance(value, EnrichModel):
        return await inline_relationships(
            value,
            max_depth=max_depth,
            _depth=depth,
            only_inline=only_inline,
        )
    if isinstance(value, Iterable) and not isinstance(value, str | bytes):
        return [await _process_result(v, max_depth, depth, only_inline) for v in value]
    return value
