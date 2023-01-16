# TravellingSalesman

In this project we have implemented the best known algorithm for solving the Travelling Salesman Problem based on dynamic programming. We do this by defining a Route class, which keeps track of its length and the parent/child routes related to it. To check that the returned solution is correct, we have also introduced the possibility to perform a brute-force search to check that we have indeed found the optimal solution.

We have also implemented a simple front-end currently hosted at: http://jedreky.pythonanywhere.com/ .

We have also implemented the possibility to interact with our code via Twitter. More specifically, our code is capable of extracting input data from Twitter posts (via Twitter API) and posting optimal solutions on Twitter. While the code responsible for finding the shortest path is capable of solving the most general instance of TSP, the Twitter-based functionality is restricted to problems where the locations are represented by 2D vectors and their distance is simply the Euclidean distance. Thanks to this restriction: (a) the users are able to provide input data in a convenient manner and (b) we can easily visualise the shortest path.

A bot is implemented by executing the watch function at regular intervals in an infinite loop. The interval between consecutive executions is stored in an external database and can be modified while the bot is running. Moreover, setting this interval to 0 will cause the bot to terminate. The watch function checks for new Twitter posts, which include the handle @SoftdevBot and tries to extract location data from them. Any string in the body of the post of the form "[x, y]" where x and y can be interpreted as floats is considered a location and our bot expects to find at least 4 locations in a post. The bot then computes the distance matrix, finds the shortest path and plots it. The length of the shortest path and the plot are then posted on Twitter as a reply to the original post.

The bot is currently down, but you can check out its previous interactions at: https://twitter.com/SoftdevBot .

# To run locally

To build containers run:

```
git checkout git@github.com:jedreky/TravellingSalesman.git
make build
```

Alternatively, you can pull the containers from Dockerhub:

https://hub.docker.com/r/jedreky/tsp/tags

```
docker pull jedreky/tsp:solver_flask
docker pull jedreky/tsp:solver_fastapi
docker pull jedreky/tsp:webapp
```

Then, use, e.g.

```
FRAMEWORK=flask docker-compose --env-file config.env up
```

or

```
FRAMEWORK=fastapi docker-compose --env-file config.env up
```

## To try

http://83.229.82.229:8338/

http://83.229.82.229:8337/

http://83.229.82.229:8337/docs