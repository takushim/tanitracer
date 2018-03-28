#!/usr/bin/env python

import os, sys, argparse, pandas, numpy
from taniclass import spotfilter

# defaults
input_filename = None
output_filename = None
count_modes = ['regression', 'lifetime', 'counting']
selected_mode = count_modes[0]
lifetime_span = [1, 20]
count_plane = 0
start_regression = 0

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
                    help='specify the span to coung using lifetime (start >= 1)')
parser.add_argument('-r', '--start-regression', nargs = 1, type = int, default=[start_regression], \
                    help='specify the plane to start regression')
parser.add_argument('-c', '--count-plane', nargs = 1, type = int, default=[count_plane], \
                    help='specify the plane to count spots')

parser.add_argument('input_file', nargs=1, default=input_filename, \
                    help='input multpage-tiff file to plot markers')

args = parser.parse_args()

# set arguments
input_filename = args.input_file[0]
selected_mode = args.selected_mode
count_plane = args.count_plane[0]
start_regression = args.start_regression[0]
lifetime_span = args.lifetime_span
if lifetime_span[0] < 1:
    raise Exception('lifetime starting plane must be >= 1')

if args.output_file is None:
    if selected_mode == 'lifetime':
        output_filename = os.path.splitext(os.path.basename(input_filename))[0] + '_liftime.txt'
    elif selected_mode == 'regression':
        output_filename = os.path.splitext(os.path.basename(input_filename))[0] + '_regression.txt' 
    elif selected_mode == 'counting':
        output_filename = os.path.splitext(os.path.basename(input_filename))[0] + '_counting.txt'
    else:
        raise Exception('invalid counting mode')

    if input_filename == output_filename:
        raise Exception('input_filename == output_filename')
else:
    output_filename = args.output_file[0]

# read results, sort, and RESET index (important)
spot_table = pandas.read_table(input_filename, comment = '#')
spot_table = spot_table.sort_values(by = ['total_index', 'plane']).reset_index(drop=True)

# lifetime or regression
if selected_mode == 'regression':
    # drop planes for regression
    spot_table = spot_table[spot_table.plane >= start_regression].reset_index(drop=True)
        
    # calculate lifetime
    spot_table = filter.calculate_lifetime(spot_table)
    spot_table = spot_table[spot_table.plane == start_regression].reset_index(drop=True)
    
    # prepare data
    output_columns = ['lifetime', 'spots']
    lifetime_max = spot_table.lifetime.max()
    output_indexes = [i for i in range(1, lifetime_max + 1)]
    output_counts = [len(results[spot_table.lifetime == i]) for i in output_indexes]

elif selected_mode == 'lifetime':
    # calculate lifetime
    spot_table = filter.calculate_lifetime(spot_table)
    spot_table = spot_table[(lifetime_span[0] <= spot_table.plane) & \
                            (spot_table.plane <= lifetime_span[1])].reset_index(drop=True)

    # prepare data
    output_columns = ['lifetime', 'spots']
    lifetime_max = spot_table.lifetime.max()
    output_indexes = [i for i in range(1, lifetime_max + 1)]
    output_counts = [len(results[spot_table.lifetime == i]) for i in output_indexes]

elif selected_mode == 'counting':
    # prepare data
    output_columns = ['plane', 'spots']
    plane_max = spot_table.plane.max()
    output_indexes = [i for i in range(1, plane_max + 1)]
    output_counts = [len(results[spot_table.plane == i]) for i in output_indexes]

else:
    raise Exception('invalid counting mode')


output_table = pandas.DataFrame({ \
                    output_columns[0] : output_indexes, \
                    output_columns[1] : output_counts}, \
                    columns = output_columns)

output_table.to_csv(output_filename, sep='\t', index=False)

