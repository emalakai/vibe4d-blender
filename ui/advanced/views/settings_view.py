"""
Settings view for application configuration.
"""

import logging 
import bpy 
import gpu 
import threading 
from typing import Dict ,Any 

from .base_view import BaseView 
from ..layout_manager import LayoutConfig ,LayoutStrategy ,LayoutConstraints ,LayoutPresets 
from ..components import Label ,Button ,Container ,TextInput ,BackButton 
from ..components .scrollview import ScrollView ,ScrollDirection 
from ..components .image import ImageComponent ,ImageFit ,ImagePosition 
from ..components .base import Bounds 
from ..theme import get_themed_style 
from ..blender_theme_integration import get_theme_color 
from ..styles import FontSizes 
from ..unified_styles import Styles 
from ..coordinates import CoordinateSystem 

logger =logging .getLogger (__name__ )



def get_font_size ():
    return Styles .get_font_size ()

def get_title_font_size ():
    return Styles .get_font_size ("title")


def get_left_margin ():
    return Styles .get_left_margin ()

def get_right_margin ():
    return Styles .get_right_margin ()

def get_container_internal_padding ():
    return Styles .get_container_internal_padding ()

def get_scrollview_internal_margin ():
    return Styles .get_scrollview_internal_margin ()

def get_scrollview_content_padding ():
    return Styles .get_scrollview_content_padding ()


def get_big_spacing ():
    return Styles .get_big_spacing ()

def get_small_spacing ():
    return Styles .get_small_spacing ()

def get_medium_spacing ():
    return Styles .get_medium_spacing ()

def get_rule_spacing ():
    return Styles .get_rule_spacing ()

def get_link_spacing ():
    return Styles .get_link_spacing ()

def get_bottom_padding ():
    return Styles .get_bottom_padding ()


def get_button_height ():
    return Styles .get_button_height ()

def get_large_button_height ():
    return Styles .get_large_button_height ()

def get_small_button_height ():
    return Styles .get_small_button_height ()

def get_label_height ():
    return Styles .get_label_height ()

def get_small_label_height ():
    return Styles .get_small_label_height ()

def get_input_height ():
    return Styles .get_input_height ()

def get_toggle_button_size ():
    return Styles .get_toggle_button_size ()


def get_go_back_button_width ():
    return Styles .get_go_back_button_width ()

def get_name_label_width ():
    return Styles .get_name_label_width ()

def get_plan_label_width ():
    return Styles .get_plan_label_width ()

def get_manage_sub_label_width ():
    return Styles .get_manage_sub_label_width ()

def get_logout_button_width ():
    return Styles .get_logout_button_width ()

def get_add_button_width ():
    return Styles .get_add_button_width ()

def get_large_add_button_width ():
    return Styles .get_large_add_button_width ()

def get_toggle_button_width ():
    return Styles .get_toggle_button_width ()

def get_delete_button_width ():
    return Styles .get_delete_button_width ()

def get_rule_button_left_offset ():
    return Styles .get_rule_button_left_offset ()

def get_link_label_width ():
    return Styles .get_link_label_width ()


def get_info_container_height ():
    return Styles .get_info_container_height ()

def get_rules_container_height ():
    return Styles .get_rules_container_height ()

def get_rules_scrollview_height ():
    return Styles .get_rules_scrollview_height ()


def get_small_radius ():
    return Styles .get_small_radius ()

def get_medium_radius ():
    return Styles .get_medium_radius ()

def get_large_radius ():
    return Styles .get_large_radius ()

def get_extra_large_radius ():
    return Styles .get_extra_large_radius ()

def get_container_radius ():
    return Styles .get_container_radius ()


def get_scrollbar_width ():
    return Styles .get_scrollbar_width ()


def get_no_border ():
    return Styles .get_no_border ()

def get_thin_border ():
    return Styles .get_thin_border ()

def get_thick_border ():
    return Styles .get_thick_border ()


MAX_RULE_TEXT_LENGTH =Styles .MAX_RULE_TEXT_LENGTH 
TRUNCATION_SUFFIX =Styles .TRUNCATION_SUFFIX 


def get_rule_toggle_x_offset ():
    """Get the X offset for rule toggle buttons - uses dynamic spacing."""
    return get_container_internal_padding ()+get_small_spacing ()

def get_rule_text_x_offset ():
    return get_rule_toggle_x_offset ()+CoordinateSystem .scale_int (16 )


TRANSPARENT_COLOR =Styles .Transparent 
DARK_CONTAINER_COLOR =Styles .DarkContainer 
BORDER_COLOR =Styles .Border 
MUTED_TEXT_COLOR =Styles .MutedText 
DISABLED_TEXT_COLOR =Styles .DisabledText 
ENABLED_TEXT_COLOR =Styles .EnabledText 
WHITE_TEXT_COLOR =Styles .WhiteText 
LINK_COLOR =Styles .Link 
LINK_HOVER_COLOR =Styles .LinkHover 
LINK_HOVER_BG_COLOR =Styles .LinkHoverBg 
AUTH_MESSAGE_COLOR =Styles .AuthMessage 
PRIMARY_BUTTON_COLOR =Styles .PrimaryButton 
DISABLED_BUTTON_COLOR =Styles .DisabledButton 
LOGOUT_BUTTON_COLOR =Styles .LogoutButton 
LOGOUT_BUTTON_HOVER_COLOR =Styles .LogoutButtonHover 
DELETE_BUTTON_COLOR =Styles .DeleteButton 
DELETE_BUTTON_HOVER_COLOR =Styles .DeleteButtonHover 
HOVER_BACKGROUND_COLOR =Styles .HoverBackground 
EDITING_HIGHLIGHT_COLOR =Styles .EditingHighlight 
TOGGLE_ENABLED_COLOR =Styles .ToggleEnabled 
TOGGLE_DISABLED_COLOR =Styles .ToggleDisabled 
TOGGLE_FILL_COLOR =Styles .ToggleFill 
CHECKMARK_COLOR =Styles .Checkmark 


def adjustCurrectY (current_y :int ,height :int ,spacing :int )->int :
    return current_y -height -spacing 


def get_go_back_button_offset ():
    return Styles .get_go_back_button_offset ()

def get_go_back_button_side_padding ():
    return Styles .get_go_back_button_side_padding ()

