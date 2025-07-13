"""
Authentication operators for Vibe4D addon.

Contains login, logout, and license purchase operators.
"""

import bpy 
import webbrowser 
from bpy .types import Operator 
import time 

from ..utils .logger import logger 
from ..api .client import api_client 
from ..auth .manager import auth_manager 


class VIBE4D_OT_verify_license (Operator ):
    """License verification operator."""

    bl_idname ="vibe4d.verify_license"
    bl_label ="Verify License"
    bl_description ="Verify license key with Emalak AI API"
    bl_options ={'REGISTER'}

    def execute (self ,context ):
        """Execute license verification."""
        try :
            license_key =context .window_manager .vibe4d_license_key .strip ()

            if not license_key :
                self .report ({'ERROR'},"Please enter a valid license key")
                return {'CANCELLED'}

            logger .info ("Attempting authentication with license key")
            context .window_manager .vibe4d_status ="Verifying license..."


            success ,data_or_error =api_client .verify_license (license_key )

            if success :
                data =data_or_error 
                logger .info ("License authentication successful")


                context .window_manager .vibe4d_user_id =data .get ("user_id","")
                context .window_manager .vibe4d_user_token =data .get ("token","")
                context .window_manager .vibe4d_user_email =data .get ("email","")
                context .window_manager .vibe4d_user_plan =data .get ("plan_id","")


                context .window_manager .vibe4d_authenticated =True 
                context .window_manager .vibe4d_status =f"Authenticated ({data.get('plan_id', 'unknown')} plan)"


                auth_manager .save_auth_state (context )


                auth_manager .update_usage_info (context )

                self .report ({'INFO'},f"Successfully authenticated! Welcome {data.get('email', 'User')}")

                return {'FINISHED'}
            else :
                error_msg =data_or_error 
                logger .error (f"License authentication failed: {error_msg}")
                context .window_manager .vibe4d_status ="Authentication failed"
                self .report ({'ERROR'},f"Authentication failed: {error_msg}")
                return {'CANCELLED'}

        except Exception as e :
            logger .error (f"License authentication error: {str(e)}")
            context .window_manager .vibe4d_status ="Authentication error"
            self .report ({'ERROR'},f"Authentication error: {str(e)}")
            return {'CANCELLED'}


class VIBE4D_OT_get_license_key (Operator ):
    """Open Gumroad license purchase page."""

    bl_idname ="vibe4d.get_license_key"
    bl_label ="Get License Key"
    bl_description ="Open Gumroad page to purchase Vibe4D license"
    bl_options ={'REGISTER'}

    def execute (self ,context ):
        """Open the Gumroad license purchase page."""
        try :
            license_url ="https://vibe4d.gumroad.com/l/blender"

            logger .info ("Opening license purchase page")
            webbrowser .open (license_url )

            self .report ({'INFO'},"License purchase page opened in browser")
            return {'FINISHED'}

        except Exception as e :
            logger .error (f"Failed to open license page: {str(e)}")
            self .report ({'ERROR'},f"Failed to open license page: {str(e)}")
            return {'CANCELLED'}


class VIBE4D_OT_open_discord (Operator ):
    """Open Vibe4D Discord server."""

    bl_idname ="vibe4d.open_discord"
    bl_label ="Discord"
    bl_description ="Join Vibe4D Discord community"
    bl_options ={'REGISTER'}

    def execute (self ,context ):
        """Open the Discord server."""
        try :
            discord_url ="https://discord.gg/hcu5PQ7Rfp"

            logger .info ("Opening Discord server")
            webbrowser .open (discord_url )

            self .report ({'INFO'},"Discord server opened in browser")
            return {'FINISHED'}

        except Exception as e :
            logger .error (f"Failed to open Discord: {str(e)}")
            self .report ({'ERROR'},f"Failed to open Discord: {str(e)}")
            return {'CANCELLED'}


class VIBE4D_OT_open_patreon (Operator ):
    """Open Vibe4D Patreon page."""

    bl_idname ="vibe4d.open_patreon"
    bl_label ="Patreon"
    bl_description ="Support Vibe4D on Patreon"
    bl_options ={'REGISTER'}

    def execute (self ,context ):
        """Open the Patreon page."""
        try :
            patreon_url ="https://patreon.com/vibe4d"

            logger .info ("Opening Patreon page")
            webbrowser .open (patreon_url )

            self .report ({'INFO'},"Patreon page opened in browser")
            return {'FINISHED'}

        except Exception as e :
            logger .error (f"Failed to open Patreon: {str(e)}")
            self .report ({'ERROR'},f"Failed to open Patreon: {str(e)}")
            return {'CANCELLED'}


