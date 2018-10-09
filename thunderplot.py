#!/usr/bin/env python

import os, platform, sys, glob, argparse, time
import pandas, numpy
from taniclass import spotplotter, spotfilter
from skimage.external import tifffile

# prepare classes
plotter = spotplotter.SpotPlotter()
filter = spotfilter.SpotFilter()

# defaults
input_filenames = None
image_size = (512, 512)
pixel_size = 80
align_spots = True
align_filename = 'align.txt'
output_filename = 'plot_%s.tif' % time.strftime("%Y-%m-%d_%H-%M-%S")
output_stackmode = None
output_stackeach = 1

# parse arguments
parser = argparse.ArgumentParser(description='make super-resolution image from thunderstorm output.', \
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('-o', '--output-file', nargs=1, default=[output_filename], \
                    help='output super-resolution tiff file')

parser.add_argument('-n', '--no-align', action='store_true', default=(align_spots is False), \
                    help='plot without alignment')
parser.add_argument('-a', '--align-file', nargs=1, default=[align_filename], \
                    help='tsv file with alignment (align.txt if not specified)')
parser.add_argument('-e', '--align-each', nargs=1, type=int, default=[plotter.align_each], \
                    help='alignment correction every X plane')

parser.add_argument('-z', '--pixel-size', nargs=1, type=int, default=[pixel_size], \
                    help='pixel size [nm] of input image (see camera settings in thunderstom)')

parser.add_argument('-X', '--image-scale', nargs=1, type=int, default=[plotter.image_scale], \
                    help='scale factor to original image')
parser.add_argument('-Z', '--image-size', nargs=2, type=int, default=image_size, \
                    metavar=('WIDTH', 'HEIGHT'), \
                    help='size of original image (read from first file if not specified)')

group = parser.add_mutually_exclusive_group()
group.add_argument('-T', '--seperate-stack', action='store_const', \
                    dest='output_stackmode', const='separate', \
                    help='output using separated stack')
group.add_argument('-U', '--cumulative-stack', action='store_const', \
                    dest='output_stackmode', const='cumulative', \
                    help='output using cumulative stack')

parser.add_argument('-E', '--stack-each', nargs=1, type=int, default=[output_stackeach], \
                    help='stack every X file')

parser.add_argument('input_file', nargs='+', default=None, \
                    help='input tsv file(s) with plotting geometries')

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
align_spots = (args.no_align is False)
align_filename = args.align_file[0]
width, height = image_size = args.image_size
pixel_size = args.pixel_size[0]
output_stackmode = args.output_stackmode
output_stackeach = args.stack_each[0]
output_filename = args.output_file[0]

plotter.align_each = args.align_each[0]
plotter.image_scale = args.image_scale[0]

# read align table
if align_spots is True:
    if os.path.isfile(align_filename) is False:
        raise Exception('alignment table (%s) does not exist' % (align_filename))
    align_table = pandas.read_table(align_filename, comment = '#')
    print("Using %s for alignment." % (align_filename))
else:
    align_table = None

# prepare output image
output_image = numpy.zeros((height * plotter.image_scale, width * plotter.image_scale), dtype=numpy.int64)
if output_stackmode is not None:
    stack_size = ((len(input_filenames) - 1) // output_stackeach) + 1
    output_stack = numpy.zeros((stack_size, \
                                height * plotter.image_scale, width * plotter.image_scale), \
                                dtype=numpy.int64)

# plot spots for each table
last_plane = 0

for index, input_filename in enumerate(input_filenames):
    # init output image for separate stack
    if output_stackmode == 'separate':
        output_image.fill(0)

    # get spots
    spot_table = pandas.read_csv(input_filename, sep='\t', comment='#')
    spot_table = spot_table.rename(columns={'frame': 'plane', 'x [nm]': 'x', 'y [nm]': 'y'})
    spot_table['plane'] = spot_table['plane'] - 1
    spot_table['x'] = spot_table['x'] / pixel_size
    spot_table['y'] = spot_table['y'] / pixel_size
    print("Total %d spots in %s." % (len(spot_table), input_filename))

    # plot
    #print(spot_table)
    output_image = plotter.plot_spots(output_image, last_plane, spot_table, align_table)

    # save into stack
    if output_stackmode is not None:
        if index % output_stackeach == 0:
            output_stack[index // output_stackeach] = output_image

    last_plane += plotter.align_each

    print("Plot %d spots from %s." % (len(spot_table), input_filename))
    print("--")

# save into last stack
if output_stackmode is not None:
    if index % output_stackeach != 0:
        output_stack[-1] = output_image


# output (multipage) tiff
desc_text = 'output by %s (Daisuke Taniguchi and Takushi Miyoshi)' % (os.path.basename(__file__))

if output_stackmode is None:
    # clip output.tif to 32bit and output
    print("Output image file to %s." % (output_filename))
    output_image_32bit = output_image.clip(0, numpy.iinfo(numpy.int32).max).astype(numpy.int32)
    tifffile.imsave(output_filename, output_image_32bit, description = desc_text)
else:
    # clip output.tif to 32bit and output
    print("Output %s stack image file to %s." % (output_stackmode, output_filename))
    output_image_32bit = output_stack.clip(0, numpy.iinfo(numpy.int32).max).astype(numpy.int32)
    tifffile.imsave(output_filename, output_image_32bit, description = desc_text)
