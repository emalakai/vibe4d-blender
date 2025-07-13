"""
ScrollView component for scrollable content.
Supports vertical and horizontal scrolling with mouse wheel and scrollbar interactions.
"""

import logging 
from typing import TYPE_CHECKING ,List ,Optional ,Tuple 
from enum import Enum 

from .base import UIComponent 
from ..types import EventType ,UIEvent ,CursorType ,Bounds 

if TYPE_CHECKING :
    from ..renderer import UIRenderer 

logger =logging .getLogger (__name__ )


class ScrollDirection (Enum ):
    """Direction of scrolling."""
    VERTICAL ="vertical"
    HORIZONTAL ="horizontal"
    BOTH ="both"


class ScrollView (UIComponent ):
    """Scrollable container component for handling large content areas."""

    def __init__ (self ,x :int =0 ,y :int =0 ,width :int =300 ,height :int =200 ,
    scroll_direction :ScrollDirection =ScrollDirection .VERTICAL ,
    show_scrollbars :bool =True ,
    scrollbar_width :int =12 ,
    reverse_y_coordinate :bool =False ):
        super ().__init__ (x ,y ,width ,height )


        self .scroll_direction =scroll_direction 
        self .show_scrollbars =show_scrollbars 
        self .scrollbar_width =scrollbar_width 
        self .reverse_y_coordinate =reverse_y_coordinate 


        self .scroll_x =0 
        self .scroll_y =0 
        self .max_scroll_x =0 
        self .max_scroll_y =0 


        self .content_bounds =Bounds (0 ,0 ,width ,height )
        self .children :List [UIComponent ]=[]


        self .vertical_scrollbar_bounds =Bounds (0 ,0 ,0 ,0 )
        self .horizontal_scrollbar_bounds =Bounds (0 ,0 ,0 ,0 )
        self .vertical_thumb_bounds =Bounds (0 ,0 ,0 ,0 )
        self .horizontal_thumb_bounds =Bounds (0 ,0 ,0 ,0 )


        self .is_dragging_vertical_thumb =False 
        self .is_dragging_horizontal_thumb =False 
        self .drag_start_y =0 
        self .drag_start_x =0 
        self .drag_start_scroll_y =0 
        self .drag_start_scroll_x =0 


        self .scroll_speed =30 
        self .smooth_scrolling =True 


        self .apply_themed_style ("scrollview")


        self .add_event_handler (EventType .MOUSE_WHEEL ,self ._on_mouse_wheel )
        self .add_event_handler (EventType .MOUSE_PRESS ,self ._on_mouse_press )
        self .add_event_handler (EventType .MOUSE_DRAG ,self ._on_mouse_drag )
        self .add_event_handler (EventType .MOUSE_RELEASE ,self ._on_mouse_release )
        self .add_event_handler (EventType .MOUSE_MOVE ,self ._on_mouse_move )

    def apply_themed_style (self ,style_type :str ="scrollview"):
        """Apply themed style using centralized colors."""
        try :
            from ..colors import Colors 
            from ..theme import get_themed_style 

            self .style =get_themed_style ("panel")
            self .style .background_color =Colors .Panel 
            self .style .border_color =Colors .Border 
            self .style .text_color =Colors .Text 

        except ImportError :

            from ..colors import Colors 
            self .style .background_color =Colors .Panel 
            self .style .border_color =Colors .Border 
            self .style .text_color =Colors .Text 

    def add_child (self ,child :UIComponent ):
        """Add a child component to the scrollview."""
        self .children .append (child )
        child .ui_state =self .ui_state 
        self ._update_content_bounds ()

    def remove_child (self ,child :UIComponent ):
        """Remove a child component from the scrollview with proper cleanup."""
        if child in self .children :

            if hasattr (child ,'cleanup'):
                try :
                    child .cleanup ()
                except Exception as e :
                    logger .debug (f"Error cleaning up child component during removal: {e}")

            self .children .remove (child )
            self ._update_content_bounds ()

    def clear_children (self ):
        """Clear all child components with proper cleanup."""

        for child in self .children :
            if hasattr (child ,'cleanup'):
                try :
                    child .cleanup ()
                except Exception as e :
                    logger .debug (f"Error cleaning up child component: {e}")

        self .children .clear ()
        self ._update_content_bounds ()

    def _update_content_bounds (self ):
        """Update content bounds based on children."""
        if not self .children :

            self .content_bounds =Bounds (0 ,0 ,self .bounds .width ,self .bounds .height )
            self .max_scroll_x =0 
            self .max_scroll_y =0 
            logger .debug (f"ScrollView no children: content_bounds={self.content_bounds}, max_scroll_y={self.max_scroll_y}")
            return 


        min_x =min (child .bounds .x for child in self .children )
        min_y =min (child .bounds .y for child in self .children )
        max_x =max (child .bounds .x +child .bounds .width for child in self .children )
        max_y =max (child .bounds .y +child .bounds .height for child in self .children )

        if self .reverse_y_coordinate :


            self .content_bounds =Bounds (
            min_x ,
            0 ,
            max_x -min_x ,
            max_y 
            )
        else :


            self .content_bounds =Bounds (
            min_x ,
            min_y ,
            max_x -min_x ,
            max_y -min_y 
            )

        logger .debug (f"ScrollView content updated: children={len(self.children)}, content_bounds={self.content_bounds}, scrollview_bounds={self.bounds}")

        self ._update_scroll_limits ()

    def _update_scroll_limits (self ):
        """Update maximum scroll values based on content size."""

        available_width =self .bounds .width 
        available_height =self .bounds .height 



        temp_max_scroll_x =max (0 ,self .content_bounds .width -available_width )
        temp_max_scroll_y =max (0 ,self .content_bounds .height -available_height )


        if self .show_scrollbars :
            if (self .scroll_direction in [ScrollDirection .VERTICAL ,ScrollDirection .BOTH ]and 
            temp_max_scroll_y >0 ):
                available_width -=self .scrollbar_width 
            if (self .scroll_direction in [ScrollDirection .HORIZONTAL ,ScrollDirection .BOTH ]and 
            temp_max_scroll_x >0 ):
                available_height -=self .scrollbar_width 


        self .max_scroll_x =max (0 ,self .content_bounds .width -available_width )
        self .max_scroll_y =max (0 ,self .content_bounds .height -available_height )

        logger .debug (f"ScrollView scroll limits: max_scroll_x={self.max_scroll_x}, max_scroll_y={self.max_scroll_y}, content_size=({self.content_bounds.width}, {self.content_bounds.height}), available_size=({available_width}, {available_height})")


        self .scroll_x =max (0 ,min (self .scroll_x ,self .max_scroll_x ))
        self .scroll_y =max (0 ,min (self .scroll_y ,self .max_scroll_y ))

        self ._update_scrollbar_bounds ()

    def _update_scrollbar_bounds (self ):
        """Update scrollbar bounds and thumb positions."""
        if not self .show_scrollbars :
            return 


        if self .scroll_direction in [ScrollDirection .VERTICAL ,ScrollDirection .BOTH ]:
            self .vertical_scrollbar_bounds =Bounds (
            self .bounds .x +self .bounds .width -self .scrollbar_width ,
            self .bounds .y ,
            self .scrollbar_width ,
            self .bounds .height -(self .scrollbar_width if self .scroll_direction ==ScrollDirection .BOTH else 0 )
            )


            if self .max_scroll_y >0 :
                thumb_height =max (20 ,int (self .vertical_scrollbar_bounds .height *
                (self .bounds .height /self .content_bounds .height )))

                if self .reverse_y_coordinate :



                    thumb_y =self .vertical_scrollbar_bounds .y +self .vertical_scrollbar_bounds .height -thumb_height -int (
                    (self .scroll_y /self .max_scroll_y )*
                    (self .vertical_scrollbar_bounds .height -thumb_height )
                    )
                else :



                    thumb_y =self .vertical_scrollbar_bounds .y +int (
                    (self .scroll_y /self .max_scroll_y )*
                    (self .vertical_scrollbar_bounds .height -thumb_height )
                    )

                self .vertical_thumb_bounds =Bounds (
                self .vertical_scrollbar_bounds .x ,
                thumb_y ,
                self .scrollbar_width ,
                thumb_height 
                )


        if self .scroll_direction in [ScrollDirection .HORIZONTAL ,ScrollDirection .BOTH ]:
            self .horizontal_scrollbar_bounds =Bounds (
            self .bounds .x ,
            self .bounds .y ,
            self .bounds .width -(self .scrollbar_width if self .scroll_direction ==ScrollDirection .BOTH else 0 ),
            self .scrollbar_width 
            )


            if self .max_scroll_x >0 :
                thumb_width =max (20 ,int (self .horizontal_scrollbar_bounds .width *
                (self .bounds .width /self .content_bounds .width )))
                thumb_x =self .horizontal_scrollbar_bounds .x +int (
                (self .scroll_x /self .max_scroll_x )*
                (self .horizontal_scrollbar_bounds .width -thumb_width )
                )

                self .horizontal_thumb_bounds =Bounds (
                thumb_x ,
                self .horizontal_scrollbar_bounds .y ,
                thumb_width ,
                self .scrollbar_width 
                )

    def _on_mouse_wheel (self ,event :UIEvent )->bool :
        """Handle mouse wheel scrolling."""
        if not self .bounds .contains_point (event .mouse_x ,event .mouse_y ):
            return False 


        wheel_delta =0 
        if 'wheel_direction'in event .data :

            wheel_delta =1 if event .data ['wheel_direction']=='DOWN'else -1 
            logger .debug (f"ScrollView wheel event: direction={event.data['wheel_direction']}, delta={wheel_delta}")
        elif 'wheel_delta'in event .data :

            wheel_delta =event .data ['wheel_delta']
            logger .debug (f"ScrollView wheel event: wheel_delta={wheel_delta}")
        else :
            logger .debug ("ScrollView wheel event: no wheel data found")
            return False 

        if self .scroll_direction in [ScrollDirection .VERTICAL ,ScrollDirection .BOTH ]:

            old_scroll_y =self .scroll_y 

            if self .reverse_y_coordinate :



                self .scroll_y =max (0 ,min (self .scroll_y +wheel_delta *self .scroll_speed ,self .max_scroll_y ))
            else :



                self .scroll_y =max (0 ,min (self .scroll_y -wheel_delta *self .scroll_speed ,self .max_scroll_y ))

            if old_scroll_y !=self .scroll_y :
                self ._update_scrollbar_bounds ()
                self .cursor_type =CursorType .SCROLL_Y 
                logger .debug (f"ScrollView vertical scroll: {old_scroll_y} -> {self.scroll_y} (reverse: {self.reverse_y_coordinate}, max: {self.max_scroll_y})")
                return True 
            else :
                logger .debug (f"ScrollView scroll unchanged: {self.scroll_y} (max: {self.max_scroll_y})")

        return False 

    def _on_mouse_press (self ,event :UIEvent )->bool :
        """Handle mouse press events."""

        if self .show_scrollbars :
            if (self .scroll_direction in [ScrollDirection .VERTICAL ,ScrollDirection .BOTH ]and 
            self .vertical_thumb_bounds .contains_point (event .mouse_x ,event .mouse_y )):
                self .is_dragging_vertical_thumb =True 
                self .drag_start_y =event .mouse_y 
                self .drag_start_scroll_y =self .scroll_y 
                self .cursor_type =CursorType .SCROLL_Y 
                return True 

            if (self .scroll_direction in [ScrollDirection .HORIZONTAL ,ScrollDirection .BOTH ]and 
            self .horizontal_thumb_bounds .contains_point (event .mouse_x ,event .mouse_y )):
                self .is_dragging_horizontal_thumb =True 
                self .drag_start_x =event .mouse_x 
                self .drag_start_scroll_x =self .scroll_x 
                self .cursor_type =CursorType .SCROLL_X 
                return True 

        return False 

    def _on_mouse_drag (self ,event :UIEvent )->bool :
        """Handle mouse drag events for scrollbar interaction."""
        if self .is_dragging_vertical_thumb :

            delta_y =event .mouse_y -self .drag_start_y 
            scroll_ratio =delta_y /(self .vertical_scrollbar_bounds .height -self .vertical_thumb_bounds .height )

            if self .reverse_y_coordinate :



                self .scroll_y =max (0 ,min (self .drag_start_scroll_y -scroll_ratio *self .max_scroll_y ,self .max_scroll_y ))
            else :



                self .scroll_y =max (0 ,min (self .drag_start_scroll_y +scroll_ratio *self .max_scroll_y ,self .max_scroll_y ))

            self ._update_scrollbar_bounds ()
            return True 

        if self .is_dragging_horizontal_thumb :

            delta_x =event .mouse_x -self .drag_start_x 
            scroll_ratio =delta_x /(self .horizontal_scrollbar_bounds .width -self .horizontal_thumb_bounds .width )
            self .scroll_x =max (0 ,min (self .drag_start_scroll_x +scroll_ratio *self .max_scroll_x ,self .max_scroll_x ))
            self ._update_scrollbar_bounds ()
            return True 

        return False 

    def _on_mouse_release (self ,event :UIEvent )->bool :
        """Handle mouse release events."""
        if self .is_dragging_vertical_thumb or self .is_dragging_horizontal_thumb :
            self .is_dragging_vertical_thumb =False 
            self .is_dragging_horizontal_thumb =False 
            self .cursor_type =CursorType .DEFAULT 
            return True 
        return False 

    def _on_mouse_move (self ,event :UIEvent )->bool :
        """Handle mouse move events for cursor updates."""
        if self .show_scrollbars :

            if (self .scroll_direction in [ScrollDirection .VERTICAL ,ScrollDirection .BOTH ]and 
            self .vertical_scrollbar_bounds .contains_point (event .mouse_x ,event .mouse_y )):
                self .cursor_type =CursorType .SCROLL_Y 
                return True 
            elif (self .scroll_direction in [ScrollDirection .HORIZONTAL ,ScrollDirection .BOTH ]and 
            self .horizontal_scrollbar_bounds .contains_point (event .mouse_x ,event .mouse_y )):
                self .cursor_type =CursorType .SCROLL_X 
                return True 
            else :
                self .cursor_type =CursorType .DEFAULT 

        return False 

    def scroll_to (self ,x :int =None ,y :int =None ):
        """Scroll to specific position."""
        if x is not None :
            self .scroll_x =max (0 ,min (x ,self .max_scroll_x ))
        if y is not None :
            self .scroll_y =max (0 ,min (y ,self .max_scroll_y ))
        self ._update_scrollbar_bounds ()

    def scroll_to_top (self ):
        """Scroll to the top of the content.
        
        In normal coordinate system (y=0 at bottom): scroll to max_scroll_y to show highest y values.
        In reversed coordinate system (y=0 at top): scroll to 0 to show lowest y values (top of content).
        """
        if self .reverse_y_coordinate :
            self .scroll_to (y =0 )
        else :
            self .scroll_to (y =self .max_scroll_y )

    def scroll_to_bottom (self ):
        """Scroll to the bottom of the content.
        
        In normal coordinate system (y=0 at bottom): scroll to 0 to show lowest y values.
        In reversed coordinate system (y=0 at top): scroll to max_scroll_y to show highest y values (bottom of content).
        """
        if self .reverse_y_coordinate :
            self .scroll_to (y =self .max_scroll_y )
        else :
            self .scroll_to (y =0 )

    def scroll_to_child (self ,child :UIComponent ):
        """Scroll to make a child component visible."""
        if child not in self .children :
            return 

        if self .reverse_y_coordinate :


            child_top_in_content =child .bounds .y 
            child_bottom_in_content =child .bounds .y +child .bounds .height 


            visible_top =self .scroll_y 
            visible_bottom =self .scroll_y +self .bounds .height 


            if child_top_in_content <visible_top :

                self .scroll_y =child_top_in_content 
            elif child_bottom_in_content >visible_bottom :

                self .scroll_y =child_bottom_in_content -self .bounds .height 
        else :


            child_left =child .bounds .x -self .scroll_x 
            child_right =child .bounds .x +child .bounds .width -self .scroll_x 
            child_top =child .bounds .y +child .bounds .height -self .scroll_y 
            child_bottom =child .bounds .y -self .scroll_y 


            if child_left <0 :
                self .scroll_x +=child_left 
            elif child_right >self .bounds .width :
                self .scroll_x +=child_right -self .bounds .width 


            if child_bottom <0 :
                self .scroll_y +=abs (child_bottom )
            elif child_top >self .bounds .height :
                self .scroll_y +=child_top -self .bounds .height 


        self .scroll_x =max (0 ,min (self .scroll_x ,self .max_scroll_x ))
        self .scroll_y =max (0 ,min (self .scroll_y ,self .max_scroll_y ))
        self ._update_scrollbar_bounds ()

    def get_visible_bounds (self )->Bounds :
        """Get the currently visible content bounds."""
        available_width =self .bounds .width 
        available_height =self .bounds .height 


        if self .show_scrollbars :
            if (self .scroll_direction in [ScrollDirection .VERTICAL ,ScrollDirection .BOTH ]and 
            self .max_scroll_y >0 ):
                available_width -=self .scrollbar_width 
            if (self .scroll_direction in [ScrollDirection .HORIZONTAL ,ScrollDirection .BOTH ]and 
            self .max_scroll_x >0 ):
                available_height -=self .scrollbar_width 

        return Bounds (
        self .bounds .x +self .scroll_x ,
        self .bounds .y +self .scroll_y ,
        available_width ,
        available_height 
        )

    def render (self ,renderer :'UIRenderer'):
        """Render the scrollview and its contents."""
        if not self .visible :
            return 


        renderer .draw_rect (self .bounds ,self .style .background_color )
        renderer .draw_rect_outline (self .bounds ,self .style .border_color ,self .style .border_width )


        content_width =self .bounds .width 
        content_height =self .bounds .height 

        if self .show_scrollbars :
            if (self .scroll_direction in [ScrollDirection .VERTICAL ,ScrollDirection .BOTH ]and 
            self .max_scroll_y >0 ):
                content_width -=self .scrollbar_width 
            if (self .scroll_direction in [ScrollDirection .HORIZONTAL ,ScrollDirection .BOTH ]and 
            self .max_scroll_x >0 ):
                content_height -=self .scrollbar_width 


        renderer .push_clip_rect (self .bounds .x ,self .bounds .y ,content_width ,content_height )

        try :

            for child in self .children :
                if child .visible :

                    screen_x =self .bounds .x +child .bounds .x -self .scroll_x 

                    if self .reverse_y_coordinate :


                        screen_y =self .bounds .y +self .bounds .height -child .bounds .y -child .bounds .height +self .scroll_y 
                    else :



                        screen_y =self .bounds .y +child .bounds .y -self .scroll_y 


                    if (screen_x +child .bounds .width >self .bounds .x and 
                    screen_x <self .bounds .x +content_width and 
                    screen_y +child .bounds .height >self .bounds .y and 
                    screen_y <self .bounds .y +content_height ):


                        original_x ,original_y =child .bounds .x ,child .bounds .y 
                        child .bounds .x =screen_x 
                        child .bounds .y =screen_y 


                        child .render (renderer )


                        child .bounds .x ,child .bounds .y =original_x ,original_y 

        finally :

            renderer .pop_clip_rect ()


        if self .show_scrollbars :
            self ._render_scrollbars (renderer )

    def _render_scrollbars (self ,renderer :'UIRenderer'):
        """Render scrollbars and thumbs using centralized colors."""
        from ..colors import Colors 

        scrollbar_color =tuple (c *0.5 for c in Colors .Border [:3 ])+(0.8 ,)
        thumb_color =tuple (c *1.2 for c in Colors .Border [:3 ])+(0.9 ,)
        thumb_hover_color =Colors .Selected 


        if (self .scroll_direction in [ScrollDirection .VERTICAL ,ScrollDirection .BOTH ]and 
        self .max_scroll_y >0 ):
            renderer .draw_rect (self .vertical_scrollbar_bounds ,scrollbar_color )


            thumb_color_current =thumb_hover_color if self .is_dragging_vertical_thumb else thumb_color 
            renderer .draw_rect (self .vertical_thumb_bounds ,thumb_color_current )


        if (self .scroll_direction in [ScrollDirection .HORIZONTAL ,ScrollDirection .BOTH ]and 
        self .max_scroll_x >0 ):
            renderer .draw_rect (self .horizontal_scrollbar_bounds ,scrollbar_color )


            thumb_color_current =thumb_hover_color if self .is_dragging_horizontal_thumb else thumb_color 
            renderer .draw_rect (self .horizontal_thumb_bounds ,thumb_color_current )

    def handle_event (self ,event :UIEvent )->bool :
        """Handle events for the scrollview and its children."""

        handled =super ().handle_event (event )
        if handled :
            return True 


        if self .bounds .contains_point (event .mouse_x ,event .mouse_y ):

            content_width =self .bounds .width 
            content_height =self .bounds .height 

            if self .show_scrollbars :
                if (self .scroll_direction in [ScrollDirection .VERTICAL ,ScrollDirection .BOTH ]and 
                self .max_scroll_y >0 ):
                    content_width -=self .scrollbar_width 
                if (self .scroll_direction in [ScrollDirection .HORIZONTAL ,ScrollDirection .BOTH ]and 
                self .max_scroll_x >0 ):
                    content_height -=self .scrollbar_width 


            if (event .mouse_x <self .bounds .x +content_width and 
            event .mouse_y <self .bounds .y +content_height ):


                adjusted_mouse_x =event .mouse_x -self .bounds .x +self .scroll_x 

                if self .reverse_y_coordinate :


                    mouse_y_from_bottom =event .mouse_y -self .bounds .y 
                    adjusted_mouse_y =self .bounds .height -mouse_y_from_bottom +self .scroll_y 
                else :



                    adjusted_mouse_y =event .mouse_y -self .bounds .y +self .scroll_y 

                adjusted_event =UIEvent (
                event .event_type ,
                adjusted_mouse_x ,
                adjusted_mouse_y ,
                event .key ,
                event .unicode ,
                event .data .copy ()
                )


                for child in reversed (self .children ):
                    if child .visible and child .bounds .contains_point (adjusted_event .mouse_x ,adjusted_event .mouse_y ):
                        if child .handle_event (adjusted_event ):
                            return True 

        return False 

    def update_layout (self ):
        """Update layout when viewport changes."""
        self ._update_scroll_limits ()


        for child in self .children :
            if hasattr (child ,'update_layout'):
                child .update_layout ()