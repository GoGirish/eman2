#!/usr/bin/env bash

set -xe

export PYTHONUNBUFFERED=1

# Download and install Miniconda
export MINICONDA_URL="https://repo.continuum.io/miniconda"

if [ ! -d "$HOME/miniconda2" ] && [ -v MINICONDA_FILE ];then
    curl -L -O "${MINICONDA_URL}/${MINICONDA_FILE}"
    bash $MINICONDA_FILE -b
fi

# Configure conda
source ${HOME}/miniconda2/bin/activate root
conda config --set show_channel_urls true


conda build purge
if [ "$(uname -s)" != "Darwin" ];then
    conda build recipes/eman -c cryoem -c defaults -c conda-forge --numpy 1.8
else
    conda build recipes/eman -c cryoem -c defaults -c conda-forge
fi
