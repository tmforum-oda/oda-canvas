#!/bin/sh

PREVIOUS_CONTENT=""

# Function to run the command based on the ConfigMap content
run_command() {
  # Checking if the ConfigMap file exists and is non-empty
  if [ -s /config/run-command/run-command ]; then
    CONFIG_CONTENT=$(cat /config/run-command/run-command)
    PREVIOUS_CONTENT="$CONFIG_CONTENT"
  else
    # This is default behavior if ConfigMap is missing or empty, this will make sure componentoperator run in default with Istio Operator
    CONFIG_CONTENT=""
    echo "ConfigMap not found or empty, running default command."
  fi

  if echo "$CONFIG_CONTENT" | grep -q "apiOperatorKong"; then
    CMD="kopf run --namespace=$COMPONENT_NAMESPACE componentOperator/componentOperator.py apiOperatorIstio/apiOperatorIstiowithKong.py securityController/securityControllerKeycloak.py apiOperatorKong/apiOperatorKong.py"
  elif echo "$CONFIG_CONTENT" | grep -q "apiOperatorApisix"; then
    CMD="kopf run --namespace=$COMPONENT_NAMESPACE componentOperator/componentOperator.py apiOperatorIstio/apiOperatorIstiowithApisix.py securityController/securityControllerKeycloak.py apiOperatorApisix/apiOperatorApisix.py"
  else
    CMD="kopf run --namespace=$COMPONENT_NAMESPACE componentOperator/componentOperator.py apiOperatorIstio/apiOperatorIstio.py securityController/securityControllerKeycloak.py"
  fi

  echo "Running command: $CMD"
  sh -c "$CMD" &
  KOPF_PID=$!
  echo "KOPF_PID is $KOPF_PID"
}

# Ensuring current process terminates before running new process to avoid multiple instance of these operator running in parallel
terminate_previous_kopf() {
  if [ -n "$KOPF_PID" ] && kill -0 "$KOPF_PID" > /dev/null 2>&1; then
    echo "Terminating previous kopf process with PID $KOPF_PID"
    kill -TERM "$KOPF_PID"
    wait "$KOPF_PID"
  fi
}

# Ensuring default runs if ConfigMap is not found
if [ ! -f /config/run-command/run-command ]; then
  echo "No ConfigMap found initially, running default command."
  run_command
else
  run_command
fi

# Watcher for changes to the ConfigMap content and it will restart the command only if the content changes
while true; do
  # Using `inotifywait` to wait for the ConfigMap file to be created if it was existing already
  if [ ! -f /config/run-command/run-command ]; then
    echo "Waiting for ConfigMap file to be created..."
    inotifywait -e create /config/run-command
    echo "ConfigMap file detected. Checking content and running command."
    
    # Immediately checking content and running based on content post the creation of the ConfigMap
    terminate_previous_kopf
    run_command
  fi

  # Watching changes once the file is detected
  inotifywait -e modify /config/run-command/run-command
  echo "ConfigMap changed, checking for content update..."

  # Rechecking the content
  if [ -s /config/run-command/run-command ]; then
    NEW_CONTENT=$(cat /config/run-command/run-command)
  else
    NEW_CONTENT=""
  fi

  # Restarting the command if the content change observed
  if [ "$NEW_CONTENT" != "$PREVIOUS_CONTENT" ]; then
    echo "Content has changed, reloading kopf process..."
    terminate_previous_kopf
    PREVIOUS_CONTENT="$NEW_CONTENT"
    run_command
  else
    echo "No content changes detected, skipping restart."
  fi
done