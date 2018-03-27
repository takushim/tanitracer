#!/usr/bin/env python

import numpy, tifffile, pandas, time
import scipy.ndimage as ndimage
import scipy.stats as stats
from skimage.feature import peak_local_max

class Gaussian8:
    def __init__ (self):
        self.laplace = 3.0 # Diameter of Spots
        self.min_distance = 1 # Pixel area (int) to find local max (usually 1)
        self.threshold_abs = 0.004 # Threshold to find local max
        self.columns = ['total_index', 'plane', 'index', 'x', 'y', 'intensity', 'fit_error']
        self.image_clip_min = 0.0
        self.image_clip_max = numpy.iinfo(numpy.int32).max
                
    def output_header (self, output_file, input_filename, image_array):
        planes = image_array.shape[0]
        if len(image_array.shape) == 2:
            planes = 1
        output_file.write('## Traced by TaniTracer at %s.\n' % (time.ctime()))
        output_file.write('#   file = %s; plane = %d; width = %d; height = %d\n' %\
                          (input_filename, planes, image_array.shape[2], image_array.shape[1]))
        output_file.write('#   laplace = %f; min_distance = %d; threshold_abs = %f\n' %\
                          (self.laplace, self.min_distance, self.threshold_abs))
        output_file.write('#   image_clip_min = %f; image_clip_max = %f\n' %\
                          (self.image_clip_min, self.image_clip_max))
    
    def set_image_clip (self, image_array):
        self.set_image_clip_percentile(image_array)

    def set_image_clip_sigma (self, image_array):
        median = numpy.median(image_array)
        sigma = numpy.std(image_array)
        self.image_clip_min = 0.0
        self.image_clip_max = median + 10 * sigma

    def set_image_clip_iqr (self, image_array):
        q1 = stats.scoreatpercentile(image_array, 25)
        q3 = stats.scoreatpercentile(image_array, 75)
        iqr = q3 - q1
        self.image_clip_min = q1 - 20 * iqr
        self.image_clip_max = q3 + 20 * iqr
    
    def set_image_clip_percentile (self, image_array):
        self.image_clip_min = stats.scoreatpercentile(image_array, 0.1)
        self.image_clip_max = stats.scoreatpercentile(image_array, 99.9)
    
    def fitting_image_array (self, input_image):
        image_orig = numpy.array(input_image)
        image_array = numpy.array(input_image, 'f')
        
        # Remove hot spots
        image_array = image_array.clip(self.image_clip_min, self.image_clip_max)
        image_array = - (image_array - numpy.max(image_array)) / numpy.ptp(image_array)
        
        # Clear objects larger than self.laplace. If no points exist, this filter may give abnormal result.
        image_array = ndimage.gaussian_laplace(image_array, self.laplace)
        
        # Find local max at 1-pixel resolution (order: [y, x])
        xy = peak_local_max(image_array, min_distance = self.min_distance,\
                            threshold_abs = self.threshold_abs, exclude_border = True)

        # Calculate subpixel correction
        c10 = ( - numpy.log(image_array[xy[:,0] - 1, xy[:,1] - 1]) - numpy.log(image_array[xy[:,0], xy[:,1] - 1]) \
                - numpy.log(image_array[xy[:,0] + 1, xy[:,1] - 1]) + numpy.log(image_array[xy[:,0] - 1, xy[:,1] + 1]) \
                + numpy.log(image_array[xy[:,0], xy[:,1] + 1]) + numpy.log(image_array[xy[:,0] + 1, xy[:,1] + 1]) ) / 6
        c01 = ( - numpy.log(image_array[xy[:,0] - 1, xy[:,1] - 1]) - numpy.log(image_array[xy[:,0] - 1, xy[:,1]]) \
                - numpy.log(image_array[xy[:,0] - 1, xy[:,1] + 1]) + numpy.log(image_array[xy[:,0] + 1, xy[:,1] - 1]) \
                + numpy.log(image_array[xy[:,0] + 1, xy[:,1]]) + numpy.log(image_array[xy[:,0] + 1, xy[:,1] + 1]) ) / 6
        c20 = (   numpy.log(image_array[xy[:,0] - 1, xy[:,1] - 1]) + numpy.log(image_array[xy[:,0], xy[:,1] - 1]) \
                + numpy.log(image_array[xy[:,0] + 1, xy[:,1] - 1]) - 2 * numpy.log(image_array[xy[:,0] - 1,xy[:,1]]) \
                - 2 * numpy.log(image_array[xy[:,0], xy[:,1]]) - 2 * numpy.log(image_array[xy[:,0] + 1, xy[:,1]]) \
                + numpy.log(image_array[xy[:,0] - 1, xy[:,1] + 1]) + numpy.log(image_array[xy[:,0], xy[:,1] + 1]) \
                + numpy.log(image_array[xy[:,0] + 1, xy[:,1] + 1]) ) / 6
        c02 = (   numpy.log(image_array[xy[:,0] - 1, xy[:,1] - 1]) + numpy.log(image_array[xy[:,0] - 1,xy[:,1]]) \
                + numpy.log(image_array[xy[:,0] - 1, xy[:,1] + 1]) - 2 * numpy.log(image_array[xy[:,0], xy[:,1] - 1]) \
                - 2 * numpy.log(image_array[xy[:,0], xy[:,1]]) - 2 * numpy.log(image_array[xy[:,0], xy[:,1] + 1]) \
                + numpy.log(image_array[xy[:,0] + 1, xy[:,1] - 1]) + numpy.log(image_array[xy[:,0] + 1,xy[:,1]]) \
                + numpy.log(image_array[xy[:,0] + 1, xy[:,1] + 1]) ) / 6
        c00 = ( - numpy.log(image_array[xy[:,0] - 1, xy[:,1] - 1]) + 2 * numpy.log(image_array[xy[:,0], xy[:,1] - 1]) \
                - numpy.log(image_array[xy[:,0] + 1, xy[:,1] - 1]) + 2 * numpy.log(image_array[xy[:,0] - 1,xy[:,1]]) \
                + 5 * numpy.log(image_array[xy[:,0], xy[:,1]]) + 2 * numpy.log(image_array[xy[:,0] + 1, xy[:,1]]) \
                - numpy.log(image_array[xy[:,0] - 1, xy[:,1] + 1]) + 2 * numpy.log(image_array[xy[:,0], xy[:,1] + 1]) \
                - numpy.log(image_array[xy[:,0] + 1, xy[:,1] + 1]) ) / 9

        fit_error = ( c00 - c10 + c20 - c01 + c02 - numpy.log(image_array[xy[:,0] - 1, xy[:,1] - 1]) )**2 \
            + ( c00 - c10 + c20 - numpy.log(image_array[xy[:,0], xy[:,1] - 1]) )**2 \
            + ( c00 - c10 + c20 + c01 + c02 - numpy.log(image_array[xy[:,0] + 1, xy[:,1] - 1]) )**2 \
            + ( c00 - c01 + c02 - numpy.log(image_array[xy[:,0] - 1, xy[:,1]]) )**2 \
            + ( c00 - numpy.log(image_array[xy[:,0], xy[:,1]]) )**2 \
            + ( c00 + c01 + c02 - numpy.log(image_array[xy[:,0] + 1, xy[:,1]]) )**2 \
            + ( c00 + c10 + c20 - c01 + c02 - numpy.log(image_array[xy[:,0] - 1, xy[:,1] + 1]) )**2 \
            + ( c00 + c10 + c20 - numpy.log(image_array[xy[:,0], xy[:,1] + 1]) )**2 \
            + ( c00 + c10 + c20 + c01 + c02 - numpy.log(image_array[xy[:,0] + 1, xy[:,1] + 1]) )**2

        dx = - 0.5 * (c10/c20)
        dy = - 0.5 * (c01/c02)

        # Add subpixel correction
        x = xy[:,1] + dx
        y = xy[:,0] + dy

        # Make Pandas dataframe
        result = pandas.DataFrame({ \
                'total_index' : numpy.arange(len(xy)), \
                'plane' : 0, \
                'index' : numpy.arange(len(xy)), \
                'x' : x, \
                'y' : y, \
                'intensity' : image_orig[xy[:,0], xy[:,1]], \
                'fit_error' : fit_error})
        
        # Drop if x/y = Nan
        total_count = len(result)
        result = result.dropna().reset_index(drop=True)
        if total_count - len(result) > 0:
            print("Dropped %d spots due to NaN." % (total_count - len(result)))
        
        return result[self.columns]
        

