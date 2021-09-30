"""
This file contains some functions to perform basic tests of the TSP bot.
"""

import numpy as np
import time
import TravellingSalesman as TS

#######################################################
# Global parameters
#######################################################
# number of random instances to check
m = 10
# number of locations in each random instance
n = 10
# error tolerance when comparing lengths of the optimal paths
err = 10e-6
#######################################################

def generate_random_locs( n, center = [0, 0] ):
	"""
	Generates a set of random locations in 2D centered around a specific point.
	"""
	rng = np.random.default_rng()
	locs = [ [rng.standard_normal() + center[0], rng.standard_normal() + center[1]] for j in range(n) ]

	return locs


def compare_paths(path1, path2):
	"""
	Checks whether two paths are equivalent, i.e. either the same or the one is the reversed variant of the other.
	"""
	path2_rev = path2.copy()
	path2_rev.reverse()
	if path1 == path2 or path1 == path2_rev:
		return True
	else:
		return False

def check_instance(label, locs, verbose, save_image):
	"""
	Given a set of locations, it solves the TSP using two methods and compares the results.
	"""
	n = len(locs)
	dist = TS.generate_distance_matrix(locs)
	# generate a list of locations to visit
	locs_to_visit = list(range(1, n))
			
	# solve the TSP using dynamical programming and measure the time elapsed
	t0 = time.time()
	tour = TS.Route(dist, 0, 0, locs_to_visit)
	time_elapsed_dp = time.time() - t0

	# solve the TSP using brute-force and measure the time elapsed		
	t0 = time.time()
	best_length_bf, best_path_bf = TS.brute_force(dist, 0, 0, locs_to_visit)
	time_elapsed_bf = time.time() - t0
	
	# if required plot and save the path to an external file
	if save_image:
		# makes a dictionary of the two optimal paths
		paths = {}
		paths['dp'] = tour.best_path
		paths['bf'] = best_path_bf
		
		for x in ( 'dp', 'bf' ):
			img = TS.plot_path( locs, paths[x] )
			filename = 'images/test{}_{}.png'.format(label, x)
			with open(filename, 'wb') as file:
				file.write( img.getvalue() )
	
	if verbose:
		print('Length (dynamic programming): {}'.format(tour.best_length))
		print('Length (brute-force): {}'.format(best_length_bf))
		print('Time elapsed (dynamic programming): {}'.format(time_elapsed_dp))
		print('Time elapsed (brute-force): {}'.format(time_elapsed_bf))

	if np.abs( tour.best_length - best_length_bf ) > err:
		print('Error: the two approaches give different lengths.')

	if not compare_paths(tour.best_path, best_path_bf):
		print('Warning: the two approaches give inequivalent routes.')

def perform_random_checks(m = 10, n = 10, verbose = False, save_image = False):
	"""
	Generates m instances of the TSP with n locations and solves them using both the dynamical approach and brute-force.
	Prints an error if in some instance the length of the shortest path obtained from the two approaches differs by more than err.
	Prints a warning if the identified paths are not equivalent (this could in principle happen but should be very uncommon).
	"""
	for j in range(1, m + 1):
		print('Instance {}:'.format(j))
		# generate a set of random locations and compute the corresponding distance matrix
		locs = generate_random_locs(n)
		check_instance(j, locs, verbose, save_image)

# perform random checks as specified by the global parameters
perform_random_checks(m, n, verbose = True, save_image = True)

# for this set of location two inequivalent optimal paths exist
locs = [ [-1, 0], [1, 0], [0, -1], [0, 0.2], [0, -0.2] ]
check_instance( str(m + 2), locs, verbose = True, save_image = True)
