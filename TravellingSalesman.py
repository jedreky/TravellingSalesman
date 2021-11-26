"""
This file contains all the functions and classes used by the TSP bot.
"""

import datetime
import io
import itertools
#import json
import matplotlib.pyplot as plt
import numpy as np
#import pymongo
import re
#import requests
import time
#import TwitterAPI

#######################################################
# Global variables
#######################################################
# minimal and maximal number of locations
n_min = 4
n_max = 12
# id of my personal Twitter account
user_id = '1390298589360844800'
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
# MongoDB functions
#######################################################
def get_client():
	"""
	Returns a MongoClient.
	"""
	with open('mongo_keys.json', 'r') as json_file:
		mongo_keys = json.load(json_file)
		client = pymongo.MongoClient( username = mongo_keys['user'], password = mongo_keys['password'] )
		return client
#######################################################
# TwitterAPI functions
#######################################################
# get a TwitterAPI object
def get_twitter_api():
	"""
	Returns a TwitterAPI object.
	"""
	with open('twitter_keys.json', 'r') as json_file:
		twitter_keys = json.load(json_file)
		api = TwitterAPI.TwitterAPI( twitter_keys['consumer_key'], twitter_keys['consumer_secret'], twitter_keys['access_token_key'], twitter_keys['access_token_secret'] )
		return api

def get_new_requests(api, requests):
	"""
	Checks Twitter for new requests.
	"""
	
	# find recent tweets mentioning @SoftdevBot
	try:
		result = api.request( 'search/tweets', { 'q': '@SoftdevBot', 'tweet_mode': 'extended' } )
		result_json = json.loads(result.text)['statuses']
	# if unsuccessful, report no recent tweets
	except:
		result_json = []

	new_requests = []

	# check which of the new requests have not been processed yet
	for j in range(len(result_json)):
		if requests.count_documents( { '_id': result_json[j]['id_str'] } ) == 0:
			new_requests.append( result_json[j] )

	return new_requests

def post_reply(api, message, tweet_id, test_mode, img = None):
	"""
	Posts a reply to a specific request.
	"""
	if test_mode:
		status = 200
		log('The following tweet has been generated, but not posted (running in test-mode):')
		print(message)
	else:
		try:
			# check whether we are expected to post an image or not
			if img is not None:
				result = api.request( 'statuses/update_with_media', { 'status': message, 'in_reply_to_status_id': tweet_id }, { 'media[]': img.getvalue() } )
				status = result.status_code
			else:
				result = api.request( 'statuses/update', { 'status': message, 'in_reply_to_status_id': tweet_id } )
				status = result.status_code

			log('Posting a tweet, status: {}'.format(status))
		except:
			status = -1

	return status

def send_direct_message(api, message, test_mode):
	"""
	Sends a direct message to my personal Twitter account.
	"""

	event = {
		'event': {
			'type': 'message_create',
			'message_create': {
				'target': {
					'recipient_id': user_id
				},
				'message_data': {
					'text': message
				}
			}
		}
	}

	if test_mode:
		status = 200
		log('The following direct message has been generated, but not posted (running in test-mode):')
		print(message)
	else:
		result = api.request( 'direct_messages/events/new', json.dumps(event) )
		status = result.status_code
		log('Posting a direct message, status: {}'.format(status))
	
	return status
#######################################################
# General functions
#######################################################
def watch(test_mode):
	"""
	This is the main watch function which checks for updates at regular
	intervals. If executed in test_mode it will not post anything on
	Twitter and will run 60x faster.
	"""
	if test_mode:
		time_multiplier = 1
	else:
		time_multiplier = 60

	interval = None

	log('Watch process initialised')

	# start a loop
	while (interval == None or interval > 0):
		log('Process requests')
		update(test_mode)

		# get access to MongoDB
		client = get_client()
		general = client['TravellingSalesman']['general']

		# read the watch_interval field from the database
		# if not specified set to 10
		# note that the watch interval is specified in minutes
		record = general.find_one( { '_id': 'watch_interval' } )

		if record is None:
			interval = 10
			general.insert_one( { '_id': 'watch_interval', 'value': interval } )
		else:
			interval = int( record['value'] )

		# wait through the specified interval		
		sleep_time = interval * time_multiplier
		log('Wait for {}s'.format(sleep_time))
		time.sleep(sleep_time)
		
		client.close()

	log('Watch process terminated')

