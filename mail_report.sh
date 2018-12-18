#!/bin/bash
#
# mail_report.sh
#
# Script takes various settings from a ".report" file and uses them to:
#
# - Run a query against PuppetDB
# - Parse the query results into a useful format
# - Mail the parsed output to defined email addresses.
#
# Author: Adrian Waters <adrian.waters@rmit.edu.au>
#

PATH=/bin:/usr/bin

progname=${0##*/}

usage() {
    echo "Usage: $progname [-d] [-v] [-n] file"
}

# if [ $(/usr/bin/id -u) -ne "0" ]; then
#     echo "Script needs to be run as root." >&2
#     exit 1
# elif [ ! -r "${HOME}/.puppetlabs/token" ]; then
#     echo "Could not read ${HOME}/.puppetlabs/token" >&2
#     exit 1
# fi

cleanup() {
    [ "$verbose" ] && echo "Cleaning up files ..."
    for file in $pql_output $report_file; do
        [ -e $file ] && rm $file
    done
}

debug= verbose= nomail= report_definition=

while getopts :hdvn opt; do
    case $opt in
        h)
            usage
            echo
            echo "Required parameter:"
            echo "    file            File containing report definition"
            echo
            echo "Optional parameters:"
            echo "    -h              Show thie help message and exit"
            echo "    -d              Debug mode (noop, implies '-n')"
            echo "    -v              Be verbose"
            echo "    -n              Do not email report"
            exit
            ;;
        d)
            debug=1
            ;;
        v)
            verbose=1
            ;;
        n)
            nomail=1
            ;;
        '?')
            usage >&2
            exit 1
            ;;
    esac
done

if [ "$#" -lt 1 ];then
    usage >&2
    exit 1
fi

shift $((OPTIND - 1))

report_definition="$1"

if [ ! -r "$report_definition" ]; then
    echo "Could not read the file '$report_definition'" >&2
    exit 1
fi

query= format= csv_headers= mail_from= mail_to=
source $report_definition

[ -z "$format" -a -z "$csv_header" ] && format="csv"
[ -z "$mail_to" ] && mail_to="isunix@rmit.edu.au"
if [ -z "$mail_from" ]; then
    mail_from="\"Tech Services - Unix <isunix@rmit.edu.au>\""
else
    mail_from="\"$mail_from\""
fi

if [ -z "$query" ]; then
    echo "No PQL query set." >&2
    exit 1
else
    query="\"$query\""
fi
if [ ! -z "$format" -a ! -z "$csv_header" ]; then
    echo "'format' and 'csv_header' options are mutually exclusive." >&2
    exit 1
fi

[ ! -z "$format" ] && format="-o $format"
[ ! -z "$csv_header" ] && csv_header="-H \"$csv_header\""

now="$(date +%Y%m%d_%H%M%S)"
[ -z "$report_name" ] && report_name="${report_definition##*/}"
report_file="/tmp/${now}_${report_name%%\.*}"
pql_output="${report_file}.temp.json"

if [ "$format" == "json" -o "$format" == "minjson" ]; then
    file_ext="json"
elif [ "$format" == "csv" -o ! -z "$csv_header" ]; then
    file_ext="csv"
else
    file_ext="txt"
fi

report_file="${report_file}.${file_ext}"

[ "$verbose" ] && echo "Running puppet query..."
if [ "$debug" ]; then
    echo "DEBUG: /usr/local/bin/puppet query $query > $pql_output"
else
    /usr/local/bin/puppet query $query > $pql_output
fi

if [ "$?" -ne 0 ]; then
    echo "Error running 'puppet query'." >&2
    cleanup
    exit 1
fi
[ "$verbose" ] && echo "Processing query results..."

if [ "$debug" ]; then
    echo "DEBUG: /opt/RMIT/bin/pqlparse.py $format $csv_header $pql_output > ${report_file}"
else
    /opt/RMIT/bin/pqlparse.py $format $csv_header $pql_output > ${report_file}
fi
if [ "$?" -ne 0 ]; then
    echo "Error running 'pqlparse.py'." >&2
    cleanup
    exit 1
fi
if [ -z "$nomail" -a  ! "$debug" ]; then
    [ "$verbose" ] && echo "Sending report ${report_file}..."
    cat <<EOF | mailx -r $mail_from -s "Output of report \"$report_name\" attached." -a $report_file $mail_to
Please find attached the output of the PuppetDB Query Report
\"${report_name}\" as defined in the file \"${report_definition}\".

This report represents the current state of hosts known to Puppet.  It
does not include:

- Hosts that are not managed by Puppet
- Hosts that have not been reporting to Puppet for various reasons for
  time exceeding the 'node-ttl' setting.
EOF
    if [ "$?" -ne 0 ] ; then
        echo "Error sending mail." >&2
        cleanup
        exit 1
    fi
else
    echo "DEBUG: Would have sent report ${report_file}"
    echo "         FROM ${mail_from}"
    echo "         TO   ${mail_to}."
fi

cleanup
exit

