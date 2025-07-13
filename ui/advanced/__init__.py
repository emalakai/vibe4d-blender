"""
Advanced UI system for Vibe4D addon.
Provides a next-level custom UI with components, views, and advanced rendering.
"""

from .manager import UIManager ,ui_manager 
from .state import UIState 
from .renderer import UIRenderer 
from .types import Bounds ,CursorType ,EventType ,UIEvent 
from .theme import theme_manager ,get_themed_style 
from .colors import Colors 
from .blender_theme_integration import blender_theme ,get_theme_color 
from .component_theming import component_themer ,get_component_color 
from .ui_factory import ImprovedUIFactory ,ViewState 
from .layout_manager import layout_manager 
from .coordinates import CoordinateSystem 
from .viewport_button import viewport_button 


from .components import *
from .views import *
from .ui_state_manager import ui_state_manager ,UIStateManager 


from .panels import VIBE4D_PT_AdvancedUI 
from .ui import VIBE4D_PT_UITest 


from .import panels 
from .import ui 


classes =[]

__all__ =[
'UIManager',
'ui_manager',
'UIState',
'UIRenderer',
'Bounds',
'CursorType',
'EventType',
'UIEvent',
'theme_manager',
'get_themed_style',
'Colors',
'blender_theme',
'get_theme_color',
'component_themer',
'get_component_color',
'ImprovedUIFactory',
'ViewState',
'layout_manager',
'CoordinateSystem',
'ui_state_manager',
'UIStateManager',
'viewport_button',
'classes',
'panels',
'ui',
]


def register ():
    """Register the advanced UI system."""

    panels .register ()


    ui .register ()


    viewport_button .enable ()


def unregister ():
    """Unregister the advanced UI system."""

    viewport_button .disable ()


    if ui_manager :
        ui_manager .cleanup ()


    ui .unregister ()
    panels .unregister ()