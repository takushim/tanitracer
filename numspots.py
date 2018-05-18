#!/usr/bin/env python

import os, platform, sys, glob, argparse
import pandas, numpy

# defaults
input_filenames = None
output_filename = 'numspots.txt'

# parse arguments
parser = argparse.ArgumentParser(description='count number of spots in files', \
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('-o', '--output-file', nargs=1, default=[output_filename], \
                    help='output tsv file name')

parser.add_argument('input_file', nargs='+', default=None, \
                    help='input WT tsv file(s) with plotting geometries')

args = parser.parse_args()

# collect input filenames
if (platform.system() == "Windows"):
    input_filenames = []
    for pattern in args.input_file:
        input_filenames.extend(sorted(glob.glob(pattern)))
    if len(input_filenames) == 0:
        raise Exception('no input filename')
else:
    input_filenames = args.input_file

# set arguments
output_filename = args.output_file[0]
spot_counts = []

# read spots
for index, input_filename in enumerate(input_filenames):
    spot_table = pandas.read_csv(input_filename, sep='\t', comment='#')
    print("Total %d spots in %s." % (len(spot_table), input_filename))
    spot_counts.append(len(spot_table))

# output tsv
result = pandas.DataFrame({'file': input_filenames, \
                           'index': numpy.arange(1, len(input_filenames) + 1), \
                           'count': spot_counts}, columns = ['file', 'index', 'count'])

print("Output tsv file to %s." % (output_filename))
result.to_csv(output_filename, sep='\t', index=False)

