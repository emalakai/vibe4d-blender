"""
Header button component for toolbar actions.
"""

import logging 
from .button import Button 
from ..theme import get_themed_style 

logger =logging .getLogger (__name__ )


class HeaderButton (Button ):
    """Styled button for header actions."""

    def __init__ (self ,text :str ,x :int =0 ,y :int =0 ,width :int =70 ,height :int =35 ,on_click =None ):
        super ().__init__ (text ,x ,y ,width ,height ,corner_radius =6 ,on_click =on_click )


        self .style =get_themed_style ("button")


        self .style .font_size =14 