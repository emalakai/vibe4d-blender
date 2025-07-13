"""
Centralized Color System for Blender UI Addon
Provides a centralized way to access colors from blender_theme_colors.json

Usage:
    from .colors import Colors
    
    # Access colors easily
    bg_color = Colors.Primary
    text_color = Colors.Text
    border_color = Colors.Border
"""

import json 
import os 
import logging 
from typing import Dict ,Tuple ,Optional 
from dataclasses import dataclass 

from .unified_styles import Styles as UnifiedStyles ,ColorInfo 

logger =logging .getLogger (__name__ )


class Colors :
    """Centralized color system with easy access to themed colors."""


    @property 
    def Primary (self )->Tuple [float ,float ,float ,float ]:
        return UnifiedStyles .Primary 

    @property 
    def Panel (self )->Tuple [float ,float ,float ,float ]:
        return UnifiedStyles .Panel 

    @property 
    def Selected (self )->Tuple [float ,float ,float ,float ]:
        return UnifiedStyles .Selected 

    @property 
    def Border (self )->Tuple [float ,float ,float ,float ]:
        return UnifiedStyles .Border 

    @property 
    def Text (self )->Tuple [float ,float ,float ,float ]:
        return UnifiedStyles .Text 

    @property 
    def TextSelected (self )->Tuple [float ,float ,float ,float ]:
        return UnifiedStyles .TextSelected 

    @property 
    def TextMuted (self )->Tuple [float ,float ,float ,float ]:
        return UnifiedStyles .TextMuted 

    @property 
    def MenuBg (self )->Tuple [float ,float ,float ,float ]:
        return UnifiedStyles .MenuBg 

    @property 
    def Button (self )->Tuple [float ,float ,float ,float ]:
        return UnifiedStyles .Button 

    @property 
    def Highlight (self )->Tuple [float ,float ,float ,float ]:
        return UnifiedStyles .Highlight 

    @classmethod 
    def get_color (cls ,token :str )->Tuple [float ,float ,float ,float ]:
        """Get color by token name."""
        return UnifiedStyles .get_color (token )

    @classmethod 
    def get_color_info (cls ,token :str )->Optional [ColorInfo ]:
        """Get complete color information by token name."""
        return UnifiedStyles .get_color_info (token )

    @classmethod 
    def get_all_colors (cls )->Dict [str ,ColorInfo ]:
        """Get all color information."""
        return UnifiedStyles .get_all_colors ()

    @classmethod 
    def reload (cls ):
        """Reload colors from the JSON file."""
        UnifiedStyles ._loaded =False 
        UnifiedStyles ._colors .clear ()
        return UnifiedStyles .load_colors ()

    @classmethod 
    def to_hex (cls ,rgba :Tuple [float ,float ,float ,float ])->str :
        """Convert RGBA tuple back to hex string."""
        return UnifiedStyles .to_hex (rgba )

    @staticmethod 
    def lighten_color (rgba :Tuple [float ,float ,float ,float ],percent :float )->Tuple [float ,float ,float ,float ]:
        """Return a lightened version of the color by the given percent (0-100)."""
        return UnifiedStyles .lighten_color (rgba ,percent )



Colors =Colors ()


def get_color (token :str )->Tuple [float ,float ,float ,float ]:
    """Get color by token name."""
    return UnifiedStyles .get_color (token )


def get_color_hex (token :str )->str :
    """Get color by token name as hex string."""
    rgba =UnifiedStyles .get_color (token )
    return UnifiedStyles .to_hex (rgba )


def lighten_color (rgba :Tuple [float ,float ,float ,float ],percent :float )->Tuple [float ,float ,float ,float ]:
    """Return a lightened version of the color by the given percent (0-100)."""
    return UnifiedStyles .lighten_color (rgba ,percent )



PALETTE ={
'primary':UnifiedStyles .Primary ,
'panel':UnifiedStyles .Panel ,
'selected':UnifiedStyles .Selected ,
'border':UnifiedStyles .Border ,
'text':UnifiedStyles .Text ,
'text_selected':UnifiedStyles .TextSelected ,
'text_muted':UnifiedStyles .TextMuted ,
'menu_bg':UnifiedStyles .MenuBg ,
'button':UnifiedStyles .Button ,
'highlight':UnifiedStyles .Highlight ,
}