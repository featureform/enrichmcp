"""Automatic SQLAlchemy entity and resolver registration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import func, inspect, select

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from sqlalchemy.orm import DeclarativeBase

import logging

from enrichmcp import EnrichContext, EnrichMCP, PageResult

from .mixin import EnrichSQLAlchemyMixin

logger = logging.getLogger(__name__)


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

    list_resource = app.resource(name=list_name, description=list_description)(list_resource)

    async def get_resource(ctx: EnrichContext, **kwargs: Any) -> enrich_model | None:  # type: ignore[name-defined]
        logger.debug(f"Received raw kwargs for get_resource: {kwargs}")

        # Determine where the actual parameters are located
        actual_params = kwargs
        # Check if param_name is directly in kwargs or if it's nested under a 'kwargs' key.
        # The latter happens if the MCP call is structured like func_name(kwargs={...}).
        if param_name not in kwargs and "kwargs" in kwargs and isinstance(kwargs["kwargs"], dict):
            actual_params = kwargs["kwargs"]
        else:  # Param not in kwargs and also not in a nested 'kwargs' dict.
            logger.debug(f"Param '{param_name}' not found directly or in nested 'kwargs'.")
            # actual_params remains kwargs, entity_id will be None in the next step

        logger.debug(f"Using '{param_name}' for ID from processed: {actual_params}")
        entity_id = actual_params.get(param_name)

        if entity_id is None:
            logger.warning(f"Param '{param_name}' not processed (raw: {kwargs}). Ret None.")
            return None

        logger.debug(f"Extracted entity_id: {entity_id} for model {sa_model.__name__}")

        session_factory = ctx.request_context.lifespan_context[session_key]
        logger.debug(f"Using session_key: '{session_key}'")

        async with session_factory() as session:
            logger.debug(f"Attempting to fetch {sa_model.__name__} with id: {entity_id}")
            obj = await session.get(sa_model, entity_id)
            if obj:
                logger.debug(f"Found object: {obj}")
                enriched_obj = _sa_to_enrich(obj, enrich_model)
                logger.debug(f"Enriched object: {enriched_obj}")
                return enriched_obj
            else:
                logger.debug(f"No object found for {sa_model.__name__} with id: {entity_id}")
                return None

    # Ensure ctx annotation is an actual class for FastMCP before decorating
    get_resource.__annotations__["ctx"] = EnrichContext

    get_resource = app.resource(name=get_name, description=get_description)(get_resource)


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
            ) -> Callable[..., Awaitable[list[Any]]]:
                async def func(
                    ctx: EnrichContext, **kwargs: Any
                ) -> list[Any]:  # Changed int to Any
                    logger.debug(f"List resolver {model.__name__}.{f_name} raw_kwargs: {kwargs}")
                    actual_params = kwargs
                    if (
                        param not in kwargs
                        and "kwargs" in kwargs
                        and isinstance(kwargs["kwargs"], dict)
                    ):
                        logger.debug(f"Param '{param}' not top-level. Check nested 'kwargs' dict.")
                        actual_params = kwargs["kwargs"]

                    entity_id = actual_params.get(param)
                    logger.debug(f"Using param_name: '{param}', extracted entity_id: {entity_id}")

                    if entity_id is None:
                        logger.warning(
                            f"Param '{param}' for {model.__name__}.{f_name} not processed."
                        )
                        return []

                    session_factory = ctx.request_context.lifespan_context[session_key]
                    async with session_factory() as session:
                        obj = await session.get(model, entity_id)
                        if not obj:
                            logger.debug(f"Parent {model.__name__} ID {entity_id} not found.")
                            return []
                        await session.refresh(obj, [f_name])
                        values = getattr(obj, f_name)
                        return [_sa_to_enrich(v, target) for v in values]

                return func

            resolver = _create_list_resolver()
            resolver.__annotations__["ctx"] = EnrichContext
        else:

            def _create_single_resolver(
                f_name: str = field_name,
                model: type = sa_model,
                target: type = target_model,
                param: str = param_name,
            ) -> Callable[..., Awaitable[Any | None]]:
                async def func(
                    ctx: EnrichContext, **kwargs: Any
                ) -> Any | None:  # Changed int to Any
                    logger.debug(f"Single resolver {model.__name__}.{f_name} raw_kwargs: {kwargs}")
                    actual_params = kwargs
                    if (
                        param not in kwargs
                        and "kwargs" in kwargs
                        and isinstance(kwargs["kwargs"], dict)
                    ):
                        logger.debug(f"Param '{param}' not top-level. Check nested 'kwargs' dict.")
                        actual_params = kwargs["kwargs"]

                    entity_id = actual_params.get(param)
                    logger.debug(f"Using param_name: '{param}', extracted entity_id: {entity_id}")

                    if entity_id is None:
                        logger.warning(
                            f"Param '{param}' for {model.__name__}.{f_name} not processed."
                        )
                        return None

                    session_factory = ctx.request_context.lifespan_context[session_key]
                    async with session_factory() as session:
                        obj = await session.get(model, entity_id)
                        if not obj:
                            logger.debug(f"Parent {model.__name__} ID {entity_id} not found.")
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
