"""
Error handling utilities for the Vibe4D addon.

Provides functions for formatting and displaying error messages consistently.
"""

import re 
from typing import List ,Optional ,Dict ,Any 
from .logger import logger 


def format_error_message (error_code :str ,user_message :str ,suggestions :List [str ]=None ,
retryable :bool =True ,technical_info :str =None )->str :
    return user_message 


def extract_error_type (error_message :str )->str :
    """
    Extract error type from error message for categorization.
    
    Args:
        error_message: The error message string
        
    Returns:
        Error type category
    """
    try :
        error_lower =error_message .lower ()


        if any (term in error_lower for term in ['connection','network','timeout','unreachable']):
            return 'network'


        if any (term in error_lower for term in ['auth','license','credential','unauthorized']):
            return 'authentication'


        if any (term in error_lower for term in ['rate limit','quota','too many requests']):
            return 'rate_limit'


        if any (term in error_lower for term in ['syntax','indentation','nameerror','typeerror']):
            return 'code_error'


        if any (term in error_lower for term in ['permission','access denied','forbidden']):
            return 'permission'


        if any (term in error_lower for term in ['service','maintenance','unavailable']):
            return 'service'

        return 'general'

    except Exception as e :
        logger .error (f"Error extracting error type: {e}")
        return 'general'


def get_error_severity (error_code :str )->str :
    """
    Get the severity level of an error.
    
    Args:
        error_code: The error code
        
    Returns:
        Severity level: 'low', 'medium', 'high', 'critical'
    """
    try :

        critical_errors ={
        'AUTHENTICATION_FAILED','SYSTEM_MISCONFIGURED',
        'SKILL_LOADING_FAILED','FEATURE_NOT_AVAILABLE'
        }


        high_errors ={
        'PLAN_LIMIT_EXCEEDED','AI_SERVICE_UNAVAILABLE',
        'CODE_GENERATION_FAILED','DB_ERROR'
        }


        medium_errors ={
        'RATE_LIMIT','INVALID_CODE_GENERATED',
        'CODE_CORRECTION_FAILED','NO_ACTIONS_GENERATED'
        }


        low_errors ={
        'INVALID_REQUEST','INTERNAL_ERROR','LLM_ERROR',
        'SKILL_SETUP_FAILED'
        }

        if error_code in critical_errors :
            return 'critical'
        elif error_code in high_errors :
            return 'high'
        elif error_code in medium_errors :
            return 'medium'
        elif error_code in low_errors :
            return 'low'
        else :
            return 'medium'

    except Exception as e :
        logger .error (f"Error determining error severity: {e}")
        return 'medium'


def should_show_retry_button (error_code :str ,retryable :bool )->bool :
    """
    Determine if a retry button should be shown for an error.
    
    Args:
        error_code: The error code
        retryable: Whether the backend says the error is retryable
        
    Returns:
        True if retry button should be shown
    """
    try :

        no_retry_errors ={
        'AUTHENTICATION_FAILED','PLAN_LIMIT_EXCEEDED',
        'FEATURE_NOT_AVAILABLE','SYSTEM_MISCONFIGURED'
        }

        if error_code in no_retry_errors :
            return False 


        always_retry_errors ={
        'INTERNAL_ERROR','AI_SERVICE_UNAVAILABLE',
        'LLM_ERROR','DB_ERROR'
        }

        if error_code in always_retry_errors :
            return True 


        return retryable 

    except Exception as e :
        logger .error (f"Error determining retry button visibility: {e}")
        return retryable 


def create_chat_error_message (error_type :str ,error_message :str ,suggestions :List [str ]=None )->str :
    """
    Create a formatted error message specifically for chat display.
    
    Args:
        error_type: The type of error (e.g., "API Error", "Tool Error", "Authentication Error")
        error_message: The main error message
        suggestions: Optional list of suggestions for the user
        
    Returns:
        Formatted error message string ready for chat display
    """
    try :

        formatted_msg =f"❌ **{error_type}**\n\n"


        formatted_msg +=f"{error_message}\n\n"

        return formatted_msg 

    except Exception as e :
        logger .error (f"Error creating chat error message: {e}")
        return f"❌ **{error_type}:** {error_message}"


def create_error_context (error_data )->Dict [str ,Any ]:
    """
    Create a comprehensive error context for debugging and display.
    
    Args:
        error_data: Error data dictionary from the API or string error message
        
    Returns:
        Enhanced error context
    """
    try :
        if isinstance (error_data ,dict ):
            error_code =error_data .get ('code','UNKNOWN')
            user_message =error_data .get ('user_message','An error occurred')
            suggestions =[]
            retryable =error_data .get ('retryable',True )
            technical_info =error_data .get ('technical_info','')
        else :

            error_code =str (error_data )

            if error_code .lower ().startswith ('error'):
                user_message =error_code 
            else :
                user_message =f"{error_code}"
            suggestions =[]
            retryable =True 
            technical_info =''

        return {
        'code':error_code ,
        'message':user_message ,
        'suggestions':suggestions ,
        'retryable':retryable ,
        'technical_info':technical_info ,
        'severity':get_error_severity (error_code ),
        'type':extract_error_type (user_message ),
        'show_retry':should_show_retry_button (error_code ,retryable ),
        'formatted_message':format_error_message (
        error_code ,user_message ,suggestions ,retryable ,technical_info 
        )
        }

    except Exception as e :
        logger .error (f"Error creating error context: {e}")
        return {
        'code':'UNKNOWN',
        'message':'An unexpected error occurred',
        'suggestions':['Try again in a moment'],
        'retryable':True ,
        'technical_info':str (e ),
        'severity':'medium',
        'type':'general',
        'show_retry':True ,
        'formatted_message':'An unexpected error occurred'
        }