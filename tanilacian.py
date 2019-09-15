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

import os, sys, argparse, numpy
from skimage.external import tifffile
from taniclass import gaussian8

# classes
tracer = gaussian8.Gaussian8()

# default values
input_filename = None
output_filename = None

# parse arguments
parser = argparse.ArgumentParser(description='make LoG-filtered image stack.', \
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-o', '--output-file', nargs=1, default=output_filename, \
                    help='output multipage-tiff file ([basename]_log.tif if not specified)')

parser.add_argument('-l', '--laplace', nargs=1, type=float, default=tracer.laplace, \
                    help='maximum spot diameter to filter noise')

parser.add_argument('input_file', nargs=1, default=input_filename, \
                    help='input file (multipage-tiff file to apply filter')

args = parser.parse_args()

# set arguments
tracer.laplace = args.laplace[0]
input_filename = args.input_file[0]

if args.output_file is None:
    #output_filename = os.path.splitext(os.path.basename(input_filename))[0] + ("_l%.2f.tif" % tracer.laplace)
    output_filename = os.path.splitext(os.path.basename(input_filename))[0] + '_log.tif'
    if input_filename == output_filename:
        raise Exception('input_filename == output_filename')
else:
    output_filename = args.output_file[0]

# read image
orig_images = tifffile.imread(input_filename)
if len(orig_images.shape) == 2:
    orig_images = numpy.array([orig_images])

# apply log filter
float_images = numpy.array(orig_images, 'f')
tracer.set_image_clip(orig_images)
float_images = tracer.clip_array(float_images)
for index in range(len(float_images)):
    float_images[index] = tracer.standardize_and_filter_image(float_images[index])

# prepare pseudo-color palette
palette = numpy.zeros((256, 3), dtype=numpy.uint8)
for i in range(256):
    palette[i, 0], palette[i, 1], palette[i, 2] = i, i, i

# prepare image of 8-bit RGB color
float_max = numpy.max(float_images)
float_min = numpy.min(float_images)
uint8_images = (255.0 * (float_images - float_min) / (float_max - float_min)).astype(numpy.uint8)

output_images = numpy.zeros((orig_images.shape + (3,)), dtype = numpy.uint8)
output_images[:, :, :] = palette[uint8_images[:, :, :]]

# output image
tifffile.imsave(output_filename, output_images)
