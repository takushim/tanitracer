#!/usr/bin/env python

import os, platform, sys, glob, argparse, time
import pandas, numpy
from taniclass import spotplotter
from skimage.external import tifffile

# prepare classes
plotter = spotplotter.SpotPlotter()

# defaults
input_filenames = None
image_size = (512, 512)
plane_each = 20000
align_spots = True
align_filename = 'ShiftXY.txt'
output_filename1 = 'plot1.tif'
output_filename2 = 'plot2.tif'

# parse arguments
parser = argparse.ArgumentParser(description='make split super-resolution image for frc using WT files', \
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('-n', '--no-align', action='store_true', default=(align_spots is False), \
                    help='plot without alignment')
parser.add_argument('-a', '--align-file', nargs=1, default=[align_filename], \
                    help='tsv file with alignment (align.txt if not specified)')
parser.add_argument('-e', '--align-each', nargs=1, type=int, default=[plotter.align_each], \
                    help='alignment correction every X plane')

parser.add_argument('-P', '--plane-each', nargs=1, type=int, default=[plane_each], \
                    help='number of planes in each file')

parser.add_argument('-X', '--image-scale', nargs=1, type=int, default=[plotter.image_scale], \
                    help='scale factor to original image')
parser.add_argument('-Z', '--image-size', nargs=2, type=int, default=image_size, \
                    metavar=('WIDTH', 'HEIGHT'), \
                    help='size of original image (read from first file if not specified)')

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
align_spots = (args.no_align is False)
align_filename = args.align_file[0]
image_size = args.image_size
plane_each = args.plane_each[0]
plotter.align_each = args.align_each[0]
plotter.image_scale = args.image_scale[0]

# read align table
if align_spots is True:
    align_table = pandas.read_table(align_filename, comment = '#')
    align_table = align_table.rename(columns = {'slice': 'align_plane', 'shiftX': 'align_x', 'shiftY': 'align_y'})
    align_table['align_plane'] = align_table['align_plane'] - 1
    print("Using %s for alignment." % (align_filename))
else:
    align_table = None

# prepare output image
height, width = image_size
output_image1 = numpy.zeros((height * plotter.image_scale, width * plotter.image_scale), dtype=numpy.int64)
output_image2 = numpy.zeros((height * plotter.image_scale, width * plotter.image_scale), dtype=numpy.int64)

# plot spots for each table
last_plane = 0

for index, input_filename in enumerate(input_filenames):
    # get parameters and spots
    spot_table = pandas.read_csv(input_filename, sep='\t', comment='#', skiprows=2)
    spot_table = spot_table.rename(columns={'Plane': 'plane', 'CentroidX(pix)': 'x', 'CentroidY(pix)': 'y'})
    spot_table['plane'] = spot_table['plane'] - 1
    print("Total %d spots in %s." % (len(spot_table), input_filename))

    # split table randomly
    spot_table['key'] = numpy.random.randint(2, size=len(spot_table))
    spot_table1 = spot_table[spot_table.key == 0].reset_index(drop=True)
    spot_table2 = spot_table[spot_table.key == 1].reset_index(drop=True)
    print("Total %d split into (%d, %d)" % (len(spot_table), len(spot_table1), len(spot_table2)))

    # plot
    output_image1 = plotter.plot_spots(output_image1, last_plane, spot_table1, align_table)
    output_image2 = plotter.plot_spots(output_image2, last_plane, spot_table2, align_table)

    last_plane += plane_each

    print("Plot %d spots from %s." % (len(spot_table), input_filename))
    print("--")

# output (multipage) tiff
desc_text = 'output by %s (Daisuke Taniguchi and Takushi Miyoshi)' % (os.path.basename(__file__))

# clip output.tif to 32bit and output
print("Output image file to %s." % (output_filename1))
output_image_32bit = output_image1.clip(0, numpy.iinfo(numpy.int32).max).astype(numpy.int32)
tifffile.imsave(output_filename1, output_image_32bit, description = desc_text)

print("Output image file to %s." % (output_filename2))
output_image_32bit = output_image2.clip(0, numpy.iinfo(numpy.int32).max).astype(numpy.int32)
tifffile.imsave(output_filename2, output_image_32bit, description = desc_text)
