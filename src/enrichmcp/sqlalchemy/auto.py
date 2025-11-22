"""Automatic SQLAlchemy entity and resolver registration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastmcp import Context
from sqlalchemy import func, inspect, select

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from sqlalchemy.orm import DeclarativeBase

from enrichmcp import EnrichMCP, PageResult
from enrichmcp.context import get_enrich_context

from .mixin import EnrichSQLAlchemyMixin


def _sa_to_enrich(instance: Any, model_cls: type) -> Any:
    """Convert a SQLAlchemy instance to its EnrichModel counterpart."""
    data: dict[str, Any] = {}
    for name in model_cls.model_fields:
        if name in model_cls.relationship_fields():
            continue
        if hasattr(instance, name):
            data[name] = getattr(instance, name)
    return model_cls(**data)


def _register_default_resources(
    app: EnrichMCP,
    sa_model: type,
    enrich_model: type,
    session_key: str,
) -> None:
    """Register basic list and get resources for ``sa_model``."""
    model_name = sa_model.__name__.lower()
    list_name = f"list_{model_name}s"
    get_name = f"get_{model_name}"
    param_name = f"{model_name}_id"

    list_description = f"List {sa_model.__name__} records"
    get_description = f"Get a single {sa_model.__name__} by ID"

    async def list_resource(
        ctx: Context | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PageResult[enrich_model]:  # type: ignore[name-defined]
        if ctx is None:
            ctx = get_enrich_context()
        session_factory = ctx.request_context.lifespan_context[session_key]
        async with session_factory() as session:
            total = await session.scalar(select(func.count()).select_from(sa_model))
            result = await session.execute(
                select(sa_model).offset((page - 1) * page_size).limit(page_size),
            )
            items = [_sa_to_enrich(obj, enrich_model) for obj in result.scalars().all()]
            has_next = page * page_size < int(total or 0)
            return PageResult.create(
                items=items,
                page=page,
                page_size=page_size,
                total_items=int(total or 0),
                has_next=has_next,
            )

    # Set annotations
    list_resource.__annotations__["ctx"] = Context | None
    list_resource.__annotations__["return"] = PageResult[enrich_model]

    app.retrieve(name=list_name, description=list_description)(list_resource)

    # Create function dynamically with the correct parameter name
    func_code = f"""
async def {get_name}({param_name}: int, ctx: "Context | None" = None) -> enrich_model | None:
    if ctx is None:
        ctx = get_enrich_context()
    session_factory = ctx.request_context.lifespan_context[session_key]
    async with session_factory() as session:
        obj = await session.get(sa_model, {param_name})
        return _sa_to_enrich(obj, enrich_model) if obj else None
"""

    # Execute the function definition
    namespace = {
        "Context": Context,
        "get_enrich_context": get_enrich_context,
        "enrich_model": enrich_model,
        "session_key": session_key,
        "sa_model": sa_model,
        "_sa_to_enrich": _sa_to_enrich,
    }
    exec(func_code, namespace)
    get_resource = namespace[get_name]

    function_tool = app.mcp.tool(
        name=get_name,
        description=get_description,
    )(get_resource)
    app.resources[get_name] = function_tool


def _register_relationship_resolvers(
    app: EnrichMCP,
    sa_model: type,
    enrich_model: type,
    models: dict[str, type],
    session_key: str,
) -> None:
    """Create default relationship resolvers for ``sa_model``."""
    mapper = inspect(sa_model)
    for rel in mapper.relationships:
        if rel.info.get("exclude"):
            continue
        field_name = rel.key
        param_name = f"{sa_model.__name__.lower()}_id"
        relationships = getattr(enrich_model, "_relationships", {})
        if field_name not in relationships:
            continue
        relationship = relationships[field_name]
        target_model = models[rel.mapper.class_.__name__]
        description = rel.info.get(
            "description",
            f"Fetches the '{field_name}' for a '{sa_model.__name__}'. "
            f"Provide ID of parent '{sa_model.__name__}' via param key '{param_name}'.",
        )

        if rel.uselist:

            def _create_list_resolver(
                f_name: str = field_name,
                model: type = sa_model,
                target: type = target_model,
                param: str = param_name,
                relation=rel,
                target_sa: type = rel.mapper.class_,
            ) -> Callable[..., Awaitable[PageResult[Any]]]:
                # Create function dynamically with the correct parameter name
                func_code = f"""
