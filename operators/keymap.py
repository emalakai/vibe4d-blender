"""
Keymap management for Vibe4D addon.

Handles registration of keyboard shortcuts.
"""

import bpy 
from ..utils .logger import logger 


class KeymapManager :
    """Manages addon keymaps."""

    def __init__ (self ):
        self .keymaps =[]

    def register_keymaps (self ):
        """Register all addon keymaps."""
        try :
            wm =bpy .context .window_manager 
            if not wm :
                logger .warning ("Window manager not available")
                return 

            kc =wm .keyconfigs .addon 
            if not kc :
                logger .warning ("Addon keyconfig not available")
                return 


            km =kc .keymaps .new (name ="3D View",space_type ='VIEW_3D')
            kmi =km .keymap_items .new (
            "vibe4d.fast_prompt",
            type ='SPACE',
            value ='PRESS',
            ctrl =True 
            )
            kmi .active =True 
            self .keymaps .append ((km ,kmi ))


            kmi2 =km .keymap_items .new (
            "vibe4d.fast_prompt",
            type ='SPACE',
            value ='PRESS',
            shift =True 
            )
            kmi2 .active =True 
            self .keymaps .append ((km ,kmi2 ))

        except Exception as e :
            logger .error (f"Failed to register keymaps: {str(e)}")
            import traceback 
            logger .error (f"Traceback: {traceback.format_exc()}")

    def unregister_keymaps (self ):
        """Unregister all addon keymaps."""
        try :
            unregistered_count =0 
            for km ,kmi in self .keymaps :
                try :
                    km .keymap_items .remove (kmi )
                    unregistered_count +=1 
                except Exception as e :
                    logger .warning (f"Failed to remove keymap item: {str(e)}")

            self .keymaps .clear ()

        except Exception as e :
            logger .error (f"Failed to unregister keymaps: {str(e)}")



keymap_manager =KeymapManager ()


def register ():
    """Register keymaps."""
    keymap_manager .register_keymaps ()


def unregister ():
    """Unregister keymaps."""
    keymap_manager .unregister_keymaps ()