"""
This file contains all the functions and classes used by the TSP bot.
"""

import datetime
import io
import json
import matplotlib.pyplot as plt
import numpy as np
import pymongo
import re
import requests
import time

from itertools import permutations
from TwitterAPI import TwitterAPI

#######################################################
# Global variables
#######################################################
# minimal and maximal number of locations
n_min = 4
n_max = 12
#######################################################
# Short functions
#######################################################
def get_timestamp():
	"""
	Returns the current timestamp
	"""
	timestamp = datetime.datetime.now()
	return timestamp.strftime('%H:%M:%S, %d.%m.%Y')

def log(str):
	"""
	Prints a timestamped message
	"""
	print( get_timestamp() + ': ' + str )

def get_current_IP():
	"""
	Returns the current public IP address
	"""
	result = requests.get('https://api.ipify.org')
	return result.text
#######################################################
# TSP-related functions
#######################################################
def convert_to_float(s):
	"""
	Converts a string to float
	"""
	try:
		ret = float(s)
	except ValueError:
		ret = False

	return ret

def generate_id(start, locs):
	"""
	Generates string id of a path
	"""
	return str(start) + ',' + str(locs)

def extract_locations(string):
	"""
	Extracts locations from a string
	"""
	locs = []
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
	Given location coordinates generates the distance matrix
	"""
	n = len(locs)
	distance_matrix = np.zeros( [n, n] )
	
	# iterate over the entries of the matrix
	for j in range(n):
		for k in range(j + 1, n):
			v = np.array( locs[j] ) - np.array( locs[k] )
			distance_matrix[j, k] = np.sqrt( np.dot(v, v) )

	# fill up the other half of the matrix
	distance_matrix = distance_matrix + np.transpose(distance_matrix)
	return distance_matrix

def compute_length(dist, path):
	"""
	Computes the length of a given path
	"""
	length = 0

	for j in range(len(path) - 1):
		length += dist[path[j], path[j + 1]]

	return length

def brute_force(dist, start, end, locs_to_visit):
	"""
	Finds the shortest path from start to end while visiting locs_to_visit
	using the brute-force approach
	"""
	perms = permutations( locs_to_visit )
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

def plot_path(locs, path):
	"""
	Plots a path through locations
	to make a closed loop the length of the path should be longer by 1 than the number of locations
	"""
	# convert the path and the locations into numpy arrays
	path = np.array( [ locs[j] for j in path ] )
	locs_array = np.array(locs)
	# create a new figure
	fig, ax = plt.subplots( figsize = (16, 8) )
	# plot the path and the locations
	ax.plot( path[:, 0], path[:, 1])
	ax.scatter( locs_array[:, 0], locs_array[:, 1], color = 'red' )
	# save the plot to a binary stream
	img = io.BytesIO()
	fig.savefig( img, format = 'png' )
	plt.close(fig)
	return img
#######################################################
# MongoDB functions
#######################################################
def get_client():
	"""
	Returns a MongoClient
	"""
	with open('mongo_keys.json', 'r') as json_file:
		mongo_keys = json.load(json_file)
		client = pymongo.MongoClient( username = mongo_keys[0], password = mongo_keys[1] )
		return client
#######################################################
# TwitterAPI functions
#######################################################
# get a TwitterAPI object
def get_twitter_api():
	"""
	Returns TwitterAPI object
	"""
	with open('twitter_keys.json', 'r') as json_file:
		twitter_keys = json.load(json_file)
		api = TwitterAPI( twitter_keys[0], twitter_keys[1], twitter_keys[2], twitter_keys[3] )
		return api

def get_new_requests(api, requests):
	"""
	Checks Twitter for new requests
	"""
	
	# find recent tweets mentioning @SoftdevBot
	try:
		result = api.request( 'search/tweets', {'q':'@SoftdevBot', 'tweet_mode':'extended'} )
		result_json = json.loads(result.text)['statuses']
	except:
		result_json = []
	
	new_requests = []

	# check which of them have not been processed yet
	for j in range(len(result_json)):
		if requests.count_documents( { '_id': result_json[j]['id_str'] } ) == 0:
			new_requests.append( result_json[j] )

	return new_requests

def post_reply(api, message, tweet_id, test_mode, img = None):
	"""
	Posts a reply to a specific request
	"""
	if test_mode:
		status = 200
		log('The following tweet generated, but not posted (running in test-mode):')
		print(message)
	else:
		try:
			if img is not None:
				result = api.request('statuses/update_with_media', { 'status': message, 'in_reply_to_status_id': tweet_id }, { 'media[]': img.getvalue() })
				status = result.status_code
			else:
				result = api.request('statuses/update', {'status': message, 'in_reply_to_status_id': tweet_id})
				status = result.status_code
			
			log('Posting a tweet, status: {}'.format(status))
		except:
			status = -1

	return status

def send_direct_message(api, message, test_mode):
	"""
	Sends a direct message to myself
	"""
	user_id = 1390298589360844800

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
		log('The following direct message generated, but not posted (running in test-mode):')
		print(message)
	else:
		result = api.request('direct_messages/events/new', json.dumps(event))
		status = result.status_code
		log('Posting a direct message, status: {}'.format(status))
	
	return status
#######################################################
# General functions
#######################################################
def watch(test_mode):
	"""
	This is the main watch function which checks for updates at regular intervals
	if run in test_mode it will not post anything on twitter and will run 60x faster
	"""
	if test_mode:
		time_multiplier = 1
	else:
		time_multiplier = 60

	interval = 1

	log('Watch process initialised')

	while (interval > 0):
		log('Execute and wait for {}m'.format(interval))
		update(test_mode)

		sleep_time = interval * time_multiplier
		time.sleep(sleep_time)

		client = get_client()
		general = client['TravellingSalesman']['general']

		# read the watch_interval from the database, if not specified set to 10
		if general.count_documents( {'_id': 'watch_interval'} ) == 1:
			interval = int(general.find_one({ '_id': 'watch_interval'})['value'])
		else:
			interval = 10
			general.insert_one( { '_id': 'watch_interval', 'value': interval } )
		
		client.close()

	log('Watch process terminated')

def update(test_mode):
	"""
	Checks for new Twitter requests and processes them
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
	Processes a single Twitter request
	"""
	try:
		text = tweet['full_text']
	except:
		text = ''

	# check if TSP request
	if 'TSP' in text:
		locs = extract_locations( text )
		# number of distinct locations
		n = len(locs)

		name = tweet['user']['name'] + ' @' + tweet['user']['screen_name']

		# check the number of locations mentioned in the tweet
		if n == 0:
			message = 'Hi {}, I have failed to find any locations in your tweet. Please try again.'.format(name)
			status = post_reply(api, message, tweet['id'], test_mode)
		elif n < n_min:
			message = 'Hi {}, I have identified fewer than 4 locations in your tweet, but this makes the problem a bit trivial. Please give me something more challenging.'.format(name)
			status = post_reply(api, message, tweet['id'], test_mode)
		elif n > n_max:
			message = 'Hi {}, I have identified more than ' + str(n_max) + ' locations in your tweet and I am kind of busy right now... Could you give me something slightly easier?'.format(name)
			status = post_reply(api, message, tweet['id'], test_mode)
		else:
			message = 'Hi {}, I have identified {} locations in your tweet, this should not take too long...'.format(name, str(n))
			status1 = post_reply(api, message, tweet['id'], test_mode)
			
			# generate the distance matrix and locations to visit
			dist = generate_distance_matrix(locs)
			locs_to_visit = list(range(1, n))
			
			# solve the TSP and measure the time elapsed
			t0 = time.time()
			tour = Route(dist, 0, 0, locs_to_visit)
			time_elapsed = time.time() - t0
			img = plot_path(locs, tour.best_path)

			if time_elapsed < 0.001:
				time_str = 'less than 0.001'
			else:
				time_str = '{:.3f}'.format(time_elapsed)
			
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
		message = 'Hello, my current IP is: {}. Have a great day!'.format(get_current_IP())
		status = send_direct_message(api, message, test_mode)

		# save the request as processed in the database
		if status == 200:
			requests.insert_one( { '_id': tweet['id_str'], 'request_type': 'IP' } )
	# if a request of unknown type, then ignore
	else:
		requests.insert_one( { '_id': tweet['id_str'], 'request_type': 'none' } )
#######################################################
# Class definition
#######################################################
# TODO: check the following class
class Route:
	# standard constructor
	# takes: distance matrix, start and end points, locations to be visited and a dictionary to be filled
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
			self.status = 0
		# 0 - untouched
		# 1 - computation in progress
		# 2 - process terminated: suboptimal
		# 3 - optimal path found
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
				child_route.add_parent(self)
				self.add_child( child_route )
				
				# if there is a complete path for the child route, we can use it
				if child_route.path_exists:
					new_length = dist[ self.start, j ] + child_route.best_length

					if (not self.path_exists) or (self.path_exists and self.best_length > new_length):
						self.best_length = new_length
						self.best_path = [self.start] + child_route.best_path
						self.path_exists = True

		elif len(locs_to_visit) == 1:
			self.best_length = dist[self.start, locs_to_visit[0]] + dist[locs_to_visit[0], self.end ]
			self.best_path = [ self.start ] + locs_to_visit  + [ self.end ]
			self.status = 3
			self.path_exists = True
	
	def add_parent(self, parent):
		self.parents.append(parent)
	
	def add_child(self, child):
		self.children.append(child)

	def print_route(self):
		print('\nStart: {}, Locs: {}, End: {}, Status: {}'.format(self.start, self.locs_to_visit, self.end, self.status))

		if self.path_exists:
			print('Best length: {}'.format(self.best_length))
			print('Best path: {}'.format(self.best_path))

#test_mode = True
#watch(test_mode)
