"""
Back button component for navigation with icon and text.
Styled according to Figma design with text_muted/text_selected colors.
"""

import logging 
from typing import Optional ,Callable 

from .button import Button 
from .image import ImageComponent ,ImageFit ,ImagePosition 
from ..theme import get_themed_style 
from ..unified_styles import Styles 
from ..types import UIEvent 
from ..coordinates import CoordinateSystem 

logger =logging .getLogger (__name__ )


class BackButton (Button ):
    """Back button component with icon and text styling."""

    def __init__ (self ,x :int =0 ,y :int =0 ,on_click :Optional [Callable ]=None ):

        icon_size =Styles .get_go_back_button_icon_size ()
        icon_gap =Styles .get_go_back_button_icon_gap ()
        text_width =CoordinateSystem .scale_int (48 )
        content_width =icon_size +icon_gap +text_width 
        content_height =max (icon_size ,CoordinateSystem .scale_int (20 ))

        super ().__init__ ("Back",x ,y ,content_width ,content_height ,corner_radius =0 ,on_click =on_click )


        self .style =get_themed_style ("default")
        self .style .background_color =Styles .Transparent 
        self .style .border_color =Styles .Transparent 
        self .style .border_width =0 
        self .style .text_color =Styles .TextMuted 
        self .style .focus_text_color =Styles .TextSelected 


        self .set_text_align ("left")


        self .icon_component =ImageComponent (
        image_path ="arrow_backward.png",
        x =x ,
        y =y +(content_height -icon_size )//2 ,
        width =icon_size ,
        height =icon_size ,
        fit =ImageFit .CONTAIN ,
        position =ImagePosition .CENTER 
        )


        self .text_x =x +icon_size +icon_gap 
        self .text_y =y +(content_height -self .style .font_size )//2 -CoordinateSystem .scale_int (20 )

    def set_position (self ,x :int ,y :int ):
        """Override to update both button and icon positions."""
        super ().set_position (x ,y )


        icon_size =Styles .get_go_back_button_icon_size ()
        content_height =self .bounds .height 
        self .icon_component .set_position (
        x ,
        y +(content_height -icon_size )//2 
        )


        icon_gap =Styles .get_go_back_button_icon_gap ()
        self .text_x =x +icon_size +icon_gap 
        self .text_y =y +(content_height -self .style .font_size )//2 

    def set_size (self ,width :int ,height :int ):
        """Override to update component sizing."""
        super ().set_size (width ,height )


        icon_size =Styles .get_go_back_button_icon_size ()
        icon_gap =Styles .get_go_back_button_icon_gap ()
        self .text_x =self .bounds .x +icon_size +icon_gap 
        self .text_y =self .bounds .y +(height -self .style .font_size )//2 


        self .icon_component .set_position (
        self .bounds .x ,
        self .bounds .y +(height -icon_size )//2 
        )

    def render (self ,renderer ):
        """Render the back button with icon and text."""
        if not self .visible :
            return 


        self ._update_pressed_state ()


        if self .is_hovered :
            text_color =self .style .focus_text_color 
            logger .debug (f"BackButton HOVERED: text_color={text_color}")
        else :
            text_color =self .style .text_color 
            logger .debug (f"BackButton NOT HOVERED: text_color={text_color}")



        original_text =self .text 
        self .text =""
        super ().render (renderer )
        self .text =original_text 


        self .icon_component .render (renderer )


        renderer .draw_text (self .text ,self .text_x ,self .text_y ,self .style .font_size ,text_color )

    def _get_current_colors (self ):
        """Override to return transparent colors for background/border."""

        bg_color =Styles .Transparent 
        border_color =Styles .Transparent 


        if self .is_hovered :
            text_color =self .style .focus_text_color 
        else :
            text_color =self .style .text_color 

        return bg_color ,border_color ,text_color 

    def _on_mouse_enter (self ,event :UIEvent )->bool :
        """Handle mouse enter event with debug logging."""
        result =super ()._on_mouse_enter (event )
        logger .debug (f"BackButton '{self.text}' HOVERED - is_hovered={self.is_hovered}")
        return result 

    def _on_mouse_leave (self ,event :UIEvent )->bool :
        """Handle mouse leave event with debug logging."""
        result =super ()._on_mouse_leave (event )
        logger .debug (f"BackButton '{self.text}' UNHOVERED - is_hovered={self.is_hovered}")
        return result 

    def cleanup (self ):
        """Clean up resources when button is destroyed."""
        if self .icon_component :
            self .icon_component .cleanup ()
