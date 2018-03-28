#!/usr/bin/env python

import os, sys, argparse, pandas, tifffile, numpy
from taniclass import spotmarker

# prepare spot marker
marker = spotmarker.SpotMarker()

# defaults
input_filename = None
marker_filename = None
output_filename = None
invert_image = False

# parse arguments
parser = argparse.ArgumentParser(description='plot centroids to check gaussian fitting.', \
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-o', '--output-file', nargs=1, default=output_filename, \
                    help='output multipage-tiff file ([basename]_marked.tif if not specified)')

parser.add_argument('-f', '--marker-file', nargs=1, default=marker_filename, \
                    help='read marker tsv file ([basename].txt if not specified)')
parser.add_argument('-z', '--marker-size', nargs=1, type=int, default=[marker.marker_size], \
                    help='marker size to plot')
parser.add_argument('-c', '--marker-colors', nargs=3, type=str, default=marker.marker_colors, \
                    metavar=('NEW', 'CONT', 'END'), \
                    help='marker colors for new/continued/end spots')

parser.add_argument('-i', '--invert-image', action='store_true', default=invert_image, \
                    help='invert image look-up table')

parser.add_argument('input_file', nargs=1, default=input_filename, \
                    help='input multpage-tiff file to plot markers')

args = parser.parse_args()

# set arguments
input_filename = args.input_file[0]
marker.marker_size = args.marker_size[0]
marker.marker_colors = args.marker_colors
invert_image = args.invert_image

if args.marker_file is None:
    marker_filename = os.path.join(os.path.dirname(input_filename),\
                      os.path.splitext(os.path.basename(input_filename))[0] + '.txt')
else:
    marker_filename = args.marker_file[0]

if args.output_file is None:
    output_filename = os.path.splitext(os.path.basename(input_filename))[0] + '_marked.tif'
    if input_filename == output_filename:
        raise Exception('input_filename == output_filename')
else:
    output_filename = args.output_file[0]

# read image
orig_image = tifffile.imread(input_filename)
if len(orig_image.shape) == 2:
    orig_image = numpy.array([orig_image])

# convert image to 8-bit RGB color
image_color = marker.convert_to_color(orig_image)
if invert_image is True:
    image_color = 255 - image_color

# read results
print("Read spots from %s." % (marker_filename))
spot_table = pandas.read_table(marker_filename, comment = '#')

# mark tracking status
print("Marked %d spots on %s." % (len(spot_table), input_filename))
image_color = marker.mark_spots(image_color, spot_table)

# output multipage tiff
print("Output image file to %s." % (output_filename))
tifffile.imsave(output_filename, image_color)
