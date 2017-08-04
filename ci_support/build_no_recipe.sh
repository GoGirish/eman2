#!/usr/bin/env bash

set -xe

# Download and install Miniconda
export MINICONDA_URL="https://repo.continuum.io/miniconda"

curl -L -O "${MINICONDA_URL}/${MINICONDA_FILE}"
bash $MINICONDA_FILE -b

# Conda-install packages
source ${HOME}/miniconda2/bin/activate root
conda config --set show_channel_urls true

# Following Wiki instructions at
# http://blake.bcm.edu/emanwiki/EMAN2/COMPILE_EMAN2_ANACONDA
if [ "$(uname -s)" != "Darwin" ];then
    conda install --yes --quiet eman-deps="*"="np18*" -c cryoem -c defaults -c conda-forge
else
    conda install --yes --quiet eman-deps -c cryoem -c defaults -c conda-forge
fi

# Build and install eman2
export build_dir=$HOME/build_eman

rm -rf ${build_dir}
mkdir -p ${build_dir}
cd ${build_dir}

cmake "${OLDPWD}"
make
make install
make test-verbose

# Run tests
e2version.py
e2speedtest.py

cd -
mpirun -n 4 $(which python) examples/mpi_test.py
bash tests/run_prog_tests.sh
python tests/test_EMAN2DIR.py
