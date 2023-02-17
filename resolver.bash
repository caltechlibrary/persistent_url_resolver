#!/bin/bash

# Make sure MySQL client is available
if [[ -d "/opt/local/bin" ]]; then
        export PATH="/opt/local/bin:$PATH"
fi

## # Make sure I am using the Mini-conda version of Python and libs
## if [[ -d "/opt/Miniconda/bin" ]]; then
##         # added by Miniconda3 installer
##         PATH="/opt/Miniconda/bin:$PATH"
##         export PATH
##         # added by Miniconda3 4.5.12 installer
##         # >>> conda init >>>
##         # !! Contents within this block are managed by 'conda init' !!
##         __conda_setup="$(CONDA_REPORT_ERRORS=false 'opt/Miniconda/bin/conda' shell.bash hook 2>/dev/null)"
##         if [ $? -eq 0 ]; then
##                 \eval "$__conda_setup"
##         else
##                 if [ -f "/opt/Miniconda/etc/profile.d/conda.sh" ]; then
##                         . "/opt/Miniconda/etc/profile.d/conda.sh"
##                         CONDA_CHANGEPS1=false conda activate base
##                 else
##                         \export PATH="/opt/Miniconda/bin:$PATH"
##                 fi
##         fi
##         unset __conda_setup
##         # <<< conda init <<<
## elif [[ -d "${HOME}/miniconda3/bin" ]]; then
##         echo "Setting up Miniconda from ${HOME}/miniconda3"
##         # added by Miniconda3 installer
##         PATH="${HOME}/miniconda3/bin:$PATH"
##         export PATH
##         # added by Miniconda3 4.5.12 installer
##         # >>> conda init >>>
##         # !! Contents within this block are managed by 'conda init' !!
##         __conda_setup="$(CONDA_REPORT_ERRORS=false '${HOME}/miniconda3/bin/conda' shell.bash hook 2>/dev/null)"
##         if [ $? -eq 0 ]; then
##                 \eval "$__conda_setup"
##         else
##                 if [ -f "${HOME}/miniconda3/etc/profile.d/conda.sh" ]; then
##                         . "${HOME}/miniconda3/etc/profile.d/conda.sh"
##                         CONDA_CHANGEPS1=false conda activate base
##                 else
##                         \export PATH="${HOME}/miniconda3/bin:$PATH"
##                 fi
##         fi
##         unset __conda_setup
##         # <<< conda init <<<
## fi

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

# Load the user .profile to pickup paths to things.
. $HOME/.profile
cd /Sites/persistent_url_resolver
LOG_FILE=$(setup_logfile "harvest")
echo "$(date) (pid $$) Harvest started"
echo "$(date) (pid $$) Harvest started" >>"${LOG_FILE}"
python resolver.py >>"${LOG_FILE}" 2>&1
if [[ "$?" == "0" ]]; then
	echo "$(date) (pid $$) Harvest completed"
else
	echo "$(date) (pid $$) python resolver.py failed, aborting"
	echo "$(date) (pid $$) aborted $(basename "$0")"
	exit 1
fi

echo "$(date) (pid $$) All done"
