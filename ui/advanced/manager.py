"""
Main UI manager that orchestrates the entire UI system.
"""

import bpy 
import logging 
import time 
from bpy .types import SpaceView3D 
from typing import Optional ,Tuple ,TYPE_CHECKING ,Dict ,Any ,List 
import threading 
import hashlib 

from .state import UIState 
from .renderer import UIRenderer 
from .components import Label ,TextInput ,Button 
from .types import Bounds ,CursorType ,EventType ,UIEvent 
from .coordinates import CoordinateSystem 
from .theme import get_themed_style ,theme_manager 
from .colors import Colors 
from .ui_factory import ImprovedUIFactory ,ViewState 
from .layout_manager import layout_manager 
from .components .component_registry import component_registry 
from .ui_state_manager import ui_state_manager 
from .import text_input_scale_fix 
from ...utils .logger import logger 
from ...utils .error_utils import create_error_context ,format_error_message 
from ...api .websocket_client import LLMWebSocketClient 
from ...engine .tools import tools_manager 
from ...utils .history_manager import history_manager 

if TYPE_CHECKING :
    from .components .base import UIComponent 

logger =logging .getLogger (__name__ )


class PerformanceConfig :
    """Configuration class for UI performance optimization levels."""


    CONSERVATIVE ="conservative"
    BALANCED ="balanced"
    AGGRESSIVE ="aggressive"

    def __init__ (self ,level :str =CONSERVATIVE ):
        self .level =level 
        self ._configure_for_level ()

    def _configure_for_level (self ):
        """Configure optimization parameters based on performance level."""
        if self .level ==self .CONSERVATIVE :
            self .timer_interval =0.1 
            self .ui_scale_check_interval =1 
            self .theme_check_interval =3 
            self .viewport_enforce_interval =0.5 
            self .animation_fps =30 
            self .cursor_blink_cycle =1.2 
            self .enable_selective_redraw =True 

        elif self .level ==self .BALANCED :
            self .timer_interval =1.0 
            self .ui_scale_check_interval =5 
            self .theme_check_interval =10 
            self .viewport_enforce_interval =3 
            self .animation_fps =15 
            self .cursor_blink_cycle =1.5 
            self .enable_selective_redraw =True 

        elif self .level ==self .AGGRESSIVE :
            self .timer_interval =2.0 
            self .ui_scale_check_interval =10 
            self .theme_check_interval =20 
            self .viewport_enforce_interval =5 
            self .animation_fps =10 
            self .cursor_blink_cycle =2.0 
            self .enable_selective_redraw =True 

    def get_animation_interval (self )->float :
        """Get animation frame interval."""
        return 1.0 /self .animation_fps 

    def should_check_ui_scale (self ,counter :int )->bool :
        """Check if UI scale should be checked this iteration."""
        return counter >=self .ui_scale_check_interval 

    def should_check_theme (self ,counter :int )->bool :
        """Check if theme should be checked this iteration."""
        return counter >=self .theme_check_interval 

    def should_enforce_viewport (self ,counter :int )->bool :
        """Check if viewport settings should be enforced."""
        return counter >=self .viewport_enforce_interval 


