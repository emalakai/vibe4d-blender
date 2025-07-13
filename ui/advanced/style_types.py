"""
Style types for the UI system.
Separated from types.py to avoid circular imports.
"""

from dataclasses import dataclass 
from typing import Tuple 


@dataclass 
class Style :
    """Style configuration for UI components."""
    background_color :Tuple [float ,float ,float ,float ]=(0.2 ,0.2 ,0.2 ,0.8 )
    border_color :Tuple [float ,float ,float ,float ]=(0.6 ,0.6 ,0.6 ,1.0 )
    text_color :Tuple [float ,float ,float ,float ]=(1.0 ,1.0 ,1.0 ,1.0 )
    focus_background_color :Tuple [float ,float ,float ,float ]=(0.3 ,0.3 ,0.3 ,0.9 )
    focus_border_color :Tuple [float ,float ,float ,float ]=(0.6 ,0.6 ,0.6 ,1.0 )
    pressed_background_color :Tuple [float ,float ,float ,float ]=(0.15 ,0.15 ,0.15 ,1.0 )
    pressed_border_color :Tuple [float ,float ,float ,float ]=(0.4 ,0.6 ,0.9 ,1.0 )
    cursor_color :Tuple [float ,float ,float ]=(1.0 ,1.0 ,1.0 )
    font_size :int =11 
    padding :int =10 
    border_width :int =1 