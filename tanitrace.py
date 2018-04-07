#!/usr/bin/env python

import os, sys, argparse, pandas, numpy
from taniclass import gaussian8, bfchaser, spotmarker
from skimage.external import tifffile

# prepare library instances
tracer = gaussian8.Gaussian8()
chaser = bfchaser.BFChaser()
marker = spotmarker.SpotMarker()

# defaults
input_filename = None
output_tsv_filename = None
output_image_filename = None
chase_spots = False
output_image = False
invert_image = False
rainbow_colors = False

# parse arguments
parser = argparse.ArgumentParser(description='trace spots using gaussian fitting.', \
                                 epilog='use "ls *.stk | foreach -process{tanitracer [options] $_.fullname}"', \
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-f', '--output-tsv-file', nargs=1, default = None, \
                    help='output tsv file name ([basename].txt if not specified)')

parser.add_argument('-l', '--laplace', nargs=1, type=float, default=[tracer.laplace], \
                    help='maximum spot diameter to filter noise')
parser.add_argument('-m', '--min-distance', nargs=1, type=int, default=[tracer.min_distance], \
                    help='pixel area to find local max (usually 1.0)')
parser.add_argument('-t', '--threshold-abs', nargs=1, type=float, default=[tracer.threshold_abs], \
                    help='threshold to find local max')

parser.add_argument('-C', '--chase-spots', action='store_true', default=chase_spots, \
                    help='chase spots before output tsv file')
parser.add_argument('-d', '--chase-distance', nargs=1, type=float, default = [chaser.chase_distance], \
                    help='maximum distance to assume as identical spots (pixel)')

parser.add_argument('-O', '--output-image', action='store_true', default=output_image, \
                    help='output image tiff')
parser.add_argument('-o', '--output-image-file', nargs=1, default = None, \
                    help='output image file name([basename]_tracer.tif if not specified)')
parser.add_argument('-z', '--marker-size', nargs=1, type=int, default=[marker.marker_size], \
                    help='marker size to plot')
parser.add_argument('-c', '--marker-colors', nargs=4, type=str, \
                    default=marker.marker_colors, metavar=('NEW', 'CONT', 'END', 'ERROR'), \
                    help='marker colors for new/continued/end spots')
parser.add_argument('-r', '--rainbow-colors', action='store_true', default=rainbow_colors, \
                    help='use rainbow colors')

parser.add_argument('-i', '--invert-image', action='store_true', default=invert_image, \
                    help='invert image LUT')

parser.add_argument('input_file', nargs=1, default=input_filename, \
                    help='input multpage-tiff file to chase spots')

args = parser.parse_args()

# set arguments
input_filename = args.input_file[0]
if args.output_tsv_file is None:
    output_tsv_filename = os.path.splitext(os.path.basename(input_filename))[0] + '.txt'
    if input_filename == output_tsv_filename:
        raise Exception('input_filename == output_tsv_filename')
else:
    output_tsv_filename = args.output_tsv_file[0]

tracer.laplace = args.laplace[0]
tracer.min_distance = args.min_distance[0]
tracer.threshold_abs = args.threshold_abs[0]

chase_spots = args.chase_spots
chaser.chase_distance = args.chase_distance[0]

marker.marker_colors = args.marker_colors
marker.marker_size = args.marker_size[0]
output_image = args.output_image
if args.output_image_file is None:
    output_image_filename = os.path.splitext(os.path.basename(input_filename))[0] + '_marked.tif'
    if input_filename == output_image_filename:
        raise Exception('input_filename == output_image_filename')
else:
    output_image_filename = args.output_image_file[0]

invert_image = args.invert_image
rainbow_colors = args.rainbow_colors

# read image
orig_image = tifffile.imread(input_filename)
if len(orig_image.shape) == 2:
    orig_image = numpy.array([orig_image])
print("Read image %s" % (input_filename))

# image clip
tracer.set_image_clip(orig_image[0])

# fitting and combine all results
results = tracer.fitting_image_stack(orig_image)
spot_counts = [len(results[results.plane == i]) for i in range(results.plane.max() + 1)]
print("Detected spots: %s" % (' '.join(map(str, spot_counts))))
print("Total %d spots detected in %d frames." % (len(results), len(orig_image)))

# chase spots
if chase_spots is True:
    results = chaser.chase_spots(results)
    print("Chaser detected %d unique spots." % (len(results.total_index.unique())))

# open tsv file and output header
output_tsv_file = open(output_tsv_filename, 'w', newline='')
tracer.output_header(output_tsv_file, input_filename, orig_image)
if chase_spots is True:
    chaser.output_header(output_tsv_file)
output_tsv_file.write('\t'.join(results.columns) + '\n')

# output result table and close
results.to_csv(output_tsv_file, columns = results.columns, \
               sep='\t', index = False, header = False, mode = 'a')
output_tsv_file.close()
print("Output tsv file to %s." % (output_tsv_filename))

# output marked image
if output_image is True:
    # prepare image of 8-bit RGB color
    image_color = marker.convert_to_color(orig_image)
    if invert_image is True:
        image_color = 255 - image_color

    # mark tracking status
    if rainbow_colors is True:
        image_color = marker.mark_rainbow_spots(image_color, results)    
    else:
        image_color = marker.mark_spots(image_color, results)

    # output multipage tiff
    tifffile.imsave(output_image_filename, image_color)
    print("Output image file to %s." % (output_image_filename))

