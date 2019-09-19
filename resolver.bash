#!/bin/bash

#
# Setup logging to a log file
#
function setup_logfile() {
	BNAME="$1" #$(basename "$0" ".bash")"
	TIME=$(date +%Y-%m-%d)
	LOG_FILE="logs/${TIME}-${BNAME}.log"
	if [ ! -d "logs" ]; then
		mkdir -p "logs"
	fi
	echo "${LOG_FILE}"
}

cd /Sites/persistent_url_resolver
LOG_FILE=$(setup_logfile "harvest")
echo "$(date) (pid $$) Harvest started"
python resolver.py >>"${LOG_FILE}" 2>&1
if [[ "$?" == "0" ]]; then
	echo "$(date) (pid $$) Harvest completed"
else
	echo "$(date) (pid $$) python resolver.py failed, aborting"
	echo "$(date) (pid $$) aborted $(basename "$0")"
	exit 1
fi

echo "$(date) (pid $$) All done"
