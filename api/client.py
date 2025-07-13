"""
API client for Vibe4D addon.

Handles communication with Emalak AI API.
"""

import json 
import urllib .request 
import urllib .parse 
import urllib .error 
from typing import Dict ,Any ,Tuple 

from ..utils .logger import logger 
from ..utils .json_utils import BlenderJSONEncoder 


class APIClient :
    """Client for Emalak AI API communication."""

    BASE_URL ="https://api.emalakai.com"


    ERROR_CODES ={
    0 :"CLIENT_ERROR",
    6 :"MAINTENANCE_MODE",
    101 :"INVALID_REQUEST",
    102 :"INTERNAL_SERVER_ERROR",
    103 :"AUTHORIZATION_FAILED",
    106 :"NOT_FOUND",
    109 :"TOO_MANY_REQUESTS",
    110 :"ALREADY_EXISTS",
    111 :"YOU_ARE_BEING_RATE_LIMITED",
    112 :"OUTDATED_CLIENT",
    1404 :"WRONG_PATH"
    }

    def __init__ (self ):
        self .timeout =30 

    def _make_request (self ,endpoint :str ,data :Dict [str ,Any ]=None ,method :str ="POST")->Tuple [bool ,Dict [str ,Any ]]:
        """Make HTTP request to API."""
        url =f"{self.BASE_URL}{endpoint}"

        try :

            headers ={
            'Content-Type':'application/json',
            'User-Agent':'Vibe4D-Blender-Addon/0.0.4'
            }


            if data :
                json_data =json .dumps (data ,cls =BlenderJSONEncoder ).encode ('utf-8')
            else :
                json_data =None 


            req =urllib .request .Request (url ,data =json_data ,headers =headers ,method =method )

            logger .debug (f"Making {method} request to {url}")


            with urllib .request .urlopen (req ,timeout =self .timeout )as response :
                response_data =response .read ().decode ('utf-8')
                result =json .loads (response_data )

                logger .debug (f"API response: {result}")
                return True ,result 

        except urllib .error .HTTPError as e :
            logger .error (f"HTTP error {e.code}: {e.reason}")
            try :
                error_data =json .loads (e .read ().decode ('utf-8'))
                return False ,error_data 
            except :
                return False ,{"error":f"HTTP {e.code}: {e.reason}"}

        except urllib .error .URLError as e :
            logger .error (f"URL error: {e.reason}")
            return False ,{"error":f"Connection error: {e.reason}"}

        except json .JSONDecodeError as e :
            logger .error (f"JSON decode error: {e}")
            return False ,{"error":"Invalid JSON response"}

        except Exception as e :
            logger .error (f"Unexpected error: {e}")
            return False ,{"error":f"Unexpected error: {str(e)}"}

    def _make_get_request (self ,endpoint :str ,params :Dict [str ,str ]=None )->Tuple [bool ,Dict [str ,Any ]]:
        """Make GET request to API with URL parameters."""
        url =f"{self.BASE_URL}{endpoint}"


        if params :
            query_string =urllib .parse .urlencode (params )
            url =f"{url}?{query_string}"

        try :

            headers ={
            'User-Agent':'Vibe4D-Blender-Addon/0.0.4'
            }


            req =urllib .request .Request (url ,headers =headers ,method ="GET")

            logger .debug (f"Making GET request to {url}")


            with urllib .request .urlopen (req ,timeout =self .timeout )as response :
                response_data =response .read ().decode ('utf-8')
                result =json .loads (response_data )

                logger .debug (f"API response: {result}")
                return True ,result 

        except urllib .error .HTTPError as e :
            logger .error (f"HTTP error {e.code}: {e.reason}")
            try :
                error_data =json .loads (e .read ().decode ('utf-8'))
                return False ,error_data 
            except :
                return False ,{"error":f"HTTP {e.code}: {e.reason}"}

        except urllib .error .URLError as e :
            logger .error (f"URL error: {e.reason}")
            return False ,{"error":f"Connection error: {e.reason}"}

        except json .JSONDecodeError as e :
            logger .error (f"JSON decode error: {e}")
            return False ,{"error":"Invalid JSON response"}

        except Exception as e :
            logger .error (f"Unexpected error: {e}")
            return False ,{"error":f"Unexpected error: {str(e)}"}

    def verify_license (self ,license_key :str )->Tuple [bool ,Dict [str ,Any ]]:
        """Verify license key with API."""
        logger .info ("Verifying license key")

        if not license_key .strip ():
            return False ,{"error":"License key cannot be empty"}

        data ={"license_key":license_key .strip ()}
        success ,response =self ._make_request ("/v1/license/verify",data )

        if not success :
            return False ,response 


        result =response .get ("result",{})
        if result .get ("type")!=2 or result .get ("code")!=0 :
            error_code =result .get ("code",0 )
            error_name =self .ERROR_CODES .get (error_code ,"UNKNOWN_ERROR")
            error_msg =result .get ("message","Unknown error")

            logger .error (f"API error {error_code} ({error_name}): {error_msg}")
            return False ,{"error":f"{error_name}: {error_msg}"}


        data =response .get ("data",{})
        if not data .get ("valid",False ):
            error_msg =data .get ("error_message","License verification failed")
            logger .warning (f"License invalid: {error_msg}")
            return False ,{"error":error_msg }


        logger .info ("License verified successfully")
        return True ,data 

    def validate_user_token (self ,user_id :str ,token :str )->Tuple [bool ,str ]:
        """Validate stored user token with API.
        
        Returns:
            Tuple[bool, str]: (is_valid, error_type)
            - is_valid: True if token is valid, False otherwise
            - error_type: "network" for connection issues, "auth" for invalid credentials, "" for success
        """
        logger .info ("Validating stored user token")

        if not user_id .strip ()or not token .strip ():
            logger .warning ("Missing user_id or token for validation")
            return False ,"auth"

        params ={
        "id":user_id .strip (),
        "token":token .strip ()
        }

        success ,response =self ._make_get_request ("/validateUserToken",params )

        if not success :

            error_msg =response .get ('error','Unknown error')
            logger .warning (f"Token validation request failed (network error): {error_msg}")
            return False ,"network"


        result =response .get ("result",{})
        if result .get ("type")==2 and result .get ("code")==0 :
            logger .info ("User token is valid")
            return True ,""
        else :

            if (result .get ("type")==0 and 
            result .get ("code")==6 and 
            result .get ("message")=="maintenance"):
                logger .warning ("API is in maintenance mode - keeping saved credentials")
                return False ,"network"


            error_code =result .get ("code",0 )
            error_name =self .ERROR_CODES .get (error_code ,"UNKNOWN_ERROR")
            error_msg =result .get ("message","Token validation failed")

            logger .warning (f"Token validation failed - {error_code} ({error_name}): {error_msg}")
            return False ,"auth"

    def get_usage_info (self ,user_id :str ,token :str )->Tuple [bool ,Dict [str ,Any ]]:
        """Get usage information from API.
        
        Args:
            user_id: Authenticated user ID
            token: Authentication token
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (success, data_or_error)
            - success: True if request was successful, False otherwise
            - data_or_error: Usage data dict on success, error dict on failure
        """
        if not user_id .strip ()or not token .strip ():
            logger .warning ("Missing user_id or token for usage request")
            return False ,{"error":"Missing authentication credentials"}

        params ={
        "user":user_id .strip (),
        "token":token .strip ()
        }

        success ,response =self ._make_get_request ("/vibe4d/v1/usage",params )

        if not success :

            error_msg =response .get ('error','Unknown error')
            logger .warning (f"Usage request failed (network error): {error_msg}")
            return False ,response 


        result =response .get ("result",{})
        if result .get ("type")==2 and result .get ("code")==0 :

            usage_data =response .get ("data",{})
            logger .info ("Usage information retrieved successfully")
            return True ,usage_data 
        else :

            error_code =result .get ("code",0 )
            error_name =self .ERROR_CODES .get (error_code ,"UNKNOWN_ERROR")
            error_msg =result .get ("message","Usage request failed")

            logger .warning (f"Usage request failed - {error_code} ({error_name}): {error_msg}")
            return False ,{"error":f"{error_name}: {error_msg}"}



api_client =APIClient ()