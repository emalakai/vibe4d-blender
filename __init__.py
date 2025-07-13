"""
Vibe4D - AI-powered Blender addon.

This addon provides AI-powered code generation and assistance for Blender.
"""

bl_info ={
"name":"Vibe4D",
"author":"Emalakai",
"version":(0 ,1 ,0 ),
"blender":(4 ,4 ,0 ),
"location":"View3D > Sidebar > Vibe4D",
"description":"Ultimate Blender AI Assistant",
"warning":"",
"doc_url":"",
"category":"Development",
}

import bpy 
from bpy .app .handlers import persistent 

from .utils .logger import logger 
from .utils .history_manager import history_manager 
from .utils .settings_manager import settings_manager 
from .utils .instructions_manager import instructions_manager 
from .auth .manager import auth_manager 


from .import ui 
from .import operators 
from .import auth 
from .import api 
from .import llm 
from .import engine 
from .import utils 



query =api .query 
execute =api .execute 
scene_context =api .scene_context 
get_query_formats =api .get_query_formats 
table_counts =api .table_counts 
viewport =api .viewport 
add_viewport_render =api .add_viewport_render 
see_viewport =api .see_viewport 
see_render =api .see_render 


render_async =api .render_async 
get_render_result =api .get_render_result 
cancel_render =api .cancel_render 
list_active_renders =api .list_active_renders 
render_with_callback =api .render_with_callback 


@persistent 
def load_auth_and_settings_on_file_load (file ):
    """Initialize auth and settings when a Blender file is loaded."""
    try :
        if bpy .context .scene :


            is_authenticated =getattr (bpy .context .window_manager ,'vibe4d_authenticated',False )

            if not is_authenticated :
                auth_manager .initialize_auth (bpy .context )

            settings_manager .initialize_settings (bpy .context )
            instructions_manager .initialize_instructions (bpy .context )
    except Exception as e :
        logger .debug (f"Failed to load auth/settings/instructions on file load: {str(e)}")


@persistent 
def recover_ui_overlay_on_file_load (file ):
    """Recover UI overlay state after scene reload/file load using robust state management."""
    def delayed_recovery ():
        """Delayed recovery function to ensure scene is fully loaded."""
        try :

            from .ui .advanced .manager import ui_manager 
            from .ui .advanced .ui_state_manager import ui_state_manager 

            logger .info ("Starting robust UI recovery process")


            recovery_success =ui_state_manager .recover_ui_state (bpy .context ,ui_manager )

            if recovery_success :
                pass 
            else :
                logger .debug ("No UI state to recover or recovery not needed")

        except Exception as e :
            logger .error (f"Error in robust UI recovery: {e}")
            import traceback 
            logger .error (traceback .format_exc ())

        return None 


    try :
        bpy .app .timers .register (delayed_recovery ,first_interval =0.1 )
    except Exception as e :
        logger .error (f"Failed to schedule UI recovery: {e}")


@persistent 
def ensure_viewport_button_handler (file ):
    """Ensure viewport button modal handler is running after file load."""
    def delayed_handler_check ():
        """Check and start viewport button handler if needed."""
        try :

            if hasattr (bpy .context ,'window_manager')and bpy .context .window_manager :


                try :
                    bpy .ops .vibe4d .viewport_button_handler ('INVOKE_DEFAULT')
                    logger .debug ("Viewport button modal handler started after file load")
                except RuntimeError as e :
                    if "already running"in str (e ).lower ():
                        logger .debug ("Viewport button modal handler already running")
                    else :
                        logger .warning (f"Failed to start viewport button modal handler: {e}")
        except Exception as e :
            logger .debug (f"Error checking viewport button handler: {e}")
        return None 


    try :
        bpy .app .timers .register (delayed_handler_check ,first_interval =0.2 )
    except Exception as e :
        logger .debug (f"Failed to schedule viewport button handler check: {e}")


