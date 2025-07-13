"""
Code execution operators for Vibe4D addon.

NOTE: These operators are deprecated as code execution now happens automatically 
via tool calls in the WebSocket client. They are kept for backward compatibility
but should not be used in the new flow.
"""

import bpy 
from bpy .types import Operator 

from ..utils .logger import logger 
from ..engine .executor import code_executor 


class VIBE4D_OT_accept_execution (Operator ):
    """Accept and commit code execution (DEPRECATED)."""

    bl_idname ="vibe4d.accept_execution"
    bl_label ="Accept Execution"
    bl_description ="Accept the executed code and keep changes (DEPRECATED - code execution is now automatic)"
    bl_options ={'REGISTER','UNDO'}

    def execute (self ,context ):
        """Execute acceptance (DEPRECATED)."""
        try :
            logger .warning ("Accept execution operator is deprecated - code execution is now automatic")
            self .report ({'WARNING'},"This operation is no longer needed - code execution is automatic")
            return {'CANCELLED'}

        except Exception as e :
            logger .error (f"Accept execution failed: {str(e)}")
            self .report ({'ERROR'},f"Operation failed: {str(e)}")
            return {'CANCELLED'}


class VIBE4D_OT_reject_execution (Operator ):
    """Reject and undo code execution (DEPRECATED)."""

    bl_idname ="vibe4d.reject_execution"
    bl_label ="Reject Execution"
    bl_description ="Reject the executed code and undo changes (DEPRECATED - code execution is now automatic)"
    bl_options ={'REGISTER','UNDO'}

    def execute (self ,context ):
        """Execute rejection (DEPRECATED)."""
        try :
            logger .warning ("Reject execution operator is deprecated - code execution is now automatic")
            self .report ({'WARNING'},"This operation is no longer needed - code execution is automatic")
            return {'CANCELLED'}

        except Exception as e :
            logger .error (f"Reject execution failed: {str(e)}")
            self .report ({'ERROR'},f"Operation failed: {str(e)}")
            return {'CANCELLED'}



classes =[
VIBE4D_OT_accept_execution ,
VIBE4D_OT_reject_execution ,
]