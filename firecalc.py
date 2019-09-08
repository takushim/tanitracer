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

import os, platform, sys, argparse
import numpy
import matplotlib.pyplot as pyplot
from taniclass import firefrc
from skimage.external import tifffile

# prepare resolver
resolver = firefrc.FireFRC()

# defaults
input_filename1 = None
input_filename2 = None
mask_image_filename = None
output_graph_filename = 'firefrc.tif'

parser = argparse.ArgumentParser(description='Calculate FRC between 2 images', \
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('-o', '--output-graph', nargs=1, default = [output_graph_filename], \
                    help='output graph file name (firefrc.tif if not specified)')

parser.add_argument('-m', '--mask-image', nargs=1, default = [mask_image_filename], \
                    help='mask image file name')

parser.add_argument('input_file', nargs=2, default=None, \
                    help='input SQUARE single-page tiff files (image1, image2)')
args = parser.parse_args()

input_filename1 = args.input_file[0]
input_filename2 = args.input_file[1]
mask_image_filename = args.mask_image[0]
output_graph_filename = args.output_graph[0]

image1 = tifffile.imread(input_filename1)
image2 = tifffile.imread(input_filename2)

# prepare masking
# masking array for fire_array
if mask_image_filename is not None:
    # read masking image
    mask_image = tifffile.imread(mask_image_filename)
    mask_image = mask_image.astype(numpy.bool).astype(numpy.uint8)
    # mask image
    image1 = image1 * mask_image
    image2 = image2 * mask_image

sf, fsc = resolver.fourier_spin_correlation(image1, image2)

smooth_fsc = resolver.smoothing_fsc(sf, fsc)

sf_fix17 = resolver.intersection_threshold(sf, smooth_fsc)
resolutions = 2.0 / sf_fix17
print("resolution (px): ", resolutions)

pyplot.plot(sf, fsc, label = 'fsc')
pyplot.plot(sf, smooth_fsc, label = 'sm_fsc')
pyplot.xlim(0, 1.0)
pyplot.ylim(0, 1.2)
pyplot.vlines(sf_fix17, 0, 1.2)
pyplot.hlines(0.1427, 0, 1)
pyplot.xlabel('Spatial Frequency')

pyplot.savefig(output_graph_filename)
pyplot.show()
