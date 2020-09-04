#!/usr/bin/env python

# Copyright (c) 2018-2019, Takushi Miyoshi
# Copyright (c) 2012-2019, Department of Otolaryngology, 
#                          Graduate School of Medicine, Kyoto University
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import os, sys, argparse, pandas, numpy, tifffile
from taniclass import spotmarker, spotfilter

# prepare spot marker
marker = spotmarker.SpotMarker()
filter = spotfilter.SpotFilter()

# defaults
input_filename = None
marker_filename = None
output_filename = None

# parse arguments
parser = argparse.ArgumentParser(description='Read TSV file and draw markers on input images', \
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-o', '--output-file', nargs=1, default=output_filename, \
                    help='output multipage TIFF file ([basename]_marked.tif if not specified)')

parser.add_argument('-f', '--marker-file', nargs=1, default=marker_filename, \
                    help='name of TSV file (read [basename].txt if not specified)')
parser.add_argument('-z', '--marker-size', nargs=1, type=int, default=[marker.marker_size], \
                    help='marker size to draw')
parser.add_argument('-w', '--marker-width', nargs=1, type=int, default=[marker.marker_width], \
                    help='marker line width to draw')
parser.add_argument('-c', '--marker-colors', nargs=4, type=str, default=marker.marker_colors, \
                    metavar=('NEW', 'CONT', 'END', 'REDUN'), \
                    help='marker colors for new, tracked, disappearing, and redundant spots')
parser.add_argument('-r', '--rainbow-colors', action='store_true', default=marker.marker_rainbow, \
                    help='use rainbow colors to distinguish each tracking')

parser.add_argument('-R', '--mark-regression', action='store_true', default=marker.mark_regression, \
                    help='regression mode (draw spots that can be tracked from the first frame)')
parser.add_argument('-E', '--force-mark-emerge', action='store_true', default=marker.force_mark_emerge, \
                    help='force marking emerging spots in regression mode')

parser.add_argument('-M', '--mask-image', nargs=1, default = filter.mask_image_filename, \
                    help='read masking image to omit unnecessary area')

parser.add_argument('-i', '--invert-image', action='store_true', default=marker.invert_image, \
                    help='invert the LUT of output image')

parser.add_argument('input_file', nargs=1, default=input_filename, \
                    help='input (multipage) TIFF file to draw markers')

args = parser.parse_args()

# set arguments
input_filename = args.input_file[0]
marker.marker_size = args.marker_size[0]
marker.marker_width = args.marker_width[0]
marker.marker_colors = args.marker_colors
marker.marker_rainbow = args.rainbow_colors
marker.invert_image = args.invert_image
marker.mark_regression = args.mark_regression
marker.force_mark_emerge = args.force_mark_emerge

if args.marker_file is None:
    marker_filename = os.path.join(os.path.dirname(input_filename),\
                      os.path.splitext(os.path.basename(input_filename))[0] + '.txt')
else:
    marker_filename = args.marker_file[0]
    fileext = os.path.splitext(os.path.basename(marker_filename))[1].lower()
    if (fileext == '.stk') or (fileext == '.tif'):
        marker_filename = os.path.splitext(os.path.basename(marker_filename))[0] + '.txt'
        print("Reading %s instead of %s." % (marker_filename, args.marker_file[0]))

if args.output_file is None:
    output_filename = os.path.splitext(os.path.basename(input_filename))[0] + '_marked.tif'
    if input_filename == output_filename:
        raise Exception('input_filename == output_filename')
else:
    output_filename = args.output_file[0]

if args.mask_image is not None:
    filter.mask_image_filename = args.mask_image[0]

# read image
orig_image = tifffile.imread(input_filename)
if len(orig_image.shape) == 2:
    orig_image = numpy.array([orig_image])

# convert image to 8-bit RGB color
image_color = marker.convert_to_color(orig_image)

# read results
print("Read spots from %s." % (marker_filename))
spot_table = pandas.read_csv(marker_filename, comment = '#', sep = '\t')

# use mask image to filter spots
if filter.mask_image_filename is not None:
    total_spots = len(spot_table)
    spot_table = filter.filter_spots_maskimage(spot_table)
    print("Filtered %d spots using a mask image: %s." % (total_spots - len(spot_table), mask_image_filename))

# mark tracking status
print("Marked %d spots on %s." % (len(spot_table), input_filename))
image_color = marker.mark_spots(image_color, spot_table)

# output multipage tiff
print("Output image file to %s." % (output_filename))
tifffile.imsave(output_filename, image_color)
