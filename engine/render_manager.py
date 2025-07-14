"""
Render result manager for Vibe4D addon.

Provides comprehensive render result access using Blender 4.4 API methods.
Handles both synchronous and asynchronous render operations with proper callbacks.
"""

import bpy 
import os 
import tempfile 
import base64 
import time 
from typing import Dict ,Any ,Optional ,Callable ,List ,Tuple 
from bpy .app .handlers import persistent 

from ..utils .logger import logger 


class RenderResultManager :
    """Manages render operations and result access with Blender 4.4 API."""

    def __init__ (self ):
        self .active_renders ={}
        self .render_callbacks ={}
        self .render_handlers_registered =False 
        self ._render_counter =0 

    def register_handlers (self ):
        """Register render completion handlers."""
        if not self .render_handlers_registered :

            bpy .app .handlers .render_complete .append (self ._on_render_complete )
            bpy .app .handlers .render_cancel .append (self ._on_render_cancel )
            bpy .app .handlers .render_write .append (self ._on_render_write )
            self .render_handlers_registered =True 
            logger .info ("Render handlers registered")

    def unregister_handlers (self ):
        """Unregister render completion handlers."""
        if self .render_handlers_registered :
            if self ._on_render_complete in bpy .app .handlers .render_complete :
                bpy .app .handlers .render_complete .remove (self ._on_render_complete )
            if self ._on_render_cancel in bpy .app .handlers .render_cancel :
                bpy .app .handlers .render_cancel .remove (self ._on_render_cancel )
            if self ._on_render_write in bpy .app .handlers .render_write :
                bpy .app .handlers .render_write .remove (self ._on_render_write )
            self .render_handlers_registered =False 
            logger .info ("Render handlers unregistered")

    def start_render_with_callback (
    self ,
    scene_name :Optional [str ]=None ,
    camera_name :Optional [str ]=None ,
    on_complete :Optional [Callable [[Dict [str ,Any ]],None ]]=None ,
    on_error :Optional [Callable [[str ],None ]]=None ,
    output_path :Optional [str ]=None ,
    use_temp_file :bool =False 
    )->str :
        """
        Start a render operation with completion callback.
        
        Args:
            scene_name: Name of scene to render (None for current)
            camera_name: Name of camera to use (None for scene camera)
            on_complete: Callback for successful completion
            on_error: Callback for error handling
            output_path: Custom output path (None for temp file)
            use_temp_file: Whether to use temporary file for output
            
        Returns:
            Render ID for tracking
        """
        try :

            self ._render_counter +=1 
            render_id =f"render_{self._render_counter}_{int(time.time() * 1000)}"


            scene =bpy .data .scenes .get (scene_name )if scene_name else bpy .context .scene 
            if not scene :
                error_msg =f"Scene '{scene_name}' not found"
                if on_error :
                    on_error (error_msg )
                return ""


            original_camera =scene .camera 
            if camera_name :
                camera =bpy .data .objects .get (camera_name )
                if not camera or camera .type !='CAMERA':
                    error_msg =f"Camera '{camera_name}' not found or not a camera"
                    if on_error :
                        on_error (error_msg )
                    return ""
                scene .camera =camera 


            if not scene .camera :
                error_msg ="No active camera found in scene"
                if on_error :
                    on_error (error_msg )
                return ""


            logger .info ("Checking for existing render result...")
            existing_result =self ._get_existing_render_result (scene ,scene .camera )
            if existing_result :
                logger .info ("Found existing render result, returning it immediately")

                existing_result ['render_id']=render_id 
                if on_complete :
                    on_complete (existing_result )
                return render_id 


            logger .info ("No existing render result found, starting new render")


            if use_temp_file or not output_path :
                temp_file =tempfile .NamedTemporaryFile (suffix ='.png',delete =False )
                output_path =temp_file .name 
                temp_file .close ()


            render_info ={
            'render_id':render_id ,
            'scene':scene ,
            'camera':scene .camera ,
            'original_camera':original_camera ,
            'output_path':output_path ,
            'use_temp_file':use_temp_file ,
            'on_complete':on_complete ,
            'on_error':on_error ,
            'start_time':time .time (),
            'status':'starting',
            'user_visible':True 
            }

            self .active_renders [render_id ]=render_info 
            self .render_callbacks [render_id ]={
            'on_complete':on_complete ,
            'on_error':on_error 
            }


            render =scene .render 
            original_filepath =render .filepath 
            original_file_format =render .image_settings .file_format 

            render_info ['original_filepath']=original_filepath 
            render_info ['original_file_format']=original_file_format 


            if use_temp_file or not output_path :
                render .filepath =output_path 
                render .image_settings .file_format ='PNG'
            else :

                render .filepath =output_path 
                render .image_settings .file_format ='PNG'

            render_info ['status']='rendering'



            logger .info (f"Starting user-visible render {render_id} to {output_path}")
            bpy .ops .render .render ('INVOKE_DEFAULT',animation =False ,write_still =False )

            return render_id 

        except Exception as e :
            error_msg =f"Failed to start render: {str(e)}"
            logger .error (error_msg )
            if on_error :
                on_error (error_msg )
            return ""

    def get_render_result (self ,render_id :str )->Optional [Dict [str ,Any ]]:
        """
        Get render result for a completed render.
        
        Args:
            render_id: Render ID from start_render_with_callback
            
        Returns:
            Dictionary with render result data or None if not found
        """
        if render_id not in self .active_renders :
            return None 

        render_info =self .active_renders [render_id ]

        if render_info ['status']!='complete':
            return None 

        return render_info .get ('result_data')

    def cancel_render (self ,render_id :str )->bool :
        """
        Cancel an active render operation.
        
        Args:
            render_id: Render ID to cancel
            
        Returns:
            True if cancellation was successful
        """
        if render_id not in self .active_renders :
            return False 

        try :

            bpy .ops .render .render (cancel =True )

            render_info =self .active_renders [render_id ]
            render_info ['status']='cancelled'


            if render_info ['on_error']:
                render_info ['on_error']("Render cancelled")


            self ._cleanup_render (render_id )

            return True 

        except Exception as e :
            logger .error (f"Error cancelling render {render_id}: {str(e)}")
            return False 

    def get_active_renders (self )->List [str ]:
        """Get list of active render IDs."""
        return [rid for rid ,info in self .active_renders .items ()
        if info ['status']in ['starting','rendering']]

    def is_render_active (self ,render_id :str )->bool :
        """Check if a render is currently active."""
        return render_id in self .active_renders and self .active_renders [render_id ]['status']in ['starting','rendering']

    @persistent 
    def _on_render_complete (self ,scene ,depsgraph =None ):
        """Handle render completion."""
        try :

            completed_render =None 
            for render_id ,render_info in self .active_renders .items ():
                if render_info ['status']=='rendering'and render_info ['scene']==scene :
                    completed_render =render_id 
                    break 

            if not completed_render :
                logger .debug ("Render completed but no matching active render found")
                return 

            render_info =self .active_renders [completed_render ]
            output_path =render_info ['output_path']


            if not os .path .exists (output_path ):

                if hasattr (scene ,'render')and hasattr (scene .render ,'result'):
                    render_result =scene .render .result 
                    if render_result and hasattr (render_result ,'save_render'):

                        render_result .save_render (output_path )
                        logger .info (f"Saved render result to {output_path}")
                    else :
                        error_msg ="Render completed but no render result available"
                        logger .error (error_msg )
                        if render_info ['on_error']:
                            render_info ['on_error'](error_msg )
                        self ._cleanup_render (completed_render )
                        return 
                else :
                    error_msg ="Render completed but output file not found"
                    logger .error (error_msg )
                    if render_info ['on_error']:
                        render_info ['on_error'](error_msg )
                    self ._cleanup_render (completed_render )
                    return 


            result_data =self ._process_render_result (completed_render ,output_path )

            if result_data :
                render_info ['result_data']=result_data 
                render_info ['status']='complete'


                if render_info ['on_complete']:
                    render_info ['on_complete'](result_data )

                logger .info (f"Render {completed_render} completed successfully")
            else :
                error_msg ="Failed to process render result"
                logger .error (error_msg )
                if render_info ['on_error']:
                    render_info ['on_error'](error_msg )


            def cleanup_later ():
                self ._cleanup_render (completed_render )
                return None 

            bpy .app .timers .register (cleanup_later ,first_interval =1.0 )

        except Exception as e :
            logger .error (f"Error in render complete handler: {str(e)}")

    @persistent 
    def _on_render_cancel (self ,scene ,depsgraph =None ):
        """Handle render cancellation."""
        try :

            for render_id ,render_info in list (self .active_renders .items ()):
                if render_info ['status']=='rendering'and render_info ['scene']==scene :
                    render_info ['status']='cancelled'

                    if render_info ['on_error']:
                        render_info ['on_error']("Render was cancelled")

                    self ._cleanup_render (render_id )

        except Exception as e :
            logger .error (f"Error in render cancel handler: {str(e)}")

    @persistent 
    def _on_render_write (self ,scene ,depsgraph =None ):
        """Handle render frame write (called after each frame is written)."""
        try :


            logger .debug (f"Render frame written for scene: {scene.name}")

        except Exception as e :
            logger .error (f"Error in render write handler: {str(e)}")

    def _get_existing_render_result (self ,scene ,camera )->Optional [dict ]:
        """
        Try to harvest the most recent "Render Result" image and convert it into
        the same dictionary structure returned by :meth:`render_sync`.

        Parameters
        ----------
        scene : bpy.types.Scene | None
            Scene that would otherwise be rendered (unused here, kept for parity).
        camera : bpy.types.Object | None
            Camera that would otherwise be rendered (unused here, kept for parity).

        Returns
        -------
        dict | None
            A dict compatible with _process_render_result(), or *None* if no
            usable cached frame exists.
        """

        tmp =tempfile .NamedTemporaryFile (suffix =".png",delete =False )
        output_path =tmp .name 
        tmp .close ()

        try :

            for img in bpy .data .images :

                if img .type =='RENDER_RESULT':
                    try :
                        img .filepath_raw =output_path 
                        img .file_format ='PNG'
                        img .save ()
                        logger .debug (f"Saved render result: {img.name} to {output_path}")
                        break 
                    except Exception as e :
                        logger .warning (f"Could not save {img.name}: {e}")
                        continue 
            else :
                logger .debug ("No render result image could be saved.")
                return None 


            existing_id =f"existing_{int(time.time() * 1000)}"
            render_info ={
            'render_id':existing_id ,
            'scene':scene ,
            'camera':camera ,
            'output_path':output_path ,
            'start_time':time .time ()-0.1 ,
            'status':'complete'
            }


            self .active_renders [existing_id ]=render_info 

            try :

                result =self ._process_render_result (existing_id ,output_path )
                return result 
            finally :

                if existing_id in self .active_renders :
                    del self .active_renders [existing_id ]

        finally :

            try :
                os .unlink (output_path )
            except Exception :
                pass 

    def _process_render_result (self ,render_id :str ,output_path :str )->Optional [Dict [str ,Any ]]:
        """
        Process render result and create result data.
        
        Args:
            render_id: Render ID
            output_path: Path to rendered image
            
        Returns:
            Dictionary with render result data
        """
        try :
            render_info =self .active_renders [render_id ]
            scene =render_info ['scene']
            camera =render_info ['camera']


            file_size =os .path .getsize (output_path )


            with open (output_path ,'rb')as f :
                image_data =f .read ()


            width ,height =scene .render .resolution_x ,scene .render .resolution_y 
            try :

                from PIL import Image 
                with Image .open (output_path )as img :
                    width ,height =img .size 
            except ImportError :

                percentage =scene .render .resolution_percentage /100.0 
                width =int (scene .render .resolution_x *percentage )
                height =int (scene .render .resolution_y *percentage )


            base64_data =base64 .b64encode (image_data ).decode ('utf-8')
            data_uri =f"data:image/png;base64,{base64_data}"


            result_data ={
            "render_id":render_id ,
            "data_uri":data_uri ,
            "width":width ,
            "height":height ,
            "render_resolution":[scene .render .resolution_x ,scene .render .resolution_y ],
            "render_percentage":scene .render .resolution_percentage ,
            "size_bytes":file_size ,
            "format":"PNG",
            "render_engine":scene .render .engine ,
            "camera_name":camera .name ,
            "scene_name":scene .name ,
            "frame":scene .frame_current ,
            "output_path":output_path ,
            "render_time":time .time ()-render_info ['start_time']
            }

            logger .info (f"Processed render result: {width}x{height}, {file_size} bytes")
            return result_data 

        except Exception as e :
            logger .error (f"Error processing render result: {str(e)}")
            return None 

    def _cleanup_render (self ,render_id :str ):
        """Clean up render resources."""
        try :
            if render_id not in self .active_renders :
                return 

            render_info =self .active_renders [render_id ]


            scene =render_info ['scene']
            if scene and scene .render :
                scene .render .filepath =render_info .get ('original_filepath','')
                scene .render .image_settings .file_format =render_info .get ('original_file_format','PNG')


            if render_info .get ('original_camera'):
                scene .camera =render_info ['original_camera']


            if render_info .get ('use_temp_file',True ):
                output_path =render_info .get ('output_path')
                if output_path and os .path .exists (output_path ):
                    try :
                        os .unlink (output_path )
                    except Exception as e :
                        logger .warning (f"Failed to clean up temporary file: {e}")


            del self .active_renders [render_id ]
            if render_id in self .render_callbacks :
                del self .render_callbacks [render_id ]

            logger .debug (f"Cleaned up render {render_id}")

        except Exception as e :
            logger .error (f"Error cleaning up render {render_id}: {str(e)}")




    def render_sync (
    self ,
    scene_name :Optional [str ]=None ,
    camera_name :Optional [str ]=None ,
    output_path :Optional [str ]=None 
    )->Dict [str ,Any ]:
        """
        Check for existing render result without performing new renders.
        
        Args:
            scene_name: Name of scene to check (None for current)
            camera_name: Name of camera to check (None for scene camera)
            output_path: Custom output path (unused in check-only mode)
            
        Returns:
            Dictionary with render result data or message if no result found
        """
        try :

            scene =bpy .data .scenes .get (scene_name )if scene_name else bpy .context .scene 
            if not scene :
                raise RuntimeError (f"Scene '{scene_name}' not found")


            original_camera =scene .camera 
            if camera_name :
                camera =bpy .data .objects .get (camera_name )
                if not camera or camera .type !='CAMERA':
                    raise RuntimeError (f"Camera '{camera_name}' not found or not a camera")
                scene .camera =camera 


            if not scene .camera :
                raise RuntimeError ("No active camera found in scene")


            logger .info ("Checking for existing render result...")
            existing_result =self ._get_existing_render_result (scene ,scene .camera )
            if existing_result :
                logger .info ("Found existing render result, returning it")
                return existing_result 


            logger .info ("No existing render result found")
            return {
            "message":"No render result found. Ask user if you should render image with execute tool or they can do that themselves"
            }

        except Exception as e :
            error_msg =f"Failed to check for render result: {str(e)}"
            logger .error (error_msg )
            raise RuntimeError (error_msg )

    def cleanup (self ):
        """Clean up all resources."""

        for render_id in list (self .active_renders .keys ()):
            self ._cleanup_render (render_id )


        self .unregister_handlers ()



render_manager =RenderResultManager ()