import datetime
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
# Simple functions
#######################################################
# get current timestamp
def get_timestamp():
	timestamp = datetime.datetime.now()
	return timestamp.strftime('%H:%M:%S, %d.%m.%Y')
#######################################################
# print a timestamped message
def log(str):
	print( get_timestamp() + ': ' + str )
#######################################################
def get_current_IP():
	result = requests.get('https://api.ipify.org')
	return result.text
#######################################################
# TSP-related functions
#######################################################
def convert_to_float(s):
	try:
		ret = float(s)
	except ValueError:
		ret = False

	return ret
#######################################################
# generate string id
def generate_id(start, locs):
	return str(start) + ',' + str(locs)
#######################################################
# extract locations from a string
# note that the first location is appended at the end (to make a loop), so the length of the list returned equals the number of locations + 1
def extract_locations(string):
	locs = []
	matches = re.findall('\[.+?,.+?\]', string)

	for match in matches:
		s0, s1 = re.split(',', match[1: -1], 1)
		x = convert_to_float(s0)
		y = convert_to_float(s1)
		
		if isinstance(x, float) and isinstance(y, float):
			locs.append( [x, y] )
		
	# append the first location
	if len(locs) > 0:
		locs.append(locs[0])
	return locs
#######################################################
# generate the distance matrix
def generate_distance_matrix(locs):
	n = len(locs)
	distance_matrix = np.zeros( [n, n] )
	
	for j in range(n):
		for k in range(j + 1, n):
			v = np.array( locs[j] ) - np.array( locs[k] )
			distance_matrix[j, k] = np.sqrt( np.dot(v, v) )
	
	distance_matrix = distance_matrix + np.transpose(distance_matrix)
	return distance_matrix
#######################################################
# compute the length of a fixed path
def compute_length(dist, path):
	length = dist[ 0, path[0] ]
	
	for j in range(len(path) - 1):
		length += dist[path[j], path[j + 1]]

	length += dist[ path[-1], n ]

	return length

def brute_force(dist, locs_to_visit):
	perms = permutations( locs_to_visit )
	best_length = 1000
	
	for perm in perms:
		length = compute_length(dist, perm)
		if length < best_length:
			best_length = length
			best_perm = perm
	
	best_path = [0] + list(best_perm) + [n]
	return best_length, best_path
#######################################################
# generate a set of random locations in 2D centered around a specific point
def generate_random_locs(n, center = [0, 0], duplicate_first_location = True):
	rng = np.random.default_rng()
	locs = [ [rng.standard_normal() + center[0], rng.standard_normal() + center[1]] for j in range(n) ]
	if duplicate_first_location:
		locs.append( locs[0] )
	return locs
#######################################################
# plot a path
def plot_path(locs, path):
	path = np.array( [ locs[j] for j in path ] )
	locs_array = np.array(locs)
	fig = plt.figure( figsize = (16, 8) )
	ax = plt.axes()
	ax.plot( path[:, 0], path[:, 1] )
	ax.scatter( locs_array[:, 0], locs_array[:, 1], color = 'red' )
	plt.savefig('sol.png')
	plt.close()
#######################################################
# MongoDB functions
#######################################################
def get_client():
	with open('mongo_keys.json', 'r') as json_file:
		mongo_keys = json.load(json_file)
		client = pymongo.MongoClient( username = mongo_keys[0], password = mongo_keys[1] )
		return client
#######################################################
# TwitterAPI functions
#######################################################
# get a TwitterAPI object
def get_twitter_api():
	with open('twitter_keys.json', 'r') as json_file:
		twitter_keys = json.load(json_file)
		api = TwitterAPI( twitter_keys[0], twitter_keys[1], twitter_keys[2], twitter_keys[3] )
		return api
#######################################################
# check Twitter for new requests
def get_new_requests(api, requests):
	try:
		result = api.request( 'search/tweets', {'q':'@SoftdevBot', 'tweet_mode':'extended'} )
		result_json = json.loads(result.text)['statuses']
	except:
		result_json = []
	
	new_requests = []

	for j in range(len(result_json)):
		if requests.count_documents( { '_id': result_json[j]['id_str'] } ) == 0:
			new_requests.append( result_json[j] )

	return new_requests
#######################################################
# post a reply
def post_reply(api, message, tweet_id, test_mode, image = False):
	if image:
		f = open('sol.png', 'rb')
		image = f.read()
		try:
			if test_mode:
				status = 200
			else:
				result = api.request('statuses/update_with_media', {'status': message, 'in_reply_to_status_id': tweet_id}, {'media[]': image})
				status = result.status_code
		except:
			status = -1
	else:
		try:
			if test_mode:
				status = 200
			else:
				result = api.request('statuses/update', {'status': message, 'in_reply_to_status_id': tweet_id})
				status = result.status_code
		except:
			status = -1

	if test_mode:
		log('Tweet ready but not posted (test-mode)')
	else:
		log('Posting a tweet, status: {}'.format(status))

	return status
