# -*- coding: utf-8 -*-
"""
Created on Sat Mar 10 11:21:33 2018

@author: TTM
"""

from __future__ import division
import numpy as np
import scipy.constants as c

from traits.api import HasTraits, Instance, Array, \
    on_trait_change
from traitsui.api import View, Item, HGroup, Group

from tvtk.api import tvtk
from tvtk.pyface.scene import Scene

from mayavi import mlab
from mayavi.core.api import PipelineBase, Source
from mayavi.core.ui.api import SceneEditor, MayaviScene, \
                                MlabSceneModel

def cartesian_to_spherical(x, y, z):
    r=np.sqrt(x*x+y*y+z*z)
    theta=np.arccos(z/r)
    phi=np.arctan2(y,x)

    r= np.round(r,5)
    theta= np.round(theta,5)
    phi= np.round(phi,5)
    
    return(r,theta,phi)
 
def absolute(cnumber):
	x=np.real(cnumber)
	y=np.imag(cnumber)
    
	return(np.sqrt(x*x+y*y))

def angular_wave_func(m,l,theta,phi):
    if l == 0 and m == 0:
        y=np.sqrt(1/(4*np.pi))
    
    elif l == 1:
        if m == 1:
            y=-np.sqrt(3/(8*np.pi))*np.sin(theta)*np.exp(1j*phi)
        elif m == 0:
            y=np.sqrt(3/(4*np.pi))*np.cos(theta)
        elif m == -1:
            y=np.sqrt(3/(8*np.pi))*np.sin(theta)*np.exp(-1j*phi)
    
    elif l==2:
        if m == 2:
            y=np.sqrt(15/(32*np.pi))*((np.sin(theta))**2)*np.exp(1j*2*phi)
        elif m == 1:
            y=-np.sqrt(15/(8*np.pi))*np.cos(theta)*np.sin(theta)*np.exp(1j*phi)
        elif m == 0:
            y=np.sqrt(5/(16*np.pi))*(3*((np.cos(theta))**2)-1)
        elif m== -1:
            y=np.sqrt(15/(8*np.pi))*np.cos(theta)*np.sin(theta)*np.exp(-1j*phi)
        elif m== -2:
            y=np.sqrt(15/(32*np.pi))*((np.sin(theta))**2)*np.exp(-1j*2*phi)
    
    return np.round(y,5) 

def radial_wave_func(l,r):
    a=c.physical_constants['Bohr radius'][0]
    r = r*a
    
    if l == 0:
        R = 2/(81*np.sqrt(3))*a**-1.5*(27-18*(r/a)+2*(r/a)**2)*np.exp(-r/(3*a))
    
    elif l == 1:
        R = 8/(27*np.sqrt(6))*a**-1.5*(1-r/(6*a))*(r/a)*np.exp(-r/(3*a))
    
    elif l == 2:
        R = 4/(81*np.sqrt(30))*a**-1.5*(r/a)**2*np.exp(-r/(3*a)) 
    
    return np.round(R,5)

def linspace(start, stop, num = 50):
    return (np.array([round(start+i*((stop-start)/(num-1)),5) for i in range(num)]))


def meshgrid(x,y,z):
    XX = []
    YY = []
    ZZ = []

    for i in x:
        lst1 = []
        for e in range(len(z)):
            lst1.append(float(i))
        XX.append(lst1)

    XX = [XX]*len(y)

    for i in y:
        lst2 = []
        for e in range(len(z)):
            lst2.append(float(i))
        lst2 = [lst2]*len(x)
        YY.append(lst2)   

    for i in range(len(z)):
        z[i] = float(z[i])

    ZZ = [z]*len(x)
    ZZ = [ZZ]*len(y)

    output = (np.array(XX), np.array(YY), np.array(ZZ))

    return output

def hydrogen_wave_func(l, m, roa, Nx, Ny, Nz):
    
    x = linspace(-roa,roa,Nx)
    y = linspace(-roa,roa,Ny)
    z = linspace(-roa,roa,Nz)
               
    yy,xx,zz = meshgrid(y,x,z)               
                
    r, theta, phi = cartesian_to_spherical(xx, yy, zz)
    
    rComponent = (radial_wave_func(l,r))
    
    if m == 0:
        angComponent = (angular_wave_func(m,l,theta,phi))
    elif m < 0:
        angComponent = 1/np.sqrt(2)*(angular_wave_func(-m,l,theta,phi)-angular_wave_func(m,l,theta,phi))
    elif m > 0:
        angComponent = 1j/np.sqrt(2)*(angular_wave_func(-m,l,theta,phi)+angular_wave_func(m,l,theta,phi))
    
    mag = np.array(np.round(absolute((rComponent*angComponent)**2),5))
    
    return mag


