#   Library, writes nothing: the terrace camera every generator draws through: a level pinhole camera
#   looking at a circular terrace floor, and the railing band that follows its rim.
#
#   World units are eye heights: the eye sits at height 1, so anything at eye
#   level lands on the horizon wherever it stands.

import numpy as np


class Camera:
    def __init__(self, horizon, focal, centre_x):
        self.horizon, self.focal, self.centre_x = horizon, focal, centre_x

    def project(self, X, Y, Z):
        return self.centre_x + self.focal * X / Z, self.horizon + self.focal * (1 - Y) / Z

    def unproject_onto_plane(self, x, y, point, normal):
        eye = np.array([0.0, 1.0, 0.0])
        ray = np.array([(x - self.centre_x) / self.focal, -(y - self.horizon) / self.focal, 1.0])
        t = np.dot(normal, point - eye) / np.dot(normal, ray)
        return eye + t * ray


class Terrace:
    def __init__(self, camera, centre_z, radius, rail_height):
        self.camera, self.centre_z, self.radius, self.rail_height = camera, centre_z, radius, rail_height

    def floor_point(self, theta, radius=None):
        r = self.radius if radius is None else radius
        return np.array([r * np.sin(theta), 0.0 * theta, self.centre_z + r * np.cos(theta)])

    @staticmethod
    def tangent(theta):
        return np.array([np.cos(theta), 0.0, -np.sin(theta)])

    @staticmethod
    def outward(theta):
        return np.array([np.sin(theta), 0.0, np.cos(theta)])

    def theta_at_x(self, x):
        """Angle of the far rim point that projects to screen x."""
        s = (np.asarray(x, float) - self.camera.centre_x) / self.camera.focal
        a, b, c = s * s + 1, -2 * self.centre_z, self.centre_z ** 2 - self.radius ** 2
        Z = (-b + np.sqrt(b * b - 4 * a * c)) / (2 * a)
        return np.arctan2(s * Z, Z - self.centre_z)

    def on_rail(self, theta, along, height):
        p = self.floor_point(theta) + along * self.tangent(theta)
        return self.camera.project(p[0], height, p[2])


# The camera fitted to the original EsmeTerrace painting, which every generator draws through.
BUILT_WITH = dict(horizon=382.96635794955125, focal=1571.6934201094296, centre_x=768.0,
                  centre_z=2.267438133663062, radius=2.993034699052806, rail_height=0.38460502914965955)


def built_terrace():
    b = BUILT_WITH
    return Terrace(Camera(b['horizon'], b['focal'], b['centre_x']), b['centre_z'], b['radius'], b['rail_height'])


def smooth_path(points, closed=False):
    """Catmull-Rom through points, as cubic Beziers."""
    p = [np.asarray(q, float) for q in points]
    d = ['M%.2f,%.2f' % tuple(p[0])]
    for i in range(len(p) - 1):
        a, b, c, e = p[max(i - 1, 0)], p[i], p[i + 1], p[min(i + 2, len(p) - 1)]
        c1, c2 = b + (c - a) / 6, c - (e - b) / 6
        d.append('C%.2f,%.2f %.2f,%.2f %.2f,%.2f' % (*c1, *c2, *c))
    if closed:
        d.append('Z')
    return ' '.join(d)



# ---------------------------------------------------------------- rail

def visible_theta_range(terrace, width, margin=80):
    a, b = terrace.theta_at_x(-margin), terrace.theta_at_x(width + margin)
    return float(min(a, b)), float(max(a, b))


def rail_band(terrace, theta_range, low, high, shift, samples=28):
    thetas = np.linspace(*theta_range, samples)
    upper = [shift(terrace.on_rail(t, 0, high)) for t in thetas]
    lower = [shift(terrace.on_rail(t, 0, low)) for t in thetas[::-1]]
    # Two smooth edges joined by straight ends off-canvas.
    top = smooth_path(upper)
    bottom = smooth_path(lower)[1:].split(' ', 1)
    return '%s L%s %s Z' % (top, bottom[0], bottom[1])
