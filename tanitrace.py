#!/usr/bin/env python

import os, sys, argparse, numpy, matplotlib, tifffile
from taniclass import gaussian8, nnchaser, spotmarker, spotplotter, spotfilter

# prepare library instances
tracer = gaussian8.Gaussian8()
chaser = nnchaser.NNChaser()
marker = spotmarker.SpotMarker()
plotter = spotplotter.SpotPlotter()
filter = spotfilter.SpotFilter()

# defaults
input_filename = None
import_settings_filename = None
output_tsv_filename = None
output_image_filename = None
chase_spots = False
output_image = False

# parse arguments
parser = argparse.ArgumentParser(description='Detect fluorescent spots with Gaussian fitting.', \
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-T', '--output-tsv-file', nargs=1, default = None, \
                    help='output tsv file name ([basename].txt if not specified)')

# import settings
group = parser.add_mutually_exclusive_group()
group.add_argument('-R', '--rerun', action='store_true', default=False, \
                   help='import settings from [basename].txt and rerun calculation')
group.add_argument('-I', '--import-settings-file', nargs=1, default = None, \
                   help='import settings from other results (can be overwritten by options)')

# append are used to judge whether or not options are set
parser.add_argument('-m', '--min-distance', nargs=1, type=int, default=[tracer.min_distance], action='append',\
                    help='pixel area to find local max (usually use default)')
parser.add_argument('-l', '--laplace', nargs=1, type=float, default=[tracer.laplace], action='append',\
                    help='sigma of LoG filter (try near the pixel diameter of spots)')
parser.add_argument('-t', '--threshold-abs', nargs=1, type=float, default=[tracer.threshold_abs], action='append',\
                    help='threshold of Gaussian fitting')
parser.add_argument('-x', '--max-diameter', nargs=1, type=float, default=[tracer.max_diameter], action='append',\
                    help='limit the maximum diameter of spots (to avoid abnormal fitting)')
parser.add_argument('-u', '--dup-threshold', nargs=1, type=float, default=[tracer.dup_threshold], action='append',\
                    help='minimum distance to distinguish two spots (to avoid redundant detection)')

parser.add_argument('-C', '--chase-spots', action='store_true', default=chase_spots, \
                    help='chase spots using k-Nearest Neighbor algorithm')
parser.add_argument('-d', '--chase-distance', nargs=1, type=float, default = [chaser.chase_distance], action='append',\
                    help='maximum distance to assume as identical spots (pixel)')

parser.add_argument('-O', '--output-image', action='store_true', default=output_image, \
                    help='output TIFF file with markers of detected spots')
parser.add_argument('-o', '--output-image-file', nargs=1, default = None, \
                    help='output TIFF file name([basename]_marked.tif if not specified)')
parser.add_argument('-z', '--marker-size', nargs=1, type=int, default=[marker.marker_size], \
                    help='marker size to draw detected spots')
parser.add_argument('-c', '--marker-colors', nargs=4, type=str, \
                    default=marker.marker_colors, metavar=('NEW', 'CONT', 'END', 'REDUN'), \
                    help='marker colors for new, tracked, disappearing, and redundant spots')
parser.add_argument('-r', '--marker-rainbow', action='store_true', default=marker.marker_rainbow, \
                    help='use rainbow colors to distinguish each tracking')

# masking image
parser.add_argument('-M', '--mask-image', nargs=1, default = filter.mask_image_filename, \
                    help='read masking image to omit unnecessary area')

parser.add_argument('-i', '--invert-image', action='store_true', default=marker.invert_image, \
                    help='invert the LUT of output image')

parser.add_argument('input_file', nargs=1, default=input_filename, \
                    help='input (multpage) TIFF file')

args = parser.parse_args()

# set arguments
input_filename = args.input_file[0]
if args.output_tsv_file is None:
    output_tsv_filename = os.path.splitext(os.path.basename(input_filename))[0] + '.txt'
    if input_filename == output_tsv_filename:
        raise Exception('input_filename == output_tsv_filename')
else:
    output_tsv_filename = args.output_tsv_file[0]

# load options from the previous result
if args.rerun is True:
    args.import_settings_file = os.path.splitext(os.path.basename(input_filename))[0] + '.txt'

if args.import_settings_file is not None:
    import_settings_filename = args.import_settings_file
    print("Importing settings: %s (can be overwritten by options)" % (import_settings_filename))
    fileext = os.path.splitext(os.path.basename(import_settings_filename))[1].lower()
    if (fileext == '.stk') or (fileext == '.tif'):
        import_settings_filename = os.path.splitext(os.path.basename(import_settings_filename))[0] + '.txt'
        print("Reading %s instead of %s." % (import_settings_filename, args.import_settings_file[0]))

    params = plotter.read_image_params(import_settings_filename)
    # pretend as if options are set
    for key in params:
        if hasattr(args, key):
            if len(getattr(args, key)) > 1:
                print("Parameter %s was overwritten by options as %f" % (key, list(matplotlib.cbook.flatten(getattr(args, key)))[-1]))
            else:
                getattr(args, key).append(params[key])
                print("Read parameter %s as %f" % (key, params[key]))
        if key == 'chase_distance':
            chase_spots = True
            print("Spot chaser ON.")

tracer.laplace = list(matplotlib.cbook.flatten(args.laplace))[-1]
tracer.min_distance = list(matplotlib.cbook.flatten(args.min_distance))[-1]
tracer.threshold_abs = list(matplotlib.cbook.flatten(args.threshold_abs))[-1]
tracer.max_diameter = list(matplotlib.cbook.flatten(args.max_diameter))[-1]
tracer.dup_threshold = list(matplotlib.cbook.flatten(args.dup_threshold))[-1]

chase_spots = (args.chase_spots | chase_spots)
chaser.chase_distance = list(matplotlib.cbook.flatten(args.chase_distance))[-1]

marker.marker_colors = args.marker_colors
marker.marker_size = args.marker_size[0]
marker.marker_rainbow = args.marker_rainbow
marker.invert_image = args.invert_image

if args.mask_image is not None:
    filter.mask_image_filename = args.mask_image[0]

output_image = args.output_image
if args.output_image_file is None:
    output_image_filename = os.path.splitext(os.path.basename(input_filename))[0] + '_marked.tif'
    if input_filename == output_image_filename:
        raise Exception('input_filename == output_image_filename')
else:
    output_image_filename = args.output_image_file[0]

# read image
orig_image = tifffile.imread(input_filename)
if len(orig_image.shape) == 2:
    orig_image = numpy.array([orig_image])
print("Read image %s" % (input_filename))

# image clip
tracer.set_image_clip(orig_image[0])

# fitting and combine all results
results = tracer.fitting_image_stack(orig_image)
if len(results) == 0:
    print("No spots detected. Quit.")
    sys.exit()

spot_counts = [len(results[results.plane == i]) for i in range(results.plane.max() + 1)]
print("Detected spots: %s" % (' '.join(map(str, spot_counts))))
print("Total %d spots detected in %d frames." % (len(results), len(orig_image)))

# chase spots
if chase_spots is True:
    results = chaser.chase_spots(results)
    print("Chaser detected %d unique spots." % (len(results.total_index.unique())))

# use mask image to filter spots
if filter.mask_image_filename is not None:
    total_spots = len(results)
    results = filter.filter_spots_maskimage(results)
    print("Filtered %d spots using a mask image: %s." % (total_spots - len(results), filter.mask_image_filename))

# open tsv file and output header
output_tsv_file = open(output_tsv_filename, 'w', newline='')
tracer.output_header(output_tsv_file, input_filename, orig_image)
if chase_spots is True:
    chaser.output_header(output_tsv_file)
if filter.mask_image_filename is not None:
    filter.output_header(output_tsv_file)
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

    # mark tracking status
    image_color = marker.mark_spots(image_color, results)

    # output multipage tiff
    tifffile.imwrite(output_image_filename, image_color)
    print("Output image file to %s." % (output_image_filename))

# spacer to next processing
print(".")
