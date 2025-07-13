"""
Authentication view for licence key entry.
"""

import logging 
import webbrowser 
import threading 
import time 
import bpy 
from typing import Dict ,Any 

from .base_view import BaseView 
from ..layout_manager import LayoutConfig ,LayoutStrategy 
from ..components import Label ,TextInput ,Button 
from ..components .icon_button import IconButton 
from ..components .image import ImageComponent 
from ..theme import get_themed_style 
from ..blender_theme_integration import get_theme_color 
from ..types import Bounds 
from ..styles import FontSizes 
from ..unified_styles import Styles 
from ..coordinates import CoordinateSystem 

logger =logging .getLogger (__name__ )


def get_main_padding ():
    return Styles .get_main_padding ()

def get_content_margin ():
    return Styles .get_content_margin ()

def get_auth_logo_size ():
    return int (20 *CoordinateSystem .get_ui_scale ())

def get_auth_welcome_width ():
    return int (400 *CoordinateSystem .get_ui_scale ())

def get_auth_welcome_height ():
    return int (30 *CoordinateSystem .get_ui_scale ())

def get_auth_status_width ():
    return int (300 *CoordinateSystem .get_ui_scale ())

def get_auth_status_height ():
    return int (20 *CoordinateSystem .get_ui_scale ())

def get_auth_error_width ():
    return int (300 *CoordinateSystem .get_ui_scale ())

def get_auth_error_height ():
    return int (20 *CoordinateSystem .get_ui_scale ())

def get_auth_input_width ():
    return int (400 *CoordinateSystem .get_ui_scale ())

def get_auth_input_height ():

    return int (32 *CoordinateSystem .get_ui_scale ())

def get_auth_button_size ():
    return int (20 *CoordinateSystem .get_ui_scale ())

def get_auth_license_text_height ():
    return int (20 *CoordinateSystem .get_ui_scale ())

def get_auth_combined_license_width ():
    return int (250 *CoordinateSystem .get_ui_scale ())

def get_auth_gap_large ():
    return int (10 *CoordinateSystem .get_ui_scale ())

def get_auth_gap_medium ():
    return int (10 *CoordinateSystem .get_ui_scale ())

def get_auth_gap_small ():
    return int (10 *CoordinateSystem .get_ui_scale ())

def get_auth_input_corner_radius ():
    return int (6 *CoordinateSystem .get_ui_scale ())

def get_auth_input_border_width ():
    return Styles .get_thin_border ()

def get_auth_input_content_padding ():

    return int (32 *CoordinateSystem .get_ui_scale ())

def get_auth_button_corner_radius ():
    return int (6 *CoordinateSystem .get_ui_scale ())

def get_auth_button_position_offset ():

    return int (6 *CoordinateSystem .get_ui_scale ())

def get_auth_center_offset ():
    return int (50 *CoordinateSystem .get_ui_scale ())

def get_auth_status_extra_offset ():
    return int (54 *CoordinateSystem .get_ui_scale ())


DEFAULT_FONT_SIZE =Styles .get_font_size ()


