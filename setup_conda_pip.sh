#!/bin/bash

ENV_NAME="tradingbot"
CONDA_PATH="/opt/miniconda3/envs/$ENV_NAME/etc/conda"

mkdir -p $CONDA_PATH/activate.d
mkdir -p $CONDA_PATH/deactivate.d

cat << 'EOF' > $CONDA_PATH/activate.d/env_vars.sh
#!/bin/bash
export OLD_PIP="$PIP"
export PIP="$(dirname $(dirname $CONDA_EXE))/envs/tradingbot/bin/pip"
EOF

cat << 'EOF' > $CONDA_PATH/deactivate.d/env_vars.sh
#!/bin/bash
export PIP="$OLD_PIP"
unset OLD_PIP
EOF

echo "Conda pip activation script installed successfully."