class VIBE4D_OT_open_website (Operator ):
    """Open Vibe4D website."""

    bl_idname ="vibe4d.open_website"
    bl_label ="Website"
    bl_description ="Visit Vibe4D official website"
    bl_options ={'REGISTER'}

    def execute (self ,context ):
        """Open the website."""
        try :
            website_url ="https://vibe4d.com"

            logger .info ("Opening Vibe4D website")
            webbrowser .open (website_url )

            self .report ({'INFO'},"Website opened in browser")
            return {'FINISHED'}

        except Exception as e :
            logger .error (f"Failed to open website: {str(e)}")
            self .report ({'ERROR'},f"Failed to open website: {str(e)}")
            return {'CANCELLED'}


class VIBE4D_OT_manage_subscription (Operator ):
    """Open subscription management page."""

    bl_idname ="vibe4d.manage_subscription"
    bl_label ="Manage Subscription"
    bl_description ="Open subscription management page"
    bl_options ={'REGISTER'}

    def execute (self ,context ):
        """Open the subscription management page."""
        try :

            subscription_url ="https://vibe4d.com/dashboard"

            logger .info ("Opening subscription management page")
            webbrowser .open (subscription_url )

            self .report ({'INFO'},"Subscription management page opened in browser")
            return {'FINISHED'}

        except Exception as e :
            logger .error (f"Failed to open subscription page: {str(e)}")
            self .report ({'ERROR'},f"Failed to open subscription page: {str(e)}")
            return {'CANCELLED'}


class VIBE4D_OT_logout (Operator ):
    """Logout and clear authentication."""

    bl_idname ="vibe4d.logout"
    bl_label ="Logout"
    bl_description ="Logout and clear authentication data"
    bl_options ={'REGISTER'}

    def execute (self ,context ):
        """Execute logout."""
        try :
            from ..auth .manager import auth_manager 


            auth_manager .clear_auth_state (context )


            context .window_manager .vibe4d_status ="Ready"

            self .report ({'INFO'},"Logged out successfully")
            logger .info ("User logged out")

            return {'FINISHED'}

        except Exception as e :
            logger .error (f"Logout error: {str(e)}")
            self .report ({'ERROR'},f"Logout failed: {str(e)}")
            return {'CANCELLED'}


class VIBE4D_OT_retry_auth (Operator ):
    """Retry authentication operator for network errors."""

    bl_idname ="vibe4d.retry_auth"
    bl_label ="Retry Connection"
    bl_description ="Retry authentication validation after network error"
    bl_options ={'REGISTER'}

    def execute (self ,context ):
        """Execute authentication retry."""
        try :
            logger .info ("Retrying authentication validation")


            context .window_manager .vibe4d_network_error =False 
            context .window_manager .vibe4d_status ="Retrying connection..."


            bpy .ops .wm .redraw_timer (type ='DRAW_WIN_SWAP',iterations =1 )


            user_id =getattr (context .window_manager ,'vibe4d_user_id','')
            token =getattr (context .window_manager ,'vibe4d_user_token','')
            plan =getattr (context .window_manager ,'vibe4d_user_plan','')

            if not user_id or not token :
                logger .error ("No credentials available for retry")
                context .window_manager .vibe4d_status ="No credentials to retry"
                self .report ({'ERROR'},"No saved credentials available")
                return {'CANCELLED'}


            is_valid ,error_type =api_client .validate_user_token (user_id ,token )

            if is_valid :

                context .window_manager .vibe4d_authenticated =True 
                context .window_manager .vibe4d_status =f"Authenticated ({plan} plan)"if plan else "Authenticated"
                context .window_manager .vibe4d_network_error =False 


                auth_manager .last_validation_time =time .time ()


                auth_manager .update_usage_info (context )

                logger .info ("Authentication retry successful")
                self .report ({'INFO'},"Connection restored successfully")
                return {'FINISHED'}

            elif error_type =="network":

                context .window_manager .vibe4d_network_error =True 
                context .window_manager .vibe4d_status =f"Authenticated ({plan} plan) - API temporarily unavailable"if plan else "Authenticated - API temporarily unavailable"

                logger .warning ("Authentication retry failed - network still unavailable")
                self .report ({'WARNING'},"API still unavailable - please try again later")
                return {'CANCELLED'}

            else :

                logger .warning ("Authentication retry failed - invalid credentials")
                context .window_manager .vibe4d_network_error =False 


                auth_manager .clear_auth_state (context )

                self .report ({'ERROR'},"Authentication failed - please log in again")
                return {'CANCELLED'}

        except Exception as e :
            logger .error (f"Authentication retry error: {str(e)}")
            context .window_manager .vibe4d_status ="Retry failed"
            context .window_manager .vibe4d_network_error =True 
            self .report ({'ERROR'},f"Retry failed: {str(e)}")
            return {'CANCELLED'}


