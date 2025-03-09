import math

def vec3_lenght(vec):
    return math.sqrt( vec[0]*vec[0] + vec[1]*vec[1] + vec[2]*vec[2] );

def vec3_normalize(vec):
    lenght = vec3_lenght(vec)
    vec[0] /= lenght
    vec[1] /= lenght
    vec[2] /= lenght
