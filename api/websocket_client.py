"""
WebSocket client for streaming LLM API communication.

Handles real-time communication with Emalak AI streaming API.
"""

import json 
import threading 
from typing import Dict ,Any ,Callable ,Optional ,List 
import time 

from ..packages .websocket import WebSocketApp 
from ..utils .logger import logger 
from ..utils .json_utils import BlenderJSONEncoder 


def _is_websocket_connection_error (error_message :str )->bool :
    """
    Check if an error message indicates a websocket connection problem.
    
    Args:
        error_message: The error message to check
        
    Returns:
        True if this is a websocket connection error
    """
    error_lower =error_message .lower ()


    websocket_error_patterns =[
    'websocket',
    'connection refused',
    'connection failed',
    'connection closed',
    'connection timeout',
    'connection reset',
    'connection aborted',
    'connection error',
    'network unreachable',
    'network error',
    'timeout',
    'timed out',
    'unreachable',
    'refused',
    'reset by peer',
    'broken pipe',
    'no route to host',
    'host unreachable',
    'socket',
    'ssl',
    'certificate',
    'handshake',
    'protocol error',
    'ping/pong timed out'
    ]

    return any (pattern in error_lower for pattern in websocket_error_patterns )


def _get_user_friendly_websocket_error (error_message :str )->str :
    """
    Convert websocket errors to user-friendly message.
    
    Args:
        error_message: The original error message
        
    Returns:
        User-friendly error message for websocket errors, or original message if not a websocket error
    """
    if _is_websocket_connection_error (error_message ):
        return "Connection problems. Try again later"
    return error_message 


class StreamingResponse :
    """Container for streaming response data."""

    def __init__ (self ):
        self .output_content =""
        self .final_code =""
        self .status_messages =[]
        self .progress =0 
        self .stage =""
        self .success =False 
        self .error =None 
        self .message_id =None 
        self .request_id =None 
        self .usage_info ={}
        self .is_complete =False 
        self .tool_calls =[]
        self .assistant_message_added =False 

        self .current_tool_call =None 
        self .tool_call_started =False 
        self .tool_call_completed =False 
        self .tool_events =[]
        self .web_search_events =[]
        self .current_tool_name =None 
        self .current_tool_status =None 
        self .current_tool_success =False 
        self .current_search_query =None 
        self .current_search_status =None 
        self .current_search_success =False 
        self .current_search_result_count =0 
        self .current_tool_call_id =None 
        self .current_tool_arguments =None 
        self .error_code =None 
        self .error_retryable =False 
        self .error_suggestions =[]


