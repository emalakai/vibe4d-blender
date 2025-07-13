"""
Authentication manager for Vibe4D addon.

Handles startup authentication validation and credential management.
"""

import bpy 
import time 
from ..utils .logger import logger 
from ..utils .storage import secure_storage 
from ..api .client import api_client 


class AuthManager :
    """Manages authentication state and validation."""

    def __init__ (self ):
        self .is_initialized =False 
        self .last_validation_time =0 
        self .validation_interval =300 

    def initialize_auth (self ,context )->bool :
        """Initialize authentication on addon startup."""

        is_already_authenticated =getattr (context .window_manager ,'vibe4d_authenticated',False )

        if is_already_authenticated :
            if not self .is_initialized :
                self .is_initialized =True 
            return True 



        if self .is_initialized :
            try :
                credentials =secure_storage .load_credentials ()
                if credentials :
                    user_id =credentials .get ("user_id","")
                    token =credentials .get ("token","")
                    email =credentials .get ("email","")
                    plan =credentials .get ("plan","")

                    if user_id and token :

                        context .window_manager .vibe4d_authenticated =True 
                        context .window_manager .vibe4d_user_id =user_id 
                        context .window_manager .vibe4d_user_token =token 
                        context .window_manager .vibe4d_user_email =email 
                        context .window_manager .vibe4d_user_plan =plan 
                        context .window_manager .vibe4d_status =f"Authenticated ({plan} plan)"if plan else "Authenticated"
                        return True 
            except Exception as e :
                logger .debug (f"Failed to restore auth from saved credentials: {str(e)}")


            return False 

        logger .info ("Initializing authentication system")

        try :

            credentials =secure_storage .load_credentials ()

            if not credentials :
                logger .info ("No saved credentials found - user needs to authenticate")
                self .is_initialized =True 
                return False 


            user_id =credentials .get ("user_id","")
            token =credentials .get ("token","")
            email =credentials .get ("email","")
            plan =credentials .get ("plan","")

            if not user_id or not token :
                logger .warning ("Invalid saved credentials - missing required fields")
                self .is_initialized =True 
                return False 


            current_time =time .time ()
            time_since_last_validation =current_time -self .last_validation_time 

            if time_since_last_validation <self .validation_interval :

                context .window_manager .vibe4d_authenticated =True 
                context .window_manager .vibe4d_user_id =user_id 
                context .window_manager .vibe4d_user_token =token 
                context .window_manager .vibe4d_user_email =email 
                context .window_manager .vibe4d_user_plan =plan 
                context .window_manager .vibe4d_status =f"Authenticated ({plan} plan)"if plan else "Authenticated"
                self .is_initialized =True 
                return True 

            logger .info ("Found saved credentials, validating with server...")


            is_valid ,error_type =api_client .validate_user_token (user_id ,token )

            if is_valid :

                context .window_manager .vibe4d_authenticated =True 
                context .window_manager .vibe4d_user_id =user_id 
                context .window_manager .vibe4d_user_token =token 
                context .window_manager .vibe4d_user_email =email 
                context .window_manager .vibe4d_user_plan =plan 
                context .window_manager .vibe4d_status =f"Authenticated ({plan} plan)"if plan else "Authenticated"

                self .last_validation_time =current_time 
                logger .info (f"Auto-authenticated user: {email}")


                self .update_usage_info (context )

                self .is_initialized =True 
                return True 
            elif error_type =="network":

                logger .warning ("API temporarily unavailable during validation - keeping saved credentials")
                context .window_manager .vibe4d_authenticated =True 
                context .window_manager .vibe4d_user_id =user_id 
                context .window_manager .vibe4d_user_token =token 
                context .window_manager .vibe4d_user_email =email 
                context .window_manager .vibe4d_user_plan =plan 
                context .window_manager .vibe4d_status =f"Authenticated ({plan} plan) - API temporarily unavailable"if plan else "Authenticated - API temporarily unavailable"
                context .window_manager .vibe4d_network_error =True 


                logger .info (f"Restored user session despite API unavailability: {email}")
                self .is_initialized =True 
                return True 
            else :

                logger .warning ("Saved credentials are invalid - clearing them")
                secure_storage .clear_credentials ()
                self ._clear_auth_state (context )
                self .is_initialized =True 
                return False 

        except Exception as e :
            logger .error (f"Authentication initialization failed: {str(e)}")
            self ._clear_auth_state (context )
            self .is_initialized =True 
            return False 

    def save_auth_state (self ,context )->bool :
        """Save current authentication state to persistent storage."""
        try :
            if not context .window_manager .vibe4d_authenticated :
                return False 

            user_id =getattr (context .window_manager ,'vibe4d_user_id','')
            token =getattr (context .window_manager ,'vibe4d_user_token','')
            email =getattr (context .window_manager ,'vibe4d_user_email','')
            plan =getattr (context .window_manager ,'vibe4d_user_plan','')

            if not user_id or not token :
                logger .warning ("Cannot save auth state - missing credentials")
                return False 

            return secure_storage .save_credentials (user_id ,token ,email ,plan )

        except Exception as e :
            logger .error (f"Failed to save auth state: {str(e)}")
            return False 

    def clear_auth_state (self ,context )->bool :
        """Clear authentication state and saved credentials."""
        try :

            secure_storage .clear_credentials ()


            self ._clear_auth_state (context )


            self .last_validation_time =0 

            logger .info ("Authentication state cleared")
            return True 

        except Exception as e :
            logger .error (f"Failed to clear auth state: {str(e)}")
            return False 

    def reset_auth_manager (self ):
        """Reset auth manager state (used on addon reload)."""
        self .is_initialized =False 
        self .last_validation_time =0 
        logger .debug ("Auth manager state reset")

    def _clear_auth_state (self ,context ):
        """Clear authentication state from scene properties."""
        context .window_manager .vibe4d_authenticated =False 
        context .window_manager .vibe4d_user_id =""
        context .window_manager .vibe4d_user_token =""
        context .window_manager .vibe4d_user_email =""
        context .window_manager .vibe4d_user_plan =""
        context .window_manager .vibe4d_status ="Ready"
        context .window_manager .vibe4d_network_error =False 


        context .window_manager .vibe4d_current_usage =0 
        context .window_manager .vibe4d_usage_limit =0 
        context .window_manager .vibe4d_limit_type =""
        context .window_manager .vibe4d_plan_id =""
        context .window_manager .vibe4d_plan_name =""
        context .window_manager .vibe4d_allowed =True 
        context .window_manager .vibe4d_usage_percentage =0.0 
        context .window_manager .vibe4d_remaining_requests =0 

    def _store_user_data (self ,context ,user_id ,token ,email ,plan ):
        """Store user data in scene properties."""
        context .window_manager .vibe4d_authenticated =True 
        context .window_manager .vibe4d_user_id =user_id 
        context .window_manager .vibe4d_user_token =token 
        context .window_manager .vibe4d_user_email =email 
        context .window_manager .vibe4d_user_plan =plan 

        logger .info (f"User authenticated: {email} (Plan: {plan})")

    def update_user_data (self ,context ,user_id ,token ,email ,plan ):
        """Update user data after successful refresh."""
        context .window_manager .vibe4d_authenticated =True 
        context .window_manager .vibe4d_user_id =user_id 
        context .window_manager .vibe4d_user_token =token 
        context .window_manager .vibe4d_user_email =email 
        context .window_manager .vibe4d_user_plan =plan 

        logger .debug ("User data updated successfully")

    def store_user_data_from_api (self ,context ,user_id ,token ,email ,plan ):
        """Store user data from API response."""
        context .window_manager .vibe4d_authenticated =True 
        context .window_manager .vibe4d_user_id =user_id 
        context .window_manager .vibe4d_user_token =token 
        context .window_manager .vibe4d_user_email =email 
        context .window_manager .vibe4d_user_plan =plan 
        context .window_manager .vibe4d_network_error =True 

        logger .info (f"User authenticated from API: {email} (Plan: {plan})")

    def get_auth_headers (self ,context ):
        """Get authentication headers for API requests."""
        token =getattr (context .window_manager ,'vibe4d_user_token','')
        user_id =getattr (context .window_manager ,'vibe4d_user_id','')

        if not token or not user_id :
            return None 

        return {
        'Authorization':f'Bearer {token}',
        'X-User-ID':user_id ,
        'Content-Type':'application/json'
        }

    def is_authenticated (self ,context ):
        """Check if user is currently authenticated."""
        if not context .window_manager .vibe4d_authenticated :
            return False 


        token =getattr (context .window_manager ,'vibe4d_user_token','')
        user_id =getattr (context .window_manager ,'vibe4d_user_id','')

        return bool (token and user_id )

    def get_user_info (self ,context ):
        """Get current user information."""
        if not self .is_authenticated (context ):
            return None 

        return {
        'user_id':getattr (context .window_manager ,'vibe4d_user_id',''),
        'email':getattr (context .window_manager ,'vibe4d_user_email',''),
        'plan':getattr (context .window_manager ,'vibe4d_user_plan',''),
        'token':getattr (context .window_manager ,'vibe4d_user_token','')
        }

    def logout (self ,context ):
        """Logout user and clear authentication data."""
        logger .info ("Logging out user")

        context .window_manager .vibe4d_authenticated =False 
        context .window_manager .vibe4d_user_id =""
        context .window_manager .vibe4d_user_token =""
        context .window_manager .vibe4d_user_email =""
        context .window_manager .vibe4d_user_plan =""
        context .window_manager .vibe4d_network_error =False 


        context .window_manager .vibe4d_current_usage =0 
        context .window_manager .vibe4d_usage_limit =0 
        context .window_manager .vibe4d_limit_type =""
        context .window_manager .vibe4d_plan_id =""
        context .window_manager .vibe4d_plan_name =""
        context .window_manager .vibe4d_allowed =True 
        context .window_manager .vibe4d_usage_percentage =0.0 
        context .window_manager .vibe4d_remaining_requests =0 


        context .scene .vibe4d_is_generating =False 
        context .scene .vibe4d_generation_progress =0 
        context .scene .vibe4d_generation_stage =""
        context .scene .vibe4d_output_content =""
        context .scene .vibe4d_final_code =""
        context .scene .vibe4d_guide_content =""
        context .scene .vibe4d_last_error =""

    def reset_user_state (self ,context ):
        """Reset user state when logging out or auth fails."""

        context .scene .vibe4d_is_generating =False 
        context .scene .vibe4d_generation_progress =0 
        context .scene .vibe4d_generation_stage =""
        context .scene .vibe4d_output_content =""
        context .scene .vibe4d_final_code =""
        context .scene .vibe4d_guide_content =""
        context .scene .vibe4d_last_error =""

    def update_usage_info (self ,context )->bool :
        """Update usage information from API.
        
        Returns:
            bool: True if update was successful, False otherwise
        """
        try :
            if not self .is_authenticated (context ):
                logger .warning ("Cannot update usage info - user not authenticated")
                return False 

            user_id =getattr (context .window_manager ,'vibe4d_user_id','')
            token =getattr (context .window_manager ,'vibe4d_user_token','')

            if not user_id or not token :
                logger .warning ("Cannot update usage info - missing credentials")
                return False 

            logger .info ("Updating usage information from API")


            success ,data_or_error =api_client .get_usage_info (user_id ,token )

            if success :

                usage_data =data_or_error 

                context .window_manager .vibe4d_current_usage =usage_data .get ("current_usage",0 )
                context .window_manager .vibe4d_usage_limit =usage_data .get ("limit",0 )
                context .window_manager .vibe4d_limit_type =usage_data .get ("limit_type","")
                context .window_manager .vibe4d_plan_id =usage_data .get ("plan_id","")
                context .window_manager .vibe4d_plan_name =usage_data .get ("plan_name","")
                context .window_manager .vibe4d_allowed =usage_data .get ("allowed",True )
                context .window_manager .vibe4d_usage_percentage =usage_data .get ("usage_percentage",0.0 )
                context .window_manager .vibe4d_remaining_requests =usage_data .get ("remaining_requests",0 )

                logger .info (f"Usage info updated - {usage_data.get('current_usage', 0)}/{usage_data.get('limit', 0)} ({usage_data.get('usage_percentage', 0.0):.1f}%)")
                return True 
            else :

                error_msg =data_or_error .get ('error','Unknown error')
                logger .warning (f"Failed to update usage info: {error_msg}")
                return False 

        except Exception as e :
            logger .error (f"Error updating usage info: {str(e)}")
            return False 



auth_manager =AuthManager ()