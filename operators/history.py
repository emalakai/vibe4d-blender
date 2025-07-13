"""
Chat message management operators for Vibe4D addon.

Handles chat message operations like clearing chat history.
"""

import bpy 
from bpy .types import Operator 

from ..utils .logger import logger 
from ..utils .history_manager import history_manager 


class VIBE4D_OT_clear_chat_messages (Operator ):
    """Clear all chat messages."""

    bl_idname ="vibe4d.clear_chat_messages"
    bl_label ="Clear All Chat Messages"
    bl_description ="Clear all chat messages from all sessions"
    bl_options ={'REGISTER','UNDO'}

    def invoke (self ,context ,event ):
        """Show confirmation dialog."""
        return context .window_manager .invoke_confirm (self ,event )

    def execute (self ,context ):
        """Execute chat message clearing."""
        try :
            history_manager .clear_all_messages (context )

            self .report ({'INFO'},"Cleared all chat messages")
            return {'FINISHED'}

        except Exception as e :
            logger .error (f"Failed to clear chat messages: {str(e)}")
            self .report ({'ERROR'},f"Failed to clear chat messages: {str(e)}")
            return {'CANCELLED'}


class VIBE4D_OT_clear_mode_chat_messages (Operator ):
    """Clear chat messages for a specific mode."""

    bl_idname ="vibe4d.clear_mode_chat_messages"
    bl_label ="Clear Mode Chat Messages"
    bl_description ="Clear chat messages for the current mode"
    bl_options ={'REGISTER','UNDO'}

    mode :bpy .props .EnumProperty (
    name ="Mode",
    description ="Mode to clear chat messages for",
    items =[
    ('agent','Agent','Clear agent mode chat messages'),
    ('ask','Ask','Clear ask mode chat messages')
    ],
    default ='agent'
    )

    def invoke (self ,context ,event ):
        """Show confirmation dialog."""

        return context .window_manager .invoke_confirm (self ,event )

    def execute (self ,context ):
        """Execute mode-specific chat message clearing."""
        try :

            history_manager .clear_session_messages (context ,self .mode )

            mode_text ="agent"if self .mode =='agent'else "ask"
            self .report ({'INFO'},f"Cleared {mode_text} mode chat messages")

            return {'FINISHED'}

        except Exception as e :
            logger .error (f"Failed to clear {self.mode} chat messages: {str(e)}")
            self .report ({'ERROR'},f"Failed to clear chat messages: {str(e)}")
            return {'CANCELLED'}


class VIBE4D_OT_clear_current_chat_session (Operator ):
    """Clear messages from the current chat."""

    bl_idname ="vibe4d.clear_current_chat"
    bl_label ="Clear Current Chat"
    bl_description ="Clear all messages from the current chat"
    bl_options ={'REGISTER'}

    def execute (self ,context ):
        """Clear current chat."""
        try :

            chat_id =history_manager .get_current_chat_id (context )
            if not chat_id :
                self .report ({'INFO'},"No active chat to clear")
                return {'FINISHED'}


            history_manager .clear_chat (context ,chat_id =chat_id )

            self .report ({'INFO'},"Current chat cleared")
            logger .info (f"Cleared current chat: {chat_id}")

            return {'FINISHED'}

        except Exception as e :
            logger .error (f"Failed to clear current chat: {str(e)}")
            self .report ({'ERROR'},f"Failed to clear chat: {str(e)}")
            return {'CANCELLED'}


class VIBE4D_OT_start_new_chat (Operator ):
    """Start a new chat."""

    bl_idname ="vibe4d.start_new_chat"
    bl_label ="New Chat"
    bl_description ="Start a new chat"
    bl_options ={'REGISTER'}

    def execute (self ,context ):
        """Start a new chat."""
        try :
            chat_id =history_manager .create_new_chat (context )

            self .report ({'INFO'},"Started new chat")
            logger .info (f"Started new chat: {chat_id}")

            return {'FINISHED'}

        except Exception as e :
            logger .error (f"Failed to start new chat: {str(e)}")
            self .report ({'ERROR'},f"Failed to start new chat: {str(e)}")
            return {'CANCELLED'}



classes =[
VIBE4D_OT_clear_chat_messages ,
VIBE4D_OT_clear_mode_chat_messages ,
VIBE4D_OT_clear_current_chat_session ,
VIBE4D_OT_start_new_chat ,
]