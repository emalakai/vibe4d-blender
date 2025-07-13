"""
UI Test operators for the advanced UI system.
"""

import bpy 
import logging 
from bpy .types import Operator 
from bpy .props import StringProperty 

from ..ui .advanced .manager import UIManager 
from ..ui .advanced .types import EventType ,CursorType 
from ..ui .advanced .state import UIState 

logger =logging .getLogger (__name__ )



def get_ui_manager ():
    """Get the UI manager instance."""
    from ..ui .advanced .manager import ui_manager 
    return ui_manager 


class VIBE4D_OT_ui_modal_handler (Operator ):
    """Combined modal operator for handling both mouse and keyboard events."""
    bl_idname ="vibe4d.ui_modal_handler"
    bl_label ="Vibe4D UI Modal Handler"
    bl_description ="Handle input events for the advanced UI"
    bl_options ={'REGISTER'}

    def modal (self ,context ,event ):
        """Handle modal events."""
        from ..ui .advanced .manager import ui_manager 

        if not ui_manager .state .is_enabled :
            return {'CANCELLED'}


        self ._handle_cursor_updates (context ,ui_manager ,event )


        if event .type =='LEFTMOUSE'and event .value =='PRESS':

            if not ui_manager ._mouse_in_target_area (event ):
                if ui_manager .state .focused_component :
                    ui_manager .state .set_focus (None )
                    if ui_manager .state .target_area :
                        ui_manager .state .target_area .tag_redraw ()

                return {'PASS_THROUGH'}


        result =ui_manager .handle_mouse_event (context ,event )
        if result =='RUNNING_MODAL':
            return {'RUNNING_MODAL'}


        result =ui_manager .handle_keyboard_event (context ,event )
        if result =='RUNNING_MODAL':
            return {'RUNNING_MODAL'}

        return {'PASS_THROUGH'}

    def _handle_cursor_updates (self ,context ,ui_manager ,event ):
        """Handle cursor updates within modal context."""
        try :

            if hasattr (ui_manager ,'_cursor_requests')and ui_manager ._cursor_requests :
                cursor_request =ui_manager ._cursor_requests .pop (0 )

                if cursor_request ['action']=='set':
                    cursor_type =cursor_request ['cursor_type']
                    is_override =cursor_request .get ('is_override',False )

                    if is_override :
                        self ._cursor_override =cursor_type 
                    else :
                        self ._current_cursor =cursor_type 


                    actual_cursor =getattr (self ,'_cursor_override',None )or getattr (self ,'_current_cursor',CursorType .DEFAULT )


                    if context .window :
                        context .window .cursor_modal_set (actual_cursor .value )

                elif cursor_request ['action']=='clear_override':
                    if hasattr (self ,'_cursor_override')and self ._cursor_override :
                        self ._cursor_override =None 
                        actual_cursor =getattr (self ,'_current_cursor',CursorType .DEFAULT )
                        if context .window :
                            context .window .cursor_modal_set (actual_cursor .value )

                elif cursor_request ['action']=='reset':
                    self ._cursor_override =None 
                    self ._current_cursor =CursorType .DEFAULT 
                    if context .window :
                        context .window .cursor_modal_set (CursorType .DEFAULT .value )


            if event .type =='MOUSEMOVE':

                if ui_manager ._mouse_in_target_area (event ):
                    region_x ,region_y =ui_manager ._screen_to_region_coords (event ,ui_manager .state .target_area )
                    if region_x is not None and region_y is not None :
                        component =ui_manager .state .get_component_at_point (region_x ,region_y )

                        if component :
                            desired_cursor =component .get_cursor_type ()
                            current_cursor =getattr (self ,'_cursor_override',None )or getattr (self ,'_current_cursor',CursorType .DEFAULT )

                            if desired_cursor !=current_cursor :
                                ui_manager .request_cursor_change (desired_cursor )
                        else :

                            current_cursor =getattr (self ,'_cursor_override',None )or getattr (self ,'_current_cursor',CursorType .DEFAULT )
                            if current_cursor !=CursorType .DEFAULT :
                                ui_manager .request_cursor_change (CursorType .DEFAULT )

        except Exception as e :
            logger .error (f"Error handling cursor updates: {e}")

    def invoke (self ,context ,event ):
        """Initialize cursor state and start modal handler."""

        self ._current_cursor =CursorType .DEFAULT 
        self ._cursor_override =None 
        context .window_manager .modal_handler_add (self )
        return {'RUNNING_MODAL'}


