# Changelog

All notable changes to enrichmcp will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2025-06-12

### Added
- Added shop_api_gateway example showing EnrichMCP as an API gateway
- SQLAlchemy integration with `EnrichSQLAlchemyMixin`,
  `include_sqlalchemy_models` and `sqlalchemy_lifespan`
- Automatic generation of resources and relationship resolvers from
  SQLAlchemy models
- Example project `examples/sqlalchemy_shop`

### Changed
- Development setup now uses `uv`

## [0.3.0] - 2025-06-11

### Added
- Context support
- Lifespan support
- Pagination

## [0.2.0] - 2025-01-15

### Added
- Initial release of enrichmcp
- Core entity and relationship system
- Automatic schema introspection via `explore_data_model()`
- Type-safe resolver pattern for relationships
- Built-in error types for semantic error handling
- Context management for dependency injection
- Comprehensive documentation and examples
- Support for `@app.entity` and `@app.resource` decorators

### Fixed
- Relationship resolver type validation now properly checks return types
- Fixed decorator patterns to work with and without parentheses

[Unreleased]: https://github.com/featureform/enrichmcp/compare/main...HEAD
[0.2.0]: https://github.com/featureform/enrichmcp/releases/tag/v0.2.0
