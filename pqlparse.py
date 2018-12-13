#!/usr/bin/env python
""" Go away pylint. """

import json

def load_json_data(data_file):
    """ Go away pylint. """

    with open(data_file) as json_data:
        data = json.load(json_data)
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


def output_as_json(data):
    """ Go away pylint. """

    print json.dumps(data, indent=4)


def main():
    """ Go away pylint. """

    query_results = load_json_data('20181029_puppet_hosts.json')
    new_json = parse_json_data(query_results)
    # output_as_json(new_json)
    output_as_csv(new_json)


if __name__ == "__main__":
    main()
