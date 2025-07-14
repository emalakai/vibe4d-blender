"""
Tools module for Vibe4D addon.

Implements backend tools that can be called by the AI assistant:
- execute: Code execution (existing)
- query: Scene data querying with SQL-like syntax
- custom_props: Custom properties access
- render_settings: Render configuration retrieval
- scene_graph: Scene hierarchy analysis  
- nodes_graph: Node tree information
- render_async: Asynchronous render with callback support
"""

import bpy 
import gpu 
from gpu .types import GPUTexture 
import base64 
import array 
import tempfile 
import os 
import time 
from typing import Dict ,Any ,List ,Optional ,Tuple 
from mathutils import Vector ,Matrix ,Euler ,Quaternion ,Color 

from ..utils .logger import logger 
from ..utils .json_utils import to_json_serializable 
from .executor import code_executor 
from .query import scene_query_engine 
from .render_manager import render_manager 


class ToolsManager :
    """Manages and dispatches tool calls."""

    def __init__ (self ):
        self .tools ={
        'execute':self ._execute_tool ,
        'query':self ._query_tool ,
        'scene_context':self ._scene_context_tool ,
        'viewport':self ._viewport_tool ,
        'add_viewport_render':self ._viewport_tool ,
        'see_viewport':self ._viewport_tool ,
        'see_render':self ._see_render_tool ,
        'render_async':self ._render_async_tool ,
        'get_render_result':self ._get_render_result_tool ,
        'cancel_render':self ._cancel_render_tool ,
        'list_active_renders':self ._list_active_renders_tool 
        }


        render_manager .register_handlers ()

    def handle_tool_call (self ,tool_name :str ,arguments :Dict [str ,Any ],context )->Tuple [bool ,Any ]:
        """Handle a tool call."""
        if tool_name not in self .tools :
            return False ,f"Unknown tool: {tool_name}"

        try :
            return self .tools [tool_name ](arguments ,context )
        except Exception as e :
            logger .error (f"Error in tool '{tool_name}': {str(e)}")
            return False ,str (e )

    def _execute_tool (self ,arguments :Dict [str ,Any ],context )->Tuple [bool ,Any ]:
        """Execute Python code."""
        try :
            code =arguments .get ("code","")
            if not code :
                return False ,"No code provided"



            prepare_success ,prepare_error =code_executor .prepare_execution (code )
            if not prepare_success :
                return False ,{"result":prepare_error or "Code preparation failed"}


            success ,error =code_executor .execute_code (context )

            if success :

                console_output =getattr (context .scene ,'vibe4d_console_output','')
                if console_output :
                    result =console_output 
                else :
                    result ="Code executed successfully"

                return True ,{"result":result }
            else :
                return False ,{"result":error or "Code execution failed"}

        except Exception as e :
            logger .error (f"Execute tool error: {str(e)}")
            return False ,{"result":f"Execution error: {str(e)}"}

    def _query_tool (self ,arguments :Dict [str ,Any ],context )->Tuple [bool ,Any ]:
        """Query scene data."""
        try :
            query =arguments .get ("expr","")
            if not query :
                return False ,{"result":"No query provided"}


            limit =arguments .get ("limit",8192 )
            format_type =arguments .get ("format","json")


            result =scene_query_engine .execute_query (query ,limit ,context ,format_type )



            return True ,{"result":result }

        except Exception as e :
            logger .error (f"Query tool error: {str(e)}")
            return False ,{"result":f"Query error: {str(e)}"}

    def _scene_context_tool (self ,arguments :Dict [str ,Any ],context )->Tuple [bool ,Any ]:
        """Get scene context information."""
        try :

            scene_info ={
            "scene_name":context .scene .name ,
            "frame_current":context .scene .frame_current ,
            "frame_start":context .scene .frame_start ,
            "frame_end":context .scene .frame_end ,
            "render_engine":context .scene .render .engine ,
            "camera":context .scene .camera .name if context .scene .camera else None ,
            "render_settings":{
            "resolution_x":context .scene .render .resolution_x ,
            "resolution_y":context .scene .render .resolution_y ,
            "resolution_percentage":context .scene .render .resolution_percentage ,
            "frame_rate":context .scene .render .fps 
            }
            }

            return True ,{"result":scene_info }

        except Exception as e :
            logger .error (f"Scene context tool error: {str(e)}")
            return False ,{"result":f"Scene context error: {str(e)}"}

    def _viewport_tool (self ,arguments :Dict [str ,Any ],context )->Tuple [bool ,Any ]:
        """Capture viewport screenshot and return as base64 data URI."""
        try :
            logger .info (f"Starting viewport capture with arguments: {arguments}")


            shading_mode =arguments .get ("shading_mode",None )
            logger .info (f"Shading mode requested: {shading_mode}")





            view3d_area =None 
            available_areas =[]
            for area in context .screen .areas :
                available_areas .append (area .type )
                if area .type =='VIEW_3D':
                    view3d_area =area 
                    break 

            logger .info (f"Available areas: {available_areas}")

            if not view3d_area :
                error_msg =f"No active 3D viewport found. Available areas: {available_areas}"
                logger .error (error_msg )
                return False ,error_msg 

            logger .info (f"Found 3D viewport area: {view3d_area}")


            space_3d =None 
            available_spaces =[]
            for space in view3d_area .spaces :
                available_spaces .append (space .type )
                if space .type =='VIEW_3D':
                    space_3d =space 
                    break 

            logger .info (f"Available spaces in 3D area: {available_spaces}")

            if not space_3d :
                error_msg =f"No 3D viewport space found. Available spaces: {available_spaces}"
                logger .error (error_msg )
                return False ,error_msg 


            original_shading_type =space_3d .shading .type 


            if shading_mode and shading_mode in ['WIREFRAME','SOLID','MATERIAL','RENDERED']:
                space_3d .shading .type =shading_mode 
                logger .info (f"Changed shading mode to: {shading_mode}")


            view3d_area .tag_redraw ()
            bpy .ops .wm .redraw_timer (type ='DRAW_WIN_SWAP',iterations =1 )


            temp_file =tempfile .NamedTemporaryFile (suffix ='.png',delete =False )
            temp_filepath =temp_file .name 
            temp_file .close ()

            try :

                bpy .ops .screen .screenshot (filepath =temp_filepath )


                if not os .path .exists (temp_filepath ):
                    return False ,"Screenshot was not created"


                file_size =os .path .getsize (temp_filepath )
                logger .info (f"Screenshot captured, file size: {file_size} bytes")


                with open (temp_filepath ,'rb')as f :
                    image_data =f .read ()


                width ,height =view3d_area .width ,view3d_area .height 
                try :
                    from PIL import Image 
                    with Image .open (temp_filepath )as img :
                        width ,height =img .size 
                        logger .info (f"Screenshot dimensions: {width}x{height}")
                except ImportError :
                    logger .info (f"Estimated screenshot dimensions: {width}x{height}")


                import base64 
                base64_data =base64 .b64encode (image_data ).decode ('utf-8')
                data_uri =f"data:image/png;base64,{base64_data}"

                logger .info (f"Successfully encoded {len(base64_data)} characters of base64 data")


                return True ,{
                "result":{
                "data_uri":data_uri ,
                "width":width ,
                "height":height ,
                "original_viewport_size":[view3d_area .width ,view3d_area .height ],
                "size_bytes":file_size ,
                "format":"PNG",
                "shading_mode":shading_mode or original_shading_type 
                }
                }

            finally :

                if shading_mode and shading_mode in ['WIREFRAME','SOLID','MATERIAL','RENDERED']:
                    space_3d .shading .type =original_shading_type 
                    logger .info (f"Restored shading mode to: {original_shading_type}")


                try :
                    os .unlink (temp_filepath )
                except Exception as cleanup_error :
                    logger .warning (f"Failed to clean up temporary file: {cleanup_error}")

        except Exception as e :
            logger .error (f"Viewport capture failed with exception: {str(e)}")
            import traceback 
            logger .error (f"Full traceback: {traceback.format_exc()}")
            return False ,f"Viewport capture failed: {str(e)}"

    def _see_render_tool (self ,arguments :Dict [str ,Any ],context )->Tuple [bool ,Any ]:
        """Render the current scene and return the final result when complete."""
        try :
            logger .info ("Starting synchronous render with user control")


            scene_name =arguments .get ("scene_name",None )
            camera_name =arguments .get ("camera_name",None )


            from ..ui .advanced .manager import ui_manager 


            if hasattr (ui_manager ,'_send_render_status_block'):
                ui_manager ._send_render_status_block ("[Checking for existing render...]")


            scene =bpy .data .scenes .get (scene_name )if scene_name else context .scene 
            camera =scene .camera 
            if camera_name :
                camera =bpy .data .objects .get (camera_name )

            existing_result =render_manager ._get_existing_render_result (scene ,camera )
            if existing_result :
                logger .info ("Found existing render result, returning it")
                if hasattr (ui_manager ,'_send_render_status_block'):
                    ui_manager ._send_render_status_block ("[Using existing render]")
                return True ,{"result":existing_result }


            if hasattr (ui_manager ,'_send_render_status_block'):
                ui_manager ._send_render_status_block ("[Rendering scene]")


            result_data =render_manager .render_sync (
            scene_name =scene_name ,
            camera_name =camera_name ,
            output_path =None 
            )


            if hasattr (ui_manager ,'_send_render_status_block'):
                ui_manager ._send_render_status_block ("[Render captured]")

            logger .info (f"Synchronous render completed successfully")


            return True ,{"result":result_data }

        except Exception as e :
            logger .error (f"Synchronous render tool failed: {str(e)}")
            import traceback 
            logger .error (f"Full traceback: {traceback.format_exc()}")


            try :
                from ..ui .advanced .manager import ui_manager 
                if hasattr (ui_manager ,'_send_render_status_block'):
                    ui_manager ._send_render_status_block (f"[Render failed: {str(e)}]")
            except :
                pass 

            return False ,{"result":f"Render failed: {str(e)}"}

    def _render_async_tool (self ,arguments :Dict [str ,Any ],context )->Tuple [bool ,Any ]:
        """Start an asynchronous render operation with callback support."""
        try :
            scene_name =arguments .get ("scene_name",None )
            camera_name =arguments .get ("camera_name",None )
            output_path =arguments .get ("output_path",None )


            completion_data ={}
            error_data ={}

            def on_complete (result_data ):
                """Callback for render completion."""
                completion_data ['result']=result_data 
                completion_data ['completed']=True 
                logger .info (f"Async render completed: {result_data.get('render_id', 'unknown')}")

            def on_error (error_msg ):
                """Callback for render error."""
                error_data ['error']=error_msg 
                error_data ['failed']=True 
                logger .error (f"Async render failed: {error_msg}")


            render_id =render_manager .start_render_with_callback (
            scene_name =scene_name ,
            camera_name =camera_name ,
            on_complete =on_complete ,
            on_error =on_error ,
            output_path =output_path 
            )

            if not render_id :
                return False ,{"result":"Failed to start render"}


            if completion_data .get ('completed'):
                result_data =completion_data ['result']
                return True ,{
                "result":{
                **result_data ,
                "status":"completed",
                "message":f"Used existing render result with ID: {render_id}",
                "used_existing":True 
                }
                }

            result_data ={
            "render_id":render_id ,
            "status":"started",
            "message":f"Async render started with ID: {render_id}",
            "scene_name":scene_name or context .scene .name ,
            "camera_name":camera_name or (context .scene .camera .name if context .scene .camera else None ),
            "used_existing":False 
            }

            return True ,{"result":result_data }

        except Exception as e :
            logger .error (f"Async render tool error: {str(e)}")
            return False ,{"result":f"Async render error: {str(e)}"}

    def _get_render_result_tool (self ,arguments :Dict [str ,Any ],context )->Tuple [bool ,Any ]:
        """Get the result of an async render operation."""
        try :
            render_id =arguments .get ("render_id","")
            if not render_id :
                return False ,{"result":"No render ID provided"}


            result_data =render_manager .get_render_result (render_id )

            if result_data :
                return True ,{"result":result_data }
            else :

                if render_manager .is_render_active (render_id ):
                    return True ,{"result":{"status":"rendering","render_id":render_id }}
                else :
                    return False ,{"result":f"Render result not found for ID: {render_id}"}

        except Exception as e :
            logger .error (f"Get render result tool error: {str(e)}")
            return False ,{"result":f"Get render result error: {str(e)}"}

    def _cancel_render_tool (self ,arguments :Dict [str ,Any ],context )->Tuple [bool ,Any ]:
        """Cancel an active render operation."""
        try :
            render_id =arguments .get ("render_id","")
            if not render_id :
                return False ,{"result":"No render ID provided"}


            success =render_manager .cancel_render (render_id )

            if success :
                return True ,{"result":f"Render {render_id} cancelled successfully"}
            else :
                return False ,{"result":f"Failed to cancel render {render_id}"}

        except Exception as e :
            logger .error (f"Cancel render tool error: {str(e)}")
            return False ,{"result":f"Cancel render error: {str(e)}"}

    def _list_active_renders_tool (self ,arguments :Dict [str ,Any ],context )->Tuple [bool ,Any ]:
        """List all active render operations."""
        try :
            active_renders =render_manager .get_active_renders ()

            result_data ={
            "active_renders":active_renders ,
            "count":len (active_renders )
            }

            return True ,{"result":result_data }

        except Exception as e :
            logger .error (f"List active renders tool error: {str(e)}")
            return False ,{"result":f"List active renders error: {str(e)}"}

    def cleanup (self ):
        """Clean up resources."""
        render_manager .cleanup ()



tools_manager =ToolsManager ()