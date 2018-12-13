#!/usr/bin/env python
""" Go away pylint. """

import argparse
import json

def load_json_data(data_file):
    """ Go away pylint. """

    try:
        with open(data_file) as json_data:
            data = json.load(json_data)
    except (IOError, ValueError) as err:
        print err
        exit(1)
    return data


def parse_json_data(data):
    """ Go away pylint. """

    new_objects = []
    new_object = {}
    for obj in data:
        try:
            if obj['certname'] != new_object['certname']:
                new_objects.append(new_object)
                new_object = {}
                new_object['certname'] = obj['certname']
        except KeyError:
            new_object['certname'] = obj['certname']
        new_object[obj['name']] = obj['value']
    return new_objects


def _generate_csv_output(data, column_names, fact_column_map=None):
    """ Go away pylint. """

    header = ','.join(column_names)
    print header

    for obj in data:
        values = []
        for column_name in column_names:
            try:
                if fact_column_map:
                    value = obj[fact_column_map[column_name]]
                else:
                    value = obj[column_name]
            except KeyError:
                value = u'Undefined'
            values.append(value.replace(',', '_'))
        line = ','.join(values)
        print line


def output_as_csv(data, fact_mappings=None):
    """ Go away pylint. """

    column_names = []
    fact_names = set()
    fact_column_map = {}

    if fact_mappings:
        fact_maps = fact_mappings.split(',')
        for fact_map in fact_maps:
            try:
                fact_name, column_name = fact_map.split('=')
            except ValueError:
                fact_name = fact_map
                column_name = fact_name
            column_names.append(column_name)
            fact_column_map[column_name] = fact_name
    else:
        for obj in data:
            for key in obj:
                if key != 'certname':
                    fact_names.add(key)

        fact_names = sorted(list(fact_names))
        fact_names.insert(0, u'certname')
        column_names = fact_names

    _generate_csv_output(data, column_names, fact_column_map)


def output_as_json(data, json_type):
    """ Go away pylint. """

    if json_type == 'minjson':
        print json.dumps(data)
    else:
        print json.dumps(data, indent=4)


def main():
    """ Go away pylint. """

    parser = argparse.ArgumentParser(description='''Processes a JSON file containing
                                     PQL output and produces either JSON with the
                                     the original objects merged on 'certname',
                                     or CSV output.''')
    group = parser.add_mutually_exclusive_group()

    parser.add_argument('file', help='File of PQL JSON output to process')
    group.add_argument('-o', '--outformat', choices=['json', 'minjson', 'csv'],
                       help='''Choose the output format: JSON (the default), minified
                       JSON, or CSV.  Use of this option for CSV will produce output
                       with 'certname' in the first field of the line, then
                       remaining facts from JSON file in ascending sort order.''')
    group.add_argument('-H', '--headers',
                       help='''String of comma-separated values for use as CSV headers
                       with optional factname-to-header mapping (factname=header).
                       Implies that the output format will be CSV.''')

    args = parser.parse_args()
    query_results = load_json_data(args.file)
    new_json = parse_json_data(query_results)

    if args.outformat == 'csv' or args.headers is not None:
        output_as_csv(new_json, args.headers)
    else:
        output_as_json(new_json, args.outformat)


if __name__ == "__main__":
    main()
