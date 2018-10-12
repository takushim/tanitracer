#!/usr/bin/env python

import os, platform, sys, glob, argparse
import numpy, pandas
from taniext import poc
from taniclass import alignsift
from PIL import Image
from skimage.external import tifffile

# prepare aligner (used for image processing only)
aligner = alignsift.AlignSift()

# defaults
input_filenames = None
output_tsv_filename = 'align.txt'
output_image = False
output_image_filename = None
reference_image_filename = None
invert_image = False

parser = argparse.ArgumentParser(description='Calculate alignment using POC algorithm', \
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-f', '--output-tsv-file', nargs=1, default = [output_tsv_filename], \
                    help='output tsv file name (alignment.txt if not specified)')

parser.add_argument('-r', '--reference-image', nargs=1, default = [reference_image_filename], \
                    help='reference image file name (first plane is used)')

parser.add_argument('-O', '--output-image', action='store_true', default=output_image, \
                    help='output image tiff')
parser.add_argument('-o', '--output-image-file', nargs=1, default = None, \
                    help='output image file name([basename]_poc.tif if not specified)')

parser.add_argument('-i', '--invert-image', action='store_true', default=invert_image, \
                    help='invert image LUT')

parser.add_argument('input_file', nargs='+', default=None, \
                    help='input multpage-tiff file(s) to align')
args = parser.parse_args()

# collect input filenames
if (platform.system() == "Windows"):
    input_filenames = []
    for pattern in args.input_file:
        input_filenames.extend(sorted(glob.glob(pattern)))
else:
    input_filenames = args.input_file

# set arguments
output_tsv_file = args.output_tsv_file[0]
invert_image = args.invert_image
reference_image_filename = args.reference_image[0]

output_image = args.output_image
if args.output_image_file is None:
    output_image_filename = os.path.splitext(os.path.basename(input_filenames[0]))[0] + '_poc.tif'
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
if reference_image_filename is not None:
    reference_image = tifffile.imread(reference_image_filename)
    if len(reference_image.shape) > 2:
        reference_image = reference_image[0]
else:
    reference_image = orig_images[0]

# array for results
move_x = numpy.zeros(len(orig_images))
move_y = numpy.zeros(len(orig_images))
for index in range(len(orig_images)):
    corr, move_y[index], move_x[index] = poc.poc(reference_image, orig_images[index])
    print("Plane %d, dislocation = (%f, %f)." % (index, move_x[index], move_y[index]))

# make pandas dataframe
results = pandas.DataFrame({'align_plane' : numpy.arange(len(orig_images)), \
                            'align_x' : move_x, \
                            'align_y' : move_y})

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
    # make 8bit image (required for output)
    images_uint8 = aligner.convert_to_uint8(orig_images)
    if invert_image is True:
        images_uint8 = 255 - images_uint8

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
    tifffile.imsave(output_image_filename, output_image_array)
