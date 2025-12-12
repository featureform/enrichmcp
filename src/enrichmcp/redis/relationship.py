"""Relationship descriptor for Redis models."""

from enrichmcp import Relationship as BaseRelationship


class Relationship(BaseRelationship):
    """Enhanced Relationship with Redis-specific features.

    This extends the base Relationship to work with Redis document storage
    and foreign key resolution.
    """

    def __init__(
        self,
        description: str,
        source_field: str | None = None,
        reverse_of: str | None = None,
        **kwargs,
    ):
        """Initialize Redis-aware relationship.

        Args:
            description: Description of the relationship
            source_field: Field in this model containing foreign key(s)
            reverse_of: Field in target model that references this model
            **kwargs: Additional arguments passed to base Relationship
        """
        super().__init__(description=description, **kwargs)
        self.source_field = source_field
        self.reverse_of = reverse_of
