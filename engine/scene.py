import os, sys, shutil, json, importlib, pyglet, functools

import camera, actor, gamestate, util, interpolator, convo
from util import walkpath

import cam, environment, gamehandler, scenehandler


update_t = 1/60.0
class Scene(interpolator.InterpolatorController):
    
    # Initialization
    
    def __init__(self, name, scene_handler=None, ui=None, load_path=None):
        super(Scene, self).__init__()
        self.name = name
        self.handler = scene_handler
        self.batch = pyglet.graphics.Batch()
        self.ui = ui
        self.actors = {}
        self.camera_points = {}
        
        self.game_time = 0.0
        self.accum_time = 0.0
        self.clock = pyglet.clock.Clock(time_function=lambda: self.game_time) 
        self.paused = False
        
        self.convo = convo.Conversation(self)
        
        self.resource_path = util.respath_func_with_base_path('game', self.name)
        
        self.load_info(load_path)
        self.initialize_from_info()
        self.load_actors()
        
        if gamestate.scripts_enabled:
            self.load_script()
    
    def initialize_from_info(self):
        """Initialize objects specified in info.json"""
        self.environment_name = self.info['environment']
        self.env = environment.Environment(self.environment_name)
        self.walkpath = walkpath.WalkPath(dict_repr = self.info['walkpath'])
        self.camera = camera.Camera(dict_repr=self.info['camera_points'])
    
    def load_actors(self):
        """Initialize actors and update them with any values specified in the info dict"""
        for identifier, attrs in self.info['actors'].viewitems():
            # Initialize and store
            new_actor = actor.Actor(name=attrs['name'], identifier=identifier, 
                                    scene=self, attrs=attrs)
            self.actors[identifier] = new_actor
            
            # Obey walk paths
            if attrs.has_key('walkpath_point'):
                new_actor.walkpath_point = attrs['walkpath_point']
                new_actor.sprite.position = self.walkpath.points[new_actor.walkpath_point]
    
    def load_script(self):
        # Requires that game/scenes is in PYTHONPATH
        self.module = importlib.import_module(self.name)
        self.module.myscene = self
        self.call_if_available('init')
    
    
    # Cleanup
    def exit(self):
        for actor in self.actors.viewvalues():
            actor.sprite.delete()
        self.env.exit()
    
    
    # Access
    
    def __repr__(self):
        return 'Scene(name="%s")' % self.name
    
    def actor_under_point(self, x, y):
        return util.first(self.actors.viewvalues(), lambda act:act.covers_point(x, y))
    
    
    # Script interaction
    
    def fire_adv_event(self, event, *args):
        self.module.handle_event(event, *args)
    
    def call_if_available(self, func_name, *args, **kwargs):
        if hasattr(self.module, func_name):
            return getattr(self.module, func_name)(*args, **kwargs)
        else:
            return False
    
    
    # Events
    
    def transition_from(self, old_scene_name):
        self.call_if_available('transition_from', old_scene_name)
    
    def on_mouse_release(self, x, y, button, modifiers):
        clicked_actor = self.actor_under_point(*self.camera.mouse_to_canvas(x, y))
        
        if clicked_actor:
            if(self.ui.inventory.held_item is not None):
                if self.call_if_available('give_actor', clicked_actor, self.ui.inventory.held_item) is False:
                    self.ui.inventory.put_item(self.held_item)
                    self.ui.inventory.held_item = None
            else:
                self.call_if_available('actor_clicked', clicked_actor)
        elif self.actors.has_key("main"):
            # Send main actor to click location according to actor's moving behavior
            main = self.actors["main"]
            while(main.blocking_actions > 0):
                main.next_action()
            if main.prepare_move(*self.camera.mouse_to_canvas(x, y)):
                main.next_action()
    
    
    # Update/draw
    
    def update(self, dt=0):
        if self.paused: 
            return
        
        # Align updates to fixed timestep 
        self.accum_time += dt 
        if self.accum_time > update_t * 3: 
            self.accum_time = update_t 
        while self.accum_time >= update_t: 
            self.game_time += update_t
            self.clock.tick() 
            self.accum_time -= update_t
        
        if self.actors.has_key('main'):
            self.camera.set_target(self.actors["main"].sprite.x, self.actors["main"].sprite.y)
        self.camera.update(dt)
        self.update_interpolators(dt)
    
    @camera.obey_camera
    def draw(self, dt=0):
        self.env.draw()
        self.batch.draw()
        
        if self.actors.has_key('cart_lady'):
            self.actors['cart_lady'].sprite.draw()
        
        self.env.draw_overlay()
        self.convo.draw()
    
    
    # Serialization
    
    def dict_repr(self):
        """Update and return all information necessary to recreate this Scene's current state"""
        self.info['actors'] = {i: act.dict_repr() for i, act in self.actors.viewitems()}
        self.info['walkpath'] = self.walkpath.dict_repr()
        self.info['camera_points'] = self.camera.dict_repr()
        return self.info
    
    def load_info(self, load_path=None):
        if load_path is None:
            with pyglet.resource.file(self.resource_path('info.json'), 'r') as info_file:
                self.info = json.load(info_file)
        else:
            self.info = util.load_json(load_path)
    
    def save_info(self):
        shutil.copyfile(self.resource_path('info.json'), self.resource_path('info.json~'))
        with pyglet.resource.file(self.resource_path('info.json'), 'w') as info_file:
            json.dump(self.dict_repr(), info_file, indent=4)
    
    
    # Editor methods
    
    def new_actor(self, actor_name, identifier=None, **kwargs):
        if identifier is None:
            next_identifier = 1
            while self.actors.has_key("%s_%d" % (actor_name, next_identifier)):
                next_identifier += 1
            identifier = "%s_%d" % (actor_name, next_identifier)
        new_actor = actor.Actor(identifier, actor_name, self, **kwargs)
        self.actors[identifier] = new_actor
        return new_actor
    
    def remove_actor(self, identifier):
        self.actors[identifier].sprite.delete()
        del self.actors[identifier]
    
