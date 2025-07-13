"""
Toggle button component for the bottom left corner of the viewport.
40x40 rounded rectangle with 20x20 icon, bg_panel background, 1px border.
"""

import logging 
from typing import Optional ,Callable 

from .button import Button 
from .image import ImageComponent ,ImageFit ,ImagePosition 
from ..theme import get_themed_style 
from ..colors import Colors 
from ..unified_styles import Styles 

logger =logging .getLogger (__name__ )


class ToggleButton (Button ):
    """Toggle button component for the bottom left corner of the viewport."""

    def __init__ (self ,icon_name :str ,x :int =0 ,y :int =0 ,on_click :Callable =None ):

        super ().__init__ ("",x ,y ,40 ,40 ,corner_radius =6 ,on_click =on_click )

        self .icon_name =icon_name 
        self .is_toggled =False 


        self .style =get_themed_style ("button")
        self .style .background_color =Colors .Panel 
        self .style .border_color =Colors .Border 
        self .style .border_width =1 
        self .style .focus_background_color =Styles .lighten_color (self .style .background_color ,10 )
        self .style .pressed_background_color =Styles .darken_color (self .style .background_color ,10 )


        icon_size =20 
        icon_padding =(40 -icon_size )//2 

        self .icon_component =ImageComponent (
        image_path =f"{icon_name}.png",
        x =x +icon_padding ,
        y =y +icon_padding ,
        width =icon_size ,
        height =icon_size ,
        fit =ImageFit .CONTAIN ,
        position =ImagePosition .CENTER 
        )

    def set_position (self ,x :int ,y :int ):
        """Override to update icon position as well."""
        super ().set_position (x ,y )
        icon_size =20 
        icon_padding =(40 -icon_size )//2 
        self .icon_component .set_position (
        x +icon_padding ,
        y +icon_padding 
        )

    def set_size (self ,width :int ,height :int ):
        """Override to update icon size as well."""
        super ().set_size (width ,height )
        icon_size =20 
        icon_padding =(width -icon_size )//2 


        self .icon_component .set_size (icon_size ,icon_size )


        self .icon_component .set_position (
        self .bounds .x +icon_padding ,
        self .bounds .y +icon_padding 
        )

    def toggle (self ):
        """Toggle the button state."""
        self .is_toggled =not self .is_toggled 
        logger .debug (f"Toggle button '{self.icon_name}' toggled to: {self.is_toggled}")

    def set_toggled (self ,toggled :bool ):
        """Set the toggle state."""
        self .is_toggled =toggled 

    def is_button_toggled (self )->bool :
        """Get the current toggle state."""
        return self .is_toggled 

    def _trigger_click (self ):
        """Override to handle toggle functionality."""
        if self .on_click and self .is_enabled :
            try :

                self .toggle ()
                self .on_click (self .is_toggled )
            except Exception as e :
                logger .error (f"Error executing toggle button click callback: {e}")

    def render (self ,renderer ):
        """Render the toggle button."""
        if not self .visible :
            return 


        self ._update_pressed_state ()


        bg_color ,border_color ,text_color =self ._get_current_colors ()


        if self .corner_radius >0 :
            renderer .draw_rounded_rect (self .bounds ,bg_color ,self .corner_radius )


            if self .style .border_width >0 :
                renderer .draw_rounded_rect_outline (self .bounds ,border_color ,
                self .style .border_width ,self .corner_radius )
        else :

            renderer .draw_rect (self .bounds ,bg_color )


            if self .style .border_width >0 :
                renderer .draw_rect_outline (self .bounds ,border_color ,self .style .border_width )


        self .icon_component .render (renderer )


        if not self .icon_component .image_loaded and self .icon_component ._texture_creation_attempted :
            fallback_text =self .icon_name [0 ].upper ()
            text_x =self .bounds .x +(self .bounds .width -12 )//2 
            text_y =self .bounds .y +(self .bounds .height -16 )//2 
            renderer .draw_text (fallback_text ,text_x ,text_y ,16 ,text_color )

    def _get_current_colors (self ):
        """Get colors for current state."""
        if not self .is_enabled :

            bg_color =tuple (c *0.5 for c in self .style .background_color [:3 ])+(0.5 ,)
            border_color =tuple (c *0.5 for c in self .style .border_color [:3 ])+(0.5 ,)
            text_color =tuple (c *0.5 for c in self .style .text_color [:3 ])+(0.5 ,)
        elif self .is_pressed :

            bg_color =self .style .pressed_background_color 
            border_color =self .style .pressed_border_color 
            text_color =self .style .text_color 
        elif self .is_hovered :

            bg_color =self .style .focus_background_color 
            border_color =self .style .border_color 
            text_color =self .style .text_color 
        elif self .is_toggled :

            bg_color =self .style .focus_background_color 
            border_color =self .style .border_color 
            text_color =self .style .text_color 
        else :

            bg_color =self .style .background_color 
            border_color =self .style .border_color 
            text_color =self .style .text_color 

        return bg_color ,border_color ,text_color 

    def cleanup (self ):
        """Clean up resources when button is destroyed."""
        if self .icon_component :
            self .icon_component .cleanup ()