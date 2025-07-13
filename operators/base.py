"""
Base operators for Vibe4D addon.

Core operators for authentication, generation, and basic functionality.
"""

import bpy 
from bpy .types import Operator 
from bpy .props import StringProperty 

from ..utils .logger import logger 


class VIBE4D_OT_authenticate (Operator ):
    """Authenticate with Vibe4D service."""

    bl_idname ="vibe4d.authenticate"
    bl_label ="Authenticate"
    bl_description ="Authenticate with Vibe4D service"
    bl_options ={'REGISTER'}

    def execute (self ,context ):
        """Execute authentication."""
        try :
            logger .info ("Authentication operator called")




            return {'FINISHED'}

        except Exception as e :
            logger .error (f"Authentication failed: {str(e)}")
            self .report ({'ERROR'},f"Authentication failed: {str(e)}")
            return {'CANCELLED'}



classes =[
VIBE4D_OT_authenticate ,
]


def register ():
    """Register operators."""
    for cls in classes :
        bpy .utils .register_class (cls )


def unregister ():
    """Unregister operators."""
    for cls in reversed (classes ):
        try :
            bpy .utils .unregister_class (cls )
        except RuntimeError :
            pass 