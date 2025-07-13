"""
Secure storage utility for Vibe4D addon.

Handles persistent storage of user credentials and custom instructions.
"""

import json 
import os 
from pathlib import Path 
from typing import Dict ,Optional ,List 

from .logger import logger 


class SecureStorage :
    """Secure storage for user credentials and settings."""

    def __init__ (self ):

        self .config_dir =Path .home ()/".config"/"blender"/"vibe4d"
        self .credentials_file =self .config_dir /"credentials.json"
        self .instructions_file =self .config_dir /"instructions.json"
        self .settings_file =self .config_dir /"settings.json"


        self .config_dir .mkdir (parents =True ,exist_ok =True )

    def save_credentials (self ,user_id :str ,token :str ,email :str ="",plan :str ="")->bool :
        """Save user credentials securely."""
        try :
            credentials ={
            "user_id":user_id ,
            "token":token ,
            "email":email ,
            "plan":plan 
            }


            with open (self .credentials_file ,'w')as f :
                json .dump (credentials ,f ,indent =2 )


            os .chmod (self .credentials_file ,0o600 )

            logger .info ("User credentials saved securely")
            return True 

        except Exception as e :
            logger .error (f"Failed to save credentials: {str(e)}")
            return False 

    def load_credentials (self )->Optional [Dict [str ,str ]]:
        """Load saved user credentials."""
        try :
            if not self .credentials_file .exists ():
                logger .debug ("No saved credentials found")
                return None 

            with open (self .credentials_file ,'r')as f :
                credentials =json .load (f )


            if not credentials .get ("user_id")or not credentials .get ("token"):
                logger .warning ("Invalid credentials file - missing required fields")
                return None 

            logger .info ("User credentials loaded successfully")
            return credentials 

        except json .JSONDecodeError as e :
            logger .error (f"Invalid credentials file format: {str(e)}")
            return None 
        except Exception as e :
            logger .error (f"Failed to load credentials: {str(e)}")
            return None 

    def clear_credentials (self )->bool :
        """Clear saved user credentials."""
        try :
            if self .credentials_file .exists ():
                self .credentials_file .unlink ()
                logger .info ("User credentials cleared")
            return True 

        except Exception as e :
            logger .error (f"Failed to clear credentials: {str(e)}")
            return False 

    def save_custom_instructions (self ,instructions )->bool :
        """Save custom instructions to persistent storage."""
        try :

            if isinstance (instructions ,dict )and ("agent"in instructions or "ask"in instructions ):

                data ={
                "instructions":instructions ,
                "version":"2.0"
                }
            else :

                instructions_data =[]
                for instruction in instructions :
                    if isinstance (instruction ,dict ):
                        instructions_data .append ({
                        "text":instruction .get ("text",""),
                        "enabled":instruction .get ("enabled",True )
                        })
                    elif isinstance (instruction ,str ):

                        instructions_data .append ({
                        "text":instruction ,
                        "enabled":True 
                        })

                data ={
                "instructions":instructions_data ,
                "version":"1.0"
                }


            with open (self .instructions_file ,'w')as f :
                json .dump (data ,f ,indent =2 )


            os .chmod (self .instructions_file ,0o600 )

            if isinstance (instructions ,dict ):
                agent_count =len (instructions .get ("agent",[]))
                ask_count =len (instructions .get ("ask",[]))
                logger .info (f"Saved {agent_count} agent and {ask_count} ask custom instructions")
            else :
                logger .info (f"Saved {len(instructions)} custom instructions")
            return True 

        except Exception as e :
            logger .error (f"Failed to save custom instructions: {str(e)}")
            return False 

    def load_custom_instructions (self ):
        """Load saved custom instructions."""
        try :
            if not self .instructions_file .exists ():
                logger .debug ("No saved custom instructions found")
                return None 

            with open (self .instructions_file ,'r')as f :
                data =json .load (f )


            if isinstance (data ,dict ):
                version =data .get ("version","1.0")

                if version =="2.0":

                    instructions =data .get ("instructions",{})
                    if not isinstance (instructions ,dict ):
                        logger .warning ("Invalid instructions format in version 2.0 file")
                        return None 


                    for mode in ["agent","ask"]:
                        mode_instructions =instructions .get (mode ,[])
                        if not isinstance (mode_instructions ,list ):
                            logger .warning (f"Invalid {mode} instructions format")
                            return None 


                        for instruction in mode_instructions :
                            if isinstance (instruction ,str ):

                                instruction ={"text":instruction ,"enabled":True }
                            elif not isinstance (instruction ,dict )or "text"not in instruction :
                                logger .warning (f"Invalid {mode} instruction format in file")
                                return None 


                            if "enabled"not in instruction :
                                instruction ["enabled"]=True 

                    return instructions 

                elif version =="1.0"or "instructions"in data :

                    legacy_instructions =data .get ("instructions",[])

                    if not isinstance (legacy_instructions ,list ):
                        logger .warning ("Invalid legacy instructions format")
                        return None 


                    converted_instructions =[]
                    for instruction in legacy_instructions :
                        if isinstance (instruction ,str ):

                            converted_instructions .append ({
                            "text":instruction ,
                            "enabled":True 
                            })
                        elif isinstance (instruction ,dict ):
                            if "text"not in instruction :
                                logger .warning ("Invalid instruction format in legacy file")
                                return None 


                            if "enabled"not in instruction :
                                instruction ["enabled"]=True 
                            converted_instructions .append (instruction )
                        else :
                            logger .warning ("Invalid instruction type in legacy file")
                            return None 

                    return converted_instructions 

            elif isinstance (data ,list ):

                converted_instructions =[]
                for instruction in data :
                    if isinstance (instruction ,str ):
                        converted_instructions .append ({
                        "text":instruction ,
                        "enabled":True 
                        })
                    elif isinstance (instruction ,dict ):
                        if "text"not in instruction :
                            logger .warning ("Invalid instruction format in old file")
                            return None 
                        if "enabled"not in instruction :
                            instruction ["enabled"]=True 
                        converted_instructions .append (instruction )
                    else :
                        logger .warning ("Invalid instruction type in old file")
                        return None 

                return converted_instructions 

            logger .warning ("Unknown instructions file format")
            return None 

        except json .JSONDecodeError as e :
            logger .error (f"Invalid instructions file format: {str(e)}")
            return None 
        except Exception as e :
            logger .error (f"Failed to load custom instructions: {str(e)}")
            return None 

    def clear_custom_instructions (self )->bool :
        """Clear saved custom instructions."""
        try :
            if self .instructions_file .exists ():
                self .instructions_file .unlink ()
                logger .info ("Custom instructions cleared")
            return True 

        except Exception as e :
            logger .error (f"Failed to clear custom instructions: {str(e)}")
            return False 

    def save_settings (self ,model :str ,mode :str )->bool :
        """Save global settings (model and mode) - legacy method."""
        try :
            settings_data ={
            "model":model ,
            "mode":mode ,
            "version":"1.0"
            }


            with open (self .settings_file ,'w')as f :
                json .dump (settings_data ,f ,indent =2 )


            os .chmod (self .settings_file ,0o600 )

            logger .debug (f"Saved global settings: model={model}, mode={mode}")
            return True 

        except Exception as e :
            logger .error (f"Failed to save settings: {str(e)}")
            return False 

    def save_all_settings (self ,settings_data :Dict [str ,str ])->bool :
        """Save all settings including agent/ask models."""
        try :
            data ={
            "agent_model":settings_data .get ("agent_model","gpt-4.1-mini"),
            "ask_model":settings_data .get ("ask_model","gpt-4.1-mini"),
            "model":settings_data .get ("model","gpt-4.1-mini"),
            "mode":settings_data .get ("mode","agent"),
            "version":"2.0"
            }


            with open (self .settings_file ,'w')as f :
                json .dump (data ,f ,indent =2 )


            os .chmod (self .settings_file ,0o600 )

            logger .debug (f"Saved all settings: agent_model={data['agent_model']}, ask_model={data['ask_model']}, mode={data['mode']}")
            return True 

        except Exception as e :
            logger .error (f"Failed to save all settings: {str(e)}")
            return False 

    def load_settings (self )->Optional [Dict [str ,str ]]:
        """Load saved global settings."""
        try :
            if not self .settings_file .exists ():
                logger .debug ("No saved settings found, using defaults")
                return None 

            with open (self .settings_file ,'r')as f :
                data =json .load (f )


            if not isinstance (data ,dict ):
                logger .warning ("Invalid settings file format")
                return None 

            version =data .get ("version","1.0")

            if version =="2.0":

                settings ={
                "agent_model":data .get ("agent_model","gpt-4.1-mini"),
                "ask_model":data .get ("ask_model","gpt-4.1-mini"),
                "model":data .get ("model","gpt-4.1-mini"),
                "mode":data .get ("mode","agent")
                }
                logger .debug (f"Loaded settings (v{version}): agent_model={settings['agent_model']}, ask_model={settings['ask_model']}, mode={settings['mode']}")
            else :

                legacy_model =data .get ("model","gpt-4.1-mini")
                settings ={
                "agent_model":legacy_model ,
                "ask_model":legacy_model ,
                "model":legacy_model ,
                "mode":data .get ("mode","agent")
                }
                logger .debug (f"Loaded legacy settings (v{version}): model={legacy_model}, mode={settings['mode']}")

            return settings 

        except json .JSONDecodeError as e :
            logger .error (f"Invalid settings file format: {str(e)}")
            return None 
        except Exception as e :
            logger .error (f"Failed to load settings: {str(e)}")
            return None 

    def clear_settings (self )->bool :
        """Clear saved global settings."""
        try :
            if self .settings_file .exists ():
                self .settings_file .unlink ()
                logger .info ("Global settings cleared")
            return True 

        except Exception as e :
            logger .error (f"Failed to clear settings: {str(e)}")
            return False 



secure_storage =SecureStorage ()