"""
Core types and data structures for the UI system.
"""

from dataclasses import dataclass ,field 
from enum import Enum 
from typing import Dict ,Any ,Tuple 
import logging 
from .styles import FontSizes 
from .style_types import Style 

logger =logging .getLogger (__name__ )


class EventType (Enum ):
    """Event types for the UI system."""
    MOUSE_CLICK ="mouse_click"
    MOUSE_PRESS ="mouse_press"
    MOUSE_DRAG ="mouse_drag"
    MOUSE_RELEASE ="mouse_release"
    MOUSE_MOVE ="mouse_move"
    MOUSE_ENTER ="mouse_enter"
    MOUSE_LEAVE ="mouse_leave"
    MOUSE_WHEEL ="mouse_wheel"
    KEY_PRESS ="key_press"
    TEXT_INPUT ="text_input"
    FOCUS_GAINED ="focus_gained"
    FOCUS_LOST ="focus_lost"
    VALUE_CHANGED ="value_changed"


class CursorType (Enum ):
    """Cursor types for different UI element interactions."""
    DEFAULT ="DEFAULT"
    TEXT ="TEXT"
    HAND ="HAND"
    CROSSHAIR ="CROSSHAIR"
    MOVE ="MOVE_XY"
    WAIT ="WAIT"
    EYEDROPPER ="EYEDROPPER"
    SCROLL_X ="SCROLL_X"
    SCROLL_Y ="SCROLL_Y"
    ZOOM_IN ="ZOOM_IN"
    ZOOM_OUT ="ZOOM_OUT"


@dataclass 
class UIEvent :
    """Represents a UI event."""
    event_type :EventType 
    mouse_x :int =0 
    mouse_y :int =0 
    key :str =""
    unicode :str =""
    data :Dict [str ,Any ]=field (default_factory =dict )


@dataclass 
class Bounds :
    """Represents rectangular bounds in area coordinates (Y=0 at bottom)."""
    x :int 
    y :int 
    width :int 
    height :int 

    def __post_init__ (self ):
        """Validate bounds after initialization."""
        if self .width <0 :
            logger .warning (f"Bounds width is negative: {self.width}, setting to 0")
            self .width =0 
        if self .height <0 :
            logger .warning (f"Bounds height is negative: {self.height}, setting to 0")
            self .height =0 

    def contains_point (self ,x :int ,y :int )->bool :
        """Check if a point is within these bounds.
        
        Uses standard rectangle hit testing:
        - Left/Bottom edges are inclusive
        - Right/Top edges are exclusive
        
        This ensures pixel-perfect alignment with visual rendering.
        """
        result =(self .x <=x <self .x +self .width and 
        self .y <=y <self .y +self .height )
        return result 

    def center (self )->Tuple [int ,int ]:
        """Get the center point of the bounds."""
        return (self .x +self .width //2 ,self .y +self .height //2 )

    def right (self )->int :
        """Get the right edge coordinate (exclusive)."""
        return self .x +self .width 

    def top (self )->int :
        """Get the top edge coordinate (exclusive)."""
        return self .y +self .height 

    def area (self )->int :
        """Get the area of the bounds."""
        return self .width *self .height 

    def is_valid (self )->bool :
        """Check if the bounds are valid (non-negative dimensions)."""
        return self .width >=0 and self .height >=0 

    def __str__ (self )->str :
        """String representation for debugging."""
        return f"Bounds(x={self.x}, y={self.y}, w={self.width}, h={self.height}, right={self.right()}, top={self.top()})"