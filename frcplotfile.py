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
image_size = None
align_spots = True
align_filename = 'align.txt'
output_prefix = 'plot'
consolidate_spots = False
divide = 8
lifetime_range = [1, 0]

# parse arguments
parser = argparse.ArgumentParser(description='make split super-resolution image for frc using WT files', \
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('-o', '--output-prefix', nargs=1, default=[output_prefix], \
                    help='prefix of output tif file [prefix]_1.tif [prefix]_2.tif')

parser.add_argument('-l', '--lifetime-range', nargs=2, type=int, default=lifetime_range, \
                    metavar=('MIN', 'MAX'), \
                    help='range of spot lifetime (set MAX = 0 for numpy.inf)')

parser.add_argument('-n', '--no-align', action='store_true', default=(align_spots is False), \
                    help='plot without alignment')
parser.add_argument('-a', '--align-file', nargs=1, default=[align_filename], \
                    help='tsv file with alignment (align.txt if not specified)')
parser.add_argument('-e', '--align-each', nargs=1, type=int, default=[plotter.align_each], \
                    help='alignment correction every X plane')
                    
parser.add_argument('-c', '--consolidate-spots', action='store_true', default=consolidate_spots, \
                    help='collapse spots')

parser.add_argument('-d', '--divide', nargs=1, type=int, default=[divide], \
                    help='span of dividing (if 8, dividev into 4 + 4)')

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

# devide input files
divide = args.divide[0]
max_range = len(input_filenames)
indexes = numpy.arange(max_range)[(numpy.arange(max_range) % divide) < (divide / 2)]
input_filenames1 = numpy.array(input_filenames)[indexes]
indexes = numpy.arange(max_range)[(numpy.arange(max_range) % divide) >= (divide / 2)]
input_filenames2 = numpy.array(input_filenames)[indexes]
#print("input_filenames1", input_filenames1)
#print("input_filenames2", input_filenames2)

# make output filename
output_filename1 = args.output_prefix[0] + '_1.tif'
output_filename2 = args.output_prefix[0] + '_2.tif'

# set arguments
align_spots = (args.no_align is False)
align_filename = args.align_file[0]
image_size = args.image_size
plotter.align_each = args.align_each[0]
plotter.image_scale = args.image_scale[0]
consolidate_spots = args.consolidate_spots
lifetime_range = args.lifetime_range

# read align table
if align_spots is True:
    align_table = pandas.read_table(align_filename, comment = '#')
    print("Using %s for alignment." % (align_filename))
else:
    align_table = None

# read first table and determine size
if image_size is None:
    width, height = plotter.read_image_size(input_filenames[0])
else:
    width, height = image_size[0], image_size[1]

# prepare output image
output_image1 = numpy.zeros((height * plotter.image_scale, width * plotter.image_scale), dtype=numpy.int64)
output_image2 = numpy.zeros((height * plotter.image_scale, width * plotter.image_scale), dtype=numpy.int64)

# plot spots for each table
last_plane = 0

for index, input_filename in enumerate(input_filenames):
    # get parameters and spots
    params = plotter.read_image_params(input_filename)
    spot_table = pandas.read_csv(input_filename, sep='\t', comment='#')
    print("Total %d spots in %s." % (len(spot_table), input_filename))
    
    # filter using lifetime of spots
    if lifetime_range != [1, 0]:
        total_spots = len(spot_table)
        filter.lifetime_min = lifetime_range[0]
        filter.lifetime_max = numpy.inf if lifetime_range[1] == 0 else lifetime_range[1]
        spot_table = filter.filter_spots_lifetime(spot_table)
        if lifetime_range[1] == 0:
            print("Filtered %d of %d spots (%d %f)." % \
                    (total_spots - len(spot_table), total_spots, filter.lifetime_min, filter.lifetime_max))
        else:
            print("Filtered %d of %d spots (%d %d)." % \
                    (total_spots - len(spot_table), total_spots, filter.lifetime_min, filter.lifetime_max))
    # average spots
    if consolidate_spots is True:
        total_spots = len(spot_table)
        spot_table = filter.keep_first_spots(spot_table)
        print("Consolidated to %d of %d spots." % (len(spot_table), total_spots))
    
    # split table randomly
    #spot_table['key'] = numpy.random.randint(2, size=len(spot_table))
    #spot_table1 = spot_table[spot_table.key == 0].reset_index(drop=True)
    #spot_table2 = spot_table[spot_table.key == 1].reset_index(drop=True)
    #print("Total %d split into (%d, %d)" % (len(spot_table), len(spot_table1), len(spot_table2)))
    
    # plot
    if input_filename in input_filenames1:
        output_image1 = plotter.plot_spots(output_image1, last_plane, spot_table, align_table)
        print("1: Plot %d spots (%d planes) from %s." % (len(spot_table), params['total_planes'], input_filename))
    else:
        output_image2 = plotter.plot_spots(output_image2, last_plane, spot_table, align_table)
        print("2: Plot %d spots (%d planes) from %s." % (len(spot_table), params['total_planes'], input_filename))
    
    last_plane += params['total_planes']
    
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

