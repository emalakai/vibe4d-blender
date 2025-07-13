"""
Automated layout management system for UI components.
Provides various layout strategies to automatically position components.
"""

import logging 
from typing import List ,Dict ,Optional ,Tuple ,Union ,Callable 
from enum import Enum 
from dataclasses import dataclass 

from .types import Bounds 
from .components .base import UIComponent 

logger =logging .getLogger (__name__ )


class LayoutStrategy (Enum ):
    """Layout positioning strategies."""
    MANUAL ="manual"
    FLEX_VERTICAL ="flex_vertical"
    FLEX_HORIZONTAL ="flex_horizontal"
    GRID ="grid"
    ABSOLUTE ="absolute"
    STACK ="stack"
    ANCHOR ="anchor"


class FlexDirection (Enum ):
    """Flex layout direction."""
    ROW ="row"
    COLUMN ="column"
    ROW_REVERSE ="row_reverse"
    COLUMN_REVERSE ="column_reverse"


class JustifyContent (Enum ):
    """How to distribute space along main axis."""
    START ="start"
    CENTER ="center"
    END ="end"
    SPACE_BETWEEN ="space_between"
    SPACE_AROUND ="space_around"
    SPACE_EVENLY ="space_evenly"


class AlignItems (Enum ):
    """How to align items along cross axis."""
    START ="start"
    CENTER ="center"
    END ="end"
    STRETCH ="stretch"
    BASELINE ="baseline"


@dataclass 
class LayoutConstraints :
    """Layout constraints for component positioning."""

    flex_grow :float =0.0 
    flex_shrink :float =1.0 
    flex_basis :Optional [int ]=None 


    min_width :Optional [int ]=None 
    max_width :Optional [int ]=None 
    min_height :Optional [int ]=None 
    max_height :Optional [int ]=None 


    margin_top :int =0 
    margin_right :int =0 
    margin_bottom :int =0 
    margin_left :int =0 


    padding_top :int =0 
    padding_right :int =0 
    padding_bottom :int =0 
    padding_left :int =0 


    top :Optional [int ]=None 
    right :Optional [int ]=None 
    bottom :Optional [int ]=None 
    left :Optional [int ]=None 


    align_self :Optional [AlignItems ]=None 


@dataclass 
class LayoutConfig :
    """Configuration for a layout container."""
    strategy :LayoutStrategy =LayoutStrategy .FLEX_VERTICAL 


    direction :FlexDirection =FlexDirection .COLUMN 
    justify_content :JustifyContent =JustifyContent .START 
    align_items :AlignItems =AlignItems .START 
    gap :int =5 


    padding_top :int =0 
    padding_right :int =0 
    padding_bottom :int =0 
    padding_left :int =0 


    grid_columns :int =1 
    grid_rows :Optional [int ]=None 
    grid_gap :int =5 


class AutoResizeManager :
    """Manages automatic resizing of layouts when viewport changes."""

    def __init__ (self ,layout_manager ):
        self .layout_manager =layout_manager 
        self .viewport_callbacks :List [Callable [[int ,int ],None ]]=[]
        self .current_viewport =(0 ,0 )

    def register_viewport_callback (self ,callback :Callable [[int ,int ],None ]):
        """Register a callback for viewport changes."""
        self .viewport_callbacks .append (callback )

    def unregister_viewport_callback (self ,callback :Callable [[int ,int ],None ]):
        """Unregister a viewport callback."""
        if callback in self .viewport_callbacks :
            self .viewport_callbacks .remove (callback )

    def handle_viewport_change (self ,width :int ,height :int ):
        """Handle viewport size change and trigger layout updates."""
        if (width ,height )==self .current_viewport :
            return 

        old_viewport =self .current_viewport 
        self .current_viewport =(width ,height )


        self .layout_manager .update_all_layouts (width ,height )


        for callback in self .viewport_callbacks :
            try :
                callback (width ,height )
            except Exception as e :
                logger .error (f"Error in viewport callback: {e}")


