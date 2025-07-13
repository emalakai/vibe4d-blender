

import bpy 
from .import base 
from .import auth 
from .import instructions 
from .import execution 
from .import history 
from .import keymap 
from .import debug 
from .import ui_test 
from .import viewport_button 


classes =[]
classes .extend (base .classes )
classes .extend (auth .classes )
classes .extend (instructions .classes )
classes .extend (execution .classes )
classes .extend (history .classes )
classes .extend (debug .classes )
classes .extend (ui_test .classes )
classes .extend (viewport_button .classes )

__all__ =['classes']


def register ():
    """Register operators module."""
    for cls in classes :
        bpy .utils .register_class (cls )


    keymap .register ()


def unregister ():
    """Unregister operators module."""

    keymap .unregister ()


    for cls in reversed (classes ):
        try :
            bpy .utils .unregister_class (cls )
        except :
            pass 