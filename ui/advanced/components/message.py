"""
Message component for displaying user messages in chat-like interface.
Features rounded background with border and proper text rendering.
"""

import blf 
import logging 
from typing import TYPE_CHECKING ,List 

from .base import UIComponent 
from ..theme import get_themed_style ,get_theme_color 
from ..styles import FontSizes 
from ..coordinates import CoordinateSystem 

if TYPE_CHECKING :
    from ..renderer import UIRenderer 

logger =logging .getLogger (__name__ )


def wrap_text_blf (text :str ,max_width :int ,font_size :int =28 )->List [str ]:
    """Wrap text using BLF text measurements with correct font size."""
    if not text :
        return [""]

    try :

        blf .size (0 ,font_size )
        full_width =blf .dimensions (0 ,text )[0 ]


        if full_width <=max_width :
            return [text ]


        segments =[]
        words =text .split (' ')
        current_segment =""

        for word in words :

            test_segment =current_segment +(" "if current_segment else "")+word 
            test_width =blf .dimensions (0 ,test_segment )[0 ]

            if test_width <=max_width -4 :
                current_segment =test_segment 
            else :

                if current_segment :
                    segments .append (current_segment )

                    word_width =blf .dimensions (0 ,word )[0 ]
                    if word_width <=max_width -4 :
                        current_segment =word 
                    else :

                        segments .extend (_break_long_word_blf (word ,max_width -4 ,font_size ))
                        current_segment =""
                else :

                    segments .extend (_break_long_word_blf (word ,max_width -4 ,font_size ))
                    current_segment =""


        if current_segment :
            segments .append (current_segment )

        result =segments if segments else [text ]
        logger .debug (f"Wrapped text '{text[:50]}...' into {len(result)} segments")
        return result 

    except Exception as e :
        logger .error (f"Error in wrap_text_blf: {e}")

        return _fallback_wrap (text ,max_width ,font_size )


