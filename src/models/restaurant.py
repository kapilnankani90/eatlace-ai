"""Restaurant domain model."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RestaurantRecord:
    """Normalized restaurant row from the Zomato dataset."""

    id: str
    name: str
    location: str
    cuisines: list[str]
    rating: float
    estimated_cost: float | None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "cuisines": self.cuisines,
            "rating": self.rating,
            "estimated_cost": self.estimated_cost,
            "metadata": self.metadata,
        }