class VIBE4D_OT_show_advanced_ui (Operator ):
    """Operator for showing/hiding the advanced UI."""
    bl_idname ="vibe4d.show_advanced_ui"
    bl_label ="Show Advanced UI"
    bl_description ="Toggle the advanced UI overlay"
    bl_options ={'REGISTER'}

    def execute (self ,context ):
        """Execute the operator."""
        from ..ui .advanced .manager import ui_manager 

        if ui_manager .is_ui_active ():

            target_area =ui_manager .state .target_area 
            ui_manager .disable_overlay ()
            self ._close_ui (context ,ui_manager ,target_area )
            self .report ({'INFO'},"Vibe4D panel closed")
        else :

            target_area =self ._open_ui (context )
            if target_area :
                ui_manager .enable_overlay (target_area )
                self .report ({'INFO'},"Vibe4D panel opened")
            else :
                self .report ({'ERROR'},"Failed to create UI viewport")
                return {'CANCELLED'}

        return {'FINISHED'}

    def _open_ui (self ,context ):
        """Open the UI panel by splitting the viewport."""

        area =context .area 

        if not area or area .type !='VIEW_3D':
            self .report ({'ERROR'},"Please run this from a 3D Viewport")
            return None 


        bpy .ops .screen .area_split (direction ='VERTICAL',factor =0.3 )


        new_ui_area =None 
        for new_area in context .screen .areas :
            if new_area !=area and new_area .type =='VIEW_3D':

                if new_area .width <area .width :
                    new_ui_area =new_area 
                    break 

        if new_ui_area :

            for space in new_ui_area .spaces :
                if space .type =='VIEW_3D':

                    space .show_gizmo =False 
                    space .show_region_ui =False 
                    space .show_region_toolbar =False 
                    space .show_region_header =False 
                    space .show_region_hud =False 


                    space .overlay .show_overlays =False 


                    space .shading .type ='SOLID'
                    space .shading .show_xray =False 
                    space .shading .show_shadows =False 
                    space .shading .show_cavity =False 
                    space .shading .show_object_outline =False 
                    space .shading .show_specular_highlight =False 
                    space .shading .show_backface_culling =True 


                    space .lens =50 
                    space .clip_start =0.1 
                    space .clip_end =100 
                    break 

            return new_ui_area 

        return None 

    def _close_ui (self ,context ,ui_manager ,target_area ):
        """Close the UI panel by deleting the viewport area."""
        if not target_area :
            logger .warning ("No target area to close")
            return 


        area_exists =False 
        for area in context .screen .areas :
            if area ==target_area :
                area_exists =True 
                break 

        if not area_exists :
            logger .warning ("Target area no longer exists in screen")
            return 


        other_view3d_areas =[area for area in context .screen .areas 
        if area .type =='VIEW_3D'and area !=target_area ]

        if not other_view3d_areas :
            return 



        best_area =None 
        best_score =-1 

        for area in other_view3d_areas :
            score =0 



            if abs (area .x -(target_area .x +target_area .width ))<5 :
                score +=100 

                overlap =min (area .y +area .height ,target_area .y +target_area .height )-max (area .y ,target_area .y )
                if overlap >0 :
                    score +=overlap 


            elif abs ((area .x +area .width )-target_area .x )<5 :
                score +=100 

                overlap =min (area .y +area .height ,target_area .y +target_area .height )-max (area .y ,target_area .y )
                if overlap >0 :
                    score +=overlap 


            elif abs (area .y -(target_area .y +target_area .height ))<5 :
                score +=100 

                overlap =min (area .x +area .width ,target_area .x +target_area .width )-max (area .x ,target_area .x )
                if overlap >0 :
                    score +=overlap 


            elif abs ((area .y +area .height )-target_area .y )<5 :
                score +=100 

                overlap =min (area .x +area .width ,target_area .x +target_area .width )-max (area .x ,target_area .x )
                if overlap >0 :
                    score +=overlap 


            else :
                score =area .width *area .height 

            if score >best_score :
                best_score =score 
                best_area =area 

        if not best_area :
            logger .error ("No suitable area found to expand into target area")
            return 


        success =False 


        try :

            cursor_x =None 
            cursor_y =None 


            if abs (best_area .x -(target_area .x +target_area .width ))<5 :
                cursor_x =target_area .x +target_area .width 
                cursor_y =max (best_area .y ,target_area .y )+min (best_area .height ,target_area .height )//2 


            elif abs ((best_area .x +best_area .width )-target_area .x )<5 :
                cursor_x =target_area .x 
                cursor_y =max (best_area .y ,target_area .y )+min (best_area .height ,target_area .height )//2 


            elif abs (best_area .y -(target_area .y +target_area .height ))<5 :
                cursor_y =target_area .y +target_area .height 
                cursor_x =max (best_area .x ,target_area .x )+min (best_area .width ,target_area .width )//2 


            elif abs ((best_area .y +best_area .height )-target_area .y )<5 :
                cursor_y =target_area .y 
                cursor_x =max (best_area .x ,target_area .x )+min (best_area .width ,target_area .width )//2 


            if cursor_x is not None and cursor_y is not None :


                with context .temp_override (area =best_area ):
                    bpy .ops .screen .area_join (cursor =(cursor_x ,cursor_y ))

                success =True 
            else :
                pass 

        except Exception as e :
            logger .warning (f"area_join failed: {e}")


        if not success :
            try :
                with context .temp_override (area =target_area ):
                    bpy .ops .screen .area_close ()

                success =True 

            except Exception as e :
                logger .warning (f"area_close failed: {e}")


        if not success :
            try :

                with context .temp_override (area =best_area ):
                    bpy .ops .screen .area_split (direction ='VERTICAL',factor =0.99 )


                tiny_area =None 
                for area in context .screen .areas :
                    if area !=best_area and area !=target_area and area .type =='VIEW_3D':
                        if area .width <100 :
                            tiny_area =area 
                            break 

                if tiny_area :

                    with context .temp_override (area =tiny_area ):
                        cursor_x =target_area .x +target_area .width //2 
                        cursor_y =target_area .y +target_area .height //2 
                        bpy .ops .screen .area_join (cursor =(cursor_x ,cursor_y ))

                    success =True 
                else :
                    logger .error ("Could not create tiny area for force close")

            except Exception as e :
                logger .error (f"Force close method failed: {e}")

        if success :
            pass 
        else :
            logger .error ("All methods to close UI area failed")


