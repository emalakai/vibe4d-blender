"""
Advanced UI Panels for Vibe4D Addon
"""

import bpy 
from bpy .types import Panel ,Operator 


class VIBE4D_PT_AdvancedUI (Panel ):
    """Advanced UI panel for Vibe4D addon."""
    bl_label ="Advanced UI"
    bl_idname ="VIBE4D_PT_advanced_ui"
    bl_space_type ='VIEW_3D'
    bl_region_type ='UI'
    bl_category ='Vibe4D'

    def draw (self ,context ):
        """Draw the panel UI."""
        layout =self .layout 


        from .manager import ui_manager 


        is_active =ui_manager .is_ui_active ()


        row =layout .row ()
        row .scale_y =1.5 
        row .scale_x =1 


        if is_active :

            row .alert =True 
            row .operator ("vibe4d.show_advanced_ui",icon ='PANEL_CLOSE',text ="Close Advanced UI")
        else :

            row .operator ("vibe4d.show_advanced_ui",icon ='WINDOW',text ="Open Advanced UI")


        layout .separator ()
        layout .label (text ="Debug Tools:")


        layout .operator ("debug.print_agent_request",icon ='CONSOLE',text ="Print Agent Request")



classes =[
VIBE4D_PT_AdvancedUI ,
]


def register ():
    """Register all panels."""
    for cls in classes :
        bpy .utils .register_class (cls )


def unregister ():
    """Unregister all panels."""
    for cls in reversed (classes ):
        bpy .utils .unregister_class (cls )