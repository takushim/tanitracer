#!/usr/bin/env python

import os, datetime
import numpy, pandas
import tifffile
#from PIL import Image

class CirisPlot:
    def __init__(self):
        self.width = 512
        self.height = 512
        self.intensity = 0.0
        self.scale = 4
        #self.input_files = ['IRIS_Localization%d.txt'% i for i in range(1,5)]
        self.input_files = ['IRIS_Localization.txt']
        self.output_file = 'iris_cython_%s.tif' % datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.shift_file = 'ShiftXY.txt'
        self.shift_each = 500
        self.drift_x = 0.0
        self.drift_y = 0.0
        self.start_plane = 0
        self.plane_each = 20000
        self.cumulative = False
        self.makestack = False

    def plot(self):
        # read shiftXY data
        if self.shift_file is not None:
            #shift_data = numpy.loadtxt(self.shift_file, delimiter="\t", skiprows=True)
            shift_data = pandas.read_csv(self.shift_file, sep='\t')
            shift_x = numpy.array(shift_data.shiftX - self.drift_x, dtype=numpy.float)
            shift_y = numpy.array(shift_data.shiftY - self.drift_y, dtype=numpy.float)

        # stack for cumulative image
        if (self.cumulative == True) or (self.makestack == True):
            image_stack = numpy.zeros((len(self.input_files), self.height * self.scale, self.width * self.scale), \
                                  dtype=numpy.uint32)
        else:
            image_stack = numpy.zeros((1, self.height * self.scale, self.width * self.scale), \
                                  dtype=numpy.uint32)

        # array for plotting
        image_array = numpy.zeros((self.height * self.scale, self.width * self.scale), dtype=numpy.uint32)
        
        # record starting
        start_time = datetime.datetime.now()
        
        # plot wavetracer data
        for file_index, input_file in enumerate(self.input_files):
            # record starting time of this file
            file_start_time = datetime.datetime.now()
        
            # open position file
            f = open(input_file, 'r')
            
            # process header for WaveTracer
            line = f.readline()
            if line is 'Width\tHeight\tPlanes count\tPoints count':
                # skip next line for wavetracer
                f.readline()
                # find centroid_x and centroid_y
                line = f.readline()
                columns = line.split()
                col_plane = columns.index('Plane')
                col_x = columns.index('CentroidX(pix)')
                col_y = columns.index('CentroidY(pix)')
                col_intensity = columns.index('Intensity')
                approx_count = int(os.path.getsize(input_file) / 128)
            else:
                # process table header for other good csv
                columns = line.split()
                col_plane = columns.index('Plane')
                col_x = columns.index('X')
                col_y = columns.index('Y')
                col_intensity = columns.index('Intensity')
                approx_count = int(os.path.getsize(input_file) / 50)
                

            print "Start: ", input_file, file_start_time.strftime("%Y-%m-%d_%H-%M-%S")
            print "The number of points is approximately: ", approx_count
            
            skipped_points = 0

            # plot points
            for index, line in enumerate(f):
                data = line.split()
                plane, orig_x, orig_y, intensity = \
                    int(data[col_plane]), float(data[col_x]), float(data[col_y]), float(data[col_intensity])
                
                if intensity < self.intensity:
                    skipped_points += 1
                    continue
                
                plane = self.start_plane + self.plane_each * file_index + plane
                if self.shift_file is None:
                    diff_x, diff_y = (0.0, 0.0)
                else:
                    slice = (plane - 1) // self.shift_each
                    diff_x, diff_y = shift_x[slice], shift_y[slice]
                
                plot_x = int(numpy.round((orig_x - diff_x) * self.scale))
                plot_y = int(numpy.round((orig_y - diff_y) * self.scale))
                #plot_x = min(max(0, plot_x), self.width * self.scale - 1)
                #plot_y = min(max(0, plot_y), self.height * self.scale - 1)
                if (0 <= plot_x) and (plot_x <= self.width * self.scale - 1):
                    if (0 <= plot_y) and (plot_y <= self.height * self.scale - 1):
                        image_array[plot_y, plot_x] = min(image_array[plot_y, plot_x], 0xfffe) + 1
                #print (orig_x, orig_y, plot_x, plot_y, self.width, self.height)
                
                if index % 100000 == 0: print input_file, index, "of", approx_count
            
            # save image_array for cumulative tiff
            if self.cumulative == True:
                image_stack[file_index] = image_array
            elif self.makestack == True:
                image_stack[file_index] = image_array
                image_array = numpy.zeros((self.height * self.scale, self.width * self.scale), dtype=numpy.uint32)
            else:
                image_stack[0] = image_array

            # end loop
            f.close()
            file_end_time = datetime.datetime.now()
            print "End: ", input_file, file_end_time.strftime("%Y-%m-%d_%H-%M-%S")
            print "Processing time: ", (file_end_time - file_start_time)
            print "Skipped points: ", skipped_points, " of ", approx_count
            print ""
        
        end_time = datetime.datetime.now()
        print "Total processing time: ", (end_time - start_time)

        # prepare image
        if image_stack.max() > 65535:
            print("Warning: pixel value > uint16 ")
            image_stack = image_stack.clip(0, 65535)
            
        tifffile.imsave(self.output_file, image_stack.astype(numpy.uint16))
        #image = Image.frombytes('I', (self.width * self.scale, self.height * self.scale), image_array)
        #image.save(self.output_file)

