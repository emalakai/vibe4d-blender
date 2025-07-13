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
    use_temp_file :bool =True 
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
            'status':'starting'
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


            render .filepath =output_path 
            render .image_settings .file_format ='PNG'
            render_info ['status']='rendering'


            logger .info (f"Starting render {render_id} to {output_path}")
            bpy .ops .render .render (write_still =True )

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
        Synchronous render operation (blocks until complete).
        
        Args:
            scene_name: Name of scene to render (None for current)
            camera_name: Name of camera to use (None for scene camera)
            output_path: Custom output path (None for temp file)
            
        Returns:
            Dictionary with render result data
            
        Raises:
            RuntimeError: If render fails
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


            use_temp_file =not output_path 
            if use_temp_file :
                temp_file =tempfile .NamedTemporaryFile (suffix ='.png',delete =False )
                output_path =temp_file .name 
                temp_file .close ()


            render =scene .render 
            original_filepath =render .filepath 
            original_file_format =render .image_settings .file_format 

            try :

                render .filepath =output_path 
                render .image_settings .file_format ='PNG'


                logger .info (f"Starting synchronous render to {output_path}")
                start_time =time .time ()
                bpy .ops .render .render (write_still =True )


                if not os .path .exists (output_path ):
                    raise RuntimeError ("Render completed but output file was not created")


                result_data =self ._create_sync_result (scene ,output_path ,start_time )

                logger .info (f"Synchronous render completed: {result_data['width']}x{result_data['height']}")
                return result_data 

            finally :

                render .filepath =original_filepath 
                render .image_settings .file_format =original_file_format 


                if original_camera :
                    scene .camera =original_camera 


                if use_temp_file and os .path .exists (output_path ):
                    try :
                        os .unlink (output_path )
                    except Exception as e :
                        logger .warning (f"Failed to clean up temporary file: {e}")

        except Exception as e :
            error_msg =f"Synchronous render failed: {str(e)}"
            logger .error (error_msg )
            raise RuntimeError (error_msg )

    def _create_sync_result (self ,scene ,output_path :str ,start_time :float )->Dict [str ,Any ]:
        """Create result data for synchronous render."""

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

        return {
        "data_uri":data_uri ,
        "width":width ,
        "height":height ,
        "render_resolution":[scene .render .resolution_x ,scene .render .resolution_y ],
        "render_percentage":scene .render .resolution_percentage ,
        "size_bytes":file_size ,
        "format":"PNG",
        "render_engine":scene .render .engine ,
        "camera_name":scene .camera .name ,
        "scene_name":scene .name ,
        "frame":scene .frame_current ,
        "render_time":time .time ()-start_time 
        }

    def cleanup (self ):
        """Clean up all resources."""

        for render_id in list (self .active_renders .keys ()):
            self ._cleanup_render (render_id )


        self .unregister_handlers ()



render_manager =RenderResultManager ()