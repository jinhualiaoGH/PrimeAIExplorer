from __future__ import annotations

from typing import Iterable

from .models import ModelRoute


class GatewayRegistry:
    def __init__(self, routes: Iterable[ModelRoute] = ()) -> None:
        self._routes: dict[str, ModelRoute] = {}
        for route in routes:
            self.register(route)

    def register(self, route: ModelRoute) -> None:
        key = route.alias.strip().lower()
        if key in self._routes:
            raise ValueError(f"route already registered: {key}")
        self._routes[key] = route

    def resolve(self, alias: str) -> ModelRoute:
        key = alias.strip().lower()
        if key not in self._routes:
            raise KeyError(f"unknown model route: {key}")
        return self._routes[key]

    def list_routes(self) -> tuple[ModelRoute, ...]:
        return tuple(self._routes[key] for key in sorted(self._routes))
