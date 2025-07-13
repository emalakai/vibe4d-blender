"""
Navigator component for tabbed navigation.
Provides tab-based navigation with multiple pages/views and customizable tab styles.
"""

import logging 
from typing import TYPE_CHECKING ,List ,Optional ,Dict ,Callable ,Any 
from enum import Enum 
from dataclasses import dataclass 

from .base import UIComponent 
from ..types import EventType ,UIEvent ,CursorType ,Bounds 

if TYPE_CHECKING :
    from ..renderer import UIRenderer 

logger =logging .getLogger (__name__ )


class TabPosition (Enum ):
    """Position of tabs relative to content."""
    TOP ="top"
    BOTTOM ="bottom"
    LEFT ="left"
    RIGHT ="right"


class TabStyle (Enum ):
    """Style of tab appearance."""
    STANDARD ="standard"
    ROUNDED ="rounded"
    PILL ="pill"
    UNDERLINE ="underline"


@dataclass 
class NavigatorTab :
    """Represents a tab in the navigator."""
    id :str 
    title :str 
    content :UIComponent 
    icon :Optional [str ]=None 
    tooltip :Optional [str ]=None 
    closable :bool =False 
    enabled :bool =True 
    visible :bool =True 
    badge_text :Optional [str ]=None 
    badge_color :tuple =(1.0 ,0.0 ,0.0 ,1.0 )

    def __post_init__ (self ):
        if self .tooltip is None :
            self .tooltip =self .title 


