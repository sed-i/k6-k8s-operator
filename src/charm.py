#!/usr/bin/env python3
# Copyright 2024 sed-i
# See LICENSE file for licensing details.

"""Charm the application."""

import logging
import os
import json
import yaml
from ops.jujucontext import _JujuContext as Context
from ops.model import _ModelBackend as HookTools
from ops import pebble


logger = logging.getLogger(__name__)


tool = HookTools()

# TODO get container names from charmcraft.yaml
pebble = {name: pebble.Client(socket_path=f"/charm/containers/{name}/pebble.socket") for name in ("k6", )}


def event() -> tuple:
    # Split dispatch path by "/", so we get e.g. 
    # - ("actions", "<action_name>"); or
    # - ("hooks", "start")
    context = Context.from_dict(os.environ)
    kind, name = context.dispatch_path.split("/")
    return (kind, name, context)


def common_exit_hook():
    print({k: v for k, v in os.environ.items() if k.startswith('JUJU')})
    match event():
        case ["hooks", "k6-relation-changed", context]:
            pebble["k6"].remove_path("/tests", recursive=True)

            # Get data from unit bag
            # TODO write all data again on upgrade-charm
            data = tool.relation_get(context.relation_id, context.remote_unit_name, is_app=False)
            if tests := data.get("tests"):
                for filename, contents in json.loads(tests).items():
                    pebble["k6"].push(f"/tests/{filename}", contents, make_dirs=True)

        case ["hooks", name, context]:
            print(f"Running hook: {name}")
            tool.status_set("active", "")

        case ["actions", name, context]:
            params: dict = tool.action_get()
            print(f"Running action: {name}, {params}, {type(params)}")
            
            if name == "run":
                process = pebble["k6"].exec(["k6", "run", f"/tests/{params['testname']}"])
                out, _ = process.wait_output()
                print(out)


if __name__ == "__main__":  # pragma: nocover
    common_exit_hook()

