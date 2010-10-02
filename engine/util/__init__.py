import pyglet, functools, json, os

# Easy access if you just import util
import const
import dijkstra
import draw
import settings
import vector
import walkpath

# Functional

def first(list_to_search, condition_to_satisfy):
    """Return first item in a list for which condition_to_satisfy(item) returns True"""
    for item in list_to_search:
        if condition_to_satisfy(item):
            return item
    return None

# Conventions

def respath(*args):
    return '/'.join(args)

def respath_func_with_base_path(*args):
    return functools.partial(respath, *args)

def mkdir_if_absent(path):
    if not os.path.exists(path):
        os.mkdir(path)

def load_json(path):
    with open('%s.json' % path, 'r') as f:
        return json.load(f)

def save_json(data, path):
    """Save data to path. Appends .json automatically."""
    with open("%s.json" % path, 'w') as f:
        json.dump(data, f, indent=4)

# Convenience and global use

def load_sprite(path, *args, **kwargs):
    loaded_image = pyglet.resource.image(respath(*path))
    return pyglet.sprite.Sprite(loaded_image, *args, **kwargs)

def image_alpha_at_point(img, x, y):
    x, y = int(x), int(y)
    # pixel_data = map(ord, list(img.get_image_data().get_data('RGBA',img.width*4)))
    pixel_data = img.get_image_data().get_data('RGBA',img.width*4)
    pos = y * img.width * 4 + x * 4
    return pixel_data[pos+3]/255.0

# Other

class ClipGroup(pyglet.graphics.OrderedGroup): 
    """Sprite group that clips to a rectangle"""
    def __init__(self, name="ClipGroup", order=0, parent=None): 
        super(ClipGroup, self).__init__(order, parent) 
        self.x, self.y, self.w, self.h = 0, 0, 256, 256 
        self.name=name 
    
    def set_state(self): 
        gl.glScissor(self.x, self.y, self.w, self.h) 
        gl.glEnable(gl.GL_SCISSOR_TEST) 
    
    def unset_state(self): 
        gl.glDisable(gl.GL_SCISSOR_TEST)
    
