"""
Debug operators for development and testing.
"""

import bpy 
import json 
from bpy .types import Operator 
import logging 

from ..llm .request_builder import LLMRequestBuilder 
from ..utils .logger import logger 

logger =logging .getLogger (__name__ )


class DEBUG_OT_print_agent_request (Operator ):
    """Build and print agent LLM request to console."""

    bl_idname ="debug.print_agent_request"
    bl_label ="Print Agent Request"
    bl_description ="Build and print agent LLM request to console for debugging"
    bl_options ={'REGISTER'}

    def execute (self ,context ):
        """Build and print agent request."""
        try :

            user_id =getattr (context .window_manager ,'vibe4d_user_id','debug_user')
            token =getattr (context .window_manager ,'vibe4d_token','debug_token')


            prompt =getattr (context .scene ,'vibe4d_prompt','Debug test prompt')
            if not prompt .strip ():
                prompt ="Create a debug cube"


            request =LLMRequestBuilder .build_request (
            context =context ,
            prompt =prompt ,
            user_id =user_id ,
            token =token ,
            mode ="agent"
            )


            print ("="*80 )

            json_output =json .dumps (request ,ensure_ascii =False )
            print (json_output )

            print ("="*80 )
            print ("DEBUG: json request, size: ",len (json_output )/1024 ,"KB")


            context .window_manager .clipboard =json_output 
            print ("Request copied to clipboard!")
            self .report ({'INFO'},f"JSON request copied to clipboard (size: {len(json_output)/1024:.1f}KB)")

            print ("="*80 )

        except Exception as e :
            error_msg =f"Failed to build agent request: {str(e)}"
            logger .error (error_msg )
            self .report ({'ERROR'},error_msg )

        return {'FINISHED'}



classes =[
DEBUG_OT_print_agent_request ,
]


def register ():
    for cls in classes :
        bpy .utils .register_class (cls )


def unregister ():
    for cls in classes :
        bpy .utils .unregister_class (cls )