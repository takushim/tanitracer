#!/usr/bin/env python

import sys, numpy, pandas, time
from scipy.spatial import distance

class BFChaser:
    def __init__ (self):
        self.chase_distance = 2.0
        
    def output_header (self, output_file):
        output_file.write('# Chased by TaniChaser at %s.\n' % (time.ctime()))
        output_file.write('#   chase_distance = %f\n' % (self.chase_distance,))
    
    def chase_spots (self, spot_table):
        # copy pandas dataframe for working, and append total index
        work_table = spot_table.copy()
        columns = work_table.columns.tolist()
        work_table['distance'] = numpy.zeros(len(work_table))
        work_table = work_table[columns + ['distance']]
        
        # compare two sequencial frames, and re-assign total index number
        for index in range(max(work_table.plane)):
            current_spots = work_table[work_table.plane == index]
            next_spots = work_table[work_table.plane == index + 1]
            
            # calculate distance matrix [curr, next]
            dist_matrix = distance.cdist(current_spots[['x', 'y']].values, next_spots[['x', 'y']].values)
            
            # leave only minimum values
            min_index = dist_matrix.argmin(axis = 0)
            dist_index = numpy.ones(dist_matrix.shape, dtype = numpy.bool)
            dist_index[min_index, range(len(min_index))] = False
            dist_matrix[dist_index] = numpy.inf

            min_index = dist_matrix.argmin(axis = 1)
            dist_index = numpy.ones(dist_matrix.shape, dtype = numpy.bool)
            dist_index[range(len(min_index)), min_index] = False
            dist_matrix[dist_index] = numpy.inf
            
            # leave dists smaller than chasing distance
            dist_matrix[dist_matrix > self.chase_distance] = numpy.inf
            
            # make indexes
            chased_spots = numpy.where(dist_matrix != numpy.inf)
            current_index = current_spots.iloc[chased_spots[0]].total_index
            next_index = next_spots.iloc[chased_spots[1]].total_index
            chased_dists = dist_matrix[chased_spots]
            
            #print("Plane %d: %d of %d spots chased." % (index, len(chased_spots[0]), len(current_spots)))
            
            # overwrite total index
            total_index_list = work_table.total_index.copy()
            total_index_list[next_index] = total_index_list[current_index]
            work_table.total_index = total_index_list
            
            # append chased distances
            dists_list = work_table.distance.copy()
            dists_list[next_index] = chased_dists
            work_table.distance = dists_list
        
        # sort table and return
        return work_table.sort_values(by = ['total_index', 'plane']).reset_index(drop=True)

