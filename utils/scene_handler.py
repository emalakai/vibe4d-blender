"""
Scene change handler for Vibe4D addon.

Monitors scene changes to auto-accept pending executions.
"""

import bpy 
from bpy .app .handlers import persistent 

from .logger import logger 


class SceneChangeHandler :
    """Handles scene change monitoring and auto-acceptance."""

    def __init__ (self ):
        self .registered =False 
        self ._last_scene_name =None 
        self ._file_new_flag =False 
        self ._in_view_change =False 

    def register (self ):
        """Register scene update handlers."""
        if not self .registered :



            self ._last_scene_name =None 


            bpy .app .handlers .depsgraph_update_post .append (self ._on_scene_update )

            bpy .app .handlers .undo_post .append (self ._on_undo_redo )
            bpy .app .handlers .redo_post .append (self ._on_undo_redo )

            bpy .app .handlers .depsgraph_update_pre .append (self ._detect_scene_change )

            bpy .app .handlers .load_post .append (self ._on_file_load )

            bpy .app .handlers .load_pre .append (self ._on_file_load_pre )
            self .registered =True 
            logger .info ("Scene change handler registered successfully")
        else :
            logger .info ("Scene change handler already registered")

    def unregister (self ):
        """Unregister scene update handlers."""
        if self .registered :

            if self ._on_scene_update in bpy .app .handlers .depsgraph_update_post :
                bpy .app .handlers .depsgraph_update_post .remove (self ._on_scene_update )
            if self ._on_undo_redo in bpy .app .handlers .undo_post :
                bpy .app .handlers .undo_post .remove (self ._on_undo_redo )
            if self ._on_undo_redo in bpy .app .handlers .redo_post :
                bpy .app .handlers .redo_post .remove (self ._on_undo_redo )
            if self ._detect_scene_change in bpy .app .handlers .depsgraph_update_pre :
                bpy .app .handlers .depsgraph_update_pre .remove (self ._detect_scene_change )
            if self ._on_file_load in bpy .app .handlers .load_post :
                bpy .app .handlers .load_post .remove (self ._on_file_load )
            if self ._on_file_load_pre in bpy .app .handlers .load_pre :
                bpy .app .handlers .load_pre .remove (self ._on_file_load_pre )
            self .registered =False 
            logger .info ("Scene change handler unregistered")

    @persistent 
    def _on_scene_update (self ,scene ,depsgraph ):
        """Handle scene updates."""
        try :
            context =bpy .context 
            if not context .scene :
                return 

            execution_pending =getattr (context .scene ,'vibe4d_execution_pending',False )

            if not execution_pending :
                return 


            has_changes =False 


            for update in depsgraph .updates :
                if update .is_updated_transform or update .is_updated_geometry :
                    has_changes =True 
                    break 

            if has_changes :
                self ._auto_accept_execution (context )

        except Exception as e :
            logger .error (f"Error in scene update handler: {str(e)}")

    @persistent 
    def _on_undo_redo (self ,scene ):
        """Handle undo/redo operations."""
        try :
            context =bpy .context 
            if not context .scene :
                return 

            execution_pending =getattr (context .scene ,'vibe4d_execution_pending',False )

            if execution_pending :
                self ._auto_accept_execution (context )

        except Exception as e :
            logger .error (f"Error in undo/redo handler: {str(e)}")

    @persistent 
    def _detect_scene_change (self ,scene ,depsgraph ):
        """Detect when the user switches to a different scene."""
        try :
            context =bpy .context 
            if not context .scene :
                return 

            current_scene_name =context .scene .name 


            if self ._last_scene_name is None :
                self ._last_scene_name =current_scene_name 
                logger .debug (f"Initialized scene tracking: {current_scene_name}")
                return 


            if self ._last_scene_name !=current_scene_name :
                logger .info (f"Scene change detected in _detect_scene_change: {self._last_scene_name} -> {current_scene_name}")
                self ._handle_scene_switch (context ,self ._last_scene_name ,current_scene_name )


            self ._last_scene_name =current_scene_name 

        except Exception as e :
            logger .error (f"Error in scene change detection: {str(e)}")
            import traceback 
            logger .error (traceback .format_exc ())

    def _handle_scene_switch (self ,context ,old_scene_name :str ,new_scene_name :str ):
        """Handle when user switches to a different scene."""
        try :
            logger .info (f"Scene switch detected: {old_scene_name} -> {new_scene_name}")


            from .history_manager import history_manager 
            history_manager .on_scene_change (context )


            try :

                from ..ui .advanced .manager import ui_manager 

                if ui_manager .is_ui_active ():

                    if hasattr (ui_manager ,'factory')and ui_manager .factory :
                        current_view =ui_manager .factory .current_view 


                        if hasattr (ui_manager .factory ,'views')and ui_manager .factory .views :
                            from ..ui .advanced .ui_factory import ViewState 
                            main_view =ui_manager .factory .views .get (ViewState .MAIN )
                            if main_view and hasattr (main_view ,'components'):
                                message_scrollview =main_view .components .get ('message_scrollview')
                                if message_scrollview :
                                    message_scrollview .clear_children ()
                                    message_scrollview ._update_content_bounds ()
                                    logger .info ("Immediately cleared message scrollview for scene switch")


                        def delayed_ui_recreation ():
                            """Delayed UI recreation to ensure scene switch is complete."""
                            try :
                                logger .info ("Performing delayed UI recreation after scene switch")


                                current_context =bpy .context 
                                if current_context .scene .name ==new_scene_name :

                                    ui_manager ._recreate_ui_for_view_change (is_view_change =True )


                                    if ui_manager .state .target_area :
                                        ui_manager .state .target_area .tag_redraw ()

                                    logger .info ("Successfully recreated UI after scene switch")
                                else :
                                    logger .warning (f"Scene context mismatch during delayed recreation: expected {new_scene_name}, got {current_context.scene.name}")

                            except Exception as e :
                                logger .error (f"Error in delayed UI recreation: {str(e)}")
                                import traceback 
                                logger .error (traceback .format_exc ())

                            return None 


                        bpy .app .timers .register (delayed_ui_recreation ,first_interval =0.1 )
                        logger .info ("Scheduled delayed UI recreation for scene switch")

                    else :
                        logger .warning ("Factory not available for UI reload")
                else :
                    logger .debug ("UI not active, no need to reload")

            except Exception as e :
                logger .error (f"Failed to reload UI for scene change: {str(e)}")
                import traceback 
                logger .error (traceback .format_exc ())

        except Exception as e :
            logger .error (f"Error handling scene switch: {str(e)}")
            import traceback 
            logger .error (traceback .format_exc ())

    def _auto_accept_execution (self ,context ):
        """Auto-accept pending execution due to scene changes."""
        try :

            execution_pending =getattr (context .scene ,'vibe4d_execution_pending',False )
            if not execution_pending :
                return 


            context .scene .vibe4d_execution_pending =False 


            for prop in ['vibe4d_pre_exec_object_count','vibe4d_pre_exec_material_count',
            'vibe4d_pre_exec_mesh_count','vibe4d_pre_exec_undo_steps']:
                if hasattr (context .scene ,prop ):
                    try :
                        del context .scene [prop ]
                    except :
                        pass 


            if hasattr (context .scene ,'vibe4d_scene_modified'):
                context .scene .vibe4d_scene_modified =False 

            logger .info ("Auto-accepted execution due to scene changes")


            try :

                logger .debug ("Skipping old history update - using new chat message system")
            except Exception as e :
                logger .warning (f"Old history system cleanup: {str(e)}")


            try :
                for area in bpy .context .screen .areas :
                    if area .type =='VIEW_3D':
                        area .tag_redraw ()
            except :
                pass 

        except Exception as e :
            logger .error (f"Error in auto-accept execution: {str(e)}")

    @persistent 
    def _on_file_load (self ,*args ):
        """Handle file load events which include scene changes."""
        try :
            context =bpy .context 
            if not context .scene :
                return 

            current_scene_name =context .scene .name 


            if current_scene_name =="Scene"and self ._last_scene_name !="Scene":




                try :
                    from ..ui .advanced .manager import ui_manager 
                    if ui_manager .is_ui_active ():
                        ui_manager ._recreate_ui_for_view_change (is_view_change =True )
                        if ui_manager .state .target_area :
                            ui_manager .state .target_area .tag_redraw ()

                except Exception as e :
                    logger .error (f"Error recreating UI for new file: {str(e)}")


            if self ._last_scene_name is None :
                self ._last_scene_name =current_scene_name 
                return 


            if self ._last_scene_name !=current_scene_name :
                self ._handle_scene_switch (context ,self ._last_scene_name ,current_scene_name )


            self ._last_scene_name =current_scene_name 

        except Exception as e :
            logger .error (f"Error in file load handler: {str(e)}")
            import traceback 
            logger .error (traceback .format_exc ())

    @persistent 
    def _on_file_load_pre (self ,*args ):
        """Handle file load pre events - detect File -> New operations."""
        try :

            self ._file_new_flag =True 


            try :

                from ..ui .advanced .manager import ui_manager 

                if ui_manager .is_ui_active ():

                    if hasattr (ui_manager ,'factory')and ui_manager .factory :
                        if hasattr (ui_manager .factory ,'views')and ui_manager .factory .views :
                            from ..ui .advanced .ui_factory import ViewState 
                            main_view =ui_manager .factory .views .get (ViewState .MAIN )
                            if main_view and hasattr (main_view ,'components'):
                                message_scrollview =main_view .components .get ('message_scrollview')
                                if message_scrollview :
                                    message_scrollview .clear_children ()
                                    message_scrollview ._update_content_bounds ()


                    self ._last_scene_name =None 

            except Exception as e :
                logger .error (f"Error clearing UI for file operation: {str(e)}")

        except Exception as e :
            logger .error (f"Error in file load pre handler: {str(e)}")

    def check_and_clear_file_new_flag (self )->bool :
        """Check if File -> New just happened and clear the flag."""
        flag_was_set =self ._file_new_flag 
        self ._file_new_flag =False 


        if self ._in_view_change :
            return False 

        return flag_was_set 

    def set_view_change_flag (self ,in_view_change :bool ):
        """Set the view change flag to prevent false File -> New detection."""
        self ._in_view_change =in_view_change 

    def is_in_view_change (self )->bool :
        """Check if we're currently in a view change operation."""
        return self ._in_view_change 



scene_handler =SceneChangeHandler ()