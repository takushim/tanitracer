#!/usr/bin/env python

import sys, numpy, pandas

class SpotPlotter:
    def __init__ (self):
        self.image_scale = 4
        self.align_each = 500

    def read_image_size (self, input_filename):
        params = self.read_image_params(input_filename)
        return int(params['width']), int(params['height'])

    def read_image_params (self, input_filename):
        params = {}
        with open(input_filename, 'r') as spot_file:
            for line in spot_file:
                if line.startswith('#') is False:
                    break
                line = line[1:].strip()
                exec(line, {}, params)

        return params

    def plot_spots (self, last_image, last_plane, spot_table, align_table):
        # prepare working array
        work_image = last_image.copy()

        # make spots dataframe
        spots = spot_table[['plane', 'x', 'y']].copy().reset_index(drop=True)

        # scale and alignment
        if align_table is not None:
            spots['align_index'] = ((spots['plane'] + last_plane) // self.align_each)
            spots = pandas.merge(spots, align_table, left_on='align_index', right_on='align_plane', how='left')
            spots['plot_x'] = ((spots['x']  - spots['align_x']) * self.image_scale).astype(int)
            spots['plot_y'] = ((spots['y']  - spots['align_y']) * self.image_scale).astype(int)
        else:
            spots['plot_x'] = (spots['x'] * self.image_scale).astype(int)
            spots['plot_y'] = (spots['y'] * self.image_scale).astype(int)

        # drop inappropriate spots
        height, width = work_image.shape
        spots = spots[(0 <= spots['plot_x']) & (spots['plot_x'] < width) & \
                      (0 <= spots['plot_y']) & (spots['plot_y'] < height)].reset_index(drop=True)

        # plot spots
        work_array = numpy.zeros(work_image.shape, dtype=numpy.int32)
        plot_x = spots.plot_x.values
        plot_y = spots.plot_y.values
        numpy.add.at(work_array, (plot_y, plot_x), 1)

        # combine with work_image
        work_image = work_image + work_array

        return work_image
