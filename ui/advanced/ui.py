"""
Advanced Custom UI System for Blender
Provides a component-based overlay system with GPU rendering

This is the main module that imports and re-exports all components.
"""

import logging 
import bpy 
from bpy .types import Panel 


logger =logging .getLogger (__name__ )


from .types import EventType ,UIEvent ,Bounds ,Style 
from .coordinates import CoordinateSystem 
from .state import UIState 
from .renderer import UIRenderer 
from .components import UIComponent ,TextInput ,Label ,Button 
from .manager import UIManager ,ui_manager 
from .theme import theme_manager ,get_themed_style ,get_theme_color 
from .colors import Colors ,get_color ,PALETTE 


class VIBE4D_PT_UITest (Panel ):
    """UI Test panel for debugging and testing the advanced UI system."""
    bl_label ="UI Test"
    bl_idname ="VIBE4D_PT_ui_test"
    bl_space_type ='VIEW_3D'
    bl_region_type ='UI'
    bl_category ='Vibe4D'
    bl_options ={'DEFAULT_CLOSED'}

    def draw (self ,context ):
        """Draw the panel UI."""
        layout =self .layout 


        layout .operator ("vibe4d.ui_debug_test",icon ='CONSOLE',text ="Debug Test")


        if ui_manager .is_ui_active ():
            layout .label (text ="UI Status: Active",icon ='CHECKMARK')
            layout .label (text =f"Components: {len(ui_manager.state.components)}")
            layout .label (text =f"Viewport: {ui_manager.state.viewport_width}x{ui_manager.state.viewport_height}")
        else :
            layout .label (text ="UI Status: Inactive",icon ='X')



def enable_overlay (target_area =None ):
    """Enable the custom overlay for a specific area."""
    ui_manager .enable_overlay (target_area )


def disable_overlay ():
    """Disable the custom overlay."""
    ui_manager .disable_overlay ()


def cleanup_overlay ():
    """Remove draw handler completely."""
    ui_manager .cleanup ()


def register ():
    """Register UI components."""
    try :
        bpy .utils .register_class (VIBE4D_PT_UITest )
        logger .info ("UI system registered")
    except Exception as e :
        logger .error (f"Error registering UI system: {e}")
        raise 


def unregister ():
    """Unregister UI components."""
    try :
        ui_manager .cleanup ()
        try :
            bpy .utils .unregister_class (VIBE4D_PT_UITest )
        except :
            pass 
        logger .info ("UI system unregistered")
    except Exception as e :
        logger .error (f"Error unregistering UI system: {e}")



__all__ =[

'EventType',
'UIEvent',
'Bounds',
'Style',


'CoordinateSystem',
'UIState',
'UIRenderer',
'UIManager',


'theme_manager',
'get_themed_style',
'get_theme_color',


'Colors',
'get_color',
'PALETTE',


'UIComponent',
'TextInput',
'Label',
'Button',


'ui_manager',


'VIBE4D_PT_UITest',


'enable_overlay',
'disable_overlay',
'cleanup_overlay',
'register',
'unregister',
]