"""
Error message component for displaying error messages in chat interface.
Features distinctive styling with error colors and icons.
"""

import blf 
import logging 
from typing import TYPE_CHECKING ,List 

from .base import UIComponent 
from .markdown_message import MarkdownMessageComponent 
from ..theme import get_themed_style ,get_theme_color 
from ..styles import FontSizes 
from ..coordinates import CoordinateSystem 

if TYPE_CHECKING :
    from ..renderer import UIRenderer 

logger =logging .getLogger (__name__ )


class ErrorMessageComponent (MarkdownMessageComponent ):
    """Component for displaying error messages with special styling."""

    def __init__ (self ,error_message :str ,x :int =0 ,y :int =0 ,width :int =400 ,height :int =40 ):

        super ().__init__ (error_message ,x ,y ,width ,height )


        self .apply_error_styling ()

        logger .debug (f"ErrorMessageComponent created with message: {error_message}")

    def apply_error_styling (self ):
        """Apply error-specific styling to the message component."""


        self .style =get_themed_style ("button")


        self .style .background_color =(0.0 ,0.0 ,0.0 ,0.0 )
        self .style .border_color =(0.0 ,0.0 ,0.0 ,0.0 )
        self .style .border_width =0 
        self .style .text_color =(1.0 ,1.0 ,1.0 ,1.0 )
        self .style .font_size =FontSizes .Default 


        self .padding =CoordinateSystem .scale_int (8 )


        self .corner_radius =CoordinateSystem .scale_int (8 )

    def apply_themed_style (self ,style_type :str ="error"):
        """Override to maintain error styling."""
        self .apply_error_styling ()

    def auto_resize_to_content (self ,max_width :int ):
        """Override auto-resize to ensure proper sizing for error messages."""
        try :
            from ..coordinates import CoordinateSystem 


            required_width ,required_height =self .calculate_required_size (max_width )


            min_width =max (CoordinateSystem .scale_int (150 ),required_width )


            min_height =max (CoordinateSystem .scale_int (30 ),required_height +CoordinateSystem .scale_int (10 ))


            final_width =min (min_width ,max_width )

            self .set_size (final_width ,min_height )

            logger .debug (f"ErrorMessageComponent auto-resized to: {final_width}x{min_height}")

        except Exception as e :
            logger .error (f"Error in ErrorMessageComponent auto_resize_to_content: {e}")

            from ..coordinates import CoordinateSystem 
            fallback_width =min (CoordinateSystem .scale_int (200 ),max_width )
            fallback_height =CoordinateSystem .scale_int (40 )
            self .set_size (fallback_width ,fallback_height )

    def set_error_message (self ,error_message :str ):
        """Update the error message text."""
        self .set_markdown (error_message )

    def get_error_message (self )->str :
        """Get the current error message text."""
        return self .markdown_text 