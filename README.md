# TravellingSalesman

This package solves the travelling salesman problem using the dynamic programming approach. Moreover, it can be used to extract input data from Twitter posts, to which it replies with an optimal solution.

The watch function, which is executed in an infinite loop, checks for new Twitter posts, which include the handle @SoftdevBot and tries to extract location data from there. Location data is expected to be a list of 2D points. The code computes the distance matrix, finds the shortest path and plots it. The length of the shortest path and the plot are then posted on Twitter as a reply to the original post.

Note that the code responsible for finding the shortest path is not restricted to 2D data and could be used to solve the most general instance of the travelling salesman problem. However, restricting ourselves to 2D problems means that: (a) the users are able to provide input data in a convenient manner and (b) we can easily visualise the shortest path.