class VolumeSlicer(HasTraits):
    # The data to plot
    data = hydrogen_wave_func(2,2,20,150,150,150)

    # The 4 views displayed
    scene3d = Instance(MlabSceneModel, ())
    scene_x = Instance(MlabSceneModel, ())
    scene_y = Instance(MlabSceneModel, ())
    scene_z = Instance(MlabSceneModel, ())

    # The data source
    data_src3d = Instance(Source)

    # The image plane widgets of the 3D scene
    ipw_3d_x = Instance(PipelineBase)
    ipw_3d_y = Instance(PipelineBase)
    ipw_3d_z = Instance(PipelineBase)

    _axis_names = dict(x=0, y=1, z=2)


    #---------------------------------------------------------------------------
    def __init__(self, **traits):
        super(VolumeSlicer, self).__init__(**traits)
        # Force the creation of the image_plane_widgets:
        self.ipw_3d_x
        self.ipw_3d_y
        self.ipw_3d_z


    #---------------------------------------------------------------------------
    # Default values
    #---------------------------------------------------------------------------
    def _data_src3d_default(self):
        return mlab.pipeline.scalar_field(self.data,
                            figure=self.scene3d.mayavi_scene)

    def make_ipw_3d(self, axis_name):
        ipw = mlab.pipeline.image_plane_widget(self.data_src3d,
                        figure=self.scene3d.mayavi_scene,
                        plane_orientation='%s_axes' % axis_name)
        return ipw

    def _ipw_3d_x_default(self):
        return self.make_ipw_3d('x')

    def _ipw_3d_y_default(self):
        return self.make_ipw_3d('y')

    def _ipw_3d_z_default(self):
        return self.make_ipw_3d('z')


    #---------------------------------------------------------------------------
    # Scene activation callbaks
    #---------------------------------------------------------------------------
    @on_trait_change('scene3d.activated')
    def display_scene3d(self):
        outline = mlab.pipeline.outline(self.data_src3d,
                        figure=self.scene3d.mayavi_scene,
                        )
        self.scene3d.mlab.view(40, 50)
        # Interaction properties can only be changed after the scene
        # has been created, and thus the interactor exists
        for ipw in (self.ipw_3d_x, self.ipw_3d_y, self.ipw_3d_z):
            # Turn the interaction off
            ipw.ipw.interaction = 0
        self.scene3d.scene.background = (0, 0, 0)
        # Keep the view always pointing up
        self.scene3d.scene.interactor.interactor_style = \
                                 tvtk.InteractorStyleTerrain()
        #mlab.axes()


    def make_side_view(self, axis_name):
        scene = getattr(self, 'scene_%s' % axis_name)

        # To avoid copying the data, we take a reference to the
        # raw VTK dataset, and pass it on to mlab. Mlab will create
        # a Mayavi source from the VTK without copying it.
        # We have to specify the figure so that the data gets
        # added on the figure we are interested in.
        outline = mlab.pipeline.outline(
                            self.data_src3d.mlab_source.dataset,
                            figure=scene.mayavi_scene,
                            )
        ipw = mlab.pipeline.image_plane_widget(
                            outline,
                            plane_orientation='%s_axes' % axis_name)
        setattr(self, 'ipw_%s' % axis_name, ipw)

        # Synchronize positions between the corresponding image plane
        # widgets on different views.
        ipw.ipw.sync_trait('slice_position',
                            getattr(self, 'ipw_3d_%s'% axis_name).ipw)

        # Make left-clicking create a crosshair
        ipw.ipw.left_button_action = 0
        # Add a callback on the image plane widget interaction to
        # move the others
        def move_view(obj, evt):
            position = obj.GetCurrentCursorPosition()
            for other_axis, axis_number in self._axis_names.items():
                if other_axis == axis_name:
                    continue
                ipw3d = getattr(self, 'ipw_3d_%s' % other_axis)
                ipw3d.ipw.slice_position = position[axis_number]

        ipw.ipw.add_observer('InteractionEvent', move_view)
        ipw.ipw.add_observer('StartInteractionEvent', move_view)

        # Center the image plane widget
        ipw.ipw.slice_position = 0.5*self.data.shape[
                    self._axis_names[axis_name]]

        # Position the view for the scene
        views = dict(x=( 0, 90),
                     y=(90, 90),
                     z=( 0,  0),
                     )
        scene.mlab.view(*views[axis_name])
        # 2D interaction: only pan and zoom
        scene.scene.interactor.interactor_style = \
                                 tvtk.InteractorStyleImage()
        scene.scene.background = (0, 0, 0)
        #mlab.axes()


    @on_trait_change('scene_x.activated')
    def display_scene_x(self):
        return self.make_side_view('x')

    @on_trait_change('scene_y.activated')
    def display_scene_y(self):
        return self.make_side_view('y')

    @on_trait_change('scene_z.activated')
    def display_scene_z(self):
        return self.make_side_view('z')


    #---------------------------------------------------------------------------
    # The layout of the dialog created
    #---------------------------------------------------------------------------
    view = View(HGroup(
                  Group(
                       Item('scene_y',
                            editor=SceneEditor(scene_class=MayaviScene),
                            height=250, width=300),
                       Item('scene_z',
                            editor=SceneEditor(scene_class=MayaviScene),
                            height=250, width=300),
                       show_labels=True,
                  ),
                  Group(
                       Item('scene_x',
                            editor=SceneEditor(scene_class=MayaviScene),
                            height=250, width=300),
                       Item('scene3d',
                            editor=SceneEditor(scene_class=MayaviScene),
                            height=250, width=300),
                       show_labels=True,
                  ),
                ),
                resizable=True,
                title='Volume Slicer',
                )


m = VolumeSlicer()
m.configure_traits()       
 

