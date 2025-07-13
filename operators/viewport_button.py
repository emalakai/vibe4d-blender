"""
Viewport button operator for handling mouse events.
"""

import bpy 
import logging 
from bpy .types import Operator 

logger =logging .getLogger (__name__ )


class VIBE4D_OT_viewport_button_handler (Operator ):
    """Modal operator for handling viewport button mouse events."""
    bl_idname ="vibe4d.viewport_button_handler"
    bl_label ="Viewport Button Handler"
    bl_description ="Handle mouse events for viewport button"
    bl_options ={'REGISTER'}

    def modal (self ,context ,event ):
        """Handle modal events."""
        try :
            from ..ui .advanced .viewport_button import viewport_button 


            if event .type in {'LEFTMOUSE','MOUSEMOVE'}:

                for area in context .screen .areas :
                    if area .type =='VIEW_3D':

                        if (area .x <=event .mouse_x <=area .x +area .width and 
                        area .y <=event .mouse_y <=area .y +area .height ):

                            with context .temp_override (area =area ):
                                if viewport_button .handle_mouse_event (event ):
                                    return {'RUNNING_MODAL'}
                            break 

            return {'PASS_THROUGH'}
        except Exception as e :
            logger .error (f"Error in viewport button modal handler: {e}")
            return {'CANCELLED'}

    def execute (self ,context ):
        """Execute the operator."""
        context .window_manager .modal_handler_add (self )
        return {'RUNNING_MODAL'}



classes =[
VIBE4D_OT_viewport_button_handler ,
]


def register ():
    """Register viewport button operators."""
    for cls in classes :
        bpy .utils .register_class (cls )


def unregister ():
    """Unregister viewport button operators."""
    for cls in reversed (classes ):
        try :
            bpy .utils .unregister_class (cls )
        except :
            pass 