"""
Dropdown components for selection interfaces.
"""

import logging 
import os 
from .button import Button 
from .image import ImageComponent 
from ..theme import get_themed_style 
from ..types import Bounds 
from ..styles import FontSizes 
from ..colors import Colors 
from ..coordinates import CoordinateSystem 
from ..unified_styles import Styles 

logger =logging .getLogger (__name__ )


class ModelDropdown (Button ):
    """Model dropdown component matching Figma design specifications."""

    def __init__ (self ,options :list ,x :int =0 ,y :int =0 ,width :int =150 ,height :int =22 ,on_change =None ):
        super ().__init__ ("",x ,y ,width ,height ,corner_radius =Styles .get_dropdown_corner_radius ())

        self .options =options 
        self .selected_index =0 
        self .is_open =False 
        self .on_change =on_change 
        self .option_height =CoordinateSystem .scale_int (21 )
        self .dropdown_items =[]


        self .style =get_themed_style ("input")
        self .style .background_color =Styles .get_themed_color ('bg_panel')
        self .style .border_color =Styles .get_themed_color ('border')
        self .style .border_width =Styles .get_thin_border ()
        self .style .padding =Styles .get_dropdown_padding_horizontal ()
        self .style .font_size =Styles .get_base_font_size ()


        self .brain_icon =self ._load_icon ("brain-icon.png")
        self .chevron_icon =self ._load_icon ("chevron.png")


        self .on_click =self ._toggle_dropdown 


        self ._create_dropdown_items ()

    def _load_icon (self ,icon_name :str ):
        """Load an icon from the icons directory."""
        try :
            current_dir =os .path .dirname (os .path .dirname (__file__ ))
            icon_path =os .path .join (current_dir ,"icons",icon_name )
            if os .path .exists (icon_path ):

                icon =ImageComponent (icon_path ,0 ,0 ,CoordinateSystem .scale_int (16 ),CoordinateSystem .scale_int (16 ))
                return icon 
            else :
                logger .warning (f"Icon not found: {icon_path}")
                return None 
        except Exception as e :
            logger .error (f"Failed to load icon {icon_name}: {e}")
            return None 

    def _create_dropdown_items (self ):
        """Create individual dropdown option components."""
        self .dropdown_items =[]
        for i ,option in enumerate (self .options ):
            is_last =(i ==len (self .options )-1 )
            item =DropdownItem (option ,i ,self ._select_option ,is_last ,self )
            self .dropdown_items .append (item )

    def _toggle_dropdown (self ):
        """Toggle dropdown open/closed state."""
        self .is_open =not self .is_open 
        logger .info (f"Dropdown {'opened' if self.is_open else 'closed'}")

        if self .is_open :

            item_spacing =2 
            for i ,item in enumerate (self .dropdown_items ):
                item_y =self .bounds .y -(i +1 )*(self .option_height +item_spacing )
                item .set_position (self .bounds .x ,item_y )
                item .set_size (self .bounds .width ,self .option_height )
                item .visible =True 


                if hasattr (self ,'ui_state')and self .ui_state :
                    if item not in self .ui_state .components :
                        self .ui_state .add_component (item )
        else :

            for item in self .dropdown_items :
                item .visible =False 

                if hasattr (self ,'ui_state')and self .ui_state :
                    if item in self .ui_state .components :
                        self .ui_state .components .remove (item )

    def _select_option (self ,index :int ):
        """Select a dropdown option."""
        if 0 <=index <len (self .options ):
            self .selected_index =index 
            self .is_open =False 


            for item in self .dropdown_items :
                item .visible =False 
                if hasattr (self ,'ui_state')and self .ui_state :
                    if item in self .ui_state .components :
                        self .ui_state .components .remove (item )


            if self .on_change :
                self .on_change (self .options [self .selected_index ])

            logger .info (f"Selected option: {self.options[self.selected_index]}")

    def get_selected_option (self ):
        """Get the currently selected option."""
        return self .options [self .selected_index ]if self .options else ""

    def handle_event (self ,event ):
        """Handle events for the dropdown."""

        result =super ().handle_event (event )


        if (self .is_open and event .event_type .name =='MOUSE_PRESS'and 
        not self .bounds .contains_point (event .mouse_x ,event .mouse_y )):


            clicked_on_item =False 
            for item in self .dropdown_items :
                if item .visible and item .bounds .contains_point (event .mouse_x ,event .mouse_y ):
                    clicked_on_item =True 
                    break 


            if not clicked_on_item :
                self .is_open =False 
                for item in self .dropdown_items :
                    item .visible =False 
                    if hasattr (self ,'ui_state')and self .ui_state :
                        if item in self .ui_state .components :
                            self .ui_state .components .remove (item )

        return result 

    def render (self ,renderer ):
        """Render the dropdown with brain icon, model name, and chevron icon."""
        if not self .visible :
            return 


        self ._update_pressed_state ()


        bg_color =self .style .background_color 
        border_color =self .style .border_color 
        text_color =Styles .get_themed_color ('text')


        if self .is_hovered :
            bg_color =Styles .lighten_color (bg_color ,5 )


        if self .is_pressed :
            bg_color =Styles .darken_color (bg_color ,5 )


        if self .is_open :
            bg_color =Colors .Selected 


        renderer .draw_rounded_rect (self .bounds ,bg_color ,self .corner_radius )


        if self .style .border_width >0 :
            renderer .draw_rounded_rect_outline (self .bounds ,border_color ,
            self .style .border_width ,self .corner_radius )


        content_x =self .bounds .x +Styles .get_dropdown_padding_horizontal ()
        content_y =self .bounds .y +Styles .get_dropdown_padding_vertical ()
        content_height =self .bounds .height -(Styles .get_dropdown_padding_vertical ()*2 )


        if self .brain_icon :
            icon_size =CoordinateSystem .scale_int (16 )
            icon_y =self .bounds .y +(self .bounds .height -icon_size )//2 
            self .brain_icon .set_position (content_x ,icon_y )
            self .brain_icon .set_size (icon_size ,icon_size )
            self .brain_icon .render (renderer )


            content_x +=icon_size +Styles .get_dropdown_icon_gap ()


        selected_text =self .get_selected_option ()
        if selected_text :
            text_y =self .bounds .y +(self .bounds .height -self .style .font_size )//2 
            renderer .draw_text (selected_text ,content_x ,text_y ,self .style .font_size ,text_color )


        if self .chevron_icon :
            icon_size =CoordinateSystem .scale_int (16 )
            chevron_x =self .bounds .x +self .bounds .width -Styles .get_dropdown_padding_horizontal ()-icon_size 
            chevron_y =self .bounds .y +(self .bounds .height -icon_size )//2 
            self .chevron_icon .set_position (chevron_x ,chevron_y )
            self .chevron_icon .set_size (icon_size ,icon_size )
            self .chevron_icon .render (renderer )


