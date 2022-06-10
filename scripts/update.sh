git fetch
git reset --hard origin/main

source ./venv/bin/activate
echo "Updating requirements"
make install-run

./scripts/run_server.sh
