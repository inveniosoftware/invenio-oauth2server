#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2015-2018 CERN.
# SPDX-FileCopyrightText: 2022 RERO.
# SPDX-FileCopyrightText: 2022-2023 Graz University of Technology.
# SPDX-License-Identifier: MIT
#
# Usage:
#   env DB=postgresql ./run-tests.sh

# Quit on errors
set -o errexit

# Quit on unbound symbols
set -o nounset

# Always bring down docker services
function cleanup {
    eval "$(docker-services-cli down --env)"
}
trap cleanup EXIT

pybabel extract -F pyproject.toml invenio_oauth2server --output-file /dev/null
python -m sphinx.cmd.build -qnNW docs docs/_build/html
eval "$(docker-services-cli up --db ${DB:-postgresql} --env)"
python -m pytest
tests_exit_code=$?
exit "$tests_exit_code"
