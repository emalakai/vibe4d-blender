"""
Component Theming System
Applies design tokens to all UI components automatically.
"""

import logging 
from typing import Dict ,Tuple ,Optional ,Any ,Union 
from .blender_theme_integration import get_theme_color ,get_theme_color_hex 
from .unified_styles import UnifiedStyles 
from .style_types import Style 

logger =logging .getLogger (__name__ )


class ComponentThemer :
    """
    Comprehensive component theming system that applies design tokens to all UI components.
    Every non-image element gets themed colors from Blender's theme system.
    """


    COMPONENT_THEMES ={
    'label':{
    'text_color':'text',
    'background_color':None ,
    'border_color':None ,
    },
    'button':{
    'text_color':'text',
    'background_color':'bg_primary',
    'border_color':'border',
    'hover_background_color':'bg_selected',
    'hover_text_color':'text_selected',
    'pressed_background_color':'bg_primary',
    'pressed_text_color':'text',
    },
    'text_input':{
    'text_color':'text',
    'background_color':'bg_menu',
    'border_color':'border',
    'focus_background_color':'bg_menu',
    'focus_border_color':'bg_selected',
    'focus_text_color':'text',
    'placeholder_text_color':'text_muted',
    },
    'container':{
    'background_color':'bg_panel',
    'border_color':'border',
    },
    'scrollview':{
    'background_color':'bg_panel',
    'border_color':'border',
    'scrollbar_color':'border',
    'scrollbar_hover_color':'bg_selected',
    },
    'dropdown':{
    'text_color':'text',
    'background_color':'bg_menu',
    'border_color':'border',
    'hover_background_color':'bg_selected',
    'hover_text_color':'text_selected',
    'selected_background_color':'bg_selected',
    'selected_text_color':'text_selected',
    },
    'message':{
    'text_color':'text',
    'background_color':'bg_panel',
    'border_color':'border',
    },
    'markdown_message':{
    'text_color':'text',
    'background_color':'bg_panel',
    'border_color':'border',
    'code_background_color':'bg_menu',
    'code_text_color':'text',
    'code_border_color':'border',
    },
    'header_button':{
    'text_color':'text',
    'background_color':'bg_primary',
    'border_color':'border',
    'hover_background_color':'bg_selected',
    'hover_text_color':'text_selected',
    },
    'icon_button':{
    'background_color':'bg_primary',
    'border_color':'border',
    'hover_background_color':'bg_selected',
    },
    'send_button':{
    'text_color':'text',
    'background_color':'bg_selected',
    'border_color':'bg_selected',
    'hover_background_color':'bg_selected',
    'hover_text_color':'text_selected',
    'disabled_background_color':'bg_primary',
    'disabled_text_color':'text_muted',
    },
    'back_button':{
    'text_color':'text',
    'background_color':'bg_primary',
    'border_color':'border',
    'hover_background_color':'bg_selected',
    'hover_text_color':'text_selected',
    },
    'navigator':{
    'background_color':'bg_panel',
    'border_color':'border',
    },
    }


    STATE_THEMES ={
    'auth_view':{
    'background_color':'bg_panel',
    'text_color':'text',
    'muted_text_color':'text_muted',
    'input_background_color':'bg_menu',
    'button_background_color':'bg_selected',
    'button_text_color':'text_selected',
    'border_color':'border',
    },
    'main_view':{
    'background_color':'bg_panel',
    'text_color':'text',
    'input_background_color':'bg_menu',
    'message_background_color':'bg_panel',
    'header_background_color':'bg_primary',
    'border_color':'border',
    },
    'settings_view':{
    'background_color':'bg_panel',
    'text_color':'text',
    'muted_text_color':'text_muted',
    'container_background_color':'bg_primary',
    'input_background_color':'bg_menu',
    'button_background_color':'bg_selected',
    'border_color':'border',
    },
    'history_view':{
    'background_color':'bg_panel',
    'text_color':'text',
    'item_background_color':'bg_primary',
    'item_hover_background_color':'bg_selected',
    'item_text_color':'text',
    'item_hover_text_color':'text_selected',
    'border_color':'border',
    },
    'no_connection_view':{
    'background_color':'bg_panel',
    'text_color':'text',
    'muted_text_color':'text_muted',
    'button_background_color':'bg_selected',
    'button_text_color':'text_selected',
    'border_color':'border',
    },
    }

    def __init__ (self ):
        self ._cached_component_styles :Dict [str ,Dict [str ,Any ]]={}
        self ._cached_state_styles :Dict [str ,Dict [str ,Any ]]={}
        self ._theme_hash :Optional [str ]=None 
        self ._update_cached_styles ()

    def _update_cached_styles (self ):
        """Update cached styles from current Blender theme."""
        try :

            UnifiedStyles .update_theme_colors ()


            self ._cached_component_styles ={}
            for component_type ,theme_config in self .COMPONENT_THEMES .items ():
                self ._cached_component_styles [component_type ]={}
                for style_property ,token in theme_config .items ():
                    if token :
                        self ._cached_component_styles [component_type ][style_property ]=get_theme_color (token )
                    else :

                        self ._cached_component_styles [component_type ][style_property ]=(0.0 ,0.0 ,0.0 ,0.0 )


            self ._cached_state_styles ={}
            for state_name ,theme_config in self .STATE_THEMES .items ():
                self ._cached_state_styles [state_name ]={}
                for style_property ,token in theme_config .items ():
                    self ._cached_state_styles [state_name ][style_property ]=get_theme_color (token )

            logger .debug ("Updated cached component styles from Blender theme")

        except Exception as e :
            logger .error (f"Failed to update cached component styles: {e}")

    def get_component_style (self ,component_type :str ,style_property :str )->Tuple [float ,float ,float ,float ]:
        """Get a themed color for a specific component type and style property."""
        self ._update_cached_styles ()

        component_styles =self ._cached_component_styles .get (component_type ,{})
        color =component_styles .get (style_property )

        if color is not None :
            return color 


        fallback_mapping ={
        'text_color':'text',
        'background_color':'bg_primary',
        'border_color':'border',
        'hover_background_color':'bg_selected',
        'hover_text_color':'text_selected',
        'focus_background_color':'bg_menu',
        'focus_border_color':'bg_selected',
        'focus_text_color':'text',
        'placeholder_text_color':'text_muted',
        'pressed_background_color':'bg_primary',
        'pressed_text_color':'text',
        'disabled_background_color':'bg_primary',
        'disabled_text_color':'text_muted',
        'selected_background_color':'bg_selected',
        'selected_text_color':'text_selected',
        'scrollbar_color':'border',
        'scrollbar_hover_color':'bg_selected',
        'code_background_color':'bg_menu',
        'code_text_color':'text',
        'code_border_color':'border',
        }

        token =fallback_mapping .get (style_property ,'text')
        return get_theme_color (token )

    def get_state_style (self ,state_name :str ,style_property :str )->Tuple [float ,float ,float ,float ]:
        """Get a themed color for a specific UI state and style property."""
        self ._update_cached_styles ()

        state_styles =self ._cached_state_styles .get (state_name ,{})
        color =state_styles .get (style_property )

        if color is not None :
            return color 


        return self .get_component_style ('label',style_property )

    def apply_theme_to_component (self ,component :Any ,component_type :str )->bool :
        """Apply theme to a specific component instance."""
        try :

            theme_config =self .COMPONENT_THEMES .get (component_type ,{})

            for style_property ,token in theme_config .items ():
                if token and hasattr (component ,style_property ):
                    color =get_theme_color (token )
                    setattr (component ,style_property ,color )
                    logger .debug (f"Applied {style_property} = {color} to {component_type}")


            if hasattr (component ,'invalidate'):
                try :
                    component .invalidate ()
                except AttributeError as e :

                    logger .debug (f"Skipping invalidate for {component_type} during initialization: {e}")
                except Exception as e :
                    logger .warning (f"Error calling invalidate on {component_type}: {e}")

            return True 

        except Exception as e :
            logger .error (f"Failed to apply theme to {component_type}: {e}")
            return False 

    def get_themed_style (self ,component_type :str )->Style :
        """Get a complete themed Style object for a component type."""
        style =Style ()

        try :

            theme_config =self .COMPONENT_THEMES .get (component_type ,{})

            for style_property ,token in theme_config .items ():
                if token and hasattr (style ,style_property ):
                    color =get_theme_color (token )
                    setattr (style ,style_property ,color )


            style .font_size =UnifiedStyles .get_font_size ()
            style .padding =UnifiedStyles .get_container_padding ()
            style .border_width =UnifiedStyles .get_thin_border ()

            return style 

        except Exception as e :
            logger .error (f"Failed to create themed style for {component_type}: {e}")
            return style 

    def get_all_themed_colors (self )->Dict [str ,Dict [str ,str ]]:
        """Get all themed colors as hex strings for debugging."""
        self ._update_cached_styles ()

        result ={}


        for component_type ,styles in self ._cached_component_styles .items ():
            result [component_type ]={}
            for style_property ,color in styles .items ():
                if color :
                    r ,g ,b =color [:3 ]
                    result [component_type ][style_property ]=f"#{int(r * 255):02X}{int(g * 255):02X}{int(b * 255):02X}"


        for state_name ,styles in self ._cached_state_styles .items ():
            result [f"state_{state_name}"]={}
            for style_property ,color in styles .items ():
                if color :
                    r ,g ,b =color [:3 ]
                    result [f"state_{state_name}"][style_property ]=f"#{int(r * 255):02X}{int(g * 255):02X}{int(b * 255):02X}"

        return result 

    def print_debug_info (self ):
        """Print debug information about component theming."""
        print ("\n=== Component Theming Debug ===")

        themed_colors =self .get_all_themed_colors ()

        for component_or_state ,styles in themed_colors .items ():
            print (f"\n{component_or_state}:")
            for style_property ,hex_color in styles .items ():
                print (f"  {style_property:25} = {hex_color}")

        print ("\n==============================\n")

    def invalidate_cache (self ):
        """Force cache invalidation on next access."""
        self ._cached_component_styles .clear ()
        self ._cached_state_styles .clear ()
        self ._theme_hash =None 



component_themer =ComponentThemer ()



def get_component_color (component_type :str ,style_property :str )->Tuple [float ,float ,float ,float ]:
    """Get a themed color for a component."""
    return component_themer .get_component_style (component_type ,style_property )


def get_state_color (state_name :str ,style_property :str )->Tuple [float ,float ,float ,float ]:
    """Get a themed color for a UI state."""
    return component_themer .get_state_style (state_name ,style_property )


def apply_theme_to_component (component :Any ,component_type :str )->bool :
    """Apply theme to a component instance."""
    return component_themer .apply_theme_to_component (component ,component_type )


def get_themed_component_style (component_type :str )->Style :
    """Get a complete themed Style object."""
    return component_themer .get_themed_style (component_type )


def print_component_theme_debug ():
    """Print debug information about component theming."""
    component_themer .print_debug_info ()


def invalidate_component_theme_cache ():
    """Force theme cache invalidation."""
    component_themer .invalidate_cache ()