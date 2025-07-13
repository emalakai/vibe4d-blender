"""
Base view class for all UI views.
Provides common functionality and structure.
"""

from abc import ABC ,abstractmethod 
from typing import Dict ,Any ,Callable ,Optional 
import logging 

from ..layout_manager import LayoutManager ,layout_manager 
from ..types import Bounds 

logger =logging .getLogger (__name__ )


class BaseView (ABC ):
    """Base class for all UI views."""

    def __init__ (self ,layout_mgr :LayoutManager =None ):
        self .layout_manager =layout_mgr or layout_manager 
        self .layouts :Dict [str ,str ]={}
        self .components :Dict [str ,Any ]={}
        self .callbacks :Dict [str ,Callable ]={}
        self .view_id =self .__class__ .__name__ .lower ().replace ('view','')

    def set_callbacks (self ,**callbacks ):
        """Set callback functions for this view."""
        self .callbacks .update (callbacks )



    @abstractmethod 
    def create_layout (self ,viewport_width :int ,viewport_height :int )->Dict [str ,Any ]:
        """Create the layout for this view."""
        pass 

    @abstractmethod 
    def update_layout (self ,viewport_width :int ,viewport_height :int ):
        """Update layout positions when viewport changes."""
        pass 

    def get_focused_component (self ):
        """Get the component that should be focused by default."""
        return None 

    def cleanup (self ):
        """Clean up resources for this view."""
        self .layouts .clear ()
        self .components .clear ()

    def _create_layout_container (self ,name :str ,config )->str :
        """Helper to create layout containers with consistent naming."""
        layout_name =f"{self.view_id}_{name}"
        return self .layout_manager .create_layout (layout_name ,config )

    def _get_all_components (self )->list :
        """Get a flat list of all components."""
        return list (self .components .values ())