class VIBE4D_OT_ui_settings_close (Operator ):
    """Operator for closing the settings overlay."""
    bl_idname ="vibe4d.ui_settings_close"
    bl_label ="Close Settings"
    bl_description ="Close the settings overlay"
    bl_options ={'REGISTER'}

    def execute (self ,context ):
        """Execute the operator."""
        from ..ui .advanced .manager import ui_manager 
        ui_manager .factory .close_settings ()
        return {'FINISHED'}


class VIBE4D_OT_test_no_connection_view (Operator ):
    """Operator to test the no connection view."""
    bl_idname ="vibe4d.test_no_connection_view"
    bl_label ="Test No Connection View"
    bl_description ="Test the no connection view functionality"
    bl_options ={'REGISTER'}

    def execute (self ,context ):
        """Execute the operator."""
        from ..ui .advanced .manager import ui_manager 
        from ..ui .advanced .ui_factory import ViewState 


        if not ui_manager .is_ui_active ():
            self .report ({'WARNING'},"Advanced UI is not active. Please open it first.")
            return {'CANCELLED'}

        try :

            ui_manager .demo_no_connection_view ()
            self .report ({'INFO'},"Switched to no connection view")
            return {'FINISHED'}

        except Exception as e :
            logger .error (f"Error testing no connection view: {e}")
            self .report ({'ERROR'},f"Failed to test no connection view: {str(e)}")
            return {'CANCELLED'}


class VIBE4D_OT_test_connectivity (Operator ):
    """Operator to test connectivity and switch views accordingly."""
    bl_idname ="vibe4d.test_connectivity"
    bl_label ="Test Connectivity"
    bl_description ="Test internet connectivity and switch to appropriate view"
    bl_options ={'REGISTER'}

    def execute (self ,context ):
        """Execute the operator."""
        from ..ui .advanced .manager import ui_manager 


        if not ui_manager .is_ui_active ():
            self .report ({'WARNING'},"Advanced UI is not active. Please open it first.")
            return {'CANCELLED'}

        try :

            ui_manager .test_connectivity_and_update_view ()
            return {'FINISHED'}

        except Exception as e :
            logger .error (f"Error testing connectivity: {e}")
            self .report ({'ERROR'},f"Failed to test connectivity: {str(e)}")
            return {'CANCELLED'}


class VIBE4D_OT_ui_mouse_handler (Operator ):
    """Modal operator for handling mouse events."""
    bl_idname ="vibe4d.ui_mouse_handler"
    bl_label ="Mouse Handler"
    bl_description ="Handle mouse events for the UI"
    bl_options ={'REGISTER'}

    def modal (self ,context ,event ):
        """Handle modal events."""
        from ..ui .advanced .manager import ui_manager 
        result =ui_manager .handle_mouse_event (context ,event )
        if result =='RUNNING_MODAL':
            return {'RUNNING_MODAL'}
        return {'PASS_THROUGH'}

    def execute (self ,context ):
        """Execute the operator."""
        context .window_manager .modal_handler_add (self )
        return {'RUNNING_MODAL'}


