import datetime
import json
import re
import time
import matplotlib.pyplot as plt
#import mysql.connector
import numpy as np

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
#######################################################
# check for new requests at regular intervals
def watch():
	interval = 1

	log('Watch process initialised')

	while (interval > 0):
		log('Execute and wait for {}m'.format(interval))
		update()

		sleep_time = interval * 60
		time.sleep(sleep_time)
		
		mysql_connection = get_mysql_connection()
		interval_record = execute_mysql_query( mysql_connection, 'SELECT * FROM general WHERE field="watch_interval"' )
		interval = int(interval_record[0][1])
		mysql_connection.close()

	log('Watch process terminated')
#######################################################
# MySQL functions
#######################################################
# get a connection to the MySQL database
def get_mysql_connection():
	import mysql.connector
	with open('mysql_keys.json', 'r') as json_file:
		mysql_keys = json.load(json_file)

	mysql_connection = mysql.connector.connect( host = mysql_keys[0], user = mysql_keys[1], password = mysql_keys[2], database = mysql_keys[3] )
	return mysql_connection
#######################################################
# execute a mysql query
def execute_mysql_query(mysql_connection, mysql_query):
	cursor = mysql_connection.cursor(buffered = True)
	cursor.execute('SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED')
	cursor.execute(mysql_query)
	result = []

	if 'INSERT INTO' in mysql_query or 'UPDATE' in mysql_query:
		mysql_connection.commit()
	elif 'SELECT * FROM' in mysql_query:
		result = cursor.fetchall()
	
	cursor.close()
	return result
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
def get_new_requests(api, mysql_connection):
	try:
		result = api.request( 'search/tweets', {'q':'@SoftdevBot', 'tweet_mode':'extended'} )
		result_json = json.loads(result.text)['statuses']
	except:
		result_json = []
	
	new_requests = []
	for j in range(len(result_json)):
		if 'TSP' in result_json[j]['full_text']:
			record = execute_mysql_query( mysql_connection, 'SELECT * FROM requests WHERE tweet_id="' + result_json[j]['id_str'] + '";' )
			if len(record) == 0:
				new_requests.append( result_json[j] )

	return new_requests
#######################################################
# post a reply
def post_reply(api, message, tweet_id, image = False):
	if image:
		f = open('sol.png', 'rb')
		image = f.read()
		try:
			result = api.request('statuses/update_with_media', {'status': message, 'in_reply_to_status_id': tweet_id}, {'media[]': image})
			status = result.status_code
		except:
			status = -1
	else:
		try:
			result = api.request('statuses/update', {'status': message, 'in_reply_to_status_id': tweet_id})
			status = result.status_code
		except:
			status = -1

	log('Posting a tweet, status: {}'.format(status))
	return status
#######################################################
# extract locations from a tweet
# note that the first location is appended at the end (to make a loop), so the length of the list returned equals the number of locations + 1
def extract_locations(tweet):
	locs = []
	matches = re.findall('\[.+?,.+?\]', tweet)

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
# process a request from Twitter
def process_request(api, mysql_connection, tweet):
	locs = extract_locations( tweet['full_text'] )
	# number of distinct locations
	n = len(locs) - 1
	
	name = tweet['user']['name'] + ' @' + tweet['user']['screen_name']
	
	# if there are no locations then just ignore the tweet
	if n == 0:
		a = 1
	elif n < 4:
		message = 'Hi ' + name + ', I have identified fewer than 4 locations in your tweet, but this makes the problem a bit trivial. Please give me something more challenging.'
		status = post_reply(api, message, tweet['id'])
	elif n > 12:
		message = 'Hi ' + name + ', I have identified more than 12 locations in your tweet and I am kind of busy right now... Could you give me something slightly easier?'
		status = post_reply(api, message, tweet['id'])
	else:
		message = 'Hi ' + name + ', I have identified ' + str(n) + ' locations in your tweet, this should not take too long...'
		
		status1 = post_reply(api, message, tweet['id'])
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
		status2 = post_reply(api, message, tweet['id'], True)
		
		if status1 == 200 and status2 == 200:
			status = 200

	if status == 200:
		query = 'INSERT INTO requests VALUES ("' + tweet['id_str'] + '", 0);'
		execute_mysql_query( mysql_connection, query )
#######################################################
# check for new requests and process them
def update():
	api = get_twitter_api()
	mysql_connection = get_mysql_connection()
	new_requests = get_new_requests(api, mysql_connection)
	log('Number of new requests: {}'.format(len(new_requests)))

	for request in new_requests:
		process_request(api, mysql_connection, request)
	mysql_connection.close()
	#return new_requests

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

#watch()
