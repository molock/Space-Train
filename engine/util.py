import math, operator

def round_down(v):
    return (int(v[0]), int(v[1]))

def tuple_op(a, b, op=operator.sub):
    return (op(a[0], b[0]), op(a[1], b[1]))

def length(v):
    return math.sqrt(v[0]*v[0] + v[1]*v[1])

def dist_between(a, b):
    return length(tuple_op(a, b, operator.sub))

def dist_squared(v):
    return v[0]*v[0] + v[1]*v[1]

def normalize(v):
    l = length(v)
    return (v[0]/l, v[1]/l)

def dot(x, y):
    return x[0]*y[0] + x[1]*y[1]

def scalar_mult(v, t):
    return (v[0]*t, v[1]*t)

def closest_point_on_line(point, a, b):
    # Shamelessly stolen from the internet and ported to Python
    # http://www.gamedev.net/community/forums/topic.asp?topic_id=198199
    
    c = tuple_op(point, a, operator.sub)        # Vector from a to Point
    v = normalize(tuple_op(b, a, operator.sub)) # Unit Vector from a to b
    d = length(tuple_op(b, a, operator.sub))    # Length of the line segment
    t = dot(v, c)                               # Intersection point Distance from a
    
    # Check to see if the point is on the line
    # if not then return the endpoint
    if t < 0: 
        return a
    if t > d: 
        return b
    
    # get the distance to move from point a
    v = scalar_mult(v, t)
    
    # move from point a to the nearest point on the segment
    return tuple_op(a, v, operator.add)