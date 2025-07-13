"""
Settings manager for Vibe4D addon.

Handles global persistence of user preferences like model selections.
"""

import bpy 
from .logger import logger 
from .storage import secure_storage 


class SettingsManager :
    """Manages global settings persistence."""

    def __init__ (self ):
        self .is_initialized =False 

    def initialize_settings (self ,context )->bool :
        """Initialize settings on addon startup."""
        if self .is_initialized :
            return True 

        try :

            saved_settings =secure_storage .load_settings ()

            if saved_settings :

                model =saved_settings .get ("model","gpt-4.1-mini")


                context .scene .vibe4d_model =model 

                logger .info (f"Loaded global settings: model={model}")
            else :
                logger .info ("No saved settings found, using defaults")

            self .is_initialized =True 
            return True 

        except Exception as e :
            logger .error (f"Settings initialization failed: {str(e)}")
            self .is_initialized =True 
            return False 

    def save_settings (self ,context )->bool :
        """Save current settings to persistent storage."""
        try :

            current_model =getattr (context .scene ,'vibe4d_model','gpt-4.1-mini')


            settings_data ={
            "model":current_model 
            }

            return secure_storage .save_all_settings (settings_data )

        except Exception as e :
            logger .error (f"Failed to save settings: {str(e)}")
            return False 

    def auto_save_settings (self ,context ):
        """Auto-save settings when they change (called from update callbacks)."""
        try :

            import threading 

            def save_in_background ():
                try :
                    self .save_settings (context )
                except Exception as e :
                    logger .debug (f"Background settings save failed: {str(e)}")

            thread =threading .Thread (target =save_in_background )
            thread .daemon =True 
            thread .start ()

        except Exception as e :
            logger .debug (f"Auto-save settings failed: {str(e)}")

    def clear_settings (self ,context )->bool :
        """Clear saved settings and reset to defaults."""
        try :

            secure_storage .clear_settings ()


            context .scene .vibe4d_model ="gpt-4.1-mini"

            logger .info ("Global settings cleared and reset to defaults")
            return True 

        except Exception as e :
            logger .error (f"Failed to clear settings: {str(e)}")
            return False 



settings_manager =SettingsManager ()