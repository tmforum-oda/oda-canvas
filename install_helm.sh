#!/bin/sh
if ! command -v helm >/dev/null 2>&1
then
  echo "***"
  echo " Installing Helm"
  echo "***"
  echo ""
  filetmp=$RANDOM
  curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 -o $filetmp.sh
  chmod 700 $filetmp.sh
  ./$filetmp.sh
  rm $filetmp.sh
else
  echo "***"
  echo " Looks like Helm may be installed already."
  echo "***"
  echo ""
fi