class UIManager :
    """Main UI manager that orchestrates everything.
    
    Timer Coordination System:
    -------------------------
    This class manages multiple timer systems that could potentially conflict:
    
    1. UI Scale Detection Timer- Detects UI scale changes, triggers complete recreation
    2. Theme Detection Timer - Detects theme changes, refreshes component styles  
    3. Viewport Resize Timer - Handles viewport size changes
    4. Cursor Animation Timer - Handles text cursor blinking
    5. API Progress Timers - Handle streaming API responses
    
    To prevent race conditions during UI scale changes, a UI Recreation Lock is used:
    - When UI scale changes are detected, the lock is set
    - Other timers check the lock and skip/postpone operations during recreation
    - The lock is cleared after complete UI recreation finishes
    - This prevents color mismatches, size inconsistencies, and random issues
    
    The lock has a 5-second timeout safety mechanism to prevent deadlocks.
    """

    def __init__ (self ):
        """Initialize the UI manager."""
        from .ui_factory import ImprovedUIFactory 
        from .layout_manager import layout_manager 


        self .performance_config =PerformanceConfig (PerformanceConfig .CONSERVATIVE )


        self .state =UIState ()
        self .layout_manager =layout_manager 
        self .factory =ImprovedUIFactory ()


        self .renderer =UIRenderer ()
        self .draw_handler =None 
        self .cursor_redraw_handler =None 


        self .components =[]
        self .ui_layout =None 


        self ._initialized =False 
        self ._pending_updates =[]
        self ._pending_resize =False 
        self ._resize_timer =None 


        self ._last_fps_update =0 
        self ._frame_count =0 
        self ._fps =0 


        self ._last_viewport_width =0 
        self ._last_viewport_height =0 


        self ._cursor_requests =[]


        self ._mouse_pressed =False 
        self ._mouse_pressed_component =None 


        self ._last_hovered_component =None 


        self ._theme_check_counter =0 


        self ._viewport_enforce_counter =0 


        self ._viewport_resize_debounce_delay =0.1 
        self ._pending_viewport_size =None 


        self ._is_generating =False 
        self ._current_ai_component =None 
        self ._websocket_client =None 
        self ._last_content_length =0 
        self ._last_tool_call_state =None 
        self ._content_after_tool_call =False 
        self ._last_sent_prompt =None 


        self ._tool_completion_blocks_created =set ()


        self ._tool_start_blocks_created =set ()


        self ._active_tool_components ={}


        self ._conversation_tracking ={
        'user_message':None ,
        'assistant_message_id':None ,
        'tool_calls':[],
        'tool_responses':[],
        'final_content':None ,
        'conversation_saved':False 
        }


        self .factory .set_view_change_callback (self ._recreate_ui_for_view_change )


        self ._current_ui_scale =None 
        self ._ui_scale_check_counter =0 


        self ._ui_recreation_in_progress =False 
        self ._ui_recreation_lock_start_time =None 

        logger .info ("UIManager initialized with performance optimizations")

    def set_performance_level (self ,level :str ):
        """Set the performance optimization level."""
        try :
            old_level =self .performance_config .level 
            self .performance_config =PerformanceConfig (level )
            logger .info (f"Performance level changed from {old_level} to {level}")


            if self .cursor_redraw_handler :
                bpy .app .timers .unregister (self .cursor_redraw_handler )
                self .cursor_redraw_handler =bpy .app .timers .register (
                self ._enforce_ui_settings ,
                first_interval =self .performance_config .timer_interval 
                )
                logger .info (f"Restarted UI enforcement timer with {self.performance_config.timer_interval}s interval")

        except Exception as e :
            logger .error (f"Error setting performance level: {e}")

    def get_performance_level (self )->str :
        """Get the current performance optimization level."""
        return self .performance_config .level 

    def get_performance_info (self )->Dict [str ,Any ]:
        """Get detailed information about current performance settings."""
        config =self .performance_config 
        return {
        'level':config .level ,
        'timer_interval':config .timer_interval ,
        'ui_scale_check_interval':config .ui_scale_check_interval ,
        'theme_check_interval':config .theme_check_interval ,
        'viewport_enforce_interval':config .viewport_enforce_interval ,
        'animation_fps':config .animation_fps ,
        'cursor_blink_cycle':config .cursor_blink_cycle ,
        'enable_selective_redraw':config .enable_selective_redraw 
        }

    def apply_aggressive_optimizations (self ):
        """Apply the most aggressive performance optimizations.
        
        Use this when you need maximum performance and can sacrifice some visual fidelity.
        Suitable for lower-end hardware or when working with very complex scenes.
        """
        self .set_performance_level (PerformanceConfig .AGGRESSIVE )
        logger .info ("Applied aggressive performance optimizations - reduced visual fidelity for better performance")

    def apply_conservative_optimizations (self ):
        """Apply conservative performance optimizations.
        
        Use this for maximum compatibility and visual quality.
        Suitable for high-end hardware or when visual fidelity is critical.
        """
        self .set_performance_level (PerformanceConfig .CONSERVATIVE )
        logger .info ("Applied conservative performance optimizations - prioritizing visual quality")

    def apply_balanced_optimizations (self ):
        """Apply balanced performance optimizations (default).
        
        Good balance between performance and visual quality.
        Suitable for most use cases and hardware configurations.
        """
        self .set_performance_level (PerformanceConfig .BALANCED )
        logger .info ("Applied balanced performance optimizations - good balance of performance and quality")

    def _create_default_ui (self ):
        """Create the default UI layout using the factory system."""


        pass 

    def _initialize_ui_layout (self ):
        """Initialize UI layout with current viewport dimensions."""
        if self .state .viewport_width ==0 or self .state .viewport_height ==0 :
            logger .warning ("Cannot initialize UI layout: viewport dimensions are zero")
            return 

        try :
            logger .info (f"Initializing UI layout for viewport: {self.state.viewport_width}x{self.state.viewport_height}")


            self .ui_layout =self .factory .create_layout (
            self .state .viewport_width ,
            self .state .viewport_height ,
            on_send =self ._handle_send ,
            on_add =self ._handle_add ,
            on_history =self ._handle_history ,
            on_settings =self ._handle_settings ,
            on_model_change =self ._handle_model_change ,
            on_auth_submit =self ._handle_auth_submit ,
            on_get_license =self ._handle_get_license ,
            on_stop_generation =self .factory ._handle_stop_generation 
            )

            if not self .ui_layout :
                logger .error ("Factory failed to create UI layout")
                return 


            self .components =self .ui_layout .get ('components',{})


            self .state .components .clear ()
            all_components =self .ui_layout .get ('all_components',[])

            logger .info (f"Adding {len(all_components)} components to state")
            for component in all_components :
                self .state .add_component (component )



            for component in self .state .components :
                if hasattr (component ,'update_layout'):
                    component .update_layout ()



            for component in self .state .components :
                if hasattr (component ,'_dimension_cache')and hasattr (component ,'invalidate'):

                    component ._dimension_cache .clear ()
                    component .invalidate ()
                    logger .debug (f"Cleared dimension cache for {type(component).__name__}")


            focused_component =self .factory .get_focused_component ()
            if focused_component :
                self .state .set_focus (focused_component )
                logger .info (f"Set initial focus to: {type(focused_component).__name__}")

            logger .info (f"✅ UI layout initialized successfully with {len(self.state.components)} components")

        except Exception as e :
            logger .error (f"Error initializing UI layout: {e}")
            import traceback 
            logger .error (traceback .format_exc ())

            self .ui_layout =None 
            self .components ={}

    def _update_layout (self ):
        """Update component positions when viewport changes."""
        if not self .ui_layout or self .state .viewport_width ==0 or self .state .viewport_height ==0 :
            return 


        self .factory ._handle_viewport_change (self .state .viewport_width ,self .state .viewport_height )

        logger .debug (f"Updated layout for viewport size: {self.state.viewport_width}x{self.state.viewport_height}")

    def _on_viewport_resize_finished (self ):
        """Called when viewport resize is finished after debounce delay."""
        try :
            if self ._pending_viewport_size is None :
                return 


            if self ._is_ui_recreation_locked ():
                logger .debug ("Viewport resize postponed - UI recreation in progress")

                self ._resize_timer =bpy .app .timers .register (
                self ._on_viewport_resize_finished ,
                first_interval =0.2 
                )
                return 

            width ,height =self ._pending_viewport_size 
            logger .debug (f"Viewport resize finished: {width}x{height}")


            self .state .update_viewport_size (width ,height )


            if self .ui_layout is None :
                self ._initialize_ui_layout ()
            else :
                self ._update_layout ()


            for component in self .state .components :
                if hasattr (component ,'_render_dirty'):
                    component ._render_dirty =True 


            if self .state .target_area :
                self .state .target_area .tag_redraw ()


            self ._pending_viewport_size =None 

        except Exception as e :
            logger .error (f"Error in viewport resize finished callback: {e}")
        finally :

            self ._resize_timer =None 

    def _handle_send (self ):
        """Handle send button click with real API integration."""
        if not self .components :
            return 


        if self ._is_generating :
            logger .warning ("Generation already in progress")
            return 

        text =self .factory .get_send_text (self .components )
        if not text .strip ():
            logger .info ("No text to send")
            return 

        try :

            try :
                context =bpy .context 
                from ...utils .history_manager import history_manager 
                current_chat_id =getattr (context .scene ,'vibe4d_current_chat_id','')
                if current_chat_id :
                    history_manager .clear_unsent_text (context ,current_chat_id )
            except Exception as e :
                logger .debug (f"Could not clear unsent text: {e}")


            self .factory .add_message_to_scrollview (self .components ,text .strip (),is_ai_response =False )

            self .factory .clear_send_text (self .components )


            self ._is_generating =True 
            self ._last_content_length =0 
            self ._last_tool_call_state =None 
            self ._content_after_tool_call =False 
            self .factory ._set_send_button_mode (False )


            self ._current_ai_component =self .factory .add_markdown_message_to_scrollview (self .components ,"",is_ai_response =True )


            self ._start_real_api_generation (text .strip ())

            if self .state .target_area :
                self .state .target_area .tag_redraw ()

        except Exception as e :
            logger .error (f"Error in _handle_send: {e}")
            self ._reset_generation_state ()

    def _start_real_api_generation (self ,prompt :str ):
        """Start real API generation using the WebSocket client."""
        try :

            self ._start_conversation_tracking (prompt )


            self ._last_sent_prompt =prompt 


            from ...llm .request_builder import LLMRequestBuilder 
            from ...api .websocket_client import llm_websocket_client 


            if not llm_websocket_client .is_ready_for_new_request ():
                logger .info ("WebSocket client is busy or has active connection, waiting...")




            context =bpy .context 


            if not getattr (context .window_manager ,'vibe4d_authenticated',False ):
                logger .error ("Not authenticated")
                self ._handle_api_error ("Please authenticate first")
                return 


            user_id =getattr (context .window_manager ,'vibe4d_user_id','')
            token =getattr (context .window_manager ,'vibe4d_user_token','')

            if not user_id or not token :
                logger .error ("Authentication credentials missing")
                self ._handle_api_error ("Authentication credentials missing")
                return 


            selected_model =getattr (context .scene ,'vibe4d_model','gpt-4.1-mini')

            logger .info (f"Using model: {selected_model}")


            request =LLMRequestBuilder .build_request (
            context =context ,
            prompt =prompt ,
            user_id =user_id ,
            token =token ,
            model =selected_model 
            )


            self ._websocket_client =llm_websocket_client 



            success =llm_websocket_client .send_prompt_request (
            request_data =request ,
            on_progress =self ._handle_api_progress ,
            on_complete =self ._handle_api_complete ,
            on_error =self ._handle_api_error 
            )

            if not success :
                logger .error ("Failed to start API generation")
                self ._handle_api_error ("Failed to start generation")
                return 

            logger .info (f"Started real API generation for prompt: '{prompt[:50]}...' using model: {selected_model}")

        except Exception as e :
            logger .error (f"Error starting real API generation: {e}")
            self ._handle_api_error (f"Failed to start generation: {str(e)}")

    def _handle_api_progress (self ,response ):
        """Handle streaming progress updates from the API."""
        def update_ui ():
            try :
                if not self ._is_generating :
                    return None 


                current_tool_call_state =None 
                if hasattr (response ,'tool_call_started')and hasattr (response ,'tool_call_completed'):
                    if response .tool_call_started and not response .tool_call_completed :
                        current_tool_call_state ="started"
                    elif response .tool_call_completed :
                        current_tool_call_state ="completed"


                if current_tool_call_state !=self ._last_tool_call_state :
                    logger .info (f"Tool call state changed: {self._last_tool_call_state} -> {current_tool_call_state}")


                if hasattr (response ,'current_tool_status')and hasattr (response ,'current_tool_name'):
                    tool_status =getattr (response ,'current_tool_status',None )
                    tool_name =getattr (response ,'current_tool_name',None )

                    if tool_status =="started"and tool_name :

                        call_id =getattr (response ,'current_tool_call_id',f"call_{len(self._conversation_tracking['tool_calls'])}")


                        logger .info (f"Tool start: call_id='{call_id}', already_created={call_id in self._tool_start_blocks_created}, created_set={self._tool_start_blocks_created}")

                        tool_call_data ={
                        'call_id':call_id ,
                        'function':{
                        'name':tool_name ,
                        'arguments':getattr (response ,'current_tool_arguments','{}')
                        },
                        'status':'started'
                        }
                        self ._track_tool_call (tool_call_data )


                        if call_id not in self ._tool_start_blocks_created :

                            status_block =self ._get_tool_status_block (tool_name ,"started")

                            if status_block :
                                status_component =self .factory .add_markdown_message_to_scrollview (
                                self .components ,status_block ,is_ai_response =True 
                                )
                                self ._current_ai_component =status_component 


                                self ._active_tool_components [call_id ]=status_component 


                                self ._tool_start_blocks_created .add (call_id )
                                logger .info (f"Created tool start component for {call_id}: '{status_block}'")

                    elif tool_status =="completed"and tool_name :

                        success =getattr (response ,'current_tool_success',False )
                        call_id =getattr (response ,'current_tool_call_id',f"call_{len(self._conversation_tracking['tool_responses'])}")

                        tool_response_data ={
                        'call_id':call_id ,
                        'content':getattr (response ,'current_tool_result','{}'),
                        'success':success 
                        }
                        self ._track_tool_response (tool_response_data )


                        completion_block =self ._get_tool_status_block (tool_name ,"completed",success )
                        if completion_block :

                            if self ._update_tool_component (call_id ,completion_block ):
                                logger .info (f"Smooth transition for {call_id}: '{completion_block}'")

                                self ._cleanup_completed_tool_component (call_id )

                                self ._tool_completion_blocks_created .add (call_id )

                                self ._content_after_tool_call =True 
                            else :

                                if call_id not in self ._tool_completion_blocks_created :
                                    status_component =self .factory .add_markdown_message_to_scrollview (
                                    self .components ,completion_block ,is_ai_response =True 
                                    )
                                    self ._current_ai_component =status_component 
                                    logger .info (f"Created fallback tool completed status block: {completion_block}")


                                    self ._tool_completion_blocks_created .add (call_id )
                                    logger .info (f"Marked call_id '{call_id}' as having completion block. Set now: {self._tool_completion_blocks_created}")


                                    self ._content_after_tool_call =True 


                if hasattr (response ,'current_search_status')and hasattr (response ,'current_search_query'):
                    search_status =getattr (response ,'current_search_status',None )
                    search_query =getattr (response ,'current_search_query',None )

                    if search_status =="started"and search_query :


                        search_call_id =f"websearch_{hashlib.md5(search_query.encode()).hexdigest()[:8]}"


                        web_search_tool_call ={
                        'call_id':search_call_id ,
                        'function':{
                        'name':'web_search',
                        'arguments':f'{{"query": "{search_query}"}}'
                        },
                        'status':'started'
                        }
                        self ._track_tool_call (web_search_tool_call )

                        status_block =f"[Searching web: {search_query}]"
                        status_component =self .factory .add_markdown_message_to_scrollview (
                        self .components ,status_block ,is_ai_response =True 
                        )
                        self ._current_ai_component =status_component 
                        logger .info (f"Added web search started status block: {status_block}")
                        logger .info (f"✅ Tracked web search as tool call: {search_call_id}")

                    elif search_status =="completed"and search_query :
                        success =getattr (response ,'current_search_success',False )
                        result_count =getattr (response ,'current_search_result_count',0 )

                        if success and result_count >0 :
                            status_block =f"[Found {result_count} results for: {search_query}]"

                            ui_message =f"Found {result_count} results"
                        elif success :
                            status_block =f"[Web search completed: {search_query}]"
                            ui_message ="Web search completed"
                        else :
                            status_block =f"[Web search failed: {search_query}]"
                            ui_message ="Web search failed"

                        status_component =self .factory .add_markdown_message_to_scrollview (
                        self .components ,status_block ,is_ai_response =True 
                        )
                        self ._current_ai_component =status_component 
                        logger .info (f"Added web search completed status block: {status_block}")



                        search_call_id =f"websearch_{hashlib.md5(search_query.encode()).hexdigest()[:8]}"


                        web_search_response_data ={
                        'call_id':search_call_id ,
                        'content':f'{{"status": "success", "result": "{ui_message}", "query": "{search_query}", "result_count": {result_count}}}',
                        'success':success ,
                        'ui_message':ui_message ,
                        'tool_name':'web_search'
                        }

                        self ._track_tool_response (web_search_response_data )
                        logger .info (f"✅ Tracked web search as tool response for history: {ui_message}")


                if hasattr (response ,'response_events')and response .response_events :
                    for event in response .response_events :
                        if event .get ('type')=='response_in_progress':
                            logger .debug ("Response in progress event received")


                if hasattr (response ,'content_events')and response .content_events :
                    for event in response .content_events :
                        event_type =event .get ('type')
                        if event_type =='content_part_added':
                            content_index =event .get ('content_index',0 )
                            logger .debug (f"Content part added at index {content_index}")
                        elif event_type =='content_part_done':
                            content_index =event .get ('content_index',0 )
                            logger .debug (f"Content part done at index {content_index}")

                if hasattr (response ,'output_events')and response .output_events :
                    for event in response .output_events :
                        event_type =event .get ('type')
                        if event_type =='output_text_done':
                            item_id =event .get ('item_id','')
                            logger .debug (f"Output text done for item: {item_id}")
                        elif event_type =='output_item_done':
                            item_type =event .get ('item_type','')
                            logger .debug (f"Output item done: {item_type}")


                if hasattr (response ,'output_content')and response .output_content :
                    content =response .output_content 


                    if hasattr (response ,'message_id'):
                        self ._track_assistant_message (response .message_id ,content )


                    logger .debug (f"Content length: {len(content)}, Last tracked: {self._last_content_length}, Content after tool call: {self._content_after_tool_call}")


                    if self ._content_after_tool_call and len (content )>self ._last_content_length :

                        new_content =content [self ._last_content_length :].strip ()
                        if new_content :

                            self ._current_ai_component =self .factory .add_markdown_message_to_scrollview (
                            self .components ,new_content ,is_ai_response =True 
                            )
                            self ._last_content_length =len (content )
                            self ._content_after_tool_call =False 
                            logger .info (f"Created new message for post-tool-call content: '{new_content[:50]}...'")
                        else :

                            logger .debug ("No new content for post-tool-call, resetting flag")
                            self ._content_after_tool_call =False 


                    elif self ._current_ai_component and len (content )>self ._last_content_length :
                        new_content =content [self ._last_content_length :]

                        logger .debug (f"Streaming update: full_content='{content[:50]}...', new_content='{new_content[:20]}...', last_length={self._last_content_length}")


                        current_content =""
                        if hasattr (self ._current_ai_component ,'get_message'):
                            current_content =self ._current_ai_component .get_message ()
                        elif hasattr (self ._current_ai_component ,'markdown_text'):
                            current_content =self ._current_ai_component .markdown_text 


                        if current_content .strip ()and not current_content .startswith ('['):

                            updated_content =current_content +new_content 
                            logger .debug (f"Appending to existing message: '{new_content[:30]}...' to '{current_content[:30]}...'")
                        elif current_content .startswith ('['):

                            if current_content .endswith (']'):

                                updated_content =current_content +new_content 
                                logger .debug (f"Appending to completed status block: '{new_content[:30]}...' to '{current_content[:30]}...'")
                            else :


                                block_start =content .find ('[')
                                if block_start !=-1 :

                                    block_portion =content [block_start :]
                                    block_end =block_portion .find (']')
                                    if block_end !=-1 :

                                        complete_block =block_portion [:block_end +1 ]
                                        remaining_content =block_portion [block_end +1 :]
                                        updated_content =complete_block +remaining_content 
                                    else :

                                        updated_content =block_portion 
                                    logger .debug (f"Building status block: '{updated_content[:30]}...'")
                                else :

                                    updated_content =current_content +new_content 
                                    logger .debug (f"Fallback append: '{new_content[:30]}...' to '{current_content[:30]}...'")
                        else :

                            updated_content =content .strip ()
                            logger .debug (f"Setting content on empty component: '{content[:30]}...'")


                        if hasattr (self ._current_ai_component ,'set_markdown'):
                            self ._current_ai_component .set_markdown (updated_content )
                        else :
                            self ._current_ai_component .set_message (updated_content )


                        self ._last_content_length =len (content )


                    elif not self ._current_ai_component and content .strip ():
                        self ._current_ai_component =self .factory .add_markdown_message_to_scrollview (
                        self .components ,content .strip (),is_ai_response =True 
                        )
                        self ._last_content_length =len (content )
                        logger .info (f"Created initial AI message component: '{content[:50]}...'")


                    if self ._current_ai_component and hasattr (self ._current_ai_component ,'auto_resize_to_content'):
                        view =self .factory .views .get (self .factory .current_view )
                        if view and hasattr (view ,'get_message_scrollview'):
                            message_scrollview =view .get_message_scrollview ()
                            if message_scrollview :

                                scaled_padding =CoordinateSystem .scale_int (40 )
                                max_width =message_scrollview .bounds .width -scaled_padding 
                                if message_scrollview .show_scrollbars :
                                    max_width -=message_scrollview .scrollbar_width 


                                old_height =self ._current_ai_component .bounds .height 
                                self ._current_ai_component .auto_resize_to_content (max_width )
                                new_height =self ._current_ai_component .bounds .height 


                                if new_height !=old_height :
                                    height_diff =new_height -old_height 
                                    for child in message_scrollview .children :
                                        if child !=self ._current_ai_component :
                                            child .bounds .y +=height_diff 


                                message_scrollview ._update_content_bounds ()


                    if self .state .target_area :
                        self .state .target_area .tag_redraw ()

                logger .debug (f"API progress update: {getattr(response, 'progress', 0)}%")


                self ._last_tool_call_state =current_tool_call_state 

            except Exception as e :
                logger .error (f"Error in API progress update: {e}")

            return None 


        bpy .app .timers .register (update_ui ,first_interval =0.0 )

    def _handle_api_complete (self ,response ):
        """Handle API completion."""
        def complete_generation ():
            try :
                import bpy 

                self ._is_generating =False 
                self .factory ._set_send_button_mode (True )


                if hasattr (response ,'output_content')and response .output_content :
                    final_content =response .output_content 


                    self ._track_assistant_message (
                    getattr (response ,'message_id',None )or f"msg_{int(time.time() * 1000)}",
                    final_content 
                    )


                    if len (final_content )>self ._last_content_length :
                        new_content =final_content [self ._last_content_length :].strip ()
                        if new_content :
                            logger .info (f"Final completion has new content: '{new_content[:50]}...'")

                            if self ._content_after_tool_call or not self ._current_ai_component :

                                final_component =self .factory .add_markdown_message_to_scrollview (
                                self .components ,new_content ,is_ai_response =True 
                                )


                                if hasattr (final_component ,'auto_resize_to_content'):
                                    view =self .factory .views .get (self .factory .current_view )
                                    if view and hasattr (view ,'get_message_scrollview'):
                                        message_scrollview =view .get_message_scrollview ()
                                        if message_scrollview :

                                            scaled_padding =CoordinateSystem .scale_int (40 )
                                            max_width =message_scrollview .bounds .width -scaled_padding 
                                            if message_scrollview .show_scrollbars :
                                                max_width -=message_scrollview .scrollbar_width 

                                            final_component .auto_resize_to_content (max_width )
                                            message_scrollview ._update_content_bounds ()

                                logger .info ("Added final message component")
                            else :

                                current_content =""
                                if hasattr (self ._current_ai_component ,'get_message'):
                                    current_content =self ._current_ai_component .get_message ()
                                elif hasattr (self ._current_ai_component ,'markdown_text'):
                                    current_content =self ._current_ai_component .markdown_text 

                                if not current_content .startswith ('['):

                                    updated_content =current_content +new_content 
                                    if hasattr (self ._current_ai_component ,'set_markdown'):
                                        self ._current_ai_component .set_markdown (updated_content )
                                    else :
                                        self ._current_ai_component .set_message (updated_content )
                                    logger .info ("Appended final content to existing message")
                                else :

                                    if new_content .strip ():

                                        updated_content =final_content .strip ()
                                        if hasattr (self ._current_ai_component ,'set_markdown'):
                                            self ._current_ai_component .set_markdown (updated_content )
                                        else :
                                            self ._current_ai_component .set_message (updated_content )
                                        logger .info ("Replaced status block with final content")
                                    else :
                                        logger .info ("Kept status block as final content is empty")
                        else :
                            logger .debug ("No new content in final completion")


                        if self ._current_ai_component and len (final_content )<=self ._last_content_length :

                            if hasattr (self ._current_ai_component ,'auto_resize_to_content'):
                                view =self .factory .views .get (self .factory .current_view )
                                if view and hasattr (view ,'get_message_scrollview'):
                                    message_scrollview =view .get_message_scrollview ()
                                    if message_scrollview :

                                        scaled_padding =CoordinateSystem .scale_int (40 )
                                        max_width =message_scrollview .bounds .width -scaled_padding 
                                        if message_scrollview .show_scrollbars :
                                            max_width -=message_scrollview .scrollbar_width 


                                        old_height =self ._current_ai_component .bounds .height 
                                        self ._current_ai_component .auto_resize_to_content (max_width )
                                        new_height =self ._current_ai_component .bounds .height 


                                        if new_height !=old_height :
                                            height_diff =new_height -old_height 
                                            for child in message_scrollview .children :
                                                if child !=self ._current_ai_component :
                                                    child .bounds .y +=height_diff 


                                        message_scrollview ._update_content_bounds ()
                else :

                    self ._track_assistant_message (
                    getattr (response ,'message_id',None )or f"msg_{int(time.time() * 1000)}",
                    ""
                    )


                self ._save_conversation_to_history ()


                if hasattr (response ,'usage_info')and response .usage_info :
                    context =bpy .context 
                    usage =response .usage_info 
                    current =usage .get ('current_usage',0 )
                    limit =usage .get ('limit',0 )
                    context .window_manager .vibe4d_current_usage =current 
                    context .window_manager .vibe4d_usage_limit =limit 
                    logger .debug (f"Updated usage info: {current}/{limit}")


                self ._reset_generation_state ()


                if self .state .target_area :
                    self .state .target_area .tag_redraw ()

                if response .success :
                    logger .info ("API generation completed successfully")
                else :
                    error =getattr (response ,'error','Generation failed')
                    logger .error (f"API generation failed: {error}")

            except Exception as e :
                logger .error (f"Error in API completion: {e}")


                if self ._conversation_tracking and not self ._conversation_tracking ['conversation_saved']:
                    try :
                        user_message =self ._conversation_tracking .get ('user_message')
                        if user_message :
                            import bpy 
                            context =bpy .context 
                            from ...utils .history_manager import history_manager 
                            history_manager .add_message (context ,"user",user_message )
                            logger .info (f"✓ Saved USER message on completion error: '{user_message[:50]}...'")
                        final_content =self ._conversation_tracking .get ('final_content')
                        tool_calls =self ._conversation_tracking .get ('tool_calls',[])
                        if final_content or tool_calls :
                            openai_tool_calls =None 
                            if tool_calls :
                                sorted_tool_calls =sorted (tool_calls ,key =lambda x :x .get ('call_id',''))
                                openai_tool_calls =[]
                                for tool_call in sorted_tool_calls :
                                    openai_tool_calls .append ({
                                    "id":tool_call .get ('call_id',f"call_{len(openai_tool_calls)}"),
                                    "type":"function",
                                    "function":{
                                    "name":tool_call .get ('function',{}).get ('name','unknown'),
                                    "arguments":tool_call .get ('function',{}).get ('arguments','{}')
                                    }
                                    })
                            history_manager .add_message (
                            context ,
                            "assistant",
                            final_content or "",
                            tool_calls =openai_tool_calls 
                            )
                            logger .info (f"✓ Saved partial ASSISTANT message on completion error: '{(final_content or '')[:50]}...' with {len(tool_calls)} tool calls")
                        tool_responses =self ._conversation_tracking .get ('tool_responses',[])
                        if tool_responses :
                            sorted_tool_responses =sorted (tool_responses ,key =lambda x :x .get ('call_id',''))
                            for tool_response in sorted_tool_responses :
                                simple_response_text =tool_response .get ("ui_message")or tool_response .get ("content","Tool response")
                                history_manager .add_message (
                                context ,
                                "tool",
                                simple_response_text ,
                                tool_call_id =tool_response .get ("call_id")
                                )
                                logger .debug (f"✓ Saved TOOL response on completion error for call_id: {tool_response.get('call_id')}")
                        logger .info ("✅ Preserved conversation data before completion error reset")
                    except Exception as save_error :
                        logger .error (f"Failed to save conversation data on completion error: {str(save_error)}")
                self ._reset_generation_state ()
            return None 


        bpy .app .timers .register (complete_generation ,first_interval =0.0 )

    def _handle_api_error (self ,error ):
        """Handle API errors with improved error display and suggestions."""
        def handle_error ():
            try :
                import bpy 

                logger .error (f"API error: {error}")



                if self ._conversation_tracking and not self ._conversation_tracking ['conversation_saved']:
                    try :

                        user_message =self ._conversation_tracking .get ('user_message')
                        if user_message :
                            import bpy 
                            context =bpy .context 
                            from ...utils .history_manager import history_manager 
                            history_manager .add_message (context ,"user",user_message )
                            logger .info (f"✓ Saved USER message on error: '{user_message[:50]}...'")


                        final_content =self ._conversation_tracking .get ('final_content')
                        tool_calls =self ._conversation_tracking .get ('tool_calls',[])
                        if final_content or tool_calls :

                            openai_tool_calls =None 
                            if tool_calls :
                                sorted_tool_calls =sorted (tool_calls ,key =lambda x :x .get ('call_id',''))
                                openai_tool_calls =[]
                                for tool_call in sorted_tool_calls :
                                    openai_tool_calls .append ({
                                    "id":tool_call .get ('call_id',f"call_{len(openai_tool_calls)}"),
                                    "type":"function",
                                    "function":{
                                    "name":tool_call .get ('function',{}).get ('name','unknown'),
                                    "arguments":tool_call .get ('function',{}).get ('arguments','{}')
                                    }
                                    })


                            history_manager .add_message (
                            context ,
                            "assistant",
                            final_content or "",
                            tool_calls =openai_tool_calls 
                            )
                            logger .info (f"✓ Saved partial ASSISTANT message on error: '{(final_content or '')[:50]}...' with {len(tool_calls)} tool calls")


                        tool_responses =self ._conversation_tracking .get ('tool_responses',[])
                        if tool_responses :
                            sorted_tool_responses =sorted (tool_responses ,key =lambda x :x .get ('call_id',''))
                            for tool_response in sorted_tool_responses :
                                simple_response_text =tool_response .get ("ui_message")or tool_response .get ("content","Tool response")
                                history_manager .add_message (
                                context ,
                                "tool",
                                simple_response_text ,
                                tool_call_id =tool_response .get ("call_id")
                                )
                                logger .debug (f"✓ Saved TOOL response on error for call_id: {tool_response.get('call_id')}")

                        logger .info ("✅ Preserved conversation data before error reset")

                    except Exception as save_error :
                        logger .error (f"Failed to save conversation data on error: {str(save_error)}")


                error_data =None 
                if hasattr (self ,'api_client')and self .api_client and self .api_client .response :
                    if hasattr (self .api_client .response ,'error_code'):

                        error_data ={
                        'code':getattr (self .api_client .response ,'error_code','UNKNOWN'),
                        'user_message':str (error ),
                        'retryable':getattr (self .api_client .response ,'error_retryable',True ),
                        'technical_info':getattr (self .api_client .response ,'technical_info','')
                        }


                if not error_data :
                    error_data =str (error )


                from ...utils .error_utils import create_error_context 
                error_context =create_error_context (error_data )


                error_content =error_context ['formatted_message']


                if self .components :

                    self .factory .add_error_message_to_scrollview (self .components ,error_content )


                    try :
                        import bpy 
                        context =bpy .context 
                        from ...utils .history_manager import history_manager 
                        history_manager .add_error_message (context ,error_content )
                        logger .debug ("Saved error message to chat history")
                    except Exception as e :
                        logger .warning (f"Failed to save error message to history: {str(e)}")
                else :

                    if self ._current_ai_component :
                        if hasattr (self ._current_ai_component ,'set_markdown'):
                            self ._current_ai_component .set_markdown (error_content )
                        else :
                            self ._current_ai_component .set_message (error_content )


                self ._reset_generation_state ()


                if self .state .target_area :
                    self .state .target_area .tag_redraw ()


                logger .debug (f"Error details - Code: {error_context['code']}, Severity: {error_context['severity']}, "
                f"Retryable: {error_context['retryable']}")

            except Exception as e :
                logger .error (f"Error handling API error: {e}")


                fallback_content =f"❌ **Error:** {error}"

                if self .components and not hasattr (e ,'_fallback_handled'):

                    e ._fallback_handled =True 

                    try :
                        self .factory .add_error_message_to_scrollview (self .components ,fallback_content )
                    except :

                        if self ._current_ai_component :
                            if hasattr (self ._current_ai_component ,'set_markdown'):
                                self ._current_ai_component .set_markdown (fallback_content )
                            else :
                                self ._current_ai_component .set_message (fallback_content )
                elif self ._current_ai_component and not hasattr (e ,'_fallback_handled'):

                    e ._fallback_handled =True 
                    if hasattr (self ._current_ai_component ,'set_markdown'):
                        self ._current_ai_component .set_markdown (fallback_content )
                    else :
                        self ._current_ai_component .set_message (fallback_content )


                if not hasattr (e ,'_reset_done'):
                    e ._reset_done =True 
                    self ._reset_generation_state ()
                    if self .state .target_area :
                        self .state .target_area .tag_redraw ()

            return None 


        bpy .app .timers .register (handle_error ,first_interval =0.0 )

    def _reset_generation_state (self ):
        """Reset UI state after generation completion or error."""
        self ._is_generating =False 
        self ._last_content_length =0 
        self ._last_tool_call_state =None 
        self ._content_after_tool_call =False 
        self ._current_ai_component =None 
        self ._websocket_client =None 


        self ._cleanup_websocket_connection ()


        self .factory ._set_send_button_mode (True )


        self ._reset_conversation_tracking ()

        if self .state .target_area :
            self .state .target_area .tag_redraw ()

    def _cleanup_websocket_connection (self ):
        """Clean up any active WebSocket connections."""
        try :
            from ...api .websocket_client import llm_websocket_client 


            if not llm_websocket_client .is_ready_for_new_request ():
                logger .info ("Cleaning up active WebSocket connection")
                llm_websocket_client .close ()

        except Exception as e :
            logger .debug (f"Error during WebSocket cleanup: {e}")

    def cleanup (self ):
        """Clean up resources when UI manager is destroyed."""
        logger .info ("Cleaning up UI manager resources")


        if self ._is_generating :

            if hasattr (self ,'_conversation_tracking')and self ._conversation_tracking :
                if not self ._conversation_tracking .get ('conversation_saved',False ):
                    try :
                        logger .info ("Saving conversation data before UI cleanup")
                        self ._save_conversation_to_history ()
                        logger .info ("✅ Conversation data saved successfully before cleanup")
                    except Exception as save_error :
                        logger .error (f"Failed to save conversation data before cleanup: {str(save_error)}")



            self ._reset_generation_state ()


        self ._cleanup_websocket_connection ()


        if self .components :
            self .components .clear ()


        self .state .reset ()

        logger .info ("UI manager cleanup completed")

    def _start_conversation_tracking (self ,user_prompt :str ):
        """Start tracking a new conversation turn."""
        self ._conversation_tracking ={
        'user_message':user_prompt ,
        'assistant_message_id':None ,
        'tool_calls':[],
        'tool_responses':[],
        'final_content':None ,
        'conversation_saved':False 
        }

        self ._tool_completion_blocks_created .clear ()
        self ._tool_start_blocks_created .clear ()

        self ._active_tool_components .clear ()
        logger .info (f"Started conversation tracking for: '{user_prompt[:50]}...'")

    def _reset_conversation_tracking (self ):
        """Reset conversation tracking state."""
        self ._conversation_tracking ={
        'user_message':None ,
        'assistant_message_id':None ,
        'tool_calls':[],
        'tool_responses':[],
        'final_content':None ,
        'conversation_saved':False 
        }

        self ._tool_completion_blocks_created .clear ()
        self ._tool_start_blocks_created .clear ()

        self ._active_tool_components .clear ()

        self ._last_sent_prompt =None 
        logger .debug ("Reset conversation tracking state")

    def _track_assistant_message (self ,message_id :str ,content :str =""):
        """Track assistant message details."""
        self ._conversation_tracking ['assistant_message_id']=message_id 
        if content :
            self ._conversation_tracking ['final_content']=content 
        logger .debug (f"Tracked assistant message: {message_id}")

    def _track_tool_call (self ,tool_call_data :dict ):
        """Track tool call information."""
        call_id =tool_call_data .get ('call_id')


        for existing_call in self ._conversation_tracking ['tool_calls']:
            if existing_call .get ('call_id')==call_id :
                return 

        self ._conversation_tracking ['tool_calls'].append (tool_call_data )
        logger .debug (f"Tracked tool call: {tool_call_data.get('function', {}).get('name', 'unknown')} (call_id: {call_id})")

    def _track_tool_response (self ,tool_response_data :dict ):
        """Track tool response information."""
        call_id =tool_response_data .get ('call_id')


        for existing_response in self ._conversation_tracking ['tool_responses']:
            if existing_response .get ('call_id')==call_id :
                return 

        self ._conversation_tracking ['tool_responses'].append (tool_response_data )
        logger .debug (f"Tracked tool response for call_id: {call_id}")

    def _save_conversation_to_history (self ):
        """Save the complete conversation turn to history with perfect ordering."""
        if self ._conversation_tracking ['conversation_saved']:
            logger .debug ("Conversation already saved to history")
            return 

        try :
            import bpy 
            context =bpy .context 

            from ...utils .history_manager import history_manager 


            user_message =self ._conversation_tracking ['user_message']
            if user_message :
                history_manager .add_message (context ,"user",user_message )
                logger .info (f"✓ Saved USER message: '{user_message[:50]}...'")


            final_content =self ._conversation_tracking ['final_content']
            assistant_message_id =self ._conversation_tracking ['assistant_message_id']
            tool_calls =self ._conversation_tracking ['tool_calls']

            if final_content or tool_calls :

                openai_tool_calls =None 
                if tool_calls :

                    sorted_tool_calls =sorted (tool_calls ,key =lambda x :x .get ('call_id',''))
                    openai_tool_calls =[]
                    for tool_call in sorted_tool_calls :
                        openai_tool_calls .append ({
                        "id":tool_call .get ('call_id',f"call_{len(openai_tool_calls)}"),
                        "type":"function",
                        "function":{
                        "name":tool_call .get ('function',{}).get ('name','unknown'),
                        "arguments":tool_call .get ('function',{}).get ('arguments','{}')
                        }
                        })


                history_manager .add_message (
                context ,
                "assistant",
                final_content or "",
                tool_calls =openai_tool_calls 
                )
                logger .info (f"✓ Saved ASSISTANT message: '{(final_content or '')[:50]}...' with {len(tool_calls) if tool_calls else 0} tool calls")


            if self ._conversation_tracking ['tool_responses']:

                sorted_tool_responses =sorted (
                self ._conversation_tracking ['tool_responses'],
                key =lambda x :x .get ('call_id','')
                )
                for tool_response in sorted_tool_responses :

                    simple_response_text =tool_response .get ("ui_message")or tool_response .get ("content","Tool response")

                    history_manager .add_message (
                    context ,
                    "tool",
                    simple_response_text ,
                    tool_call_id =tool_response .get ("call_id")
                    )
                    logger .debug (f"✓ Saved TOOL response for call_id: {tool_response.get('call_id')} as simple text: '{simple_response_text}'")


            if self ._conversation_tracking ['tool_responses']:
                for tool_response in sorted_tool_responses :

                    if 'image_data'in tool_response and tool_response ['image_data']:
                        image_data_info =tool_response ['image_data']
                        data_uri =image_data_info .get ('data_uri')
                        message_text =image_data_info .get ('message_text')
                        call_id =tool_response .get ('call_id')

                        if data_uri and message_text and call_id :

                            success =history_manager .add_message_after_tool_response (
                            context ,
                            "user",
                            message_text ,
                            call_id ,
                            image_data =data_uri 
                            )

                            if success :

                                logger .info (f"✅ Image data saved to history (UI display disabled): {message_text}")
                            else :
                                logger .warning (f"Failed to create image message after tool response {call_id}")


            self ._conversation_tracking ['conversation_saved']=True 


            msg_count =(1 if user_message else 0 )+(1 if final_content or tool_calls else 0 )+len (self ._conversation_tracking ['tool_responses'])
            logger .info (f"✅ Complete conversation saved to history with {msg_count} messages in perfect order")

        except Exception as e :
            logger .error (f"❌ Failed to save conversation to history: {str(e)}")
            import traceback 
            logger .error (traceback .format_exc ())

    def handle_message_send (self ,text :str ):
        """Shared function for handling message sending from both send button and Enter key."""
        if text .strip ():

            self ._handle_send_with_text (text .strip ())

    def _handle_send_with_text (self ,text :str ):
        """Handle sending with specific text (for Enter key support)."""
        if not self .components :
            return 


        if self ._is_generating :
            logger .warning ("Generation already in progress")
            return 

        try :

            try :
                context =bpy .context 
                from ...utils .history_manager import history_manager 
                current_chat_id =getattr (context .scene ,'vibe4d_current_chat_id','')
                if current_chat_id :
                    history_manager .clear_unsent_text (context ,current_chat_id )
            except Exception as e :
                logger .debug (f"Could not clear unsent text: {e}")


            self .factory .add_message_to_scrollview (self .components ,text ,is_ai_response =False )


            self ._is_generating =True 
            self ._last_content_length =0 
            self ._last_tool_call_state =None 
            self ._content_after_tool_call =False 
            self .factory ._set_send_button_mode (False )


            self ._current_ai_component =self .factory .add_markdown_message_to_scrollview (self .components ,"",is_ai_response =True )


            self ._start_real_api_generation (text )

            if self .state .target_area :
                self .state .target_area .tag_redraw ()

        except Exception as e :
            logger .error (f"Error in _handle_send_with_text: {e}")
            self ._reset_generation_state ()

    def _handle_add (self ):
        """Handle add button click - start a new chat session."""
        try :
            logger .info ("Add button clicked - starting new chat session")


            self ._reset_generation_state ()


            message_scrollview =None 
            try :
                current_view =self .factory .get_current_view ()
                if current_view and hasattr (current_view ,'get_message_scrollview'):
                    message_scrollview =current_view .get_message_scrollview ()
                    if message_scrollview :
                        message_scrollview .children .clear ()
                        message_scrollview ._update_content_bounds ()
                        logger .info ("Cleared message scrollview UI")
            except Exception as e :
                logger .error (f"Error clearing message scrollview: {e}")


            try :
                context =bpy .context 


                from ...utils .history_manager import history_manager 
                new_chat_id =history_manager .create_new_chat (context )

                logger .info (f"✅ Started new chat: {new_chat_id}")

            except Exception as e :
                logger .error (f"Failed to start new chat: {str(e)}")


            try :
                context =bpy .context 
                context .scene .vibe4d_output_content =""
                context .scene .vibe4d_final_code =""
                context .scene .vibe4d_guide_content =""
                context .scene .vibe4d_last_error =""
                context .scene .vibe4d_console_output =""
                context .scene .vibe4d_is_generating =False 
                logger .info ("Cleared scene-level chat state")
            except Exception as e :
                logger .error (f"Error clearing scene state: {e}")


            if self .state .target_area :
                self .state .target_area .tag_redraw ()

            logger .info ("✅ Ready for new chat session")

        except Exception as e :
            logger .error (f"Error in _handle_add: {e}")

            self ._reset_generation_state ()

    def _handle_history (self ):
        """Handle history button click."""
        logger .info ("History button clicked")

        self .factory .switch_to_view (ViewState .HISTORY )

    def _handle_settings (self ):
        """Handle settings button click."""
        logger .info ("Settings button clicked")

        self .factory .switch_to_view (ViewState .SETTINGS )

    def _handle_model_change (self ,selected_model :str ):
        """Handle model dropdown change."""
        logger .info (f"Model changed to: {selected_model}")

        try :

            context =bpy .context 


            model_mapping ={
            "GPT 4.1":"gpt-4.1",
            "GPT 4.1 Mini":"gpt-4.1-mini",
            "GPT 4.1 Nano":"gpt-4.1-nano"
            }


            internal_model =model_mapping .get (selected_model ,selected_model .lower ().replace (" ","-"))


            context .scene .vibe4d_model =internal_model 

            logger .info (f"Updated unified model to: {internal_model}")

        except Exception as e :
            logger .error (f"Error updating model selection: {e}")

    def _handle_auth_submit (self ):
        """Handle authentication/license submission."""
        logger .info ("Auth submit clicked")


        current_view =self .factory .views .get (self .factory .current_view )
        if current_view and hasattr (current_view ,'get_license_key'):
            license_key =current_view .get_license_key ()
        else :
            license_key =""

        if license_key :
            logger .info (f"Processing license key: {license_key[:10]}...")


            self ._authenticate_success ()
        else :
            logger .warning ("No license key provided")

    def _handle_get_license (self ):
        """Handle get license link click."""
        logger .info ("Get license clicked")



    def _authenticate_success (self ):
        """Handle successful authentication."""
        logger .info ("Authentication successful")


        self .factory .switch_to_view (ViewState .MAIN )

    def enable_overlay (self ,target_area =None ):
        """Enable the custom overlay."""
        try :
            logger .info ("Enabling UI overlay")

            self .state .target_area =target_area 
            self .state .is_enabled =True 


            self ._original_workspace =bpy .context .window .workspace 
            self ._original_screen =bpy .context .window .screen 


            self ._current_ui_scale =CoordinateSystem .get_ui_scale ()
            self ._ui_scale_check_counter =0 


            try :
                ui_state_manager .save_ui_state (bpy .context ,self ,target_area )
            except Exception as e :
                logger .debug (f"Could not save UI state: {e}")


            theme_manager .update_if_changed ()


            logger .info ("Determining initial view based on connectivity and auth status")
            self .factory .switch_to_appropriate_view_on_startup ()


            if self .draw_handler is None :
                self .draw_handler =SpaceView3D .draw_handler_add (
                self ._draw_callback ,(),'WINDOW','POST_PIXEL'
                )
                logger .info ("Draw handler registered")


            if self .cursor_redraw_handler is None :
                self .cursor_redraw_handler =bpy .app .timers .register (self ._enforce_ui_settings ,first_interval =self .performance_config .timer_interval )
                logger .info (f"UI enforcement timer started with {self.performance_config.timer_interval}s interval")


            try :
                bpy .ops .vibe4d .ui_modal_handler ('INVOKE_DEFAULT')
                logger .info ("Modal handler started")
            except Exception as e :
                logger .warning (f"Failed to start modal handler: {e}")


            self ._redraw_viewports ()


            def delayed_init_check ():
                """Check if UI initialized properly after a short delay."""
                try :
                    import bpy 

                    if self .state .is_enabled and self .state .target_area :
                        if not self .ui_layout or not self .state .components :
                            logger .warning ("UI not fully initialized, attempting reinitialization")

                            success =self .force_ui_reinitialization ()
                            if success :
                                logger .info ("✅ UI reinitialization successful")
                            else :
                                logger .error ("❌ UI reinitialization failed")

                                def retry_init ():
                                    try :
                                        import bpy 

                                        if self .state .is_enabled and self .state .target_area :
                                            if not self .ui_layout or not self .state .components :
                                                logger .warning ("Retrying UI initialization...")
                                                self .force_ui_reinitialization ()
                                        return None 
                                    except Exception as e :
                                        logger .error (f"Error in retry init: {e}")
                                        return None 


                                bpy .app .timers .register (retry_init ,first_interval =1.0 )
                        else :
                            logger .info (f"✅ UI overlay enabled successfully with {len(self.state.components)} components")
                    return None 
                except Exception as e :
                    logger .error (f"Error in delayed init check: {e}")
                    return None 


            bpy .app .timers .register (delayed_init_check ,first_interval =0.5 )

        except Exception as e :
            logger .error (f"Error enabling overlay: {e}")
            import traceback 
            logger .error (traceback .format_exc ())
            raise 

    def disable_overlay (self ):
        """Disable the custom UI overlay."""
        if not self .state .is_enabled :
            return 

        logger .info ("Disabling UI overlay")


        try :
            ui_state_manager .clear_ui_state (bpy .context )
        except Exception as e :
            logger .debug (f"Could not clear UI state: {e}")


        if self .draw_handler :
            bpy .types .SpaceView3D .draw_handler_remove (self .draw_handler ,'WINDOW')
            self .draw_handler =None 


        if self ._resize_timer is not None :
            try :
                bpy .app .timers .unregister (self ._resize_timer )
            except :
                pass 
            self ._resize_timer =None 
            self ._pending_viewport_size =None 


        if hasattr (self ,'_cursor_timer'):
            try :
                bpy .app .timers .unregister (self ._cursor_timer )
            except :
                pass 
            del self ._cursor_timer 


        if hasattr (self ,'_animation_timer'):
            try :
                bpy .app .timers .unregister (self ._animation_timer )
            except :
                pass 
            del self ._animation_timer 


        if self .cursor_redraw_handler :
            bpy .app .timers .unregister (self .cursor_redraw_handler )
            self .cursor_redraw_handler =None 


        self .state .is_enabled =False 
        self .state .target_area =None 
        self .state .components .clear ()
        self .state .focused_component =None 


        if hasattr (self ,'_original_workspace'):
            del self ._original_workspace 
        if hasattr (self ,'_original_screen'):
            del self ._original_screen 


        self ._current_ui_scale =None 
        self ._ui_scale_check_counter =0 


        self ._ui_recreation_in_progress =False 
        self ._ui_recreation_lock_start_time =None 


        self .reset_cursor_to_default ()


        self .factory .cleanup ()


        self ._redraw_viewports ()

    def _draw_callback (self ):
        """Main draw callback with optimized rendering."""
        try :
            if not self .state .is_enabled or not self .state .target_area :
                logger .debug ("Draw callback: UI not enabled or no target area")
                return 


            context =bpy .context 
            region =context .region 
            area =context .area 


            if not region or area !=self .state .target_area :



                return 


            new_width ,new_height =region .width ,region .height 
            viewport_changed =False 
            if (self .state .viewport_width !=new_width or 
            self .state .viewport_height !=new_height ):


                is_initial_draw =(self .state .viewport_width ==0 or self .state .viewport_height ==0 )

                if is_initial_draw :

                    logger .info (f"Initial viewport setup: {new_width}x{new_height}")
                    self .state .update_viewport_size (new_width ,new_height )


                    if self .ui_layout is None :
                        logger .info ("Initializing UI layout")
                        self ._initialize_ui_layout ()
                    else :
                        logger .info ("Updating UI layout")
                        self ._update_layout ()

                    viewport_changed =True 
                else :

                    self ._pending_viewport_size =(new_width ,new_height )


                    if self ._resize_timer is not None :
                        bpy .app .timers .unregister (self ._resize_timer )
                        self ._resize_timer =None 


                    self ._resize_timer =bpy .app .timers .register (
                    self ._on_viewport_resize_finished ,
                    first_interval =self ._viewport_resize_debounce_delay 
                    )

                    viewport_changed =True 
                    logger .debug (f"Viewport resizing: {self.state.viewport_width}x{self.state.viewport_height} -> {new_width}x{new_height}")


                for component in self .state .components :
                    if hasattr (component ,'_render_dirty'):
                        component ._render_dirty =True 


            if self .ui_layout is None :
                logger .info ("No UI layout, trying to initialize")
                self ._initialize_ui_layout ()
                if self .ui_layout is None :
                    logger .warning ("Failed to initialize UI layout, skipping drawing")

                    self ._draw_error_message (region )
                    return 


            if not self .state .components :
                logger .warning ("No components to draw, attempting to reinitialize")
                self ._initialize_ui_layout ()
                if not self .state .components :
                    logger .error ("Still no components after reinitialization")
                    self ._draw_error_message (region )
                    return 


            bg_bounds =Bounds (0 ,0 ,region .width ,region .height )
            bg_color =Colors .Panel 
            self .renderer .draw_rect (bg_bounds ,bg_color )


            visible_components =[c for c in self .state .components if c .is_visible ()]

            if not visible_components :
                logger .warning ("No visible components to draw")
                self ._draw_error_message (region )
                return 


            has_animations =False 

            for component in visible_components :
                try :
                    component .render (self .renderer )


                    if hasattr (component ,'elements'):
                        for element in component .elements :
                            if hasattr (element ,'is_animated')and element .is_animated :
                                has_animations =True 
                                break 


                    if hasattr (component ,'is_animated')and component .is_animated :
                        has_animations =True 
                except Exception as e :
                    logger .error (f"Error rendering component {type(component).__name__}: {e}")
                    continue 


            if self .state .focused_component and isinstance (self .state .focused_component ,TextInput ):
                self ._schedule_cursor_redraw ()


            if has_animations :
                self ._schedule_animation_redraw ()

        except Exception as e :
            logger .error (f"Error in draw callback: {e}")
            import traceback 
            logger .error (traceback .format_exc ())

            try :
                if region :
                    self ._draw_error_message (region )
            except :
                pass 

    def _draw_error_message (self ,region ):
        """Draw a simple error message when UI fails to load."""
        try :

            bg_bounds =Bounds (0 ,0 ,region .width ,region .height )
            bg_color =(0.1 ,0.1 ,0.1 ,0.9 )
            self .renderer .draw_rect (bg_bounds ,bg_color )


            error_text ="UI Loading Error - Please try reopening"
            text_bounds =Bounds (10 ,region .height //2 ,region .width -20 ,30 )


            from .components import Label 
            error_label =Label (error_text ,text_bounds .x ,text_bounds .y ,text_bounds .width ,text_bounds .height )
            error_label .style .text_color =(1.0 ,0.3 ,0.3 ,1.0 )
            error_label .render (self .renderer )

        except Exception as e :
            logger .error (f"Error drawing error message: {e}")

    def _schedule_animation_redraw (self ):
        """Schedule redraw for animations - OPTIMIZED."""
        import time 
        current_time =time .time ()


        animation_interval =self .performance_config .get_animation_interval ()


        if not hasattr (self ,'_animation_timer'):

            has_active_animations =self ._check_for_active_animations ()
            if has_active_animations :
                self ._animation_timer =bpy .app .timers .register (
                lambda :self ._animation_redraw_callback (),
                first_interval =animation_interval 
                )

    def _check_for_active_animations (self )->bool :
        """Check if there are actually active animations before scheduling timer."""
        try :
            if not self .state .components :
                return False 

            visible_components =[c for c in self .state .components if c .is_visible ()]

            for component in visible_components :

                if hasattr (component ,'elements'):
                    for element in component .elements :
                        if hasattr (element ,'is_animated')and element .is_animated :
                            return True 


                if hasattr (component ,'is_animated')and component .is_animated :
                    return True 

            return False 
        except Exception :
            return False 

    def _animation_redraw_callback (self ):
        """Timer callback for animation redraw - OPTIMIZED."""
        try :

            if hasattr (self ,'_animation_timer'):
                del self ._animation_timer 


            if self ._is_ui_recreation_locked ():
                logger .debug ("Animation redraw skipped - UI recreation in progress")
                return None 


            if self .state .is_enabled and self .state .target_area :

                has_animations =self ._check_for_active_animations ()

                if has_animations :

                    self ._selective_redraw ()

                    return self .performance_config .get_animation_interval ()

            return None 
        except Exception as e :
            logger .error (f"Error in animation redraw callback: {e}")
            if hasattr (self ,'_animation_timer'):
                del self ._animation_timer 
            return None 

    def _schedule_cursor_redraw (self ):
        """Schedule next redraw for cursor animation only when needed - OPTIMIZED."""
        import time 
        current_time =time .time ()


        cursor_cycle_time =self .performance_config .cursor_blink_cycle 
        time_in_cycle =current_time %cursor_cycle_time 


        visible_time =cursor_cycle_time *0.67 


        if time_in_cycle <visible_time :

            next_redraw =visible_time -time_in_cycle 
        else :

            next_redraw =cursor_cycle_time -time_in_cycle 


        if (next_redraw >0.01 and not hasattr (self ,'_cursor_timer')and 
        self .state .focused_component and 
        hasattr (self .state .focused_component ,'__class__')and 
        'TextInput'in str (self .state .focused_component .__class__ )):

            self ._cursor_timer =bpy .app .timers .register (
            lambda :self ._cursor_redraw_callback (),
            first_interval =next_redraw 
            )

    def _cursor_redraw_callback (self ):
        """Timer callback for cursor redraw - OPTIMIZED."""
        try :

            if hasattr (self ,'_cursor_timer'):
                del self ._cursor_timer 


            if self ._is_ui_recreation_locked ():
                logger .debug ("Cursor redraw skipped - UI recreation in progress")
                return None 


            if (self .state .is_enabled and self .state .target_area and 
            self .state .focused_component and 
            hasattr (self .state .focused_component ,'__class__')and 
            'TextInput'in str (self .state .focused_component .__class__ )):


                self ._selective_redraw ()

                return None 

            return None 
        except Exception as e :
            logger .error (f"Error in cursor redraw callback: {e}")
            if hasattr (self ,'_cursor_timer'):
                del self ._cursor_timer 
            return None 

    def _enforce_ui_settings (self ):
        """Timer function to enforce UI settings and detect area closure - OPTIMIZED."""
        try :

            if not self .state .is_enabled or not self .state .target_area :
                return self .performance_config .timer_interval 


            if self ._is_ui_recreation_locked ():
                logger .debug ("UI enforcement skipped - UI recreation in progress")
                return self .performance_config .timer_interval 


            needs_redraw =False 


            if self .performance_config .should_check_ui_scale (self ._ui_scale_check_counter ):
                if self ._check_ui_scale_changes ():
                    self ._handle_ui_scale_change ()

                    return self .performance_config .timer_interval 
                self ._ui_scale_check_counter =0 
            else :
                self ._ui_scale_check_counter +=1 


            if self .performance_config .should_check_theme (self ._theme_check_counter ):
                if self ._check_theme_changes ():

                    self ._refresh_all_component_themes ()
                    needs_redraw =True 
                self ._theme_check_counter =0 
            else :
                self ._theme_check_counter +=1 


            if not self ._verify_target_area_exists ():

                self ._cleanup_on_area_closure ()
                return None 


            if self .performance_config .should_enforce_viewport (self ._viewport_enforce_counter ):
                if self ._enforce_view3d_settings ():
                    needs_redraw =True 
                self ._viewport_enforce_counter =0 
            else :
                self ._viewport_enforce_counter +=1 


            if needs_redraw :
                self ._request_redraw ()

            return self .performance_config .timer_interval 

        except Exception as e :
            logger .error (f"Error enforcing UI settings: {e}")
            self ._handle_enforcement_error ()
            return None 

    def _should_check_ui_scale (self )->bool :
        """Determine if UI scale should be checked this iteration - CONFIGURABLE."""
        return self .performance_config .should_check_ui_scale (self ._ui_scale_check_counter )

    def _should_check_theme_changes (self )->bool :
        """Determine if theme changes should be checked this iteration - CONFIGURABLE."""
        return self .performance_config .should_check_theme (self ._theme_check_counter )

    def _should_enforce_viewport_settings (self )->bool :
        """Determine if viewport settings should be enforced - CONFIGURABLE."""
        return self .performance_config .should_enforce_viewport (getattr (self ,'_viewport_enforce_counter',0 ))

    def _check_theme_changes (self )->bool :
        """Check if theme has changed."""
        try :
            return theme_manager .check_for_changes ()
        except Exception as e :
            logger .error (f"Error checking theme changes: {e}")
            return False 

    def _refresh_all_component_themes (self ):
        """Refresh themes for all components when Blender theme changes."""
        try :

            for component in self .state .components :
                if hasattr (component ,'refresh_theme'):
                    component .refresh_theme ()

            logger .debug ("Refreshed themes for all components")

        except Exception as e :
            logger .error (f"Error refreshing component themes: {e}")

    def _verify_target_area_exists (self )->bool :
        """Verify that the target area still exists in any screen."""
        try :

            current_screen =bpy .context .screen 
            if current_screen and any (area ==self .state .target_area for area in current_screen .areas ):
                return True 


            for screen in bpy .data .screens :
                if any (area ==self .state .target_area for area in screen .areas ):
                    return True 

            return False 

        except Exception as e :
            logger .error (f"Error verifying target area exists: {e}")
            return False 

    def _cleanup_on_area_closure (self ):
        """Clean up UI state when target area is closed externally."""
        try :


            bpy .context .window_manager .vibe4d_ui_was_active =False 

        except Exception as e :
            logger .debug (f"Could not clear UI state tracking: {e}")


        self .disable_overlay ()

    def _enforce_view3d_settings (self )->bool :
        """Enforce UI settings on VIEW_3D spaces. Returns True if settings were applied."""
        try :
            settings_applied =False 

            for space in self .state .target_area .spaces :
                if space .type =='VIEW_3D':

                    space .show_gizmo =False 
                    space .show_region_ui =False 
                    space .show_region_toolbar =False 
                    space .show_region_header =False 
                    space .show_region_hud =False 
                    space .overlay .show_overlays =False 


                    space .shading .show_xray =False 
                    space .shading .show_shadows =False 
                    space .shading .show_cavity =False 
                    space .shading .show_object_outline =False 
                    space .shading .show_specular_highlight =False 
                    space .shading .show_backface_culling =True 
                    space .shading .use_world_space_lighting =False 


                    if hasattr (space .shading ,'show_cavity_edge'):
                        space .shading .show_cavity_edge =False 
                    if hasattr (space .shading ,'show_cavity_ridge'):
                        space .shading .show_cavity_ridge =False 
                    if hasattr (space .shading ,'show_cavity_valley'):
                        space .shading .show_cavity_valley =False 


                    if hasattr (space ,'show_region_tool_header'):
                        space .show_region_tool_header =False 
                    if hasattr (space ,'show_region_asset_shelf'):
                        space .show_region_asset_shelf =False 


                    if space .shading .type not in ['SOLID']:

                        pass 


                    space .shading .use_dof =False 
                    if hasattr (space .shading ,'use_world_space_lighting'):
                        space .shading .use_world_space_lighting =False 


                    space .clip_start =max (space .clip_start ,0.1 )
                    space .clip_end =min (space .clip_end ,100.0 )

                    settings_applied =True 
                    break 

            return settings_applied 

        except Exception as e :
            logger .error (f"Error enforcing VIEW_3D settings: {e}")
            return False 

    def _request_redraw (self ):
        """Centralized method to request selective area redraw - UI only when possible."""
        try :
            if self .state .target_area :

                self ._selective_redraw ()
        except Exception as e :
            logger .error (f"Error requesting redraw: {e}")

    def _selective_redraw (self ):
        """Implement selective redraw to minimize scene rerendering."""
        try :

            if self .state .target_area :

                if hasattr (self .state .target_area ,'tag_redraw'):

                    self .state .target_area .tag_redraw ()

        except Exception as e :
            logger .error (f"Error in selective redraw: {e}")

            if self .state .target_area :
                self .state .target_area .tag_redraw ()

    def _handle_enforcement_error (self ):
        """Handle errors that occur during UI enforcement."""
        try :
            logger .info ("Attempting cleanup due to enforcement error")
            self .disable_overlay ()
        except Exception as cleanup_error :
            logger .error (f"Error during cleanup: {cleanup_error}")

    def is_ui_active (self )->bool :
        """Check if the UI is currently active and the area exists."""
        if not self .state .is_enabled or not self .state .target_area :
            return False 


        try :

            if bpy .context .screen :
                return any (area ==self .state .target_area for area in bpy .context .screen .areas )
        except :
            pass 

        return False 

    def _redraw_viewports (self ):
        """Force redraw of all 3D viewports."""
        try :
            for area in bpy .context .screen .areas :
                if area .type =='VIEW_3D':
                    area .tag_redraw ()
        except Exception as e :
            logger .error (f"Error redrawing viewports: {e}")

    def handle_mouse_event (self ,context ,event )->str :
        """Handle mouse events."""
        try :

            if not self .state .is_enabled or not self .state .target_area :
                return 'PASS_THROUGH'


            if (hasattr (self ,'_original_workspace')and hasattr (self ,'_original_screen')and 
            (bpy .context .window .workspace !=self ._original_workspace or 
            bpy .context .window .screen !=self ._original_screen )):

                return 'PASS_THROUGH'


            if not self ._mouse_in_target_area (event ):

                if self ._last_hovered_component :
                    from .types import UIEvent ,EventType 
                    leave_event =UIEvent (EventType .MOUSE_LEAVE ,event .mouse_x ,event .mouse_y )
                    self ._last_hovered_component .handle_event (leave_event )
                    self ._last_hovered_component =None 

                    self .state .target_area .tag_redraw ()


                self .reset_cursor_to_default ()
                return 'PASS_THROUGH'


            mouse_x ,mouse_y =self ._screen_to_region_coords (event ,self .state .target_area )

            if mouse_x is None or mouse_y is None :
                return 'PASS_THROUGH'


            self .state .mouse_x =mouse_x 
            self .state .mouse_y =mouse_y 


            self ._update_cursor_for_mouse_position (mouse_x ,mouse_y )


            if event .type =='LEFTMOUSE'and event .value =='PRESS':


                component =self .state .get_component_at_point (mouse_x ,mouse_y )

                if component :

                    self ._mouse_pressed =True 
                    self ._mouse_pressed_component =component 


                    from .types import UIEvent ,EventType 
                    ui_event =UIEvent (EventType .MOUSE_PRESS ,mouse_x ,mouse_y )
                    result =component .handle_event (ui_event )
                else :

                    self .state .set_focus (None )
                    self ._mouse_pressed =False 
                    self ._mouse_pressed_component =None 

                self .state .target_area .tag_redraw ()
                return 'RUNNING_MODAL'

            elif event .type =='LEFTMOUSE'and event .value =='RELEASE':


                if self ._mouse_pressed and self ._mouse_pressed_component :
                    from .types import UIEvent ,EventType 
                    ui_event =UIEvent (EventType .MOUSE_RELEASE ,mouse_x ,mouse_y )
                    result =self ._mouse_pressed_component .handle_event (ui_event )


                    current_component =self .state .get_component_at_point (mouse_x ,mouse_y )
                    if current_component ==self ._mouse_pressed_component :
                        click_event =UIEvent (EventType .MOUSE_CLICK ,mouse_x ,mouse_y )
                        click_result =self ._mouse_pressed_component .handle_event (click_event )

                        if click_result :
                            result =click_result 


                self ._mouse_pressed =False 
                self ._mouse_pressed_component =None 

                self .state .target_area .tag_redraw ()
                return 'RUNNING_MODAL'

            elif event .type =='MOUSEMOVE'and self ._mouse_pressed and self ._mouse_pressed_component :


                from .types import UIEvent ,EventType 
                ui_event =UIEvent (EventType .MOUSE_DRAG ,mouse_x ,mouse_y )
                result =self ._mouse_pressed_component .handle_event (ui_event )

                self .state .target_area .tag_redraw ()
                return 'RUNNING_MODAL'

            elif event .type =='MOUSEMOVE'and not self ._mouse_pressed :


                component =self .state .get_component_at_point (mouse_x ,mouse_y )


                if self ._last_hovered_component and self ._last_hovered_component !=component :
                    from .types import UIEvent ,EventType 
                    leave_event =UIEvent (EventType .MOUSE_LEAVE ,mouse_x ,mouse_y )
                    self ._last_hovered_component .handle_event (leave_event )


                if component and component !=self ._last_hovered_component :
                    from .types import UIEvent ,EventType 
                    enter_event =UIEvent (EventType .MOUSE_ENTER ,mouse_x ,mouse_y )
                    component .handle_event (enter_event )


                if component :
                    from .types import UIEvent ,EventType 
                    ui_event =UIEvent (EventType .MOUSE_MOVE ,mouse_x ,mouse_y )
                    result =component .handle_event (ui_event )


                    if result :
                        self .state .target_area .tag_redraw ()


                self ._last_hovered_component =component 

                return 'RUNNING_MODAL'


            elif event .type in {'WHEELUPMOUSE','WHEELDOWNMOUSE'}and event .value =='PRESS':


                component =self .state .get_component_at_point (mouse_x ,mouse_y )
                if component :
                    from .types import UIEvent ,EventType 


                    wheel_direction ='UP'if event .type =='WHEELUPMOUSE'else 'DOWN'
                    ui_event =UIEvent (
                    EventType .MOUSE_WHEEL ,
                    mouse_x ,
                    mouse_y ,
                    data ={'wheel_direction':wheel_direction }
                    )

                    result =component .handle_event (ui_event )

                    if result :
                        self .state .target_area .tag_redraw ()
                        return 'RUNNING_MODAL'


            if event .type in {'LEFTMOUSE','RIGHTMOUSE','MIDDLEMOUSE','WHEELUPMOUSE','WHEELDOWNMOUSE','MOUSEMOVE','INBETWEEN_MOUSEMOVE'}:
                return 'RUNNING_MODAL'

            return 'PASS_THROUGH'
        except Exception as e :
            logger .error (f"Error handling mouse event: {e}")
            return 'PASS_THROUGH'

    def handle_keyboard_event (self ,context ,event )->str :
        """Handle keyboard events - pass all to focused component when available."""
        try :
            if not self .state .is_enabled or not self .state .target_area :
                return 'PASS_THROUGH'


            if (hasattr (self ,'_original_workspace')and hasattr (self ,'_original_screen')and 
            (bpy .context .window .workspace !=self ._original_workspace or 
            bpy .context .window .screen !=self ._original_screen )):

                return 'PASS_THROUGH'


            if self .state .focused_component :
                consumed =False 


                from .types import UIEvent ,EventType 

                if event .value =='PRESS':

                    key_name =event .type 


                    modifiers =[]
                    if event .ctrl :
                        modifiers .append ('CTRL')
                    if event .shift :
                        modifiers .append ('SHIFT')
                    if event .alt :
                        modifiers .append ('ALT')


                    if modifiers :
                        key_name ='_'.join (modifiers )+'_'+event .type 


                    if (not modifiers or (len (modifiers )==1 and 'SHIFT'in modifiers ))and len (event .unicode )==1 and event .unicode .isprintable ():

                        ui_event =UIEvent (EventType .TEXT_INPUT ,unicode =event .unicode )
                        consumed =self .state .focused_component .handle_event (ui_event )
                    else :

                        ui_event =UIEvent (EventType .KEY_PRESS ,key =key_name )
                        consumed =self .state .focused_component .handle_event (ui_event )



                    if event .type =='SPACE'and not modifiers and (len (event .unicode )!=1 or not event .unicode .isprintable ()):
                        ui_event =UIEvent (EventType .TEXT_INPUT ,unicode =' ')
                        consumed =self .state .focused_component .handle_event (ui_event )


                if consumed :
                    self .state .target_area .tag_redraw ()
                    return 'RUNNING_MODAL'
                else :


                    from .components import TextInput 
                    if isinstance (self .state .focused_component ,TextInput ):
                        return 'RUNNING_MODAL'

            return 'PASS_THROUGH'
        except Exception as e :
            logger .error (f"Error handling keyboard event: {e}")
            return 'PASS_THROUGH'

    def _mouse_in_target_area (self ,event )->bool :
        """Check if mouse is in target area."""
        if not self .state .target_area :
            return False 

        return (self .state .target_area .x <=event .mouse_x <=self .state .target_area .x +self .state .target_area .width and 
        self .state .target_area .y <=event .mouse_y <=self .state .target_area .y +self .state .target_area .height )

    def _screen_to_region_coords (self ,event ,area )->Tuple [Optional [int ],Optional [int ]]:
        """Convert screen coordinates to area coordinates using centralized system."""
        if not area :
            return None ,None 

        for region in area .regions :
            if region .type =='WINDOW':

                region_x ,region_y =CoordinateSystem .screen_to_region (
                event .mouse_x ,event .mouse_y ,area ,region 
                )


                if 0 <=region_x <=area .width and 0 <=region_y <=area .height :
                    return region_x ,region_y 

        return None ,None 

    def _check_ui_scale_changes (self )->bool :
        """Check if UI scale has changed since last check.
        
        Note: UI scale changes are rare user actions, so we prioritize correctness
        over performance. Complete UI recreation ensures all components are properly
        rebuilt with new scaled values, avoiding potential issues with cached state.
        """
        try :
            current_scale =CoordinateSystem .get_ui_scale ()

            if self ._current_ui_scale is None :

                self ._current_ui_scale =current_scale 
                return False 

            if abs (current_scale -self ._current_ui_scale )>0.01 :
                logger .info (f"UI scale changed: {self._current_ui_scale} -> {current_scale}")
                self ._current_ui_scale =current_scale 
                return True 

            return False 
        except Exception as e :
            logger .error (f"Error checking UI scale changes: {e}")
            return False 

    def _handle_ui_scale_change (self ):
        """Handle UI scale change by triggering complete UI recreation."""
        try :
            logger .info ("Handling UI scale change - triggering complete UI recreation")


            self ._set_ui_recreation_lock (True )


            current_focused_component =self .state .focused_component 



            if self .state .viewport_width >0 and self .state .viewport_height >0 :
                self ._recreate_ui_for_view_change (is_view_change =False )
                logger .info ("UI completely recreated for scale change")


                if current_focused_component is not None :

                    for component in self .state .components :
                        if type (component )==type (current_focused_component ):

                            self .state .set_focus (component )
                            logger .info (f"Restored focus to {type(component).__name__} after UI scale change")
                            break 
                    else :
                        logger .info ("Could not restore focus after UI scale change - no matching component found")
            else :
                logger .warning ("Cannot recreate UI for scale change - invalid viewport dimensions")

        except Exception as e :
            logger .error (f"Error handling UI scale change: {e}")

            try :
                if self .ui_layout and self .state .viewport_width >0 and self .state .viewport_height >0 :
                    self ._update_layout ()
                    logger .info ("Fallback: Updated layout after UI recreation failed")


                if self .state .target_area :
                    self .state .target_area .tag_redraw ()
            except Exception as fallback_error :
                logger .error (f"Fallback layout update also failed: {fallback_error}")
        finally :

            self ._set_ui_recreation_lock (False )

    def _set_ui_recreation_lock (self ,locked :bool ):
        """Set or clear the UI recreation lock to prevent timer conflicts."""
        self ._ui_recreation_in_progress =locked 
        if locked :
            self ._ui_recreation_lock_start_time =time .time ()
            logger .debug ("UI recreation lock SET - blocking conflicting timers")
        else :
            lock_duration =time .time ()-(self ._ui_recreation_lock_start_time or 0 )
            self ._ui_recreation_lock_start_time =None 
            logger .debug (f"UI recreation lock CLEARED after {lock_duration:.3f}s")

    def _is_ui_recreation_locked (self )->bool :
        """Check if UI recreation is currently in progress."""

        if (self ._ui_recreation_in_progress and self ._ui_recreation_lock_start_time and 
        time .time ()-self ._ui_recreation_lock_start_time >5.0 ):
            logger .warning ("UI recreation lock timeout - forcing unlock")
            self ._set_ui_recreation_lock (False )
            return False 
        return self ._ui_recreation_in_progress 

    def set_cursor (self ,cursor_type :CursorType ,is_override :bool =False ):
        """Request cursor change through modal operator context.
        
        Args:
            cursor_type: The cursor type to set
            is_override: If True, this is a temporary override that can be cleared
        """
        try :
            self ._cursor_requests .append ({
            'action':'set',
            'cursor_type':cursor_type ,
            'is_override':is_override 
            })
        except Exception as e :
            logger .error (f"Failed to request cursor change to {cursor_type.value}: {e}")

    def clear_cursor_override (self ):
        """Request clearing any temporary cursor override."""
        self ._cursor_requests .append ({
        'action':'clear_override'
        })

    def reset_cursor_to_default (self ):
        """Request resetting cursor to default and clear any overrides."""
        self ._cursor_requests .append ({
        'action':'reset'
        })

    def request_cursor_change (self ,cursor_type :CursorType ):
        """Request a cursor change (convenience method)."""
        self .set_cursor (cursor_type )

    def _update_cursor_for_mouse_position (self ,mouse_x :int ,mouse_y :int ):
        """Update cursor based on the component under the mouse."""
        try :
            component =self .state .get_component_at_point (mouse_x ,mouse_y )

            if component :

                desired_cursor =component .get_cursor_type ()
                self .request_cursor_change (desired_cursor )
            else :

                self .request_cursor_change (CursorType .DEFAULT )
        except Exception as e :
            logger .error (f"Error updating cursor for mouse position: {e}")

    def _recreate_ui_for_view_change (self ,is_view_change :bool =True ):
        """Recreate UI layout when view changes or UI scale changes.
        
        Args:
            is_view_change: True if this is a view change, False if it's a UI scale change
        
        This method provides complete UI recreation by:
        1. Cleaning up existing components
        2. Clearing state and layout manager
        3. Creating new UI layout with current scale/view
        4. Adding new components to state
        5. Setting initial focus (only for view changes)
        """
        if self .state .viewport_width ==0 or self .state .viewport_height ==0 :
            return 

        try :
            reason ="view change"if is_view_change else "UI scale change"
            logger .info (f"Starting UI recreation for {reason}")


            if is_view_change :
                try :
                    from ...utils .scene_handler import scene_handler 
                    scene_handler .set_view_change_flag (True )
                except Exception as e :
                    logger .error (f"Error setting view change flag: {e}")


            lock_was_already_set =self ._is_ui_recreation_locked ()
            if not lock_was_already_set :
                self ._set_ui_recreation_lock (True )


            for component in self .state .components :
                if hasattr (component ,'cleanup'):
                    try :
                        component .cleanup ()
                    except Exception as e :
                        logger .debug (f"Error cleaning up component during {reason}: {e}")


            self .state .components .clear ()


            if hasattr (layout_manager ,'containers'):
                layout_manager .containers .clear ()
                layout_manager .layouts .clear ()
                layout_manager .constraints .clear ()
                if hasattr (layout_manager ,'container_bounds'):
                    layout_manager .container_bounds .clear ()


            logger .info (f"Creating new UI layout for view: {self.factory.current_view.value}")
            self .ui_layout =self .factory .create_layout (
            self .state .viewport_width ,
            self .state .viewport_height ,
            on_send =self ._handle_send ,
            on_add =self ._handle_add ,
            on_history =self ._handle_history ,
            on_settings =self ._handle_settings ,
            on_model_change =self ._handle_model_change ,
            on_auth_submit =self ._handle_auth_submit ,
            on_get_license =self ._handle_get_license ,
            on_stop_generation =self .factory ._handle_stop_generation 
            )


            logger .info ("Storing components reference")
            self .components =self .ui_layout ['components']


            logger .info ("Adding new components to state")
            for component in self .ui_layout ['all_components']:
                self .state .add_component (component )



            for component in self .state .components :
                component .update_layout ()



            for component in self .state .components :
                if hasattr (component ,'_dimension_cache')and hasattr (component ,'invalidate'):

                    component ._dimension_cache .clear ()
                    component .invalidate ()
                    logger .debug (f"Cleared dimension cache for {type(component).__name__}")


            if is_view_change :
                focused_component =self .factory .get_focused_component ()
                if focused_component :
                    self .state .set_focus (focused_component )
            else :
                logger .info ("Skipping initial focus setting for UI scale change")


            if self .state .target_area :
                self .state .target_area .tag_redraw ()

            logger .info (f"Recreated UI for {reason}")
        except Exception as e :
            logger .error (f"Error in _recreate_ui_for_view_change: {e}")
            raise 
        finally :

            if is_view_change :
                try :
                    from ...utils .scene_handler import scene_handler 
                    scene_handler .set_view_change_flag (False )
                except Exception as e :
                    logger .error (f"Error clearing view change flag: {e}")


            if not lock_was_already_set :
                self ._set_ui_recreation_lock (False )

    def demo_no_connection_view (self ):
        """Demo method to show the no connection view (for testing purposes)."""
        logger .info ("Demo: Switching to no connection view")
        self .factory .switch_to_view (ViewState .NO_CONNECTION )

    def test_connectivity_and_update_view (self ):
        """Test connectivity and update view accordingly."""
        logger .info ("Testing connectivity and updating view")
        if self .factory .check_and_handle_connectivity ():
            logger .info ("Connectivity test passed - connection is available")
        else :
            logger .info ("Connectivity test failed - switched to no connection view")

    def _get_tool_status_block (self ,tool_name :str ,status :str ,success :bool =True )->str :
        """Generate appropriate status block text for tool events."""
        try :
            if status =="started":
                if tool_name =="execute":
                    return "[Writing code]"
                elif tool_name =="query":
                    return "[Reading scene]"
                elif tool_name =="web_search_preview":
                    return "[Searching web]"
                elif tool_name =="custom_props":
                    return "[Reading properties]"
                elif tool_name =="render_settings":
                    return "[Reading render settings]"
                elif tool_name =="scene_graph":
                    return "[Analyzing scene]"
                elif tool_name =="nodes_graph":
                    return "[Analyzing nodes]"
                elif tool_name in ["viewport","see_viewport","add_viewport_render"]:
                    return "[Capturing viewport]"
                elif tool_name =="see_render":
                    return "[Rendering scene]"
                elif "image"in tool_name .lower ():
                    return "[Analyzing image]"
                else :
                    return f"[Using tool]"

            elif status =="completed":
                if tool_name =="execute":
                    return "[Code executed]"if success else "[Code execution failed]"
                elif tool_name =="query":
                    return "[Scene read]"if success else "[Scene reading failed]"
                elif tool_name =="web_search_preview":
                    return "[Found results]"if success else "[Web search failed]"
                elif tool_name =="custom_props":
                    return "[Properties read]"if success else "[Properties reading failed]"
                elif tool_name =="render_settings":
                    return "[Render settings read]"if success else "[Render settings reading failed]"
                elif tool_name =="scene_graph":
                    return "[Scene analyzed]"if success else "[Scene analysis failed]"
                elif tool_name =="nodes_graph":
                    return "[Nodes analyzed]"if success else "[Nodes analysis failed]"
                elif tool_name in ["viewport","see_viewport","add_viewport_render"]:
                    if success :
                        return "[Viewport captured]"
                    else :
                        return "[Viewport capture failed]"
                elif tool_name =="see_render":
                    if success :
                        return "[Render captured]"
                    else :
                        return "[Render failed]"
                elif "image"in tool_name .lower ():
                    return "[Image analyzed]"if success else "[Image analysis failed]"
                else :
                    return f"[Tool completed]"if success else f"[Tool failed]"

            return None 

        except Exception as e :
            logger .error (f"Error generating tool status block: {str(e)}")
            return None 

    def _update_tool_component (self ,call_id :str ,new_content :str ):
        """Update an existing tool component with new content for smooth transitions."""
        try :
            if call_id in self ._active_tool_components :
                component =self ._active_tool_components [call_id ]
                if hasattr (component ,'set_markdown'):
                    component .set_markdown (new_content )


                    self ._stop_animations_for_completed_tool (component ,new_content )

                    logger .info (f"Updated tool component for {call_id}: '{new_content}'")
                    return True 
                else :
                    logger .warning (f"Tool component for {call_id} doesn't have set_markdown method")
            else :
                logger .debug (f"No active tool component found for {call_id}")
            return False 
        except Exception as e :
            logger .error (f"Error updating tool component for {call_id}: {str(e)}")
            return False 

    def _stop_animations_for_completed_tool (self ,component ,content :str ):
        """Stop animations for tool blocks that have completed."""
        try :
            if hasattr (component ,'elements'):
                for element in component .elements :
                    if hasattr (element ,'is_animated')and element .is_animated :

                        if self ._is_completed_tool_block (element .text ):
                            element .stop_animation ()
                            logger .debug (f"Stopped animation for completed tool: {element.text}")
        except Exception as e :
            logger .error (f"Error stopping animations for completed tool: {e}")

    def _is_completed_tool_block (self ,text :str )->bool :
        """Check if a tool block represents a completed action."""
        text_lower =text .lower ()


        completed_indicators =[
        'code executed','execution complete','executed successfully',
        'scene read','scene analyzed','analysis complete',
        'found results','search completed','search finished',
        'image analyzed','image processing complete',
        'viewport captured','viewport capture complete','screenshot captured',
        'render captured, render complete','render finished','rendered successfully',
        'properties read','settings read',
        'tool completed','tool finished','execution done',
        'scene modified','scene updated','objects created',
        'objects added','modification complete','update complete'
        ]

        return any (indicator in text_lower for indicator in completed_indicators )

    def _cleanup_completed_tool_component (self ,call_id :str ):
        """Clean up a completed tool component from tracking."""
        try :
            if call_id in self ._active_tool_components :
                del self ._active_tool_components [call_id ]
                return True 
            return False 
        except Exception as e :
            logger .error (f"Error cleaning up tool component for {call_id}: {str(e)}")
            return False 

    def handle_external_tool_call (self ,tool_call_data :dict ):
        """Handle tool call events from external sources (like websocket client).
        
        This replaces direct history saving in websocket client and other components.
        """
        try :

            call_id =tool_call_data .get ('call_id')
            tool_name =tool_call_data .get ('tool_name')
            arguments =tool_call_data .get ('arguments','{}')


            tracked_data ={
            'call_id':call_id ,
            'function':{
            'name':tool_name ,
            'arguments':arguments 
            },
            'status':'executed'
            }
            self ._track_tool_call (tracked_data )

            logger .info (f"🔧 Tracked external tool call: {tool_name} (call_id: {call_id})")

        except Exception as e :
            logger .error (f"Failed to handle external tool call: {str(e)}")

    def handle_external_tool_response (self ,tool_response_data :dict ):
        """Handle tool response events from external sources (like websocket client).
        
        This replaces direct history saving in websocket client and other components.
        """
        try :

            call_id =tool_response_data .get ('call_id')


            history_content =tool_response_data .get ('content','{}')


            ui_message =tool_response_data .get ('ui_message')
            if not ui_message :

                try :
                    import json 
                    original_result =json .loads (history_content )if isinstance (history_content ,str )else history_content 
                    if isinstance (original_result ,dict ):
                        if original_result .get ('status')=='success':
                            result_data =original_result .get ('result',{})
                            if isinstance (result_data ,str ):
                                ui_message =result_data .strip ()if result_data .strip ()else "Tool executed successfully"
                            else :
                                ui_message ="Tool executed successfully"
                        else :
                            ui_message =str (original_result .get ('result','Tool execution failed'))
                    else :
                        ui_message =str (original_result )
                except :
                    ui_message ="Tool response received"

            success =tool_response_data .get ('success',True )


            tracked_data ={
            'call_id':call_id ,
            'content':history_content ,
            'success':success ,
            'ui_message':ui_message 
            }


            image_data =tool_response_data .get ('image_data')
            if image_data and isinstance (image_data ,dict ):
                tracked_data ['image_data']=image_data 
                logger .info (f"🔧 Stored image data for later processing: {image_data.get('message_text', 'Unknown')}")

            self ._track_tool_response (tracked_data )

            logger .info (f"🔧 Tracked external tool response for call_id: {call_id} (history: original result, UI: '{ui_message}')")

        except Exception as e :
            logger .error (f"Failed to handle external tool response: {str(e)}")
            import traceback 
            logger .error (traceback .format_exc ())

    def save_current_ui_state (self ):
        """Save current UI state to scene (called when state changes)."""
        try :
            if self .state .is_enabled and self .state .target_area :
                ui_state_manager .save_ui_state (bpy .context ,self ,self .state .target_area )
        except Exception as e :
            logger .debug (f"Could not save current UI state: {e}")

    def debug_ui_scale_info (self ):
        """Debug method to log current UI scale information."""
        try :
            current_scale =CoordinateSystem .get_ui_scale ()
            stored_scale =self ._current_ui_scale 

            logger .info (f"DEBUG: Current UI scale: {current_scale}")
            logger .info (f"DEBUG: Stored UI scale: {stored_scale}")
            logger .info (f"DEBUG: Scale changed: {abs(current_scale - (stored_scale or 0)) > 0.01}")
            logger .info (f"DEBUG: UI enabled: {self.state.is_enabled}")
            logger .info (f"DEBUG: Viewport size: {self.state.viewport_width}x{self.state.viewport_height}")
            logger .info (f"DEBUG: Component count: {len(self.state.components)}")
            logger .info (f"DEBUG: UI recreation locked: {self._is_ui_recreation_locked()}")


            logger .info (f"DEBUG: INPUT_AREA_HEIGHT: {int(60 * current_scale)}")
            logger .info (f"DEBUG: HEADER_HEIGHT: {int(32 * current_scale)}")
            logger .info (f"DEBUG: VIEWPORT_MARGIN: {int(10 * current_scale)}")


            logger .info ("DEBUG: UI scale changes trigger complete UI recreation (not just layout update)")
            logger .info ("DEBUG: Timer coordination prevents conflicts during recreation")
        except Exception as e :
            logger .error (f"Error in debug_ui_scale_info: {e}")

    def debug_force_ui_scale_recreation (self ):
        """Debug method to manually trigger UI recreation for testing."""
        try :
            logger .info ("DEBUG: Manually triggering UI recreation for testing")
            if self .state .is_enabled and self .state .viewport_width >0 and self .state .viewport_height >0 :
                self ._handle_ui_scale_change ()
                logger .info ("DEBUG: UI recreation completed successfully")
            else :
                logger .warning ("DEBUG: Cannot trigger UI recreation - UI not enabled or invalid viewport")
        except Exception as e :
            logger .error (f"Error in debug_force_ui_scale_recreation: {e}")

    def debug_test_timer_coordination (self ):
        """Debug method to test timer coordination during UI recreation."""
        try :
            logger .info ("DEBUG: Testing timer coordination system")


            logger .info (f"DEBUG: Lock state before: {self._is_ui_recreation_locked()}")

            self ._set_ui_recreation_lock (True )
            logger .info (f"DEBUG: Lock state after set: {self._is_ui_recreation_locked()}")


            logger .info (f"DEBUG: Cursor timer would skip: {self._is_ui_recreation_locked()}")
            logger .info (f"DEBUG: Enforcement timer would skip: {self._is_ui_recreation_locked()}")

            self ._set_ui_recreation_lock (False )
            logger .info (f"DEBUG: Lock state after clear: {self._is_ui_recreation_locked()}")

            logger .info ("DEBUG: Timer coordination test completed")
        except Exception as e :
            logger .error (f"Error in debug_test_timer_coordination: {e}")

    def debug_print_theme_info (self ):
        """Debug method to print current theme information."""
        try :
            logger .info ("=== THEME DEBUG INFO ===")

            from .blender_theme_integration import print_theme_debug 
            from .component_theming import print_component_theme_debug 


            print_theme_debug ()


            print_component_theme_debug ()

            logger .info ("=== THEME DEBUG COMPLETE ===")

        except Exception as e :
            logger .error (f"Error printing theme debug info: {e}")

    def force_ui_reinitialization (self ):
        """Force complete UI reinitialization when UI fails to load properly."""
        try :
            logger .info ("Forcing UI reinitialization")


            self .state .components .clear ()
            self .ui_layout =None 
            self .components ={}


            if hasattr (layout_manager ,'containers'):
                layout_manager .containers .clear ()
                layout_manager .layouts .clear ()
                layout_manager .constraints .clear ()
                if hasattr (layout_manager ,'container_bounds'):
                    layout_manager .container_bounds .clear ()


            if self .state .viewport_width >0 and self .state .viewport_height >0 :
                logger .info ("Reinitializing UI layout with current dimensions")
                self ._initialize_ui_layout ()

                if self .ui_layout and self .state .components :
                    logger .info (f"✅ UI reinitialization successful with {len(self.state.components)} components")

                    if self .state .target_area :
                        self .state .target_area .tag_redraw ()
                    return True 
                else :
                    logger .error ("UI reinitialization failed - no layout or components created")
                    return False 
            else :
                logger .warning ("Cannot reinitialize UI - no valid viewport dimensions")
                return False 

        except Exception as e :
            logger .error (f"Error during UI reinitialization: {e}")
            import traceback 
            logger .error (traceback .format_exc ())
            return False 

    def save_current_unsent_text (self ):
        """Save current unsent text before UI changes."""
        try :
            context =bpy .context 
            from ...utils .history_manager import history_manager 
            current_chat_id =getattr (context .scene ,'vibe4d_current_chat_id','')
            if current_chat_id :

                current_text =self .factory .get_send_text ()if self .factory else ""
                history_manager .save_unsent_text (context ,current_chat_id ,current_text )
                logger .debug (f"Saved unsent text before UI change: '{current_text[:50]}...'")
        except Exception as e :
            logger .debug (f"Could not save unsent text: {e}")

    def restore_current_unsent_text (self ):
        """Restore unsent text after UI changes."""
        try :
            context =bpy .context 
            from ...utils .history_manager import history_manager 
            current_chat_id =getattr (context .scene ,'vibe4d_current_chat_id','')
            if current_chat_id :
                history_manager .restore_unsent_text (context ,current_chat_id )
                logger .debug (f"Restored unsent text after UI change for chat: {current_chat_id}")
        except Exception as e :
            logger .debug (f"Could not restore unsent text: {e}")

    def _show_render_progress (self ,render_state :Dict [str ,Any ]):
        """Show render progress UI."""
        try :
            logger .info (f"Showing render progress for render ID: {render_state.get('render_id', 'unknown')}")


            self ._render_progress_state =render_state 


            if not self ._render_progress_component :
                self ._render_progress_component =self ._create_render_progress_component (render_state )
            else :
                self ._update_render_progress_component (render_state )


            if self ._render_progress_timer is None :
                self ._render_progress_timer =bpy .app .timers .register (
                self ._update_render_progress ,
                first_interval =0.1 
                )


            if self .state .target_area :
                self .state .target_area .tag_redraw ()

        except Exception as e :
            logger .error (f"Error showing render progress: {e}")

    def _update_render_status (self ,render_state :Dict [str ,Any ]):
        """Update render status in the UI."""
        try :
            logger .info (f"Updating render status: {render_state.get('status', 'unknown')}")


            self ._render_progress_state =render_state 


            if self ._render_progress_component :
                self ._update_render_progress_component (render_state )


            if render_state .get ('status')in ['completed','error','cancelled']:
                if self ._render_progress_timer :
                    try :
                        bpy .app .timers .unregister (self ._render_progress_timer )
                    except :
                        pass 
                    self ._render_progress_timer =None 


                def cleanup_progress_ui ():
                    self ._cleanup_render_progress_ui ()
                    return None 

                bpy .app .timers .register (cleanup_progress_ui ,first_interval =3.0 )


            if self .state .target_area :
                self .state .target_area .tag_redraw ()

        except Exception as e :
            logger .error (f"Error updating render status: {e}")

    def _create_render_progress_component (self ,render_state :Dict [str ,Any ]):
        """Create a render progress component."""
        try :

            from .components .render_progress import RenderProgressComponent 


            component =RenderProgressComponent (
            render_state =render_state ,
            x =10 ,y =self .state .viewport_height -100 ,
            width =400 ,height =80 
            )


            self .state .add_component (component )

            return component 

        except Exception as e :
            logger .error (f"Error creating render progress component: {e}")
            return None 

    def _update_render_progress_component (self ,render_state :Dict [str ,Any ]):
        """Update the render progress component."""
        try :
            if not self ._render_progress_component :
                return 


            if hasattr (self ._render_progress_component ,'update_render_state'):
                self ._render_progress_component .update_render_state (render_state )
            else :

                status =render_state .get ('status','unknown')
                render_id =render_state .get ('render_id','unknown')

                if status =='starting':
                    message ="Starting render..."
                elif status =='rendering':
                    elapsed =time .time ()-render_state .get ('start_time',time .time ())
                    message =f"Rendering... (ID: {render_id}, {elapsed:.1f}s)"
                elif status =='completed':
                    message ="Render completed! Check the result below."
                elif status =='error':
                    error =render_state .get ('error','Unknown error')
                    message =f"Render failed: {error}"
                elif status =='cancelled':
                    message ="Render cancelled."
                else :
                    message =f"Render status: {status}"


                if hasattr (self ._render_progress_component ,'text'):
                    self ._render_progress_component .text =message 

        except Exception as e :
            logger .error (f"Error updating render progress component: {e}")

    def _update_render_progress (self ):
        """Timer callback to update render progress."""
        try :
            if not self ._render_progress_state or not self ._render_progress_component :
                return None 


            self ._update_render_progress_component (self ._render_progress_state )


            if self .state .target_area :
                self .state .target_area .tag_redraw ()


            if self ._render_progress_state .get ('status')in ['starting','rendering']:
                return 0.5 
            else :
                return None 

        except Exception as e :
            logger .error (f"Error updating render progress: {e}")
            return None 

    def _cleanup_render_progress_ui (self ):
        """Clean up render progress UI components."""
        try :
            if self ._render_progress_component :

                self .state .remove_component (self ._render_progress_component )
                self ._render_progress_component =None 


            self ._render_progress_state =None 


            if self .state .target_area :
                self .state .target_area .tag_redraw ()

        except Exception as e :
            logger .error (f"Error cleaning up render progress UI: {e}")

    def cancel_current_render (self ):
        """Cancel the current render if one is active."""
        try :
            if self ._render_progress_state and self ._render_progress_state .get ('can_cancel',False ):
                render_id =self ._render_progress_state .get ('render_id')
                if render_id :

                    from ...engine .render_manager import render_manager 
                    success =render_manager .cancel_render (render_id )

                    if success :
                        logger .info (f"Cancelled render: {render_id}")

                        self ._render_progress_state ['status']='cancelled'
                        self ._render_progress_state ['can_cancel']=False 
                        self ._update_render_status (self ._render_progress_state )
                    else :
                        logger .error (f"Failed to cancel render: {render_id}")

        except Exception as e :
            logger .error (f"Error cancelling render: {e}")

    def _send_render_status_block (self ,status_text :str ):
        """Send render status as a markdown block to the current AI component."""
        try :
            if self ._current_ai_component and hasattr (self ._current_ai_component ,'set_markdown'):

                current_content =self ._current_ai_component .get_message ()


                if current_content :
                    new_content =current_content +"\n\n"+status_text 
                else :
                    new_content =status_text 


                self ._current_ai_component .set_markdown (new_content )


                if self .state .target_area :
                    self .state .target_area .tag_redraw ()

                logger .info (f"Sent render status block: {status_text}")

        except Exception as e :
            logger .error (f"Error sending render status block: {e}")



ui_manager =UIManager ()