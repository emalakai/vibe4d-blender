"""
Enhanced Theme System for Blender UI Addon
Integrates with centralized color system and Blender's theme preferences.
"""

import bpy 
import logging 
import hashlib 
from typing import Tuple 
from .style_types import Style 
from .unified_styles import Styles as UnifiedStyles 
from .component_theming import get_themed_component_style ,invalidate_component_theme_cache 

logger =logging .getLogger (__name__ )


class ThemeManager :
    """Enhanced theme manager that integrates centralized colors with Blender theme."""

    def __init__ (self ):
        self ._cached_theme_hash =None 
        self .colors ={}
        self .sizes ={}
        self ._update_theme ()

    def _calculate_theme_hash (self )->str :
        """Calculate a hash of current theme values to detect real changes."""
        return UnifiedStyles ._calculate_theme_hash ()

    def _update_theme (self ):
        """Update theme from centralized colors and Blender preferences."""
        try :

            current_hash =self ._calculate_theme_hash ()


            if current_hash !=self ._cached_theme_hash :

                UnifiedStyles .update_theme_colors ()


                self .colors ={
                'background':UnifiedStyles .Panel ,
                'panel_bg':UnifiedStyles .Panel ,
                'menu_bg':UnifiedStyles .MenuBg ,
                'primary':UnifiedStyles .Primary ,
                'selected':UnifiedStyles .Selected ,
                'text':UnifiedStyles .Text ,
                'text_selected':UnifiedStyles .TextSelected ,
                'text_muted':UnifiedStyles .TextMuted ,
                'input_bg':UnifiedStyles .Primary ,
                'input_focus':UnifiedStyles .Selected ,
                'border':UnifiedStyles .Border ,
                }

                self .sizes ={
                'font_normal':UnifiedStyles .get_font_size (),
                'font_title':UnifiedStyles .get_font_size ("title"),
                'padding':UnifiedStyles .get_container_padding (),
                }

                self ._cached_theme_hash =current_hash 


                invalidate_component_theme_cache ()

                return True 

        except Exception as e :
            logger .warning (f"Failed to update theme: {e}")

            if not self .colors :

                UnifiedStyles .update_theme_colors ()

                self .colors ={
                'background':UnifiedStyles .Panel ,
                'panel_bg':UnifiedStyles .Panel ,
                'menu_bg':UnifiedStyles .MenuBg ,
                'primary':UnifiedStyles .Primary ,
                'selected':UnifiedStyles .Selected ,
                'text':UnifiedStyles .Text ,
                'text_selected':UnifiedStyles .TextSelected ,
                'text_muted':UnifiedStyles .TextMuted ,
                'input_bg':UnifiedStyles .Primary ,
                'input_focus':UnifiedStyles .Selected ,
                'border':UnifiedStyles .Border ,
                }
                self .sizes ={
                'font_normal':UnifiedStyles .get_font_size (),
                'font_title':UnifiedStyles .get_font_size ("title"),
                'padding':UnifiedStyles .get_container_padding (),
                }

        return False 

    def get_color (self ,name :str )->Tuple [float ,float ,float ,float ]:
        """Get a theme color."""
        return self .colors .get (name ,UnifiedStyles .Text )

    def get_size (self ,name :str )->int :
        """Get a theme size."""
        return self .sizes .get (name ,24 )

    def get_style (self ,style_type :str ="default")->Style :
        """Get a themed style using unified styles."""
        return UnifiedStyles .get_style (style_type )

    def check_for_changes (self )->bool :
        """Check if theme has changed and update if needed. Returns True if changed."""
        return self ._update_theme ()

    def update_if_changed (self )->bool :
        """Update theme only if it has actually changed. Returns True if changed."""
        return self ._update_theme ()



theme_manager =ThemeManager ()


def get_theme_color (name :str )->Tuple [float ,float ,float ,float ]:
    """Get theme color - now uses unified styles system."""
    return theme_manager .get_color (name )

def get_themed_style (style_type :str ="default")->Style :
    """Get themed style - now uses component theming system."""
    try :

        return get_themed_component_style (style_type )
    except Exception as e :
        logger .warning (f"Failed to get themed component style for {style_type}: {e}")

        return UnifiedStyles .get_style (style_type )

def rgba_to_hex (rgba_tuple :Tuple [float ,float ,float ,float ])->str :
    """Convert RGBA tuple (0-1 floats) to hex color string."""
    return UnifiedStyles .to_hex (rgba_tuple )

def print_theme_hex_colors ():
    """Print all theme colors as hex values for debugging."""
    theme_manager .check_for_changes ()

    print ("=== Unified Theme Colors (Hex Format) ===")
    for name ,color in theme_manager .colors .items ():
        hex_color =rgba_to_hex (color )
        print (f"{name}: {hex_color}")
    print ("=========================================")

def get_all_theme_colors_hex ()->dict :
    """Get all theme colors as hex strings in a dictionary."""
    theme_manager .check_for_changes ()
    return {name :rgba_to_hex (color )for name ,color in theme_manager .colors .items ()}