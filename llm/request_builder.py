"""
Request builder for LLM API calls.

Prepares requests in the required format for the AI service.
"""

import bpy 
from typing import Dict ,Any ,Optional ,List 

from ..utils .logger import logger 


class LLMRequestBuilder :
    """Builds LLM API requests in the required format."""

    DEFAULT_MODEL ="gpt-4.1-mini"
    SOFTWARE_NAME ="blender"

    @staticmethod 
    def _get_addon_info ()->Dict [str ,Any ]:
        """Extract addon information from bl_info."""
        try :

            import sys 
            addon_module =None 


            try :

                current_package =__name__ .split ('.')[0 ]
                addon_module =sys .modules .get (current_package )


                if addon_module and hasattr (addon_module ,'bl_info'):
                    logger .debug (f"Found addon module via package name: {current_package}")
                else :
                    addon_module =None 
            except Exception as e :
                logger .debug (f"Failed to get module via package name: {str(e)}")


            if not addon_module :
                for module_name ,module in sys .modules .items ():
                    if (hasattr (module ,'bl_info')and 
                    isinstance (module .bl_info ,dict )and 
                    module .bl_info .get ('name')=='Vibe4D'):
                        addon_module =module 
                        logger .debug (f"Found addon module via name search: {module_name}")
                        break 


            if not addon_module :
                for module_name ,module in sys .modules .items ():
                    if ('vibe4d'in module_name .lower ()and 
                    hasattr (module ,'bl_info')and 
                    isinstance (module .bl_info ,dict )):
                        addon_module =module 
                        logger .debug (f"Found addon module via name pattern: {module_name}")
                        break 

            if addon_module and hasattr (addon_module ,'bl_info'):
                bl_info =addon_module .bl_info 


                version_tuple =bl_info .get ('version',(0 ,0 ,0 ))
                version_str ='.'.join (map (str ,version_tuple ))

                return {
                "name":bl_info .get ('name','Unknown Addon'),
                "version":version_str ,
                "author":bl_info .get ('author','Unknown'),
                "description":bl_info .get ('description',''),
                "category":bl_info .get ('category','Unknown')
                }


            logger .warning ("Could not find bl_info, using fallback addon information")
            return {
            "name":"Vibe4D",
            "version":"1.0.0",
            "author":"Vibe4D Team",
            "description":"AI-powered Blender addon",
            "category":"Development"
            }

        except Exception as e :
            logger .error (f"Failed to extract addon info: {str(e)}")

            return {
            "name":"Vibe4D",
            "version":"1.0.0",
            "author":"Vibe4D Team",
            "description":"AI-powered Blender addon",
            "category":"Development"
            }

    @staticmethod 
    def _get_model_and_instructions (context ):
        """Get model and custom instructions from unified properties."""

        model_prop =getattr (context .scene ,'vibe4d_model',LLMRequestBuilder .DEFAULT_MODEL )


        instructions =getattr (context .scene ,'vibe4d_custom_instructions',[])

        return model_prop ,instructions 

    @staticmethod 
    def build_chat_request (
    context ,
    prompt :str ,
    user_id :str ,
    token :str ,
    model :Optional [str ]=None ,
    include_history :bool =True 
    )->Dict [str ,Any ]:
        """
        Build chat request with message history for /vibe4d/v1/chat endpoint.
        
        Args:
            context: Blender context object
            prompt: User's prompt/question
            user_id: Authenticated user ID
            token: Authentication token
            model: Model to use (defaults to unified model selection)
            include_history: Whether to include chat history in messages
            
        Returns:
            Dict containing the formatted chat request
        """
        try :

            selected_model ,raw_instructions =LLMRequestBuilder ._get_model_and_instructions (context )
            selected_model =model or selected_model 


            instructions =LLMRequestBuilder ._get_enabled_instructions_from_collection (raw_instructions )


            blender_version =LLMRequestBuilder ._get_blender_version ()


            addon_info =LLMRequestBuilder ._get_addon_info ()


            messages =[]

            if include_history :

                recent_messages =LLMRequestBuilder ._get_chat_messages_from_history (context ,limit =10 )
                messages .extend (recent_messages )


            messages .append ({
            "role":"user",
            "content":prompt .strip ()
            })


            try :
                from ..engine .query import scene_query_engine 
                schema_summary =scene_query_engine .get_llm_friendly_schema_summary (context )
            except Exception as e :
                logger .warning (f"Failed to get schema summary: {str(e)}")
                schema_summary =""


            request ={
            "user":user_id ,
            "token":token ,
            "messages":messages ,
            "model":selected_model ,
            "instructions":instructions ,
            "tables_schemas_summary":schema_summary ,
            "software":{
            "name":LLMRequestBuilder .SOFTWARE_NAME ,
            "version":blender_version 
            },
            "addon":{
            "version":addon_info ["version"],
            "name":addon_info ["name"]
            }
            }

            logger .debug (f"Built chat request with {len(messages)} messages")
            return request 

        except Exception as e :
            logger .error (f"Failed to build chat request: {str(e)}")
            raise 

    @staticmethod 
    def build_request (
    context ,
    prompt :str ,
    user_id :str ,
    token :str ,
    model :Optional [str ]=None 
    )->Dict [str ,Any ]:
        """
        Build LLM request.
        
        Args:
            context: Blender context object
            prompt: User's prompt/question
            user_id: Authenticated user ID
            token: Authentication token
            model: Model to use (defaults to unified model selection)
            
        Returns:
            Dict containing the formatted request
        """
        return LLMRequestBuilder .build_chat_request (
        context =context ,
        prompt =prompt ,
        user_id =user_id ,
        token =token ,
        model =model ,
        include_history =True 
        )

    @staticmethod 
    def _get_chat_messages_from_history (context ,limit :int =10 )->List [Dict [str ,Any ]]:
        """Get recent chat messages from history."""
        try :
            from ..utils .history_manager import history_manager 

            messages =history_manager .get_chat_messages (context )


            return messages [-limit :]if len (messages )>limit else messages 

        except Exception as e :
            logger .error (f"Failed to get chat messages from history: {str(e)}")
            return []

    @staticmethod 
    def _get_blender_version ()->str :
        """Get Blender version string."""
        try :
            version =bpy .app .version 

            return f"{version[0]}.{version[1]}"
        except Exception as e :
            logger .error (f"Failed to get Blender version: {str(e)}")
            return "4.4"

    @staticmethod 
    def _get_enabled_instructions (context )->List [str ]:
        """Get list of enabled custom instructions."""
        try :
            instructions =[]
            custom_instructions =getattr (context .scene ,'vibe4d_custom_instructions',[])

            for instruction in custom_instructions :
                if instruction .enabled and instruction .text .strip ():
                    instructions .append (instruction .text .strip ())

            logger .debug (f"Found {len(instructions)} enabled custom instructions")
            return instructions 

        except Exception as e :
            logger .error (f"Failed to get custom instructions: {str(e)}")
            return []

    @staticmethod 
    def _get_enabled_instructions_from_collection (custom_instructions )->List [str ]:
        """Get list of enabled custom instructions from a specific collection."""
        try :
            instructions =[]

            for instruction in custom_instructions :
                if instruction .enabled and instruction .text .strip ():
                    instructions .append (instruction .text .strip ())

            logger .debug (f"Found {len(instructions)} enabled custom instructions from collection")
            return instructions 

        except Exception as e :
            logger .error (f"Failed to get custom instructions from collection: {str(e)}")
            return []