def update(test_mode):
	"""
	Checks for new Twitter requests and processes them.
	"""
	api = get_twitter_api()
	client = get_client()
	requests = client['TravellingSalesman']['requests']
	# get a list of unprocessed requests
	new_requests = get_new_requests(api, requests)
	log('Number of new requests: {}'.format(len(new_requests)))

	# iterate over requests to process them
	for tweet in new_requests:
		process_request(api, requests, tweet, test_mode)
	
	client.close()

def process_request(api, requests, tweet, test_mode):
	"""
	Processes a single Twitter request.
	"""
	try:
		text = tweet['full_text']
	except:
		text = ''

	# check if TSP request
	if 'TSP' in text:
		log('Request {} identified as TSP.'.format(tweet['id_str']))
		locs = extract_locations( text )
		# number of identified locations
		n = len(locs)

		name = tweet['user']['name'] + ' @' + tweet['user']['screen_name']

		# check the number of locations mentioned in the tweet
		if n == 0:
			message = 'Hi {}, I have failed to find any locations in your tweet. Please try again.'.format(name)
			status = post_reply(api, message, tweet['id'], test_mode)
		elif n < n_min:
			message = 'Hi {}, I have identified fewer than {} locations in your tweet, but this makes the problem a bit trivial. Please give me something more challenging.'.format(name, n_min)
			status = post_reply(api, message, tweet['id'], test_mode)
		elif n > n_max:
			message = 'Hi {}, I have identified more than {} locations in your tweet and I am kind of busy right now... Could you give me something slightly easier?'.format(name, n_max)
			status = post_reply(api, message, tweet['id'], test_mode)
		else:
			message = 'Hi {}, I have identified {} locations in your tweet, this should not take too long...'.format(name, n)
			status1 = post_reply(api, message, tweet['id'], test_mode)

			# generate the distance matrix and locations to visit
			dist, locs_to_visit = generate_TSP_instance(locs)
			
			# solve the TSP and measure the time elapsed
			t0 = time.time()
			tour = Route(dist, 0, 0, locs_to_visit)
			time_str = get_time_string( time.time() - t0 )
			img = plot_path(locs, tour.best_path)
			
			message = 'Ok {}, the length of the shortest path equals {:.3f} and it took me {} seconds to compute it. I hope this makes your life easier, consider liking this tweet :)'.format(name, tour.best_length, time_str)
			status2 = post_reply(api, message, tweet['id'], test_mode, img)
			img.close()
			
			# check if both messages have been posted successfully
			if status1 == 200 and status2 == 200:
				status = 200

		# save the request as processed in the database
		if status == 200:
			requests.insert_one( { '_id': tweet['id_str'], 'request_type': 'TSP' } )

	# check if NeedIP request
	elif 'NeedIP' in text:
		log('Request {} identified as NeedIP.'.format(tweet['id_str']))
		message = 'Hello, my current IP is: {}. Have a great day!'.format( get_current_IP() )
		status = send_direct_message(api, message, test_mode)

		# save the request as processed in the database
		if status == 200:
			requests.insert_one( { '_id': tweet['id_str'], 'request_type': 'IP' } )
	# if a request of unknown type, then ignore and mark as processed
	else:
		log('Request {} of unknown type, will be ignored.'.format(tweet['id_str']))
		requests.insert_one( { '_id': tweet['id_str'], 'request_type': 'none' } )
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

if __name__ == "__main__":
	test_mode = False
	watch(test_mode)
