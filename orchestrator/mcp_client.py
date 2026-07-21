"""MCP client adapters for Swiggy MCP servers with example integration.

The client reads config from a dict or config/servers.yaml and supports safe mocked
responses when real API credentials are not provided (useful for development).
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

import yaml

try:
    import requests
except Exception:  # pragma: no cover - requests may not be available in some test envs
    requests = None  # type: ignore


DEFAULT_CONFIG_PATH = os.path.join("config", "servers.yaml")


class MCPClient:
    def __init__(self, config: Optional[Dict[str, Any]] = None, config_path: Optional[str] = None) -> None:
        self._config = config or {}
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        if not config and os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self._config = yaml.safe_load(f) or {}
            except Exception:
                self._config = {}

        # Allow overriding API keys via environment variables for secure deployments
        # e.g., FOOD_API_KEY, INSTAMART_API_KEY, DINEOUT_API_KEY
        servers = self._config.get("servers") if isinstance(self._config, dict) else None
        if servers:
            for name, cfg in list(servers.items()):
                env_key = f"{name.upper()}_API_KEY"
                env_url = f"{name.upper()}_URL"
                if os.environ.get(env_key):
                    cfg["api_key"] = os.environ.get(env_key)
                if os.environ.get(env_url):
                    cfg["url"] = os.environ.get(env_url)
            self._config["servers"] = servers

    def get_server_config(self, name: str) -> Dict[str, Any]:
        servers = self._config.get("servers") if isinstance(self._config, dict) else None
        if not servers:
            return {}
        return servers.get(name, {}) or {}

    def _has_valid_key(self, cfg: Dict[str, Any]) -> bool:
        key = cfg.get("api_key")
        return bool(key) and "REPLACE" not in str(key).upper()

    def request(self, server_name: str, path: str = "", method: str = "GET", params: Optional[Dict[str, Any]] = None, json: Optional[Any] = None) -> Dict[str, Any]:
        cfg = self.get_server_config(server_name)
        url_base = cfg.get("url")

        # If no config or missing credentials, return a safe mocked response for development
        if not url_base or not self._has_valid_key(cfg):
            return {
                "mock": True,
                "server": server_name,
                "path": path,
                "params": params,
                "json": json,
                "note": "No API key or server URL configured — this is a mocked response for local development.",
            }

        # Make a real HTTP request when possible
        api_key = cfg.get('api_key')
        headers = {}
        if api_key:
            # set both common patterns; server docs will clarify exact header
            headers['Authorization'] = f"Bearer {api_key}"
            headers['X-API-Key'] = api_key
        url = url_base.rstrip("/") + "/" + path.lstrip("/")

        if requests is None:
            return {"error": "requests library not available"}

        try:
            resp = requests.request(method, url, params=params, json=json, headers=headers, timeout=10)
            try:
                data = resp.json()
            except Exception:
                data = {"text": resp.text}
            return {"status_code": resp.status_code, "data": data}
        except Exception as exc:
            return {"error": str(exc)}

    # Convenience helpers (mock-friendly)
    def search_restaurants(self, query: str, server_name: str = "food") -> Dict[str, Any]:
        return self.request(server_name, path="search", params={"q": query})

    def get_menu(self, restaurant_id: Optional[str] = None, server_name: str = "food") -> Dict[str, Any]:
        """Fetch a restaurant menu or a generic catalog. Returns a mocked menu when no server configured."""
        if not restaurant_id:
            # call a generic catalog endpoint if supported
            return self.request(server_name, path="menu")
        return self.request(server_name, path=f"menu/{restaurant_id}")

    def find_menu_item(self, name: str, restaurant_id: Optional[str] = None, server_name: str = "food") -> Dict[str, Any]:
        """Try to resolve a free-text item name to a menu item id. Mock fallback does a simple substring match."""
        cfg = self.get_server_config(server_name)
        if not cfg or not self._has_valid_key(cfg):
            # mock menu
            mock_items = [
                {"id": "m1", "name": "Margherita Pizza", "price": 199},
                {"id": "m2", "name": "Paneer Butter Masala", "price": 249},
                {"id": "m3", "name": "Coke (500ml)", "price": 49},
            ]
            for it in mock_items:
                if name.lower() in it['name'].lower():
                    return {"found": True, "item": it}
            # best-effort: return first item as fallback
            return {"found": False, "item": mock_items[0]}
        # if real server: try menu lookup then fuzzy match
        menu_resp = self.get_menu(restaurant_id, server_name)
        items = []
        if isinstance(menu_resp, dict) and 'data' in menu_resp and isinstance(menu_resp['data'], dict):
            items = menu_resp['data'].get('items') or menu_resp['data'].get('menu') or []
        # fallback simplification
        for it in items:
            name_field = it.get('name') or it.get('title') or ''
            if name.lower() in name_field.lower():
                return {"found": True, "item": it}
        return {"found": False, "item": items[0] if items else None}

    def add_to_cart(self, cart_id: Optional[str], item_id: str, qty: int = 1, server_name: str = "food") -> Dict[str, Any]:
        payload = {"cart_id": cart_id, "item_id": item_id, "qty": qty}
        return self.request(server_name, path="cart/add", method="POST", json=payload)

    def place_order(self, order: Dict[str, Any], server_name: str = "food") -> Dict[str, Any]:
        return self.request(server_name, path="order", method="POST", json=order)

    def get_order_status(self, order_id: str, server_name: str = "food") -> Dict[str, Any]:
        return self.request(server_name, path=f"order/{order_id}")