class LLMWebSocketClient :
    """WebSocket client for streaming LLM API communication."""

    WEBSOCKET_URL ="wss://api.emalakai.com/vibe4d/v1/chat"

    def __init__ (self ):
        self .ws =None 
        self .response =None 
        self .on_progress_callback =None 
        self .on_complete_callback =None 
        self .on_error_callback =None 
        self ._connection_timeout =30 
        self ._response_timeout =300 
        self ._pending_tool_calls ={}
        self ._last_progress_content_length =0 

    def send_prompt_request (
    self ,
    request_data :Dict [str ,Any ],
    on_progress :Optional [Callable [[StreamingResponse ],None ]]=None ,
    on_complete :Optional [Callable [[StreamingResponse ],None ]]=None ,
    on_error :Optional [Callable [[str ],None ]]=None 
    )->bool :
        """
        Send prompt request via WebSocket and handle streaming response.
        
        Args:
            request_data: The LLM request data
            on_progress: Callback for progress updates
            on_complete: Callback when response is complete
            on_error: Callback for errors
            
        Returns:
            True if connection established successfully
        """
        try :
            logger .info ("Connecting to LLM WebSocket API")


            self .on_progress_callback =on_progress 
            self .on_complete_callback =on_complete 
            self .on_error_callback =on_error 


            self .response =StreamingResponse ()


            self .ws =WebSocketApp (
            self .WEBSOCKET_URL ,
            on_open =self ._on_open ,
            on_message =self ._on_message ,
            on_error =self ._on_error ,
            on_close =self ._on_close 
            )


            self ._request_data =request_data 


            ws_thread =threading .Thread (
            target =self .ws .run_forever ,
            kwargs ={'ping_interval':30 ,'ping_timeout':10 }
            )
            ws_thread .daemon =True 
            ws_thread .start ()

            return True 

        except Exception as e :
            logger .error (f"Failed to start WebSocket connection: {str(e)}")
            if self .on_error_callback :

                user_friendly_error =_get_user_friendly_websocket_error (f"Connection failed: {str(e)}")
                self .on_error_callback (user_friendly_error )
            return False 

    def _on_open (self ,ws ):
        """Handle WebSocket connection opened."""
        logger .info ("WebSocket connection established")

        try :

            message =json .dumps (self ._request_data ,cls =BlenderJSONEncoder )
            ws .send (message )
            logger .debug (f"Sent request: {message}")

        except Exception as e :
            logger .error (f"Failed to send request: {str(e)}")
            if self .on_error_callback :

                user_friendly_error =_get_user_friendly_websocket_error (f"Failed to send request: {str(e)}")
                self .on_error_callback (user_friendly_error )

    def _on_message (self ,ws ,message ):
        """Handle incoming WebSocket message."""
        try :

            data =json .loads (message )
            event =data .get ("event","")
            event_data =data .get ("data",{})

            logger .debug (f"Received event: {event} with data: {event_data}")


            if event =="status":
                self ._handle_status_event (event_data )
            elif event =="output_chunk":
                self ._handle_output_chunk_event (event_data )
            elif event =="tool_call_request":
                self ._handle_tool_call_request_event (event_data )
            elif event =="tool_started":
                self ._handle_tool_started_event (event_data )
            elif event =="tool_completed":
                self ._handle_tool_completed_event (event_data )
            elif event =="web_search_started":
                self ._handle_web_search_started_event (event_data )
            elif event =="web_search_completed":
                self ._handle_web_search_completed_event (event_data )
            elif event =="response_in_progress":
                self ._handle_response_in_progress_event (event_data )
            elif event =="content_part_added":
                self ._handle_content_part_added_event (event_data )
            elif event =="output_text_done":
                self ._handle_output_text_done_event (event_data )
            elif event =="content_part_done":
                self ._handle_content_part_done_event (event_data )
            elif event =="output_item_done":
                self ._handle_output_item_done_event (event_data )
            elif event =="code":
                self ._handle_code_event (event_data )
            elif event =="result":
                self ._handle_result_event (event_data )
            elif event =="request_id":
                self ._handle_request_id_event (event_data )
            elif event =="error":
                self ._handle_error_event (event_data )
            else :
                logger .warning (f"Unknown event type: {event}")


            if self .on_progress_callback and self .response and event !="error":

                content_changed =(hasattr (self .response ,'output_content')and 
                len (self .response .output_content )!=self ._last_progress_content_length )
                tool_state_changed =(hasattr (self .response ,'tool_call_started')or 
                hasattr (self .response ,'tool_call_completed'))
                special_event =event in ["status","tool_call_request","tool_started","tool_completed",
                "web_search_started","web_search_completed","response_in_progress",
                "content_part_added","output_text_done","content_part_done","output_item_done"]

                if content_changed or tool_state_changed or special_event :
                    self .on_progress_callback (self .response )
                    self ._last_progress_content_length =len (self .response .output_content )if hasattr (self .response ,'output_content')else 0 

        except json .JSONDecodeError as e :
            logger .error (f"Failed to parse WebSocket message: {str(e)}")
        except Exception as e :
            logger .error (f"Error handling WebSocket message: {str(e)}")

    def _handle_status_event (self ,data :Dict [str ,Any ]):
        """Handle status event."""
        message =data .get ("message","")
        progress =data .get ("progress",0 )
        stage =data .get ("stage","")

        self .response .status_messages .append (message )
        self .response .progress =progress 
        self .response .stage =stage 

        logger .info (f"Status: {message} ({progress}% - {stage})")

    def _handle_output_chunk_event (self ,data :Dict [str ,Any ]):
        """Handle unified output chunk event (text streaming)."""
        content =data .get ("content","")
        self .response .output_content +=content 

    def _handle_tool_call_request_event (self ,data :Dict [str ,Any ]):
        """
        Handle tool call request event.
        The AI wants to execute a tool - we need to execute it and send back the result.
        """
        try :
            call_id =data .get ("call_id","")
            tool_id =data .get ("id","")
            tool_name =data .get ("name","")
            arguments_json =data .get ("arguments","{}")


            arguments =json .loads (arguments_json )


            self .response .current_tool_call ={
            "name":tool_name ,
            "call_id":call_id ,
            "arguments":arguments 
            }
            self .response .tool_call_started =True 
            self .response .tool_call_completed =False 
            self .response .current_tool_call_id =call_id 
            self .response .current_tool_name =tool_name 
            self .response .current_tool_status ="requested"
            self .response .current_tool_arguments =arguments_json 


            if tool_name =="execute"and "code"in arguments :
                self .response .final_code =arguments ["code"]



            try :
                from ..ui .advanced .manager import ui_manager 


                tool_call_data ={
                'call_id':call_id ,
                'tool_name':tool_name ,
                'arguments':arguments_json 
                }
                ui_manager .handle_external_tool_call (tool_call_data )


                if self .response .output_content or self .response .message_id :
                    ui_manager ._track_assistant_message (
                    self .response .message_id or f"msg_{int(time.time() * 1000)}",
                    self .response .output_content or ""
                    )

                logger .debug (f"🔗 Used centralized tracking for tool call: {tool_name}")

            except Exception as e :
                logger .warning (f"Failed to use centralized tool call tracking: {str(e)}")

                logger .info ("❌ Fallback tool call history saving is disabled - using centralized tracking only")


            def execute_on_main_thread ():
                try :

                    logger .info (f"execute_on_main_thread: call_id='{call_id}', tool_name='{tool_name}'")


                    from ..engine .tools import tools_manager 
                    from ..utils .history_manager import history_manager 
                    import bpy 


                    context =bpy .context 


                    try :
                        success ,result_data =tools_manager .handle_tool_call (tool_name ,arguments ,bpy .context )



                        backend_result =result_data 


                        ui_status_message =None 


                        if tool_name in ["viewport","see_viewport","add_viewport_render","see_render"]:
                            if success and isinstance (result_data ,dict ):

                                if "result"in result_data :
                                    tool_result =result_data ["result"]
                                    if isinstance (tool_result ,dict )and "data_uri"in tool_result :

                                        image_data_uri =tool_result ["data_uri"]
                                        image_width =tool_result .get ("width",0 )
                                        image_height =tool_result .get ("height",0 )

                                        ui_status_message =f"Captured {image_width}x{image_height} image successfully"



                                        image_message_text ="[Render captured]"if tool_name =="see_render"else "[Viewport captured]"


                                        backend_result ["_image_data"]={
                                        "data_uri":image_data_uri ,
                                        "message_text":image_message_text 
                                        }

                                        logger .info (f"Prepared image data for centralized tracking: {image_message_text}")
                                    else :
                                        ui_status_message ="Image capture failed"
                                else :
                                    ui_status_message ="Image capture failed"
                            else :

                                ui_status_message =str (result_data .get ("result","Image capture failed"))if not success else "Image capture failed"
                        else :

                            if success :

                                if tool_name =="execute":

                                    tool_result =result_data .get ("result","")
                                    if isinstance (tool_result ,str )and tool_result .strip ():
                                        ui_status_message =tool_result .strip ()
                                    else :
                                        ui_status_message ="Code executed successfully"
                                elif tool_name =="query":


                                    tool_result =result_data .get ("result",{})
                                    if isinstance (tool_result ,dict )and "count"in tool_result :
                                        count =tool_result .get ("count",0 )
                                        ui_status_message =f"Found {count} results"
                                    else :
                                        ui_status_message ="Query executed successfully"
                                elif tool_name =="scene_context":

                                    ui_status_message ="Scene context retrieved"
                                else :

                                    ui_status_message ="Tool executed successfully"
                            else :
                                ui_status_message =str (result_data .get ("result","Tool execution failed"))

                    except Exception as e :
                        logger .error (f"Error executing tool '{tool_name}' on main thread: {str(e)}")

                        self .response .tool_call_completed =True 
                        backend_result ={
                        "status":"error",
                        "result":f"Tool call execution failed: {str(e)}"
                        }
                        ui_status_message =f"Tool call execution failed: {str(e)}"
                        self ._send_tool_call_response (call_id ,backend_result )


                        if self .on_progress_callback :
                            self .on_progress_callback (self .response )


                    self .response .tool_call_completed =True 


                    try :
                        from ..ui .advanced .manager import ui_manager 


                        image_data =backend_result .get ("_image_data")


                        tool_response_data ={
                        'call_id':call_id ,
                        'content':json .dumps (backend_result ),
                        'success':backend_result .get ("status")=="success",
                        'ui_message':ui_status_message ,
                        'original_result':backend_result ,
                        'image_data':image_data 
                        }
                        ui_manager .handle_external_tool_response (tool_response_data )

                        logger .debug (f"🔗 Used centralized tracking for tool response: {call_id}")

                    except Exception as e :
                        logger .warning (f"Failed to use centralized tool response tracking: {str(e)}")


                    if "_image_data"in backend_result :
                        del backend_result ["_image_data"]


                    logger .info (f"Sending tool call response to server: call_id='{call_id}'")
                    self ._send_tool_call_response (call_id ,backend_result )


                    if self .on_progress_callback :
                        self .on_progress_callback (self .response )

                except Exception as e :
                    logger .error (f"Error executing tool '{tool_name}' on main thread: {str(e)}")

                    self .response .tool_call_completed =True 
                    backend_result ={
                    "status":"error",
                    "result":f"Tool call execution failed: {str(e)}"
                    }
                    ui_status_message =f"Tool call execution failed: {str(e)}"
                    self ._send_tool_call_response (call_id ,backend_result )


                    if self .on_progress_callback :
                        self .on_progress_callback (self .response )

                return None 


            import bpy 
            bpy .app .timers .register (execute_on_main_thread ,first_interval =0.0 )

        except Exception as e :
            logger .error (f"Error handling tool call request: {str(e)}")
            call_id =data .get ("call_id","")
            if call_id :

                self .response .tool_call_completed =True 
                self ._send_tool_call_response (call_id ,{
                "status":"error",
                "result":f"Tool call processing failed: {str(e)}"
                })


                if self .on_progress_callback :
                    self .on_progress_callback (self .response )

    def _send_tool_call_response (self ,call_id :str ,result :Dict [str ,Any ]):
        """Send tool call response back to server."""
        try :

            if not isinstance (result ,dict ):
                result ={"status":"error","result":str (result )}


            if "status"not in result :
                result ["status"]="success"if result .get ("result")and not str (result .get ("result")).startswith ("Error")else "error"

            response_data ={
            "call_id":call_id ,
            "output":json .dumps (result )
            }

            message =json .dumps (response_data )
            self .ws .send (message )
            logger .debug (f"Sent tool call response: {message}")



            if result .get ("status")=="success":

                self .response .success =True 
                logger .debug ("Tool call completed successfully, conversation may end soon")
            else :
                logger .warning (f"Tool call response indicates failure: {result}")

        except Exception as e :
            logger .error (f"Failed to send tool call response: {str(e)}")



            try :
                error_response ={
                "call_id":call_id ,
                "output":json .dumps ({
                "status":"error",
                "result":f"Failed to send tool response: {str(e)}"
                })
                }

                error_message =json .dumps (error_response )
                self .ws .send (error_message )
                logger .debug (f"Sent error tool call response: {error_message}")

            except Exception as e2 :
                logger .error (f"Failed to send error tool call response: {str(e2)}")



    def _handle_code_event (self ,data :Dict [str ,Any ]):
        """Handle final code event."""
        code =data .get ("code","")
        self .response .final_code =code 
        logger .info ("Final code received")

    def _handle_result_event (self ,data :Dict [str ,Any ]):
        """Handle result event (completion)."""
        self .response .message_id =data .get ("message_id","")
        self .response .success =data .get ("success",self .response .success )
        self .response .usage_info =data .get ("usage_info",{})
        self .response .is_complete =True 


        if not self .response .final_code and self .response .output_content :
            self .response .final_code =self .response .output_content 
            logger .info ("Using output_content as final_code")

        logger .info (f"Request completed - Success: {self.response.success}")


        if self .on_complete_callback :
            self .on_complete_callback (self .response )


        if self .ws :
            self .ws .close ()

    def _handle_request_id_event (self ,data :Dict [str ,Any ]):
        """Handle request ID event."""
        request_id =data .get ("request_id","")
        self .response .request_id =request_id 
        logger .debug (f"Request ID: {request_id}")

    def _handle_error_event (self ,data :Dict [str ,Any ]):
        """Handle error event from server."""
        try :

            error_info =data .get ("error",{})

            if isinstance (error_info ,dict ):

                error_code =error_info .get ("code","UNKNOWN")
                user_message =error_info .get ("user_message","An error occurred")
                technical_message =error_info .get ("message","Unknown error")
                suggestions =error_info .get ("suggestions",[])
                retryable =error_info .get ("retryable",False )
                technical_info =error_info .get ("technical_info","")


                display_message =user_message 



                logger .error (f"Server error ({error_code}): {technical_message}")
                if technical_info :
                    logger .error (f"Technical details: {technical_info}")
                if suggestions :
                    logger .error (f"Suggestions: {suggestions}")


                self .response .error =display_message 
                self .response .error_code =error_code 
                self .response .error_retryable =retryable 
                self .response .error_suggestions =[]

            elif isinstance (error_info ,str ):

                error_code =error_info 
                error_message =self ._get_legacy_error_message (error_code )

                logger .error (f"Server error ({error_code}): {error_message}")


                self .response .error =error_message 
                self .response .error_code =error_code 
                self .response .error_retryable =self ._is_legacy_error_retryable (error_code )
                self .response .error_suggestions =self ._get_legacy_error_suggestions (error_code )

            else :

                error_message ="An unexpected error occurred"
                logger .error (f"Unexpected error format: {error_info}")

                self .response .error =error_message 
                self .response .error_code ="UNKNOWN"
                self .response .error_retryable =True 
                self .response .error_suggestions =["Try again in a moment"]

            self .response .success =False 


            if self .on_error_callback :
                self .on_error_callback (self .response .error )


            if self .ws :
                self .ws .close ()

        except Exception as e :
            logger .error (f"Error handling server error event: {str(e)}")

    def _get_legacy_error_message (self ,error_code :str )->str :
        """Get user-friendly message for legacy error codes."""
        legacy_messages ={
        "INVALID_REQUEST":"Request format error. Please try again.",
        "AUTHENTICATION_FAILED":"Authentication failed. Please check your license key.",
        "RATE_LIMIT":"Rate limit exceeded. Please wait before making another request.",
        "PLAN_LIMIT_EXCEEDED":"You've reached your plan's usage limit for this period.",
        "DB_ERROR":"A temporary server error occurred. Please try again.",
        "INTERNAL_ERROR":"An unexpected error occurred. Please try again.",
        "LLM_ERROR":"The AI service encountered an error. Please try again.",
        "IMPOSSIBLE_REQUEST":"This request cannot be completed as described.",
        }
        return legacy_messages .get (error_code ,f"An error occurred: {error_code}")

    def _is_legacy_error_retryable (self ,error_code :str )->bool :
        """Check if legacy error code represents a retryable error."""
        retryable_codes ={
        "INVALID_REQUEST","RATE_LIMIT","DB_ERROR","INTERNAL_ERROR","LLM_ERROR"
        }
        return error_code in retryable_codes 

    def _get_legacy_error_suggestions (self ,error_code :str )->List [str ]:
        """Get suggestions for legacy error codes."""
        legacy_suggestions ={
        "INVALID_REQUEST":[
        "Ensure you're using the latest version of the addon",
        "Try refreshing and sending your request again",
        ],
        "AUTHENTICATION_FAILED":[
        "Verify your license key is correct",
        "Check if your subscription is still active",
        "Try re-entering your license key in the addon settings",
        ],
        "RATE_LIMIT":[
        "Wait a few minutes before trying again",
        "Consider upgrading your plan for higher limits",
        ],
        "PLAN_LIMIT_EXCEEDED":[
        "Wait for your limit to reset (usually monthly)",
        "Upgrade to a higher tier plan for more usage",
        ],
        "DB_ERROR":[
        "Wait a moment and try again",
        "If the issue persists, contact support",
        ],
        "INTERNAL_ERROR":[
        "Wait a moment and try again",
        "Try a simpler request to test if the service is working",
        ],
        "LLM_ERROR":[
        "Try rephrasing your request",
        "Try a simpler or more specific request",
        ],
        "IMPOSSIBLE_REQUEST":[
        "Try breaking down your request into smaller steps",
        "Rephrase your request with more specific details",
        ],
        }
        return legacy_suggestions .get (error_code ,["Try again in a moment"])

    def _on_error (self ,ws ,error ):
        """Handle WebSocket error."""
        error_msg =str (error )
        logger .error (f"WebSocket error: {error_msg}")


        user_friendly_error =_get_user_friendly_websocket_error (error_msg )

        if self .response :
            self .response .error =user_friendly_error 

        if self .on_error_callback :
            self .on_error_callback (user_friendly_error )

    def _on_close (self ,ws ,close_status_code ,close_msg ):
        """Handle WebSocket connection closed."""
        logger .info (f"WebSocket connection closed: {close_status_code} - {close_msg}")


        expected_close =(
        self .response and 
        (self .response .is_complete or 
        self .response .error is not None or 
        (self .response .success and self .response .final_code ))
        )


        if (self .response and not self .response .is_complete and 
        self .response .success and self .response .final_code and 
        not self .response .error ):

            logger .info ("Connection closed after successful tool execution - treating as completion")
            self .response .is_complete =True 


            if self .on_complete_callback :
                self .on_complete_callback (self .response )
            return 


        if self .response and not expected_close and not self .response .is_complete :
            error_msg =f"Connection closed unexpectedly: {close_msg or 'Unknown reason'}"


            user_friendly_error =_get_user_friendly_websocket_error (error_msg )

            self .response .error =user_friendly_error 

            if self .on_error_callback :
                self .on_error_callback (user_friendly_error )

    def _handle_tool_started_event (self ,data :Dict [str ,Any ]):
        """Handle tool started event for UX."""
        try :
            tool_name =data .get ("tool_name","")
            call_id =data .get ("call_id","")
            timestamp =data .get ("timestamp",0 )

            logger .info (f"Tool started: {tool_name} (call_id: {call_id})")


            if not hasattr (self .response ,'tool_events'):
                self .response .tool_events =[]

            self .response .tool_events .append ({
            "type":"tool_started",
            "tool_name":tool_name ,
            "call_id":call_id ,
            "timestamp":timestamp 
            })


            self .response .current_tool_name =tool_name 
            self .response .current_tool_status ="started"
            self .response .current_tool_call_id =call_id 
            self .response .current_tool_arguments =data .get ("arguments","{}")

        except Exception as e :
            logger .error (f"Error handling tool started event: {str(e)}")

    def _handle_tool_completed_event (self ,data :Dict [str ,Any ]):
        """Handle tool completed event for UX."""
        try :
            tool_name =data .get ("tool_name","")
            call_id =data .get ("call_id","")
            success =data .get ("success",False )
            timestamp =data .get ("timestamp",0 )

            logger .info (f"Tool completed: {tool_name} (call_id: {call_id}, success: {success})")


            if not hasattr (self .response ,'tool_events'):
                self .response .tool_events =[]

            self .response .tool_events .append ({
            "type":"tool_completed",
            "tool_name":tool_name ,
            "call_id":call_id ,
            "success":success ,
            "timestamp":timestamp 
            })


            self .response .current_tool_name =tool_name 
            self .response .current_tool_status ="completed"
            self .response .current_tool_success =success 
            self .response .current_tool_call_id =call_id 

        except Exception as e :
            logger .error (f"Error handling tool completed event: {str(e)}")

    def _handle_web_search_started_event (self ,data :Dict [str ,Any ]):
        """Handle web search started event for UX."""
        try :
            query =data .get ("query","")
            timestamp =data .get ("timestamp",0 )

            logger .info (f"Web search started: {query}")


            if not hasattr (self .response ,'web_search_events'):
                self .response .web_search_events =[]

            self .response .web_search_events .append ({
            "type":"web_search_started",
            "query":query ,
            "timestamp":timestamp 
            })


            self .response .current_search_query =query 
            self .response .current_search_status ="started"

        except Exception as e :
            logger .error (f"Error handling web search started event: {str(e)}")

    def _handle_web_search_completed_event (self ,data :Dict [str ,Any ]):
        """Handle web search completed event for UX."""
        try :
            query =data .get ("query","")
            result_count =data .get ("result_count",0 )
            success =data .get ("success",False )
            timestamp =data .get ("timestamp",0 )

            logger .info (f"Web search completed: {query} (results: {result_count}, success: {success})")


            if not hasattr (self .response ,'web_search_events'):
                self .response .web_search_events =[]

            self .response .web_search_events .append ({
            "type":"web_search_completed",
            "query":query ,
            "result_count":result_count ,
            "success":success ,
            "timestamp":timestamp 
            })


            self .response .current_search_query =query 
            self .response .current_search_status ="completed"
            self .response .current_search_success =success 
            self .response .current_search_result_count =result_count 

        except Exception as e :
            logger .error (f"Error handling web search completed event: {str(e)}")

    def _handle_response_in_progress_event (self ,data :Dict [str ,Any ]):
        """Handle response in progress event."""
        try :
            timestamp =data .get ("timestamp",0 )

            logger .debug (f"Response in progress (timestamp: {timestamp})")


            if not hasattr (self .response ,'response_events'):
                self .response .response_events =[]

            self .response .response_events .append ({
            "type":"response_in_progress",
            "timestamp":timestamp 
            })

        except Exception as e :
            logger .error (f"Error handling response in progress event: {str(e)}")

    def _handle_content_part_added_event (self ,data :Dict [str ,Any ]):
        """Handle content part added event."""
        try :
            content_index =data .get ("content_index",0 )
            timestamp =data .get ("timestamp",0 )

            logger .debug (f"Content part added at index {content_index} (timestamp: {timestamp})")


            if not hasattr (self .response ,'content_events'):
                self .response .content_events =[]

            self .response .content_events .append ({
            "type":"content_part_added",
            "content_index":content_index ,
            "timestamp":timestamp 
            })

        except Exception as e :
            logger .error (f"Error handling content part added event: {str(e)}")

    def _handle_output_text_done_event (self ,data :Dict [str ,Any ]):
        """Handle output text done event."""
        try :
            item_id =data .get ("item_id","")
            timestamp =data .get ("timestamp",0 )

            logger .debug (f"Output text done for item: {item_id} (timestamp: {timestamp})")


            if not hasattr (self .response ,'output_events'):
                self .response .output_events =[]

            self .response .output_events .append ({
            "type":"output_text_done",
            "item_id":item_id ,
            "timestamp":timestamp 
            })

        except Exception as e :
            logger .error (f"Error handling output text done event: {str(e)}")

    def _handle_content_part_done_event (self ,data :Dict [str ,Any ]):
        """Handle content part done event."""
        try :
            content_index =data .get ("content_index",0 )
            timestamp =data .get ("timestamp",0 )

            logger .debug (f"Content part done at index {content_index} (timestamp: {timestamp})")


            if not hasattr (self .response ,'content_events'):
                self .response .content_events =[]

            self .response .content_events .append ({
            "type":"content_part_done",
            "content_index":content_index ,
            "timestamp":timestamp 
            })

        except Exception as e :
            logger .error (f"Error handling content part done event: {str(e)}")

    def _handle_output_item_done_event (self ,data :Dict [str ,Any ]):
        """Handle output item done event."""
        try :
            item_type =data .get ("item_type","")
            timestamp =data .get ("timestamp",0 )

            logger .debug (f"Output item done: {item_type} (timestamp: {timestamp})")


            if not hasattr (self .response ,'output_events'):
                self .response .output_events =[]

            self .response .output_events .append ({
            "type":"output_item_done",
            "item_type":item_type ,
            "timestamp":timestamp 
            })

        except Exception as e :
            logger .error (f"Error handling output item done event: {str(e)}")

    def close (self ):
        """Close WebSocket connection."""
        if self .ws :
            self .ws .close ()
            self .ws =None 



llm_websocket_client =LLMWebSocketClient ()