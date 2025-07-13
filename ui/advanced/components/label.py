"""
Label component for displaying text.
"""

from typing import TYPE_CHECKING ,List ,Optional ,Dict ,Callable ,Tuple 
from dataclasses import dataclass 
import blf 
import logging 

from .base import UIComponent 
from ..types import EventType ,UIEvent ,Bounds 

if TYPE_CHECKING :
    from ..renderer import UIRenderer 


logger =logging .getLogger (__name__ )
logger .setLevel (logging .INFO )

@dataclass 
class TextSegment :
    """Represents a segment of text with its own style and interactivity."""
    text :str 
    start_index :int 
    end_index :int 
    style :Optional [Dict ]=None 
    hover_style :Optional [Dict ]=None 
    clickable :bool =False 
    hoverable :bool =False 
    on_click :Optional [Callable ]=None 
    on_hover_start :Optional [Callable ]=None 
    on_hover_end :Optional [Callable ]=None 
    data :Optional [Dict ]=None 

@dataclass 
class RenderedSegment :
    """Represents a rendered text segment with position information."""
    segment :TextSegment 
    x :int 
    y :int 
    width :int 
    height :int 
    line_index :int 

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

        if test_width <=max_width -2 :
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

class Label (UIComponent ):
    """Label component for displaying text with multiline support and interactivity."""

    def __init__ (self ,text :str ="",x :int =0 ,y :int =0 ,width :int =200 ,height :int =30 ):

        super ().__init__ (x ,y ,width ,height )
        self .text =text 
        self .text_align ="center"
        self .vertical_align ="center"
        self .line_spacing =4 


        self ._wrapped_lines :List [str ]=[]
        self ._last_wrap_width =0 
        self ._last_wrap_font_size =0 


        self .text_segments :List [TextSegment ]=[]
        self .rendered_segments :List [RenderedSegment ]=[]
        self .hovered_segment :Optional [TextSegment ]=None 


        self .highlight_styles :Dict [str ,Dict ]={
        'default_hover':{
        'background_color':(0.3 ,0.5 ,0.8 ,0 ),
        'text_color':(1.0 ,1.0 ,1.0 ,1.0 )
        },
        'default_highlight':{
        'background_color':(0.8 ,0.8 ,0.2 ,0 ),
        'text_color':(0.0 ,0.0 ,0.0 ,1.0 )
        }
        }


        self .apply_themed_style ("label")


        self ._update_cursor_type ()


        self ._update_wrapped_lines ()


        self .add_event_handler (EventType .MOUSE_MOVE ,self ._handle_mouse_move )
        self .add_event_handler (EventType .MOUSE_CLICK ,self ._handle_mouse_click )
        self .add_event_handler (EventType .MOUSE_LEAVE ,self ._handle_mouse_leave )

    def set_text (self ,text :str ):
        """Set the label text and update wrapping."""
        if self .text !=text :
            self .text =text 
            self ._update_wrapped_lines ()

    def get_text (self )->str :
        """Get the label text."""
        return self .text 

    def add_text_segment (self ,start_index :int ,end_index :int ,
    style_name :str =None ,hover_style_name :str =None ,
    clickable :bool =False ,hoverable :bool =True ,
    on_click :Callable =None ,on_hover_start :Callable =None ,
    on_hover_end :Callable =None ,data :Dict =None ):
        """Add an interactive text segment."""
        if start_index >=end_index or start_index <0 or end_index >len (self .text ):
            raise ValueError ("Invalid segment indices")

        segment_text =self .text [start_index :end_index ]
        style =self .highlight_styles .get (style_name )if style_name else None 
        hover_style =self .highlight_styles .get (hover_style_name )if hover_style_name else None 

        segment =TextSegment (
        text =segment_text ,
        start_index =start_index ,
        end_index =end_index ,
        style =style ,
        hover_style =hover_style ,
        clickable =clickable ,
        hoverable =hoverable ,
        on_click =on_click ,
        on_hover_start =on_hover_start ,
        on_hover_end =on_hover_end ,
        data =data 
        )

        self .text_segments .append (segment )
        self ._update_cursor_type ()
        self ._update_wrapped_lines ()

        logger .info (f"Added interactive text segment: '{segment_text}' (clickable={clickable}, hoverable={hoverable})")

    def add_highlight_style (self ,name :str ,background_color :Tuple =None ,
    text_color :Tuple =None ):
        """Add a custom highlight style."""
        style ={}
        if background_color :
            style ['background_color']=background_color 
        if text_color :
            style ['text_color']=text_color 
        self .highlight_styles [name ]=style 

    def clear_segments (self ):
        """Clear all text segments."""
        self .text_segments .clear ()
        self .rendered_segments .clear ()
        self .hovered_segment =None 
        self ._update_cursor_type ()

    def set_text_align (self ,align :str ):
        """Set text alignment."""
        self .text_align =align 

    def set_vertical_align (self ,align :str ):
        """Set vertical alignment."""
        self .vertical_align =align 

    def set_line_spacing (self ,spacing :int ):
        """Set spacing between lines."""
        self .line_spacing =spacing 

    def set_size (self ,width :int ,height :int ):
        """Override set_size to trigger text rewrapping."""
        super ().set_size (width ,height )
        self ._update_wrapped_lines ()

    def update_layout (self ):
        """Update component layout (called when viewport changes)."""
        super ().update_layout ()
        self ._update_wrapped_lines ()

    def _update_cursor_type (self ):
        """Update cursor type based on interactive segments."""
        from ..types import CursorType 
        has_interactive =any (seg .clickable or seg .hoverable for seg in self .text_segments )
        if has_interactive :
            self .set_cursor_type (CursorType .DEFAULT )
        else :
            self .set_cursor_type (CursorType .DEFAULT )

    def _update_wrapped_lines (self ):
        """Update the wrapped lines cache when text or size changes."""
        if not self .text :
            self ._wrapped_lines =[""]
            self .rendered_segments .clear ()
            return 


        current_width =self .bounds .width 
        current_font_size =getattr (self .style ,'font_size',14 )

        if (self ._last_wrap_width !=current_width or 
        self ._last_wrap_font_size !=current_font_size or 
        not self ._wrapped_lines ):


            lines =self .text .split ('\n')
            wrapped_lines =[]

            for line in lines :
                if line .strip ():
                    wrapped =wrap_text_blf (line ,current_width ,current_font_size )
                    wrapped_lines .extend (wrapped )
                else :
                    wrapped_lines .append ("")

            self ._wrapped_lines =wrapped_lines 
            self ._last_wrap_width =current_width 
            self ._last_wrap_font_size =current_font_size 



        if self .text_segments :
            self ._update_rendered_segments ()
        elif self .rendered_segments :
            self .rendered_segments .clear ()

    def _update_rendered_segments (self ):
        """Update the positions of rendered segments based on current layout."""
        self .rendered_segments .clear ()

        if not self .text_segments or not self ._wrapped_lines :
            return 

        font_size =getattr (self .style ,'font_size',14 )
        line_height =font_size +self .line_spacing 
        content_height =self .get_content_height ()


        if self .vertical_align =="top":
            start_y =self .bounds .y +self .bounds .height -font_size 
        elif self .vertical_align =="bottom":
            start_y =self .bounds .y +content_height -font_size 
        else :
            start_y =self .bounds .y +(self .bounds .height +content_height )//2 -font_size 


        if len (self ._wrapped_lines )==1 and self ._wrapped_lines [0 ]==self .text :
            line =self ._wrapped_lines [0 ]
            line_y =start_y 


            blf .size (0 ,font_size )
            line_width =blf .dimensions (0 ,line )[0 ]

            if self .text_align =="center":
                line_x =self .bounds .x +(self .bounds .width -line_width )//2 
            elif self .text_align =="right":
                line_x =self .bounds .x +self .bounds .width -line_width 
            else :
                line_x =self .bounds .x 


            for segment in self .text_segments :

                segment_text =self .text [segment .start_index :segment .end_index ]


                prefix_text =self .text [:segment .start_index ]
                prefix_width =blf .dimensions (0 ,prefix_text )[0 ]if prefix_text else 0 
                segment_width =blf .dimensions (0 ,segment_text )[0 ]

                rendered_seg =RenderedSegment (
                segment =segment ,
                x =line_x +prefix_width ,
                y =line_y ,
                width =segment_width ,
                height =font_size ,
                line_index =0 
                )
                self .rendered_segments .append (rendered_seg )
            return 



        text_char_pos =0 

        for line_idx ,line in enumerate (self ._wrapped_lines ):
            if not line :
                text_char_pos +=1 
                continue 

            line_y =start_y -(line_idx *line_height )


            blf .size (0 ,font_size )
            line_width =blf .dimensions (0 ,line )[0 ]

            if self .text_align =="center":
                line_x =self .bounds .x +(self .bounds .width -line_width )//2 
            elif self .text_align =="right":
                line_x =self .bounds .x +self .bounds .width -line_width 
            else :
                line_x =self .bounds .x 


            line_char_start =text_char_pos 
            line_char_end =text_char_pos +len (line )

            for segment in self .text_segments :

                seg_start =max (segment .start_index ,line_char_start )
                seg_end =min (segment .end_index ,line_char_end )

                if seg_start <seg_end :

                    char_offset_in_line =seg_start -line_char_start 
                    segment_text =line [char_offset_in_line :char_offset_in_line +(seg_end -seg_start )]


                    prefix_text =line [:char_offset_in_line ]
                    prefix_width =blf .dimensions (0 ,prefix_text )[0 ]if prefix_text else 0 
                    segment_width =blf .dimensions (0 ,segment_text )[0 ]

                    rendered_seg =RenderedSegment (
                    segment =segment ,
                    x =line_x +prefix_width ,
                    y =line_y ,
                    width =segment_width ,
                    height =font_size ,
                    line_index =line_idx 
                    )
                    self .rendered_segments .append (rendered_seg )

            text_char_pos =line_char_end 

    def _handle_mouse_move (self ,event :UIEvent )->bool :
        """Handle mouse move events for hover detection."""

        hovered_segment =None 

        for rendered_seg in self .rendered_segments :
            if (rendered_seg .segment .hoverable and 
            rendered_seg .x <=event .mouse_x <=rendered_seg .x +rendered_seg .width and 
            rendered_seg .y <=event .mouse_y <=rendered_seg .y +rendered_seg .height ):
                hovered_segment =rendered_seg .segment 
                break 


        hover_state_changed =False 
        if hovered_segment !=self .hovered_segment :
            hover_state_changed =True 


            if self .hovered_segment and self .hovered_segment .on_hover_end :
                try :
                    self .hovered_segment .on_hover_end (self .hovered_segment )
                except Exception as e :
                    logger .error (f"Error in hover end handler: {e}")


            if hovered_segment and hovered_segment .on_hover_start :
                try :
                    hovered_segment .on_hover_start (hovered_segment )
                except Exception as e :
                    logger .error (f"Error in hover start handler: {e}")

            self .hovered_segment =hovered_segment 


            self ._force_immediate_redraw ()


        return hover_state_changed or (hovered_segment is not None )

    def _handle_mouse_click (self ,event :UIEvent )->bool :
        """Handle mouse click events."""
        for rendered_seg in self .rendered_segments :
            if (rendered_seg .segment .clickable and 
            rendered_seg .x <=event .mouse_x <=rendered_seg .x +rendered_seg .width and 
            rendered_seg .y <=event .mouse_y <=rendered_seg .y +rendered_seg .height ):

                if rendered_seg .segment .on_click :
                    try :
                        rendered_seg .segment .on_click (rendered_seg .segment )
                        return True 
                    except Exception as e :
                        logger .error (f"Error in click handler: {e}")

        return False 

    def _handle_mouse_leave (self ,event :UIEvent )->bool :
        """Handle mouse leave events."""
        hover_state_changed =False 

        if self .hovered_segment :
            hover_state_changed =True 

            if self .hovered_segment .on_hover_end :
                try :
                    self .hovered_segment .on_hover_end (self .hovered_segment )
                except Exception as e :
                    logger .error (f"Error in hover end handler: {e}")

            self .hovered_segment =None 


            self ._force_immediate_redraw ()


        return hover_state_changed 

    def get_wrapped_lines (self )->List [str ]:
        """Get the current wrapped lines."""
        return self ._wrapped_lines 

    def get_content_height (self )->int :
        """Calculate the total height needed for all text lines."""
        if not self ._wrapped_lines :
            return 0 

        font_size =getattr (self .style ,'font_size',14 )
        line_height =font_size +self .line_spacing 
        return len (self ._wrapped_lines )*line_height -self .line_spacing 

    def render (self ,renderer :'UIRenderer'):
        """Render the label with multiline support and highlighting."""
        if not self .text or not self ._wrapped_lines :
            return 

        font_size =getattr (self .style ,'font_size',14 )
        line_height =font_size +self .line_spacing 
        content_height =self .get_content_height ()


        if self .vertical_align =="top":
            start_y =self .bounds .y +self .bounds .height -font_size 
        elif self .vertical_align =="bottom":
            start_y =self .bounds .y +content_height -font_size 
        else :
            start_y =self .bounds .y +(self .bounds .height +content_height )//2 -font_size 


        for rendered_seg in self .rendered_segments :
            segment =rendered_seg .segment 


            style_to_use =None 
            if segment ==self .hovered_segment and segment .hoverable :

                if segment .hover_style :
                    style_to_use =segment .hover_style 
                elif segment .style :
                    style_to_use =segment .style 
                else :
                    style_to_use =self .highlight_styles .get ('default_hover')
            elif segment .style :
                style_to_use =segment .style 


            if style_to_use and 'background_color'in style_to_use :
                highlight_bounds =Bounds (
                rendered_seg .x -2 ,
                rendered_seg .y -2 ,
                rendered_seg .width +4 ,
                rendered_seg .height +4 
                )
                renderer .draw_rect (highlight_bounds ,style_to_use ['background_color'])


        text_char_pos =0 

        for i ,line in enumerate (self ._wrapped_lines ):
            if not line :
                text_char_pos +=1 
                continue 

            line_y =start_y -(i *line_height )


            if line_y <self .bounds .y -font_size or line_y >self .bounds .y +self .bounds .height :
                text_char_pos +=len (line )
                continue 


            text_width ,_ =renderer .get_text_dimensions (line ,font_size )

            if self .text_align =="center":
                line_x =self .bounds .x +(self .bounds .width -text_width )//2 
            elif self .text_align =="right":
                line_x =self .bounds .x +self .bounds .width -text_width 
            else :
                line_x =self .bounds .x 


            char_x =line_x 
            line_char_start =text_char_pos 

            for char_idx ,char in enumerate (line ):
                current_char_pos =line_char_start +char_idx 


                text_color =self .style .text_color 


                for segment in self .text_segments :
                    if segment .start_index <=current_char_pos <segment .end_index :

                        if segment ==self .hovered_segment and segment .hoverable :

                            if segment .hover_style and 'text_color'in segment .hover_style :
                                text_color =segment .hover_style ['text_color']
                            elif segment .style and 'text_color'in segment .style :
                                text_color =segment .style ['text_color']
                            else :
                                hover_style =self .highlight_styles .get ('default_hover')
                                if hover_style and 'text_color'in hover_style :
                                    text_color =hover_style ['text_color']
                        elif segment .style and 'text_color'in segment .style :
                            text_color =segment .style ['text_color']
                        break 


                renderer .draw_text (char ,char_x ,line_y ,font_size ,text_color )


                char_width ,_ =renderer .get_text_dimensions (char ,font_size )
                char_x +=char_width 

            text_char_pos +=len (line )

    def _force_immediate_redraw (self ):
        """Force an immediate redraw of the UI when hover state changes."""
        try :

            if self .ui_state and hasattr (self .ui_state ,'target_area')and self .ui_state .target_area :
                self .ui_state .target_area .tag_redraw ()

            elif hasattr (self ,'ui_state')and self .ui_state :
                import bpy 
                if hasattr (bpy .context ,'area')and bpy .context .area :
                    bpy .context .area .tag_redraw ()
        except Exception as e :

            pass 