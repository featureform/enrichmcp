"""Enhanced Field function with Redis search metadata."""

from typing import Any

from pydantic import Field as PydanticField


def Field(  # noqa: N802
    *,
    description: str,
    default: Any = None,
    # Redis search options
    index: str | list[str] | None = None,  # "primary", "text", "tag", "numeric", "vector"
    # Vector-specific options
    vector_dim: int | None = None,
    distance_metric: str = "cosine",
    # Text-specific options
    weight: float = 1.0,
    no_stem: bool = False,
    # Numeric-specific options
    sortable: bool = False,
    **kwargs,
) -> Any:
    """Enhanced Field with Redis search metadata.

    Args:
        description: Field description (required)
        default: Default value
        index: Index type(s) - "primary", "text", "tag", "numeric", "vector", or list
        vector_dim: Vector dimensions (required for vector index)
        distance_metric: Vector distance metric ("cosine", "euclidean", "dot_product")
        weight: Text search weight (default 1.0)
        no_stem: Disable text stemming (default False)
        sortable: Enable sorting for numeric fields (default False)
        **kwargs: Additional Pydantic Field arguments

    Returns:
        Pydantic Field with Redis metadata stored in json_schema_extra
    """
    # Store Redis metadata in json_schema_extra
    redis_metadata = {}

    if index:
        index_list = index if isinstance(index, list) else [index]

        # Validate vector fields
        if "vector" in index_list and vector_dim is None:
            raise ValueError("vector_dim is required for vector index fields")

        redis_metadata["redis_search"] = {
            "index": index_list,
            "vector_dim": vector_dim,
            "distance_metric": distance_metric,
            "weight": weight,
            "no_stem": no_stem,
            "sortable": sortable,
        }

    return PydanticField(
        description=description, default=default, json_schema_extra=redis_metadata, **kwargs
    )
