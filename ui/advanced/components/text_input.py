"""
Advanced Text input component with multiline support, selection, and smart features.
Implements line-based text storage, word wrapping, clipboard integration, and advanced navigation.
"""

import blf 
import gpu 
from gpu_extras .batch import batch_for_shader 
import time 
import logging 
import re 
import math 
from typing import TYPE_CHECKING ,List ,Tuple ,Optional ,Set ,Callable ,Any 
from dataclasses import dataclass ,field 
from collections import deque 

from .base import UIComponent 
from ..types import EventType ,UIEvent ,CursorType ,Bounds 
from ..state import UIState 
from ..coordinates import CoordinateSystem 

if TYPE_CHECKING :
    from ..renderer import UIRenderer 

logger =logging .getLogger (__name__ )


CURSOR_BLINK_INTERVAL =0.45 
SCROLL_SENSITIVITY =30 
SCROLL_MARGIN =20 
SCROLL_SPEED =20 
AUTO_SCROLL_TOLERANCE =10 
LINE_HEIGHT_MULTIPLIER =1.21 
FONT_BASELINE_OFFSET_RATIO =0.5 
SAFETY_MARGIN_RATIO =0.02 
MIN_SAFETY_MARGIN =4 
MIN_USABLE_WIDTH =30 
MIN_INDICATOR_WIDTH =20 
MIN_INDICATOR_HEIGHT =4 
INDICATOR_OPACITY =0.7 
TRACK_OPACITY =0.3 
SELECTION_OPACITY =0.3 
PLACEHOLDER_OPACITY =0.5 
HEIGHT_CHANGE_THRESHOLD =5 
DIMENSION_BUFFER =2 
MAX_UNDO_HISTORY =500 


@dataclass 
class TextSelection :
    """Represents a text selection range."""
    start_row :int =0 
    start_col :int =0 
    end_row :int =0 
    end_col :int =0 
    active :bool =False 

    def clear (self ):
        """Clear the selection."""
        self .active =False 
        self .start_row =self .start_col =self .end_row =self .end_col =0 

    def set (self ,start_row :int ,start_col :int ,end_row :int ,end_col :int ):
        """Set selection bounds."""

        if (start_row ,start_col )>(end_row ,end_col ):
            start_row ,start_col ,end_row ,end_col =end_row ,end_col ,start_row ,start_col 

        self .start_row ,self .start_col =start_row ,start_col 
        self .end_row ,self .end_col =end_row ,end_col 
        self .active =True 

    def contains (self ,row :int ,col :int )->bool :
        """Check if position is within selection."""
        if not self .active :
            return False 
        return (self .start_row ,self .start_col )<=(row ,col )<(self .end_row ,self .end_col )


@dataclass 
class TextState :
    """Represents a snapshot of text state for undo/redo."""
    text_lines :List [str ]
    cursor_row :int 
    cursor_col :int 
    selection :TextSelection 

    def copy (self )->'TextState':
        """Create a deep copy of this state."""
        return TextState (
        text_lines =self .text_lines .copy (),
        cursor_row =self .cursor_row ,
        cursor_col =self .cursor_col ,
        selection =TextSelection (
        self .selection .start_row ,
        self .selection .start_col ,
        self .selection .end_row ,
        self .selection .end_col ,
        self .selection .active 
        )
        )


def wrap_text_blf (text :str ,max_width :int ,font_size :int =14 )->List [str ]:
    """Wrap text using BLF text measurements with correct font size."""
    if not text :
        return [""]


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

        if test_width <=max_width -DIMENSION_BUFFER :
            current_segment =test_segment 
        else :

            if current_segment :
                segments .append (current_segment )
                current_segment =word 
            else :

                segments .append (word )
                current_segment =""


    if current_segment :
        segments .append (current_segment )

    return segments if segments else [text ]


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