class Navigator (UIComponent ):
    """Tabbed navigation component with multiple pages."""

    def __init__ (self ,x :int =0 ,y :int =0 ,width :int =400 ,height :int =300 ,
    tab_position :TabPosition =TabPosition .TOP ,
    tab_style :TabStyle =TabStyle .STANDARD ,
    tab_height :int =35 ,
    tab_min_width :int =80 ,
    tab_max_width :int =200 ,
    scrollable_tabs :bool =True ,
    show_close_buttons :bool =False ,
    show_add_button :bool =False ):
        super ().__init__ (x ,y ,width ,height )


        self .tab_position =tab_position 
        self .tab_style =tab_style 
        self .tab_height =tab_height 
        self .tab_min_width =tab_min_width 
        self .tab_max_width =tab_max_width 
        self .scrollable_tabs =scrollable_tabs 
        self .show_close_buttons =show_close_buttons 
        self .show_add_button =show_add_button 


        self .tabs :List [NavigatorTab ]=[]
        self .active_tab_id :Optional [str ]=None 
        self .hovered_tab_id :Optional [str ]=None 
        self .hovered_close_button :Optional [str ]=None 


        self .tab_scroll_offset =0 
        self .max_tab_scroll =0 


        self .tab_bar_bounds =Bounds (0 ,0 ,0 ,0 )
        self .content_bounds =Bounds (0 ,0 ,0 ,0 )
        self .add_button_bounds =Bounds (0 ,0 ,0 ,0 )


        self .tab_bounds_cache :Dict [str ,Bounds ]={}
        self .close_button_bounds_cache :Dict [str ,Bounds ]={}


        self .on_tab_changed :Optional [Callable [[str ],None ]]=None 
        self .on_tab_closed :Optional [Callable [[str ],None ]]=None 
        self .on_tab_added :Optional [Callable [[],None ]]=None 


        self .apply_themed_style ()


        self .add_event_handler (EventType .MOUSE_CLICK ,self ._on_mouse_click )
        self .add_event_handler (EventType .MOUSE_MOVE ,self ._on_mouse_move )
        self .add_event_handler (EventType .MOUSE_LEAVE ,self ._on_mouse_leave )
        self .add_event_handler (EventType .MOUSE_WHEEL ,self ._on_mouse_wheel )

        self ._update_layout ()

    def apply_themed_style (self ):
        """Apply themed style to the navigator."""
        try :
            from ..colors import Colors 
            from ..theme import get_themed_style 

            self .style =get_themed_style ("panel")
            self .style .background_color =Colors .Panel 
            self .style .border_color =Colors .Border 
            self .style .text_color =Colors .Text 

        except ImportError :

            from ..colors import Colors 
            self .style .background_color =Colors .Panel 
            self .style .border_color =Colors .Border 
            self .style .text_color =Colors .Text 

    def add_tab (self ,tab_id :str ,title :str ,content :UIComponent ,**kwargs )->NavigatorTab :
        """Add a new tab to the navigator."""

        if any (tab .id ==tab_id for tab in self .tabs ):
            logger .warning (f"Tab with ID '{tab_id}' already exists")
            return None 


        tab =NavigatorTab (
        id =tab_id ,
        title =title ,
        content =content ,
        **kwargs 
        )


        content .ui_state =self .ui_state 
        content .visible =False 

        self .tabs .append (tab )


        if len (self .tabs )==1 :
            self .set_active_tab (tab_id )

        self ._update_layout ()

        logger .debug (f"Added tab: '{title}' with ID '{tab_id}'")
        return tab 

    def remove_tab (self ,tab_id :str )->bool :
        """Remove a tab from the navigator."""
        tab =self .get_tab (tab_id )
        if not tab :
            return False 


        was_active =self .active_tab_id ==tab_id 


        self .tabs .remove (tab )


        self .tab_bounds_cache .pop (tab_id ,None )
        self .close_button_bounds_cache .pop (tab_id ,None )


        if was_active :
            if self .tabs :

                new_active_index =min (len (self .tabs )-1 ,max (0 ,len (self .tabs )-1 ))
                self .set_active_tab (self .tabs [new_active_index ].id )
            else :
                self .active_tab_id =None 


        if self .on_tab_closed :
            try :
                self .on_tab_closed (tab_id )
            except Exception as e :
                logger .error (f"Error in tab closed callback: {e}")

        self ._update_layout ()

        logger .debug (f"Removed tab with ID '{tab_id}'")
        return True 

    def get_tab (self ,tab_id :str )->Optional [NavigatorTab ]:
        """Get a tab by ID."""
        return next ((tab for tab in self .tabs if tab .id ==tab_id ),None )

    def set_active_tab (self ,tab_id :str )->bool :
        """Set the active tab."""
        tab =self .get_tab (tab_id )
        if not tab or not tab .enabled :
            return False 


        if self .active_tab_id :
            current_tab =self .get_tab (self .active_tab_id )
            if current_tab :
                current_tab .content .visible =False 


        self .active_tab_id =tab_id 
        tab .content .visible =True 


        tab .content .set_position (self .content_bounds .x ,self .content_bounds .y )
        tab .content .set_size (self .content_bounds .width ,self .content_bounds .height )


        if self .on_tab_changed :
            try :
                self .on_tab_changed (tab_id )
            except Exception as e :
                logger .error (f"Error in tab changed callback: {e}")

        logger .debug (f"Set active tab to '{tab_id}'")
        return True 

    def get_active_tab (self )->Optional [NavigatorTab ]:
        """Get the currently active tab."""
        return self .get_tab (self .active_tab_id )if self .active_tab_id else None 

    def set_tab_title (self ,tab_id :str ,title :str ):
        """Set the title of a tab."""
        tab =self .get_tab (tab_id )
        if tab :
            tab .title =title 
            self ._update_layout ()

    def set_tab_badge (self ,tab_id :str ,badge_text :Optional [str ],badge_color :tuple =(1.0 ,0.0 ,0.0 ,1.0 )):
        """Set or clear a badge on a tab."""
        tab =self .get_tab (tab_id )
        if tab :
            tab .badge_text =badge_text 
            tab .badge_color =badge_color 

    def set_tab_enabled (self ,tab_id :str ,enabled :bool ):
        """Enable or disable a tab."""
        tab =self .get_tab (tab_id )
        if tab :
            tab .enabled =enabled 
            if not enabled and self .active_tab_id ==tab_id :

                for other_tab in self .tabs :
                    if other_tab .enabled and other_tab .id !=tab_id :
                        self .set_active_tab (other_tab .id )
                        break 

    def _update_layout (self ):
        """Update navigator layout and tab positioning."""

        if self .tab_position ==TabPosition .TOP :
            self .tab_bar_bounds =Bounds (
            self .bounds .x ,self .bounds .y +self .bounds .height -self .tab_height ,
            self .bounds .width ,self .tab_height 
            )
            self .content_bounds =Bounds (
            self .bounds .x ,self .bounds .y ,
            self .bounds .width ,self .bounds .height -self .tab_height 
            )
        elif self .tab_position ==TabPosition .BOTTOM :
            self .tab_bar_bounds =Bounds (
            self .bounds .x ,self .bounds .y ,
            self .bounds .width ,self .tab_height 
            )
            self .content_bounds =Bounds (
            self .bounds .x ,self .bounds .y +self .tab_height ,
            self .bounds .width ,self .bounds .height -self .tab_height 
            )
        elif self .tab_position ==TabPosition .LEFT :

            tab_width =max (self .tab_height ,100 )
            self .tab_bar_bounds =Bounds (
            self .bounds .x ,self .bounds .y ,
            tab_width ,self .bounds .height 
            )
            self .content_bounds =Bounds (
            self .bounds .x +tab_width ,self .bounds .y ,
            self .bounds .width -tab_width ,self .bounds .height 
            )
        elif self .tab_position ==TabPosition .RIGHT :
            tab_width =max (self .tab_height ,100 )
            self .tab_bar_bounds =Bounds (
            self .bounds .x +self .bounds .width -tab_width ,self .bounds .y ,
            tab_width ,self .bounds .height 
            )
            self .content_bounds =Bounds (
            self .bounds .x ,self .bounds .y ,
            self .bounds .width -tab_width ,self .bounds .height 
            )


        self ._update_tab_bounds ()


        if self .active_tab_id :
            active_tab =self .get_tab (self .active_tab_id )
            if active_tab :
                active_tab .content .set_position (self .content_bounds .x ,self .content_bounds .y )
                active_tab .content .set_size (self .content_bounds .width ,self .content_bounds .height )

    def _update_tab_bounds (self ):
        """Update individual tab bounds."""
        if not self .tabs :
            return 

        visible_tabs =[tab for tab in self .tabs if tab .visible ]
        if not visible_tabs :
            return 


        if self .tab_position in [TabPosition .TOP ,TabPosition .BOTTOM ]:

            available_width =self .tab_bar_bounds .width 
            if self .show_add_button :
                available_width -=self .tab_height 


            if len (visible_tabs )*self .tab_min_width <=available_width :

                tab_width =min (self .tab_max_width ,available_width //len (visible_tabs ))
            else :

                tab_width =self .tab_min_width 


            current_x =self .tab_bar_bounds .x -self .tab_scroll_offset 

            for tab in visible_tabs :
                self .tab_bounds_cache [tab .id ]=Bounds (
                current_x ,self .tab_bar_bounds .y ,
                tab_width ,self .tab_height 
                )


                if self .show_close_buttons and tab .closable :
                    close_size =16 
                    self .close_button_bounds_cache [tab .id ]=Bounds (
                    current_x +tab_width -close_size -5 ,
                    self .tab_bar_bounds .y +(self .tab_height -close_size )//2 ,
                    close_size ,close_size 
                    )

                current_x +=tab_width 


            total_tabs_width =len (visible_tabs )*tab_width 
            self .max_tab_scroll =max (0 ,total_tabs_width -available_width )
            self .tab_scroll_offset =max (0 ,min (self .tab_scroll_offset ,self .max_tab_scroll ))


            if self .show_add_button :
                self .add_button_bounds =Bounds (
                self .tab_bar_bounds .x +self .tab_bar_bounds .width -self .tab_height ,
                self .tab_bar_bounds .y ,
                self .tab_height ,self .tab_height 
                )

        else :

            available_height =self .tab_bar_bounds .height 
            tab_height =max (self .tab_height ,available_height //max (1 ,len (visible_tabs )))

            current_y =self .tab_bar_bounds .y +self .tab_bar_bounds .height -tab_height 

            for tab in visible_tabs :
                self .tab_bounds_cache [tab .id ]=Bounds (
                self .tab_bar_bounds .x ,current_y ,
                self .tab_bar_bounds .width ,tab_height 
                )


                if self .show_close_buttons and tab .closable :
                    close_size =16 
                    self .close_button_bounds_cache [tab .id ]=Bounds (
                    self .tab_bar_bounds .x +self .tab_bar_bounds .width -close_size -5 ,
                    current_y +(tab_height -close_size )//2 ,
                    close_size ,close_size 
                    )

                current_y -=tab_height 

    def _on_mouse_click (self ,event :UIEvent )->bool :
        """Handle mouse click events."""

        if (self .show_add_button and 
        self .add_button_bounds .contains_point (event .mouse_x ,event .mouse_y )):
            if self .on_tab_added :
                try :
                    self .on_tab_added ()
                except Exception as e :
                    logger .error (f"Error in tab added callback: {e}")
            return True 


        for tab in self .tabs :
            if not tab .visible or not tab .enabled :
                continue 

            tab_bounds =self .tab_bounds_cache .get (tab .id )
            if not tab_bounds :
                continue 


            if (self .show_close_buttons and tab .closable and 
            tab .id in self .close_button_bounds_cache ):
                close_bounds =self .close_button_bounds_cache [tab .id ]
                if close_bounds .contains_point (event .mouse_x ,event .mouse_y ):
                    self .remove_tab (tab .id )
                    return True 


            if tab_bounds .contains_point (event .mouse_x ,event .mouse_y ):
                self .set_active_tab (tab .id )
                return True 

        return False 

    def _on_mouse_move (self ,event :UIEvent )->bool :
        """Handle mouse move events for hover effects."""

        self .hovered_tab_id =None 
        self .hovered_close_button =None 


        for tab in self .tabs :
            if not tab .visible :
                continue 

            tab_bounds =self .tab_bounds_cache .get (tab .id )
            if not tab_bounds :
                continue 

            if tab_bounds .contains_point (event .mouse_x ,event .mouse_y ):
                self .hovered_tab_id =tab .id 
                self .cursor_type =CursorType .DEFAULT 


                if (self .show_close_buttons and tab .closable and 
                tab .id in self .close_button_bounds_cache ):
                    close_bounds =self .close_button_bounds_cache [tab .id ]
                    if close_bounds .contains_point (event .mouse_x ,event .mouse_y ):
                        self .hovered_close_button =tab .id 

                return True 


        if (self .show_add_button and 
        self .add_button_bounds .contains_point (event .mouse_x ,event .mouse_y )):
            self .cursor_type =CursorType .DEFAULT 
            return True 

        self .cursor_type =CursorType .DEFAULT 
        return False 

    def _on_mouse_leave (self ,event :UIEvent )->bool :
        """Handle mouse leave events."""
        self .hovered_tab_id =None 
        self .hovered_close_button =None 
        self .cursor_type =CursorType .DEFAULT 
        return False 

    def _on_mouse_wheel (self ,event :UIEvent )->bool :
        """Handle mouse wheel for tab scrolling."""
        if not self .scrollable_tabs or self .max_tab_scroll ==0 :
            return False 

        if self .tab_bar_bounds .contains_point (event .mouse_x ,event .mouse_y ):
            wheel_delta =0 
            if 'wheel_direction'in event .data :

                wheel_delta =1 if event .data ['wheel_direction']=='DOWN'else -1 
            elif 'wheel_delta'in event .data :

                wheel_delta =event .data ['wheel_delta']
            else :
                return False 

            old_scroll =self .tab_scroll_offset 

            self .tab_scroll_offset =max (0 ,min (
            self .tab_scroll_offset -wheel_delta *20 ,
            self .max_tab_scroll 
            ))

            if old_scroll !=self .tab_scroll_offset :
                self ._update_tab_bounds ()
                return True 

        return False 

    def render (self ,renderer :'UIRenderer'):
        """Render the navigator and its contents."""
        if not self .visible :
            return 


        renderer .draw_rect (self .bounds ,self .style .background_color )
        renderer .draw_rect_outline (self .bounds ,self .style .border_color ,self .style .border_width )


        tab_bar_bg =tuple (c *0.9 for c in self .style .background_color [:3 ])+(1.0 ,)
        renderer .draw_rect (self .tab_bar_bounds ,tab_bar_bg )


        renderer .push_clip_rect (
        self .tab_bar_bounds .x ,self .tab_bar_bounds .y ,
        self .tab_bar_bounds .width ,self .tab_bar_bounds .height 
        )

        try :

            for tab in self .tabs :
                if tab .visible :
                    self ._render_tab (renderer ,tab )


            if self .show_add_button :
                self ._render_add_button (renderer )

        finally :
            renderer .pop_clip_rect ()


        if self .active_tab_id :
            active_tab =self .get_tab (self .active_tab_id )
            if active_tab and active_tab .content .visible :

                renderer .push_clip_rect (
                self .content_bounds .x ,self .content_bounds .y ,
                self .content_bounds .width ,self .content_bounds .height 
                )

                try :
                    active_tab .content .render (renderer )
                finally :
                    renderer .pop_clip_rect ()

    def _render_tab (self ,renderer :'UIRenderer',tab :NavigatorTab ):
        """Render an individual tab."""
        tab_bounds =self .tab_bounds_cache .get (tab .id )
        if not tab_bounds :
            return 


        is_active =self .active_tab_id ==tab .id 
        is_hovered =self .hovered_tab_id ==tab .id 

        if is_active :
            bg_color =self .style .background_color 
            text_color =self .style .text_color 
        elif is_hovered and tab .enabled :
            bg_color =tuple (c *1.1 for c in self .style .background_color [:3 ])+(1.0 ,)
            text_color =self .style .text_color 
        elif not tab .enabled :
            bg_color =tuple (c *0.7 for c in self .style .background_color [:3 ])+(0.5 ,)
            text_color =tuple (c *0.5 for c in self .style .text_color [:3 ])+(0.5 ,)
        else :
            bg_color =tuple (c *0.8 for c in self .style .background_color [:3 ])+(1.0 ,)
            text_color =self .style .text_color 


        if self .tab_style ==TabStyle .ROUNDED :
            renderer .draw_rounded_rect (tab_bounds ,bg_color ,6 )
        elif self .tab_style ==TabStyle .PILL :
            renderer .draw_rounded_rect (tab_bounds ,bg_color ,tab_bounds .height //2 )
        else :
            renderer .draw_rect (tab_bounds ,bg_color )


        if not is_active :
            renderer .draw_rect_outline (tab_bounds ,self .style .border_color ,1 )


        if is_active and self .tab_style ==TabStyle .UNDERLINE :
            underline_color =self .style .focus_border_color 
            if self .tab_position in [TabPosition .TOP ,TabPosition .BOTTOM ]:
                renderer .draw_line (
                tab_bounds .x ,tab_bounds .y ,
                tab_bounds .x +tab_bounds .width ,tab_bounds .y ,
                underline_color 
                )
            else :
                renderer .draw_line (
                tab_bounds .x ,tab_bounds .y ,
                tab_bounds .x ,tab_bounds .y +tab_bounds .height ,
                underline_color 
                )


        text_area =Bounds (tab_bounds .x ,tab_bounds .y ,tab_bounds .width ,tab_bounds .height )
        if self .show_close_buttons and tab .closable :
            text_area .width -=20 


        text_x =text_area .x +8 
        text_y =text_area .y +(text_area .height -self .style .font_size )//2 


        max_text_width =text_area .width -16 
        display_text =tab .title 
        text_width ,_ =renderer .get_text_dimensions (display_text ,self .style .font_size )

        if text_width >max_text_width :

            while len (display_text )>3 :
                display_text =display_text [:-4 ]+"..."
                text_width ,_ =renderer .get_text_dimensions (display_text ,self .style .font_size )
                if text_width <=max_text_width :
                    break 

        renderer .draw_text (display_text ,text_x ,text_y ,self .style .font_size ,text_color )


        if tab .badge_text :
            badge_size =16 
            badge_x =text_area .x +text_area .width -badge_size -2 
            badge_y =text_area .y +2 
            badge_bounds =Bounds (badge_x ,badge_y ,badge_size ,badge_size )

            renderer .draw_rounded_rect (badge_bounds ,tab .badge_color ,badge_size //2 )


            badge_text_x =badge_x +(badge_size -8 )//2 
            badge_text_y =badge_y +(badge_size -10 )//2 
            renderer .draw_text (tab .badge_text ,badge_text_x ,badge_text_y ,10 ,(1 ,1 ,1 ,1 ))


        if self .show_close_buttons and tab .closable :
            close_bounds =self .close_button_bounds_cache .get (tab .id )
            if close_bounds :
                is_close_hovered =self .hovered_close_button ==tab .id 
                close_color =(1 ,0.5 ,0.5 ,1 )if is_close_hovered else (0.7 ,0.7 ,0.7 ,1 )


                if is_close_hovered :
                    renderer .draw_rounded_rect (close_bounds ,(1 ,0 ,0 ,0.3 ),3 )


                center_x =close_bounds .x +close_bounds .width //2 
                center_y =close_bounds .y +close_bounds .height //2 
                size =4 

                renderer .draw_line (center_x -size ,center_y -size ,center_x +size ,center_y +size ,close_color )
                renderer .draw_line (center_x -size ,center_y +size ,center_x +size ,center_y -size ,close_color )

    def _render_add_button (self ,renderer :'UIRenderer'):
        """Render the add button."""
        if not self .show_add_button :
            return 


        bg_color =tuple (c *0.8 for c in self .style .background_color [:3 ])+(1.0 ,)
        renderer .draw_rect (self .add_button_bounds ,bg_color )
        renderer .draw_rect_outline (self .add_button_bounds ,self .style .border_color ,1 )


        center_x =self .add_button_bounds .x +self .add_button_bounds .width //2 
        center_y =self .add_button_bounds .y +self .add_button_bounds .height //2 
        size =6 

        renderer .draw_line (center_x -size ,center_y ,center_x +size ,center_y ,self .style .text_color )
        renderer .draw_line (center_x ,center_y -size ,center_x ,center_y +size ,self .style .text_color )

    def handle_event (self ,event :UIEvent )->bool :
        """Handle events for the navigator and its contents."""

        handled =super ().handle_event (event )
        if handled :
            return True 


        if self .active_tab_id and self .content_bounds .contains_point (event .mouse_x ,event .mouse_y ):
            active_tab =self .get_tab (self .active_tab_id )
            if active_tab and active_tab .content .visible :
                return active_tab .content .handle_event (event )

        return False 

    def update_layout (self ):
        """Update layout when viewport changes."""
        self ._update_layout ()


        if self .active_tab_id :
            active_tab =self .get_tab (self .active_tab_id )
            if active_tab and hasattr (active_tab .content ,'update_layout'):
                active_tab .content .update_layout ()