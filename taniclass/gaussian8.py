#!/usr/bin/env python

import os, sys, numpy, pandas, time
import scipy.ndimage as ndimage
import scipy.stats as stats
from skimage.feature import peak_local_max

class Gaussian8:
    def __init__ (self):
        self.laplace = 2.0 # Diameter of Spots
        self.min_distance = 1 # Pixel area (int) to find local max (usually 1)
        self.threshold_abs = 0.006 # Threshold to find local max
        self.max_diameter = 10.0
        self.columns = ['total_index', 'plane', 'index', 'x', 'y', 'diameter', 'intensity', 'fit_error']
        self.image_clip_min = 0.0
        self.image_clip_max = numpy.iinfo(numpy.int32).max
                
    def output_header (self, output_file, input_filename, image_array):
        filename = os.path.basename(input_filename)
        planes = image_array.shape[0]
        if len(image_array.shape) == 2:
            planes = 1
            
        #params = {'input_file': filename, 'total_planes': planes, \
        #          'width': image_array.shape[2], 'height': image_array.shape[1], \
        #          'laplace': self.laplace. 'min_distance': self.min_distance, \
        #          'threshold_abs': self.threshold_abs, \
        #          'image_clip_min': self.image_clip_min, 'image_clip_max': self.image_clip_max}
        
        output_file.write('## Traced by TaniTracer at %s for %s\n' % (time.ctime(), filename))
        output_file.write('#   total_planes = %d; width = %d; height = %d\n' %\
                          (planes, image_array.shape[2], image_array.shape[1]))
        output_file.write('#   laplace = %f; min_distance = %d; threshold_abs = %f\n' %\
                          (self.laplace, self.min_distance, self.threshold_abs))
        output_file.write('#   image_clip_min = %f; image_clip_max = %f\n' %\
                          (self.image_clip_min, self.image_clip_max))
    
    def set_image_clip (self, image_array):
        self.image_clip_min = stats.scoreatpercentile(image_array, 0.1)
        self.image_clip_max = stats.scoreatpercentile(image_array, 99.9)
    
    def gaussian_fitting (self, input_image, float_image):
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
        diameter = 2 * numpy.sqrt(- (0.5/c20 + 0.5/c02) / 2)
        intensity = input_image[xy[:,0], xy[:,1]]
        
        total_spots = len(xy)
        indexes = numpy.ones(len(xy), dtype=numpy.bool)
        indexes = indexes & (x >= 0) & (x <= float_image.shape[1])
        indexes = indexes & (y >= 0) & (y <= float_image.shape[0])
        drop_by_nan = total_spots - numpy.sum(indexes)
        last_spots = numpy.sum(indexes)
        
        indexes = indexes & ((0.5 * (c10/c20)) < 1)
        indexes = indexes & ((0.5 * (c01/c02)) < 1)
        drop_by_shift = last_spots - numpy.sum(indexes)
        last_spots = numpy.sum(indexes)
        
        indexes = indexes & (diameter <= self.max_diameter)
        drop_by_diameter = last_spots - numpy.sum(indexes)
        last_spots = numpy.sum(indexes)
        
        x = x[indexes]
        y = y[indexes]
        fit_error = fit_error[indexes]
        diameter = diameter[indexes]
        intensity = intensity[indexes]
        
        if total_spots - last_spots > 0:
            print("Dropped %d of %d spots (nan: %d, shift: %d, diameter: %d)." % \
                  (total_spots - last_spots, total_spots, drop_by_nan, drop_by_shift, drop_by_diameter))

        return {'x': x, 'y': y, 'fit_error': fit_error, 'diameter': diameter, 'intensity': intensity}

    def clip_array (self, float_array):
        return float_array.clip(self.image_clip_min, self.image_clip_max)

    def standardize_and_filter_image (self, float_image):
        float_image = - (float_image - numpy.max(float_image)) / numpy.ptp(float_image)
        return ndimage.gaussian_laplace(float_image, self.laplace)
    
    def convert_to_pandas (self, result):
        length = max([len(item) for item in result.values()])
        result.update({'total_index' : numpy.arange(length)})
        return pandas.DataFrame(result, columns = self.columns)

    def fitting_image_array (self, input_image):
        # get float image anf filter
        float_image = numpy.array(input_image, 'f')
        float_image = self.clip_array(float_image)
        float_image = self.standardize_and_filter_image(float_image)
        
        # fitting
        result = self.gaussian_fitting(input_image, float_image)

        # Make Pandas dataframe
        length = max([len(item) for item in result.values()])
        result.update({'plane': numpy.full(length, 0), 'index': numpy.arange(length)})
        spot_table = self.convert_to_pandas(result)

        return spot_table
        
    def fitting_image_stack (self, input_stack):
        # get float image anf filter
        float_stack = numpy.array(input_stack, 'f')
        float_stack = self.clip_array(float_stack)
        
        # arrays to store results
        result_array = []

        for index in range(len(input_stack)):
            # filter and fitting            
            float_stack[index] = self.standardize_and_filter_image(float_stack[index])
            result = self.gaussian_fitting(input_stack[index], float_stack[index])
            
            # add plane and index
            length = max([len(item) for item in result.values()])
            result.update({'plane': numpy.full(length, index), 'index': numpy.arange(length)})
            
            # append to arrays
            result_array.append(result)

        # accumulate result
        result_concat = {}
        for key in result_array[0].keys():
            result_concat[key] = numpy.concatenate([result[key] for result in result_array])

        # make pandas table
        spot_table = self.convert_to_pandas(result_concat)
        spot_table['total_index'] = numpy.arange(len(spot_table))
        return spot_table

