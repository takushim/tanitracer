#!/usr/bin/env python

import os, sys, argparse, pandas, numpy

# defaults
input_filename = None
output_filename = None
count_modes = ['regression', 'lifetime', 'counting']
selected_mode = count_modes[0]
lifetime_span = [2, 11]
count_plane = 0

# parse arguments
parser = argparse.ArgumentParser(description='count lifetime using regression.', \
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-o', '--output-file', nargs=1, default = None, \
                    help='output tsv file name ([basename].txt if not specified)')

group = parser.add_mutually_exclusive_group()
group.add_argument('-R', '--regression', action='store_const', default=selected_mode, \
                    dest='selected_mode', const=count_modes[0], \
                    help='count using regression (default)')
group.add_argument('-L', '--lifetime', action='store_const', \
                    dest='selected_mode', const=count_modes[1], \
                    help='count using lifetime')
group.add_argument('-C', '--counting', action='store_const', \
                    dest='selected_mode', const=count_modes[2], \
                    help='count spots withoug tracking')
                    
parser.add_argument('-l', '--lifetime-span', nargs = 2, type = int, \
                    metavar = ('START', 'END'), default = lifetime_span, \
                    help='specify the span to coung using lifetime (start >= 2)')
parser.add_argument('-c', '--count-plane', nargs = 1, type = int, default=[count_plane], \
                    help='specify the plane to count spots')

parser.add_argument('input_file', nargs=1, default=input_filename, \
                    help='input multpage-tiff file to plot markers')

args = parser.parse_args()

# set arguments
input_filename = args.input_file[0]
selected_mode = args.selected_mode
count_plane = args.count_plane[0]
lifetime_span = args.lifetime_span
if lifetime_span[0] < 2:
    raise Exception('lifetime starting plane must be >= 2')

if args.output_file is None:
    output_filename = os.path.splitext(os.path.basename(input_filename))[0] + '_liftime.txt'
    if input_filename == output_filename:
        raise Exception('input_filename == output_filename')
else:
    output_filename = args.output_file[0]

# read results, sort, and RESET index (important)
spot_table = pandas.read_table(input_filename, comment = '#')
spot_table = spot_table.sort_values(by = ['total_index', 'plane']).reset_index(drop=True)

# lifetime or regression
if selected_mode == 'regression' or selected_mode == 'lifetime':
    # count lifetime
    lifetime_series = spot_table['total_index'].value_counts()
    spot_table = spot_table.drop_duplicates(subset='total_index', keep='first').reset_index(drop=True)
    spot_table['lifetime'] = lifetime_series.sort_index().tolist()

    # regression of lifetime
    if selected_mode == 'regression':
        spot_table = spot_table[spot_table.plane == 0]
    else:
        spot_table = spot_table[(lifetime_span[0] <= spot_table.plane) & (spot_table.plane <= lifetime_span[1])]

    # output tsv
    print(spot_table['lifetime'].tolist())
    lifetime_series = spot_table['lifetime'].value_counts().sort_index()

    lifetime_counts = numpy.zeros(max(lifetime_series.index.tolist()), dtype=numpy.int)
    lifetime_counts[numpy.asarray(lifetime_series.index.tolist()) - 1] = lifetime_series.tolist()

    print(lifetime_counts)
    lifetime_table = pandas.DataFrame({ \
                        'lifetime' : numpy.arange(len(lifetime_counts)) + 1, \
                        'count' : lifetime_counts}, \
                        columns = ['lifetime', 'count'])
    lifetime_table.to_csv(output_filename, sep='\t', index=False)
    
elif selected_mode == 'counting':
    spot_table = spot_table[spot_table.plane == count_plane]
    print("File %s, Plane %d, spots %d" % (input_filename, count_plane, len(spot_table)))
    
else:
    raise Exception('invalid counting mode')