@persistent 
def auto_open_chat_ui_on_file_load (file ):
    """Automatically open the chat UI when a new scene is loaded."""

    if file :
        logger .debug (f"Skipping auto-open for existing file: {file}")
        return 

    def delayed_ui_open ():
        """Delayed UI opening function to ensure scene is fully loaded."""
        try :

            from .ui .advanced .manager import ui_manager 


            if ui_manager .is_ui_active ():
                logger .debug ("Chat UI already active, skipping auto-open")
                return None 


            target_area =None 
            for area in bpy .context .screen .areas :
                if area .type =='VIEW_3D':

                    if area .width >800 and area .height >600 :
                        target_area =area 
                        break 

            if not target_area :
                logger .debug ("No suitable 3D viewport found for auto-opening chat UI")
                return None 

            logger .info ("Auto-opening chat UI for new scene")


            try :
                with bpy .context .temp_override (area =target_area ):
                    bpy .ops .vibe4d .show_advanced_ui ()
                logger .info ("Successfully auto-opened chat UI")
            except Exception as e :
                logger .error (f"Failed to auto-open chat UI using operator: {e}")

        except Exception as e :
            logger .error (f"Error in auto-open chat UI handler: {e}")
            import traceback 
            logger .error (traceback .format_exc ())

        return None 


    try :
        bpy .app .timers .register (delayed_ui_open ,first_interval =0.1 )
    except Exception as e :
        logger .error (f"Failed to schedule auto-open chat UI: {e}")


def register ():
    """Register the addon."""
    try :
        logger .info ("=== Registering Vibe4D Addon ===")


        ui .register ()
        operators .register ()
        auth .register ()
        api .register ()
        llm .register ()
        engine .register ()
        utils .register ()


        if load_auth_and_settings_on_file_load not in bpy .app .handlers .load_post :
            bpy .app .handlers .load_post .append (load_auth_and_settings_on_file_load )


        if recover_ui_overlay_on_file_load not in bpy .app .handlers .load_post :
            bpy .app .handlers .load_post .append (recover_ui_overlay_on_file_load )


        if ensure_viewport_button_handler not in bpy .app .handlers .load_post :
            bpy .app .handlers .load_post .append (ensure_viewport_button_handler )


        if auto_open_chat_ui_on_file_load not in bpy .app .handlers .load_post :
            bpy .app .handlers .load_post .append (auto_open_chat_ui_on_file_load )


        def delayed_modal_handler_start ():
            """Start the viewport button modal handler after context is ready."""
            try :
                if hasattr (bpy .context ,'window_manager')and bpy .context .window_manager :
                    bpy .ops .vibe4d .viewport_button_handler ('INVOKE_DEFAULT')
                    logger .info ("Viewport button modal handler started")
                else :
                    logger .warning ("Context not ready for modal handler, will retry on file load")
            except Exception as e :
                logger .warning (f"Failed to start viewport button modal handler: {e}")
            return None 


        try :
            bpy .app .timers .register (delayed_modal_handler_start ,first_interval =0.1 )
        except Exception as e :
            logger .warning (f"Failed to schedule viewport button modal handler: {e}")


        try :
            if bpy .context .scene :

                auth_manager .initialize_auth (bpy .context )
                settings_manager .initialize_settings (bpy .context )
                instructions_manager .initialize_instructions (bpy .context )
        except Exception as e :
            logger .debug (f"Failed to load initial auth/settings/instructions: {str(e)}")

        logger .info ("Vibe4D addon registered successfully")

    except Exception as e :
        logger .error (f"Failed to register Vibe4D addon: {str(e)}")
        raise 


def unregister ():
    """Unregister the addon."""
    try :
        logger .info ("=== Unregistering Vibe4D Addon ===")


        try :
            if bpy .context .scene :

                settings_manager .save_settings (bpy .context )
                instructions_manager .save_instructions (bpy .context )
        except Exception as e :
            logger .debug (f"Failed to save settings/instructions on unregister: {str(e)}")


        if load_auth_and_settings_on_file_load in bpy .app .handlers .load_post :
            bpy .app .handlers .load_post .remove (load_auth_and_settings_on_file_load )
        if recover_ui_overlay_on_file_load in bpy .app .handlers .load_post :
            bpy .app .handlers .load_post .remove (recover_ui_overlay_on_file_load )
        if ensure_viewport_button_handler in bpy .app .handlers .load_post :
            bpy .app .handlers .load_post .remove (ensure_viewport_button_handler )
        if auto_open_chat_ui_on_file_load in bpy .app .handlers .load_post :
            bpy .app .handlers .load_post .remove (auto_open_chat_ui_on_file_load )


        utils .unregister ()
        engine .unregister ()
        llm .unregister ()
        api .unregister ()
        auth .unregister ()
        operators .unregister ()
        ui .unregister ()

        logger .info ("Vibe4D addon unregistered successfully")

    except Exception as e :
        logger .error (f"Failed to unregister Vibe4D addon: {str(e)}")


if __name__ =="__main__":
    register ()

