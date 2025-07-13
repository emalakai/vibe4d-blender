"""
Utilities package for Vibe4D addon.
"""

from .logger import logger 
from .storage import secure_storage 
from .settings_manager import settings_manager 
from .scene_handler import scene_handler 
from .json_utils import BlenderJSONEncoder ,to_json_serializable 

classes =[]

__all__ =['classes','logger','secure_storage','settings_manager','scene_handler','BlenderJSONEncoder','to_json_serializable']


def register ():
    """Register utils module."""

    scene_handler .register ()
    pass 


def unregister ():
    """Unregister utils module."""

    scene_handler .unregister ()
    pass 
