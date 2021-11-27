"""
This file contains functions and classes used by the Twitter bot.
"""

import json
import pymongo
import requests
import time
import TwitterAPI

import TravellingSalesman as TS

#######################################################
# Global variables
#######################################################
# minimal and maximal number of locations
n_min = 4
n_max = 12
# id of my personal Twitter account
user_id = '1390298589360844800'

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
		api = TwitterAPI.TwitterAPI( twitter_keys['consumer_key'], twitter_keys['consumer_secret'], twitter_keys['access_token_key'], twitter_keys['access_token_secret'])
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
		TS.log('An error occured while trying to read the outcome of a request')
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
		TS.log('The following tweet has been generated, but not posted (running in test-mode):')
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

			TS.log('Posting a tweet, status: {}'.format(status))
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
		TS.log('The following direct message has been generated, but not posted (running in test-mode):')
		print(message)
	else:
		result = api.request( 'direct_messages/events/new', json.dumps(event) )
		status = result.status_code
		TS.log('Posting a direct message, status: {}'.format(status))
	
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

	TS.log('Watch process initialised')

	# start a loop
	while (interval == None or interval > 0):
		TS.log('Process requests')
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
		TS.log('Wait for {}s'.format(sleep_time))
		time.sleep(sleep_time)
		
		client.close()

	TS.log('Watch process terminated')

def update(test_mode):
	"""
	Checks for new Twitter requests and processes them.
	"""
	api = get_twitter_api()
	client = get_client()
	requests = client['TravellingSalesman']['requests']
	# get a list of unprocessed requests
	new_requests = get_new_requests(api, requests)
	TS.log('Number of new requests: {}'.format(len(new_requests)))

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
		TS.log('Request {} identified as TSP.'.format(tweet['id_str']))
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
		TS.log('Request {} identified as NeedIP.'.format(tweet['id_str']))
		message = 'Hello, my current IP is: {}. Have a great day!'.format( get_current_IP() )
		status = send_direct_message(api, message, test_mode)

		# save the request as processed in the database
		if status == 200:
			requests.insert_one( { '_id': tweet['id_str'], 'request_type': 'IP' } )
	# if a request of unknown type, then ignore and mark as processed
	else:
		TS.log('Request {} of unknown type, will be ignored.'.format(tweet['id_str']))
		requests.insert_one( { '_id': tweet['id_str'], 'request_type': 'none' } )

if __name__ == "__main__":
	test_mode = True
	watch(test_mode)
