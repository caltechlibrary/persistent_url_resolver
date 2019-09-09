#!/usr/bin/env python3.7
#

import os
import sys
from subprocess import run, Popen, PIPE

mysql_cmd = '/usr/bin/mysql'

#
# Run and retrieve the purr.bash scripts from the EPrints repositories
#


#
# purr_eprints - contact the MySQL on a remote EPrints server and
# retrieve the assigned resolver URL and eprint record URL.
#
# EPrints' SQL:  
#
#  "SELECT id_number, eprintid FROM eprint WHERE eprint_status = 'archive'"
#
# Write out "purr_${hostname}.csv" with resolver URL and EPrints URL.
# 
# Example SQL script "purr_${hostname}.csv"
#
# -- 
# -- Run this script from remote system using the --batch option to generate
# -- a Tab delimited version of output. Use tr to convert tab to comma.
# --
# USE ${DB_NAME_HERE};
# SELECT id_number, 
#     CONCAT('${URL_PREFIX_HERE','/', eprintid) 
#     FROM eprint WHERE eprint_status = 'archive';
#
def purr_eprints(connect_string, sql_script_name, output_csv):
    remote_cmd = f'''mysql --batch < '{sql_script_name}' '''
    cmd = [ 
            "ssh", 
            connect_string, 
            remote_cmd
          ]
    with Popen(cmd, stdout = PIPE, encoding = 'utf-8') as proc:
        src = proc.stdout.read().replace("\t", ",")
        with open(output_csv, 'w') as fp:
            fp.write(src)
        t = src.split('\n')
        print(f'Wrote {len(t)} lines to {output_csv}')
#
# Main logic
#
if __name__ == "__main__":
    connect_string = ''
    sql_script_name = ''
    output_csv = ''
    if len(sys.argv) == 4:
        connect_string, sql_script_name, output_csv = sys.argv[1], sys.argv[2], sys.argv[3]
    else:
        print(f"USAGE:\n\t{os.path.basename(sys.argv[0])} SSH_CONNECT_STRING SQL_SCRIPT_NAME OUTPUT_CSV_FILENAME")
        sys.exit(1)
    print(f"Connecting with {connect_string}")
    print(f"Running script {sql_script_name}")
    purr_eprints(connect_string, sql_script_name, output_csv)


