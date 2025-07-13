"""
Simplified History manager for Vibe4D addon.

Simple chat management: create new empty chats, store by ID, track current text input.
"""

import bpy 
import json 
import uuid 
from datetime import datetime 
from typing import Dict ,Any ,List ,Optional ,Union 
from .logger import logger 
import time 


class HistoryManager :
    """Simple chat history manager."""

    def __init__ (self ):
        """Initialize history manager."""

        self ._unsent_text_per_chat :Dict [str ,str ]={}
        pass 

    def save_unsent_text (self ,context ,chat_id :str =None ,text :str =None ):
        """Save unsent text for a specific chat."""
        try :
            if not chat_id :
                chat_id =getattr (context .scene ,'vibe4d_current_chat_id','')

            if not chat_id :
                logger .debug ("No chat ID available to save unsent text")
                return 


            if text is None :

                try :

                    from ..ui .advanced .manager import ui_manager 
                    if ui_manager and ui_manager .factory :
                        text =ui_manager .factory .get_send_text ()
                    else :
                        text =""
                except :
                    text =""


            self ._unsent_text_per_chat [chat_id ]=text 


            context .scene .vibe4d_current_text_input =text 

            logger .debug (f"Saved unsent text for chat {chat_id}: '{text[:50]}...' ({len(text)} chars)")

        except Exception as e :
            logger .error (f"Failed to save unsent text: {str(e)}")

    def restore_unsent_text (self ,context ,chat_id :str =None ):
        """Restore unsent text for a specific chat."""
        try :
            if not chat_id :
                chat_id =getattr (context .scene ,'vibe4d_current_chat_id','')

            if not chat_id :
                logger .debug ("No chat ID available to restore unsent text")
                return 


            saved_text =self ._unsent_text_per_chat .get (chat_id ,"")


            try :

                from ..ui .advanced .manager import ui_manager 
                if ui_manager and ui_manager .factory :

                    current_view =ui_manager .factory .views .get (ui_manager .factory .current_view )
                    if current_view and hasattr (current_view ,'components'):
                        text_input =current_view .components .get ('text_input')
                        if text_input and hasattr (text_input ,'set_text'):
                            text_input .set_text (saved_text )


                context .scene .vibe4d_current_text_input =saved_text 

                logger .debug (f"Restored unsent text for chat {chat_id}: '{saved_text[:50]}...' ({len(saved_text)} chars)")

            except Exception as e :
                logger .warning (f"Failed to restore unsent text to UI: {str(e)}")

                context .scene .vibe4d_current_text_input =saved_text 

        except Exception as e :
            logger .error (f"Failed to restore unsent text: {str(e)}")

    def clear_unsent_text (self ,context ,chat_id :str =None ):
        """Clear unsent text for a specific chat."""
        try :
            if not chat_id :
                chat_id =getattr (context .scene ,'vibe4d_current_chat_id','')

            if not chat_id :
                logger .debug ("No chat ID available to clear unsent text")
                return 


            if chat_id in self ._unsent_text_per_chat :
                del self ._unsent_text_per_chat [chat_id ]


            context .scene .vibe4d_current_text_input =""

            logger .debug (f"Cleared unsent text for chat {chat_id}")

        except Exception as e :
            logger .error (f"Failed to clear unsent text: {str(e)}")

    def create_new_chat (self ,context )->str :
        """Create a new empty chat and return its ID."""
        try :
            scene_name =context .scene .name if context .scene else 'None'
            logger .info (f"🔍 Creating new chat for scene '{scene_name}'")


            current_chat_id =getattr (context .scene ,'vibe4d_current_chat_id','')
            if current_chat_id :
                self .save_unsent_text (context ,current_chat_id )


            chat_id =f"chat_{int(datetime.now().timestamp() * 1000)}_{str(uuid.uuid4())[:8]}"


            context .scene .vibe4d_current_chat_id =chat_id 


            context .scene .vibe4d_current_text_input =""


            self .clear_unsent_text (context ,chat_id )


            try :
                from ..ui .advanced .manager import ui_manager 
                if ui_manager and ui_manager .factory :
                    current_view =ui_manager .factory .views .get (ui_manager .factory .current_view )
                    if current_view and hasattr (current_view ,'components'):
                        text_input =current_view .components .get ('text_input')
                        if text_input and hasattr (text_input ,'set_text'):
                            text_input .set_text ("")
            except Exception as e :
                logger .debug (f"Could not clear UI text input: {e}")

            logger .info (f"🔍 Created new chat: {chat_id} for scene '{scene_name}'")
            return chat_id 

        except Exception as e :
            logger .error (f"Failed to create new chat: {str(e)}")
            fallback_id =f"fallback_chat_{int(datetime.now().timestamp())}"
            logger .info (f"🔍 Using fallback chat ID: {fallback_id}")
            return fallback_id 

    def get_current_chat_id (self ,context )->str :
        """Get current chat ID, or create one if none exists."""
        scene_name =context .scene .name if context .scene else 'None'
        chat_id =getattr (context .scene ,'vibe4d_current_chat_id','')

        logger .debug (f"🔍 get_current_chat_id called for scene '{scene_name}', found chat_id: '{chat_id}'")

        if not chat_id :

            logger .debug (f"🔍 No chat ID found, searching for latest chat in scene '{scene_name}'")
            chat_id =self ._find_latest_chat_for_scene (context )
            if not chat_id :
                logger .debug (f"🔍 No latest chat found, creating new chat for scene '{scene_name}'")
                chat_id =self .create_new_chat (context )
            else :
                logger .debug (f"🔍 Found latest chat '{chat_id}', setting as current for scene '{scene_name}'")
                context .scene .vibe4d_current_chat_id =chat_id 

                self .restore_unsent_text (context ,chat_id )

        logger .debug (f"🔍 Returning chat_id: '{chat_id}' for scene '{scene_name}'")
        return chat_id 

    def add_message (self ,context ,role :str ,content :str ,tool_calls :List [Dict ]=None ,image_data :str =None ,tool_call_id :str =None )->bool :
        """Add a message to the current chat."""
        try :
            chat_id =self .get_current_chat_id (context )


            chat_messages =context .scene .vibe4d_chat_messages 
            new_message =chat_messages .add ()
            new_message .chat_id =chat_id 
            new_message .role =role 
            new_message .content =content 
            new_message .timestamp =datetime .now ().isoformat ()
            new_message .message_id =f"{role}_{int(datetime.now().timestamp() * 1000)}"


            if tool_calls :
                new_message .tool_calls_json =json .dumps (tool_calls )


            if image_data :
                new_message .image_data =image_data 


            if tool_call_id and role =="tool":
                new_message .tool_call_id =tool_call_id 

            logger .debug (f"Added {role} message to chat {chat_id}")
            return True 

        except Exception as e :
            logger .error (f"Failed to add message: {str(e)}")
            return False 

    def add_error_message (self ,context ,error_content :str )->bool :
        """Add an error message to the current chat."""
        try :
            chat_id =self .get_current_chat_id (context )


            chat_messages =context .scene .vibe4d_chat_messages 
            new_message =chat_messages .add ()
            new_message .chat_id =chat_id 
            new_message .role ="error"
            new_message .content =error_content 
            new_message .timestamp =datetime .now ().isoformat ()
            new_message .message_id =f"error_{int(datetime.now().timestamp() * 1000)}"

            logger .debug (f"Added error message to chat {chat_id}")
            return True 

        except Exception as e :
            logger .error (f"Failed to add error message: {str(e)}")
            return False 

    def get_chat_messages (self ,context ,chat_id :str =None )->List [Dict [str ,Any ]]:
        """Get messages for a chat in OpenAI format."""
        try :
            if not chat_id :
                chat_id =self .get_current_chat_id (context )


            if not chat_id :
                logger .debug ("No chat ID found - returning empty messages list")
                return []

            chat_messages =context .scene .vibe4d_chat_messages 


            indexed_messages =[]
            for i ,msg in enumerate (chat_messages ):
                if msg .chat_id ==chat_id :

                    has_image =hasattr (msg ,'image_data')and msg .image_data 

                    if has_image :

                        message_dict ={
                        "role":msg .role ,
                        "content":[
                        {
                        "type":"text",
                        "text":msg .content 
                        },
                        {
                        "type":"image_url",
                        "image_url":{
                        "url":msg .image_data ,
                        "detail":"high"
                        }
                        }
                        ]
                        }
                    else :

                        message_dict ={
                        "role":msg .role ,
                        "content":msg .content 
                        }


                    if msg .role =="assistant"and msg .tool_calls_json :
                        try :
                            message_dict ["tool_calls"]=json .loads (msg .tool_calls_json )
                        except json .JSONDecodeError :
                            logger .warning (f"Failed to parse tool calls for message {msg.message_id}")


                    if msg .role =="tool"and hasattr (msg ,'tool_call_id')and msg .tool_call_id :
                        message_dict ["tool_call_id"]=msg .tool_call_id 


                    indexed_messages .append ((i ,message_dict ))


            indexed_messages .sort (key =lambda x :x [0 ])


            messages =[msg_dict for index ,msg_dict in indexed_messages ]


            if messages :
                logger .debug (f"Found {len(messages)} messages for chat {chat_id} in scene {context.scene.name}")
            else :
                logger .debug (f"No messages found for chat {chat_id} in scene {context.scene.name}")

            return messages 

        except Exception as e :
            logger .error (f"Failed to get chat messages: {str(e)}")
            return []

    def get_all_chats (self ,context )->List [Dict [str ,Any ]]:
        """Get all chats for the current scene."""
        try :
            scene_name =context .scene .name if context .scene else 'None'
            chat_messages =context .scene .vibe4d_chat_messages 
            chats ={}

            logger .debug (f"🔍 get_all_chats called for scene '{scene_name}', found {len(chat_messages)} total messages")


            for msg in chat_messages :
                chat_id =msg .chat_id 
                if chat_id not in chats :
                    chats [chat_id ]={
                    'chat_id':chat_id ,
                    'title':'New conversation',
                    'last_message_time':msg .timestamp ,
                    'message_count':0 
                    }

                chats [chat_id ]['message_count']+=1 
                chats [chat_id ]['last_message_time']=max (chats [chat_id ]['last_message_time'],msg .timestamp )


                if msg .role =='user'and chats [chat_id ]['title']=='New conversation':
                    title =msg .content .strip ().split ('\n')[0 ]
                    if len (title )>50 :
                        title =title [:50 ]+"..."
                    chats [chat_id ]['title']=title 


            chat_list =list (chats .values ())
            chat_list .sort (key =lambda c :c ['last_message_time'],reverse =True )

            logger .debug (f"🔍 Found {len(chat_list)} chats in scene '{scene_name}': {[c['chat_id'] for c in chat_list]}")

            return chat_list 

        except Exception as e :
            logger .error (f"Failed to get all chats: {str(e)}")
            return []

    def save_current_text_input (self ,context ,text :str ):
        """Save current unsent text input."""
        try :
            context .scene .vibe4d_current_text_input =text 
        except Exception as e :
            logger .error (f"Failed to save text input: {str(e)}")

    def get_current_text_input (self ,context )->str :
        """Get current unsent text input."""
        try :
            return getattr (context .scene ,'vibe4d_current_text_input','')
        except Exception as e :
            logger .error (f"Failed to get text input: {str(e)}")
            return ""

    def switch_to_chat (self ,context ,chat_id :str ):
        """Switch to a specific chat, saving current unsent text and restoring target chat's unsent text."""
        try :
            scene_name =context .scene .name if context .scene else 'None'
            current_chat_id =getattr (context .scene ,'vibe4d_current_chat_id','')

            if current_chat_id ==chat_id :
                logger .debug (f"Already on chat {chat_id}")
                return 

            logger .info (f"🔍 Switching from chat '{current_chat_id}' to chat '{chat_id}' in scene '{scene_name}'")


            if current_chat_id :
                self .save_unsent_text (context ,current_chat_id )


            context .scene .vibe4d_current_chat_id =chat_id 


            self .restore_unsent_text (context ,chat_id )

            logger .info (f"🔍 Switched to chat: {chat_id} in scene '{scene_name}'")

        except Exception as e :
            logger .error (f"Failed to switch to chat: {str(e)}")

    def on_scene_change (self ,context ):
        """Called when scene changes - load latest chat for this scene."""
        try :
            scene_name =context .scene .name 
            logger .info (f"Processing scene change to: {scene_name}")


            latest_chat =self ._find_latest_chat_for_scene (context )

            if latest_chat :
                context .scene .vibe4d_current_chat_id =latest_chat 

                logger .info (f"Scene change: loaded latest chat {latest_chat} for scene {scene_name}")
            else :

                context .scene .vibe4d_current_chat_id =""
                context .scene .vibe4d_current_text_input =""
                logger .info (f"Scene change: no chats found for scene {scene_name}, cleared state")



            time .sleep (0.01 )

        except Exception as e :
            logger .error (f"Failed to handle scene change: {str(e)}")

            try :
                context .scene .vibe4d_current_chat_id =""
                context .scene .vibe4d_current_text_input =""
                logger .info ("Cleared chat state due to scene change error")
            except :
                pass 

    def _find_latest_chat_for_scene (self ,context )->str :
        """Find the latest chat for the current scene."""
        try :
            chats =self .get_all_chats (context )
            if chats :
                return chats [0 ]['chat_id']
            return ""
        except Exception as e :
            logger .error (f"Failed to find latest chat: {str(e)}")
            return ""

    def clear_chat (self ,context ,chat_id :str =None ):
        """Clear a specific chat or current chat."""
        try :
            if not chat_id :
                chat_id =self .get_current_chat_id (context )

            chat_messages =context .scene .vibe4d_chat_messages 


            messages_to_remove =[]
            for i ,msg in enumerate (chat_messages ):
                if msg .chat_id ==chat_id :
                    messages_to_remove .append (i )


            for i in reversed (messages_to_remove ):
                chat_messages .remove (i )

            logger .info (f"Cleared {len(messages_to_remove)} messages from chat {chat_id}")

        except Exception as e :
            logger .error (f"Failed to clear chat: {str(e)}")

    def add_message_after_tool_response (self ,context ,role :str ,content :str ,tool_call_id :str ,image_data :str =None )->bool :
        """Add a message immediately after a specific tool response in chronological order."""
        try :
            chat_id =self .get_current_chat_id (context )
            chat_messages =context .scene .vibe4d_chat_messages 


            tool_response_index =-1 
            for i ,msg in enumerate (chat_messages ):
                if (msg .chat_id ==chat_id and 
                msg .role =="tool"and 
                hasattr (msg ,'tool_call_id')and 
                msg .tool_call_id ==tool_call_id ):
                    tool_response_index =i 
                    break 

            if tool_response_index ==-1 :
                logger .warning (f"Could not find tool response with call_id {tool_call_id}, adding message normally")
                return self .add_message (context ,role ,content ,image_data =image_data )


            new_message =chat_messages .add ()
            new_message .chat_id =chat_id 
            new_message .role =role 
            new_message .content =content 
            new_message .timestamp =datetime .now ().isoformat ()
            new_message .message_id =f"{role}_{int(datetime.now().timestamp() * 1000)}"


            if image_data :
                new_message .image_data =image_data 

            new_message_index =len (chat_messages )-1 
            target_index =tool_response_index +1 


            current_index =new_message_index 


            while current_index >target_index :
                chat_messages .move (current_index ,current_index -1 )
                current_index -=1 

            logger .info (f"Added {role} message after tool response {tool_call_id} at position {target_index}")
            return True 

        except Exception as e :
            logger .error (f"Failed to add message after tool response: {str(e)}")
            import traceback 
            logger .error (traceback .format_exc ())
            return False 


history_manager =HistoryManager ()