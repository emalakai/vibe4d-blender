"""
Fix for TextInput component to handle UI scale changes properly.

PROBLEM:
--------
The TextInput component behaved strangely during dynamic UI scaling changes:
- Text wrapping would break during scale changes
- Cursor positioning would be incorrect
- Component worked fine after reload but not during live scale updates
- Height calculations were sometimes incorrect during scale changes

ROOT CAUSE:
-----------
The TextInput component's dimension caching system used cache keys that didn't include UI scale:
- Cache key was only (text, font_size) 
- When UI scale changed, actual text dimensions changed but cache returned stale values
- This caused incorrect text measurement, wrapping, and cursor positioning

ADDITIONAL ISSUE:
-----------------
The TextInput component used static style values (font_size, padding) that didn't update
when UI scale changed, causing incorrect height calculations and padding.

SOLUTION:
---------
Three-part fix:
1. Enhanced cache invalidation in UIManager during UI recreation (manager.py)
2. Scale-aware caching patch (this file)
3. Dynamic scaling for height calculations and padding (this file)

This patches multiple methods to ensure all calculations use current UI scale values.
"""

from .coordinates import CoordinateSystem 
from .unified_styles import UnifiedStyles 
import logging 
import math 

logger =logging .getLogger (__name__ )

def patch_text_input_for_scaling ():
    """Patch TextInput component to handle UI scale changes properly."""
    try :
        from .components .text_input import TextInput 
        import blf 


        original_get_text_dimensions =TextInput .get_text_dimensions 
        original_get_line_height =TextInput ._get_line_height 
        original_get_total_padding_vertical =TextInput ._get_total_padding_vertical 
        original_get_total_padding_horizontal =TextInput ._get_total_padding_horizontal 
        original_get_text_usable_width =TextInput ._get_text_usable_width 

        def get_text_dimensions_with_scale (self ,text :str ,font_size :int =None ):
            """Enhanced version that includes UI scale in cache key."""
            if font_size is None :

                font_size =UnifiedStyles .get_font_size ()


            current_ui_scale =CoordinateSystem .get_ui_scale ()
            cache_key =(text ,font_size ,current_ui_scale )

            if cache_key not in self ._dimension_cache :

                try :
                    blf .size (0 ,font_size )
                except Exception as e :
                    logger .warning (f"Failed to set font size: {e}")
                    blf .size (0 ,font_size )


                self ._dimension_cache [cache_key ]=blf .dimensions (0 ,text )

            return self ._dimension_cache [cache_key ]

        def get_line_height_with_scale (self ):
            """Get height of a single line using dynamic scaling."""

            scaled_font_size =UnifiedStyles .get_font_size ()
            LINE_HEIGHT_MULTIPLIER =1.21 
            return math .ceil (scaled_font_size *LINE_HEIGHT_MULTIPLIER )

        def get_total_padding_vertical_with_scale (self ):
            """Get total vertical padding using dynamic scaling."""

            scaled_padding =UnifiedStyles .get_text_input_padding ()
            scaled_border_width =UnifiedStyles .get_text_input_border_width ()

            return (scaled_padding *2 )+self .content_padding_top +self .content_padding_bottom +(scaled_border_width *2 )

        def get_total_padding_horizontal_with_scale (self ):
            """Get total horizontal padding using dynamic scaling."""

            scaled_padding =UnifiedStyles .get_text_input_padding ()
            scaled_border_width =UnifiedStyles .get_text_input_border_width ()

            return (scaled_padding *2 )+self .content_padding_left +self .content_padding_right +(scaled_border_width *2 )

        def get_text_usable_width_with_scale (self ):
            """Get the usable width for text rendering with dynamic scaling."""
            usable_width =self .bounds .width -self ._get_total_padding_horizontal ()


            current_ui_scale =CoordinateSystem .get_ui_scale ()
            MIN_SAFETY_MARGIN =int (4 *current_ui_scale )
            MIN_USABLE_WIDTH =int (30 *current_ui_scale )
            SAFETY_MARGIN_RATIO =0.02 


            safety_margin =max (MIN_SAFETY_MARGIN ,math .ceil (usable_width *SAFETY_MARGIN_RATIO ))
            usable_width -=safety_margin 


            return max (MIN_USABLE_WIDTH ,usable_width )


        TextInput .get_text_dimensions =get_text_dimensions_with_scale 
        TextInput ._get_line_height =get_line_height_with_scale 
        TextInput ._get_total_padding_vertical =get_total_padding_vertical_with_scale 
        TextInput ._get_total_padding_horizontal =get_total_padding_horizontal_with_scale 
        TextInput ._get_text_usable_width =get_text_usable_width_with_scale 

    except Exception as e :
        logger .error (f"Failed to patch TextInput for UI scale support: {e}")
        import traceback 
        logger .error (f"Traceback: {traceback.format_exc()}")


patch_text_input_for_scaling ()