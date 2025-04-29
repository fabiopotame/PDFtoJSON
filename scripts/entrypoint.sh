#!/bin/sh
# entrypoint para Docker
chmod +x scripts/run_tests.sh
exec "$@" 