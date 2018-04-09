#!/usr/bin/env python

import sys, numpy, pandas, time
import scipy.ndimage as ndimage
import scipy.stats as stats
from skimage.feature import peak_local_max

class Gaussian8:
    def __init__ (self):
        self.laplace = 3.0 # Diameter of Spots
        self.min_distance = 1 # Pixel area (int) to find local max (usually 1)
        self.threshold_abs = 0.006 # Threshold to find local max
        self.columns = ['total_index', 'plane', 'index', 'x', 'y', 'diameter', 'intensity', 'fit_error']
        self.image_clip_min = 0.0
        self.image_clip_max = numpy.iinfo(numpy.int32).max
                
    def output_header (self, output_file, input_filename, image_array):
        planes = image_array.shape[0]
        if len(image_array.shape) == 2:
            planes = 1
        output_file.write('## Traced by TaniTracer at %s.\n' % (time.ctime()))
        output_file.write('#   file = r\'%s\'; total_planes = %d; width = %d; height = %d\n' %\
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
    
    def gaussian_fitting (self, float_image):
        # Find local max at 1-pixel resolution (order: [y, x])
        xy = peak_local_max(float_image, min_distance = self.min_distance,\
                            threshold_abs = self.threshold_abs, exclude_border = True)

        # Calculate subpixel correction (x = xy[:,1], y = xy[:,0])
        c10 = ( - numpy.log(float_image[xy[:,0] - 1, xy[:,1] - 1]) - numpy.log(float_image[xy[:,0], xy[:,1] - 1]) \
                - numpy.log(float_image[xy[:,0] + 1, xy[:,1] - 1]) + numpy.log(float_image[xy[:,0] - 1, xy[:,1] + 1]) \
                + numpy.log(float_image[xy[:,0], xy[:,1] + 1]) + numpy.log(float_image[xy[:,0] + 1, xy[:,1] + 1]) ) / 6
        c01 = ( - numpy.log(float_image[xy[:,0] - 1, xy[:,1] - 1]) - numpy.log(float_image[xy[:,0] - 1, xy[:,1]]) \
                - numpy.log(float_image[xy[:,0] - 1, xy[:,1] + 1]) + numpy.log(float_image[xy[:,0] + 1, xy[:,1] - 1]) \
                + numpy.log(float_image[xy[:,0] + 1, xy[:,1]]) + numpy.log(float_image[xy[:,0] + 1, xy[:,1] + 1]) ) / 6
        c20 = (   numpy.log(float_image[xy[:,0] - 1, xy[:,1] - 1]) + numpy.log(float_image[xy[:,0], xy[:,1] - 1]) \
                + numpy.log(float_image[xy[:,0] + 1, xy[:,1] - 1]) - 2 * numpy.log(float_image[xy[:,0] - 1,xy[:,1]]) \
                - 2 * numpy.log(float_image[xy[:,0], xy[:,1]]) - 2 * numpy.log(float_image[xy[:,0] + 1, xy[:,1]]) \
                + numpy.log(float_image[xy[:,0] - 1, xy[:,1] + 1]) + numpy.log(float_image[xy[:,0], xy[:,1] + 1]) \
                + numpy.log(float_image[xy[:,0] + 1, xy[:,1] + 1]) ) / 6
        c02 = (   numpy.log(float_image[xy[:,0] - 1, xy[:,1] - 1]) + numpy.log(float_image[xy[:,0] - 1,xy[:,1]]) \
                + numpy.log(float_image[xy[:,0] - 1, xy[:,1] + 1]) - 2 * numpy.log(float_image[xy[:,0], xy[:,1] - 1]) \
                - 2 * numpy.log(float_image[xy[:,0], xy[:,1]]) - 2 * numpy.log(float_image[xy[:,0], xy[:,1] + 1]) \
                + numpy.log(float_image[xy[:,0] + 1, xy[:,1] - 1]) + numpy.log(float_image[xy[:,0] + 1,xy[:,1]]) \
                + numpy.log(float_image[xy[:,0] + 1, xy[:,1] + 1]) ) / 6
        c00 = ( - numpy.log(float_image[xy[:,0] - 1, xy[:,1] - 1]) + 2 * numpy.log(float_image[xy[:,0], xy[:,1] - 1]) \
                - numpy.log(float_image[xy[:,0] + 1, xy[:,1] - 1]) + 2 * numpy.log(float_image[xy[:,0] - 1,xy[:,1]]) \
                + 5 * numpy.log(float_image[xy[:,0], xy[:,1]]) + 2 * numpy.log(float_image[xy[:,0] + 1, xy[:,1]]) \
                - numpy.log(float_image[xy[:,0] - 1, xy[:,1] + 1]) + 2 * numpy.log(float_image[xy[:,0], xy[:,1] + 1]) \
                - numpy.log(float_image[xy[:,0] + 1, xy[:,1] + 1]) ) / 9

        fit_error = ( c00 - c10 + c20 - c01 + c02 - numpy.log(float_image[xy[:,0] - 1, xy[:,1] - 1]) )**2 \
            + ( c00 - c10 + c20 - numpy.log(float_image[xy[:,0], xy[:,1] - 1]) )**2 \
            + ( c00 - c10 + c20 + c01 + c02 - numpy.log(float_image[xy[:,0] + 1, xy[:,1] - 1]) )**2 \
            + ( c00 - c01 + c02 - numpy.log(float_image[xy[:,0] - 1, xy[:,1]]) )**2 \
            + ( c00 - numpy.log(float_image[xy[:,0], xy[:,1]]) )**2 \
            + ( c00 + c01 + c02 - numpy.log(float_image[xy[:,0] + 1, xy[:,1]]) )**2 \
            + ( c00 + c10 + c20 - c01 + c02 - numpy.log(float_image[xy[:,0] - 1, xy[:,1] + 1]) )**2 \
            + ( c00 + c10 + c20 - numpy.log(float_image[xy[:,0], xy[:,1] + 1]) )**2 \
            + ( c00 + c10 + c20 + c01 + c02 - numpy.log(float_image[xy[:,0] + 1, xy[:,1] + 1]) )**2
        
        x = xy[:,1] - 0.5 * (c10/c20)
        y = xy[:,0] - 0.5 * (c01/c02)
        
        total_spots = len(xy)
        
        indexes = numpy.ones(len(xy), dtype=numpy.bool)
        indexes = indexes & (x >= 0) & (x <= float_image.shape[1])
        indexes = indexes & (y >= 0) & (y <= float_image.shape[0])
        
        x = x[indexes]
        y = y[indexes]
        fit_error = fit_error[indexes]
        
        if total_spots - len(x) > 0:
            print("Dropped %d of %d spots due to NaN or Inf values." % (total_spots - len(x), total_spots))
        
        return x, y, fit_error

    def calculate_diameter (self, input_image, int_x, int_y):
    
        return numpy.zeros(len(int_x))
        #c20 = (   numpy.log(input_image[int_y - 1, int_x - 1]) + numpy.log(input_image[int_y, int_x - 1]) \
        #        + numpy.log(input_image[int_y + 1, int_x - 1]) - 2 * numpy.log(input_image[int_y - 1,int_x]) \
        #        - 2 * numpy.log(input_image[int_y, int_x]) - 2 * numpy.log(input_image[int_y + 1, int_x]) \
        #        + numpy.log(input_image[int_y - 1, int_x + 1]) + numpy.log(input_image[int_y, int_x + 1]) \
        #        + numpy.log(input_image[int_y + 1, int_x + 1]) ) / 6
        #c02 = (   numpy.log(input_image[int_y - 1, int_x - 1]) + numpy.log(input_image[int_y - 1,int_x]) \
        #        + numpy.log(input_image[int_y - 1, int_x + 1]) - 2 * numpy.log(input_image[int_y, int_x - 1]) \
        #        - 2 * numpy.log(input_image[int_y, int_x]) - 2 * numpy.log(input_image[int_y, int_x + 1]) \
        #        + numpy.log(input_image[int_y + 1, int_x - 1]) + numpy.log(input_image[int_y + 1,int_x]) \
        #        + numpy.log(input_image[int_y + 1, int_x + 1]) ) / 6

        #sigma_x = numpy.sqrt(- 2 * c20)
        #sigma_y = numpy.sqrt(- 2 * c02)
        
        #return (2 * numpy.sqrt((sigma_x * sigma_x + sigma_y * sigma_y) / 2))

    def clip_array (self, float_array):
        return float_array.clip(self.image_clip_min, self.image_clip_max)

    def standardize_and_filter_image (self, float_image):
        float_image = - (float_image - numpy.max(float_image)) / numpy.ptp(float_image)
        return ndimage.gaussian_laplace(float_image, self.laplace)
    
    def convert_to_pandas (self, plane, index, x, y, diameter, intensity, error):
        length = max(len(x), len(y), len(intensity), len(error))
        result = pandas.DataFrame({'total_index' : numpy.arange(length), 'plane' : plane, \
                                   'index' : index, 'x' : x, 'y' : y, 'diameter' : diameter, \
                                   'intensity' : intensity, 'fit_error' : error}, \
                                   columns = self.columns)
         
        return result

    def fitting_image_array (self, input_image):
        # get float image anf filter
        float_image = numpy.array(input_image, 'f')
        float_image = self.clip_array(float_image)
        float_image = self.standardize_and_filter_image(float_image)
        
        # fitting
        x, y, error = self.gaussian_fitting(float_image)
        intensity = input_image[y.astype(numpy.int), x.astype(numpy.int)]
        diameter = self.calculate_diameter(input_image, x.astype(numpy.int), y.astype(numpy.int))

        # Make Pandas dataframe
        result = self.convert_to_pandas(0, numpy.arange(len(x)), x, y, diameter, intensity, error)

        return result
        
    def fitting_image_stack (self, input_stack):
        # get float image anf filter
        float_stack = numpy.array(input_stack, 'f')
        float_stack = self.clip_array(float_stack)
        
        # arrays to store results
        stored_plane = numpy.array([], dtype=numpy.int)
        stored_index = numpy.array([], dtype=numpy.int)
        stored_x = numpy.array([], dtype=numpy.float)
        stored_y = numpy.array([], dtype=numpy.float)
        stored_error = numpy.array([], dtype=numpy.float)
        stored_intensity = numpy.array([], dtype=numpy.int)
        stored_diameter = numpy.array([], dtype=numpy.float)

        for index in range(len(input_stack)):
            # filter and fitting            
            float_stack[index] = self.standardize_and_filter_image(float_stack[index])
            x, y, error = self.gaussian_fitting(float_stack[index])
            intensity = input_stack[index, y.astype(numpy.int), x.astype(numpy.int)]
            diameter = self.calculate_diameter(input_stack[index], x.astype(numpy.int), y.astype(numpy.int))
            
            # append to arrays
            stored_plane = numpy.append(stored_plane, numpy.full(len(x), index))
            stored_index = numpy.append(stored_index, numpy.arange(len(x)))
            stored_x = numpy.append(stored_x, x)
            stored_y = numpy.append(stored_y, y)
            stored_error = numpy.append(stored_error, error)
            stored_intensity = numpy.append(stored_intensity, intensity)
            stored_diameter = numpy.append(stored_diameter, diameter)

        spot_table = self.convert_to_pandas(stored_plane, stored_index, \
                                            stored_x, stored_y, stored_diameter, \
                                            stored_intensity, stored_error)
        spot_table['total_index'] = numpy.arange(len(spot_table))
        return spot_table

