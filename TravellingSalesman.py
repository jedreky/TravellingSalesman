"""
This file contains functions and classes used to compute the shortest path and plot it.
"""

import datetime
import io
import itertools
import matplotlib.pyplot as plt
import numpy as np
import re

#######################################################
# Global variables
#######################################################
# dpi value used for saving images
dpi = 100
#######################################################
# Short functions
#######################################################
def get_timestamp():
	"""
	Returns the current timestamp.
	"""
	timestamp = datetime.datetime.now()
	return timestamp.strftime('%H:%M:%S, %d.%m.%Y')

def log(str):
	"""
	Prints a timestamped message.
	"""
	print( get_timestamp() + ': ' + str )

def get_current_IP():
	"""
	Returns the current external IP address.
	"""
	result = requests.get('https://api.ipify.org')
	return result.text

def get_time_string(time_elapsed):
	"""
	Returns a human-readable string containing the computation time.
	"""
	if time_elapsed < 0.001:
		time_str = 'less than 0.001'
	else:
		time_str = '{:.3f}'.format(time_elapsed)

	return time_str		
#######################################################
# TSP-related functions
#######################################################
def convert_to_float(s):
	"""
	Converts a string to float.
	"""
	try:
		ret = float(s)
	except ValueError:
		ret = False

	return ret

def generate_id(start, locs):
	"""
	Generates string id of a path.
	"""
	return str(start) + ',' + str(locs)

def extract_locations(string):
	"""
	Extracts locations from a string.
	"""
	locs = []
	# find all square brackets
	matches = re.findall('\[.+?,.+?\]', string)

	# iterate over the matches and see if they correspond to valid locations
	for match in matches:
		s0, s1 = re.split(',', match[1: -1], 1)
		x = convert_to_float(s0)
		y = convert_to_float(s1)

		if isinstance(x, float) and isinstance(y, float):
			locs.append( [x, y] )

	return locs

def generate_distance_matrix(locs):
	"""
	Given location coordinates generates the distance matrix.
	"""
	n = len(locs)
	# initialise an empty matrix
	distance_matrix = np.zeros( [n, n] )
	
	# iterate over the entries of the matrix
	for j in range(n):
		for k in range(j + 1, n):
			v = np.array( locs[j] ) - np.array( locs[k] )
			distance_matrix[j, k] = np.sqrt( np.dot(v, v) )

	# fill up the other half of the matrix
	distance_matrix = distance_matrix + np.transpose(distance_matrix)
	return distance_matrix

def generate_TSP_instance(locs):
	"""
	Generates the distance matrix and the list of locations to visit.
	"""
	n = len(locs)
	dist = generate_distance_matrix(locs)
	locs_to_visit = list(range(1, n))
	return dist, locs_to_visit

def compute_length(dist, path):
	"""
	Computes the length of a given path.
	"""
	length = 0

	for j in range(len(path) - 1):
		length += dist[path[j], path[j + 1]]

	return length

def brute_force(dist, start, end, locs_to_visit):
	"""
	Finds the shortest path from start to end while visiting locs_to_visit
	using the brute-force approach.
	"""
	perms = itertools.permutations( locs_to_visit )
	best_length = None
	
	# iterate over all permutations
	for perm in perms:
		path = [ start ] + list(perm) + [ end ]
		length = compute_length(dist, path)
		
		# if better that the current best solution, update
		if best_length == None or length < best_length:
			best_length = length
			best_path = path

	return best_length, best_path

def plot_path(locs, path, for_Twitter = True, img_info = None):
	"""
	Plots a path through locations (to make a closed loop the first and last
	locations should be the same).
	"""
	# convert the path and the locations into numpy arrays
	path = np.array( [ locs[j] for j in path ] )
	locs_array = np.array(locs)
	if for_Twitter:
		# create a new figure
		fig, ax = plt.subplots( figsize = (16, 8) )
		# plot the path and the locations
		ax.plot( path[:, 0], path[:, 1])
		ax.scatter( locs_array[:, 0], locs_array[:, 1], color = 'red' )
		# save the plot to a binary stream
		img = io.BytesIO()
		fig.savefig( img, format = 'png', dpi = dpi )
		plt.close(fig)
	else:
		fig, ax = plt.subplots( figsize = ( img_info['width']/dpi, img_info['height']/dpi ), tight_layout = {'pad': 0} )
		ax.axis('off')
		background = plt.imread('static/' + img_info['file'])
		back_img = ax.imshow(background)
		ax.plot( path[:, 0], path[:, 1])
		ax.scatter( locs_array[:, 0], locs_array[:, 1], color = 'red' )

		img = io.BytesIO()
		fig.savefig( img, format = 'png', dpi = dpi )
		plt.close(fig)

	return img
#######################################################
# Class definition
#######################################################
# This class is used to store information about routes and in particular
# it is used to recursively investigate shorter (children) routes.
class Route:
	# standard constructor
	# takes: distance matrix, start and end points, locations to be visited
	# and a dictionary of routes to be filled
	def __init__(self, dist, start, end, locs_to_visit, routes = None):
		# initialise variables
		self.start = start
		self.end = end
		self.locs_to_visit = locs_to_visit
		self.parents = []
		self.children = []
		self.id = generate_id(start, locs_to_visit)

		# if no dictionary passed, create one
		if routes == None:
			routes = {}

		# add route to the dictionary
		routes[self.id] = self

		# if the route is non-trivial, generate child routes
		if len(locs_to_visit) >= 2:
			self.path_exists = False
			
			# iterate over the next location
			for j in locs_to_visit:
				# set parameters of the child route
				child_start = j
				child_locs_to_visit = locs_to_visit.copy()
				child_locs_to_visit.remove(j)
				child_route_id = generate_id(child_start, child_locs_to_visit)

				# if such a route exists, link it, if not create it
				if child_route_id in routes.keys():
					child_route = routes[ child_route_id ]
				else:
					child_route = Route(dist, child_start, self.end, child_locs_to_visit, routes)

				# add parent/child relations
				child_route.add_parent( self )
				self.add_child( child_route )
				
				# if there is a complete path for the child route, we can use it
				if child_route.path_exists:
					new_length = dist[ self.start, j ] + child_route.best_length

					if (not self.path_exists) or (self.path_exists and self.best_length > new_length):
						self.best_length = new_length
						self.best_path = [self.start] + child_route.best_path
						self.path_exists = True

		elif len(locs_to_visit) == 1:
			self.best_length = dist[ self.start, locs_to_visit[0] ] + dist[ locs_to_visit[0], self.end ]
			self.best_path = [ self.start ] + locs_to_visit  + [ self.end ]
			self.path_exists = True

	# a method to add a parent route
	def add_parent(self, parent):
		self.parents.append(parent)

	# a method to add a child route
	def add_child(self, child):
		self.children.append(child)

	# a method to print a route
	def print_route(self):
		print('\nStart: {}, Locs: {}, End: {}'.format(self.start, self.locs_to_visit, self.end))

		if self.path_exists:
			print('Best length: {}'.format(self.best_length))
			print('Best path: {}'.format(self.best_path))
