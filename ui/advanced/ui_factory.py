"""
Improved UI Factory with separated views, component registry, and automatic layout management.
"""

import logging 
import time 
import bpy 
from typing import Dict ,Any ,Callable ,Optional 
from enum import Enum 

from .layout_manager import layout_manager 
from .components .component_registry import component_registry ,ComponentState 
from .views import BaseView ,AuthView ,MainView ,HistoryView ,SettingsView ,NoConnectionView 
from .coordinates import CoordinateSystem 

logger =logging .getLogger (__name__ )


class ViewState (Enum ):
    """Enum for different view states."""
    AUTH ="auth"
    MAIN ="main"
    HISTORY ="history"
    SETTINGS ="settings"
    NO_CONNECTION ="no_connection"


class ImprovedUIFactory :
    """Improved UI Factory with better separation of concerns."""

    def __init__ (self ,ui_manager =None ):
        self .ui_manager =ui_manager 
        self .views ={}
        self .current_view =ViewState .MAIN 


        from .unified_styles import UnifiedStyles as Styles 
        self .styles =Styles 

        self .view_callbacks :Dict [str ,Callable ]={}
        self .on_view_change_callback :Optional [Callable ]=None 
        self .active_layout =None 


        self .typewriter_active =False 
        self .typewriter_message =""
        self .typewriter_current_text =""
        self .typewriter_component =None 
        self .typewriter_timer =None 
        self .typewriter_speed =0.03 
        self .typewriter_start_time =0 
        self .typewriter_char_index =0 


        self ._initialize_views ()


        layout_manager .register_auto_resize_callback (self ._handle_viewport_change )


        component_registry .add_lifecycle_callback (
        ComponentState .CREATED ,self ._on_component_created 
        )
        component_registry .add_lifecycle_callback (
        ComponentState .DESTROYED ,self ._on_component_destroyed 
        )

    def _initialize_views (self ):
        """Initialize all view instances."""
        self .views ={
        ViewState .AUTH :AuthView (),
        ViewState .MAIN :MainView (),
        ViewState .HISTORY :HistoryView (),
        ViewState .SETTINGS :SettingsView (),
        ViewState .NO_CONNECTION :NoConnectionView (),
        }


        for view in self .views .values ():
            view .set_callbacks (
            on_view_change =self ._handle_view_change ,
            on_go_back =self ._handle_go_back ,
            )


        if ViewState .SETTINGS in self .views :
            settings_view =self .views [ViewState .SETTINGS ]
            if hasattr (settings_view ,'set_refresh_callback'):
                settings_view .set_refresh_callback (self ._refresh_current_view )


    def create_layout (self ,viewport_width :int ,viewport_height :int ,**callbacks )->Dict [str ,Any ]:
        """Create layout for current view."""
        try :
            logger .info (f"Creating layout for {self.current_view.value} view with dimensions {viewport_width}x{viewport_height}")


            self ._save_unsent_text_before_ui_change ()


            self .view_callbacks =callbacks 


            current_view =self .views .get (self .current_view )
            if not current_view :
                logger .error (f"Current view {self.current_view.value} not found in views")
                return {'components':{},'all_components':[],'layouts':{}}


            current_view .set_callbacks (**callbacks )


            layout_result =current_view .create_layout (viewport_width ,viewport_height )

            if not layout_result :
                logger .error (f"View {self.current_view.value} failed to create layout")
                return {'components':{},'all_components':[],'layouts':{}}

            self .active_layout =layout_result 


            components =layout_result .get ('components',{})
            if components :
                for comp_name ,component in components .items ():
                    try :
                        component_registry .register (component ,comp_name )
                    except Exception as e :
                        logger .warning (f"Failed to register component {comp_name}: {e}")


            layout_manager .handle_viewport_change (viewport_width ,viewport_height )


            if hasattr (current_view ,'update_layout'):
                current_view .update_layout (viewport_width ,viewport_height )


            self ._restore_unsent_text_after_ui_change ()

            return layout_result 

        except Exception as e :
            logger .error (f"Error in create_layout: {e}")
            return {'components':{},'all_components':[],'layouts':{}}

    def switch_to_view (self ,view_state :ViewState ):
        """Switch to a different view."""
        if self .current_view ==view_state :
            return 

        try :
            logger .info (f"Starting view switch from {self.current_view.value} to {view_state.value}")


            self ._save_unsent_text_before_ui_change ()


            if self .current_view in self .views :
                self .views [self .current_view ].cleanup ()


            component_registry .cleanup_all ()


            old_view =self .current_view 
            self .current_view =view_state 


            if view_state ==ViewState .SETTINGS and ViewState .SETTINGS in self .views :
                settings_view =self .views [ViewState .SETTINGS ]
                if hasattr (settings_view ,'reset_usage_fetch_state'):
                    settings_view .reset_usage_fetch_state ()
                    logger .info ("Reset usage fetch state for settings view")

            logger .info (f"Switched from {old_view.value} to {view_state.value} view")


            if self .on_view_change_callback :
                logger .info ("Triggering UI recreation callback")
                self .on_view_change_callback ()
                logger .info ("UI recreation callback completed")


            try :

                from .manager import ui_manager 
                ui_manager .save_current_ui_state ()
            except Exception as e :
                logger .debug (f"Could not save UI state after view change: {e}")

        except Exception as e :
            logger .error (f"Error in switch_to_view: {e}")
            raise 

    def get_current_view (self )->ViewState :
        """Get current view state."""
        return self .current_view 

    def get_focused_component (self ):
        """Get focused component from current view."""
        if self .current_view in self .views :
            return self .views [self .current_view ].get_focused_component ()
        return None 

    def get_send_text (self ,components =None )->str :
        """Get text from the current view's text input."""
        if self .current_view in self .views :
            view =self .views [self .current_view ]
            if hasattr (view ,'get_send_text'):
                return view .get_send_text ()
        return ""

    def clear_send_text (self ,components =None ):
        """Clear text from the current view's text input."""
        if self .current_view in self .views :
            view =self .views [self .current_view ]
            if hasattr (view ,'clear_send_text'):
                view .clear_send_text ()

    def _calculate_message_gap (self ,message_scrollview ,is_ai_response :bool ,is_error_message :bool =False )->int :
        """Calculate the appropriate gap between messages based on roles.
        
        Args:
            message_scrollview: The scrollview containing messages
            is_ai_response: Whether this is an AI response message
            is_error_message: Whether this is an error message
        
        Returns:
            12 scaled pixels for same-role messages (user->user or assistant->assistant)
            16 scaled pixels for different-role messages (user->assistant or assistant->user)
            20 scaled pixels for error messages (always different role)
        """
        if not message_scrollview .children :

            return self .styles .get_same_role_message_gap ()


        previous_message =message_scrollview .children [0 ]


        if is_error_message :
            return self .styles .get_different_role_message_gap ()


        previous_is_ai =(hasattr (previous_message ,'style')and 
        getattr (previous_message .style ,'border_width',0 )==0 )


        previous_is_error =(hasattr (previous_message ,'style')and 
        hasattr (previous_message .style ,'background_color')and 
        previous_message .style .background_color ==(0.2 ,0.1 ,0.1 ,1.0 ))


        if previous_is_error :
            return self .styles .get_different_role_message_gap ()


        if previous_is_ai ==is_ai_response :

            return self .styles .get_same_role_message_gap ()
        else :

            return self .styles .get_different_role_message_gap ()

    def add_message_to_scrollview (self ,components ,text :str ,is_ai_response :bool =False ):
        """Add message to the current view's scrollview."""
        if self .current_view ==ViewState .MAIN :

            view =self .views [self .current_view ]
            message_scrollview =view .get_message_scrollview ()if hasattr (view ,'get_message_scrollview')else None 

            if not message_scrollview :
                logger .error ("Message scrollview not found")
                return 


            self ._remove_empty_state_if_present (message_scrollview )


            from .components .message import MessageComponent 



            scaled_padding =CoordinateSystem .scale_int (40 )
            max_width =message_scrollview .bounds .width -scaled_padding 
            if message_scrollview .show_scrollbars :
                max_width -=message_scrollview .scrollbar_width 


            message_component =MessageComponent (text ,0 ,0 ,100 ,40 )


            if is_ai_response :

                message_component .style .border_color =(0 ,0 ,0 ,0 )
                message_component .style .border_width =0 
            else :

                message_component .style .border_width =1 


            message_component .auto_resize_to_content (max_width )


            message_gap =self ._calculate_message_gap (message_scrollview ,is_ai_response )




            component_height =message_component .bounds .height +message_gap 
            for existing_child in message_scrollview .children :
                existing_child .bounds .y +=component_height 



            scaled_message_padding =CoordinateSystem .scale_int (20 )
            if is_ai_response :

                message_x =scaled_message_padding 
            else :

                message_x =message_scrollview .bounds .width -message_component .bounds .width -scaled_message_padding 


            message_y =0 
            message_component .set_position (message_x ,message_y )


            message_scrollview .children .insert (0 ,message_component )
            message_component .ui_state =message_scrollview .ui_state 


            message_scrollview ._update_content_bounds ()


            message_scrollview .scroll_to (y =0 )

            logger .info (f"Added MessageComponent to scrollview: {text} (size: {message_component.bounds.width}x{message_component.bounds.height}, total messages: {len(message_scrollview.children)})")

            return message_component 

    def add_ai_response_with_typewriter (self ,components ,text :str ):
        """Add AI response with typewriter effect to the current view."""
        if self .typewriter_active :

            self ._stop_typewriter ()


        self ._set_send_button_mode (False )


        ai_component =self .add_markdown_message_to_scrollview (components ,"",is_ai_response =True )


        self .typewriter_active =True 
        self .typewriter_message =text 
        self .typewriter_current_text =""
        self .typewriter_component =ai_component 
        self .typewriter_start_time =time .time ()
        self .typewriter_char_index =0 


        self .typewriter_speed =0.03 


        self .typewriter_timer =bpy .app .timers .register (
        self ._typewriter_update ,
        first_interval =self .typewriter_speed 
        )

        logger .info (f"Started typewriter effect for AI markdown response: {text[:50]}...")

    def add_markdown_message_to_scrollview (self ,components ,markdown_text :str ,is_ai_response :bool =False ):
        """Add a markdown message to the scrollview using MarkdownMessageComponent."""
        if self .current_view ==ViewState .MAIN :

            view =self .views [self .current_view ]
            message_scrollview =view .get_message_scrollview ()if hasattr (view ,'get_message_scrollview')else None 

            if not message_scrollview :
                logger .error ("Message scrollview not found")
                return 


            self ._remove_empty_state_if_present (message_scrollview )


            from .components .markdown_message import MarkdownMessageComponent 



            scaled_padding =CoordinateSystem .scale_int (40 )
            max_width =message_scrollview .bounds .width -scaled_padding 
            if message_scrollview .show_scrollbars :
                max_width -=message_scrollview .scrollbar_width 


            message_component =MarkdownMessageComponent (markdown_text ,0 ,0 ,100 ,40 )


            message_component .auto_resize_to_content (max_width )


            message_gap =self ._calculate_message_gap (message_scrollview ,is_ai_response )




            component_height =message_component .bounds .height +message_gap 
            for existing_child in message_scrollview .children :
                existing_child .bounds .y +=component_height 



            scaled_message_padding =CoordinateSystem .scale_int (20 )
            if is_ai_response :

                message_x =scaled_message_padding 
            else :

                message_x =message_scrollview .bounds .width -message_component .bounds .width -scaled_message_padding 


            message_y =0 
            message_component .set_position (message_x ,message_y )


            message_scrollview .children .insert (0 ,message_component )
            message_component .ui_state =message_scrollview .ui_state 


            message_scrollview ._update_content_bounds ()


            message_scrollview .scroll_to (y =0 )

            logger .info (f"Added MarkdownMessageComponent to scrollview: {markdown_text[:50]}... (size: {message_component.bounds.width}x{message_component.bounds.height}, total messages: {len(message_scrollview.children)})")

            return message_component 

    def _remove_empty_state_if_present (self ,message_scrollview ):
        """Remove the empty state message if present and re-enable scrollbars."""
        try :

            if len (message_scrollview .children )==1 :
                child =message_scrollview .children [0 ]

                if (hasattr (child ,'get_text')and 
                child .get_text ()=="Ready when you are."and 
                hasattr (child ,'style')and 
                hasattr (child .style ,'text_color')and 
                child .style .text_color ==(0.6 ,0.6 ,0.6 ,1.0 )):


                    message_scrollview .children .clear ()


                    message_scrollview .show_scrollbars =True 

                    logger .info ("✅ Removed empty state message and re-enabled scrollbars")

        except Exception as e :
            logger .warning (f"Error removing empty state message: {e}")

    def _typewriter_update (self ):
        """Update typewriter effect - called by Blender timer."""
        if not self .typewriter_active or not self .typewriter_component :
            return None 


        if self .typewriter_char_index <len (self .typewriter_message ):
            self .typewriter_char_index +=1 
            self .typewriter_current_text =self .typewriter_message [:self .typewriter_char_index ]


            if hasattr (self .typewriter_component ,'set_markdown'):
                self .typewriter_component .set_markdown (self .typewriter_current_text )
            else :
                self .typewriter_component .set_message (self .typewriter_current_text )


            view =self .views .get (self .current_view )
            if view and hasattr (view ,'get_message_scrollview'):
                message_scrollview =view .get_message_scrollview ()
                if message_scrollview :

                    scaled_padding =CoordinateSystem .scale_int (40 )
                    max_width =message_scrollview .bounds .width -scaled_padding 
                    if message_scrollview .show_scrollbars :
                        max_width -=message_scrollview .scrollbar_width 


                    old_height =self .typewriter_component .bounds .height 
                    self .typewriter_component .auto_resize_to_content (max_width )
                    new_height =self .typewriter_component .bounds .height 


                    if new_height !=old_height :


                        current_y =0 


                        for i in range (len (message_scrollview .children )):
                            child =message_scrollview .children [i ]


                            if i ==0 :

                                child .bounds .y =0 
                                current_y =child .bounds .height 
                            else :

                                child .bounds .y =current_y 


                            if i <len (message_scrollview .children )-1 :

                                next_child =message_scrollview .children [i +1 ]


                                current_is_ai =(hasattr (child ,'style')and 
                                getattr (child .style ,'border_width',0 )==0 )
                                next_is_ai =(hasattr (next_child ,'style')and 
                                getattr (next_child .style ,'border_width',0 )==0 )


                                if current_is_ai ==next_is_ai :

                                    message_gap =self .styles .get_same_role_message_gap ()
                                else :

                                    message_gap =self .styles .get_different_role_message_gap ()

                                if i >0 :
                                    current_y +=child .bounds .height +message_gap 
                            else :

                                if i >0 :
                                    current_y +=child .bounds .height 


                        message_scrollview ._update_content_bounds ()


            if hasattr (bpy .context ,'area')and bpy .context .area :
                bpy .context .area .tag_redraw ()


            next_interval =self .typewriter_speed 

            import random 
            next_interval +=random .uniform (-0.01 ,0.01 )

            if self .typewriter_char_index >0 and self .typewriter_message [self .typewriter_char_index -1 ]in '.!?':
                next_interval +=0.1 
            elif self .typewriter_message [self .typewriter_char_index -1 ]in ',;:':
                next_interval +=0.05 

            return max (0.01 ,next_interval )
        else :

            self .typewriter_current_text =self .typewriter_message 


            if hasattr (self .typewriter_component ,'set_markdown'):
                self .typewriter_component .set_markdown (self .typewriter_current_text )
            else :
                self .typewriter_component .set_message (self .typewriter_current_text )


            view =self .views .get (self .current_view )
            if view and hasattr (view ,'get_message_scrollview'):
                message_scrollview =view .get_message_scrollview ()
                if message_scrollview :

                    scaled_padding =CoordinateSystem .scale_int (40 )
                    max_width =message_scrollview .bounds .width -scaled_padding 
                    if message_scrollview .show_scrollbars :
                        max_width -=message_scrollview .scrollbar_width 
                    self .typewriter_component .auto_resize_to_content (max_width )


            self ._stop_typewriter ()


            if hasattr (bpy .context ,'area')and bpy .context .area :
                bpy .context .area .tag_redraw ()

            return None 

    def _stop_typewriter (self ):
        """Stop the typewriter effect."""
        self .typewriter_active =False 
        if self .typewriter_timer :
            try :
                bpy .app .timers .unregister (self .typewriter_timer )
            except :
                pass 
            self .typewriter_timer =None 

        self .typewriter_component =None 
        self .typewriter_current_text =""
        self .typewriter_message =""
        self .typewriter_char_index =0 


        self ._set_send_button_mode (True )

    def _set_send_button_mode (self ,is_send_mode :bool ):
        """Set the send button to send or stop mode."""
        if self .current_view ==ViewState .MAIN :
            view =self .views [self .current_view ]
            if hasattr (view ,'components')and 'send_button'in view .components :
                send_button =view .components ['send_button']
                if send_button and hasattr (send_button ,'set_mode'):
                    send_button .set_mode (is_send_mode )

                    if hasattr (send_button ,'set_stop_callback'):
                        send_button .set_stop_callback (self ._handle_stop_generation )

    def _handle_stop_generation (self ):
        """Handle stop button click - stop real API generation."""
        logger .info ("Stop button clicked - cancelling real API generation")

        try :

            from ...api .websocket_client import llm_websocket_client 


            llm_websocket_client .close ()
            logger .info ("WebSocket connection closed to cancel generation")



            from .manager import ui_manager 
            if hasattr (ui_manager ,'_reset_generation_state'):
                ui_manager ._reset_generation_state ()
                logger .info ("UI manager generation state reset")

        except Exception as e :
            logger .error (f"Error stopping generation: {e}")


        if self .typewriter_active :
            self ._stop_typewriter ()
            logger .info ("Stopped typewriter effect as fallback")

    def set_view_change_callback (self ,callback :Callable ):
        """Set callback for view changes."""
        self .on_view_change_callback =callback 

    def _handle_viewport_change (self ,width :int ,height :int ):
        """Handle automatic viewport changes."""
        if self .current_view in self .views :
            self .views [self .current_view ].update_layout (width ,height )


        component_registry .process_updates ()

    def _handle_view_change (self ,new_view :ViewState ):
        """Handle view change requests from views."""
        self .switch_to_view (new_view )

    def _handle_go_back (self ):
        """Handle go back navigation."""

        self .switch_to_view (ViewState .MAIN )

    def _refresh_current_view (self ):
        """Refresh the current view by triggering UI recreation."""
        if self .on_view_change_callback :
            logger .info (f"Refreshing current view: {self.current_view.value}")
            self .on_view_change_callback ()

    def _on_component_created (self ,component ,state ):
        """Callback when component is created."""

    def _on_component_destroyed (self ,component ,state ):
        """Callback when component is destroyed."""

    def cleanup (self ):
        """Clean up all resources."""

        if self .typewriter_active :
            self ._stop_typewriter ()


        for view in self .views .values ():
            view .cleanup ()


        component_registry .cleanup_all ()


        layout_manager .containers .clear ()
        layout_manager .layouts .clear ()
        layout_manager .constraints .clear ()
        layout_manager .container_bounds .clear ()

    def get_stats (self )->Dict [str ,Any ]:
        """Get factory statistics."""
        return {
        'current_view':self .current_view .value ,
        'active_components':len (component_registry .get_all_components ()),
        'typewriter_active':self .typewriter_active ,
        'views_initialized':len (self .views ),
        }

    def check_and_handle_connectivity (self )->bool :
        """Check internet connectivity and switch to no connection view if needed.
        
        Returns:
            bool: True if connected, False if switched to no connection view
        """
        try :

            from .views .no_connection_view import NoConnectionView 


            if NoConnectionView .check_internet_connection ():
                logger .debug ("Internet connection is available")
                return True 
            else :
                logger .warning ("No internet connection detected - switching to no connection view")
                self .switch_to_view (ViewState .NO_CONNECTION )
                return False 

        except Exception as e :
            logger .error (f"Error checking connectivity: {e}")

            self .switch_to_view (ViewState .NO_CONNECTION )
            return False 

    def switch_to_appropriate_view_on_startup (self ):
        """Switch to the appropriate view on startup based on auth and connectivity."""
        try :
            import bpy 
            context =bpy .context 

            logger .info ("Determining appropriate startup view...")


            if not self .check_and_handle_connectivity ():

                logger .info ("No internet connection detected - staying on NO_CONNECTION view")
                return 


            is_authenticated =getattr (context .window_manager ,'vibe4d_authenticated',False )

            if is_authenticated :
                logger .info ("User is authenticated - switching to main view")
                self .switch_to_view (ViewState .MAIN )
            else :
                logger .info ("User not authenticated - staying on auth view")
                self .switch_to_view (ViewState .AUTH )

        except Exception as e :
            logger .error (f"Error determining startup view: {e}")
            import traceback 
            logger .error (traceback .format_exc ())

            try :
                self .switch_to_view (ViewState .AUTH )
                logger .info ("Fallback: Switched to auth view due to error")
            except Exception as fallback_error :
                logger .error (f"Failed to switch to auth view as fallback: {fallback_error}")

    def add_image_message_to_scrollview (self ,components ,text :str ,image_data_uri :str ,is_ai_response :bool =False ):
        """Add an image message to the scrollview with image preview."""
        if self .current_view ==ViewState .MAIN :

            view =self .views [self .current_view ]
            message_scrollview =view .get_message_scrollview ()if hasattr (view ,'get_message_scrollview')else None 

            if not message_scrollview :
                logger .error ("Message scrollview not found")
                return 


            self ._remove_empty_state_if_present (message_scrollview )


            from .components .message import MessageComponent 



            scaled_padding =CoordinateSystem .scale_int (40 )
            max_width =message_scrollview .bounds .width -scaled_padding 
            if message_scrollview .show_scrollbars :
                max_width -=message_scrollview .scrollbar_width 


            text_component =MessageComponent (text ,0 ,0 ,max_width ,40 )
            text_component .auto_resize_to_content (max_width )


            if is_ai_response :

                text_component .style .border_color =(0 ,0 ,0 ,0 )
                text_component .style .border_width =0 
            else :

                text_component .style .border_width =1 


            message_gap =self ._calculate_message_gap (message_scrollview ,is_ai_response )




            component_height =text_component .bounds .height +message_gap 
            for existing_child in message_scrollview .children :
                existing_child .bounds .y +=component_height 



            scaled_message_padding =CoordinateSystem .scale_int (20 )
            if is_ai_response :

                message_x =scaled_message_padding 
            else :

                message_x =message_scrollview .bounds .width -text_component .bounds .width -scaled_message_padding 


            message_y =0 
            text_component .set_position (message_x ,message_y )


            message_scrollview .children .insert (0 ,text_component )
            text_component .ui_state =message_scrollview .ui_state 


            message_scrollview ._update_content_bounds ()


            message_scrollview .scroll_to (y =0 )

            logger .info (f"Added image message text to scrollview (image disabled): {text} (size: {text_component.bounds.width}x{text_component.bounds.height})")

            return text_component 

        logger .warning (f"Cannot add image message to {self.current_view} view")
        return None 

    def add_error_message_to_scrollview (self ,components ,error_text :str ):
        """Add an error message to the scrollview using ErrorMessageComponent."""
        if self .current_view ==ViewState .MAIN :

            view =self .views [self .current_view ]
            message_scrollview =view .get_message_scrollview ()if hasattr (view ,'get_message_scrollview')else None 

            if not message_scrollview :
                logger .error ("Message scrollview not found")
                return 


            self ._remove_empty_state_if_present (message_scrollview )


            from .components .error_message import ErrorMessageComponent 



            scaled_padding =CoordinateSystem .scale_int (40 )
            max_width =message_scrollview .bounds .width -scaled_padding 
            if message_scrollview .show_scrollbars :
                max_width -=message_scrollview .scrollbar_width 


            error_component =ErrorMessageComponent (error_text ,0 ,0 ,100 ,40 )


            error_component .auto_resize_to_content (max_width )


            message_gap =self ._calculate_message_gap (message_scrollview ,False ,is_error_message =True )




            component_height =error_component .bounds .height +message_gap 
            for existing_child in message_scrollview .children :
                existing_child .bounds .y +=component_height 



            scaled_message_padding =CoordinateSystem .scale_int (20 )
            message_x =scaled_message_padding 


            message_y =0 
            error_component .set_position (message_x ,message_y )


            message_scrollview .children .insert (0 ,error_component )
            error_component .ui_state =message_scrollview .ui_state 


            message_scrollview ._update_content_bounds ()


            message_scrollview .scroll_to (y =0 )

            logger .info (f"Added ErrorMessageComponent to scrollview: {error_text[:50]}... (size: {error_component.bounds.width}x{error_component.bounds.height}, total messages: {len(message_scrollview.children)})")

            return error_component 

    def _save_unsent_text_before_ui_change (self ):
        """Save unsent text before UI changes."""
        try :

            if self .current_view ==ViewState .MAIN :
                import bpy 
                context =bpy .context 
                from ...utils .history_manager import history_manager 
                current_chat_id =getattr (context .scene ,'vibe4d_current_chat_id','')
                if current_chat_id :

                    current_text =self .get_send_text ()
                    history_manager .save_unsent_text (context ,current_chat_id ,current_text )
                    logger .debug (f"Saved unsent text before UI change: '{current_text[:50]}...'")
        except Exception as e :
            logger .debug (f"Could not save unsent text before UI change: {e}")

    def _restore_unsent_text_after_ui_change (self ):
        """Restore unsent text after UI changes."""
        try :

            if self .current_view ==ViewState .MAIN :
                import bpy 
                context =bpy .context 
                from ...utils .history_manager import history_manager 
                current_chat_id =getattr (context .scene ,'vibe4d_current_chat_id','')
                if current_chat_id :
                    history_manager .restore_unsent_text (context ,current_chat_id )
                    logger .debug (f"Restored unsent text after UI change for chat: {current_chat_id}")
        except Exception as e :
            logger .debug (f"Could not restore unsent text after UI change: {e}")



improved_ui_factory =ImprovedUIFactory ()