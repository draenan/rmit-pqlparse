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

PATH=/bin:/usr/bin:/opt/puppetlabs/bin:/opt/RMIT/bin

progname=${0##*/}

usage() {
    echo "Usage: $progname [-d] [-v] [-n] [-m email_address] file"
}

cleanup() {
    [ "$verbose" ] && echo "Cleaning up files ..."
    for file in $pql_output $report_file; do
        [ -e $file ] && rm $file
    done
}

debug= verbose= nomail= mail_to_override= report_definition=

while getopts :hdvnm: opt; do
    case $opt in
        h)
            usage
            echo
            echo "Required parameter:"
            echo "    file              File containing report definition"
            echo
            echo "Optional parameters:"
            echo "    -h                Show this help message and exit"
            echo "    -d                Debug mode (noop, implies '-n')"
            echo "    -v                Be verbose"
            echo "    -n                Do not email report"
            echo "    -m email_address  Mail output to email_address"
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
        m)
            mail_to_override=$OPTARG
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

if [ -z "$debug" ]; then
    if [ $(/usr/bin/id -u) -ne "0" ]; then
        echo "Script needs to be run as root." >&2
        exit 1
    elif [ ! -r "${HOME}/.puppetlabs/token" ]; then
        echo "Could not read ${HOME}/.puppetlabs/token" >&2
        exit 1
    fi
fi

report_definition="$1"

if [ ! -r "$report_definition" ]; then
    echo "Could not read the file '$report_definition'" >&2
    exit 1
fi

report_definition=$(readlink -f $report_definition)

query= format= csv_header= mail_from= mail_to=
source $report_definition

if [ ! -z "$format" ]; then
    if [ "$format" != "csv" -a "$format" != "json" -a "$format" != "minjson" ]; then
        echo "'format' not set to one of 'csv', 'json', or 'minjson'."
        exit 1
    fi
fi

[ -z "$format" -a -z "$csv_header" ] && format="csv"
if [ ! -z "$format" ]; then
    if [ "$format" == "csv" -a "$csv_header" ]; then
        format=
    elif [ "$csv_header" ]; then
        echo "'csv_header' is defined but 'format' is defined as something other than 'csv'." >&2
        exit 1
    fi
fi

[ ! -z "$mail_to_override" ] && mail_to="$mail_to_override"
mail_to=${mail_to:="isunix@rmit.edu.au"}
mail_from=${mail_from:="Server Platforms - Unix <isunix@rmit.edu.au>"}

if [ -z "$query" ]; then
    echo "No PQL query set." >&2
    exit 1
fi

now="$(date +%Y%m%d_%H%M%S)"

if [ -z "$report_name" ]; then
    report_name="${report_definition##*/}"
    report_name="${report_name%%\.*}"
fi

pql_output="/tmp/${now}_${report_name}.temp.json"

if [ "$format" == "json" -o "$format" == "minjson" ]; then
    file_ext="json"
else
    file_ext="csv"
fi

report_file="/tmp/${now}_${report_name}.${file_ext}"

[ "$verbose" ] && echo "Running puppet query..."
if [ "$debug" ]; then
    echo "DEBUG: puppet query \"$query\" > $pql_output"; echo
else
    puppet query "$query" > $pql_output
fi

if [ "$?" -ne 0 ]; then
    echo "Error running 'puppet query'." >&2
    cleanup
    exit 1
fi
[ "$verbose" ] && echo "Processing query results..."

if [ "$debug" ]; then
    if [ "$csv_header" ]; then
        echo "DEBUG: pqlparse.py -H \"$csv_header\" $pql_output > ${report_file}"; echo
    else
        echo "DEBUG: pqlparse.py -o $format $pql_output > ${report_file}"; echo
    fi
else
    if [ "$csv_header" ]; then
        pqlparse.py -H "$csv_header" $pql_output > ${report_file}
    else
        pqlparse.py -o $format $pql_output > ${report_file}
    fi
fi

if [ "$?" -ne 0 ]; then
    echo "Error running 'pqlparse.py'." >&2
    cleanup
    exit 1
fi
if [ -z "$nomail" -a  ! "$debug" ]; then
    [ "$verbose" ] && echo "Sending report ${report_file}..."
    cat <<EOF | mailx -r "$mail_from" -s "Output of report \"$report_name\" attached." -a $report_file $mail_to
Please find attached the output of the PuppetDB Query Report "${report_name}" as defined in the file "${report_definition}" on the Puppet Master.

This report represents the current state of hosts known to Puppet.  It does not include:

- Hosts that are not managed by Puppet
- Hosts that have not been reporting to Puppet for various reasons for time exceeding the 'node-ttl' setting.

EOF
    if [ "$?" -ne 0 ] ; then
        echo "Error sending mail." >&2
        cleanup
        exit 1
    fi
else
    echo "DEBUG: Would have sent report ${report_file}"
    echo "         FROM \"${mail_from}\""
    echo "         TO   \"${mail_to}\"."; echo
fi

cleanup
exit

