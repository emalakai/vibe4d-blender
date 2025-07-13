"""
Container component for flexible layout management.
Provides a general-purpose container with various layout options and styling.
"""

import logging 
from typing import TYPE_CHECKING ,List ,Optional ,Union ,Tuple 
from enum import Enum 

from .base import UIComponent 
from ..types import EventType ,UIEvent ,Bounds 

if TYPE_CHECKING :
    from ..renderer import UIRenderer 

logger =logging .getLogger (__name__ )


def _get_numeric_value (obj ,attr_name :str ,default =0 ):
    """
    Safely get numeric value from an object attribute.
    Handles cases where the attribute might be a property object.
    """
    try :
        value =getattr (obj ,attr_name ,default )

        if hasattr (value ,'__get__'):
            return default 

        if callable (value ):
            return value ()

        return value if isinstance (value ,(int ,float ))else default 
    except (AttributeError ,TypeError ,ValueError ):
        return default 


class ContainerType (Enum ):
    """Types of containers."""
    PANEL ="panel"
    GROUP ="group"
    CARD ="card"
    SECTION ="section"
    TOOLBAR ="toolbar"


class Container (UIComponent ):
    """Flexible container component for layout management."""

    def __init__ (self ,x :int =0 ,y :int =0 ,width :int =200 ,height :int =150 ,
    container_type :ContainerType =ContainerType .PANEL ,
    padding :int =10 ,
    spacing :int =5 ,
    corner_radius :int =4 ,
    title :str ="",
    collapsible :bool =False ):
        super ().__init__ (x ,y ,width ,height )


        self .container_type =container_type 
        self .spacing =spacing 
        self .corner_radius =corner_radius 
        self .title =title 
        self .collapsible =collapsible 
        self .padding =padding 


        self .is_collapsed =False 
        self .children :List [UIComponent ]=[]


        self .title_bar_height =30 if title else 0 
        self .title_bar_bounds =Bounds (0 ,0 ,0 ,0 )


        self .content_bounds =Bounds (0 ,0 ,0 ,0 )


        if not hasattr (self ,'style'):
            from ..types import Style 
            self .style =Style ()


        self .apply_themed_style (container_type .value )


        if self .collapsible and self .title :
            self .add_event_handler (EventType .MOUSE_CLICK ,self ._on_title_click )

        self ._update_layout ()

    def apply_themed_style (self ,style_type :str ="panel"):
        """Apply themed style based on container type."""

        if not hasattr (self ,'style')or self .style is None :
            from ..types import Style 
            self .style =Style ()

        try :
            from ..theme import get_themed_style 




            if not hasattr (self ,'container_type'):

                themed_style =get_themed_style ("panel")
                if themed_style :
                    self .style =themed_style 

                if not hasattr (self .style ,'background_color')or self .style .background_color is None :
                    self .style .background_color =(0.15 ,0.15 ,0.15 ,1.0 )
                if not hasattr (self .style ,'border_color')or self .style .border_color is None :
                    self .style .border_color =(0.3 ,0.3 ,0.3 ,1.0 )
            elif self .container_type ==ContainerType .PANEL :
                themed_style =get_themed_style ("panel")
                if themed_style :
                    self .style =themed_style 

                if not hasattr (self .style ,'background_color')or self .style .background_color is None :
                    self .style .background_color =(0.15 ,0.15 ,0.15 ,1.0 )
                if not hasattr (self .style ,'border_color')or self .style .border_color is None :
                    self .style .border_color =(0.3 ,0.3 ,0.3 ,1.0 )
            elif self .container_type ==ContainerType .GROUP :

                self .style .background_color =(0 ,0 ,0 ,0 )
                self .style .border_color =(0 ,0 ,0 ,0 )
            elif self .container_type ==ContainerType .CARD :
                themed_style =get_themed_style ("panel")
                if themed_style :
                    self .style =themed_style 
                self .style .background_color =(0.2 ,0.2 ,0.2 ,1.0 )
                self .style .border_color =(0.4 ,0.4 ,0.4 ,1.0 )
            elif self .container_type ==ContainerType .SECTION :
                themed_style =get_themed_style ("panel")
                if themed_style :
                    self .style =themed_style 
                self .style .background_color =(0.18 ,0.18 ,0.18 ,1.0 )
                self .style .border_color =(0.3 ,0.3 ,0.3 ,1.0 )
            elif self .container_type ==ContainerType .TOOLBAR :
                themed_style =get_themed_style ("panel")
                if themed_style :
                    self .style =themed_style 
                self .style .background_color =(0.25 ,0.25 ,0.25 ,1.0 )
                self .style .border_color =(0.3 ,0.3 ,0.3 ,1.0 )


            if not hasattr (self .style ,'text_color')or self .style .text_color is None :
                self .style .text_color =(1.0 ,1.0 ,1.0 ,1.0 )


            if not hasattr (self .style ,'border_width'):
                self .style .border_width =1 

        except (ImportError ,Exception )as e :
            logger .warning (f"Failed to apply themed style: {e}")

            self .style .background_color =(0.15 ,0.15 ,0.15 ,1.0 )
            self .style .border_color =(0.3 ,0.3 ,0.3 ,1.0 )
            self .style .text_color =(1.0 ,1.0 ,1.0 ,1.0 )
            self .style .border_width =1 

    def add_child (self ,child :UIComponent ):
        """Add a child component to the container."""
        self .children .append (child )
        if hasattr (child ,'ui_state'):
            child .ui_state =self .ui_state 
        self ._update_layout ()

    def remove_child (self ,child :UIComponent ):
        """Remove a child component from the container with proper cleanup."""
        if child in self .children :

            if hasattr (child ,'cleanup'):
                try :
                    child .cleanup ()
                except Exception as e :
                    logger .debug (f"Error cleaning up child component during removal: {e}")

            self .children .remove (child )
            self ._update_layout ()

    def clear_children (self ):
        """Clear all child components with proper cleanup."""

        for child in self .children :
            if hasattr (child ,'cleanup'):
                try :
                    child .cleanup ()
                except Exception as e :
                    logger .debug (f"Error cleaning up child component: {e}")

        self .children .clear ()
        self ._update_layout ()

    def set_title (self ,title :str ):
        """Set the container title."""
        self .title =title 
        self .title_bar_height =30 if title else 0 
        self ._update_layout ()

    def set_collapsed (self ,collapsed :bool ):
        """Set the collapsed state."""
        if self .collapsible :
            self .is_collapsed =collapsed 
            self ._update_layout ()

    def toggle_collapsed (self ):
        """Toggle the collapsed state."""
        if self .collapsible :
            self .is_collapsed =not self .is_collapsed 
            self ._update_layout ()

    def _on_title_click (self ,event :UIEvent )->bool :
        """Handle title bar click for collapsible containers."""
        if (self .collapsible and self .title and 
        self .title_bar_bounds .contains_point (event .mouse_x ,event .mouse_y )):
            self .toggle_collapsed ()
            return True 
        return False 

    def _update_layout (self ):
        """Update container layout and child positioning."""

        if self .title :
            self .title_bar_bounds =Bounds (
            self .bounds .x ,
            self .bounds .y +self .bounds .height -self .title_bar_height ,
            self .bounds .width ,
            self .title_bar_height 
            )


        padding_value =_get_numeric_value (self ,'padding',10 )
        content_y =self .bounds .y +padding_value 
        content_height =self .bounds .height -(padding_value *2 )

        if self .title :
            content_height -=self .title_bar_height 

        if self .is_collapsed :
            content_height =0 

        self .content_bounds =Bounds (
        self .bounds .x +padding_value ,
        content_y ,
        self .bounds .width -(padding_value *2 ),
        max (0 ,content_height )
        )

    def get_content_bounds (self )->Bounds :
        """Get the content area bounds."""
        return self .content_bounds 

    def render (self ,renderer :'UIRenderer'):
        """Render the container."""

        if self .container_type ==ContainerType .GROUP :
            return 


        if hasattr (self .style ,'background_color')and self .style .background_color [3 ]>0 :
            if hasattr (self ,'corner_radius')and self .corner_radius >0 :
                renderer .draw_rounded_rect (self .bounds ,self .style .background_color ,self .corner_radius )
            else :
                renderer .draw_rect (self .bounds ,self .style .background_color )


        if (hasattr (self .style ,'border_color')and hasattr (self .style ,'border_width')and 
        self .style .border_color [3 ]>0 and self .style .border_width >0 ):
            if hasattr (self ,'corner_radius')and self .corner_radius >0 :
                renderer .draw_rounded_rect_outline (self .bounds ,self .style .border_color ,
                self .style .border_width ,self .corner_radius )
            else :
                renderer .draw_rect_outline (self .bounds ,self .style .border_color ,self .style .border_width )


        if self .title and not self .is_collapsed :
            self ._render_title_bar (renderer )

    def _render_title_bar (self ,renderer :'UIRenderer'):
        """Render the title bar."""
        if not self .title :
            return 


        title_y =self .title_bar_bounds .y +(self .title_bar_bounds .height //2 )-10 
        title_x =self .title_bar_bounds .x +10 

        font_size =getattr (self .style ,'font_size',16 )
        text_color =getattr (self .style ,'text_color',(1.0 ,1.0 ,1.0 ,1.0 ))

        renderer .draw_text (self .title ,title_x ,title_y ,font_size ,text_color )


        if self .collapsible :
            indicator ="▼"if not self .is_collapsed else "▶"
            indicator_x =self .title_bar_bounds .x +self .title_bar_bounds .width -25 
            renderer .draw_text (indicator ,indicator_x ,title_y ,font_size ,text_color )

    def handle_event (self ,event :UIEvent )->bool :
        """Handle events for the container and its children."""

        handled =super ().handle_event (event )


        if not handled and not self .is_collapsed :
            for child in reversed (self .children ):
                if hasattr (child ,'handle_event')and child .handle_event (event ):
                    return True 

        return handled 

    def update_layout (self ):
        """Update component layout (called when viewport changes)."""
        super ().update_layout ()
        self ._update_layout ()


        for child in self .children :
            if hasattr (child ,'update_layout'):
                child .update_layout ()