class DropdownItem (Button ):
    """Individual dropdown option item."""

    def __init__ (self ,text :str ,index :int ,select_callback ,is_last :bool ,parent_dropdown =None ):
        super ().__init__ (text ,0 ,0 ,CoordinateSystem .scale_int (100 ),CoordinateSystem .scale_int (30 ),corner_radius =CoordinateSystem .scale_int (8 ))
        self .index =index 
        self .select_callback =select_callback 
        self .visible =False 
        self .is_last =is_last 
        self .parent_dropdown =parent_dropdown 


        self .style =get_themed_style ("button")
        self .style .background_color =Styles .get_themed_color ('bg_menu')
        self .style .border_color =Styles .get_themed_color ('border')
        self .style .border_width =Styles .get_thin_border ()
        self .style .text_color =Styles .get_themed_color ('text')
        self .style .font_size =Styles .get_base_font_size ()
        self .style .padding =Styles .get_dropdown_padding_horizontal ()


        self .on_click =self ._on_item_click 

    def _on_item_click (self ):
        """Handle click on this dropdown item."""
        self .select_callback (self .index )

    def render (self ,renderer ):
        """Render the dropdown item."""
        if not self .visible :
            return 


        self ._update_pressed_state ()


        bg_color =self .style .background_color 
        border_color =self .style .border_color 
        text_color =self .style .text_color 


        is_selected =(self .parent_dropdown and 
        self .parent_dropdown .selected_index ==self .index )


        if self .is_hovered :
            bg_color =Styles .lighten_color (bg_color ,10 )


        if self .is_pressed :
            bg_color =Styles .darken_color (bg_color ,10 )


        if is_selected :
            bg_color =Colors .Selected 


        if self .is_last :

            renderer .draw_rect_with_bottom_corners_rounded (
            self .bounds ,bg_color ,self .corner_radius 
            )
        else :

            renderer .draw_rect (self .bounds ,bg_color )


        if self .style .border_width >0 :
            if self .is_last :

                renderer .draw_rect_outline_with_bottom_corners_rounded (
                self .bounds ,border_color ,self .style .border_width ,self .corner_radius 
                )
            else :

                renderer .draw_rect_outline (self .bounds ,border_color ,self .style .border_width )


        if self .text :
            text_x =self .bounds .x +self .style .padding 
            text_y =self .bounds .y +(self .bounds .height -self .style .font_size )//2 +CoordinateSystem .scale_int (2 )
            renderer .draw_text (self .text ,text_x ,text_y ,self .style .font_size ,text_color )

    def _get_current_colors (self ):
        """Get colors for current state."""
        bg_color =self .style .background_color 
        border_color =self .style .border_color 
        text_color =self .style .text_color 

        if self .is_hovered :
            bg_color =Styles .lighten_color (bg_color ,10 )

        if self .is_pressed :
            bg_color =Styles .darken_color (bg_color ,10 )

        return bg_color ,border_color ,text_color 