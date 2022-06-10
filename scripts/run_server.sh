source ./venv/bin/activate
echo "Running bot server..."

make run ENV_FOR_DYNACONF=dev
tail -n 0 -f console.log
