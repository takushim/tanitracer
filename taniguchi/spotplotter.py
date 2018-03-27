#!/usr/bin/env python

import os, sys, datetime
import numpy, pandas
import tifffile

class SpotPlotter:
    def __init__ (self):
        self.orig_width = None
        self.orig_height = None
        self.image_scale = 4
        self.align_each = 500
        
    def find_image_size (self, input_filename):
        locals = {}
        with open(input_filename, 'r') as spot_file:
            for line in spot_file:
                if line.startswith('#') is False:
                    break
                line = line[1:].strip()
                exec(line, {}, locals)
        
        return int(locals['width']), int(locals['height'])

    def plot_spots (self, spot_table, image_array):
        pass
