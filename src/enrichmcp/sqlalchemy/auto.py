"""Automatic SQLAlchemy entity and resolver registration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import func, inspect, select

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from sqlalchemy.orm import DeclarativeBase

from enrichmcp import EnrichContext, EnrichMCP, PageResult

from .mixin import EnrichSQLAlchemyMixin


def _sa_to_enrich(instance: Any, model_cls: type) -> Any:
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
    model_name = sa_model.__name__.lower()
    list_name = f"list_{model_name}s"
    get_name = f"get_{model_name}"
    param_name = f"{model_name}_id"

    list_description = f"List {sa_model.__name__} records"
    get_description = f"Get a single {sa_model.__name__} by ID"

    async def list_resource(
        ctx: EnrichContext, page: int = 1, page_size: int = 20
    ) -> PageResult[enrich_model]:  # type: ignore[name-defined]
        session_factory = ctx.request_context.lifespan_context[session_key]
        async with session_factory() as session:
            total = await session.scalar(select(func.count()).select_from(sa_model))
            result = await session.execute(
                select(sa_model).offset((page - 1) * page_size).limit(page_size)
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

    # Ensure ctx annotation is an actual class for FastMCP before decorating
    list_resource.__annotations__["ctx"] = EnrichContext
    list_resource.__annotations__["return"] = PageResult[enrich_model]

    list_resource = app.retrieve(name=list_name, description=list_description)(list_resource)

    async def get_resource(ctx: EnrichContext, **kwargs: Any) -> enrich_model | None:  # type: ignore[name-defined]
        entity_id = kwargs.get(param_name)
        if entity_id is None:
            return None

        session_factory = ctx.request_context.lifespan_context[session_key]
        async with session_factory() as session:
            obj = await session.get(sa_model, entity_id)
            return _sa_to_enrich(obj, enrich_model) if obj else None

    # Ensure ctx annotation is an actual class for FastMCP before decorating
    get_resource.__annotations__["ctx"] = EnrichContext
    get_resource.__annotations__["return"] = enrich_model | None

    get_resource = app.retrieve(name=get_name, description=get_description)(get_resource)


def _register_relationship_resolvers(
    app: EnrichMCP,
    sa_model: type,
    enrich_model: type,
    models: dict[str, type],
    session_key: str,
) -> None:
    mapper = inspect(sa_model)
    for rel in mapper.relationships:
        if rel.info.get("exclude"):
            continue
        field_name = rel.key
        param_name = f"{sa_model.__name__.lower()}_id"
        if field_name not in enrich_model.model_fields:
            continue
        relationship = enrich_model.model_fields[field_name].default
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
                async def resolver_func(
                    ctx: EnrichContext,
                    page: int = 1,
                    page_size: int = 20,
                    **kwargs: Any,
                ) -> PageResult[Any]:
                    if page < 1 or page_size < 1:
                        raise ValueError("page and page_size must be >= 1")

                    entity_id = kwargs.get(param)
                    if entity_id is None and "kwargs" in kwargs:
                        entity_id = kwargs["kwargs"].get(param)
                    if entity_id is None:
                        return PageResult.create(
                            items=[],
                            page=page,
                            page_size=page_size,
                            has_next=False,
                            total_items=None,
                        )

                    session_factory = ctx.request_context.lifespan_context[session_key]
                    async with session_factory() as session:
                        primary_col = inspect(model).primary_key[0]
                        back_attr = getattr(target_sa, relation.back_populates)

                        offset = (page - 1) * page_size

                        stmt = (
                            select(target_sa)
                            .join(back_attr)
                            .where(primary_col == entity_id)
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

                return resolver_func

            resolver = _create_list_resolver()
            resolver.__annotations__["ctx"] = EnrichContext
        else:

            def _create_single_resolver(
                f_name: str = field_name,
                model: type = sa_model,
                target: type = target_model,
                param: str = param_name,
            ) -> Callable[..., Awaitable[Any | None]]:
                async def func(ctx: EnrichContext, **kwargs: Any) -> Any | None:
                    entity_id = kwargs.get(param)
                    if entity_id is None and "kwargs" in kwargs:
                        entity_id = kwargs["kwargs"].get(param)
                    if entity_id is None:
                        return None

                    session_factory = ctx.request_context.lifespan_context[session_key]
                    async with session_factory() as session:
                        obj = await session.get(model, entity_id)
                        if not obj:
                            return None
                        await session.refresh(obj, [f_name])
                        value = getattr(obj, f_name)
                        return _sa_to_enrich(value, target) if value else None

                return func

            resolver = _create_single_resolver()
            resolver.__annotations__["ctx"] = EnrichContext

        resolver.__name__ = f"get_{sa_model.__name__.lower()}_{field_name}"
        resolver.__doc__ = description
        relationship.resolver(name="get")(resolver)


def include_sqlalchemy_models(
    app: EnrichMCP,
    base: type[DeclarativeBase],
    *,
    session_key: str = "session_factory",
) -> dict[str, type]:
    """Register SQLAlchemy models with automatic resources and resolvers."""

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

    for mapper in base.registry.mappers:
        sa_model = mapper.class_
        if sa_model.__name__ not in models:
            continue
        enrich_model = models[sa_model.__name__]
        _register_default_resources(app, sa_model, enrich_model, session_key)
        _register_relationship_resolvers(app, sa_model, enrich_model, models, session_key)
        enrich_model.model_rebuild(_types_namespace=models)

    return models
