"""
Blender Theme Integration System
Maps design tokens to Blender's theme API for automatic color synchronization.
"""

import bpy 
import logging 
import hashlib 
from typing import Dict ,Tuple ,Optional ,Any 
from dataclasses import dataclass 

logger =logging .getLogger (__name__ )


@dataclass 
class ThemeToken :
    """Represents a design token mapped to Blender theme path."""
    token :str 
    blender_path :str 
    description :str 
    fallback_color :Tuple [float ,float ,float ,float ]


class BlenderThemeIntegration :
    """
    Comprehensive Blender theme integration system.
    Maps design tokens to Blender's theme API for automatic color synchronization.
    """


    THEME_TOKENS ={
    'bg_primary':ThemeToken (
    token ='bg_primary',
    blender_path ='user_interface.wcol_regular.inner',
    description ='Primary background color',
    fallback_color =(0.33 ,0.33 ,0.33 ,1.0 )
    ),
    'bg_panel':ThemeToken (
    token ='bg_panel',
    blender_path ='user_interface.wcol_box.inner',
    description ='Panel background color',
    fallback_color =(0.11 ,0.11 ,0.11 ,1.0 )
    ),
    'bg_selected':ThemeToken (
    token ='bg_selected',
    blender_path ='user_interface.wcol_menu.inner_sel',
    description ='Selected background color',
    fallback_color =(0.28 ,0.45 ,0.70 ,1.0 )
    ),
    'border':ThemeToken (
    token ='border',
    blender_path ='user_interface.wcol_regular.outline',
    description ='Border color',
    fallback_color =(0.24 ,0.24 ,0.24 ,1.0 )
    ),
    'text':ThemeToken (
    token ='text',
    blender_path ='user_interface.wcol_regular.text',
    description ='Primary text color',
    fallback_color =(0.90 ,0.90 ,0.90 ,1.0 )
    ),
    'text_selected':ThemeToken (
    token ='text_selected',
    blender_path ='user_interface.wcol_regular.text_sel',
    description ='Selected text color',
    fallback_color =(1.0 ,1.0 ,1.0 ,1.0 )
    ),
    'text_muted':ThemeToken (
    token ='text_muted',
    blender_path ='user_interface.wcol_menu_back.text',
    description ='Muted text color',
    fallback_color =(0.60 ,0.60 ,0.60 ,1.0 )
    ),
    'bg_menu':ThemeToken (
    token ='bg_menu',
    blender_path ='user_interface.wcol_menu.inner',
    description ='Menu background color',
    fallback_color =(0.16 ,0.16 ,0.16 ,1.0 )
    ),
    }

    def __init__ (self ):
        self ._cached_theme_hash :Optional [str ]=None 
        self ._cached_colors :Dict [str ,Tuple [float ,float ,float ,float ]]={}
        self ._update_colors ()

    def _calculate_theme_hash (self )->str :
        """Calculate a hash of current Blender theme values to detect changes."""
        try :
            theme =bpy .context .preferences .themes [0 ]


            theme_values =[]
            for token_info in self .THEME_TOKENS .values ():
                try :
                    color =self ._get_blender_color_by_path (theme ,token_info .blender_path )
                    theme_values .append (tuple (color [:3 ]))
                except Exception as e :
                    logger .warning (f"Failed to get theme color for {token_info.token}: {e}")
                    theme_values .append (token_info .fallback_color [:3 ])


            try :
                dpi =bpy .context .preferences .system .dpi 
                theme_values .append (dpi )
            except :
                theme_values .append (72 )

            theme_str =str (theme_values )
            return hashlib .md5 (theme_str .encode ()).hexdigest ()

        except Exception as e :
            logger .warning (f"Failed to calculate theme hash: {e}")
            return "fallback"

    def _get_blender_color_by_path (self ,theme :Any ,path :str )->Tuple [float ,float ,float ,float ]:
        """Get a color from Blender theme using dot notation path."""
        try :

            obj =theme 
            for part in path .split ('.'):
                obj =getattr (obj ,part )


            if hasattr (obj ,'__len__')and len (obj )>=3 :
                r ,g ,b =obj [:3 ]
                a =obj [3 ]if len (obj )>=4 else 1.0 


                if path in ['user_interface.wcol_box.inner','user_interface.wcol_regular.inner']:
                    a =1.0 

                return (float (r ),float (g ),float (b ),float (a ))
            else :
                raise ValueError (f"Invalid color object at path: {path}")

        except Exception as e :
            logger .warning (f"Failed to get color from path '{path}': {e}")
            raise 

    def _update_colors (self )->bool :
        """Update cached colors from Blender theme. Returns True if colors changed."""
        try :
            current_hash =self ._calculate_theme_hash ()


            if current_hash ==self ._cached_theme_hash :
                return False 

            theme =bpy .context .preferences .themes [0 ]
            new_colors ={}


            for token ,token_info in self .THEME_TOKENS .items ():
                try :
                    color =self ._get_blender_color_by_path (theme ,token_info .blender_path )
                    new_colors [token ]=color 
                    logger .debug (f"Theme color {token}: {color}")
                except Exception as e :
                    logger .warning (f"Failed to get theme color for {token}, using fallback: {e}")
                    new_colors [token ]=token_info .fallback_color 


            self ._cached_colors =new_colors 
            self ._cached_theme_hash =current_hash 
            return True 

        except Exception as e :
            logger .error (f"Failed to update theme colors: {e}")

            if not self ._cached_colors :
                self ._cached_colors ={
                token :token_info .fallback_color 
                for token ,token_info in self .THEME_TOKENS .items ()
                }
            return False 

    def get_color (self ,token :str )->Tuple [float ,float ,float ,float ]:
        """Get a theme color by token name."""

        self ._update_colors ()

        if token in self ._cached_colors :
            return self ._cached_colors [token ]
        elif token in self .THEME_TOKENS :
            logger .warning (f"Color token '{token}' not in cache, using fallback")
            return self .THEME_TOKENS [token ].fallback_color 
        else :
            logger .warning (f"Unknown color token '{token}', using white")
            return (1.0 ,1.0 ,1.0 ,1.0 )

    def get_all_colors (self )->Dict [str ,Tuple [float ,float ,float ,float ]]:
        """Get all theme colors as a dictionary."""
        self ._update_colors ()
        return self ._cached_colors .copy ()

    def check_for_changes (self )->bool :
        """Check if theme has changed. Returns True if changed."""
        return self ._update_colors ()

    def get_color_hex (self ,token :str )->str :
        """Get a theme color as hex string."""
        rgba =self .get_color (token )
        r ,g ,b =rgba [:3 ]
        return f"#{int(r * 255):02X}{int(g * 255):02X}{int(b * 255):02X}"

    def get_token_info (self ,token :str )->Optional [ThemeToken ]:
        """Get information about a theme token."""
        return self .THEME_TOKENS .get (token )

    def get_all_tokens (self )->Dict [str ,ThemeToken ]:
        """Get all available theme tokens."""
        return self .THEME_TOKENS .copy ()

    def print_debug_info (self ):
        """Print debug information about current theme colors."""
        self ._update_colors ()

        print ("\n=== Blender Theme Integration Debug ===")
        print (f"Theme hash: {self._cached_theme_hash}")
        print ("\nColor mapping:")

        for token ,token_info in self .THEME_TOKENS .items ():
            color =self ._cached_colors .get (token ,token_info .fallback_color )
            hex_color =self .get_color_hex (token )
            print (f"  {token:12} -> {token_info.blender_path:35} = {color} ({hex_color})")

        print ("=====================================\n")



blender_theme =BlenderThemeIntegration ()



def get_theme_color (token :str )->Tuple [float ,float ,float ,float ]:
    """Get a theme color by token name."""
    return blender_theme .get_color (token )


def get_theme_color_hex (token :str )->str :
    """Get a theme color as hex string."""
    return blender_theme .get_color_hex (token )


def check_theme_changes ()->bool :
    """Check if Blender theme has changed. Returns True if changed."""
    return blender_theme .check_for_changes ()


def get_all_theme_colors ()->Dict [str ,Tuple [float ,float ,float ,float ]]:
    """Get all theme colors as a dictionary."""
    return blender_theme .get_all_colors ()


def print_theme_debug ():
    """Print debug information about current theme colors."""
    blender_theme .print_debug_info ()