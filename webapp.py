import io
import os
import random
import string
import sys
import time

from flask import Flask, Markup, render_template, request
import PIL

import TravellingSalesman as TS

#######################################################
# Global variables
#######################################################
# minimal and maximal number of locations
n_min = 4
n_max = 16
background_file = 'background.jpg'
#######################################################

def generate_random_string(length):
	ret = ''.join( random.choices( string.ascii_lowercase + string.digits, k = length ) )
	return ret

app = Flask(__name__)

@app.route( '/', methods=['GET', 'POST'] )
def main():
	img = PIL.Image.open('static/' + background_file)
	img_size = img.size

	if request.method == 'GET':
		return render_template('main.html', img_file = background_file, img_size = img_size)
	elif request.method == 'POST':
		locs = TS.extract_locations( request.form['points'] )
		n = len(locs)

		if n >= n_min:
			message = ''

			if n > n_max:
				locs = locs[:n_max]
				message += 'You have specified a lot of points, so I have only considered the first {} of them.<br>'.format(n_max)

			dist, locs_to_visit = TS.generate_TSP_instance(locs)

			t0 = time.time()
			tour = TS.Route(dist, 0, 0, locs_to_visit)
			time_str = TS.get_time_string( time.time() - t0 )

			img_info = { 'file': background_file, 'width': img.size[0], 'height': img.size[1] }
			img = TS.plot_path(locs, tour.best_path, False, img_info)

			img_file = 't-' + generate_random_string(12) + '.jpg'

			with open('static/' + img_file, 'wb') as f:
				f.write(img.getbuffer())

			message += 'Length of the shortest path: {:.3f} (size of the entire map: {} x {})<br>'.format( tour.best_length, img_size[0], img_size[1] )
			message += 'Total computation time: {}s'.format( time_str )
			return render_template('main.html', img_file = img_file, img_size = img_size, message = Markup(message) )
		elif n < n_min:
			return render_template('main.html', img_file = background_file, img_size = img_size, message = 'You have not specified enough points!')
	else:
		return 'An error has occurred';

if __name__ == '__main__':
	host = '127.0.0.1'
	app.run( host = host, port = 8081, debug = True )