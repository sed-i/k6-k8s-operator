#!/usr/bin/env python3
# Copyright 2024 sed-i
# See LICENSE file for licensing details.

"""Charm the application."""

import logging
import os

from ops.jujucontext import _JujuContext as Context
from ops.model import _ModelBackend as HookTools


logger = logging.getLogger(__name__)


context = Context.from_dict(os.environ)
tool = HookTools()


def common_exit_hook():
    print(context)
    tool.status_set("active", "")


if __name__ == "__main__":  # pragma: nocover
    common_exit_hook()

