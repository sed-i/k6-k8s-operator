#!/usr/bin/env python3
# Copyright 2024 sed-i
# See LICENSE file for licensing details.

"""Charm the application."""

import json
import logging
import os
from dataclasses import dataclass
from typing import Optional

from ops import pebble
from ops.jujucontext import _JujuContext as Context
from ops.model import _ModelBackend as HookTools

logger = logging.getLogger(__name__)


tool = HookTools()
context = Context.from_dict(os.environ)

# TODO get container names from charmcraft.yaml
pebble = {
    name: pebble.Client(socket_path=f"/charm/containers/{name}/pebble.socket") for name in ("k6",)
}


@dataclass(frozen=True)
class RelationChangedEvent:
    """All that's special about RelationChanged. Could be part of ops."""

    relation_name: str
    relation_id: int


@dataclass(frozen=True)
class ActionEvent:
    """All that's special about Action. Could be part of ops."""

    name: str
    params: dict


def parse_event() -> Optional[dataclass]:
    """Convert the "environ" context into event context.

    Ideally would be a method of JujuContext.
    """
    # Split dispatch path by "/", so we get e.g.
    # - ("actions", "<action_name>"); or
    # - ("hooks", "start")
    match context.dispatch_path.split("/"):
        case ["actions", name]:
            return ActionEvent(context.action_name, tool.action_get())
        case ["hooks", name]:  # name is e.g. "k6-relation-changed"
            if name.endswith("-relation-changed"):
                return RelationChangedEvent(context.relation_name, context.relation_id)

    return None


def common_exit_hook():
    """Charm without ops.Main or events."""
    # print({k: v for k, v in os.environ.items() if k.startswith("JUJU")})
    event = parse_event()
    match event:
        case RelationChangedEvent(relation_name="k6"):
            pebble["k6"].remove_path("/tests", recursive=True)

            # Get data from unit bag
            # TODO write all data again on upgrade-charm
            data = tool.relation_get(context.relation_id, context.remote_unit_name, is_app=False)
            if tests := data.get("tests"):
                for filename, contents in json.loads(tests).items():
                    pebble["k6"].push(f"/tests/{filename}", contents, make_dirs=True)

        case ActionEvent(name="run"):
            print(f"Running action: {event.name}, {event.params}")

            process = pebble["k6"].exec(["k6", "run", f"/tests/{event.params['testname']}"])
            out, _ = process.wait_output()
            print(out)

    tool.status_set("active", "")


if __name__ == "__main__":
    common_exit_hook()
