# Script: start-jupyter.sh
# Purpose: Docker run script.
###############################################################################

set -o nounset    # give error for any unset variables
set -o errexit    # exit if a command returns non-zero status

EXEC_USER=jupyter
JUPYTER_CMD='jupyter lab --port=8888 --no-browser --ip=0.0.0.0  --notebook-dir=/opt/notebooks'

# if running from docker the nohup output will go to the console.
EXEC_CMD="nohup $JUPYTER_CMD &"

echo "Starting JupyterLab..."
su -l $EXEC_USER -c "$EXEC_CMD"
