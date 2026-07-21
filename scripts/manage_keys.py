"""CLI to manage API keys stored by the orchestrator auth system.

Usage examples:
  # list keys
  python scripts/manage_keys.py list

  # add key with explicit value
  python scripts/manage_keys.py add --key mykey123 --role user

  # add key with generated value
  python scripts/manage_keys.py add --role admin

  # remove key
  python scripts/manage_keys.py remove --key mykey123

This script imports orchestrator.auth and uses MemoryStore (or configured DB) to persist keys.
"""
from __future__ import annotations

import argparse
import sys
import uuid
import os

from orchestrator import auth


def list_keys() -> None:
    keys = auth.get_all_keys()
    if not keys:
        print("No keys configured.")
        return
    print("Configured API keys (key: role):")
    for k, r in keys.items():
        print(f"- {k}: {r}")


def add_key(key: str | None, role: str) -> None:
    if not key:
        key = uuid.uuid4().hex
    auth.add_key(key, role)
    print(f"Added key: {key} (role={role})")


def remove_key(key: str) -> None:
    auth.remove_key(key)
    print(f"Removed key: {key}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="manage_keys")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("list", help="List configured API keys")

    p_add = sub.add_parser("add", help="Add an API key")
    p_add.add_argument("--key", help="Key value (if omitted a random key is generated)")
    p_add.add_argument("--role", choices=["user", "admin"], default="user")

    p_rm = sub.add_parser("remove", help="Remove an API key")
    p_rm.add_argument("--key", required=True, help="Key to remove")

    args = parser.parse_args(argv)
    if args.cmd == "list":
        list_keys()
        return 0
    if args.cmd == "add":
        add_key(args.key, args.role)
        return 0
    if args.cmd == "remove":
        remove_key(args.key)
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