async def resolver_func(
    {param}: int,
    page: int = 1,
    page_size: int = 20,
    ctx: Context | None = None,
) -> PageResult[target]:
    if page < 1 or page_size < 1:
        raise ValueError("page and page_size must be >= 1")

    if ctx is None:
        ctx = get_enrich_context()
    session_factory = ctx.request_context.lifespan_context[session_key]
    async with session_factory() as session:
        primary_col = inspect(model).primary_key[0]
        back_attr = getattr(target_sa, relation.back_populates)

        offset = (page - 1) * page_size

        stmt = (
            select(target_sa)
            .join(back_attr)
            .where(primary_col == {param})
            .offset(offset)
            .limit(page_size + 1)
        )
        result = await session.execute(stmt)
        values = result.scalars().all()

        has_next = len(values) > page_size
        items = values[:page_size]

        if not items and page > 1:
            return PageResult.create(
                items=[],
                page=page,
                page_size=page_size,
                has_next=False,
                total_items=None,
            )

        items = [_sa_to_enrich(v, target) for v in items]
        return PageResult.create(
            items=items,
            page=page,
            page_size=page_size,
            has_next=has_next,
            total_items=None,
        )
"""

                # Execute the function definition
                namespace = {
                    "Context": Context,
                    "get_enrich_context": get_enrich_context,
                    "PageResult": PageResult,
                    "target": target,
                    "session_key": session_key,
                    "inspect": inspect,
                    "model": model,
                    "target_sa": target_sa,
                    "relation": relation,
                    "select": select,
                    "_sa_to_enrich": _sa_to_enrich,
                }
                exec(func_code, namespace)
                return namespace["resolver_func"]

            resolver = _create_list_resolver()
        else:

            def _create_single_resolver(
                f_name: str = field_name,
                model: type = sa_model,
                target: type = target_model,
                param: str = param_name,
            ) -> Callable[..., Awaitable[Any | None]]:
                # Create function dynamically with the correct parameter name
                func_code = f"""
async def resolver_func({param}: int, ctx: Context | None = None) -> target | None:
    if ctx is None:
        ctx = get_enrich_context()
    session_factory = ctx.request_context.lifespan_context[session_key]
    async with session_factory() as session:
        obj = await session.get(model, {param})
        if not obj:
            return None
        await session.refresh(obj, [f_name])
        value = getattr(obj, f_name)
        return _sa_to_enrich(value, target) if value else None
"""

                # Execute the function definition
                namespace = {
                    "Context": Context,
                    "get_enrich_context": get_enrich_context,
                    "target": target,
                    "session_key": session_key,
                    "model": model,
                    "f_name": f_name,
                    "_sa_to_enrich": _sa_to_enrich,
                }
                exec(func_code, namespace)
                return namespace["resolver_func"]

            resolver = _create_single_resolver()

        resolver.__name__ = f"get_{sa_model.__name__.lower()}_{field_name}"
        resolver.__doc__ = description
        relationship.resolver(name="get")(resolver)


def include_sqlalchemy_models(
    app: EnrichMCP,
    base: type[DeclarativeBase],
    *,
    session_key: str = "session_factory",
) -> dict[str, type]:
    """Convert and register SQLAlchemy models on ``app``.

    The returned mapping contains both the original SQLAlchemy class names and
    the generated EnrichModel classes for easy lookup.
    """
    models: dict[str, type] = {}
    for mapper in base.registry.mappers:
        sa_model = mapper.class_
        if not issubclass(sa_model, EnrichSQLAlchemyMixin):
            continue
        enrich_cls = sa_model.__enrich_model__()
        model = type(
            enrich_cls.__name__,
            (enrich_cls,),
            {"__doc__": enrich_cls.__doc__},
        )
        app.entity(model)
        models[sa_model.__name__] = model
        models[model.__name__] = model

    # First, rebuild all models to resolve forward references
    for mapper in base.registry.mappers:
        sa_model = mapper.class_
        if sa_model.__name__ not in models:
            continue
        enrich_model = models[sa_model.__name__]
        enrich_model.model_rebuild(_types_namespace=models)

    # Then register resources and resolvers
    for mapper in base.registry.mappers:
        sa_model = mapper.class_
        if sa_model.__name__ not in models:
            continue
        enrich_model = models[sa_model.__name__]
        _register_default_resources(app, sa_model, enrich_model, session_key)
        _register_relationship_resolvers(app, sa_model, enrich_model, models, session_key)

    return models
