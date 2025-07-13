"""
Icon button component that displays PNG icons using the unified ImageComponent.
"""

import logging 
from typing import Optional ,Callable 

from .button import Button 
from .image import ImageComponent ,ImageFit ,ImagePosition 
from ..theme import get_themed_style 
from ..colors import Colors 
from ..unified_styles import Styles 

logger =logging .getLogger (__name__ )


class IconButton (Button ):
    """Button component that displays a PNG icon using the unified ImageComponent."""

    def __init__ (self ,icon_name :str ,x :int =0 ,y :int =0 ,width :int =52 ,height :int =52 ,
    corner_radius :int =6 ,on_click :Callable =None ):
        super ().__init__ ("",x ,y ,width ,height ,corner_radius ,on_click )

        self .icon_name =icon_name 


        self .style =get_themed_style ("button")
        self .style .background_color =Styles .get_themed_color ('bg_menu')
        self .style .border_color =Styles .get_themed_color ('border')
        self .style .border_width =Styles .get_thin_border ()
        self .style .focus_background_color =Styles .lighten_color (self .style .background_color ,10 )
        self .style .pressed_background_color =Styles .darken_color (self .style .background_color ,10 )



        icon_size =Styles .get_header_icon_size ()
        icon_padding =(width -icon_size )//2 

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
        icon_size =Styles .get_header_icon_size ()
        icon_padding =(self .bounds .width -icon_size )//2 
        self .icon_component .set_position (
        x +icon_padding ,
        y +icon_padding 
        )

    def set_size (self ,width :int ,height :int ):
        """Override to update icon size as well."""
        super ().set_size (width ,height )
        icon_size =Styles .get_header_icon_size ()
        icon_padding =(width -icon_size )//2 


        self .icon_component .set_size (icon_size ,icon_size )


        self .icon_component .set_position (
        self .bounds .x +icon_padding ,
        self .bounds .y +icon_padding 
        )

    def render (self ,renderer ):
        """Render the icon button."""
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
        else :

            bg_color =self .style .background_color 
            border_color =self .style .border_color 
            text_color =self .style .text_color 

        return bg_color ,border_color ,text_color 

    def cleanup (self ):
        """Clean up resources when button is destroyed."""
        if self .icon_component :
            self .icon_component .cleanup ()