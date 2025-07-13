"""
Button component for clickable UI elements.
Supports hover states, click handling, and theming.
"""

import time 
import logging 
from typing import TYPE_CHECKING ,Optional ,Callable 

from .base import UIComponent 
from ..types import EventType ,UIEvent ,CursorType 

if TYPE_CHECKING :
    from ..renderer import UIRenderer 

logger =logging .getLogger (__name__ )


class Button (UIComponent ):
    """Button component for user interactions."""

    def __init__ (self ,text :str ="Button",x :int =0 ,y :int =0 ,width :int =120 ,height :int =40 ,
    corner_radius :int =6 ,on_click :Optional [Callable ]=None ):

        super ().__init__ (x ,y ,width ,height )


        self .cursor_type =CursorType .DEFAULT 


        self .text =text 
        self .corner_radius =corner_radius 
        self .on_click =on_click 
        self .text_align ="center"


        self .is_hovered =False 
        self .is_pressed =False 
        self .is_enabled =True 


        self ._press_start_time =0 
        self ._press_duration =0.1 


        self .apply_themed_style ("button")


        self .add_event_handler (EventType .MOUSE_CLICK ,self ._on_mouse_click )
        self .add_event_handler (EventType .MOUSE_PRESS ,self ._on_mouse_press )
        self .add_event_handler (EventType .MOUSE_RELEASE ,self ._on_mouse_release )
        self .add_event_handler (EventType .MOUSE_ENTER ,self ._on_mouse_enter )
        self .add_event_handler (EventType .MOUSE_LEAVE ,self ._on_mouse_leave )

    def apply_themed_style (self ,style_type :str ="button"):
        """Apply a themed style to this button using centralized colors."""
        try :
            from ..colors import Colors 
            from ..theme import get_themed_style 


            self .style =get_themed_style ("button")


            self .style .background_color =Colors .Primary 
            self .style .border_color =Colors .Border 
            self .style .focus_background_color =tuple (min (c *1.3 ,1.0 )for c in Colors .Primary [:3 ])+(1.0 ,)
            self .style .focus_border_color =Colors .Border 
            self .style .pressed_background_color =tuple (c *0.8 for c in Colors .Primary [:3 ])+(1.0 ,)
            self .style .pressed_border_color =Colors .Border 
            self .style .text_color =Colors .Text 

        except ImportError :

            self .style .background_color =(0.25 ,0.25 ,0.25 ,1.0 )
            self .style .border_color =(0.5 ,0.5 ,0.5 ,1.0 )
            self .style .focus_background_color =(0.35 ,0.35 ,0.35 ,1.0 )
            self .style .focus_border_color =(0.5 ,0.5 ,0.5 ,1.0 )
            self .style .text_color =(1.0 ,1.0 ,1.0 ,1.0 )

    def set_text (self ,text :str ):
        """Set the button text."""
        self .text =text 

    def get_text (self )->str :
        """Get the button text."""
        return self .text 

    def set_enabled (self ,enabled :bool ):
        """Enable or disable the button."""
        self .is_enabled =enabled 
        if not enabled :
            self .is_hovered =False 
            self .is_pressed =False 

    def is_button_enabled (self )->bool :
        """Check if button is enabled."""
        return self .is_enabled 

    def set_on_click (self ,callback :Callable ):
        """Set the click callback function."""
        self .on_click =callback 

    def set_text_align (self ,align :str ):
        """Set text alignment ('left', 'center', 'right')."""
        if align in ["left","center","right"]:
            self .text_align =align 

    def _on_mouse_enter (self ,event :UIEvent )->bool :
        """Handle mouse enter event."""
        was_hovered =self .is_hovered 

        if self .is_enabled :
            self .is_hovered =True 
            logger .debug (f"Button '{self.text}' hovered at ({event.mouse_x}, {event.mouse_y}) - was_hovered: {was_hovered}")
        return True 

    def _on_mouse_leave (self ,event :UIEvent )->bool :
        """Handle mouse leave event."""
        was_hovered =self .is_hovered 
        was_pressed =self .is_pressed 

        self .is_hovered =False 
        self .is_pressed =False 

        logger .debug (f"Button '{self.text}' unhovered at ({event.mouse_x}, {event.mouse_y}) - was_hovered: {was_hovered}, was_pressed: {was_pressed}")
        return True 

    def _on_mouse_press (self ,event :UIEvent )->bool :
        """Handle mouse press event."""
        if self .is_enabled and self .bounds .contains_point (event .mouse_x ,event .mouse_y ):
            self .is_pressed =True 
            self ._press_start_time =time .time ()
            return True 
        return False 

    def _on_mouse_release (self ,event :UIEvent )->bool :
        """Handle mouse release event."""
        if self .is_pressed and self .is_enabled :
            self .is_pressed =False 

            if self .bounds .contains_point (event .mouse_x ,event .mouse_y ):
                self ._trigger_click ()
            return True 
        return False 

    def _on_mouse_click (self ,event :UIEvent )->bool :
        """Handle mouse click event."""
        if self .is_enabled and self .bounds .contains_point (event .mouse_x ,event .mouse_y ):
            return True 
        return False 

    def _trigger_click (self ):
        """Trigger the button click action."""
        if self .on_click and self .is_enabled :
            try :
                self .on_click ()
            except Exception as e :
                logger .error (f"Error executing button click callback: {e}")

    def _get_current_colors (self ):
        """Get colors based on current button state."""
        if not self .is_enabled :

            bg_color =tuple (c *0.5 for c in self .style .background_color [:3 ])+(0.5 ,)
            border_color =self .style .border_color 
            text_color =tuple (c *0.5 for c in self .style .text_color [:3 ])+(0.5 ,)
        elif self .is_pressed :

            bg_color =self .style .pressed_background_color 
            border_color =self .style .border_color 
            text_color =self .style .text_color 
        elif self .is_hovered :

            bg_color =self .style .focus_background_color 
            border_color =self .style .border_color 
            text_color =self .style .text_color 
        else :

            bg_color =self .style .background_color 
            border_color =self .style .border_color 
            text_color =self .style .text_color 

        return bg_color ,border_color ,text_color 

    def _update_pressed_state (self ):
        """Update pressed state based on timing."""
        if self .is_pressed and self ._press_start_time >0 :
            elapsed =time .time ()-self ._press_start_time 
            if elapsed >self ._press_duration :

                pass 

    def render (self ,renderer :'UIRenderer'):
        """Render the button."""
        if not self .visible :
            return 


        self ._update_pressed_state ()


        bg_color ,border_color ,text_color =self ._get_current_colors ()


        if hasattr (self ,'_last_render_state'):
            current_state =(self .is_hovered ,self .is_pressed ,self .is_enabled )
            if current_state !=self ._last_render_state :
                logger .debug (f"Button '{self.text}' state changed: hovered={self.is_hovered}, pressed={self.is_pressed}, enabled={self.is_enabled}")
                logger .debug (f"Colors: bg={bg_color}, border={border_color}, text={text_color}")
                self ._last_render_state =current_state 
        else :
            self ._last_render_state =(self .is_hovered ,self .is_pressed ,self .is_enabled )


        if self .corner_radius >0 :
            renderer .draw_rounded_rect (self .bounds ,bg_color ,self .corner_radius )


            if self .style .border_width >0 :
                renderer .draw_rounded_rect_outline (self .bounds ,border_color ,
                self .style .border_width ,self .corner_radius )
        else :

            renderer .draw_rect (self .bounds ,bg_color )


            if self .style .border_width >0 :
                renderer .draw_rect_outline (self .bounds ,border_color ,self .style .border_width )


        if self .text :
            text_width ,text_height =renderer .get_text_dimensions (self .text ,self .style .font_size )


            if self .text_align =="left":
                text_x =self .bounds .x +10 
            elif self .text_align =="right":
                text_x =self .bounds .x +self .bounds .width -text_width -10 
            else :
                text_x =self .bounds .x +(self .bounds .width -text_width )//2 

            text_y =self .bounds .y +(self .bounds .height -text_height )//2 

            renderer .draw_text (self .text ,text_x ,text_y ,self .style .font_size ,text_color )

    def get_preferred_size (self )->tuple [int ,int ]:
        """Get the preferred size based on text content."""
        if not self .text :
            return (self .bounds .width ,self .bounds .height )

        try :

            import blf 
            font_id =0 
            blf .size (font_id ,self .style .font_size )
            text_width ,text_height =blf .dimensions (font_id ,self .text )


            preferred_width =int (text_width +self .style .padding *2 )
            preferred_height =int (text_height +self .style .padding )

            return (preferred_width ,preferred_height )
        except Exception as e :
            logger .warning (f"Failed to calculate preferred size: {e}")
            return (self .bounds .width ,self .bounds .height )

    def auto_size (self ):
        """Automatically size the button based on text content."""
        preferred_width ,preferred_height =self .get_preferred_size ()
        self .set_size (preferred_width ,preferred_height )