class ToggleIconButton (Button ):
    """Button that displays toggle icons for enabled/disabled states."""

    def __init__ (self ,enabled :bool =True ,x :int =0 ,y :int =0 ,
    width :int =CoordinateSystem .scale_int (14 ),height :int =CoordinateSystem .scale_int (14 ),
    on_click =None ):
        super ().__init__ ("",x ,y ,width ,height ,corner_radius =0 ,on_click =on_click )

        self .enabled_state =enabled 
        self .visible =True 


        self .enabled_icon =ImageComponent (
        image_path ="toggle-filled.png",
        x =x ,
        y =y +(height -CoordinateSystem .scale_int (14 ))//2 ,
        width =CoordinateSystem .scale_int (14 ),
        height =CoordinateSystem .scale_int (14 ),
        )

        self .disabled_icon =ImageComponent (
        image_path ="toggle-outline.png",
        x =x ,
        y =y +(height -CoordinateSystem .scale_int (14 ))//2 ,
        width =CoordinateSystem .scale_int (14 ),
        height =CoordinateSystem .scale_int (14 ),
        )


        self .style .background_color =TRANSPARENT_COLOR 
        self .style .border_width =get_no_border ()
        self .style .hover_background_color =TRANSPARENT_COLOR 
        self .style .focus_background_color =TRANSPARENT_COLOR 
        self .style .pressed_background_color =TRANSPARENT_COLOR 


    def set_enabled_state (self ,enabled :bool ):
        """Set the enabled state of the toggle."""
        self .enabled_state =enabled 

    def set_position (self ,x :int ,y :int ):
        """Override to update icon positions as well."""
        super ().set_position (x ,y )

        icon_y =y +(self .bounds .height -CoordinateSystem .scale_int (14 ))//2 
        self .enabled_icon .set_position (x ,icon_y )
        self .disabled_icon .set_position (x ,icon_y )

    def set_size (self ,width :int ,height :int ):
        """Override to update icon sizes as well."""
        super ().set_size (width ,height )

        self .enabled_icon .set_size (CoordinateSystem .scale_int (14 ),CoordinateSystem .scale_int (14 ))
        self .disabled_icon .set_size (CoordinateSystem .scale_int (14 ),CoordinateSystem .scale_int (14 ))

        icon_y =self .bounds .y +(height -CoordinateSystem .scale_int (14 ))//2 
        self .enabled_icon .set_position (self .bounds .x ,icon_y )
        self .disabled_icon .set_position (self .bounds .x ,icon_y )

    def _render_simple_icon (self ,renderer ,enabled_state ):
        """Render a simple colored icon when texture loading fails."""

        bounds =self .bounds 


        border_color =TOGGLE_ENABLED_COLOR if enabled_state else TOGGLE_DISABLED_COLOR 
        fill_color =TOGGLE_FILL_COLOR if enabled_state else TRANSPARENT_COLOR 


        renderer .draw_rounded_rect (bounds ,border_color ,get_large_radius ())


        if enabled_state and fill_color [3 ]>0 :
            inner_bounds =Bounds (
            bounds .x +get_thick_border (),bounds .y +get_thick_border (),
            bounds .width -(get_thick_border ()*2 ),bounds .height -(get_thick_border ()*2 )
            )
            renderer .draw_rounded_rect (inner_bounds ,fill_color ,get_medium_radius ())


        if enabled_state :

            check_size =min (bounds .width ,bounds .height )//3 
            check_x =bounds .x +bounds .width //2 -check_size //2 
            check_y =bounds .y +bounds .height //2 -check_size //2 


            check_bounds =Bounds (check_x ,check_y ,check_size ,check_size //2 )
            renderer .draw_rect (check_bounds ,CHECKMARK_COLOR )

    def render (self ,renderer ):
        """Render the toggle button with appropriate icon."""
        if not self .visible :
            return 


        self ._update_pressed_state ()


        if self .is_hovered or self .is_pressed :
            if self .corner_radius >0 :
                renderer .draw_rounded_rect (self .bounds ,TRANSPARENT_COLOR ,self .corner_radius )
            else :
                renderer .draw_rect (self .bounds ,TRANSPARENT_COLOR )


        icon_y =self .bounds .y +(self .bounds .height -CoordinateSystem .scale_int (14 ))//2 
        self .enabled_icon .set_position (self .bounds .x ,icon_y )
        self .disabled_icon .set_position (self .bounds .x ,icon_y )


        current_icon =self .enabled_icon if self .enabled_state else self .disabled_icon 


        if not current_icon .image_loaded and current_icon ._texture_creation_attempted :
            current_icon ._texture_creation_attempted =False 


        if not current_icon .image_loaded and not current_icon ._texture_creation_attempted :

            if not current_icon .image_data :
                current_icon ._load_image_data ()

            is_valid =current_icon ._is_image_data_valid ()

            if is_valid :
                try :

                    success =self ._create_texture_with_fallback (current_icon )
                    if success :
                        current_icon ._texture_creation_attempted =True 
                    else :
                        logger .error (f"All fallback methods failed for {current_icon.image_path}")
                        current_icon ._texture_creation_attempted =True 
                except Exception as e :
                    logger .error (f"Exception during fallback texture creation for {current_icon.image_path}: {e}")
                    current_icon ._texture_creation_attempted =True 
            else :
                logger .warning (f"Image data not valid for {current_icon.image_path}, skipping texture creation")
                current_icon ._texture_creation_attempted =True 


        if current_icon .image_loaded and current_icon .image_texture :
            try :

                render_bounds =current_icon .bounds 
                texture_coords =(0.0 ,0.0 ,1.0 ,1.0 )


                renderer .draw_textured_rect (
                x =render_bounds .x ,
                y =render_bounds .y ,
                width =render_bounds .width ,
                height =render_bounds .height ,
                texture =current_icon .image_texture ,
                texture_coords =texture_coords 
                )
            except Exception as e :
                logger .error (f"Error rendering texture for {current_icon.image_path}: {e}")

                self ._render_simple_icon (renderer ,self .enabled_state )
        else :

            self ._render_simple_icon (renderer ,self .enabled_state )

    def cleanup (self ):
        """Clean up resources when button is destroyed."""
        if self .enabled_icon :
            self .enabled_icon .cleanup ()
        if self .disabled_icon :
            self .disabled_icon .cleanup ()

    def _create_texture_with_fallback (self ,icon_component ):
        """Create GPU texture with fallback formats in case RGBA32F isn't supported."""
        if not icon_component ._is_image_data_valid ():
            logger .warning (f"Image data not valid for {icon_component.image_path}")
            return False 

        try :
            import array 

            width =icon_component .image_data .size [0 ]
            height =icon_component .image_data .size [1 ]


            pixel_data =list (icon_component .image_data .pixels )


            if icon_component .tint_color :
                tinted_pixels =[]
                for i in range (0 ,len (pixel_data ),4 ):
                    r ,g ,b ,a =pixel_data [i :i +4 ]
                    tinted_pixels .extend ([
                    r *icon_component .tint_color [0 ],
                    g *icon_component .tint_color [1 ],
                    b *icon_component .tint_color [2 ],
                    a *icon_component .tint_color [3 ]
                    ])
                pixel_data =tinted_pixels 


            if icon_component .opacity <1.0 :
                for i in range (3 ,len (pixel_data ),4 ):
                    pixel_data [i ]*=icon_component .opacity 


            formats_to_try =[
            ('RGBA32F','float'),
            ]

            for format_name ,data_type in formats_to_try :
                try :
                    if data_type =='float':

                        pixel_buffer =array .array ('f',pixel_data )
                        gpu_buffer =gpu .types .Buffer ('FLOAT',len (pixel_buffer ),pixel_buffer )
                    else :

                        byte_data =[int (max (0 ,min (255 ,p *255 )))for p in pixel_data ]
                        pixel_buffer =array .array ('B',byte_data )
                        gpu_buffer =gpu .types .Buffer ('UBYTE',len (pixel_buffer ),pixel_buffer )


                    texture =gpu .types .GPUTexture (
                    size =(width ,height ),
                    format =format_name ,
                    data =gpu_buffer 
                    )


                    if texture :
                        icon_component .image_texture =texture 
                        icon_component .image_loaded =True 
                        return True 
                    else :
                        logger .warning (f"Texture creation returned None for format {format_name}")
                        continue 

                except Exception as format_error :
                    logger .warning (f"Failed to create texture with format {format_name} for {icon_component.image_path}: {format_error}")
                    continue 


            logger .error (f"All texture formats failed for {icon_component.image_path}")
            return False 

        except Exception as e :
            logger .error (f"Error in texture creation fallback for {icon_component.image_path}: {e}")
            import traceback 
            logger .error (f"Traceback: {traceback.format_exc()}")
            return False 

class SettingsView (BaseView ):
    """Settings view for application configuration."""

    def __init__ (self ):
        super ().__init__ ()
        self .new_rule_text =""
        self .editing_rule_index =-1 
        self .refresh_callback =None 
        self .last_input_text =""
        self .is_fetching_usage =False 
        self .usage_data_fetched =False 

    def create_layout (self ,viewport_width :int ,viewport_height :int )->Dict [str ,Any ]:
        """Create the settings view layout."""
        layouts ={}
        components ={}


        context =bpy .context 
        is_authenticated =getattr (context .window_manager ,'vibe4d_authenticated',False )
        user_email =getattr (context .window_manager ,'vibe4d_user_email','')
        user_plan =getattr (context .window_manager ,'vibe4d_user_plan','')


        current_usage =getattr (context .window_manager ,'vibe4d_current_usage',0 )
        usage_limit =getattr (context .window_manager ,'vibe4d_usage_limit',100 )


        if is_authenticated and not self .usage_data_fetched and not self .is_fetching_usage :
            self .usage_data_fetched =True 
            self ._fetch_usage_data_async ()


        main_layout =self ._create_layout_container (
        "main",
        LayoutConfig (
        strategy =LayoutStrategy .ABSOLUTE ,
        padding_top =get_container_internal_padding (),
        padding_right =get_container_internal_padding (),
        padding_bottom =get_container_internal_padding (),
        padding_left =get_container_internal_padding ()
        )
        )
        layouts ['main']=main_layout 


        side_padding =get_go_back_button_side_padding ()
        top_offset =get_go_back_button_offset ()

        go_back_button =BackButton (side_padding ,0 ,on_click =self ._handle_go_back )

        button_y =viewport_height -top_offset -go_back_button .bounds .height 
        go_back_button .set_position (side_padding ,button_y )
        components ['go_back_button']=go_back_button 


        content_start_y =button_y -get_small_spacing ()
        current_y =content_start_y 

        if is_authenticated and user_email :

            user_name =user_email .split ('@')[0 ]if '@'in user_email else user_email 


            name_label =Label (user_name ,get_left_margin (),current_y ,get_name_label_width (),get_label_height ())
            name_label .style =get_themed_style ("title")
            name_label .style .font_size =get_font_size ()
            name_label .set_text_align ("left")
            components ['name_label']=name_label 

            current_y =adjustCurrectY (current_y ,get_label_height (),CoordinateSystem .scale_int (6 ))



            plan_name =getattr (context .window_manager ,'vibe4d_plan_name','')
            if plan_name :
                plan_display =plan_name 
            else :
                plan_display =user_plan .title ()if user_plan else "Free"
            plan_text =f"Plan: {plan_display}"
            plan_label =Label (plan_text ,get_left_margin (),current_y ,get_plan_label_width (),get_label_height ())
            plan_label .style =get_themed_style ("label")
            plan_label .style .font_size =get_font_size ()
            plan_label .style .text_color =MUTED_TEXT_COLOR 
            plan_label .set_text_align ("left")
            components ['plan_label']=plan_label 

            current_y =adjustCurrectY (current_y ,get_label_height (),CoordinateSystem .scale_int (8 ))


            info_container =Container (get_left_margin (),current_y -get_info_container_height (),
            viewport_width -get_left_margin ()-get_right_margin (),get_info_container_height ())
            info_container .style .background_color =DARK_CONTAINER_COLOR 
            info_container .style .border_color =BORDER_COLOR 
            info_container .style .border_width =get_thin_border ()
            info_container .corner_radius =get_container_radius ()
            components ['info_container']=info_container 


            info_current_y =current_y -get_container_internal_padding ()


            email_label =Label (user_email ,get_left_margin ()+get_container_internal_padding (),info_current_y ,
            viewport_width -get_left_margin ()-get_right_margin ()-(get_container_internal_padding ()*2 ),get_small_label_height ())
            email_label .style =get_themed_style ("label")
            email_label .style .font_size =get_font_size ()
            email_label .set_text_align ("left")
            components ['email_label']=email_label 

            info_current_y =adjustCurrectY (info_current_y ,get_small_label_height (),CoordinateSystem .scale_int (8 ))



            if current_usage ==0 and usage_limit ==0 :
                usage_text ="Usages left: loading..."
            else :
                usage_text =f"Usages left: {usage_limit-current_usage}/{usage_limit}"
            usage_label =Label (usage_text ,get_left_margin ()+get_container_internal_padding (),info_current_y ,
            viewport_width -get_left_margin ()-get_right_margin ()-(get_container_internal_padding ()*2 ),get_small_label_height ())
            usage_label .style =get_themed_style ("label")
            usage_label .style .font_size =get_font_size ()
            usage_label .set_text_align ("left")
            components ['usage_label']=usage_label 

            info_current_y =adjustCurrectY (info_current_y ,get_small_label_height (),CoordinateSystem .scale_int (8 ))


            manage_sub_label =Label ("Manage subscription ↗",get_left_margin ()+get_container_internal_padding (),info_current_y ,
            get_manage_sub_label_width (),get_small_label_height ())
            manage_sub_label .style =get_themed_style ("label")
            manage_sub_label .style .text_color =get_theme_color ('text_muted')
            manage_sub_label .style .font_size =get_font_size ()
            manage_sub_label .set_text_align ("left")
            manage_sub_label .add_text_segment (
            0 ,len ("Manage subscription ↗"),
            hover_style_name ="link_hover",
            clickable =True ,
            hoverable =True ,
            on_click =self ._handle_manage_subscription ,
            on_hover_start =self ._handle_link_hover_start ,
            on_hover_end =self ._handle_link_hover_end 
            )
            manage_sub_label .add_highlight_style ("link_hover",
            background_color =LINK_HOVER_BG_COLOR ,
            text_color =get_theme_color ('text_selected'))
            components ['manage_sub_label']=manage_sub_label 

            info_current_y =adjustCurrectY (info_current_y ,get_small_label_height (),CoordinateSystem .scale_int (8 ))


            logout_button =Button ("Log out",get_left_margin ()+get_container_internal_padding (),info_current_y ,
            get_logout_button_width (),get_large_button_height (),
            corner_radius =get_extra_large_radius (),on_click =self ._handle_logout )
            logout_button .style .background_color =LOGOUT_BUTTON_COLOR 
            logout_button .style .text_color =ENABLED_TEXT_COLOR 
            logout_button .style .hover_background_color =LOGOUT_BUTTON_HOVER_COLOR 
            logout_button .style .font_size =get_font_size ()
            components ['logout_button']=logout_button 

            current_y =adjustCurrectY (current_y ,get_info_container_height (),get_big_spacing ())


            rules_section_title =Label ("Custom rules",get_left_margin (),current_y ,get_plan_label_width (),get_label_height ())
            rules_section_title .style =get_themed_style ("title")
            rules_section_title .style .font_size =get_font_size ()
            rules_section_title .set_text_align ("left")
            components ['rules_section_title']=rules_section_title 

            current_y =adjustCurrectY (current_y ,get_label_height (),get_small_spacing ())


            rules_container =Container (get_left_margin (),current_y -get_rules_container_height (),
            viewport_width -get_left_margin ()-get_right_margin (),get_rules_container_height ())
            rules_container .style .background_color =DARK_CONTAINER_COLOR 
            rules_container .style .border_color =BORDER_COLOR 
            rules_container .style .border_width =get_thin_border ()
            rules_container .corner_radius =get_container_radius ()
            components ['rules_container']=rules_container 


            rules_current_y =current_y -get_container_internal_padding ()


            if self .editing_rule_index >=0 :
                instructions =getattr (context .scene ,'vibe4d_custom_instructions',[])
                if self .editing_rule_index <len (instructions ):
                    input_text =instructions [self .editing_rule_index ].text 
                    placeholder ="Edit rule..."
                else :
                    input_text =""
                    placeholder ="Edit rule..."
            else :
                input_text =self .new_rule_text 
                placeholder ="Type new rule..."

            rule_input =TextInput (x =get_left_margin ()+get_container_internal_padding (),y =rules_current_y ,
            width =viewport_width -get_left_margin ()-get_right_margin ()-CoordinateSystem .scale_int (60 )-(get_container_internal_padding ()*2 )-get_small_spacing (),
            height =get_input_height (),placeholder =placeholder ,multiline =False ,auto_resize =False )
            rule_input .set_text (input_text )
            rule_input .on_submit =self ._handle_rule_input_enter 
            rule_input .style =get_themed_style ("input")
            rule_input .style .font_size =get_font_size ()

            rule_input .style .background_color =Styles .Transparent 
            rule_input .style .border_color =Styles .Transparent 
            rule_input .style .border_width =0 
            rule_input .style .focus_background_color =Styles .Transparent 
            rule_input .style .focus_border_color =Styles .Transparent 
            rule_input .style .focus_border_width =0 
            rule_input .corner_radius =0 
            components ['rule_input']=rule_input 


            bottom_border =Container (
            get_left_margin ()+get_container_internal_padding (),
            rules_current_y ,
            viewport_width -get_left_margin ()-get_right_margin ()-CoordinateSystem .scale_int (60 )-(get_container_internal_padding ()*2 )-get_small_spacing (),
            1 
            )
            bottom_border .style .background_color =Styles .Border 
            bottom_border .style .border_width =0 
            components ['rule_input_border']=bottom_border 


            done_button =Button ("Done"if self .editing_rule_index <0 else "Save",
            viewport_width -CoordinateSystem .scale_int (60 )-get_right_margin (),rules_current_y ,CoordinateSystem .scale_int (60 ),get_input_height (),
            corner_radius =0 ,on_click =self ._handle_add_rule )
            done_button .style .background_color =Styles .Transparent 
            done_button .style .hover_background_color =TRANSPARENT_COLOR 
            done_button .style .focus_background_color =TRANSPARENT_COLOR 
            done_button .style .pressed_background_color =TRANSPARENT_COLOR 
            done_button .style .text_color =Styles .TextMuted 
            done_button .style .focus_text_color =Styles .TextSelected 
            done_button .style .font_size =get_font_size ()
            done_button .style .border_width =0 
            components ['done_button']=done_button 

            if not input_text .strip ():
                done_button .style .text_color =Styles .DisabledText 

            rules_current_y =adjustCurrectY (rules_current_y ,get_input_height (),get_small_spacing ())


            rules_scrollview =ScrollView (
            get_left_margin ()+get_scrollview_internal_margin (),
            rules_current_y -get_rules_scrollview_height (),
            viewport_width -get_left_margin ()-get_right_margin ()-get_scrollview_content_padding (),
            get_rules_scrollview_height (),
            scroll_direction =ScrollDirection .VERTICAL ,
            reverse_y_coordinate =True ,
            show_scrollbars =True ,
            scrollbar_width =get_scrollbar_width ()
            )
            rules_scrollview .style .background_color =TRANSPARENT_COLOR 
            rules_scrollview .style .border_color =TRANSPARENT_COLOR 
            rules_scrollview .style .border_width =get_no_border ()
            components ['rules_scrollview']=rules_scrollview 


            instructions =getattr (context .scene ,'vibe4d_custom_instructions',[])

            rule_y =0 


            for i in reversed (range (len (instructions ))):
                instruction =instructions [i ]
                if instruction .text :

                    toggle_button =ToggleIconButton (
                    enabled =instruction .enabled ,
                    x =get_rule_toggle_x_offset (),y =rule_y +CoordinateSystem .scale_int (3 ),width =CoordinateSystem .scale_int (14 ),height =CoordinateSystem .scale_int (14 ),
                    on_click =lambda idx =i :self ._handle_toggle_rule (idx )
                    )
                    rules_scrollview .add_child (toggle_button )



                    rule_text =instruction .text [:MAX_RULE_TEXT_LENGTH ]+TRUNCATION_SUFFIX if len (instruction .text )>MAX_RULE_TEXT_LENGTH else instruction .text 
                    rule_button =Button (rule_text ,get_rule_text_x_offset (),rule_y ,
                    rules_scrollview .bounds .width -get_rule_text_x_offset ()-get_delete_button_width ()-CoordinateSystem .scale_int (6 ),get_small_button_height (),
                    corner_radius =get_small_radius (),on_click =lambda idx =i :self ._handle_edit_rule (idx ))
                    rule_button .style .background_color =TRANSPARENT_COLOR 
                    rule_button .style .text_color =ENABLED_TEXT_COLOR if instruction .enabled else DISABLED_TEXT_COLOR 
                    rule_button .style .font_size =get_font_size ()
                    rule_button .style .hover_background_color =TRANSPARENT_COLOR 
                    rule_button .style .focus_background_color =TRANSPARENT_COLOR 
                    rule_button .style .pressed_background_color =TRANSPARENT_COLOR 
                    rule_button .style .border_width =get_no_border ()
                    rule_button .set_text_align ("left")


                    if i ==self .editing_rule_index :
                        rule_button .style .background_color =EDITING_HIGHLIGHT_COLOR 

                    rules_scrollview .add_child (rule_button )



                    delete_button =Button ("×",rules_scrollview .bounds .width -get_delete_button_width (),rule_y ,
                    get_delete_button_width (),get_small_button_height (),
                    corner_radius =get_small_radius (),on_click =lambda idx =i :self ._handle_delete_rule (idx ))
                    delete_button .style .background_color =TRANSPARENT_COLOR 
                    delete_button .style .text_color =WHITE_TEXT_COLOR 
                    delete_button .style .hover_background_color =DELETE_BUTTON_HOVER_COLOR 
                    delete_button .style .font_size =get_font_size ()
                    delete_button .style .border_width =get_no_border ()
                    rules_scrollview .add_child (delete_button )


                    rule_y +=get_rule_spacing ()


            if instructions :

                spacer =Container (0 ,rule_y ,rules_scrollview .bounds .width ,get_bottom_padding ())
                spacer .visible =False 
                spacer .style .background_color =TRANSPARENT_COLOR 
                rules_scrollview .add_child (spacer )


            rules_scrollview ._update_content_bounds ()


            rules_scrollview .scroll_to_top ()

            current_y =adjustCurrectY (current_y ,get_rules_container_height (),get_big_spacing ())
        else :
            auth_message =Label ("Please authenticate to access settings",get_left_margin (),current_y ,
            viewport_width -get_left_margin ()-get_right_margin (),get_label_height ())
            auth_message .style =get_themed_style ("label")
            auth_message .style .text_color =AUTH_MESSAGE_COLOR 
            auth_message .style .font_size =get_font_size ()
            auth_message .set_text_align ("left")
            components ['auth_message']=auth_message 
            current_y =adjustCurrectY (current_y ,get_label_height (),get_big_spacing ())


        links_section_title =Label ("Vibe4D links",get_left_margin (),current_y ,get_plan_label_width (),get_label_height ())
        links_section_title .style =get_themed_style ("title")
        links_section_title .style .font_size =get_font_size ()
        links_section_title .set_text_align ("left")
        components ['links_section_title']=links_section_title 

        current_y =adjustCurrectY (current_y ,get_label_height (),get_small_spacing ())

        links =[
        ("Github ↗",self ._handle_open_github ),
        ("Website ↗",self ._handle_open_website ),
        ("Twitter (X) ↗",self ._handle_open_twitter ),
        ("Discord ↗",self ._handle_open_discord )
        ]

        for i ,(link_text ,handler )in enumerate (links ):
            link_label =Label (link_text ,get_left_margin (),current_y ,get_link_label_width (),get_small_label_height ())
            link_label .style =get_themed_style ("label")
            link_label .style .text_color =get_theme_color ('text_muted')
            link_label .style .font_size =get_font_size ()
            link_label .set_text_align ("left")
            link_label .add_text_segment (
            0 ,len (link_text ),
            hover_style_name ="link_hover",
            clickable =True ,
            hoverable =True ,
            on_click =handler ,
            on_hover_start =self ._handle_link_hover_start ,
            on_hover_end =self ._handle_link_hover_end 
            )
            link_label .add_highlight_style ("link_hover",
            background_color =TRANSPARENT_COLOR ,
            text_color =get_theme_color ('text_selected'))
            components [f'link_{i}']=link_label 
            current_y =adjustCurrectY (current_y ,get_small_label_height (),get_link_spacing ())

        self .components =components 
        self .layouts =layouts 

        return {
        'layouts':layouts ,
        'components':components ,
        'all_components':self ._get_all_components ()
        }

    def update_layout (self ,viewport_width :int ,viewport_height :int ):
        """Update layout positions when viewport changes."""


        self ._check_input_changes ()


        if 'go_back_button'in self .components :
            go_back_button =self .components ['go_back_button']
            side_padding =get_go_back_button_side_padding ()
            top_offset =get_go_back_button_offset ()
            button_y =viewport_height -top_offset -go_back_button .bounds .height 
            go_back_button .set_position (side_padding ,button_y )


            content_start_y =button_y -get_small_spacing ()
            current_y =content_start_y 
        else :
            current_y =viewport_height 

        current_y -=get_big_spacing ()

        if 'name_label'in self .components :
            self .components ['name_label'].set_position (get_left_margin (),current_y )
            self .components ['name_label'].set_size (get_name_label_width (),get_label_height ())

        current_y =adjustCurrectY (current_y ,get_label_height (),CoordinateSystem .scale_int (6 ))

        if 'plan_label'in self .components :
            self .components ['plan_label'].set_position (get_left_margin (),current_y )
            self .components ['plan_label'].set_size (get_plan_label_width (),get_label_height ())

        current_y =adjustCurrectY (current_y ,get_label_height (),CoordinateSystem .scale_int (-4 ))


        if 'info_container'in self .components :
            self .components ['info_container'].set_position (get_left_margin (),current_y -get_info_container_height ())
            self .components ['info_container'].set_size (viewport_width -get_left_margin ()-get_right_margin (),get_info_container_height ())


        info_current_y =current_y -get_container_internal_padding ()-CoordinateSystem .scale_int (12 )

        if 'email_label'in self .components :
            self .components ['email_label'].set_position (get_left_margin ()+get_container_internal_padding (),info_current_y )
            self .components ['email_label'].set_size (viewport_width -get_left_margin ()-get_right_margin ()-(get_container_internal_padding ()*2 ),get_small_label_height ())

        info_current_y =adjustCurrectY (info_current_y ,get_small_label_height (),CoordinateSystem .scale_int (8 ))

        if 'usage_label'in self .components :
            self .components ['usage_label'].set_position (get_left_margin ()+get_container_internal_padding (),info_current_y )
            self .components ['usage_label'].set_size (viewport_width -get_left_margin ()-get_right_margin ()-(get_container_internal_padding ()*2 ),get_small_label_height ())

        info_current_y =adjustCurrectY (info_current_y ,get_small_label_height (),CoordinateSystem .scale_int (8 ))

        if 'manage_sub_label'in self .components :
            self .components ['manage_sub_label'].set_position (get_left_margin ()+get_container_internal_padding (),info_current_y )
            self .components ['manage_sub_label'].set_size (viewport_width -get_left_margin ()-get_right_margin ()-(get_container_internal_padding ()*2 ),get_small_label_height ())

        info_current_y =adjustCurrectY (info_current_y ,get_small_label_height ()+CoordinateSystem .scale_int (12 ),CoordinateSystem .scale_int (8 ))

        if 'logout_button'in self .components :
            self .components ['logout_button'].set_position (get_left_margin ()+get_container_internal_padding (),info_current_y )
            self .components ['logout_button'].set_size (get_logout_button_width (),get_small_button_height ())

        current_y =adjustCurrectY (current_y ,get_info_container_height ()+CoordinateSystem .scale_int (12 ),get_big_spacing ())


        if 'rules_section_title'in self .components :
            self .components ['rules_section_title'].set_position (get_left_margin (),current_y )
            self .components ['rules_section_title'].set_size (get_plan_label_width (),get_label_height ())

        current_y =adjustCurrectY (current_y ,get_label_height ()-CoordinateSystem .scale_int (12 ),get_small_spacing ())


        if 'rules_container'in self .components :
            self .components ['rules_container'].set_position (get_left_margin (),current_y -get_rules_container_height ())
            self .components ['rules_container'].set_size (viewport_width -get_left_margin ()-get_right_margin (),get_rules_container_height ())


        rules_current_y =current_y -get_container_internal_padding ()-CoordinateSystem .scale_int (30 )


        if 'rule_input'in self .components :
            self .components ['rule_input'].set_position (get_left_margin ()+get_container_internal_padding (),rules_current_y )
            self .components ['rule_input'].set_size (viewport_width -get_left_margin ()-get_right_margin ()-CoordinateSystem .scale_int (60 )-get_small_spacing ()-get_container_internal_padding (),get_input_height ())

        if 'rule_input_border'in self .components :
            self .components ['rule_input_border'].set_position (get_left_margin ()+get_container_internal_padding (),rules_current_y )
            self .components ['rule_input_border'].set_size (viewport_width -get_left_margin ()-get_right_margin ()-CoordinateSystem .scale_int (60 )-get_small_spacing ()-get_container_internal_padding (),1 )

        if 'done_button'in self .components :
            self .components ['done_button'].set_size (CoordinateSystem .scale_int (60 ),get_input_height ())
            self .components ['done_button'].set_position (viewport_width -CoordinateSystem .scale_int (60 )-get_right_margin ()-get_container_internal_padding (),rules_current_y )

        rules_current_y =adjustCurrectY (rules_current_y ,get_input_height (),get_small_spacing ())


        if 'rules_scrollview'in self .components :
            self .components ['rules_scrollview'].set_position (get_left_margin (),rules_current_y -get_rules_scrollview_height ()/1.5 )
            self .components ['rules_scrollview'].set_size (viewport_width -get_left_margin ()-get_right_margin (),get_rules_scrollview_height ())

            self .components ['rules_scrollview']._update_content_bounds ()

        current_y =adjustCurrectY (current_y ,get_rules_container_height ()+CoordinateSystem .scale_int (12 ),get_big_spacing ())


        if 'links_section_title'in self .components :
            self .components ['links_section_title'].set_position (get_left_margin (),current_y )
            self .components ['links_section_title'].set_size (get_plan_label_width (),get_label_height ())

        current_y =adjustCurrectY (current_y ,get_label_height (),get_small_spacing ())


        for i in range (4 ):
            if f'link_{i}'in self .components :
                self .components [f'link_{i}'].set_position (get_left_margin (),current_y )
                current_y =adjustCurrectY (current_y ,get_small_label_height (),get_link_spacing ())

    def _handle_go_back (self ):
        """Handle go back button click - return to main view."""
        if self .callbacks .get ('on_go_back'):
            self .callbacks ['on_go_back']()
        else :

            if self .callbacks .get ('on_view_change'):
                from ..ui_factory import ViewState 
                self .callbacks ['on_view_change'](ViewState .MAIN )

    def _handle_manage_subscription (self ,segment ):
        """Handle manage subscription click."""
        try :
            bpy .ops .vibe4d .manage_subscription ()
        except Exception as e :
            logger .error (f"Error opening subscription management: {e}")

    def _handle_logout (self ):
        """Handle logout button click."""
        try :
            bpy .ops .vibe4d .logout ()

            if self .callbacks .get ('on_view_change'):
                from ..ui_factory import ViewState 
                self .callbacks ['on_view_change'](ViewState .AUTH )
        except Exception as e :
            logger .error (f"Error during logout: {e}")

    def _handle_rule_input_enter (self ):
        """Handle enter key in text input."""
        if 'rule_input'in self .components :
            text =self .components ['rule_input'].get_text ().strip ()
            if text :
                self ._handle_add_rule ()
            else :

                if self .editing_rule_index >=0 :
                    self .editing_rule_index =-1 
                    self ._update_ui_instantly ()

    def _cancel_editing (self ):
        """Cancel current editing mode."""
        if self .editing_rule_index >=0 :
            self .editing_rule_index =-1 
            self .new_rule_text =""
            if 'rule_input'in self .components :
                self .components ['rule_input'].set_text ("")

                self .last_input_text =""
            self ._update_ui_instantly ()
            logger .info ("Editing cancelled")

    def _handle_add_rule (self ):
        """Handle add/save rule button click."""
        try :
            context =bpy .context 
            instructions =getattr (context .scene ,'vibe4d_custom_instructions',[])

            if self .editing_rule_index >=0 :

                if 'rule_input'in self .components :
                    new_text =self .components ['rule_input'].get_text ().strip ()
                    if new_text and self .editing_rule_index <len (instructions ):
                        instructions [self .editing_rule_index ].text =new_text 
                        logger .info (f"Updated rule {self.editing_rule_index}: {new_text}")


                        from ....utils .instructions_manager import instructions_manager 
                        instructions_manager .auto_save_instructions (context )


                        self .editing_rule_index =-1 
                        self .new_rule_text =""
                        if 'rule_input'in self .components :
                            self .components ['rule_input'].set_text ("")

                            self .last_input_text =""
                        self ._update_ui_instantly ()

            else :

                if 'rule_input'in self .components :
                    new_text =self .components ['rule_input'].get_text ().strip ()
                else :
                    new_text =self .new_rule_text .strip ()

                if new_text :

                    new_instruction =instructions .add ()
                    new_instruction .text =new_text 
                    new_instruction .enabled =True 

                    logger .info (f"Added new rule: {new_text}")


                    from ....utils .instructions_manager import instructions_manager 
                    instructions_manager .auto_save_instructions (context )


                    self .new_rule_text =""
                    if 'rule_input'in self .components :
                        self .components ['rule_input'].set_text ("")

                        self .last_input_text =""

                    self ._update_ui_instantly ()


                    if 'rules_scrollview'in self .components :
                        self .components ['rules_scrollview'].scroll_to_top ()

        except Exception as e :
            logger .error (f"Error adding/saving rule: {e}")

    def _update_ui_instantly (self ):
        """Update UI components instantly without full refresh."""
        try :
            context =bpy .context 
            instructions =getattr (context .scene ,'vibe4d_custom_instructions',[])


            if 'rule_input'in self .components :
                if self .editing_rule_index >=0 :

                    if self .editing_rule_index <len (instructions ):
                        self .components ['rule_input'].set_text (instructions [self .editing_rule_index ].text )
                        self .components ['rule_input'].placeholder ="Edit rule..."
                    else :
                        self .editing_rule_index =-1 
                        self .components ['rule_input'].set_text ("")
                        self .components ['rule_input'].placeholder ="Type new rule..."
                else :

                    self .components ['rule_input'].set_text (self .new_rule_text )
                    self .components ['rule_input'].placeholder ="Type new rule..."


            if 'done_button'in self .components :
                button_text ="Save"if self .editing_rule_index >=0 else "Done"
                self .components ['done_button'].text =button_text 


                current_text =self ._get_current_rule_text ().strip ()
                if current_text :
                    self .components ['done_button'].style .text_color =Styles .TextMuted 
                else :
                    self .components ['done_button'].style .text_color =Styles .DisabledText 


            if 'rules_scrollview'in self .components :
                scrollview =self .components ['rules_scrollview']


                current_scroll_y =scrollview .scroll_y 


                scrollview .clear_children ()


                comp_names_to_remove =[]
                for comp_name in self .components :
                    if (comp_name .startswith ('toggle_')or 
                    comp_name .startswith ('rule_')or 
                    comp_name .startswith ('delete_')):
                        comp_names_to_remove .append (comp_name )

                for comp_name in comp_names_to_remove :
                    del self .components [comp_name ]


                rule_y =0 


                for i in reversed (range (len (instructions ))):
                    instruction =instructions [i ]
                    if instruction .text :

                        toggle_button =ToggleIconButton (
                        enabled =instruction .enabled ,
                        x =get_rule_toggle_x_offset (),y =rule_y +CoordinateSystem .scale_int (3 ),width =CoordinateSystem .scale_int (14 ),height =CoordinateSystem .scale_int (14 ),
                        on_click =lambda idx =i :self ._handle_toggle_rule (idx )
                        )
                        scrollview .add_child (toggle_button )



                        rule_text =instruction .text [:MAX_RULE_TEXT_LENGTH ]+TRUNCATION_SUFFIX if len (instruction .text )>MAX_RULE_TEXT_LENGTH else instruction .text 
                        rule_button =Button (rule_text ,get_rule_text_x_offset (),rule_y ,
                        scrollview .bounds .width -get_rule_text_x_offset ()-get_delete_button_width ()-6 ,get_small_button_height (),
                        corner_radius =get_small_radius (),on_click =lambda idx =i :self ._handle_edit_rule (idx ))
                        rule_button .style .background_color =TRANSPARENT_COLOR 
                        rule_button .style .text_color =ENABLED_TEXT_COLOR if instruction .enabled else DISABLED_TEXT_COLOR 
                        rule_button .style .font_size =get_font_size ()
                        rule_button .style .hover_background_color =TRANSPARENT_COLOR 
                        rule_button .style .border_width =get_no_border ()
                        rule_button .set_text_align ("left")


                        if i ==self .editing_rule_index :
                            rule_button .style .background_color =EDITING_HIGHLIGHT_COLOR 

                        scrollview .add_child (rule_button )



                        delete_button =Button ("×",scrollview .bounds .width -get_delete_button_width (),rule_y ,
                        get_delete_button_width (),get_small_button_height (),
                        corner_radius =get_small_radius (),on_click =lambda idx =i :self ._handle_delete_rule (idx ))
                        delete_button .style .background_color =TRANSPARENT_COLOR 
                        delete_button .style .text_color =WHITE_TEXT_COLOR 
                        delete_button .style .hover_background_color =DELETE_BUTTON_HOVER_COLOR 
                        delete_button .style .font_size =get_font_size ()
                        delete_button .style .border_width =get_no_border ()
                        scrollview .add_child (delete_button )


                        rule_y +=get_rule_spacing ()


                if instructions :

                    spacer =Container (0 ,rule_y ,scrollview .bounds .width ,get_bottom_padding ())
                    spacer .visible =False 
                    spacer .style .background_color =TRANSPARENT_COLOR 
                    scrollview .add_child (spacer )


                scrollview ._update_content_bounds ()


                scrollview .scroll_to_top ()


            self ._notify_ui_system_of_changes ()


            self ._force_redraw ()

            logger .info (f"UI updated instantly with {len(instructions)} rules")

        except Exception as e :
            logger .error (f"Error updating UI instantly: {e}")

    def _notify_ui_system_of_changes (self ):
        """Notify the UI system that components have changed."""
        try :

            from ..components .component_registry import component_registry 
            component_registry .process_updates ()


            if self .refresh_callback :
                self .refresh_callback ()
                logger .debug ("Triggered view refresh via callback")
                return 


            from ..ui_factory import improved_ui_factory 
            if improved_ui_factory and hasattr (improved_ui_factory ,'_refresh_current_view'):
                improved_ui_factory ._refresh_current_view ()
                logger .debug ("Triggered UI factory refresh")
                return 


            from ..manager import ui_manager 
            if ui_manager and hasattr (ui_manager ,'state'):

                for component in ui_manager .state .components :
                    if hasattr (component ,'_render_dirty'):
                        component ._render_dirty =True 

                logger .debug ("Marked UI components as dirty")

        except Exception as e :
            logger .debug (f"Could not notify UI system: {e}")

    def _force_redraw (self ):
        """Force immediate redraw of the viewport."""
        try :

            for window in bpy .context .window_manager .windows :
                for area in window .screen .areas :
                    area .tag_redraw ()


            if hasattr (bpy .context ,'area')and bpy .context .area :
                bpy .context .area .tag_redraw ()


            if hasattr (bpy .ops .wm ,'redraw_timer'):
                bpy .ops .wm .redraw_timer (type ='DRAW_WIN_SWAP',iterations =1 )


            try :
                bpy .ops .wm .redraw_timer (type ='DRAW',iterations =1 )
            except :
                pass 

        except Exception as e :
            logger .debug (f"Could not force redraw: {e}")

    def _handle_toggle_rule (self ,rule_index ):
        """Handle rule checkbox toggle."""
        try :
            context =bpy .context 
            instructions =getattr (context .scene ,'vibe4d_custom_instructions',[])

            if rule_index <len (instructions ):
                instructions [rule_index ].enabled =not instructions [rule_index ].enabled 
                logger .info (f"Toggled rule {rule_index} to {'enabled' if instructions[rule_index].enabled else 'disabled'}")


                from ....utils .instructions_manager import instructions_manager 
                instructions_manager .auto_save_instructions (context )


                self ._update_ui_instantly ()

        except Exception as e :
            logger .error (f"Error toggling rule: {e}")

    def _handle_edit_rule (self ,rule_index ):
        """Handle rule edit click."""
        try :
            context =bpy .context 
            instructions =getattr (context .scene ,'vibe4d_custom_instructions',[])

            if rule_index <len (instructions ):

                self .editing_rule_index =rule_index 

                logger .info (f"Editing rule {rule_index}")


                self ._update_ui_instantly ()


                if 'rule_input'in self .components :
                    input_component =self .components ['rule_input']
                    if hasattr (input_component ,'ui_state')and input_component .ui_state :
                        input_component .ui_state .set_focus (input_component )

        except Exception as e :
            logger .error (f"Error editing rule: {e}")

    def _handle_delete_rule (self ,rule_index ):
        """Handle rule delete click."""
        try :
            context =bpy .context 
            instructions =getattr (context .scene ,'vibe4d_custom_instructions',[])

            if rule_index <len (instructions ):
                rule_text =instructions [rule_index ].text 
                instructions .remove (rule_index )

                logger .info (f"Deleted rule {rule_index}: {rule_text}")


                from ....utils .instructions_manager import instructions_manager 
                instructions_manager .auto_save_instructions (context )


                if self .editing_rule_index ==rule_index :
                    self .editing_rule_index =-1 
                    self .new_rule_text =""
                elif self .editing_rule_index >rule_index :

                    self .editing_rule_index -=1 


                self ._update_ui_instantly ()

        except Exception as e :
            logger .error (f"Error deleting rule: {e}")

    def _handle_open_github (self ,segment ):
        """Handle GitHub link click."""
        try :
            import webbrowser 
            webbrowser .open ("https://github.com/vibe4d")
        except Exception as e :
            logger .error (f"Error opening GitHub: {e}")

    def _handle_open_website (self ,segment ):
        """Handle website link click."""
        try :
            bpy .ops .vibe4d .open_website ()
        except Exception as e :
            logger .error (f"Error opening website: {e}")

    def _handle_open_discord (self ,segment ):
        """Handle Discord link click."""
        try :
            bpy .ops .vibe4d .open_discord ()
        except Exception as e :
            logger .error (f"Error opening Discord: {e}")

    def _handle_open_twitter (self ,segment ):
        """Handle Twitter link click."""
        try :
            import webbrowser 
            webbrowser .open ("https://twitter.com/vibe4d")
        except Exception as e :
            logger .error (f"Error opening Twitter: {e}")

    def _handle_link_hover_start (self ,segment ):
        """Handle link hover start - could add additional effects."""
        pass 

    def _handle_link_hover_end (self ,segment ):
        """Handle link hover end - could add additional effects."""
        pass 

    def set_refresh_callback (self ,callback ):
        """Set the refresh callback."""
        self .refresh_callback =callback 

    def reset_usage_fetch_state (self ):
        """Reset the usage data fetch state to allow re-fetching."""
        self .usage_data_fetched =False 
        self .is_fetching_usage =False 

    def _get_current_rule_text (self ):
        """Get current text from input field."""
        if 'rule_input'in self .components :
            return self .components ['rule_input'].get_text ()
        return self .new_rule_text 

    def _check_input_changes (self ):
        """Check for text input changes and update button state."""
        if 'rule_input'in self .components :
            current_text =self .components ['rule_input'].get_text ().strip ()
            if current_text !=self .last_input_text :
                self .last_input_text =current_text 
                self ._update_button_state_only ()

    def _update_button_state_only (self ):
        """Update only the add button state based on current text."""
        if 'add_button'in self .components :
            current_text =self ._get_current_rule_text ().strip ()
            if current_text :
                self .components ['add_button'].style .background_color =PRIMARY_BUTTON_COLOR 
                self .components ['add_button'].style .text_color =WHITE_TEXT_COLOR 
            else :
                self .components ['add_button'].style .background_color =DISABLED_BUTTON_COLOR 
                self .components ['add_button'].style .text_color =DISABLED_TEXT_COLOR 

    def _fetch_usage_data_async (self ):
        """Fetch usage data in a background thread."""
        if self .is_fetching_usage :
            logger .debug ("Usage data fetch already in progress, skipping")
            return 

        self .is_fetching_usage =True 


        usage_thread =threading .Thread (target =self ._fetch_usage_data )
        usage_thread .daemon =True 
        usage_thread .start ()

    def _fetch_usage_data (self ):
        """Fetch usage data from API and update the view."""
        try :
            context =bpy .context 


            user_id =getattr (context .window_manager ,'vibe4d_user_id','')
            token =getattr (context .window_manager ,'vibe4d_user_token','')

            if not user_id or not token :
                logger .warning ("Cannot fetch usage data - missing authentication credentials")
                return 


            try :
                from ....api .client import api_client 
            except ImportError :

                from vibe4d .api .client import api_client 

            logger .info ("Fetching usage data from API")


            success ,data_or_error =api_client .get_usage_info (user_id ,token )

            def update_ui_on_main_thread ():
                """Update UI on main thread with fetched data."""
                try :
                    if success :

                        usage_data =data_or_error 


                        if 'plan_id'in usage_data :
                            context .window_manager .vibe4d_user_plan =usage_data ['plan_id']

                        if 'plan_name'in usage_data :



                            context .window_manager .vibe4d_plan_name =usage_data ['plan_name']


                        if 'current_usage'in usage_data :
                            context .window_manager .vibe4d_current_usage =usage_data ['current_usage']

                        if 'limit'in usage_data :
                            context .window_manager .vibe4d_usage_limit =usage_data ['limit']


                        if 'limit_type'in usage_data :
                            context .window_manager .vibe4d_limit_type =usage_data ['limit_type']

                        if 'plan_id'in usage_data :
                            context .window_manager .vibe4d_plan_id =usage_data ['plan_id']

                        if 'plan_name'in usage_data :
                            context .window_manager .vibe4d_plan_name =usage_data ['plan_name']

                        if 'allowed'in usage_data :
                            context .window_manager .vibe4d_allowed =usage_data ['allowed']

                        if 'usage_percentage'in usage_data :
                            context .window_manager .vibe4d_usage_percentage =usage_data ['usage_percentage']

                        if 'remaining_requests'in usage_data :
                            context .window_manager .vibe4d_remaining_requests =usage_data ['remaining_requests']

                        logger .info (f"Updated usage data: {usage_data.get('current_usage', 0)}/{usage_data.get('limit', 0)} ({usage_data.get('plan_id', 'unknown')} plan)")


                        try :
                            from ....auth .manager import auth_manager 
                            auth_manager .save_auth_state (context )
                        except Exception as e :
                            logger .debug (f"Could not save auth state: {e}")


                        if self .refresh_callback :
                            self .refresh_callback ()
                        else :

                            self ._notify_ui_system_of_changes ()

                    else :

                        error_msg =data_or_error .get ('error','Unknown error')
                        logger .warning (f"Failed to fetch usage data: {error_msg}")




                except Exception as e :
                    logger .error (f"Error updating UI with usage data: {e}")

                return None 


            bpy .app .timers .register (update_ui_on_main_thread ,first_interval =0.1 )

        except Exception as e :
            logger .error (f"Error fetching usage data: {e}")
        finally :
            self .is_fetching_usage =False 