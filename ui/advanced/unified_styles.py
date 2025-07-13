"""
Unified Styles System for Blender UI Addon
Consolidates all styling information: colors, fonts, sizes, spacing, etc.
Provides dynamic scaling based on CoordinateSystem.get_ui_scale()
"""

import json 
import os 
import logging 
import bpy 
import hashlib 
from typing import Dict ,Tuple ,Optional 
from dataclasses import dataclass 

from .coordinates import CoordinateSystem 
from .style_types import Style 
from .blender_theme_integration import get_theme_color ,check_theme_changes 

logger =logging .getLogger (__name__ )


@dataclass 
class ColorInfo :
    """Information about a color token."""
    token :str 
    hex :str 
    rgba :Tuple [float ,float ,float ,float ]
    theme_path :str 
    description :str 


class UnifiedStyles :
    """
    Unified styles system providing centralized access to all styling information.
    All size-related values are dynamically scaled based on UI scale factor.
    
    Note: UI scale changes are detected automatically by the UIManager every second
    and trigger a complete UI recreation for real-time scaling.
    """






    _theme_colors_cache :Dict [str ,Tuple [float ,float ,float ,float ]]={}
    _theme_cache_valid :bool =False 

    @classmethod 
    def _update_theme_colors (cls ):
        """Update theme colors from Blender theme integration."""
        try :

            if check_theme_changes ()or not cls ._theme_cache_valid :
                cls ._theme_colors_cache ={
                'bg_primary':get_theme_color ('bg_primary'),
                'bg_panel':get_theme_color ('bg_panel'),
                'bg_selected':get_theme_color ('bg_selected'),
                'border':get_theme_color ('border'),
                'text':get_theme_color ('text'),
                'text_selected':get_theme_color ('text_selected'),
                'text_muted':get_theme_color ('text_muted'),
                'bg_menu':get_theme_color ('bg_menu'),
                }


                bg_primary =cls ._theme_colors_cache ['bg_primary']
                cls ._theme_colors_cache ['bg_primary']=(bg_primary [0 ],bg_primary [1 ],bg_primary [2 ],1.0 )

                bg_panel =cls ._theme_colors_cache ['bg_panel']
                cls ._theme_colors_cache ['bg_panel']=(bg_panel [0 ],bg_panel [1 ],bg_panel [2 ],1.0 )


                cls .Primary =cls ._theme_colors_cache ['bg_primary']
                cls .Panel =cls ._theme_colors_cache ['bg_panel']
                cls .Selected =cls ._theme_colors_cache ['bg_selected']
                cls .Border =cls ._theme_colors_cache ['border']
                cls .Text =cls ._theme_colors_cache ['text']
                cls .TextSelected =cls ._theme_colors_cache ['text_selected']
                cls .TextMuted =cls ._theme_colors_cache ['text_muted']
                cls .MenuBg =cls ._theme_colors_cache ['bg_menu']
                cls .Button =cls .MenuBg 
                cls .Highlight =cls .Selected 

                cls ._theme_cache_valid =True 
                logger .debug ("Updated theme colors from Blender")
        except Exception as e :
            logger .warning (f"Failed to update theme colors: {e}")

            if not cls ._theme_colors_cache :
                cls ._theme_colors_cache ={
                'bg_primary':(0.33 ,0.33 ,0.33 ,1.0 ),
                'bg_panel':(0.11 ,0.11 ,0.11 ,1.0 ),
                'bg_selected':(0.28 ,0.45 ,0.70 ,1.0 ),
                'border':(0.24 ,0.24 ,0.24 ,1.0 ),
                'text':(0.90 ,0.90 ,0.90 ,1.0 ),
                'text_selected':(1.0 ,1.0 ,1.0 ,1.0 ),
                'text_muted':(0.60 ,0.60 ,0.60 ,1.0 ),
                'bg_menu':(0.16 ,0.16 ,0.16 ,1.0 ),
                }


                cls .Primary =cls ._theme_colors_cache ['bg_primary']
                cls .Panel =cls ._theme_colors_cache ['bg_panel']
                cls .Selected =cls ._theme_colors_cache ['bg_selected']
                cls .Border =cls ._theme_colors_cache ['border']
                cls .Text =cls ._theme_colors_cache ['text']
                cls .TextSelected =cls ._theme_colors_cache ['text_selected']
                cls .TextMuted =cls ._theme_colors_cache ['text_muted']
                cls .MenuBg =cls ._theme_colors_cache ['bg_menu']
                cls .Button =cls .MenuBg 
                cls .Highlight =cls .Selected 


    Primary :Tuple [float ,float ,float ,float ]=(0.33 ,0.33 ,0.33 ,1.0 )
    Panel :Tuple [float ,float ,float ,float ]=(0.11 ,0.11 ,0.11 ,1.0 )
    Selected :Tuple [float ,float ,float ,float ]=(0.28 ,0.45 ,0.70 ,1.0 )
    Border :Tuple [float ,float ,float ,float ]=(0.24 ,0.24 ,0.24 ,1.0 )
    Text :Tuple [float ,float ,float ,float ]=(0.90 ,0.90 ,0.90 ,1.0 )
    TextSelected :Tuple [float ,float ,float ,float ]=(1.0 ,1.0 ,1.0 ,1.0 )
    TextMuted :Tuple [float ,float ,float ,float ]=(0.60 ,0.60 ,0.60 ,1.0 )
    MenuBg :Tuple [float ,float ,float ,float ]=(0.16 ,0.16 ,0.16 ,1.0 )
    Button :Tuple [float ,float ,float ,float ]=(0.16 ,0.16 ,0.16 ,1.0 )
    Highlight :Tuple [float ,float ,float ,float ]=(0.28 ,0.45 ,0.70 ,1.0 )

    @classmethod 
    def update_theme_colors (cls ):
        """Public method to update theme colors from Blender."""
        cls ._update_theme_colors ()

    @classmethod 
    def get_themed_color (cls ,token :str )->Tuple [float ,float ,float ,float ]:
        """Get a themed color by token name."""
        cls ._update_theme_colors ()
        return cls ._theme_colors_cache .get (token ,(1.0 ,1.0 ,1.0 ,1.0 ))


    Transparent :Tuple [float ,float ,float ,float ]=(0.0 ,0.0 ,0.0 ,0.0 )
    DarkContainer :Tuple [float ,float ,float ,float ]=(0.15 ,0.15 ,0.15 ,1.0 )
    MutedText :Tuple [float ,float ,float ,float ]=(0.7 ,0.7 ,0.7 ,1.0 )
    DisabledText :Tuple [float ,float ,float ,float ]=(0.6 ,0.6 ,0.6 ,1.0 )
    EnabledText :Tuple [float ,float ,float ,float ]=(0.9 ,0.9 ,0.9 ,1.0 )
    WhiteText :Tuple [float ,float ,float ,float ]=(1.0 ,1.0 ,1.0 ,1.0 )
    Link :Tuple [float ,float ,float ,float ]=(0.4 ,0.7 ,1.0 ,1.0 )
    LinkHover :Tuple [float ,float ,float ,float ]=(0.6 ,0.8 ,1.0 ,1.0 )
    LinkHoverBg :Tuple [float ,float ,float ,float ]=(0.4 ,0.7 ,1.0 ,0.2 )
    AuthMessage :Tuple [float ,float ,float ,float ]=(1.0 ,0.7 ,0.4 ,1.0 )
    PrimaryButton :Tuple [float ,float ,float ,float ]=(0.4 ,0.7 ,1.0 ,1.0 )
    DisabledButton :Tuple [float ,float ,float ,float ]=(0.3 ,0.3 ,0.3 ,1.0 )
    LogoutButton :Tuple [float ,float ,float ,float ]=(0.25 ,0.25 ,0.25 ,1.0 )
    LogoutButtonHover :Tuple [float ,float ,float ,float ]=(0.35 ,0.35 ,0.35 ,1.0 )
    DeleteButton :Tuple [float ,float ,float ,float ]=(0.6 ,0.2 ,0.2 ,1.0 )
    DeleteButtonHover :Tuple [float ,float ,float ,float ]=(0.8 ,0.3 ,0.3 ,1.0 )
    HoverBackground :Tuple [float ,float ,float ,float ]=(0.2 ,0.2 ,0.2 ,0.5 )
    EditingHighlight :Tuple [float ,float ,float ,float ]=(0.4 ,0.7 ,1.0 ,0.3 )
    ToggleEnabled :Tuple [float ,float ,float ,float ]=(0.4 ,0.7 ,1.0 ,1.0 )
    ToggleDisabled :Tuple [float ,float ,float ,float ]=(0.6 ,0.6 ,0.6 ,1.0 )
    ToggleFill :Tuple [float ,float ,float ,float ]=(0.2 ,0.5 ,0.8 ,0.8 )
    Checkmark :Tuple [float ,float ,float ,float ]=(1.0 ,1.0 ,1.0 ,1.0 )


    _colors :Dict [str ,ColorInfo ]={}
    _loaded :bool =False 
    _cached_theme_hash :Optional [str ]=None 





    @classmethod 
    def get_base_font_size (cls )->int :
        """Get the base font size scaled by UI scale factor."""
        return int (11 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_font_size (cls ,size_type :str ="default")->int :
        """Get font size for different use cases."""
        base_size =cls .get_base_font_size ()

        if size_type =="title":
            return base_size +int (4 *CoordinateSystem .get_ui_scale ())
        elif size_type =="small":
            return int (base_size *0.9 )
        elif size_type =="large":
            return int (base_size *1.2 )
        else :
            return base_size 





    @classmethod 
    def get_input_area_height (cls )->int :
        return int (32 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_header_height (cls )->int :
        return int (32 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_viewport_margin (cls )->int :
        return int (4 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_viewport_padding_small (cls )->int :
        return int (10 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_container_padding (cls )->int :
        return int (10 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_button_margin (cls )->int :
        return int (5 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_min_button_margin (cls )->int :
        return int (5 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_header_gap (cls )->int :
        return int (10 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_button_gap (cls )->int :
        return int (6 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_message_gap (cls )->int :
        return int (12 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_same_role_message_gap (cls )->int :
        """Gap between messages from the same role (user->user or assistant->assistant)."""
        return int (12 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_different_role_message_gap (cls )->int :
        """Gap between messages from different roles (user->assistant or assistant->user)."""
        return int (16 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_message_padding (cls )->int :
        return int (20 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_message_area_padding (cls )->int :
        return int (10 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_header_vertical_margin (cls )->int :
        return int (16 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_dropdown_width (cls )->int :
        return int (150 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_dropdown_height (cls )->int :
        return int (22 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_dropdown_corner_radius (cls )->int :
        return int (4 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_dropdown_padding_horizontal (cls )->int :
        return int (6 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_dropdown_padding_vertical (cls )->int :
        return int (4 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_dropdown_icon_gap (cls )->int :
        return int (6 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_header_padding_horizontal (cls )->int :
        return int (12 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_header_padding_vertical (cls )->int :
        return int (4 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_header_icon_button_size (cls )->int :
        return int (22 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_header_icon_button_corner_radius (cls )->int :
        return int (4 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_header_icon_button_spacing (cls )->int :
        return int (6 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_header_icon_size (cls )->int :
        return int (14 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_send_button_size (cls )->int :
        return int (20 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_send_button_corner_radius (cls )->int :
        return int (6 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_send_button_icon_size (cls )->int :
        return int (14 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_send_button_spacing (cls )->int :
        return int (6 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_text_input_margin (cls )->int :
        return int (12 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_text_input_max_height (cls )->int :
        return int (280 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_min_message_height (cls )->int :
        return int (100 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_scrollbar_buffer (cls )->int :
        return int (40 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_button_corner_radius (cls )->int :
        return int (6 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_text_input_corner_radius (cls )->int :
        return int (8 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_text_input_padding (cls )->int :
        return int (6 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_text_input_border_width (cls )->int :
        return int (1 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_text_input_content_padding_left (cls )->int :
        return int (4 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_text_input_content_padding_right_offset (cls )->int :
        return int (8 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_message_border_width (cls )->int :
        return int (1 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_button_container_height (cls )->int :
        return int (40 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_button_container_width_estimate (cls )->int :
        return int (200 *CoordinateSystem .get_ui_scale ())





    @classmethod 
    def get_left_margin (cls )->int :
        return int (20 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_right_margin (cls )->int :
        return int (20 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_container_internal_padding (cls )->int :
        return int (8 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_scrollview_internal_margin (cls )->int :
        return int (6 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_scrollview_content_padding (cls )->int :
        return int (12 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_big_spacing (cls )->int :
        return int (24 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_small_spacing (cls )->int :
        return int (8 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_medium_spacing (cls )->int :
        return int (12 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_rule_spacing (cls )->int :
        return int (26 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_link_spacing (cls )->int :
        return int (8 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_bottom_padding (cls )->int :
        return int (20 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_button_height (cls )->int :
        return int (24 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_large_button_height (cls )->int :
        return int (24 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_small_button_height (cls )->int :
        return int (20 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_label_height (cls )->int :
        return int (11 *1.2 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_small_label_height (cls )->int :
        return int (11 *1.2 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_input_height (cls )->int :
        return int (30 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_toggle_button_size (cls )->int :
        return int (20 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_go_back_button_width (cls )->int :
        return int (100 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_name_label_width (cls )->int :
        return int (150 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_plan_label_width (cls )->int :
        return int (200 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_manage_sub_label_width (cls )->int :
        return int (200 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_logout_button_width (cls )->int :
        return int (70 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_add_button_width (cls )->int :
        return int (50 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_large_add_button_width (cls )->int :
        return int (60 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_toggle_button_width (cls )->int :
        return int (20 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_delete_button_width (cls )->int :
        return int (30 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_rule_button_left_offset (cls )->int :
        return int (60 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_link_label_width (cls )->int :
        return int (100 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_info_container_height (cls )->int :
        return int (104 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_rules_container_height (cls )->int :
        return int (150 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_rules_scrollview_height (cls )->int :
        return int (100 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_small_radius (cls )->int :
        return int (1 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_medium_radius (cls )->int :
        return int (2 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_large_radius (cls )->int :
        return int (4 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_extra_large_radius (cls )->int :
        return int (6 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_container_radius (cls )->int :
        return int (8 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_scrollbar_width (cls )->int :
        return int (6 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_no_border (cls )->int :
        return 0 

    @classmethod 
    def get_thin_border (cls )->int :
        return 1 

    @classmethod 
    def get_thick_border (cls )->int :
        return int (2 *CoordinateSystem .get_ui_scale ())





    @classmethod 
    def get_main_padding (cls )->int :
        return int (10 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_content_margin (cls )->int :
        return int (10 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_scrollview_margin (cls )->int :
        return int (20 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_button_height_standard (cls )->int :
        return int (24 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_button_height_large (cls )->int :
        return int (30 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_new_chat_button_height (cls )->int :
        return int (26 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_button_width_standard (cls )->int :
        return int (100 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_button_corner_radius_standard (cls )->int :
        return int (4 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_button_spacing (cls )->int :
        return int (5 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_item_height_chat (cls )->int :
        return int (22 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_item_height_label (cls )->int :
        return int (20 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_item_spacing (cls )->int :
        return int (5 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_go_back_button_offset (cls )->int :
        return int (6 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_go_back_button_side_padding (cls )->int :
        return int (12 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_go_back_button_icon_size (cls )->int :
        return int (14 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_go_back_button_icon_gap (cls )->int :
        return int (4 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_new_chat_button_offset (cls )->int :
        return int (70 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_history_area_top_offset (cls )->int :
        return int (80 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_history_area_bottom_offset (cls )->int :
        return int (80 *CoordinateSystem .get_ui_scale ())





    @classmethod 
    def get_markdown_corner_radius (cls )->int :
        return int (8 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_markdown_padding (cls )->int :
        return int (12 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_markdown_block_icon_size (cls )->int :
        return int (12 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_markdown_block_padding (cls )->int :
        return int (8 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_markdown_block_text_padding (cls )->int :
        return int (4 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_markdown_block_height (cls )->int :
        return int (22 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_markdown_block_margin (cls )->int :
        return int (0 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_markdown_block_corner_radius (cls )->int :
        return int (6 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_markdown_block_min_width (cls )->int :
        return int (0 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_markdown_min_component_width (cls )->int :
        return int (100 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_markdown_min_component_height (cls )->int :
        return int (0 *CoordinateSystem .get_ui_scale ())





    @classmethod 
    def get_style (cls ,style_type :str ="default")->Style :
        """Get a themed style using centralized colors."""
        style =Style ()

        if style_type =="input":
            style .background_color =cls .MenuBg 
            style .focus_background_color =cls .lighten_color (cls .MenuBg ,10 )
            style .border_color =cls .Border 
            style .focus_border_color =cls .Border 
            style .text_color =cls .Text 
            style .font_size =cls .get_font_size ()
            style .padding =cls .get_container_padding ()

        elif style_type =="button":
            style .background_color =cls .Primary 
            style .focus_background_color =tuple (min (c *1.3 ,1.0 )for c in cls .Primary [:3 ])+(1.0 ,)
            style .pressed_background_color =tuple (c *0.8 for c in cls .Primary [:3 ])+(1.0 ,)
            style .border_color =cls .Border 
            style .focus_border_color =cls .Border 
            style .pressed_border_color =tuple (c *0.9 for c in cls .Selected [:3 ])+(1.0 ,)
            style .text_color =cls .Text 
            style .font_size =cls .get_font_size ()
            style .padding =cls .get_container_padding ()
            style .border_width =cls .get_thin_border ()

        elif style_type =="title":
            style .background_color =cls .Transparent 
            style .text_color =cls .Text 
            style .font_size =cls .get_font_size ("title")
            style .padding =cls .get_container_padding ()
            style .border_width =cls .get_no_border ()

        elif style_type =="panel":
            style .background_color =cls .Panel 
            style .border_color =cls .Border 
            style .text_color =cls .Text 
            style .font_size =cls .get_font_size ()
            style .padding =cls .get_container_padding ()
            style .border_width =cls .get_thin_border ()

        elif style_type =="menu":
            style .background_color =cls .MenuBg 
            style .border_color =cls .Border 
            style .text_color =cls .Text 
            style .font_size =cls .get_font_size ()
            style .padding =cls .get_container_padding ()
            style .border_width =cls .get_thin_border ()

        else :
            style .background_color =cls .Transparent 
            style .text_color =cls .Text 
            style .font_size =cls .get_font_size ()
            style .padding =cls .get_container_padding ()//2 
            style .border_width =cls .get_no_border ()

        return style 





    @classmethod 
    def load_colors (cls )->bool :
        """Load colors from the JSON file."""
        if cls ._loaded :
            return True 

        try :
            current_dir =os .path .dirname (__file__ )
            json_path =os .path .join (current_dir ,'blender_theme_colors.json')

            if not os .path .exists (json_path ):
                logger .warning (f"Color JSON file not found at {json_path}")
                return False 

            with open (json_path ,'r')as f :
                color_data =json .load (f )


            for color_info in color_data :
                token =color_info ['token']
                hex_color =color_info ['hex']
                rgba =cls ._hex_to_rgba (hex_color )

                color_obj =ColorInfo (
                token =token ,
                hex =hex_color ,
                rgba =rgba ,
                theme_path =color_info ['theme_path'],
                description =color_info ['description']
                )

                cls ._colors [token ]=color_obj 


            cls ._update_class_colors ()
            cls ._loaded =True 
            return True 

        except Exception as e :
            logger .error (f"Failed to load colors from JSON: {e}")
            return False 

    @classmethod 
    def _hex_to_rgba (cls ,hex_color :str )->Tuple [float ,float ,float ,float ]:
        """Convert hex color to RGBA tuple (0-1 range)."""
        hex_color =hex_color .lstrip ('#')
        r =int (hex_color [0 :2 ],16 )
        g =int (hex_color [2 :4 ],16 )
        b =int (hex_color [4 :6 ],16 )
        return (r /255.0 ,g /255.0 ,b /255.0 ,1.0 )

    @classmethod 
    def _update_class_colors (cls ):
        """Update class color variables from loaded colors."""
        color_mapping ={
        'ui_bg_primary':'Primary',
        'ui_bg_panel':'Panel',
        'ui_bg_selected':'Selected',
        'ui_border':'Border',
        'ui_text':'Text',
        'ui_text_selected':'TextSelected',
        'ui_text_muted':'TextMuted',
        'ui_menu_bg':'MenuBg',
        }

        for token ,attr_name in color_mapping .items ():
            if token in cls ._colors :
                setattr (cls ,attr_name ,cls ._colors [token ].rgba )


        if 'ui_menu_bg'in cls ._colors :
            cls .Button =cls ._colors ['ui_menu_bg'].rgba 
        if 'ui_bg_selected'in cls ._colors :
            cls .Highlight =cls ._colors ['ui_bg_selected'].rgba 

    @classmethod 
    def get_color (cls ,token :str )->Tuple [float ,float ,float ,float ]:
        """Get color by token name."""
        cls .load_colors ()

        if token in cls ._colors :
            return cls ._colors [token ].rgba 
        else :
            logger .warning (f"Color token '{token}' not found, returning white")
            return (1.0 ,1.0 ,1.0 ,1.0 )

    @classmethod 
    def get_color_info (cls ,token :str )->Optional [ColorInfo ]:
        """Get complete color information by token name."""
        cls .load_colors ()
        return cls ._colors .get (token )

    @classmethod 
    def get_all_colors (cls )->Dict [str ,ColorInfo ]:
        """Get all color information."""
        cls .load_colors ()
        return cls ._colors .copy ()

    @classmethod 
    def to_hex (cls ,rgba :Tuple [float ,float ,float ,float ])->str :
        """Convert RGBA tuple back to hex string."""
        r ,g ,b =rgba [:3 ]
        return f"#{int(r * 255):02X}{int(g * 255):02X}{int(b * 255):02X}"

    @classmethod 
    def lighten_color (cls ,rgba :Tuple [float ,float ,float ,float ],percent :float )->Tuple [float ,float ,float ,float ]:
        """Return a lightened version of the color by the given percent (0-100)."""
        r ,g ,b ,a =rgba 
        factor =percent /100.0 
        r =min (r +(1.0 -r )*factor ,1.0 )
        g =min (g +(1.0 -g )*factor ,1.0 )
        b =min (b +(1.0 -b )*factor ,1.0 )
        return (r ,g ,b ,a )

    @classmethod 
    def darken_color (cls ,rgba :Tuple [float ,float ,float ,float ],percent :float )->Tuple [float ,float ,float ,float ]:
        """Return a darkened version of the color by the given percent (0-100)."""
        r ,g ,b ,a =rgba 
        factor =percent /100.0 
        r =max (r *(1.0 -factor ),0.0 )
        g =max (g *(1.0 -factor ),0.0 )
        b =max (b *(1.0 -factor ),0.0 )
        return (r ,g ,b ,a )





    @classmethod 
    def update_from_blender_theme (cls )->bool :
        """Update theme from Blender's theme preferences."""
        try :
            current_hash =cls ._calculate_theme_hash ()

            if current_hash !=cls ._cached_theme_hash :

                cls ._cached_theme_hash =current_hash 
                return True 

        except Exception as e :
            logger .warning (f"Failed to update theme: {e}")

        return False 

    @classmethod 
    def _calculate_theme_hash (cls )->str :
        """Calculate a hash of current theme values to detect changes."""
        try :
            theme =bpy .context .preferences .themes [0 ]
            ui =theme .user_interface 
            view_3d =theme .view_3d 
            system =bpy .context .preferences .system 

            wcol_text =ui .wcol_text 
            wcol_regular =ui .wcol_regular 
            wcol_menu_back =ui .wcol_menu_back 

            theme_data =(
            tuple (wcol_menu_back .inner [:3 ]),
            tuple (wcol_regular .text [:3 ]),
            tuple (wcol_text .inner [:3 ]),
            tuple (view_3d .edge_select [:3 ]),
            tuple (wcol_text .outline [:3 ]),
            system .dpi ,
            )

            theme_str =str (theme_data )
            return hashlib .md5 (theme_str .encode ()).hexdigest ()

        except Exception as e :
            logger .warning (f"Failed to calculate theme hash: {e}")
            return "fallback"






    @classmethod 
    def get_no_connection_icon_width (cls )->int :
        return int (60 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_no_connection_icon_height (cls )->int :
        return int (60 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_no_connection_title_width (cls )->int :
        return int (300 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_no_connection_title_height (cls )->int :
        return int (30 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_no_connection_subtitle_width (cls )->int :
        return int (400 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_no_connection_subtitle_height (cls )->int :
        return int (40 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_no_connection_button_width (cls )->int :
        return int (160 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_no_connection_button_height (cls )->int :
        return int (30 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_no_connection_gap_large (cls )->int :
        return int (30 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_no_connection_gap_medium (cls )->int :
        return int (20 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_no_connection_padding (cls )->int :
        return int (20 *CoordinateSystem .get_ui_scale ())

    @classmethod 
    def get_no_connection_button_corner_radius (cls )->int :
        return int (12 *CoordinateSystem .get_ui_scale ())






    MAX_RULE_TEXT_LENGTH =40 
    TRUNCATION_SUFFIX ="..."
    TITLE_MAX_LENGTH =32 


    LINE_HEIGHT_ADDITION =4 
    TEXT_ESTIMATION_FACTOR =0.6 


    HEADING_SIZE_MULTIPLIERS ={
    1 :1.8 ,
    2 :1.6 ,
    3 :1.4 ,
    4 :1.2 ,
    5 :1.1 ,
    6 :1.05 
    }


    CODE_FONT_SIZE_MULTIPLIER =1 
    INLINE_CODE_FONT_SIZE_MULTIPLIER =1 
    BOLD_FONT_SIZE_MULTIPLIER =1 



UnifiedStyles .load_colors ()



Styles =UnifiedStyles 


def get_color (token :str )->Tuple [float ,float ,float ,float ]:
    """Get color by token name."""
    return UnifiedStyles .get_color (token )

def get_color_hex (token :str )->str :
    """Get color by token name as hex string."""
    rgba =UnifiedStyles .get_color (token )
    return UnifiedStyles .to_hex (rgba )

def get_themed_style (style_type :str ="default")->Style :
    """Get themed style using unified styles."""
    return UnifiedStyles .get_style (style_type )

def lighten_color (rgba :Tuple [float ,float ,float ,float ],percent :float )->Tuple [float ,float ,float ,float ]:
    """Return a lightened version of the color by the given percent (0-100)."""
    return UnifiedStyles .lighten_color (rgba ,percent )

def darken_color (rgba :Tuple [float ,float ,float ,float ],percent :float )->Tuple [float ,float ,float ,float ]:
    """Return a darkened version of the color by the given percent (0-100)."""
    return UnifiedStyles .darken_color (rgba ,percent )

