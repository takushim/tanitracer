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

import os, platform, sys, glob, argparse
import numpy, pandas, tifffile
from taniclass import akaze
from PIL import Image

# prepare aligner
aligner = akaze.Akaze()

# defaults
input_filenames = None
output_tsv_filename = 'align.txt'
output_image = False
output_image_filename = None
reference_image_filename = None

parser = argparse.ArgumentParser(description='Calculate sample drift using A-KAZE feature matching', \
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-f', '--output-tsv-file', nargs=1, default = [output_tsv_filename], \
                    help='output TSV file name (align.txt if not specified)')

parser.add_argument('-r', '--reference-image', nargs=1, default = [reference_image_filename], \
                    help='use an external reference image')

parser.add_argument('-O', '--output-image', action='store_true', default=output_image, \
                    help='output image after drift correction')
parser.add_argument('-o', '--output-image-file', nargs=1, default = None, \
                    help='output image file name ([basename]_akaze.tif if not specified)')

parser.add_argument('-i', '--invert-image', action='store_true', default=aligner.invert_image, \
                    help='invert the LUT of output image')

parser.add_argument('input_file', nargs='+', default=None, \
                    help='series of multipage TIFF file(s) to align')
args = parser.parse_args()

# collect input filenames
if (platform.system() == "Windows"):
    input_filenames = []
    for pattern in args.input_file:
        input_filenames.extend(sorted(glob.glob(pattern)))
else:
    input_filenames = args.input_file

# set arguments
aligner.invert_image = args.invert_image
output_tsv_file = args.output_tsv_file[0]
reference_image_filename = args.reference_image[0]

output_image = args.output_image
if args.output_image_file is None:
    output_image_filename = os.path.splitext(os.path.basename(input_filenames[0]))[0] + '_akaze.tif'
    if output_image_filename in args.input_file:
        raise Exception('input_filename == output_filename')
else:
    output_image_filename = args.output_image_file[0]

# read input image(s)
image_list = []
for input_filename in input_filenames:
    images = tifffile.imread(input_filename)
    if len(images.shape) == 2:
        image_list += [images]
    else:
        image_list += [images[i] for i in range(len(images))]

orig_images = numpy.asarray(image_list)

# read reference image
reference_image = None
if reference_image_filename is not None:
    reference_image = tifffile.imread(reference_image_filename)
    if len(reference_image.shape) > 2:
        reference_image = reference_image[0]

# alignment
results = aligner.calculate_alignments(orig_images, reference_image)

# open tsv file and write header
output_tsv_file = open(output_tsv_filename, 'w', newline='')
aligner.output_header(output_tsv_file, input_filenames[0], reference_image_filename)
output_tsv_file.write('\t'.join(results.columns) + '\n')

# output result and close
results.to_csv(output_tsv_file, columns = results.columns, \
               sep='\t', index = False, header = False, mode = 'a')
output_tsv_file.close()
print("Output alignment tsv file to %s." % (output_tsv_filename))

# output image
if output_image is True:
    images_uint8 = aligner.convert_to_uint8(orig_images)

    output_image_array = numpy.zeros(images_uint8.shape, dtype=numpy.uint8)

    for row, align in results.iterrows():
        plane = results.align_plane[row]
        if plane not in range(len(images_uint8)):
            print("Skip plane %d due to out-of-range." % (results.plane[row]))
            continue

        image = Image.fromarray(images_uint8[plane])
        image = image.rotate(0, translate=(int(-align.align_x), int(-align.align_y)))
        output_image_array[plane] = numpy.asarray(image, dtype=numpy.uint8)

    # output multipage tiff
    print("Output image file to %s." % (output_image_filename))
    tifffile.imwrite(output_image_filename, output_image_array)
