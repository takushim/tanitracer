#!/usr/bin/env python

import sys, numpy, pandas, datetime

class DriftSift:
    def __init__ (self):
        self.columns = ['plane', 'x', 'y', 'error']
        
    def output_header (self, output_file):
        output_file.write('# Chased by TaniTracer at %s.\n' % (input_filename, datetime.now().ctime()))
        output_file.write('# chase_distance = %f\n' % (chaser.chase_distance,))
    
    def output_columns (self, output_file, spot_table)    
        output_file.write('\t'.join(self.get_columns_name()) + '\n')
        