#######################################################
# send a direct message
def send_direct_message(api, message, test_mode):
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

	if not test_mode:
		result = api.request('direct_messages/events/new', json.dumps(event))
		ret = result.status_code
	else:
		ret = 200
	
	return ret
#######################################################
# General functions
#######################################################
# main watch function
# if run in test_mode it will not post anything on twitter and will run 60x faster
def watch(test_mode):
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

		if general.count_documents( {'_id': 'watch_interval'} ) == 1:
			interval = int(general.find_one({ '_id': 'watch_interval'})['value'])
		else:
			interval = 10
			general.insert_one( { '_id': 'watch_interval', 'value': interval } )
		
		client.close()

	log('Watch process terminated')
#######################################################
# check for new requests and process them
def update(test_mode):
	api = get_twitter_api()
	client = get_client()
	requests = client['TravellingSalesman']['requests']
	new_requests = get_new_requests(api, requests)
	log('Number of new requests: {}'.format(len(new_requests)))

	for tweet in new_requests:
		process_request(api, requests, tweet, test_mode)
	
	client.close()
#######################################################
# process a request from Twitter
def process_request(api, requests, tweet, test_mode):
	text = tweet['full_text']

	if 'TSP' in text:
		locs = extract_locations( text )
		# number of distinct locations
		n = len(locs) - 1
		
		name = tweet['user']['name'] + ' @' + tweet['user']['screen_name']
		
		# if there are no locations then just ignore the tweet
		if n == 0:
			a = 1
		elif n < 4:
			message = 'Hi ' + name + ', I have identified fewer than 4 locations in your tweet, but this makes the problem a bit trivial. Please give me something more challenging.'
			status = post_reply(api, message, tweet['id'], test_mode)
		elif n > 12:
			message = 'Hi ' + name + ', I have identified more than 12 locations in your tweet and I am kind of busy right now... Could you give me something slightly easier?'
			status = post_reply(api, message, tweet['id'], test_mode)
		else:
			message = 'Hi ' + name + ', I have identified ' + str(n) + ' locations in your tweet, this should not take too long...'
			
			status1 = post_reply(api, message, tweet['id'], test_mode)
			dist = generate_distance_matrix(locs)
			start = 0
			locs_to_visit = list(range(1, n + 1))
			
			t0 = time.time()
			tour = Route(dist, start, locs_to_visit)
			time_elapsed = time.time() - t0
			plot_path(locs, tour.best_path)

			if time_elapsed < 0.001:
				time_str = 'less than 0.001'
			else:
				time_str = '{:.3f}'.format(time_elapsed)
			
			message = 'Ok ' + name + ', the length of the shortest path equals {:.3f} and it took me {} seconds to compute it. I hope this makes your life easier, consider liking this tweet :)'.format(tour.best_length, time_str)
			status2 = post_reply(api, message, tweet['id'], test_mode, True)
			
			if status1 == 200 and status2 == 200:
				status = 200

		if status == 200:
			requests.insert_one( { '_id': tweet['id_str'], 'request_type': 'TSP' } )

	elif 'NeedIP' in text:
		message = 'Hello, my current IP is: {}. Have a great day!'.format(get_current_IP())
		status = send_direct_message(api, message, test_mode)

		if status == 200:
			requests.insert_one( { '_id': tweet['id_str'], 'request_type': 'IP' } )
	else:
		requests.insert_one( { '_id': tweet['id_str'], 'request_type': 'none' } )
#######################################################
# define a route class
class Route:
	# standard constructor
	def __init__(self, dist, start, locs, routes = None):
		n = len(dist) - 1
		# initialise variables
		self.start = start
		self.locs = locs
		self.parents = []
		self.children = []
		self.id = generate_id(start, locs)
		
		# if no dictionary passed, create one
		if routes == None:
			routes = {}
		
		# add route to the dictionary
		routes[self.id] = self

		# if the route is non-trivial, generate child routes
		if len(locs) >= 2:
			self.status = 0
		# 0 - untouched
		# 1 - computation in progress
		# 2 - process terminated: suboptimal
		# 3 - optimal path found
			self.path_exists = False
			
			# iterate over the next location
			for j in locs:
				# set parameters of the child route
				child_start = j
				child_locs = locs.copy()
				child_locs.remove(j)
				child_route_id = generate_id(child_start, child_locs)
				
				# if such a route exists, link it, if not create it
				if child_route_id in routes.keys():
					child_route = routes[ child_route_id ]
				else:
					child_route = Route(dist, child_start, child_locs, routes)
				
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
			
		elif len(locs) == 1:
			self.best_length = dist[self.start, locs[0]] + dist[locs[0], n ]
			self.best_path = [self.start] + locs  + [ n ]
			self.status = 3
			self.path_exists = True
	
	def add_parent(self, parent):
		self.parents.append(parent)
	
	def add_child(self, child):
		self.children.append(child)

	def print_route(self):
		print('\nStart: {}, Locs: {}, Status: {}'.format(self.start, self.locs, self.status))

		if self.path_exists:
			print('Best length: {}'.format(self.best_length))
			print('Best path: {}'.format(self.best_path))

test_mode = True
watch(test_mode)