class TextInput (UIComponent ):
    """Advanced multiline text input component with smart features."""

    def __init__ (self ,x :int =0 ,y :int =0 ,width :int =600 ,height :int =300 ,placeholder :str ="",
    auto_resize :bool =True ,min_height :int =60 ,max_height :int =800 ,corner_radius :int =8 ,
    multiline :bool =True ,content_padding_top :int =0 ,content_padding_left :int =0 ,
    content_padding_right :int =0 ,content_padding_bottom :int =0 ):

        super ().__init__ (x ,y ,width ,height )


        self .placeholder =placeholder 
        self .auto_resize =auto_resize 
        self .min_height =min_height 
        self .max_height =max_height 
        self .corner_radius =corner_radius 
        self .multiline =multiline 


        self .content_padding_top =content_padding_top 
        self .content_padding_left =content_padding_left 
        self .content_padding_right =content_padding_right 
        self .content_padding_bottom =content_padding_bottom 


        self ._text_lines =[""]
        self .cursor_row =0 
        self .cursor_col =0 


        self .selection =TextSelection ()
        self .selection_anchor_row =0 
        self .selection_anchor_col =0 
        self ._selecting =False 
        self ._selection_start_row =0 
        self ._selection_start_col =0 


        self ._mouse_press_pos =None 
        self ._has_dragged =False 


        self ._cursor_visible =True 
        self ._last_cursor_toggle =time .time ()


        self .is_scrollable =False 
        self .scroll_offset_y =0 
        self .max_scroll_offset =0 


        self .horizontal_scroll_offset =0 
        self .max_horizontal_scroll_offset =0 
        self .is_horizontally_scrollable =False 


        self .wrapped_lines :List [List [str ]]=[[""]]
        self .wrap_cache_valid =False 
        self ._last_wrap_width =0 
        self ._text_content_hash =""


        self ._dimension_cache ={}
        self ._render_dirty =True 


        self .on_submit :Optional [Callable [[],None ]]=None 
        self .on_change :Optional [Callable [[str ],None ]]=None 


        self ._history :deque [TextState ]=deque (maxlen =MAX_UNDO_HISTORY )
        self ._history_index =-1 
        self ._save_state_on_next_change =True 


        self ._key_handlers =self ._build_key_dispatch_table ()


        self .apply_themed_style ("input")


        self .cursor_type =CursorType .TEXT 


        if not self .multiline :

            line_height =self ._get_line_height ()
            total_padding =self ._get_total_padding_vertical ()
            recommended_height =line_height +total_padding 


            absolute_minimum =self .style .font_size +total_padding 


            self .auto_resize =False 
            self .min_height =absolute_minimum 
            self .is_scrollable =False 


            if height ==300 :
                self .max_height =recommended_height 
                self .set_size (width ,recommended_height )
            else :

                self .max_height =max (height ,absolute_minimum )



        if height <self .min_height :
            self .set_size (width ,self .min_height )


        self ._save_initial_state ()


        self .add_event_handler (EventType .MOUSE_CLICK ,self ._on_mouse_click )
        self .add_event_handler (EventType .MOUSE_PRESS ,self ._on_mouse_press )
        self .add_event_handler (EventType .MOUSE_DRAG ,self ._on_mouse_drag )
        self .add_event_handler (EventType .MOUSE_RELEASE ,self ._on_mouse_release )
        self .add_event_handler (EventType .MOUSE_MOVE ,self ._on_mouse_move )
        self .add_event_handler (EventType .MOUSE_ENTER ,self ._on_mouse_enter )
        self .add_event_handler (EventType .MOUSE_LEAVE ,self ._on_mouse_leave )
        if self .multiline :
            self .add_event_handler (EventType .MOUSE_WHEEL ,self ._on_mouse_wheel )
        else :
            self .add_event_handler (EventType .MOUSE_WHEEL ,self ._on_mouse_wheel_horizontal )
        self .add_event_handler (EventType .TEXT_INPUT ,self ._on_text_input )
        self .add_event_handler (EventType .KEY_PRESS ,self ._on_key_press )

    def _get_total_padding_vertical (self )->int :
        """Get total vertical padding including style and custom padding."""
        padding_value =_get_numeric_value (self .style ,'padding',10 )
        border_width =_get_numeric_value (self .style ,'border_width',1 )if hasattr (self .style ,'border_width')else 0 
        return (padding_value *2 )+self .content_padding_top +self .content_padding_bottom +(border_width *2 )

    def _get_total_padding_horizontal (self )->int :
        """Get total horizontal padding including style and custom padding."""
        padding_value =_get_numeric_value (self .style ,'padding',10 )
        border_width =_get_numeric_value (self .style ,'border_width',1 )if hasattr (self .style ,'border_width')else 0 
        return (padding_value *2 )+self .content_padding_left +self .content_padding_right +(border_width *2 )

    def _get_content_area_bounds (self )->Tuple [int ,int ,int ,int ]:
        """Get the content area bounds accounting for all padding and borders."""

        padding_value =_get_numeric_value (self .style ,'padding',10 )
        content_x =self .bounds .x +padding_value +self .content_padding_left 
        content_y =self .bounds .y +padding_value +self .content_padding_bottom 
        content_width =self .bounds .width -self ._get_total_padding_horizontal ()
        content_height =self .bounds .height -self ._get_total_padding_vertical ()

        return content_x ,content_y ,content_width ,content_height 

    def _set_font_size_with_dpi (self ,font_size :int ):
        """Set font size with proper scaling for consistent rendering."""
        try :


            font_id =0 
            blf .size (font_id ,font_size )
        except Exception as e :
            logger .warning (f"Failed to set font size: {e}")

            font_id =0 
            blf .size (font_id ,font_size )

    def _get_cached_dimensions (self ,text :str ,font_size :int )->Tuple [int ,int ]:
        """Get text dimensions with consistent font size handling."""
        cache_key =(text ,font_size )
        if cache_key not in self ._dimension_cache :

            try :
                blf .size (0 ,font_size )
            except Exception as e :
                logger .warning (f"Failed to set font size: {e}")
                blf .size (0 ,font_size )

            font_id =0 
            self ._dimension_cache [cache_key ]=blf .dimensions (font_id ,text )
        return self ._dimension_cache [cache_key ]

    def _invalidate_wrap_cache (self ):
        """Invalidate word wrap cache only when necessary."""
        current_hash ='\n'.join (self ._text_lines )
        current_width =self ._get_text_usable_width ()

        if (not self .wrap_cache_valid or 
        current_hash !=self ._text_content_hash or 
        self ._last_wrap_width !=current_width ):
            self .wrap_cache_valid =False 
            self ._text_content_hash =current_hash 
            self ._last_wrap_width =current_width 
            self ._dimension_cache .clear ()
            self ._render_dirty =True 

    def _update_word_wrap (self ):
        """Update word wrapping cache with optimizations and better width utilization."""
        if self .wrap_cache_valid :
            return 


        old_cursor_row =self .cursor_row 
        old_cursor_col =self .cursor_col 

        self .wrapped_lines =[]

        available_width =self ._get_text_usable_width ()
        self ._last_wrap_width =available_width 

        for line_idx ,line in enumerate (self ._text_lines ):
            if not line :
                self .wrapped_lines .append ([""])
                continue 

            wrapped_segments =self ._wrap_line_optimized (line ,available_width )
            self .wrapped_lines .append (wrapped_segments )

        self .wrap_cache_valid =True 


        if self ._text_lines :

            if self .cursor_row >=len (self ._text_lines ):
                self .cursor_row =len (self ._text_lines )-1 
            elif self .cursor_row <0 :
                self .cursor_row =0 


            if self .cursor_row <len (self ._text_lines ):
                current_line =self ._text_lines [self .cursor_row ]
                max_col =len (current_line )
                if self .cursor_col >max_col :
                    self .cursor_col =max_col 
                elif self .cursor_col <0 :
                    self .cursor_col =0 


        if self .auto_resize :
            self ._update_auto_resize ()

    def _update_auto_resize (self ):
        """Update component height based on content when auto-resize is enabled, with scrolling support."""
        if not self .auto_resize :
            return 


        total_display_lines =0 
        for segments in self .wrapped_lines :
            if segments :
                total_display_lines +=len (segments )


        if total_display_lines ==0 :
            total_display_lines =1 

        line_height =self ._get_line_height ()


        content_height =total_display_lines *line_height 
        required_height =content_height +self ._get_total_padding_vertical ()

        required_height +=0.6 *line_height 


        new_height =max (self .min_height ,min (self .max_height ,required_height ))


        if required_height >self .max_height :
            self .is_scrollable =True 

            visible_content_height =self .max_height -self ._get_total_padding_vertical ()

            self .max_scroll_offset =max (0 ,content_height -visible_content_height )


            self .scroll_offset_y =max (0 ,min (self .scroll_offset_y ,self .max_scroll_offset ))
        else :
            self .is_scrollable =False 
            self .scroll_offset_y =0 
            self .max_scroll_offset =0 


        height_diff =abs (new_height -self .bounds .height )
        if height_diff >HEIGHT_CHANGE_THRESHOLD :
            self ._last_content_height =content_height 
            self .set_size (self .bounds .width ,new_height )


        self ._ensure_cursor_visible ()

    def _wrap_line_optimized (self ,line :str ,max_width :int )->List [str ]:
        """Optimized O(N) line wrapping using cached dimensions."""
        if not line :
            return [""]


        full_width ,_ =self .get_text_dimensions (line )

        if full_width <=max_width :
            return [line ]


        segments =[]
        words =line .split (' ')
        current_segment =""
        current_width =0 


        word_widths ={}
        space_width ,_ =self .get_text_dimensions (' ')

        for word in words :
            if word not in word_widths :
                word_widths [word ]=self .get_text_dimensions (word )[0 ]

        effective_max_width =max_width -DIMENSION_BUFFER 

        for word in words :
            word_width =word_widths [word ]


            if current_segment :
                test_width =current_width +space_width +word_width 
                test_segment =current_segment +" "+word 
            else :
                test_width =word_width 
                test_segment =word 

            if test_width <=effective_max_width :

                current_segment =test_segment 
                current_width =test_width 
            else :

                if current_segment :
                    segments .append (current_segment )

                    if word_width <=effective_max_width :
                        current_segment =word 
                        current_width =word_width 
                    else :

                        word_segments =self ._break_long_word_optimized (word ,effective_max_width )
                        segments .extend (word_segments [:-1 ])
                        current_segment =word_segments [-1 ]if word_segments else ""
                        current_width =self .get_text_dimensions (current_segment )[0 ]if current_segment else 0 
                else :

                    word_segments =self ._break_long_word_optimized (word ,effective_max_width )
                    segments .extend (word_segments [:-1 ])
                    current_segment =word_segments [-1 ]if word_segments else ""
                    current_width =self .get_text_dimensions (current_segment )[0 ]if current_segment else 0 


        if current_segment :
            segments .append (current_segment )

        return segments if segments else [line ]

    def _break_long_word_optimized (self ,word :str ,max_width :int )->List [str ]:
        """Optimized long word breaking with dimension caching."""
        if not word :
            return [""]

        segments =[]
        current_chars =""
        current_width =0 

        for char in word :
            char_width ,_ =self .get_text_dimensions (char )
            test_width =current_width +char_width 

            if test_width <=max_width :
                current_chars +=char 
                current_width =test_width 
            else :
                if current_chars :
                    segments .append (current_chars )
                current_chars =char 
                current_width =char_width 

        if current_chars :
            segments .append (current_chars )

        return segments if segments else [word ]

    def _get_line_height (self )->int :
        """Get height of a single line."""
        return math .ceil (self .style .font_size *LINE_HEIGHT_MULTIPLIER )

    def _get_text_usable_width (self )->int :
        """Get the usable width for text rendering after accounting for padding and borders."""
        usable_width =self .bounds .width -self ._get_total_padding_horizontal ()


        safety_margin =max (MIN_SAFETY_MARGIN ,math .ceil (usable_width *SAFETY_MARGIN_RATIO ))
        usable_width -=safety_margin 


        return max (MIN_USABLE_WIDTH ,usable_width )

    def _calculate_visible_lines (self )->int :
        """Calculate how many lines fit in the component."""
        _ ,_ ,_ ,content_height =self ._get_content_area_bounds ()
        line_height =self ._get_line_height ()
        return max (1 ,content_height //line_height )

    def _cursor_to_display_position (self ,row :int ,col :int )->Tuple [int ,int ]:
        """Convert logical cursor position to display position considering word wrap."""
        self ._update_word_wrap ()



        row =max (0 ,min (row ,len (self ._text_lines )-1 ))if self ._text_lines else 0 
        if row <len (self ._text_lines ):
            col =max (0 ,min (col ,len (self ._text_lines [row ])))

        display_row =0 
        for line_idx in range (min (row ,len (self .wrapped_lines ))):
            display_row +=len (self .wrapped_lines [line_idx ])


        if row <len (self .wrapped_lines ):
            segments =self .wrapped_lines [row ]
            if not segments :
                return display_row ,0 


            original_line =self ._text_lines [row ]
            char_count =0 

            for seg_idx ,segment in enumerate (segments ):

                segment_start =char_count 
                segment_end =char_count +len (segment )


                if col >=segment_start and (col <=segment_end or seg_idx ==len (segments )-1 ):
                    display_col =col -segment_start 

                    display_col =max (0 ,min (display_col ,len (segment )))
                    display_row +=seg_idx 
                    return display_row ,display_col 

                char_count =segment_end 

        return display_row ,0 

    def _display_to_cursor_position (self ,display_row :int ,display_col :int )->Tuple [int ,int ]:
        """Convert display position back to logical cursor position."""
        self ._update_word_wrap ()


        display_row =max (0 ,display_row )
        display_col =max (0 ,display_col )

        current_display_row =0 
        for line_idx ,segments in enumerate (self .wrapped_lines ):
            if not segments :
                continue 

            line_display_rows =len (segments )
            if current_display_row +line_display_rows >display_row :

                segment_idx =display_row -current_display_row 
                segment_idx =max (0 ,min (segment_idx ,len (segments )-1 ))

                if segment_idx <len (segments ):

                    char_offset =0 
                    for i in range (segment_idx ):
                        char_offset +=len (segments [i ])


                    final_col =char_offset +display_col 


                    if line_idx <len (self ._text_lines ):
                        max_col =len (self ._text_lines [line_idx ])
                        final_col =min (final_col ,max_col )

                    return line_idx ,final_col 

            current_display_row +=line_display_rows 


        if self ._text_lines :
            return len (self ._text_lines )-1 ,len (self ._text_lines [-1 ])
        return 0 ,0 

    def _on_mouse_click (self ,event :UIEvent )->bool :
        """Handle mouse click with multiline support, proper wrapped text handling, and scroll support."""
        if not self .get_bounds ().contains_point (event .mouse_x ,event .mouse_y ):
            return False 


        if self .selection .active :
            return True 


        self ._update_word_wrap ()


        logical_row ,logical_col =self ._get_cursor_position_from_mouse (event .mouse_x ,event .mouse_y )


        self .cursor_row =logical_row 
        self .cursor_col =logical_col 
        self .selection .clear ()


        self ._ensure_cursor_visible ()


        if self .ui_state :
            self .ui_state .set_focus (self )

        return True 

    def _find_logical_line_from_display_line (self ,display_line :int )->Tuple [int ,int ]:
        """Find which logical line and segment index corresponds to a display line."""
        current_display_line =0 

        for logical_row ,segments in enumerate (self .wrapped_lines ):
            if not segments :
                segments =[""]

            num_segments =len (segments )


            if current_display_line +num_segments >display_line :
                segment_idx =display_line -current_display_line 
                return logical_row ,max (0 ,min (segment_idx ,num_segments -1 ))

            current_display_line +=num_segments 


        if self ._text_lines :
            return len (self ._text_lines )-1 ,0 
        return 0 ,0 

    def _find_column_from_click_x (self ,logical_row :int ,segment_idx :int ,click_x :int )->int :
        """Find the precise column position within a segment based on click X coordinate."""
        if logical_row >=len (self ._text_lines )or logical_row >=len (self .wrapped_lines ):
            return 0 

        line_text =self ._text_lines [logical_row ]
        segments =self .wrapped_lines [logical_row ]

        if not segments or segment_idx >=len (segments ):

            return len (line_text )



        char_offset =0 
        for i in range (segment_idx ):
            if i <len (segments ):
                char_offset +=len (segments [i ])


        segment_text =segments [segment_idx ]


        if not segment_text :
            return char_offset 


        segment_width ,_ =self .get_text_dimensions (segment_text )
        if click_x >=segment_width :


            if segment_idx ==len (segments )-1 :

                return len (line_text )
            else :

                return char_offset +len (segment_text )


        best_col_in_segment =0 
        best_distance =float ('inf')

        for col_in_segment in range (len (segment_text )+1 ):
            text_part =segment_text [:col_in_segment ]
            text_width ,_ =self .get_text_dimensions (text_part )
            distance =abs (text_width -click_x )

            if distance <best_distance :
                best_distance =distance 
                best_col_in_segment =col_in_segment 


        final_col =char_offset +best_col_in_segment 


        max_col =len (line_text )


        total_segment_chars =sum (len (seg )for seg in segments )
        if total_segment_chars !=max_col :



            if total_segment_chars >0 :
                proportion =(char_offset +best_col_in_segment )/total_segment_chars 
                final_col =math .ceil (proportion *max_col )
            else :
                final_col =0 

        return min (final_col ,max_col )

    def _on_text_input (self ,event :UIEvent )->bool :
        """Handle text input events."""
        if hasattr (event ,'unicode')and event .unicode :

            if self .selection .active :
                self ._delete_selection ()


            self ._insert_text (event .unicode )

            return True 
        return False 

    def _mark_dirty (self ):
        """Mark component as needing re-render and update auto-resize."""


        self ._render_dirty =True 
        self ._invalidate_wrap_cache ()


        if not self .multiline :
            self ._update_horizontal_scroll_state ()
            self ._ensure_cursor_visible_horizontal ()





        if self .ui_state and self .ui_state .target_area :
            self .ui_state .target_area .tag_redraw ()

    def _insert_text (self ,text :str ):
        """Insert text at cursor position, handling newlines."""
        self ._save_state ()


        if not self .multiline :
            text =text .replace ('\n',' ').replace ('\r',' ')

        lines =text .split ('\n')

        if len (lines )==1 :

            current_line =self ._text_lines [self .cursor_row ]
            new_line =current_line [:self .cursor_col ]+text +current_line [self .cursor_col :]
            self ._text_lines [self .cursor_row ]=new_line 

            self .cursor_col +=len (text )
        else :

            if not self .multiline :

                combined_text =' '.join (lines )
                current_line =self ._text_lines [self .cursor_row ]
                new_line =current_line [:self .cursor_col ]+combined_text +current_line [self .cursor_col :]
                self ._text_lines [self .cursor_row ]=new_line 
                self .cursor_col +=len (combined_text )
            else :

                current_line =self ._text_lines [self .cursor_row ]


                self ._text_lines [self .cursor_row ]=current_line [:self .cursor_col ]+lines [0 ]


                for i ,line in enumerate (lines [1 :-1 ],1 ):
                    self ._text_lines .insert (self .cursor_row +i ,line )


                last_line =lines [-1 ]+current_line [self .cursor_col :]
                self ._text_lines .insert (self .cursor_row +len (lines )-1 ,last_line )


                self .cursor_row +=len (lines )-1 
                self .cursor_col =len (lines [-1 ])


        self .invalidate ()


        if self .multiline :
            self ._ensure_cursor_visible ()
        else :
            self ._ensure_cursor_visible_horizontal ()


        self ._save_state_on_next_change =True 

    def _on_key_press (self ,event :UIEvent )->bool :
        """Handle key press using dispatch table. Block ALL keys when focused."""
        if not self .focused :
            return False 


        key_handled =False 


        if event .key in self ._key_handlers :
            try :
                key_handled =self ._key_handlers [event .key ](event )
            except Exception as e :
                logger .error (f"Error handling key {event.key}: {e}")
                key_handled =True 
        else :

            if self ._handle_dynamic_keys (event ):
                key_handled =True 


        if not key_handled :
            logger .debug (f"Unhandled key {event.key} consumed by text input to prevent Blender shortcuts")


        return True 

    def _handle_dynamic_keys (self ,event :UIEvent )->bool :
        """Handle keys that require dynamic pattern matching."""

        if event .key .startswith ('ALT_'):
            return True 


        if event .key .startswith ('CTRL_')and any (event .key .endswith (str (i ))for i in range (10 )):
            return True 
        elif event .key .startswith ('ALT_')and any (event .key .endswith (str (i ))for i in range (10 )):
            return True 
        elif event .key .startswith ('SHIFT_')and any (event .key .endswith (str (i ))for i in range (10 )):
            return True 


        elif event .key in ['G','R','S','E','I','P','B','L','U','H','J','K','M','Q','W','T']:
            return True 

        return False 

    def _handle_undo (self ,event :UIEvent )->bool :
        """Handle Ctrl+Z - undo."""
        logger .debug (f"Undo requested. History length: {len(self._history)}, Index: {self._history_index}")


        if len (self ._history )>0 and self ._history_index >0 :
            self ._history_index -=1 
            logger .debug (f"Undoing to index {self._history_index}")
            self ._restore_state (self ._history [self ._history_index ])
        else :
            logger .debug ("Cannot undo: no previous states available")
        return True 

    def _handle_redo (self ,event :UIEvent )->bool :
        """Handle Ctrl+Y or Ctrl+Shift+Z - redo."""
        logger .debug (f"Redo requested. History length: {len(self._history)}, Index: {self._history_index}")


        if self ._history_index <len (self ._history )-1 :
            self ._history_index +=1 
            logger .debug (f"Redoing to index {self._history_index}")
            self ._restore_state (self ._history [self ._history_index ])
        else :
            logger .debug ("Cannot redo: no newer states available")
        return True 

    def _handle_backspace (self ,event :UIEvent =None )->bool :
        """Handle backspace key."""
        self ._save_state ()

        if self .selection .active :
            self ._delete_selection ()
            self .invalidate ()
            self ._ensure_cursor_visible ()
            self ._save_state_on_next_change =True 
            return True 

        if self .cursor_col >0 :

            current_line =self ._text_lines [self .cursor_row ]
            new_line =current_line [:self .cursor_col -1 ]+current_line [self .cursor_col :]
            self ._text_lines [self .cursor_row ]=new_line 
            self .cursor_col -=1 
        elif self .cursor_row >0 :

            current_line =self ._text_lines .pop (self .cursor_row )
            self .cursor_row -=1 
            self .cursor_col =len (self ._text_lines [self .cursor_row ])
            self ._text_lines [self .cursor_row ]+=current_line 

        self .invalidate ()
        self ._ensure_cursor_visible ()
        self ._save_state_on_next_change =True 
        return True 

    def _handle_delete (self ,event :UIEvent =None )->bool :
        """Handle delete key."""
        self ._save_state ()

        if self .selection .active :
            self ._delete_selection ()
            self .invalidate ()
            self ._ensure_cursor_visible ()
            self ._save_state_on_next_change =True 
            return True 

        current_line =self ._text_lines [self .cursor_row ]
        if self .cursor_col <len (current_line ):

            new_line =current_line [:self .cursor_col ]+current_line [self .cursor_col +1 :]
            self ._text_lines [self .cursor_row ]=new_line 
        elif self .cursor_row <len (self ._text_lines )-1 :

            next_line =self ._text_lines .pop (self .cursor_row +1 )
            self ._text_lines [self .cursor_row ]+=next_line 

        self .invalidate ()
        self ._ensure_cursor_visible ()
        self ._save_state_on_next_change =True 
        return True 

    def _handle_arrow_key (self ,direction :str ,shift_held :bool ,ctrl_held :bool ):
        """Handle arrow key navigation with selection support and auto-scroll."""
        if not shift_held and self .selection .active :

            self .selection .clear ()
        elif shift_held and not self .selection .active :

            self .selection_anchor_row =self .cursor_row 
            self .selection_anchor_col =self .cursor_col 


        if direction =='LEFT':
            if ctrl_held :
                self ._move_cursor_word_left ()
            else :
                self ._move_cursor_left ()
        elif direction =='RIGHT':
            if ctrl_held :
                self ._move_cursor_word_right ()
            else :
                self ._move_cursor_right ()
        elif direction =='UP':
            self ._move_cursor_up ()
        elif direction =='DOWN':
            self ._move_cursor_down ()


        if shift_held :
            self .selection .set (
            self .selection_anchor_row ,self .selection_anchor_col ,
            self .cursor_row ,self .cursor_col 
            )


        if self .multiline :
            self ._ensure_cursor_visible ()
        else :
            self ._ensure_cursor_visible_horizontal ()

    def _move_cursor_left (self ):
        """Move cursor left by one character."""
        if self .cursor_col >0 :
            self .cursor_col -=1 
        elif self .cursor_row >0 :
            self .cursor_row -=1 
            self .cursor_col =len (self ._text_lines [self .cursor_row ])

    def _move_cursor_right (self ):
        """Move cursor right by one character."""
        current_line =self ._text_lines [self .cursor_row ]
        if self .cursor_col <len (current_line ):
            self .cursor_col +=1 
        elif self .cursor_row <len (self ._text_lines )-1 :
            self .cursor_row +=1 
            self .cursor_col =0 

    def _move_cursor_up (self ):
        """Move cursor up by one line."""
        if self .cursor_row >0 :
            self .cursor_row -=1 

            self .cursor_col =min (self .cursor_col ,len (self ._text_lines [self .cursor_row ]))

    def _move_cursor_down (self ):
        """Move cursor down by one line."""
        if self .cursor_row <len (self ._text_lines )-1 :
            self .cursor_row +=1 

            self .cursor_col =min (self .cursor_col ,len (self ._text_lines [self .cursor_row ]))

    def _move_cursor_word_left (self ):
        """Move cursor left by one word."""
        current_line =self ._text_lines [self .cursor_row ]


        while self .cursor_col >0 and current_line [self .cursor_col -1 ].isspace ():
            self .cursor_col -=1 


        while self .cursor_col >0 and not current_line [self .cursor_col -1 ].isspace ():
            self .cursor_col -=1 

    def _move_cursor_word_right (self ):
        """Move cursor right by one word."""
        current_line =self ._text_lines [self .cursor_row ]


        while self .cursor_col <len (current_line )and not current_line [self .cursor_col ].isspace ():
            self .cursor_col +=1 


        while self .cursor_col <len (current_line )and current_line [self .cursor_col ].isspace ():
            self .cursor_col +=1 

    def _handle_home_key (self ,shift_held :bool ):
        """Handle Home key - jump to beginning of line."""
        if shift_held and not self .selection .active :
            self .selection_anchor_row =self .cursor_row 
            self .selection_anchor_col =self .cursor_col 
        elif not shift_held :
            self .selection .clear ()

        self .cursor_col =0 

        if shift_held :
            self .selection .set (
            self .selection_anchor_row ,self .selection_anchor_col ,
            self .cursor_row ,self .cursor_col 
            )

    def _handle_end_key (self ,shift_held :bool ):
        """Handle End key - jump to end of line."""
        if shift_held and not self .selection .active :
            self .selection_anchor_row =self .cursor_row 
            self .selection_anchor_col =self .cursor_col 
        elif not shift_held :
            self .selection .clear ()

        self .cursor_col =len (self ._text_lines [self .cursor_row ])

        if shift_held :
            self .selection .set (
            self .selection_anchor_row ,self .selection_anchor_col ,
            self .cursor_row ,self .cursor_col 
            )

    def _handle_enter_key (self ,event :UIEvent =None )->bool :
        """Handle Shift+Enter - create new line (only in multiline mode)."""
        if not self .multiline :

            return self ._handle_submit (event )

        self ._save_state ()

        if self .selection .active :
            self ._delete_selection ()


        current_line =self ._text_lines [self .cursor_row ]
        new_line =current_line [self .cursor_col :]
        self ._text_lines [self .cursor_row ]=current_line [:self .cursor_col ]


        self .cursor_row +=1 
        self .cursor_col =0 
        self ._text_lines .insert (self .cursor_row ,new_line )

        self .invalidate ()
        self ._ensure_cursor_visible ()
        self ._save_state_on_next_change =True 
        return True 

    def _handle_submit (self ,event :UIEvent =None )->bool :
        """Handle Enter - submit text like send button."""
        text =self .text .strip ()
        if text and self .on_submit :

            self .on_submit ()
        elif not text :

            logger .debug ("Enter pressed but no text to send")
        return True 

    def _handle_select_all (self ,event :UIEvent =None )->bool :
        """Handle Ctrl+A - select all text."""
        if self ._text_lines :
            self .selection .set (0 ,0 ,len (self ._text_lines )-1 ,len (self ._text_lines [-1 ]))
        return True 

    def _handle_copy (self ,event :UIEvent =None )->bool :
        """Handle Ctrl+C - copy to clipboard."""
        text_to_copy =self ._get_selected_text ()if self .selection .active else self .text 
        self ._copy_to_clipboard (text_to_copy )
        return True 

    def _handle_paste (self ,event :UIEvent =None )->bool :
        """Handle Ctrl+V - paste from clipboard."""
        try :
            import bpy 
            clipboard_text =bpy .context .window_manager .clipboard 
            if clipboard_text :
                self ._save_state ()
                if self .selection .active :
                    self ._delete_selection ()
                self ._insert_text (clipboard_text )

        except Exception as e :
            logger .error (f"Failed to paste from clipboard: {e}")
        return True 

    def _handle_cut (self ,event :UIEvent =None )->bool :
        """Handle Ctrl+X - cut to clipboard."""
        if self .selection .active :
            self ._save_state ()
            text_to_cut =self ._get_selected_text ()
            self ._copy_to_clipboard (text_to_cut )
            self ._delete_selection ()
            self ._ensure_cursor_visible ()
            self ._save_state_on_next_change =True 
        return True 

    def _get_selected_text (self )->str :
        """Get the currently selected text."""
        if not self .selection .active :
            return ""

        if self .selection .start_row ==self .selection .end_row :

            line =self ._text_lines [self .selection .start_row ]
            return line [self .selection .start_col :self .selection .end_col ]
        else :

            lines =[]
            for row in range (self .selection .start_row ,self .selection .end_row +1 ):
                line =self ._text_lines [row ]
                if row ==self .selection .start_row :
                    lines .append (line [self .selection .start_col :])
                elif row ==self .selection .end_row :
                    lines .append (line [:self .selection .end_col ])
                else :
                    lines .append (line )
            return '\n'.join (lines )

    def _copy_to_clipboard (self ,text :str ):
        """Copy text to system clipboard."""
        try :
            import bpy 
            bpy .context .window_manager .clipboard =text 
        except Exception as e :
            logger .error (f"Failed to copy to clipboard: {e}")

    def _delete_selection (self ):
        """Delete the currently selected text."""
        if not self .selection .active :
            return 

        if self .selection .start_row ==self .selection .end_row :

            line =self ._text_lines [self .selection .start_row ]
            new_line =line [:self .selection .start_col ]+line [self .selection .end_col :]
            self ._text_lines [self .selection .start_row ]=new_line 
        else :

            start_line =self ._text_lines [self .selection .start_row ]
            end_line =self ._text_lines [self .selection .end_row ]


            merged_line =start_line [:self .selection .start_col ]+end_line [self .selection .end_col :]


            del self ._text_lines [self .selection .start_row :self .selection .end_row +1 ]


            self ._text_lines .insert (self .selection .start_row ,merged_line )


        self .cursor_row =self .selection .start_row 
        self .cursor_col =self .selection .start_col 
        self .selection .clear ()
        self .invalidate ()
        self ._ensure_cursor_visible ()


    def get_text (self )->str :
        """Get the current text as a single string."""
        return '\n'.join (self ._text_lines )

    def set_text (self ,text :str ):
        """Set the text content."""
        self ._text_lines =text .split ('\n')if text else [""]

        if self .cursor_row >=len (self ._text_lines ):
            self .cursor_row =len (self ._text_lines )-1 
        if self .cursor_row >=0 and self .cursor_row <len (self ._text_lines ):
            if self .cursor_col >len (self ._text_lines [self .cursor_row ]):
                self .cursor_col =len (self ._text_lines [self .cursor_row ])

        self .selection .clear ()
        self ._mark_dirty ()


        if self .auto_resize :
            self ._invalidate_wrap_cache ()
            self ._update_word_wrap ()

    def set_size (self ,width :int ,height :int ):
        """Set component size and invalidate wrap cache."""
        old_width =self .bounds .width 
        super ().set_size (width ,height )

        if old_width !=width :
            self ._render_dirty =True 
            self ._invalidate_wrap_cache ()


    def render (self ,renderer :'UIRenderer'):
        """Render the text input with proper layering, visual feedback, and scrolling support."""

        current_time =time .time ()
        if current_time -self ._last_cursor_toggle >CURSOR_BLINK_INTERVAL :
            self ._cursor_visible =not self ._cursor_visible 
            self ._last_cursor_toggle =current_time 


        content_x ,content_y ,content_width ,content_height =self ._get_content_area_bounds ()


        self ._update_word_wrap ()


        if not self .multiline :
            self ._update_horizontal_scroll_state ()


        bg_color =self .style .focus_background_color if self .focused else self .style .background_color 
        renderer .draw_rounded_rect (self .bounds ,bg_color ,self .corner_radius )


        if self .is_scrollable or self .is_horizontally_scrollable :

            if self .multiline :
                renderer .push_clip_rect (content_x ,content_y ,content_width ,content_height )
            else :
                renderer .push_clip_rect (content_x ,content_y -CoordinateSystem .scale_int (8 ),content_width ,self .bounds .height +CoordinateSystem .scale_int (16 ))


        if self .selection .active :
            self ._render_selection (renderer ,content_x ,content_y ,self ._get_line_height ())


        line_height =self ._get_line_height ()


        if self .text :

            self ._render_text_content_with_scroll (renderer ,content_x ,content_y ,content_width ,line_height )
        else :

            placeholder_color =(*self .style .text_color [:3 ],PLACEHOLDER_OPACITY )
            self ._render_placeholder_wrapped (renderer ,content_x ,content_y ,content_width ,line_height ,placeholder_color )


        if self .focused :
            self ._render_cursor_with_scroll ()


        if self .is_scrollable or self .is_horizontally_scrollable :
            renderer .pop_clip_rect ()


        border_color =self .style .focus_border_color if self .focused else self .style .border_color 
        renderer .draw_rounded_rect_outline (self .bounds ,border_color ,self .style .border_width ,self .corner_radius )


        if self .is_scrollable :
            self ._render_scroll_indicator (renderer )

        elif self .is_horizontally_scrollable and self .multiline :
            self ._render_horizontal_scroll_indicator (renderer )


        if not self .auto_resize :
            self ._render_dirty =False 

    def _render_text_content_with_scroll (self ,renderer :'UIRenderer',start_x :int ,start_y :int ,width :int ,line_height :int ):
        """Render text content with scrolling support."""
        if not self ._text_lines or (len (self ._text_lines )==1 and not self ._text_lines [0 ]):
            return 


        font_size =self .style .font_size 

        if not self .multiline :

            self ._render_single_line_text (renderer ,start_x ,start_y ,width ,line_height )
            return 


        content_x ,content_y ,content_width ,content_height =self ._get_content_area_bounds ()
        visible_height =content_height 


        first_visible_line =max (0 ,self .scroll_offset_y //line_height )
        last_visible_line =min (
        self ._get_total_display_lines ()-1 ,
        (self .scroll_offset_y +visible_height )//line_height +1 
        )




        text_start_y =content_y +content_height -line_height 


        current_display_line =0 


        for line_idx ,line_segments in enumerate (self .wrapped_lines ):
            if not line_segments or (len (line_segments )==1 and not line_segments [0 ]):

                if first_visible_line <=current_display_line <=last_visible_line :

                    pass 
                current_display_line +=1 
                continue 


            for segment_idx ,segment in enumerate (line_segments ):

                if first_visible_line <=current_display_line <=last_visible_line :


                    line_y =text_start_y -(current_display_line *line_height )+self .scroll_offset_y 


                    if (line_y >=content_y -line_height and 
                    line_y <=content_y +content_height ):
                        if segment .strip ():
                            renderer .draw_text (segment ,start_x ,line_y ,font_size ,self .style .text_color )

                current_display_line +=1 

    def _render_single_line_text (self ,renderer :'UIRenderer',start_x :int ,start_y :int ,width :int ,line_height :int ):
        """Render single line text centered vertically with horizontal scrolling."""
        if not self ._text_lines or not self ._text_lines [0 ]:
            return 

        text =self ._text_lines [0 ]
        if not text .strip ():
            return 


        text_y =self ._get_single_line_text_baseline_y ()


        if self .is_horizontally_scrollable :

            text_x =start_x -self .horizontal_scroll_offset 
            renderer .draw_text (text ,text_x ,text_y ,self .style .font_size ,self .style .text_color )
        else :

            renderer .draw_text (text ,start_x ,text_y ,self .style .font_size ,self .style .text_color )

    def _get_single_line_text_baseline_y (self )->int :
        """Get the Y coordinate for text baseline positioning in single-line mode."""


        container_center_y =self .bounds .y +(self .bounds .height //2 )


        baseline_offset =self .style .font_size *FONT_BASELINE_OFFSET_RATIO 
        return container_center_y -baseline_offset 

    def _render_horizontal_scroll_indicator (self ,renderer :'UIRenderer'):
        """Render horizontal scroll indicator at the bottom when content is horizontally scrollable."""
        if not self .is_horizontally_scrollable or self .max_horizontal_scroll_offset <=0 :
            return 


        indicator_height =MIN_INDICATOR_HEIGHT 
        indicator_y =self .bounds .y +2 


        content_width =self .bounds .width -self ._get_total_padding_horizontal ()
        text_width =content_width +self .max_horizontal_scroll_offset 


        indicator_width =max (MIN_INDICATOR_WIDTH ,int ((content_width /text_width )*content_width ))


        scroll_ratio =self .horizontal_scroll_offset /self .max_horizontal_scroll_offset if self .max_horizontal_scroll_offset >0 else 0 
        max_indicator_travel =content_width -indicator_width 
        indicator_x_offset =int (scroll_ratio *max_indicator_travel )
        indicator_x =self .bounds .x +self .style .padding +self .content_padding_left +indicator_x_offset 


        from ..types import Bounds 
        track_bounds =Bounds (
        self .bounds .x +self .style .padding +self .content_padding_left ,
        indicator_y ,
        content_width ,
        indicator_height 
        )
        track_color =(0.2 ,0.2 ,0.2 ,TRACK_OPACITY )
        renderer .draw_rect (track_bounds ,track_color )


        thumb_bounds =Bounds (
        indicator_x ,
        indicator_y ,
        indicator_width ,
        indicator_height 
        )
        thumb_color =(0.5 ,0.5 ,0.5 ,INDICATOR_OPACITY )
        renderer .draw_rect (thumb_bounds ,thumb_color )

    def _get_cursor_x_offset_in_text (self ,text :str )->int :
        """Get the X offset of the cursor within the text."""
        if self .cursor_col <=0 :
            return 0 

        text_before_cursor =text [:self .cursor_col ]
        if not text_before_cursor :
            return 0 

        return self .get_text_dimensions (text_before_cursor )[0 ]

    def _render_cursor_with_scroll (self ):
        """Render the cursor with scroll offset support."""
        if not (self ._cursor_visible and self .focused ):
            return 


        if not self .wrapped_lines or self .cursor_row >=len (self .wrapped_lines ):
            logger .warning (f"Invalid wrapped_lines state for cursor rendering, cursor_row: {self.cursor_row}")
            return 


        if self .cursor_row >=len (self ._text_lines ):
            logger .warning (f"Cursor row {self.cursor_row} out of bounds, text_lines length: {len(self._text_lines)}")
            return 

        current_line =self ._text_lines [self .cursor_row ]


        line_height =self ._get_line_height ()

        if not self .multiline :

            self ._render_single_line_cursor (current_line ,line_height )
            return 


        wrapped_segments =self .wrapped_lines [self .cursor_row ]
        if not wrapped_segments :
            wrapped_segments =[""]


        chars_processed =0 
        cursor_segment_index =0 
        cursor_x_in_segment =0 
        cursor_found =False 

        for i ,segment in enumerate (wrapped_segments ):
            segment_length =len (segment )

            if chars_processed +segment_length >=self .cursor_col :

                cursor_segment_index =i 
                cursor_x_in_segment =self .cursor_col -chars_processed 

                cursor_x_in_segment =max (0 ,min (cursor_x_in_segment ,segment_length ))
                cursor_found =True 
                break 
            chars_processed +=segment_length 


        if not cursor_found :
            cursor_segment_index =len (wrapped_segments )-1 
            if wrapped_segments and wrapped_segments [-1 ]:
                cursor_x_in_segment =len (wrapped_segments [-1 ])
            else :
                cursor_x_in_segment =0 


        cursor_x_offset =0 
        if cursor_x_in_segment >0 and cursor_segment_index <len (wrapped_segments ):
            segment_text_before_cursor =wrapped_segments [cursor_segment_index ][:cursor_x_in_segment ]
            if segment_text_before_cursor :
                cursor_x_offset =self .get_text_dimensions (segment_text_before_cursor )[0 ]


        content_x ,_ ,_ ,_ =self ._get_content_area_bounds ()
        cursor_x =content_x +cursor_x_offset 



        display_lines_before =0 
        for row in range (self .cursor_row ):
            if row <len (self .wrapped_lines ):
                display_lines_before +=len (self .wrapped_lines [row ])


        display_lines_before +=cursor_segment_index 


        _ ,content_y ,_ ,content_height =self ._get_content_area_bounds ()
        text_start_y =content_y +content_height -line_height 
        cursor_y =text_start_y -(display_lines_before *line_height )+self .scroll_offset_y 


        visible_top =content_y 
        visible_bottom =content_y +content_height 

        if cursor_y >=visible_top -line_height and cursor_y <=visible_bottom :

            cursor_height =line_height -2 
            self ._draw_cursor_line (cursor_x ,cursor_y ,cursor_height )

    def _render_single_line_cursor (self ,current_line :str ,line_height :int ):
        """Render cursor for single-line mode, centered vertically with horizontal scroll support."""

        text_before_cursor =current_line [:self .cursor_col ]
        cursor_x_offset =0 
        if text_before_cursor :
            cursor_x_offset =self .get_text_dimensions (text_before_cursor )[0 ]


        content_x ,_ ,_ ,_ =self ._get_content_area_bounds ()
        cursor_x =content_x +cursor_x_offset 
        if self .is_horizontally_scrollable :
            cursor_x -=self .horizontal_scroll_offset 




        container_center_y =self .bounds .y +(self .bounds .height //2 )
        cursor_y =container_center_y -(self .style .font_size //2 )


        cursor_height =self .style .font_size +2 
        self ._draw_cursor_line (cursor_x ,cursor_y ,cursor_height )

    def _draw_cursor_line (self ,cursor_x :int ,cursor_y :int ,cursor_height :int ):
        """Draw the cursor line at the specified position."""
        gpu .state .blend_set ('ALPHA')


        vertices =[
        (cursor_x ,cursor_y ),
        (cursor_x +1 ,cursor_y ),
        (cursor_x +1 ,cursor_y +cursor_height ),
        (cursor_x ,cursor_y +cursor_height )
        ]

        indices =[(0 ,1 ,2 ),(0 ,2 ,3 )]

        batch =batch_for_shader (
        gpu .shader .from_builtin ('UNIFORM_COLOR'),
        'TRIS',
        {"pos":vertices },
        indices =indices 
        )

        gpu .shader .from_builtin ('UNIFORM_COLOR').bind ()
        gpu .shader .from_builtin ('UNIFORM_COLOR').uniform_float ("color",(*self .style .cursor_color ,1.0 ))

        batch .draw (gpu .shader .from_builtin ('UNIFORM_COLOR'))
        gpu .state .blend_set ('NONE')

    def _render_scroll_indicator (self ,renderer :'UIRenderer'):
        """Render scroll indicator on the right side when content is scrollable."""
        if not self .is_scrollable or self .max_scroll_offset <=0 :
            return 


        indicator_width =MIN_INDICATOR_HEIGHT 
        indicator_x =self .bounds .x +self .bounds .width -indicator_width -2 


        _ ,_ ,_ ,content_height =self ._get_content_area_bounds ()
        total_content_height =content_height +self .max_scroll_offset 


        indicator_height =max (MIN_INDICATOR_WIDTH ,int ((content_height /total_content_height )*content_height ))


        scroll_ratio =self .scroll_offset_y /self .max_scroll_offset if self .max_scroll_offset >0 else 0 
        max_indicator_travel =content_height -indicator_height 
        indicator_y_offset =int (scroll_ratio *max_indicator_travel )
        _ ,content_y ,_ ,_ =self ._get_content_area_bounds ()
        indicator_y =content_y +content_height -indicator_height -indicator_y_offset 


        from ..types import Bounds 
        track_bounds =Bounds (
        indicator_x ,
        content_y ,
        indicator_width ,
        content_height 
        )
        track_color =(0.2 ,0.2 ,0.2 ,TRACK_OPACITY )
        renderer .draw_rect (track_bounds ,track_color )


        thumb_bounds =Bounds (
        indicator_x ,
        indicator_y ,
        indicator_width ,
        indicator_height 
        )
        thumb_color =(0.5 ,0.5 ,0.5 ,INDICATOR_OPACITY )
        renderer .draw_rect (thumb_bounds ,thumb_color )

    def _get_total_display_lines (self )->int :
        """Get total number of display lines (including wrapped lines)."""
        total =0 
        for segments in self .wrapped_lines :
            if segments :
                total +=len (segments )
        return max (1 ,total )

    def _ensure_cursor_visible (self ):
        """Ensure the cursor is visible by auto-scrolling if necessary."""
        if not self .is_scrollable :
            return 


        display_row ,_ =self ._cursor_to_display_position (self .cursor_row ,self .cursor_col )


        self ._scroll_to_line (display_row )

    def _scroll_to_line (self ,display_line :int ):
        """Scroll to make the specified display line visible."""
        if not self .is_scrollable :
            return 

        line_height =self ._get_line_height ()
        line_y_offset =display_line *line_height 


        _ ,_ ,_ ,visible_height =self ._get_content_area_bounds ()


        if line_y_offset <self .scroll_offset_y :
            self .scroll_offset_y =line_y_offset 

        elif line_y_offset +line_height >self .scroll_offset_y +visible_height :
            self .scroll_offset_y =line_y_offset +line_height -visible_height 


        self .scroll_offset_y =max (0 ,min (self .scroll_offset_y ,self .max_scroll_offset ))

    def _on_mouse_wheel (self ,event :UIEvent )->bool :
        """Handle mouse wheel scrolling when content is scrollable."""
        if not self .is_scrollable :
            return False 


        if not self .get_bounds ().contains_point (event .mouse_x ,event .mouse_y ):
            return False 


        scroll_delta =0 
        if 'wheel_direction'in event .data :

            scroll_delta =SCROLL_SENSITIVITY if event .data ['wheel_direction']=='DOWN'else -SCROLL_SENSITIVITY 
        elif hasattr (event ,'wheel_delta'):

            scroll_delta =-event .wheel_delta *SCROLL_SENSITIVITY 

        if scroll_delta !=0 :
            self ._scroll_by (scroll_delta )
            return True 

        return False 

    def _scroll_by (self ,delta :int ):
        """Scroll content by the specified pixel delta."""
        if not self .is_scrollable :
            return 

        old_offset =self .scroll_offset_y 
        self .scroll_offset_y =max (0 ,min (self .scroll_offset_y +delta ,self .max_scroll_offset ))


        if self .scroll_offset_y !=old_offset :
            self ._render_dirty =True 

    def _on_mouse_press (self ,event :UIEvent )->bool :
        """Handle mouse press to start text selection."""
        if not self .get_bounds ().contains_point (event .mouse_x ,event .mouse_y ):
            return False 


        self ._update_word_wrap ()


        logical_row ,logical_col =self ._get_cursor_position_from_mouse (event .mouse_x ,event .mouse_y )


        self .cursor_row =logical_row 
        self .cursor_col =logical_col 


        self ._selecting =True 
        self ._selection_start_row =logical_row 
        self ._selection_start_col =logical_col 
        self ._has_dragged =False 
        self ._mouse_press_pos =(event .mouse_x ,event .mouse_y )
        self .selection .clear ()


        if self .ui_state :
            self .ui_state .set_focus (self )

        return True 

    def _on_mouse_drag (self ,event :UIEvent )->bool :
        """Handle mouse drag to extend text selection with auto-scrolling."""
        if not self ._selecting :
            return False 


        if self ._mouse_press_pos :
            dx =abs (event .mouse_x -self ._mouse_press_pos [0 ])
            dy =abs (event .mouse_y -self ._mouse_press_pos [1 ])

            if dx >3 or dy >3 :
                self ._has_dragged =True 


        logical_row ,logical_col =self ._get_cursor_position_from_mouse (event .mouse_x ,event .mouse_y )


        if self .is_scrollable :

            content_y =event .mouse_y -(self .bounds .y +self .style .padding )
            content_height =self .bounds .height -(2 *self .style .padding )


            if content_y <SCROLL_MARGIN :
                self ._scroll_by (SCROLL_SPEED )
            elif content_y >content_height -SCROLL_MARGIN :
                self ._scroll_by (-SCROLL_SPEED )
        elif self .is_horizontally_scrollable :

            content_x ,_ ,content_width ,_ =self ._get_content_area_bounds ()
            click_x =event .mouse_x -content_x 


            if click_x <SCROLL_MARGIN :

                self ._scroll_horizontally_by (-SCROLL_SPEED )
            elif click_x >content_width -SCROLL_MARGIN :

                self ._scroll_horizontally_by (SCROLL_SPEED )


        self .selection .set (
        self ._selection_start_row ,self ._selection_start_col ,
        logical_row ,logical_col 
        )




        return True 

    def _on_mouse_release (self ,event :UIEvent )->bool :
        """Handle mouse release to finish text selection."""
        if not self ._selecting :
            return False 


        logical_row ,logical_col =self ._get_cursor_position_from_mouse (event .mouse_x ,event .mouse_y )


        self .selection .set (
        self ._selection_start_row ,self ._selection_start_col ,
        logical_row ,logical_col 
        )


        self .cursor_row =logical_row 
        self .cursor_col =logical_col 




        if (not self ._has_dragged and 
        self ._selection_start_row ==logical_row and 
        self ._selection_start_col ==logical_col ):
            self .selection .clear ()


        self ._selecting =False 
        self ._has_dragged =False 
        self ._mouse_press_pos =None 

        return True 

    def _on_mouse_move (self ,event :UIEvent )->bool :
        """Handle mouse move events for hover detection."""



        return False 

    def _on_mouse_enter (self ,event :UIEvent )->bool :
        """Handle mouse enter events - set cursor to TEXT when entering text input."""

        self .cursor_type =CursorType .TEXT 
        return True 

    def _on_mouse_leave (self ,event :UIEvent )->bool :
        """Handle mouse leave events - reset cursor when leaving text input."""

        self .cursor_type =CursorType .DEFAULT 
        return True 

    def _get_cursor_position_from_mouse (self ,mouse_x :int ,mouse_y :int )->Tuple [int ,int ]:
        """Get cursor position from mouse coordinates with scroll support. Extracted from _on_mouse_click for reuse."""

        content_x ,content_y ,content_width ,content_height =self ._get_content_area_bounds ()

        click_x =mouse_x -content_x 
        click_y =mouse_y -content_y 



        tolerance =10 
        click_x =max (-tolerance ,min (click_x ,content_width +tolerance ))
        click_y =max (-tolerance ,min (click_y ,content_height +tolerance ))


        if not self .multiline :

            if self .is_horizontally_scrollable :
                click_x +=self .horizontal_scroll_offset 


            text =self ._text_lines [0 ]if self ._text_lines else ""
            logical_col =self ._find_column_from_click_x_single_line (text ,click_x )
            return 0 ,logical_col 


        line_height =self ._get_line_height ()



        text_start_y =content_y +content_height -line_height 



        y_offset_from_text_start =text_start_y -click_y -self .scroll_offset_y 


        display_line =max (0 ,int (y_offset_from_text_start //line_height ))


        logical_row ,segment_idx =self ._find_logical_line_from_display_line (display_line )


        if logical_row >=len (self ._text_lines ):

            if self ._text_lines :
                logical_row =len (self ._text_lines )-1 
                logical_col =len (self ._text_lines [logical_row ])
            else :
                logical_row =0 
                logical_col =0 
        else :

            logical_col =self ._find_column_from_click_x (logical_row ,segment_idx ,click_x )

        return logical_row ,logical_col 

    def _find_column_from_click_x_single_line (self ,text :str ,click_x :int )->int :
        """Find the column position in single-line text based on click X coordinate."""
        if not text :
            return 0 


        text_width ,_ =self .get_text_dimensions (text )
        if click_x >=text_width :
            return len (text )


        best_col =0 
        best_distance =float ('inf')

        for col in range (len (text )+1 ):
            text_part =text [:col ]
            text_width ,_ =self .get_text_dimensions (text_part )
            distance =abs (text_width -click_x )

            if distance <best_distance :
                best_distance =distance 
                best_col =col 

        return best_col 

    def _render_placeholder_wrapped (self ,renderer :'UIRenderer',start_x :int ,start_y :int ,width :int ,line_height :int ,placeholder_color :Tuple [float ,float ,float ,float ]):
        """Render placeholder text with consistent font sizing and proper wrapping."""
        if not self .placeholder :
            return 

        if not self .multiline :

            self ._render_single_line_placeholder (renderer ,start_x ,start_y ,placeholder_color )
            return 



        usable_width =self ._get_text_usable_width ()


        wrapped_segments =self ._wrap_line_optimized (self .placeholder ,usable_width )


        content_x ,content_y ,content_width ,content_height =self ._get_content_area_bounds ()
        text_start_y =content_y +content_height -line_height 


        for i ,segment in enumerate (wrapped_segments ):
            if segment .strip ():

                segment_y =text_start_y -(i *line_height )
                renderer .draw_text (segment ,start_x ,segment_y ,self .style .font_size ,placeholder_color )

    def _render_single_line_placeholder (self ,renderer :'UIRenderer',start_x :int ,start_y :int ,placeholder_color :Tuple [float ,float ,float ,float ]):
        """Render single-line placeholder text centered vertically."""

        placeholder_y =self ._get_single_line_text_baseline_y ()


        renderer .draw_text (self .placeholder ,start_x ,placeholder_y ,self .style .font_size ,placeholder_color )

    def set_auto_resize (self ,enabled :bool ,min_height :int =None ,max_height :int =None ):
        """Configure auto-resize behavior."""
        self .auto_resize =enabled 
        if min_height is not None :
            self .min_height =min_height 
        if max_height is not None :
            self .max_height =max_height 

        if enabled :
            self ._mark_dirty ()

    def get_content_height (self )->int :
        """Get the height required for current content."""
        self ._update_word_wrap ()


        total_display_lines =0 
        for segments in self .wrapped_lines :
            if segments :
                total_display_lines +=len (segments )


        if total_display_lines ==0 :
            total_display_lines =1 

        line_height =self ._get_line_height ()
        content_height =total_display_lines *line_height 


        total_height =content_height +self ._get_total_padding_vertical ()

        return total_height 

    def _calculate_total_text_height (self )->int :
        """Calculate the total height needed for all text content."""
        if not self ._text_lines or (len (self ._text_lines )==1 and not self ._text_lines [0 ]):
            return 0 


        self ._update_word_wrap ()


        total_display_lines =0 
        for segments in self .wrapped_lines :
            if segments :
                total_display_lines +=len (segments )


        line_height =self ._get_line_height ()
        return total_display_lines *line_height 

    def _validate_cursor_position (self ):
        """Validate and fix cursor position if it becomes invalid."""
        if not self ._text_lines :
            self ._text_lines =[""]
            self .cursor_row =0 
            self .cursor_col =0 
            return 


        cursor_changed =False 


        if self .cursor_row <0 :
            logger .warning (f"Cursor row {self.cursor_row} is negative, resetting to 0")
            self .cursor_row =0 
            cursor_changed =True 
        elif self .cursor_row >=len (self ._text_lines ):
            logger .warning (f"Cursor row {self.cursor_row} is out of bounds, clamping to {len(self._text_lines) - 1}")
            self .cursor_row =len (self ._text_lines )-1 
            cursor_changed =True 


        if self .cursor_row <len (self ._text_lines ):
            max_col =len (self ._text_lines [self .cursor_row ])
            if self .cursor_col <0 :
                logger .warning (f"Cursor col {self.cursor_col} is negative, resetting to 0")
                self .cursor_col =0 
                cursor_changed =True 
            elif self .cursor_col >max_col :
                logger .warning (f"Cursor col {self.cursor_col} is out of bounds for row {self.cursor_row}, clamping to {max_col}")
                self .cursor_col =max_col 
                cursor_changed =True 

    def _render_selection (self ,renderer :'UIRenderer',content_x :int ,content_y :int ,line_height :int ):
        """Render selection highlighting with proper visual feedback and scroll support."""
        if not self .selection .active :
            return 


        selection_color =(0.3 ,0.5 ,0.8 ,SELECTION_OPACITY )


        if not self .multiline :
            self ._render_single_line_selection (renderer ,content_x ,content_y ,line_height ,selection_color )
            return 



        if not self .wrapped_lines :
            return 


        start_display_row ,start_display_col =self ._cursor_to_display_position (
        self .selection .start_row ,self .selection .start_col 
        )
        end_display_row ,end_display_col =self ._cursor_to_display_position (
        self .selection .end_row ,self .selection .end_col 
        )


        if (start_display_row ,start_display_col )>(end_display_row ,end_display_col ):
            start_display_row ,start_display_col ,end_display_row ,end_display_col =end_display_row ,end_display_col ,start_display_row ,start_display_col 


        content_x_sel ,content_y_sel ,content_width_sel ,content_height_sel =self ._get_content_area_bounds ()
        first_visible_line =max (0 ,self .scroll_offset_y //line_height )if self .is_scrollable else 0 
        last_visible_line =(
        min (self ._get_total_display_lines ()-1 ,(self .scroll_offset_y +content_height_sel )//line_height +1 )
        if self .is_scrollable else self ._get_total_display_lines ()-1 
        )


        for display_row in range (max (start_display_row ,first_visible_line ),
        min (end_display_row +1 ,last_visible_line +1 )):

            selection_y =content_y_sel +content_height_sel -line_height -(display_row *line_height )+self .scroll_offset_y 


            if (selection_y +line_height <content_y_sel or 
            selection_y >content_y_sel +content_height_sel ):
                continue 


            line_start_col =start_display_col if display_row ==start_display_row else 0 

            if display_row ==end_display_row :
                line_end_col =end_display_col 
            else :


                logical_row ,segment_idx =self ._find_logical_line_from_display_line (display_row )
                if (logical_row <len (self .wrapped_lines )and 
                segment_idx <len (self .wrapped_lines [logical_row ])):
                    line_end_col =len (self .wrapped_lines [logical_row ][segment_idx ])
                else :
                    line_end_col =0 


            logical_row ,segment_idx =self ._find_logical_line_from_display_line (display_row )
            if (logical_row <len (self .wrapped_lines )and 
            segment_idx <len (self .wrapped_lines [logical_row ])):
                line_text =self .wrapped_lines [logical_row ][segment_idx ]
            else :
                continue 


            if line_start_col >0 :
                start_text =line_text [:line_start_col ]
                selection_start_x =content_x +self .get_text_dimensions (start_text )[0 ]
            else :
                selection_start_x =content_x 

            if line_end_col <len (line_text ):
                end_text =line_text [:line_end_col ]
                selection_end_x =content_x +self .get_text_dimensions (end_text )[0 ]
            else :
                selection_end_x =content_x +self .get_text_dimensions (line_text )[0 ]


            selection_width =max (1 ,selection_end_x -selection_start_x )
            selection_height =line_height 

            from ..types import Bounds 
            selection_bounds =Bounds (
            int (selection_start_x ),
            int (selection_y ),
            int (selection_width ),
            int (selection_height )
            )

            renderer .draw_rect (selection_bounds ,selection_color )

    def _render_single_line_selection (self ,renderer :'UIRenderer',content_x :int ,content_y :int ,line_height :int ,selection_color :tuple ):
        """Render selection highlighting for single-line mode with horizontal scroll support."""
        if not self ._text_lines :
            return 

        text =self ._text_lines [0 ]
        if not text :
            return 


        start_col =min (self .selection .start_col ,self .selection .end_col )
        end_col =max (self .selection .start_col ,self .selection .end_col )


        start_text =text [:start_col ]if start_col >0 else ""
        end_text =text [:end_col ]if end_col >0 else ""

        start_x_offset =self .get_text_dimensions (start_text )[0 ]if start_text else 0 
        end_x_offset =self .get_text_dimensions (end_text )[0 ]if end_text else 0 


        selection_start_x =content_x +start_x_offset 
        selection_end_x =content_x +end_x_offset 

        if self .is_horizontally_scrollable :
            selection_start_x -=self .horizontal_scroll_offset 
            selection_end_x -=self .horizontal_scroll_offset 




        container_center_y =self .bounds .y +(self .bounds .height //2 )
        selection_y =container_center_y -(self .style .font_size //2 )


        content_x_bounds ,_ ,content_width ,_ =self ._get_content_area_bounds ()
        if (selection_end_x >=content_x_bounds and 
        selection_start_x <=content_x_bounds +content_width ):


            visible_start_x =max (selection_start_x ,content_x_bounds )
            visible_end_x =min (selection_end_x ,content_x_bounds +content_width )

            if visible_end_x >visible_start_x :

                selection_width =visible_end_x -visible_start_x 
                selection_height =self .style .font_size +2 

                from ..types import Bounds 
                selection_bounds =Bounds (
                int (visible_start_x ),
                int (selection_y ),
                int (selection_width ),
                int (selection_height )
                )

                renderer .draw_rect (selection_bounds ,selection_color )

    def _handle_page_key (self ,direction :str ,shift_held :bool ):
        """Handle Page Up/Down keys for scrolling and cursor movement."""
        if not shift_held and self .selection .active :

            self .selection .clear ()
        elif shift_held and not self .selection .active :

            self .selection_anchor_row =self .cursor_row 
            self .selection_anchor_col =self .cursor_col 


        _ ,_ ,_ ,visible_height =self ._get_content_area_bounds ()
        line_height =self ._get_line_height ()
        lines_per_page =max (1 ,visible_height //line_height )


        if direction =='UP':
            for _ in range (lines_per_page ):
                if self .cursor_row >0 :
                    self ._move_cursor_up ()
                else :
                    break 
        else :
            for _ in range (lines_per_page ):
                if self .cursor_row <len (self ._text_lines )-1 :
                    self ._move_cursor_down ()
                else :
                    break 


        if shift_held :
            self .selection .set (
            self .selection_anchor_row ,self .selection_anchor_col ,
            self .cursor_row ,self .cursor_col 
            )


        self ._ensure_cursor_visible ()

    def _handle_ctrl_home_end (self ,key :str ,shift_held :bool ):
        """Handle Ctrl+Home and Ctrl+End for document start/end navigation."""
        if not shift_held and self .selection .active :
            self .selection .clear ()
        elif shift_held and not self .selection .active :
            self .selection_anchor_row =self .cursor_row 
            self .selection_anchor_col =self .cursor_col 

        if key =='HOME':

            self .cursor_row =0 
            self .cursor_col =0 
        else :

            if self ._text_lines :
                self .cursor_row =len (self ._text_lines )-1 
                self .cursor_col =len (self ._text_lines [self .cursor_row ])
            else :
                self .cursor_row =0 
                self .cursor_col =0 


        if shift_held :
            self .selection .set (
            self .selection_anchor_row ,self .selection_anchor_col ,
            self .cursor_row ,self .cursor_col 
            )


        self ._ensure_cursor_visible ()

    def scroll_to_top (self ):
        """Scroll to the top of the content."""
        if self .is_scrollable :
            self .scroll_offset_y =0 
            self ._render_dirty =True 

    def scroll_to_bottom (self ):
        """Scroll to the bottom of the content."""
        if self .is_scrollable :
            self .scroll_offset_y =self .max_scroll_offset 
            self ._render_dirty =True 

    def scroll_to_cursor (self ):
        """Scroll to make the cursor visible."""
        self ._ensure_cursor_visible ()

    def get_scroll_info (self )->dict :
        """Get current scroll information."""
        return {
        'is_scrollable':self .is_scrollable ,
        'scroll_offset':self .scroll_offset_y ,
        'max_scroll_offset':self .max_scroll_offset ,
        'scroll_percentage':(
        (self .scroll_offset_y /self .max_scroll_offset *100 )
        if self .max_scroll_offset >0 else 0 
        )
        }

    def _on_mouse_wheel_horizontal (self ,event :UIEvent )->bool :
        """Handle horizontal mouse wheel scrolling for single-line mode."""
        if self .multiline or not self .is_horizontally_scrollable :
            return False 


        if not self .get_bounds ().contains_point (event .mouse_x ,event .mouse_y ):
            return False 


        scroll_delta =0 
        if 'wheel_direction'in event .data :

            scroll_delta =SCROLL_SENSITIVITY if event .data ['wheel_direction']=='DOWN'else -SCROLL_SENSITIVITY 
        elif hasattr (event ,'wheel_delta'):

            scroll_delta =-event .wheel_delta *SCROLL_SENSITIVITY 

        if scroll_delta !=0 :
            self ._scroll_horizontally_by (scroll_delta )
            return True 

        return False 

    def _scroll_horizontally_by (self ,delta :int ):
        """Scroll horizontally by the specified pixel delta."""
        if not self .is_horizontally_scrollable :
            return 

        old_offset =self .horizontal_scroll_offset 
        self .horizontal_scroll_offset =max (0 ,min (self .horizontal_scroll_offset +delta ,self .max_horizontal_scroll_offset ))


        if self .horizontal_scroll_offset !=old_offset :
            self ._render_dirty =True 

    def _handle_arrow_key (self ,direction :str ,shift_held :bool ,ctrl_held :bool ):
        """Handle arrow key navigation with selection support and auto-scroll."""
        if not shift_held and self .selection .active :

            self .selection .clear ()
        elif shift_held and not self .selection .active :

            self .selection_anchor_row =self .cursor_row 
            self .selection_anchor_col =self .cursor_col 


        if direction =='LEFT':
            if ctrl_held :
                self ._move_cursor_word_left ()
            else :
                self ._move_cursor_left ()
        elif direction =='RIGHT':
            if ctrl_held :
                self ._move_cursor_word_right ()
            else :
                self ._move_cursor_right ()
        elif direction =='UP':
            self ._move_cursor_up ()
        elif direction =='DOWN':
            self ._move_cursor_down ()


        if shift_held :
            self .selection .set (
            self .selection_anchor_row ,self .selection_anchor_col ,
            self .cursor_row ,self .cursor_col 
            )


        if self .multiline :
            self ._ensure_cursor_visible ()
        else :
            self ._ensure_cursor_visible_horizontal ()

    def set_content_padding (self ,top :int =None ,left :int =None ,right :int =None ,bottom :int =None ):
        """Set custom content padding for UI elements."""
        if top is not None :
            self .content_padding_top =top 
        if left is not None :
            self .content_padding_left =left 
        if right is not None :
            self .content_padding_right =right 
        if bottom is not None :
            self .content_padding_bottom =bottom 


        self ._mark_dirty ()

    def get_content_padding (self )->Tuple [int ,int ,int ,int ]:
        """Get current content padding (top, left, right, bottom)."""
        return (self .content_padding_top ,self .content_padding_left ,
        self .content_padding_right ,self .content_padding_bottom )

    def _update_horizontal_scroll_state (self ):
        """Update horizontal scroll state for single-line mode."""
        if self .multiline or not self ._text_lines :
            self .is_horizontally_scrollable =False 
            self .horizontal_scroll_offset =0 
            self .max_horizontal_scroll_offset =0 
            return 

        text =self ._text_lines [0 ]
        if not text :
            self .is_horizontally_scrollable =False 
            self .horizontal_scroll_offset =0 
            self .max_horizontal_scroll_offset =0 
            return 


        text_width ,_ =self .get_text_dimensions (text )
        available_width =self ._get_text_usable_width ()

        if text_width >available_width :
            self .is_horizontally_scrollable =True 
            self .max_horizontal_scroll_offset =text_width -available_width 


            self .horizontal_scroll_offset =max (0 ,min (self .horizontal_scroll_offset ,self .max_horizontal_scroll_offset ))
        else :
            self .is_horizontally_scrollable =False 
            self .horizontal_scroll_offset =0 
            self .max_horizontal_scroll_offset =0 

    def _ensure_cursor_visible_horizontal (self ):
        """Ensure cursor is visible in single-line mode by adjusting horizontal scroll."""
        if self .multiline or not self .is_horizontally_scrollable :
            return 

        text =self ._text_lines [0 ]if self ._text_lines else ""
        cursor_x_offset =self ._get_cursor_x_offset_in_text (text )
        available_width =self ._get_text_usable_width ()


        left_margin =SCROLL_MARGIN 
        right_margin =SCROLL_MARGIN 


        cursor_screen_x =cursor_x_offset -self .horizontal_scroll_offset 

        if cursor_screen_x <left_margin :

            self .horizontal_scroll_offset =max (0 ,cursor_x_offset -left_margin )
        elif cursor_screen_x >available_width -right_margin :

            self .horizontal_scroll_offset =min (
            self .max_horizontal_scroll_offset ,
            cursor_x_offset -available_width +right_margin 
            )

    def _calculate_visible_lines (self )->int :
        """Calculate how many lines fit in the component."""
        _ ,_ ,_ ,content_height =self ._get_content_area_bounds ()
        line_height =self ._get_line_height ()
        return max (1 ,content_height //line_height )

    def _build_key_dispatch_table (self )->dict [str ,Callable [[UIEvent ],bool ]]:
        """Build the key handler dispatch table."""
        return {

        'BACK_SPACE':self ._handle_backspace ,
        'DEL':self ._handle_delete ,
        'RET':self ._handle_submit ,
        'SHIFT_RET':self ._handle_enter_key ,


        'LEFT_ARROW':lambda e :self ._handle_arrow_key ('LEFT',False ,False ),
        'RIGHT_ARROW':lambda e :self ._handle_arrow_key ('RIGHT',False ,False ),
        'UP_ARROW':lambda e :self ._handle_arrow_key ('UP',False ,False ),
        'DOWN_ARROW':lambda e :self ._handle_arrow_key ('DOWN',False ,False ),
        'HOME':lambda e :self ._handle_home_key (False ),
        'END':lambda e :self ._handle_end_key (False ),
        'PAGE_UP':lambda e :self ._handle_page_key ('UP',False ),
        'PAGE_DOWN':lambda e :self ._handle_page_key ('DOWN',False ),


        'SHIFT_LEFT_ARROW':lambda e :self ._handle_arrow_key ('LEFT',True ,False ),
        'SHIFT_RIGHT_ARROW':lambda e :self ._handle_arrow_key ('RIGHT',True ,False ),
        'SHIFT_UP_ARROW':lambda e :self ._handle_arrow_key ('UP',True ,False ),
        'SHIFT_DOWN_ARROW':lambda e :self ._handle_arrow_key ('DOWN',True ,False ),
        'SHIFT_HOME':lambda e :self ._handle_home_key (True ),
        'SHIFT_END':lambda e :self ._handle_end_key (True ),
        'SHIFT_PAGE_UP':lambda e :self ._handle_page_key ('UP',True ),
        'SHIFT_PAGE_DOWN':lambda e :self ._handle_page_key ('DOWN',True ),


        'CTRL_LEFT_ARROW':lambda e :self ._handle_arrow_key ('LEFT',False ,True ),
        'CTRL_RIGHT_ARROW':lambda e :self ._handle_arrow_key ('RIGHT',False ,True ),
        'CTRL_HOME':lambda e :self ._handle_ctrl_home_end ('HOME',False ),
        'CTRL_END':lambda e :self ._handle_ctrl_home_end ('END',False ),
        'CTRL_SHIFT_HOME':lambda e :self ._handle_ctrl_home_end ('HOME',True ),
        'CTRL_SHIFT_END':lambda e :self ._handle_ctrl_home_end ('END',True ),
        'CTRL_SHIFT_LEFT_ARROW':lambda e :self ._handle_arrow_key ('LEFT',True ,True ),
        'CTRL_SHIFT_RIGHT_ARROW':lambda e :self ._handle_arrow_key ('RIGHT',True ,True ),


        'CTRL_A':self ._handle_select_all ,
        'CTRL_C':self ._handle_copy ,
        'CTRL_V':self ._handle_paste ,
        'CTRL_X':self ._handle_cut ,


        'CTRL_Z':self ._handle_undo ,
        'CTRL_Y':self ._handle_redo ,
        'CTRL_SHIFT_Z':self ._handle_redo ,


        'ESC':self ._handle_escape ,


        'TAB':self ._block_key ,
        'SHIFT_TAB':self ._block_key ,
        'CTRL_S':self ._block_key ,
        'CTRL_O':self ._block_key ,
        'CTRL_N':self ._block_key ,
        'CTRL_UP_ARROW':self ._block_key ,
        'CTRL_DOWN_ARROW':self ._block_key ,
        'F1':self ._block_key ,'F2':self ._block_key ,'F3':self ._block_key ,
        'F4':self ._block_key ,'F5':self ._block_key ,'F6':self ._block_key ,
        'F7':self ._block_key ,'F8':self ._block_key ,'F9':self ._block_key ,
        'F10':self ._block_key ,'F11':self ._block_key ,'F12':self ._block_key ,
        }

    def _block_key (self ,event :UIEvent )->bool :
        """Block a key from being processed."""
        logger .debug (f"Key {event.key} blocked in text input")
        return True 

    def get_text_dimensions (self ,text :str ,font_size :int =None )->Tuple [int ,int ]:
        """Unified method for getting text dimensions with caching and proper font setup."""
        if font_size is None :
            font_size =self .style .font_size 

        cache_key =(text ,font_size )
        if cache_key not in self ._dimension_cache :

            try :
                blf .size (0 ,font_size )
            except Exception as e :
                logger .warning (f"Failed to set font size: {e}")
                blf .size (0 ,font_size )


            self ._dimension_cache [cache_key ]=blf .dimensions (0 ,text )

        return self ._dimension_cache [cache_key ]

    def invalidate (self ):
        """Mark component as needing re-render and update auto-resize."""
        self ._render_dirty =True 
        self ._invalidate_wrap_cache ()


        if not self .multiline :
            self ._update_horizontal_scroll_state ()
            self ._ensure_cursor_visible_horizontal ()


        if self .ui_state and self .ui_state .target_area :
            self .ui_state .target_area .tag_redraw ()

    @property 
    def text_lines (self )->List [str ]:
        """Get the text lines."""
        return self ._text_lines 

    @text_lines .setter 
    def text_lines (self ,value :List [str ]):
        """Set the text lines and trigger change events."""
        if self ._text_lines !=value :
            self ._text_lines =value 
            self ._on_text_changed ()

    @property 
    def text (self )->str :
        """Get the current text as a single string."""
        return '\n'.join (self ._text_lines )

    @text .setter 
    def text (self ,value :str ):
        """Set the text content."""
        new_lines =value .split ('\n')if value else [""]
        if self ._text_lines !=new_lines :
            self ._save_state ()
            self ._text_lines =new_lines 

            if self .cursor_row >=len (self ._text_lines ):
                self .cursor_row =len (self ._text_lines )-1 
            if self .cursor_row >=0 and self .cursor_row <len (self ._text_lines ):
                if self .cursor_col >len (self ._text_lines [self .cursor_row ]):
                    self .cursor_col =len (self ._text_lines [self .cursor_row ])

            self .selection .clear ()
            self ._on_text_changed ()

    def _on_text_changed (self ):
        """Handle text change notifications."""
        self .invalidate ()


        if self .auto_resize :
            self ._invalidate_wrap_cache ()
            self ._update_word_wrap ()


        if self .on_change :
            self .on_change (self .text )

    def _save_state (self ):
        """Save current state to history for undo/redo."""
        if not self ._save_state_on_next_change :
            logger .debug ("State saving disabled by flag")
            return 

        current_state =TextState (
        text_lines =self ._text_lines .copy (),
        cursor_row =self .cursor_row ,
        cursor_col =self .cursor_col ,
        selection =TextSelection (
        self .selection .start_row ,
        self .selection .start_col ,
        self .selection .end_row ,
        self .selection .end_col ,
        self .selection .active 
        )
        )


        while len (self ._history )>self ._history_index +1 :
            removed_state =self ._history .pop ()
            logger .debug (f"Removed future state from history")

        self ._history .append (current_state )
        self ._history_index =len (self ._history )-1 
        self ._save_state_on_next_change =False 

        logger .debug (f"State saved. History length: {len(self._history)}, Index: {self._history_index}")

    def _restore_state (self ,state :TextState ):
        """Restore a text state."""
        logger .debug ("Restoring state")
        self ._save_state_on_next_change =False 

        self ._text_lines =state .text_lines .copy ()
        self .cursor_row =state .cursor_row 
        self .cursor_col =state .cursor_col 
        self .selection =TextSelection (
        state .selection .start_row ,
        state .selection .start_col ,
        state .selection .end_row ,
        state .selection .end_col ,
        state .selection .active 
        )

        self ._on_text_changed ()
        self ._save_state_on_next_change =True 
        logger .debug ("State restored successfully")

    def _save_initial_state (self ):
        """Save the initial state to enable undo from the very first action."""
        initial_state =TextState (
        text_lines =self ._text_lines .copy (),
        cursor_row =self .cursor_row ,
        cursor_col =self .cursor_col ,
        selection =TextSelection (
        self .selection .start_row ,
        self .selection .start_col ,
        self .selection .end_row ,
        self .selection .end_col ,
        self .selection .active 
        )
        )

        self ._history .append (initial_state )
        self ._history_index =0 
        logger .debug (f"Initial state saved. History length: {len(self._history)}, Index: {self._history_index}")

    def _handle_escape (self ,event :UIEvent )->bool :
        """Handle ESC - unfocus the text input."""
        logger .debug ("ESC pressed - unfocusing text input")
        if self .ui_state :
            self .ui_state .set_focus (None )
        return True 

    def _draw_cursor (self ,renderer :'UIRenderer',content_x :int ,content_y :int ,content_width :int ,content_height :int ):
        """Draw the text cursor at the current position."""
        if not self .focused or not self .show_cursor :
            return 


        cursor_x ,cursor_y =self ._get_cursor_position ()


        padding_value =_get_numeric_value (self .style ,'padding',10 )
        text_x =content_x +padding_value +self .content_padding_left 
        text_y_bottom =content_y +padding_value +self .content_padding_bottom 


        cursor_screen_x =text_x +cursor_x 
        cursor_screen_y =text_y_bottom +cursor_y 


        cursor_height =self ._get_line_height ()
        cursor_bounds =Bounds (cursor_screen_x ,cursor_screen_y ,1 ,cursor_height )
        renderer .draw_rect (cursor_bounds ,self .style .cursor_color +(1.0 ,))

    def _get_mouse_text_position (self ,event :UIEvent )->Tuple [int ,int ]:
        """Get text position from mouse coordinates."""
        content_x ,content_y ,content_width ,content_height =self ._get_content_area_bounds ()


        padding_value =_get_numeric_value (self .style ,'padding',10 )
        relative_x =event .mouse_x -(content_x +padding_value )
        relative_y =event .mouse_y -(content_y +padding_value )


        line_height =self ._get_line_height ()
        line_index =max (0 ,min (relative_y //line_height ,len (self .lines )-1 ))


        if line_index <len (self .lines ):
            line =self .lines [line_index ]
            char_index =self ._get_char_index_at_x (line ,relative_x )
        else :
            char_index =0 

        return int (line_index ),int (char_index )

    def _calculate_scroll_position (self ,event :UIEvent )->float :
        """Calculate scroll position from mouse coordinates."""
        content_x ,content_y ,content_width ,content_height =self ._get_content_area_bounds ()


        padding_value =_get_numeric_value (self .style ,'padding',10 )
        content_y_bottom =content_y +padding_value +self .content_padding_bottom 
        content_height =self .bounds .height -(2 *padding_value )


        relative_y =event .mouse_y -content_y_bottom 
        return max (0.0 ,min (1.0 ,relative_y /content_height ))if content_height >0 else 0.0 