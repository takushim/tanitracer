#!/usr/bin/env python

import sys, numpy, pandas, time
from scipy.spatial import distance

class BFChaser:
    def __init__ (self):
        self.chase_distance = 3.5
        
    def output_header (self, output_file):
        output_file.write('## Chased by TaniChaser at %s\n' % (time.ctime()))
        output_file.write('#   chase_distance = %f\n' % (self.chase_distance))
    
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
            
            # prepare index to insert numpy.inf
            dist_index = numpy.ones(dist_matrix.shape, dtype = numpy.bool)

            # leave only minimum values
            dist_index[:,:] = True
            min_index = dist_matrix.argmin(axis = 0)
            dist_index[min_index, range(len(min_index))] = False
            dist_matrix[dist_index] = numpy.inf
            
            dist_index[:,:] = True
            min_index = dist_matrix.argmin(axis = 1)
            dist_index[range(len(min_index)), min_index] = False
            dist_matrix[dist_index] = numpy.inf

            # leave dists smaller than chasing distance
            dist_matrix[dist_matrix > self.chase_distance] = numpy.inf

            # make indexes
            chased_spots = numpy.where(dist_matrix != numpy.inf)
            chased_dists = dist_matrix[chased_spots]
            current_index_list = current_spots.total_index.tolist()
            current_indexes = [current_index_list[i] for i in chased_spots[0]]
            next_index_list = next_spots.total_index.tolist()
            next_indexes = [next_index_list[i] for i in chased_spots[1]]
            
            # append chased distances
            #print(chased_spots)
            work_table.loc[work_table.total_index.isin(next_indexes), 'distance'] = chased_dists

            # overwrite total index
            work_table['total_index'] = work_table.total_index.replace(dict(zip(next_indexes, current_indexes)))
                    
        # sort table and return
        return work_table.sort_values(by = ['total_index', 'plane']).reset_index(drop=True)