class LayoutManager :
    """Manages automated layout for UI components."""

    def __init__ (self ):
        self .layouts :Dict [str ,LayoutConfig ]={}
        self .constraints :Dict [UIComponent ,LayoutConstraints ]={}
        self .containers :Dict [str ,List [UIComponent ]]={}
        self .container_bounds :Dict [str ,Bounds ]={}


        self .auto_resize =AutoResizeManager (self )

    def create_layout (self ,name :str ,config :LayoutConfig )->str :
        """Create a new layout configuration."""
        self .layouts [name ]=config 
        self .containers [name ]=[]
        return name 

    def add_component (self ,layout_name :str ,component :UIComponent ,
    constraints :Optional [LayoutConstraints ]=None ):
        """Add a component to a layout."""
        if layout_name not in self .containers :
            raise ValueError (f"Layout '{layout_name}' does not exist")

        self .containers [layout_name ].append (component )
        if constraints :
            self .constraints [component ]=constraints 

    def remove_component (self ,layout_name :str ,component :UIComponent ):
        """Remove a component from a layout."""
        if layout_name in self .containers and component in self .containers [layout_name ]:
            self .containers [layout_name ].remove (component )
            if component in self .constraints :
                del self .constraints [component ]

    def update_layout (self ,layout_name :str ,container_bounds :Bounds ):
        """Update positions of all components in a layout."""
        if layout_name not in self .layouts :
            return 


        self .container_bounds [layout_name ]=container_bounds 

        config =self .layouts [layout_name ]
        components =self .containers .get (layout_name ,[])

        if not components :
            return 


        if config .strategy ==LayoutStrategy .FLEX_VERTICAL :
            self ._apply_flex_layout (components ,container_bounds ,config ,FlexDirection .COLUMN )
        elif config .strategy ==LayoutStrategy .FLEX_HORIZONTAL :
            self ._apply_flex_layout (components ,container_bounds ,config ,FlexDirection .ROW )
        elif config .strategy ==LayoutStrategy .STACK :
            self ._apply_stack_layout (components ,container_bounds ,config )
        elif config .strategy ==LayoutStrategy .GRID :
            self ._apply_grid_layout (components ,container_bounds ,config )
        elif config .strategy ==LayoutStrategy .ABSOLUTE :
            self ._apply_absolute_layout (components ,container_bounds ,config )
        elif config .strategy ==LayoutStrategy .ANCHOR :
            self ._apply_anchor_layout (components ,container_bounds ,config )


    def update_all_layouts (self ,viewport_width :int ,viewport_height :int ):
        """Update all layouts when viewport changes."""
        for layout_name ,bounds in self .container_bounds .items ():

            if bounds .width >=viewport_width *0.9 and bounds .height >=viewport_height *0.9 :
                new_bounds =Bounds (bounds .x ,bounds .y ,viewport_width ,viewport_height )
                self .update_layout (layout_name ,new_bounds )
            else :

                self .update_layout (layout_name ,bounds )

    def register_auto_resize_callback (self ,callback :Callable [[int ,int ],None ]):
        """Register callback for automatic viewport change handling."""
        self .auto_resize .register_viewport_callback (callback )

    def handle_viewport_change (self ,width :int ,height :int ):
        """Handle viewport change automatically."""
        self .auto_resize .handle_viewport_change (width ,height )

    def _apply_flex_layout (self ,components :List [UIComponent ],container_bounds :Bounds ,
    config :LayoutConfig ,direction :FlexDirection ):
        """Apply flex layout positioning."""
        if not components :
            return 


        available_width =container_bounds .width -config .padding_left -config .padding_right 
        available_height =container_bounds .height -config .padding_top -config .padding_bottom 


        is_row =direction in [FlexDirection .ROW ,FlexDirection .ROW_REVERSE ]
        main_size =available_width if is_row else available_height 
        cross_size =available_height if is_row else available_width 


        total_gap =config .gap *(len (components )-1 )
        remaining_main_size =main_size -total_gap 


        component_info =[]
        total_flex_grow =0 

        for comp in components :
            constraints =self .constraints .get (comp ,LayoutConstraints ())


            if is_row :
                preferred_main =comp .bounds .width 
                preferred_cross =comp .bounds .height 
            else :
                preferred_main =comp .bounds .height 
                preferred_cross =comp .bounds .width 


            if constraints .flex_basis is not None :
                main_size_comp =constraints .flex_basis 
            else :
                main_size_comp =preferred_main 

            component_info .append ({
            'component':comp ,
            'constraints':constraints ,
            'preferred_main':preferred_main ,
            'preferred_cross':preferred_cross ,
            'main_size':main_size_comp ,
            'cross_size':preferred_cross 
            })

            total_flex_grow +=constraints .flex_grow 
            remaining_main_size -=main_size_comp 


        if total_flex_grow >0 and remaining_main_size >0 :
            for info in component_info :
                if info ['constraints'].flex_grow >0 :
                    extra_space =remaining_main_size *(info ['constraints'].flex_grow /total_flex_grow )
                    info ['main_size']+=extra_space 


        current_main_pos =0 


        if config .justify_content ==JustifyContent .CENTER :
            current_main_pos =(main_size -sum (info ['main_size']for info in component_info )-total_gap )//2 
        elif config .justify_content ==JustifyContent .END :
            current_main_pos =main_size -sum (info ['main_size']for info in component_info )-total_gap 
        elif config .justify_content ==JustifyContent .SPACE_BETWEEN :
            if len (components )>1 :
                config .gap =(main_size -sum (info ['main_size']for info in component_info ))//(len (components )-1 )
        elif config .justify_content ==JustifyContent .SPACE_AROUND :
            if len (components )>0 :
                extra_space =(main_size -sum (info ['main_size']for info in component_info ))//len (components )
                current_main_pos =extra_space //2 
                config .gap =extra_space 

        for i ,info in enumerate (component_info ):
            comp =info ['component']
            constraints =info ['constraints']


            cross_pos =0 
            cross_component_size =info ['cross_size']


            align =constraints .align_self or config .align_items 
            if align ==AlignItems .CENTER :
                cross_pos =(cross_size -cross_component_size )//2 
            elif align ==AlignItems .END :
                cross_pos =cross_size -cross_component_size 
            elif align ==AlignItems .STRETCH :
                cross_component_size =cross_size 


            main_pos_with_margin =current_main_pos 
            cross_pos_with_margin =cross_pos 

            if is_row :
                main_pos_with_margin +=constraints .margin_left 
                cross_pos_with_margin +=constraints .margin_top 


                final_x =container_bounds .x +config .padding_left +main_pos_with_margin 
                final_y =container_bounds .y +config .padding_bottom +cross_pos_with_margin 
                final_width =int (info ['main_size']-constraints .margin_left -constraints .margin_right )
                final_height =int (cross_component_size -constraints .margin_top -constraints .margin_bottom )
            else :
                main_pos_with_margin +=constraints .margin_top 
                cross_pos_with_margin +=constraints .margin_left 


                final_x =container_bounds .x +config .padding_left +cross_pos_with_margin 
                final_y =container_bounds .y +config .padding_bottom +main_pos_with_margin 
                final_width =int (cross_component_size -constraints .margin_left -constraints .margin_right )
                final_height =int (info ['main_size']-constraints .margin_top -constraints .margin_bottom )


            if constraints .min_width :
                final_width =max (final_width ,constraints .min_width )
            if constraints .max_width :
                final_width =min (final_width ,constraints .max_width )
            if constraints .min_height :
                final_height =max (final_height ,constraints .min_height )
            if constraints .max_height :
                final_height =min (final_height ,constraints .max_height )


            comp .set_position (final_x ,final_y )
            comp .set_size (final_width ,final_height )


            current_main_pos +=info ['main_size']+config .gap 

    def _apply_stack_layout (self ,components :List [UIComponent ],container_bounds :Bounds ,
    config :LayoutConfig ):
        """Apply simple stack layout (vertical by default)."""
        current_y =container_bounds .y +config .padding_bottom 

        for comp in components :
            constraints =self .constraints .get (comp ,LayoutConstraints ())


            x =container_bounds .x +config .padding_left +constraints .margin_left 
            y =current_y +constraints .margin_top 
            width =(container_bounds .width -config .padding_left -config .padding_right -
            constraints .margin_left -constraints .margin_right )
            height =comp .bounds .height 


            if constraints .min_width :
                width =max (width ,constraints .min_width )
            if constraints .max_width :
                width =min (width ,constraints .max_width )
            if constraints .min_height :
                height =max (height ,constraints .min_height )
            if constraints .max_height :
                height =min (height ,constraints .max_height )

            comp .set_position (x ,y )
            comp .set_size (width ,height )

            current_y +=height +constraints .margin_top +constraints .margin_bottom +config .gap 

    def _apply_grid_layout (self ,components :List [UIComponent ],container_bounds :Bounds ,
    config :LayoutConfig ):
        """Apply grid layout positioning."""
        if not components :
            return 


        cols =config .grid_columns 
        rows =config .grid_rows or ((len (components )+cols -1 )//cols )


        available_width =container_bounds .width -config .padding_left -config .padding_right 
        available_height =container_bounds .height -config .padding_top -config .padding_bottom 

        cell_width =(available_width -config .grid_gap *(cols -1 ))//cols 
        cell_height =(available_height -config .grid_gap *(rows -1 ))//rows 


        for i ,comp in enumerate (components ):
            if i >=cols *rows :
                break 

            row =i //cols 
            col =i %cols 

            constraints =self .constraints .get (comp ,LayoutConstraints ())


            x =(container_bounds .x +config .padding_left +
            col *(cell_width +config .grid_gap )+constraints .margin_left )
            y =(container_bounds .y +config .padding_bottom +
            row *(cell_height +config .grid_gap )+constraints .margin_top )


            width =cell_width -constraints .margin_left -constraints .margin_right 
            height =cell_height -constraints .margin_top -constraints .margin_bottom 


            if constraints .min_width :
                width =max (width ,constraints .min_width )
            if constraints .max_width :
                width =min (width ,constraints .max_width )
            if constraints .min_height :
                height =max (height ,constraints .min_height )
            if constraints .max_height :
                height =min (height ,constraints .max_height )

            comp .set_position (x ,y )
            comp .set_size (width ,height )

    def _apply_absolute_layout (self ,components :List [UIComponent ],container_bounds :Bounds ,
    config :LayoutConfig ):
        """Apply absolute positioning based on constraints."""
        for comp in components :
            constraints =self .constraints .get (comp ,LayoutConstraints ())


            x =comp .bounds .x 
            y =comp .bounds .y 
            width =comp .bounds .width 
            height =comp .bounds .height 


            if constraints .left is not None and constraints .right is not None :

                x =container_bounds .x +constraints .left 
                width =container_bounds .width -constraints .left -constraints .right 
            elif constraints .left is not None :

                x =container_bounds .x +constraints .left 
            elif constraints .right is not None :

                x =container_bounds .x +container_bounds .width -constraints .right -width 


            if constraints .top is not None and constraints .bottom is not None :

                y =container_bounds .y +constraints .bottom 
                height =container_bounds .height -constraints .top -constraints .bottom 
            elif constraints .top is not None :

                y =container_bounds .y +container_bounds .height -constraints .top -height 
            elif constraints .bottom is not None :

                y =container_bounds .y +constraints .bottom 


            comp .set_position (x ,y )
            comp .set_size (width ,height )

    def _apply_anchor_layout (self ,components :List [UIComponent ],container_bounds :Bounds ,
    config :LayoutConfig ):
        """Apply anchor-based positioning (similar to CSS positioning)."""

        self ._apply_absolute_layout (components ,container_bounds ,config )



class LayoutPresets :
    """Common layout presets for quick setup."""

    @staticmethod 
    def vertical_stack (gap :int =5 ,padding :int =10 )->LayoutConfig :
        """Vertical stack layout."""
        return LayoutConfig (
        strategy =LayoutStrategy .FLEX_VERTICAL ,
        direction =FlexDirection .COLUMN ,
        justify_content =JustifyContent .START ,
        align_items =AlignItems .STRETCH ,
        gap =gap ,
        padding_top =padding ,
        padding_right =padding ,
        padding_bottom =padding ,
        padding_left =padding 
        )

    @staticmethod 
    def horizontal_stack (gap :int =5 ,padding :int =10 )->LayoutConfig :
        """Horizontal stack layout."""
        return LayoutConfig (
        strategy =LayoutStrategy .FLEX_HORIZONTAL ,
        direction =FlexDirection .ROW ,
        justify_content =JustifyContent .START ,
        align_items =AlignItems .CENTER ,
        gap =gap ,
        padding_top =padding ,
        padding_right =padding ,
        padding_bottom =padding ,
        padding_left =padding 
        )

    @staticmethod 
    def centered_content (padding :int =10 )->LayoutConfig :
        """Centered content layout."""
        return LayoutConfig (
        strategy =LayoutStrategy .FLEX_VERTICAL ,
        direction =FlexDirection .COLUMN ,
        justify_content =JustifyContent .CENTER ,
        align_items =AlignItems .CENTER ,
        gap =10 ,
        padding_top =padding ,
        padding_right =padding ,
        padding_bottom =padding ,
        padding_left =padding 
        )

    @staticmethod 
    def toolbar (gap :int =5 ,padding :int =5 )->LayoutConfig :
        """Toolbar layout with right alignment."""
        return LayoutConfig (
        strategy =LayoutStrategy .FLEX_HORIZONTAL ,
        direction =FlexDirection .ROW ,
        justify_content =JustifyContent .END ,
        align_items =AlignItems .CENTER ,
        gap =gap ,
        padding_top =padding ,
        padding_right =padding ,
        padding_bottom =padding ,
        padding_left =padding 
        )

    @staticmethod 
    def grid (columns :int =2 ,gap :int =5 ,padding :int =10 )->LayoutConfig :
        """Grid layout."""
        return LayoutConfig (
        strategy =LayoutStrategy .GRID ,
        grid_columns =columns ,
        grid_gap =gap ,
        padding_top =padding ,
        padding_right =padding ,
        padding_bottom =padding ,
        padding_left =padding 
        )



layout_manager =LayoutManager ()