class VIBE4D_OT_ui_debug_test (Operator ):
    """Debug test operator."""
    bl_idname ="vibe4d.ui_debug_test"
    bl_label ="Debug Test"
    bl_description ="Run debug tests"
    bl_options ={'REGISTER'}

    def execute (self ,context ):
        """Execute the operator."""
        try :
            from ..ui .advanced .manager import ui_manager 

            logger .info ("=== UI Debug Test ===")


            is_active =ui_manager .is_ui_active ()
            logger .info (f"UI Active: {is_active}")

            if is_active :

                component_count =len (ui_manager .state .components )
                logger .info (f"Components: {component_count}")


                has_layout =ui_manager .ui_layout is not None 
                logger .info (f"Has Layout: {has_layout}")


                width =ui_manager .state .viewport_width 
                height =ui_manager .state .viewport_height 
                logger .info (f"Viewport: {width}x{height}")


                has_target =ui_manager .state .target_area is not None 
                logger .info (f"Has Target Area: {has_target}")


                if hasattr (ui_manager ,'factory'):
                    current_view =ui_manager .factory .current_view .value 
                    logger .info (f"Current View: {current_view}")


                if component_count ==0 or not has_layout :
                    logger .info ("UI appears incomplete, attempting reinitialization...")
                    success =ui_manager .force_ui_reinitialization ()
                    if success :
                        self .report ({'INFO'},"UI reinitialization successful")
                    else :
                        self .report ({'ERROR'},"UI reinitialization failed")
                else :
                    self .report ({'INFO'},f"UI appears healthy: {component_count} components")
            else :
                logger .info ("UI is not active")
                self .report ({'INFO'},"UI is not active")

        except Exception as e :
            logger .error (f"Error in debug test: {e}")
            self .report ({'ERROR'},f"Debug test failed: {e}")

        return {'FINISHED'}


class VIBE4D_OT_ui_keyboard_handler (Operator ):
    """Modal operator for handling keyboard events."""
    bl_idname ="vibe4d.ui_keyboard_handler"
    bl_label ="Keyboard Handler"
    bl_description ="Handle keyboard events for the UI"
    bl_options ={'REGISTER'}

    def modal (self ,context ,event ):
        """Handle modal events."""
        from ..ui .advanced .manager import ui_manager 
        result =ui_manager .handle_keyboard_event (context ,event )
        if result =='RUNNING_MODAL':
            return {'RUNNING_MODAL'}
        return {'PASS_THROUGH'}

    def execute (self ,context ):
        """Execute the operator."""
        context .window_manager .modal_handler_add (self )
        return {'RUNNING_MODAL'}


class VIBE4D_OT_ui_login (Operator ):
    """Operator for handling login submissions."""
    bl_idname ="vibe4d.ui_login"
    bl_label ="UI Login"
    bl_description ="Handle login form submission"
    bl_options ={'REGISTER'}

    username :StringProperty (
    name ="Username",
    description ="Username for login",
    default =""
    )

    password :StringProperty (
    name ="Password",
    description ="Password for login",
    default ="",
    subtype ='PASSWORD'
    )

    def execute (self ,context ):
        """Execute the operator."""
        from ..ui .advanced .manager import ui_manager 


        if self .username and self .password :

            ui_manager .authenticate_success ()
            self .report ({'INFO'},f"Logged in as {self.username}")
        else :
            self .report ({'ERROR'},"Please enter both username and password")

        return {'FINISHED'}



classes =[
VIBE4D_OT_ui_modal_handler ,
VIBE4D_OT_show_advanced_ui ,
VIBE4D_OT_ui_settings_close ,
VIBE4D_OT_test_no_connection_view ,
VIBE4D_OT_test_connectivity ,
VIBE4D_OT_ui_mouse_handler ,
VIBE4D_OT_ui_debug_test ,
VIBE4D_OT_ui_keyboard_handler ,
VIBE4D_OT_ui_login ,
]


def register ():
    """Register UI test operators."""
    for cls in classes :
        bpy .utils .register_class (cls )


def unregister ():
    """Unregister UI test operators."""
    for cls in reversed (classes ):
        try :
            bpy .utils .unregister_class (cls )
        except :
            pass 