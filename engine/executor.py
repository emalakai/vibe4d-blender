"""
Code execution engine for Vibe4D addon.

Handles safe code execution with rollback capabilities and error reporting.
"""

import bpy 
import traceback 
import sys 
import io 
from typing import Dict ,Any ,Optional ,Tuple ,List 
from contextlib import contextmanager 

from ..utils .logger import logger 
from .script_guard import script_guard 


class ExecutionState :
    """Tracks execution state for rollback functionality."""

    def __init__ (self ):
        self .scene_snapshot =None 
        self .objects_snapshot =None 
        self .materials_snapshot =None 
        self .meshes_snapshot =None 
        self .is_executing =False 
        self .execution_id =None 
        self .execution_content =""
        self .error_info =None 
        self .existing_data =None 

    def clear (self ):
        """Clear execution state."""
        self .scene_snapshot =None 
        self .objects_snapshot =None 
        self .materials_snapshot =None 
        self .meshes_snapshot =None 
        self .is_executing =False 
        self .execution_id =None 
        self .execution_content =""
        self .error_info =None 
        self .existing_data =None 


class PrintCapture :
    """Captures print statements and stores them for UI display."""

    def __init__ (self ,context ):
        self .context =context 
        self .outputs =[]
        self .original_stdout =sys .stdout 

    def write (self ,text ):
        """Capture written text."""
        if text .strip ():
            self .outputs .append (text .strip ())

            try :
                current_output =getattr (self .context .scene ,'vibe4d_console_output','')
                if current_output :
                    new_output =current_output +'\n'+text .strip ()
                else :
                    new_output =text .strip ()
                self .context .scene .vibe4d_console_output =new_output 
            except Exception as e :
                logger .error (f"Failed to update console output: {str(e)}")

    def flush (self ):
        """Required for stdout compatibility."""
        pass 

    def get_output (self ):
        """Get captured output as string."""
        return '\n'.join (self .outputs )


