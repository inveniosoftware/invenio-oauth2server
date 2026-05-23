# SPDX-FileCopyrightText: 2015-2018 CERN.
# SPDX-FileCopyrightText: 2023 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""Blueprint instances."""

from .server import blueprint as server_blueprint
from .settings import blueprint as settings_blueprint

__all__ = (
    "server_blueprint",
    "settings_blueprint",
)