class VIBE4D_OT_check_auth_status (Operator ):
    """Check current authentication status."""

    bl_idname ="vibe4d.check_auth_status"
    bl_label ="Check Auth Status"
    bl_description ="Check current authentication status"
    bl_options ={'REGISTER'}

    def execute (self ,context ):
        """Check authentication status."""
        try :
            if auth_manager .is_authenticated (context ):
                user_info =auth_manager .get_user_info (context )
                if user_info :
                    email =user_info ['email']
                    plan =user_info ['plan']
                    self .report ({'INFO'},f"Authenticated as {email} ({plan} plan)")
                else :
                    self .report ({'INFO'},"Authenticated")
            else :
                self .report ({'INFO'},"Not authenticated")

            return {'FINISHED'}

        except Exception as e :
            logger .error (f"Failed to check auth status: {str(e)}")
            self .report ({'ERROR'},f"Failed to check status: {str(e)}")
            return {'CANCELLED'}


class VIBE4D_OT_handle_network_error (Operator ):
    """Handle network error states."""

    bl_idname ="vibe4d.handle_network_error"
    bl_label ="Retry Connection"
    bl_description ="Retry connecting to Vibe4D API"
    bl_options ={'REGISTER'}

    def execute (self ,context ):
        """Handle network error retry."""
        try :
            if auth_manager .initialize_auth (context ):
                context .window_manager .vibe4d_network_error =False 
                self .report ({'INFO'},"Connection restored!")
                return {'FINISHED'}
            else :
                context .window_manager .vibe4d_network_error =True 
                self .report ({'WARNING'},"Still unable to connect to API")
                return {'FINISHED'}

        except Exception as e :
            logger .error (f"Network error handling failed: {str(e)}")
            context .window_manager .vibe4d_network_error =True 
            self .report ({'ERROR'},f"Connection retry failed: {str(e)}")
            return {'CANCELLED'}


class VIBE4D_OT_clear_network_error (Operator ):
    """Clear network error flag."""

    bl_idname ="vibe4d.clear_network_error"
    bl_label ="Dismiss"
    bl_description ="Dismiss network error notification"
    bl_options ={'REGISTER'}

    def execute (self ,context ):
        """Clear network error flag."""
        context .window_manager .vibe4d_network_error =False 
        return {'FINISHED'}


class VIBE4D_OT_refresh_usage (Operator ):
    """Refresh usage information from API."""

    bl_idname ="vibe4d.refresh_usage"
    bl_label ="Refresh Usage"
    bl_description ="Refresh usage information from API"
    bl_options ={'REGISTER'}

    def execute (self ,context ):
        """Refresh usage information."""
        try :
            from ..auth .manager import auth_manager 

            if not auth_manager .is_authenticated (context ):
                self .report ({'ERROR'},"Not authenticated")
                return {'CANCELLED'}

            logger .info ("Manually refreshing usage information")


            success =auth_manager .update_usage_info (context )

            if success :
                current_usage =getattr (context .window_manager ,'vibe4d_current_usage',0 )
                usage_limit =getattr (context .window_manager ,'vibe4d_usage_limit',0 )
                usage_percentage =getattr (context .window_manager ,'vibe4d_usage_percentage',0.0 )

                self .report ({'INFO'},f"Usage updated: {current_usage}/{usage_limit} ({usage_percentage:.1f}%)")
                logger .info ("Usage information refreshed successfully")
            else :
                self .report ({'WARNING'},"Failed to refresh usage information")
                logger .warning ("Failed to refresh usage information")

            return {'FINISHED'}

        except Exception as e :
            logger .error (f"Usage refresh error: {str(e)}")
            self .report ({'ERROR'},f"Usage refresh failed: {str(e)}")
            return {'CANCELLED'}



classes =[
VIBE4D_OT_verify_license ,
VIBE4D_OT_get_license_key ,
VIBE4D_OT_open_discord ,
VIBE4D_OT_open_patreon ,
VIBE4D_OT_open_website ,
VIBE4D_OT_manage_subscription ,
VIBE4D_OT_logout ,
VIBE4D_OT_retry_auth ,
VIBE4D_OT_check_auth_status ,
VIBE4D_OT_handle_network_error ,
VIBE4D_OT_clear_network_error ,
VIBE4D_OT_refresh_usage ,
]