def _break_long_word_blf (word :str ,max_width :int ,font_size :int )->List [str ]:
    """Break a long word using BLF measurements."""
    if not word :
        return [""]

    try :
        blf .size (0 ,font_size )
        segments =[]
        current_chars =""

        for char in word :
            test_chars =current_chars +char 
            test_width =blf .dimensions (0 ,test_chars )[0 ]

            if test_width <=max_width :
                current_chars =test_chars 
            else :
                if current_chars :
                    segments .append (current_chars )
                current_chars =char 

        if current_chars :
            segments .append (current_chars )

        return segments if segments else [word ]

    except Exception as e :
        logger .error (f"Error breaking long word: {e}")

        chars_per_line =max (1 ,max_width //10 )
        return [word [i :i +chars_per_line ]for i in range (0 ,len (word ),chars_per_line )]


def _fallback_wrap (text :str ,max_width :int ,font_size :int )->List [str ]:
    """Fallback text wrapping when BLF is not available."""

    chars_per_line =max (10 ,max_width //max (8 ,font_size //4 ))

    words =text .split (' ')
    lines =[]
    current_line =""

    for word in words :
        test_line =current_line +(" "if current_line else "")+word 
        if len (test_line )<=chars_per_line :
            current_line =test_line 
        else :
            if current_line :
                lines .append (current_line )
            current_line =word 

    if current_line :
        lines .append (current_line )

    return lines if lines else [text ]


class MessageComponent (UIComponent ):
    """Component for displaying user messages with styled background."""

    def __init__ (self ,message :str ,x :int =0 ,y :int =0 ,width :int =400 ,height :int =20 ):
        super ().__init__ (x ,y ,width ,height )

        self .message =message 
        self .corner_radius =CoordinateSystem .scale_int (8 )


        self .padding_horizontal =CoordinateSystem .scale_int (8 )
        self .padding_vertical =CoordinateSystem .scale_int (8 )


        self .line_height_multiplier =1.5 


        self ._cached_wrapped_lines =None 
        self ._cached_width =None 
        self ._cached_message =None 
        self ._cached_font_size =None 


        self .apply_themed_style ("message")

        logger .debug (f"MessageComponent created with message: {message}")

    def apply_themed_style (self ,style_type :str ="message"):
        """Apply themed style to the message component using centralized colors."""
        try :
            from ..colors import Colors 
            from ..theme import get_themed_style 


            self .style =get_themed_style ("button")


            self .style .background_color =Colors .Border 
            self .style .border_color =Colors .Primary 
            self .style .border_width =1 
            self .style .text_color =Colors .Text 
            self .style .font_size =FontSizes .Default 

        except Exception as e :
            logger .warning (f"Could not apply themed style: {e}")

            from ..colors import Colors 
            self .style .background_color =Colors .Border 
            self .style .border_color =Colors .Primary 
            self .style .border_width =1 
            self .style .text_color =Colors .Text 
            self .style .font_size =FontSizes .Default 

    def set_message (self ,message :str ):
        """Update the message text and invalidate cache."""
        if self .message !=message :
            self .message =message 
            self ._invalidate_text_cache ()

    def get_message (self )->str :
        """Get the current message text."""
        return self .message 

    def _invalidate_text_cache (self ):
        """Invalidate the text wrapping cache."""
        self ._cached_wrapped_lines =None 
        self ._cached_width =None 
        self ._cached_message =None 
        self ._cached_font_size =None 

    def _get_line_height (self )->int :
        """Calculate line height using 140% of font size."""
        return int (self .style .font_size *self .line_height_multiplier )

    def _get_wrapped_lines (self ,available_width :int )->List [str ]:
        """Get wrapped lines with caching to avoid recalculating every frame."""

        if (self ._cached_wrapped_lines is not None and 
        self ._cached_width ==available_width and 
        self ._cached_message ==self .message and 
        self ._cached_font_size ==self .style .font_size ):
            return self ._cached_wrapped_lines 


        self ._cached_wrapped_lines =wrap_text_blf (self .message ,available_width ,self .style .font_size )
        self ._cached_width =available_width 
        self ._cached_message =self .message 
        self ._cached_font_size =self .style .font_size 

        logger .debug (f"Recalculated wrapped lines for message: '{self.message[:30]}...' -> {len(self._cached_wrapped_lines)} lines")

        return self ._cached_wrapped_lines 

    def calculate_required_size (self ,max_width :int )->tuple [int ,int ]:
        """Calculate the width and height needed to display the message properly using BLF measurements."""
        if not self .message :
            return (100 ,40 )


        border_and_padding =(self .padding_horizontal *2 )+(self .style .border_width *2 )
        available_text_width =max_width -border_and_padding 


        wrapped_lines =self ._get_wrapped_lines (available_text_width )


        try :
            blf .size (0 ,self .style .font_size )
            max_line_width =0 
            for line in wrapped_lines :
                if line .strip ():
                    line_width =blf .dimensions (0 ,line )[0 ]
                    max_line_width =max (max_line_width ,line_width )
        except Exception as e :
            logger .error (f"Error measuring text width: {e}")

            max_line_width =max (len (line )for line in wrapped_lines )*(self .style .font_size *0.6 )


        content_width =max_line_width +border_and_padding 
        content_width =min (content_width ,max_width )


        line_height =self ._get_line_height ()
        vertical_padding_and_border =(self .padding_vertical *2 )+(self .style .border_width *2 )
        content_height =len (wrapped_lines )*line_height +vertical_padding_and_border 

        return content_width ,max (40 ,content_height )

    def _calculate_wrapped_lines (self ,available_width :int )->list [str ]:
        """Calculate how text should be wrapped using BLF measurements."""
        return self ._get_wrapped_lines (available_width )

    def calculate_required_height (self ,available_width :int )->int :
        """Calculate the height needed to display the message properly."""
        _ ,height =self .calculate_required_size (available_width )
        return height 

    def set_size (self ,width :int ,height :int ):
        """Override set_size to invalidate cache when size changes."""
        old_width =self .bounds .width 
        super ().set_size (width ,height )

        if old_width !=width :
            self ._invalidate_text_cache ()

    def render (self ,renderer :'UIRenderer'):
        """Render the message component with rounded background and border."""
        if not self .visible or not self .message :
            return 


        renderer .draw_rounded_rect (self .bounds ,self .style .background_color ,self .corner_radius )


        renderer .draw_rounded_rect_outline (
        self .bounds ,
        self .style .border_color ,
        self .style .border_width ,
        self .corner_radius 
        )


        text_x =self .bounds .x +self .padding_horizontal +self .style .border_width 
        text_y =self .bounds .y +self .padding_vertical +self .style .border_width +CoordinateSystem .scale_int (4 )
        text_width =self .bounds .width -(self .padding_horizontal *2 )-(self .style .border_width *2 )
        text_height =self .bounds .height -(self .padding_vertical *2 )-(self .style .border_width *2 )


        if len (self .message )>0 :
            self ._render_wrapped_text (renderer ,text_x ,text_y ,text_width ,text_height )

    def _render_wrapped_text (self ,renderer :'UIRenderer',x :int ,y :int ,width :int ,height :int ):
        """Render text with word wrapping within the specified bounds using cached wrapped lines."""
        if not self .message :
            return 


        blf .size (0 ,self .style .font_size )


        wrapped_lines =self ._get_wrapped_lines (width )

        if not wrapped_lines :
            return 


        line_height =self ._get_line_height ()


        total_lines =len (wrapped_lines )
        total_text_height =total_lines *line_height 




        text_area_center_y =y +height /2 



        text_block_top_y =text_area_center_y +total_text_height /2 


        current_y =text_block_top_y -line_height 

        for line in wrapped_lines :
            if current_y >=y and current_y <=y +height :
                renderer .draw_text (
                line ,
                x ,
                current_y ,
                self .style .font_size ,
                self .style .text_color 
                )
            current_y -=line_height 

    def auto_resize_to_content (self ,max_width :int ):
        """Auto-resize the component to fit the message content."""
        required_width ,required_height =self .calculate_required_size (max_width )
        self .set_size (required_width ,required_height )