class CodeExecutor :
    """Handles safe code execution with rollback capabilities."""

    def __init__ (self ):
        self .execution_state =ExecutionState ()
        self .restricted_globals =self ._create_restricted_globals ()

    def _create_restricted_globals (self )->Dict [str ,Any ]:
        """Create restricted globals for safe execution."""

        import builtins 
        safe_builtins ={}


        excluded_builtins ={'eval','exec','compile','open','input','__import__'}

        for name in dir (builtins ):
            if not name .startswith ('_')or name in ['__name__','__doc__']:
                if name not in excluded_builtins :
                    safe_builtins [name ]=getattr (builtins ,name )

        return {
        '__builtins__':safe_builtins ,
        'bpy':bpy ,
        'bmesh':None ,
        'mathutils':None ,
        }

    def prepare_execution (self ,code :str )->Tuple [bool ,Optional [str ]]:
        """
        Prepare code for execution with safety checks.
        
        Args:
            code: Raw code content (may include markdown)
            
        Returns:
            Tuple of (success, error_message)
        """
        try :

            python_code =script_guard .extract_python_code (code )

            if not python_code .strip ():
                return False ,"No Python code found to execute"


            is_safe ,error_msg =script_guard .validate_code (python_code )
            if not is_safe :
                return False ,f"Security check failed: {error_msg}"


            self ._create_snapshot ()


            self .execution_state .execution_content =python_code 
            self .execution_state .is_executing =True 
            self .execution_state .execution_id =self ._generate_execution_id ()

            logger .info (f"Code prepared for execution (ID: {self.execution_state.execution_id})")
            return True ,None 

        except Exception as e :
            error_msg =f"Failed to prepare code execution: {str(e)}"
            logger .error (error_msg )
            return False ,error_msg 

    def execute_code (self ,context )->Tuple [bool ,Optional [str ]]:
        """
        Execute prepared code in safe environment.
        
        Args:
            context: Blender context
            
        Returns:
            Tuple of (success, error_message)
        """
        if not self .execution_state .is_executing :
            return False ,"No code prepared for execution"

        try :
            logger .info (f"Executing code (ID: {self.execution_state.execution_id})")


            context .scene .vibe4d_console_output =""


            safe_globals =self ._prepare_safe_globals ()
            safe_locals ={}


            print_capture =PrintCapture (context )
            original_stdout =sys .stdout 

            try :

                sys .stdout =print_capture 


                exec (self .execution_state .execution_content ,safe_globals ,safe_locals )

            finally :

                sys .stdout =original_stdout 


            context .view_layer .update ()
            bpy .ops .wm .redraw_timer (type ='DRAW_WIN_SWAP',iterations =1 )

            logger .info ("Code executed successfully")
            return True ,None 

        except Exception as e :

            sys .stdout =original_stdout 

            error_msg =str (e )
            error_traceback =traceback .format_exc ()


            self .execution_state .error_info ={
            'error':error_msg ,
            'traceback':error_traceback ,
            'execution_id':self .execution_state .execution_id 
            }

            logger .error (f"Code execution failed: {error_msg}")
            logger .debug (f"Full traceback: {error_traceback}")


            return self ._handle_execution_error (context ,error_msg ,error_traceback )

    def _create_snapshot (self ):
        """Create snapshot of current Blender state."""
        try :
            logger .debug ("Creating execution snapshot")


            self .execution_state .scene_snapshot ={
            'active_object':bpy .context .active_object .name if bpy .context .active_object else None ,
            'selected_objects':[obj .name for obj in bpy .context .selected_objects ],
            'cursor_location':bpy .context .scene .cursor .location .copy (),
            'frame_current':bpy .context .scene .frame_current 
            }


            existing_objects =set (obj .name for obj in bpy .data .objects )
            existing_meshes =set (mesh .name for mesh in bpy .data .meshes )
            existing_materials =set (mat .name for mat in bpy .data .materials )
            existing_textures =set (tex .name for tex in bpy .data .textures )
            existing_images =set (img .name for img in bpy .data .images )
            existing_curves =set (curve .name for curve in bpy .data .curves )
            existing_lights =set (light .name for light in bpy .data .lights )
            existing_cameras =set (cam .name for cam in bpy .data .cameras )


            self .execution_state .objects_snapshot ={}
            for obj in bpy .data .objects :
                self .execution_state .objects_snapshot [obj .name ]={
                'location':obj .location .copy (),
                'rotation_euler':obj .rotation_euler .copy (),
                'scale':obj .scale .copy (),
                'hide_viewport':obj .hide_viewport ,
                'hide_render':obj .hide_render ,
                'data_name':obj .data .name if obj .data else None 
                }


            self .execution_state .existing_data ={
            'objects':existing_objects ,
            'meshes':existing_meshes ,
            'materials':existing_materials ,
            'textures':existing_textures ,
            'images':existing_images ,
            'curves':existing_curves ,
            'lights':existing_lights ,
            'cameras':existing_cameras 
            }

            logger .debug ("Snapshot created successfully")

        except Exception as e :
            logger .error (f"Failed to create snapshot: {str(e)}")
            raise 

    def _rollback_changes (self ,context )->bool :
        """Rollback changes to snapshot state."""
        try :
            logger .debug ("Rolling back changes")

            if not self .execution_state .scene_snapshot or not self .execution_state .existing_data :
                logger .warning ("No snapshot available for rollback")
                return False 

            existing_data =self .execution_state .existing_data 


            objects_to_remove =[]
            for obj in bpy .data .objects :
                if obj .name not in existing_data ['objects']:
                    objects_to_remove .append (obj )

            logger .debug (f"Found {len(objects_to_remove)} new objects to remove")
            for obj in objects_to_remove :
                try :
                    logger .debug (f"Removing newly created object: {obj.name}")
                    bpy .data .objects .remove (obj ,do_unlink =True )
                except Exception as e :
                    logger .warning (f"Failed to remove object {obj.name}: {str(e)}")


            meshes_to_remove =[]
            for mesh in bpy .data .meshes :
                if mesh .name not in existing_data ['meshes']and mesh .users ==0 :
                    meshes_to_remove .append (mesh )

            logger .debug (f"Found {len(meshes_to_remove)} new meshes to remove")
            for mesh in meshes_to_remove :
                try :
                    logger .debug (f"Removing newly created mesh: {mesh.name}")
                    bpy .data .meshes .remove (mesh )
                except Exception as e :
                    logger .warning (f"Failed to remove mesh {mesh.name}: {str(e)}")


            materials_to_remove =[]
            for mat in bpy .data .materials :
                if mat .name not in existing_data ['materials']and mat .users ==0 :
                    materials_to_remove .append (mat )

            logger .debug (f"Found {len(materials_to_remove)} new materials to remove")
            for mat in materials_to_remove :
                try :
                    logger .debug (f"Removing newly created material: {mat.name}")
                    bpy .data .materials .remove (mat )
                except Exception as e :
                    logger .warning (f"Failed to remove material {mat.name}: {str(e)}")


            curves_to_remove =[]
            for curve in bpy .data .curves :
                if curve .name not in existing_data ['curves']and curve .users ==0 :
                    curves_to_remove .append (curve )

            logger .debug (f"Found {len(curves_to_remove)} new curves to remove")
            for curve in curves_to_remove :
                try :
                    logger .debug (f"Removing newly created curve: {curve.name}")
                    bpy .data .curves .remove (curve )
                except Exception as e :
                    logger .warning (f"Failed to remove curve {curve.name}: {str(e)}")


            lights_to_remove =[]
            for light in bpy .data .lights :
                if light .name not in existing_data ['lights']and light .users ==0 :
                    lights_to_remove .append (light )

            logger .debug (f"Found {len(lights_to_remove)} new lights to remove")
            for light in lights_to_remove :
                try :
                    logger .debug (f"Removing newly created light: {light.name}")
                    bpy .data .lights .remove (light )
                except Exception as e :
                    logger .warning (f"Failed to remove light {light.name}: {str(e)}")


            cameras_to_remove =[]
            for cam in bpy .data .cameras :
                if cam .name not in existing_data ['cameras']and cam .users ==0 :
                    cameras_to_remove .append (cam )

            logger .debug (f"Found {len(cameras_to_remove)} new cameras to remove")
            for cam in cameras_to_remove :
                try :
                    logger .debug (f"Removing newly created camera: {cam.name}")
                    bpy .data .cameras .remove (cam )
                except Exception as e :
                    logger .warning (f"Failed to remove camera {cam.name}: {str(e)}")


            images_to_remove =[]
            for img in bpy .data .images :
                if img .name not in existing_data ['images']and img .users ==0 :
                    images_to_remove .append (img )

            logger .debug (f"Found {len(images_to_remove)} new images to remove")
            for img in images_to_remove :
                try :
                    logger .debug (f"Removing newly created image: {img.name}")
                    bpy .data .images .remove (img )
                except Exception as e :
                    logger .warning (f"Failed to remove image {img.name}: {str(e)}")


            textures_to_remove =[]
            for tex in bpy .data .textures :
                if tex .name not in existing_data ['textures']and tex .users ==0 :
                    textures_to_remove .append (tex )

            logger .debug (f"Found {len(textures_to_remove)} new textures to remove")
            for tex in textures_to_remove :
                try :
                    logger .debug (f"Removing newly created texture: {tex.name}")
                    bpy .data .textures .remove (tex )
                except Exception as e :
                    logger .warning (f"Failed to remove texture {tex.name}: {str(e)}")


            for obj_name ,obj_state in self .execution_state .objects_snapshot .items ():
                if obj_name in bpy .data .objects :
                    obj =bpy .data .objects [obj_name ]
                    obj .location =obj_state ['location']
                    obj .rotation_euler =obj_state ['rotation_euler']
                    obj .scale =obj_state ['scale']
                    obj .hide_viewport =obj_state ['hide_viewport']
                    obj .hide_render =obj_state ['hide_render']


            scene_state =self .execution_state .scene_snapshot 


            context .scene .cursor .location =scene_state ['cursor_location']


            context .scene .frame_current =scene_state ['frame_current']


            bpy .ops .object .select_all (action ='DESELECT')
            for obj_name in scene_state ['selected_objects']:
                if obj_name in bpy .data .objects :
                    bpy .data .objects [obj_name ].select_set (True )


            if scene_state ['active_object']and scene_state ['active_object']in bpy .data .objects :
                context .view_layer .objects .active =bpy .data .objects [scene_state ['active_object']]


            context .view_layer .update ()
            bpy .ops .wm .redraw_timer (type ='DRAW_WIN_SWAP',iterations =1 )


            try :
                bpy .ops .outliner .orphans_purge (do_local_ids =True ,do_linked_ids =True ,do_recursive =True )
                logger .debug ("Orphaned data blocks purged")
            except Exception as e :
                logger .warning (f"Failed to purge orphaned data: {str(e)}")

            logger .debug ("Rollback completed successfully")
            return True 

        except Exception as e :
            logger .error (f"Rollback failed: {str(e)}")
            return False 

    def _prepare_safe_globals (self )->Dict [str ,Any ]:
        """Prepare safe globals for code execution."""
        safe_globals =self .restricted_globals .copy ()


        def safe_import (name ,globals =None ,locals =None ,fromlist =(),level =0 ):
            """Custom import function that blocks dangerous imports."""
            try :

                base_module =name .split ('.')[0 ]
                if base_module in script_guard .dangerous_imports :
                    logger .warning (f"Blocked dangerous import attempt: {name}")
                    raise ImportError (f"Import of '{name}' is not allowed for security reasons")


                logger .debug (f"Allowing safe import: {name}")


                return __import__ (name ,globals ,locals ,fromlist ,level )

            except ImportError as e :

                raise 
            except Exception as e :

                logger .error (f"Unexpected error during import of '{name}': {str(e)}")
                raise ImportError (f"Failed to import '{name}': {str(e)}")


        if isinstance (safe_globals ['__builtins__'],dict ):
            safe_globals ['__builtins__']=safe_globals ['__builtins__'].copy ()
            safe_globals ['__builtins__']['__import__']=safe_import 
        else :

            import builtins 
            safe_builtins_dict ={}
            for attr in dir (builtins ):
                if not attr .startswith ('_')or attr in ['__name__','__doc__']:
                    if attr =='__import__':
                        safe_builtins_dict [attr ]=safe_import 
                    elif attr not in {'eval','exec','compile','open','input'}:
                        safe_builtins_dict [attr ]=getattr (builtins ,attr )
            safe_globals ['__builtins__']=safe_builtins_dict 


        try :
            import bmesh 
            safe_globals ['bmesh']=bmesh 
        except ImportError :
            pass 

        try :
            import mathutils 
            safe_globals ['mathutils']=mathutils 
        except ImportError :
            pass 


        safe_modules =['math','random','time','datetime','json','re','collections',
        'itertools','functools','operator','copy','string','textwrap',
        'struct','array','heapq','bisect','weakref','types']

        for module_name in safe_modules :
            if module_name not in script_guard .dangerous_imports :
                try :
                    module =__import__ (module_name )
                    safe_globals [module_name ]=module 
                except ImportError :
                    pass 

        return safe_globals 

    def _generate_execution_id (self )->str :
        """Generate unique execution ID."""
        import time 
        return f"exec_{int(time.time() * 1000)}"

    def _handle_execution_error (self ,context ,error_msg :str ,traceback_str :str )->Tuple [bool ,Optional [str ]]:
        """
        Handle execution error by rolling back changes and reporting the error.
        
        Args:
            context: Blender context
            error_msg: Error message
            traceback_str: Full traceback string
            
        Returns:
            Tuple of (success, error_message)
        """
        try :

            clean_error_msg =self ._extract_clean_error_message (error_msg )


            logger .info ("Rolling back changes due to execution error")
            rollback_success =self ._rollback_changes (context )


            context .scene .vibe4d_console_output =""


            self .execution_state .clear ()

            if not rollback_success :
                logger .error ("Rollback failed")
                return False ,f"Execution failed and rollback unsuccessful: {clean_error_msg}"

            logger .info ("Changes rolled back successfully")
            return False ,clean_error_msg 

        except Exception as e :
            logger .error (f"Error in _handle_execution_error: {str(e)}")
            return False ,f"Error handling failed: {str(e)}"

    def _extract_clean_error_message (self ,error_msg :str )->str :
        """
        Extract clean error message from full error string and enhance with helpful context.
        
        Converts messages like:
        'Error: GeometryNodeTree object has no attribute inputs Traceback: ...'
        
        To clean messages like:
        'GeometryNodeTree object has no attribute inputs'
        
        Args:
            error_msg: Full error message string
            
        Returns:
            Clean, helpful error message
        """
        try :

            clean_msg =error_msg 
            if clean_msg .startswith ("Error: "):
                clean_msg =clean_msg [7 :]


            traceback_markers =[" Traceback:","\nTraceback","Traceback (most recent call last)"]
            for marker in traceback_markers :
                if marker in clean_msg :
                    clean_msg =clean_msg .split (marker )[0 ]
                    break 


            clean_msg =clean_msg .strip ()


            enhanced_msg =clean_msg 


            if "has no attribute"in clean_msg .lower ():
                if "bpy.context"in clean_msg :
                    enhanced_msg +="\n\n**Issue:** Invalid context access."
                    enhanced_msg +="\n**Solution:** Make sure you're accessing valid Blender context properties."
                elif "object"in clean_msg .lower ():
                    enhanced_msg +="\n\n**Issue:** Object property doesn't exist."
                    enhanced_msg +="\n**Solution:** Check if the object exists and has the requested property."
                else :
                    enhanced_msg +="\n\n**Issue:** Property or method doesn't exist."
                    enhanced_msg +="\n**Solution:** Check the Blender API documentation for correct property names."

            elif "keyerror"in clean_msg .lower ()or "key error"in clean_msg .lower ():
                enhanced_msg +="\n\n**Issue:** Dictionary key not found."
                enhanced_msg +="\n**Solution:** Check if the key exists before accessing it."

            elif "indexerror"in clean_msg .lower ()or "index error"in clean_msg .lower ():
                enhanced_msg +="\n\n**Issue:** List index out of range."
                enhanced_msg +="\n**Solution:** Make sure the list has enough elements before accessing by index."

            elif "typeerror"in clean_msg .lower ()or "type error"in clean_msg .lower ():
                if "unsupported operand"in clean_msg .lower ():
                    enhanced_msg +="\n\n**Issue:** Operation not supported between these data types."
                    enhanced_msg +="\n**Solution:** Check that you're using compatible data types for the operation."
                elif "can't convert"in clean_msg .lower ():
                    enhanced_msg +="\n\n**Issue:** Type conversion failed."
                    enhanced_msg +="\n**Solution:** Make sure the data can be converted to the target type."
                else :
                    enhanced_msg +="\n\n**Issue:** Incorrect data type used."
                    enhanced_msg +="\n**Solution:** Check that you're passing the correct data type to the function."

            elif "nameerror"in clean_msg .lower ()or "name error"in clean_msg .lower ():
                enhanced_msg +="\n\n**Issue:** Variable or function name not defined."
                enhanced_msg +="\n**Solution:** Make sure all variables and functions are properly defined before use."

            elif "syntaxerror"in clean_msg .lower ()or "syntax error"in clean_msg .lower ():
                enhanced_msg +="\n\n**Issue:** Python syntax error in the generated code."
                enhanced_msg +="\n**Solution:** The AI generated invalid Python syntax. Try rephrasing your request."

            elif "indentationerror"in clean_msg .lower ():
                enhanced_msg +="\n\n**Issue:** Incorrect code indentation."
                enhanced_msg +="\n**Solution:** Python requires proper indentation. Try regenerating the code."

            elif "valueerror"in clean_msg .lower ()or "value error"in clean_msg .lower ():
                enhanced_msg +="\n\n**Issue:** Invalid value provided to function."
                enhanced_msg +="\n**Solution:** Check that the values being passed are within acceptable ranges."

            elif "runtimeerror"in clean_msg .lower ():
                if "context is incorrect"in clean_msg .lower ()or "context"in clean_msg .lower ():
                    enhanced_msg +="\n\n**Issue:** Blender context error."
                    enhanced_msg +="\n**Solution:** Make sure you're in the right mode (Edit, Object, etc.) for this operation."
                else :
                    enhanced_msg +="\n\n**Issue:** Runtime error during execution."
                    enhanced_msg +="\n**Solution:** Check if all required objects and properties exist."

            elif "permission"in clean_msg .lower ()or "access"in clean_msg .lower ():
                enhanced_msg +="\n\n**Issue:** Permission or access denied."
                enhanced_msg +="\n**Solution:** Make sure Blender has the necessary permissions for this operation."

            elif "file not found"in clean_msg .lower ()or "no such file"in clean_msg .lower ():
                enhanced_msg +="\n\n**Issue:** File or path not found."
                enhanced_msg +="\n**Solution:** Check that the file path is correct and the file exists."

            elif "memory"in clean_msg .lower ():
                enhanced_msg +="\n\n**Issue:** Memory error."
                enhanced_msg +="\n**Solution:** Try working with smaller datasets or restart Blender to free memory."

            elif "timeout"in clean_msg .lower ():
                enhanced_msg +="\n\n**Issue:** Operation timed out."
                enhanced_msg +="\n**Solution:** Try breaking the task into smaller operations."

            else :

                if len (clean_msg )>10 :
                    enhanced_msg +="\n\n**Tip:** If this error persists, try simplifying your request or asking for a different approach."

            return enhanced_msg 

        except Exception as e :
            logger .error (f"Failed to extract clean error message: {str(e)}")
            return error_msg 

    def accept_execution (self ,context )->bool :
        """
        Accept the execution results and clear state.
        
        Args:
            context: Blender context
            
        Returns:
            True if accepted successfully
        """
        try :
            if not self .execution_state .is_executing :
                logger .warning ("No execution to accept")
                return False 

            logger .info (f"Accepting execution (ID: {self.execution_state.execution_id})")


            self .execution_state .clear ()


            context .scene .vibe4d_final_code =""
            context .scene .vibe4d_last_error =""
            context .scene .vibe4d_console_output =""
            context .scene .vibe4d_prompt =""


            for area in bpy .context .screen .areas :
                if area .type =='VIEW_3D':
                    area .tag_redraw ()

            logger .info ("Execution accepted successfully")
            return True 

        except Exception as e :
            logger .error (f"Failed to accept execution: {str(e)}")
            return False 

    def reject_execution (self ,context )->bool :
        """
        Reject the execution and rollback changes.
        
        Args:
            context: Blender context
            
        Returns:
            True if rollback successful
        """
        try :
            if not self .execution_state .is_executing :
                logger .warning ("No execution to reject")
                return False 

            logger .info (f"Rejecting execution (ID: {self.execution_state.execution_id})")


            rollback_success =self ._rollback_changes (context )

            if not rollback_success :
                logger .error ("Rollback failed during rejection")
                return False 


            self .execution_state .clear ()


            context .scene .vibe4d_final_code =""
            context .scene .vibe4d_last_error =""
            context .scene .vibe4d_console_output =""
            context .scene .vibe4d_execution_pending =False 
            context .scene .vibe4d_prompt =""


            for area in bpy .context .screen .areas :
                if area .type =='VIEW_3D':
                    area .tag_redraw ()

            logger .info ("Execution rejected and changes rolled back successfully")
            return True 

        except Exception as e :
            logger .error (f"Failed to reject execution: {str(e)}")
            return False 



code_executor =CodeExecutor ()