class AuthView (BaseView ):
    """Authentication view for license key entry."""

    def __init__ (self ):
        super ().__init__ ()
        self .is_verifying =False 

    def create_layout (self ,viewport_width :int ,viewport_height :int )->Dict [str ,Any ]:
        """Create the authentication view layout."""
        layouts ={}
        components ={}


        from ..component_theming import get_component_color 


        layout_data =self ._get_auth_layout_params (viewport_width ,viewport_height )
        layout_params =layout_data ['params']
        positions =layout_data ['positions']


        main_layout =self ._create_layout_container (
        "main",
        LayoutConfig (
        strategy =LayoutStrategy .ABSOLUTE ,
        padding_top =get_main_padding (),
        padding_right =get_main_padding (),
        padding_bottom =get_main_padding (),
        padding_left =get_main_padding ()
        )
        )
        layouts ['main']=main_layout 


        logo =ImageComponent ("logo.png",
        layout_params ['center_x']-layout_params ['logo_width']//2 ,
        positions ['logo_y'],
        layout_params ['logo_width'],
        layout_params ['logo_height'])
        components ['logo']=logo 


        welcome_text =Label ("Hello! Enter your license key to use Vibe4d",
        layout_params ['center_x']-layout_params ['welcome_width']//2 ,
        positions ['welcome_y'],
        layout_params ['welcome_width'],
        layout_params ['welcome_height'])
        welcome_text .style =get_themed_style ("title")
        welcome_text .style .font_size =DEFAULT_FONT_SIZE 
        welcome_text .style .text_align ="center"
        welcome_text .set_vertical_align ("center")
        components ['welcome_text']=welcome_text 


        status_text =Label ("Verifying...",
        layout_params ['center_x']-layout_params ['status_width']//2 ,
        positions ['status_y'],
        layout_params ['status_width'],
        layout_params ['status_height'])
        status_text .style =get_themed_style ("label")
        status_text .style .font_size =DEFAULT_FONT_SIZE 
        status_text .style .text_align ="center"
        status_text .style .text_color =(0.8 ,0.8 ,0.8 ,1.0 )
        status_text .visible =False 
        components ['status_text']=status_text 


        error_text =Label ("Invalid license key. Please try again.",
        layout_params ['center_x']-layout_params ['error_width']//2 ,
        positions ['error_y'],
        layout_params ['error_width'],
        layout_params ['error_height'])
        error_text .style =get_themed_style ("label")
        error_text .style .font_size =DEFAULT_FONT_SIZE 
        error_text .style .text_align ="center"
        error_text .style .text_color =(0.827 ,0.325 ,0.325 ,1.0 )
        error_text .visible =False 
        components ['error_text']=error_text 


        license_input =TextInput (placeholder ="Enter license key",max_height =get_auth_input_height (),
        corner_radius =get_auth_input_corner_radius (),auto_resize =False ,multiline =False )
        license_input .style =get_themed_style ("input")
        license_input .style .border_width =get_auth_input_border_width ()

        license_input .style .border_color =get_component_color ('text_input','border_color')
        license_input .set_position (layout_params ['center_x']-layout_params ['input_width']//2 ,positions ['input_y'])
        license_input .set_size (layout_params ['input_width'],layout_params ['input_height'])
        license_input .on_submit =self ._handle_auth_submit 
        license_input .set_content_padding (right =get_auth_input_content_padding ())
        components ['license_input']=license_input 



        button_spacing =int (6 *CoordinateSystem .get_ui_scale ())
        auth_button =IconButton ("arrow_up",
        layout_params ['center_x']+layout_params ['input_width']//2 -layout_params ['button_size']-button_spacing ,
        positions ['input_y']+button_spacing ,
        layout_params ['button_size'],
        layout_params ['button_size'],
        corner_radius =get_auth_button_corner_radius (),
        on_click =self ._handle_auth_submit )
        auth_button .style =get_themed_style ("button")

        auth_button .style .background_color =get_component_color ('button','background_color')

        auth_button .style .border_width =0 


        icon_size =int (14 *CoordinateSystem .get_ui_scale ())
        icon_padding =(layout_params ['button_size']-icon_size )//2 
        auth_button .icon_component .set_size (icon_size ,icon_size )
        auth_button .icon_component .set_position (
        auth_button .bounds .x +icon_padding ,
        auth_button .bounds .y +icon_padding 
        )
        components ['auth_button']=auth_button 


        license_text_combined =Label ("Need license? Get free license ↗",
        layout_params ['center_x']-layout_params ['combined_license_width']//2 ,
        positions ['license_y'],
        layout_params ['combined_license_width'],
        layout_params ['license_text_height'])
        license_text_combined .style =get_themed_style ("label")
        license_text_combined .style .text_align ="center"


        license_text_combined .add_highlight_style ('license_link_hover',
        text_color =get_theme_color ('text_selected'))


        license_text_combined .add_highlight_style ('license_link_normal',
        text_color =get_theme_color ('text_muted'))


        target_text ="Get free license ↗"
        start_idx =license_text_combined .text .find (target_text )
        end_idx =start_idx +len (target_text )

        license_text_combined .add_text_segment (
        start_index =start_idx ,
        end_index =end_idx ,
        style_name ='license_link_normal',
        hover_style_name ='license_link_hover',
        clickable =True ,
        hoverable =True ,
        on_click =lambda segment :self ._handle_get_license (),
        data ={'url':'https://vibe4d.com'}
        )

        components ['license_text_combined']=license_text_combined 

        self .components =components 
        self .layouts =layouts 

        return {
        'layouts':layouts ,
        'components':components ,
        'all_components':self ._get_all_components ()
        }

    def update_layout (self ,viewport_width :int ,viewport_height :int ):
        """Update layout positions when viewport changes."""
        layout_data =self ._get_auth_layout_params (viewport_width ,viewport_height )
        layout_params =layout_data ['params']
        positions =layout_data ['positions']


        if 'logo'in self .components :
            logo =self .components ['logo']
            logo .set_position (layout_params ['center_x']-layout_params ['logo_width']//2 ,positions ['logo_y'])
            logo .set_size (layout_params ['logo_width'],layout_params ['logo_height'])


        if 'welcome_text'in self .components :
            welcome_text =self .components ['welcome_text']
            welcome_text .set_position (layout_params ['center_x']-layout_params ['welcome_width']//2 ,positions ['welcome_y'])
            welcome_text .set_size (layout_params ['welcome_width'],layout_params ['welcome_height'])


        if 'status_text'in self .components :
            status_text =self .components ['status_text']
            status_text .set_position (layout_params ['center_x']-layout_params ['status_width']//2 ,positions ['status_y'])
            status_text .set_size (layout_params ['status_width'],layout_params ['status_height'])


        if 'error_text'in self .components :
            error_text =self .components ['error_text']
            error_text .set_position (layout_params ['center_x']-layout_params ['error_width']//2 ,positions ['error_y'])
            error_text .set_size (layout_params ['error_width'],layout_params ['error_height'])


        if 'license_input'in self .components :
            license_input =self .components ['license_input']
            license_input .set_position (layout_params ['center_x']-layout_params ['input_width']//2 ,positions ['input_y'])
            license_input .set_size (layout_params ['input_width'],layout_params ['input_height'])


        if 'auth_button'in self .components :
            auth_button =self .components ['auth_button']
            button_spacing =int (6 *CoordinateSystem .get_ui_scale ())
            auth_button .set_position (
            layout_params ['center_x']+layout_params ['input_width']//2 -layout_params ['button_size']-button_spacing ,
            positions ['input_y']+button_spacing 
            )
            auth_button .set_size (layout_params ['button_size'],layout_params ['button_size'])


            icon_size =int (14 *CoordinateSystem .get_ui_scale ())
            icon_padding =(layout_params ['button_size']-icon_size )//2 
            auth_button .icon_component .set_size (icon_size ,icon_size )
            auth_button .icon_component .set_position (
            auth_button .bounds .x +icon_padding ,
            auth_button .bounds .y +icon_padding 
            )


        if 'license_text_combined'in self .components :
            license_text_combined =self .components ['license_text_combined']
            license_text_combined .set_position (layout_params ['center_x']-layout_params ['combined_license_width']//2 ,positions ['license_y'])
            license_text_combined .set_size (layout_params ['combined_license_width'],layout_params ['license_text_height'])

    def get_focused_component (self ):
        """Get the component that should be focused by default."""
        return self .components .get ('license_input')

    def get_license_key (self )->str :
        """Get license key from the license input component."""
        license_input =self .components .get ('license_input')
        if license_input and hasattr (license_input ,'get_text'):
            return license_input .get_text ().strip ()
        return ""

    def clear_license_input (self ):
        """Clear the license input field."""
        license_input =self .components .get ('license_input')
        if license_input and hasattr (license_input ,'set_text'):
            license_input .set_text ("")

    def _show_status (self ,visible :bool =True ):
        """Show or hide the verification status message."""
        if 'status_text'in self .components :
            self .components ['status_text'].visible =visible 

    def _show_error (self ,visible :bool =True ):
        """Show or hide the error message."""
        if 'error_text'in self .components :
            self .components ['error_text'].visible =visible 

    def _hide_all_messages (self ):
        """Hide all status and error messages."""
        self ._show_status (False )
        self ._show_error (False )

    def _verify_license_async (self ,license_key :str ):
        """Verify license key asynchronously with the actual API."""
        def verify ():
            try :

                try :
                    from ...api .client import api_client 
                except ImportError :

                    from vibe4d .api .client import api_client 

                logger .info (f"Starting license verification for key: {license_key[:8]}...")


                success ,data_or_error =api_client .verify_license (license_key )


                def update_ui_result ():
                    self ._handle_verification_result (success ,data_or_error )
                    return None 


                bpy .app .timers .register (update_ui_result ,first_interval =0.1 )

            except Exception as e :
                logger .error (f"Error during license verification: {e}")

                error_msg =str (e )

                def update_ui_error ():
                    self ._handle_verification_result (False ,{"error":error_msg })
                    return None 
                bpy .app .timers .register (update_ui_error ,first_interval =0.1 )


        verification_thread =threading .Thread (target =verify )
        verification_thread .daemon =True 
        verification_thread .start ()

    def _handle_verification_result (self ,success :bool ,data_or_error :Dict [str ,Any ]):
        """Handle the result of license verification from the actual API."""
        self .is_verifying =False 
        self ._show_status (False )

        if success :
            logger .info ("License key is valid - storing authentication data")

            try :

                try :
                    from ...auth .manager import auth_manager 
                except ImportError :

                    from vibe4d .auth .manager import auth_manager 


                context =bpy .context 


                data =data_or_error 
                context .window_manager .vibe4d_user_id =data .get ("user_id","")
                context .window_manager .vibe4d_user_token =data .get ("token","")
                context .window_manager .vibe4d_user_email =data .get ("email","")
                context .window_manager .vibe4d_user_plan =data .get ("plan_id","")


                context .window_manager .vibe4d_authenticated =True 
                plan_name =data .get ("plan_id","unknown")
                context .window_manager .vibe4d_status =f"Authenticated ({plan_name} plan)"


                auth_manager .save_auth_state (context )


                auth_manager .update_usage_info (context )

                logger .info (f"Successfully authenticated user: {data.get('email', 'Unknown')}")


                if self .callbacks .get ('on_view_change'):
                    from ..ui_factory import ViewState 
                    self .callbacks ['on_view_change'](ViewState .MAIN )
                else :
                    logger .error ("No on_view_change callback available")

            except Exception as e :
                logger .error (f"Error storing authentication data: {e}")
                self ._show_error (True )
        else :
            logger .info ("License key is invalid - showing error")


            error_data =data_or_error 
            error_msg =error_data .get ("error","Authentication failed")

            logger .error (f"Authentication failed: {error_msg}")


            detailed_error_msg =error_msg 


            if "network"in error_msg .lower ()or "connection"in error_msg .lower ():
                detailed_error_msg +="\n\n**Connection Issue:**\n"
                detailed_error_msg +="• Check your internet connection\n"
                detailed_error_msg +="• Try again in a moment\n"
                detailed_error_msg +="• Check if you can access emalakai.com in your browser"

            elif "invalid"in error_msg .lower ()or "not found"in error_msg .lower ():
                detailed_error_msg +="\n\n**License Key Issue:**\n"
                detailed_error_msg +="• Double-check your license key for typos\n"
                detailed_error_msg +="• Make sure you're using the complete key\n"
                detailed_error_msg +="• Verify your purchase was successful\n"
                detailed_error_msg +="• Contact support if you believe this is an error"

            elif "expired"in error_msg .lower ()or "subscription"in error_msg .lower ():
                detailed_error_msg +="\n\n**Subscription Issue:**\n"
                detailed_error_msg +="• Check if your subscription is still active\n"
                detailed_error_msg +="• Verify your payment method is valid\n"
                detailed_error_msg +="• Log into your account on emalakai.com to check status\n"
                detailed_error_msg +="• Contact support for subscription assistance"

            elif "rate limit"in error_msg .lower ()or "too many"in error_msg .lower ():
                detailed_error_msg +="\n\n**Rate Limit:**\n"
                detailed_error_msg +="• Wait a few minutes before trying again\n"
                detailed_error_msg +="• Too many verification attempts were made recently"

            elif "maintenance"in error_msg .lower ()or "service"in error_msg .lower ():
                detailed_error_msg +="\n\n**Service Status:**\n"
                detailed_error_msg +="• The service is temporarily unavailable\n"
                detailed_error_msg +="• Try again in a few minutes\n"
                detailed_error_msg +="• Check emalakai.com for service updates"

            else :

                detailed_error_msg +="\n\n**What you can try:**\n"
                detailed_error_msg +="• Verify your license key is correct\n"
                detailed_error_msg +="• Check your internet connection\n"
                detailed_error_msg +="• Try again in a moment\n"
                detailed_error_msg +="• Contact support if the issue persists"


            self ._error_message =detailed_error_msg 


            try :
                context =bpy .context 
                context .window_manager .vibe4d_status ="Authentication failed"
            except Exception as e :
                logger .warning (f"Could not update status in context: {e}")

            self ._show_error (True )

    def _get_auth_layout_params (self ,viewport_width :int ,viewport_height :int )->Dict [str ,Any ]:
        """Get standardized auth layout parameters for consistent positioning."""

        main_padding =get_main_padding ()
        available_width =viewport_width -(main_padding *2 )


        default_input_width =get_auth_input_width ()


        actual_input_width =min (default_input_width ,available_width )

        layout_params ={
        'center_x':viewport_width //2 ,
        'center_y':viewport_height //2 ,
        'logo_width':get_auth_logo_size (),
        'logo_height':get_auth_logo_size (),
        'welcome_width':get_auth_welcome_width (),
        'welcome_height':get_auth_welcome_height (),
        'status_width':get_auth_status_width (),
        'status_height':get_auth_status_height (),
        'error_width':get_auth_error_width (),
        'error_height':get_auth_error_height (),
        'input_width':actual_input_width ,
        'input_height':get_auth_input_height (),
        'button_size':get_auth_button_size (),
        'license_text_height':get_auth_license_text_height (),
        'combined_license_width':get_auth_combined_license_width (),
        'gap_large':get_auth_gap_large (),
        'gap_medium':get_auth_gap_medium (),
        'gap_small':get_auth_gap_small (),
        }


        uniform_gap =int (10 *CoordinateSystem .get_ui_scale ())






        input_style_padding =int (10 *CoordinateSystem .get_ui_scale ())
        input_border_width =layout_params .get ('input_border_width',1 )
        input_internal_padding =(input_style_padding *2 )+(input_border_width *2 )


        total_height =(layout_params ['logo_height']+
        layout_params ['welcome_height']+
        layout_params ['input_height']+
        layout_params ['license_text_height']+
        3 *uniform_gap )


        start_y =layout_params ['center_y']+(total_height //2 )

        positions ={}
        positions ['logo_y']=start_y 
        positions ['welcome_y']=positions ['logo_y']-layout_params ['logo_height']-uniform_gap 
        positions ['input_y']=positions ['welcome_y']-layout_params ['welcome_height']-uniform_gap 




        input_visual_bottom =positions ['input_y']-layout_params ['input_height']+input_internal_padding 
        positions ['license_y']=input_visual_bottom -uniform_gap 



        positions ['status_y']=positions ['input_y']-layout_params ['input_height']-(uniform_gap //2 )
        positions ['error_y']=positions ['input_y']-layout_params ['input_height']-(uniform_gap //2 )

        return {'params':layout_params ,'positions':positions }

    def _handle_get_license (self ):

        webbrowser .open ("https://vibe4d.gumroad.com/l/blender")
        logger .info ("Opened Gumroad license page")


        if self .callbacks .get ('on_get_license'):
            self .callbacks ['on_get_license']()

    def _handle_auth_submit (self ):
        """Handle auth submit button click - validate license key."""
        if self .is_verifying :
            logger .info ("Already verifying license key, ignoring submit")
            return 

        logger .info ("Auth submit clicked - validating license key")

        try :

            license_key =self .get_license_key ()

            if not license_key :
                logger .info ("No license key entered")
                self ._hide_all_messages ()
                self ._show_error (True )
                return 

            logger .info (f"Verifying license key: {license_key}")


            self ._hide_all_messages ()
            self ._show_status (True )
            self .is_verifying =True 


            self ._verify_license_async (license_key )

        except Exception as e :
            logger .error (f"Error in auth submit handler: {e}")
            import traceback 
            logger .error (f"Traceback: {traceback.format_exc()}")
            self .is_verifying =False 
            self ._show_status (False )
            self ._show_error (True )

    def validate_layout_consistency (self ,viewport_width :int ,viewport_height :int )->bool :
        """Validate that all auth layout functions use consistent parameters."""
        try :

            layout_data =self ._get_auth_layout_params (viewport_width ,viewport_height )


            required_param_keys =[
            'center_x','center_y','logo_width','logo_height',
            'welcome_width','welcome_height','status_width','status_height',
            'error_width','error_height','input_width','input_height',
            'button_size','license_text_height','combined_license_width',
            'gap_large','gap_medium','gap_small'
            ]

            required_position_keys =['logo_y','welcome_y','status_y','error_y','input_y','license_y']

            params_valid =all (key in layout_data ['params']for key in required_param_keys )
            positions_valid =all (key in layout_data ['positions']for key in required_position_keys )


            positions =layout_data ['positions']
            logical_order =(
            positions ['logo_y']>positions ['welcome_y']>
            positions ['input_y']>positions ['license_y']
            )

            logger .info (f"Auth layout validation: params={params_valid}, positions={positions_valid}, order={logical_order}")
            return params_valid and positions_valid and logical_order 

        except Exception as e :
            logger .error (f"Auth layout validation failed: {e}")
            return False 

    def is_authenticated (self )->bool :
        """Check if user is already authenticated."""
        try :

            try :
                from ...auth .manager import auth_manager 
            except ImportError :

                from vibe4d .auth .manager import auth_manager 

            context =bpy .context 
            return auth_manager .is_authenticated (context )
        except Exception as e :
            logger .error (f"Error checking authentication status: {e}")
            return False 

    def get_user_info (self )->Dict [str ,Any ]:
        """Get current user information if authenticated."""
        try :

            try :
                from ...auth .manager import auth_manager 
            except ImportError :

                from vibe4d .auth .manager import auth_manager 

            context =bpy .context 
            return auth_manager .get_user_info (context )or {}
        except Exception as e :
            logger .error (f"Error getting user info: {e}")
            return {}

    def logout (self )->bool :
        """Logout current user."""
        try :

            try :
                from ...auth .manager import auth_manager 
            except ImportError :

                from vibe4d .auth .manager import auth_manager 

            context =bpy .context 
            auth_manager .logout (context )
            logger .info ("User logged out successfully")
            return True 
        except Exception as e :
            logger .error (f"Error during logout: {e}")
            return False 