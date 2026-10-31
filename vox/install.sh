#!/usr/bin/env bash
# The Vox effects are part of the main skill now - this runs the main installer.
exec bash "$(cd "$(dirname "$0")" && pwd)/../install.sh" "$@"
