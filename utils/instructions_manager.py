"""
Custom instructions manager for Vibe4D addon.

Handles loading and saving custom instructions between sessions.
"""

import bpy 
from ..utils .logger import logger 
from ..utils .storage import secure_storage 


class InstructionsManager :
    """Manages custom instructions persistence."""

    def __init__ (self ):
        self .is_initialized =False 

    def initialize_instructions (self ,context )->bool :
        """Initialize custom instructions on addon startup."""
        if self .is_initialized :
            return True 

        logger .info ("Initializing custom instructions system")

        try :

            saved_instructions =secure_storage .load_custom_instructions ()

            if not saved_instructions :
                logger .info ("No saved custom instructions found")
                self .is_initialized =True 
                return True 


            if isinstance (saved_instructions ,dict ):

                instructions =saved_instructions .get ("agent",[])
            elif isinstance (saved_instructions ,list ):

                instructions =saved_instructions 
            else :
                logger .warning (f"Unknown instructions format: {type(saved_instructions)}")
                self .is_initialized =True 
                return True 


            context .scene .vibe4d_custom_instructions .clear ()
            context .scene .vibe4d_custom_instructions_index =0 


            for instruction_data in instructions :
                if isinstance (instruction_data ,dict ):
                    new_instruction =context .scene .vibe4d_custom_instructions .add ()
                    new_instruction .text =instruction_data .get ("text","")
                    new_instruction .enabled =instruction_data .get ("enabled",True )
                elif isinstance (instruction_data ,str ):

                    new_instruction =context .scene .vibe4d_custom_instructions .add ()
                    new_instruction .text =instruction_data 
                    new_instruction .enabled =True 

            logger .info (f"Loaded {len(instructions)} custom instructions")
            self .is_initialized =True 
            return True 

        except Exception as e :
            logger .error (f"Failed to initialize custom instructions: {str(e)}")
            self .is_initialized =True 
            return False 

    def save_instructions (self ,context )->bool :
        """Save current custom instructions to persistent storage."""
        try :
            instructions =[]

            for instruction in context .scene .vibe4d_custom_instructions :
                instructions .append ({
                "text":instruction .text ,
                "enabled":instruction .enabled 
                })


            instructions_data ={
            "agent":instructions 
            }

            return secure_storage .save_custom_instructions (instructions_data )

        except Exception as e :
            logger .error (f"Failed to save custom instructions: {str(e)}")
            return False 

    def clear_instructions (self ,context )->bool :
        """Clear custom instructions from both scene and storage."""
        try :

            context .scene .vibe4d_custom_instructions .clear ()
            context .scene .vibe4d_custom_instructions_index =0 


            secure_storage .clear_custom_instructions ()

            logger .info ("Custom instructions cleared")
            return True 

        except Exception as e :
            logger .error (f"Failed to clear custom instructions: {str(e)}")
            return False 

    def auto_save_instructions (self ,context ):
        """Auto-save instructions when they change (called from operators)."""
        try :

            import threading 

            def save_in_background ():
                try :
                    self .save_instructions (context )
                except Exception as e :
                    logger .debug (f"Background save failed: {str(e)}")

            thread =threading .Thread (target =save_in_background )
            thread .daemon =True 
            thread .start ()

        except Exception as e :
            logger .debug (f"Auto-save failed: {str(e)}")



instructions_manager =InstructionsManager ()