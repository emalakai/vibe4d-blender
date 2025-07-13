"""
Send button component
"""

import logging 
from .button import Button 
from .image import ImageComponent ,ImageFit ,ImagePosition 
from ..theme import get_themed_style 
from ..colors import Colors 
from ..unified_styles import Styles 
from ..component_theming import get_component_color 

logger =logging .getLogger (__name__ )


class SendButton (Button ):

    def __init__ (self ,text :str ="",x :int =0 ,y :int =0 ,width :int =50 ,height :int =50 ,
    corner_radius :int =6 ,on_click =None ):
        super ().__init__ (text ,x ,y ,width ,height ,corner_radius ,on_click )


        self .style =get_themed_style ("button")


        self .style .background_color =get_component_color ('button','background_color')
        self .style .focus_background_color =Styles .lighten_color (self .style .background_color ,10 )
        self .style .pressed_background_color =Styles .lighten_color (self .style .background_color ,20 )


        self .style .border_width =0 


        self .corner_radius =corner_radius 


        self .is_send_mode =True 
        self .on_send_click =on_click 
        self .on_stop_click =None 


        icon_size =Styles .get_send_button_icon_size ()
        icon_padding =(width -icon_size )//2 

        self .icon_component =ImageComponent (
        image_path ="arrow_up.png",
        x =x +icon_padding ,
        y =y +icon_padding ,
        width =icon_size ,
        height =icon_size ,
        fit =ImageFit .CONTAIN ,
        position =ImagePosition .CENTER 
        )

    def set_mode (self ,is_send_mode :bool ):
        """Switch between send and stop modes."""
        self .is_send_mode =is_send_mode 

    def set_stop_callback (self ,callback ):
        """Set the callback for stop button clicks."""
        self .on_stop_click =callback 

    def _trigger_click (self ):
        """Trigger the appropriate button click action based on current mode."""
        if not self .is_enabled :
            return 

        try :
            if self .is_send_mode and self .on_send_click :
                self .on_send_click ()
            elif not self .is_send_mode and self .on_stop_click :
                self .on_stop_click ()
        except Exception as e :
            logger .error (f"Error executing button click callback: {e}")

    def set_position (self ,x :int ,y :int ):
        """Override to update icon position as well."""
        super ().set_position (x ,y )
        icon_size =Styles .get_send_button_icon_size ()
        icon_padding =(self .bounds .width -icon_size )//2 
        self .icon_component .set_position (
        x +icon_padding ,
        y +icon_padding 
        )

    def set_size (self ,width :int ,height :int ):
        """Override to update icon size as well."""
        super ().set_size (width ,height )
        icon_size =Styles .get_send_button_icon_size ()
        icon_padding =(width -icon_size )//2 


        self .icon_component .set_size (icon_size ,icon_size )


        self .icon_component .set_position (
        self .bounds .x +icon_padding ,
        self .bounds .y +icon_padding 
        )

    def render (self ,renderer ):
        if not self .visible :
            return 


        self ._update_pressed_state ()


        bg_color =self ._get_current_colors ()


        if self .corner_radius >0 :
            renderer .draw_rounded_rect (self .bounds ,bg_color ,self .corner_radius )
        else :

            renderer .draw_rect (self .bounds ,bg_color )

        if self .is_send_mode :
            self .icon_component .set_image ("arrow_up.png")
        else :
            self .icon_component .set_image ("stop.png")

        self .icon_component .render (renderer )

    def _get_current_colors (self ):
        """Get colors for current state using base class method."""
        if not self .is_enabled :

            bg_color =tuple (c *0.5 for c in self .style .background_color [:3 ])+(0.5 ,)
        elif self .is_pressed :

            bg_color =self .style .pressed_background_color 
        elif self .is_hovered :

            bg_color =self .style .focus_background_color 
        else :

            bg_color =self .style .background_color 

        return bg_color 

    def cleanup (self ):
        """Clean up resources when button is destroyed."""
        if self .icon_component :
            self .icon_component .cleanup ()