# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
# Usage:
#   env DB=postgresql ./run-tests.sh

# Quit on errors
set -o errexit

# Quit on unbound symbols
set -o nounset

pydocstyle invenio_oauth2server
isort -rc -c -df **/*.py
check-manifest --ignore ".travis-*"
sphinx-build -qnNW docs docs/_build/html
docker-services-cli up ${DB}
python setup.py test
sphinx-build -qnNW -b doctest docs docs/_build/doctest
tests_exit_code=$?
docker-services-cli down
exit "$tests_exit_code"
