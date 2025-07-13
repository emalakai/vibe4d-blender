"""
Tools API module for Vibe4D addon.

Provides Python API functions that can be called directly from Blender's Python console
or scripts. Allows calling tools like:
- vibe4d.query("SELECT * FROM objects")
- vibe4d.execute("bpy.ops.mesh.primitive_cube_add()")
- vibe4d.scene_graph()
- vibe4d.render_settings(["engine", "resolution_x"])
"""

import bpy 
from typing import Dict ,Any ,List ,Optional ,Union 

from ..utils .logger import logger 
from ..engine .tools import tools_manager 


def _get_context ():
    """Get current Blender context."""
    return bpy .context 


def query (expr :str ,limit :int =8192 ,format_type :str ="json")->Dict [str ,Any ]:
    """
    Query scene data using SQL-like expressions.
    
    Args:
        expr: SQL-like query expression
        limit: Maximum number of results to return
        format_type: Output format ("csv", "json", "table")
        
    Returns:
        Dictionary containing query results
        
    Example:
        >>> import vibe4d
        >>> result = vibe4d.query("SELECT name, type FROM objects WHERE type = 'MESH'")
        >>> print(result)
    """
    try :
        context =_get_context ()
        success ,result =tools_manager .handle_tool_call ("query",{
        "expr":expr ,
        "limit":limit ,
        "format":format_type 
        },context )

        if success :
            return result 
        else :
            raise RuntimeError (f"Query failed: {result}")

    except Exception as e :
        logger .error (f"Query API error: {str(e)}")
        raise 


def execute (code :str )->str :
    """
    Execute Python code in Blender.
    
    Args:
        code: Python code to execute
        
    Returns:
        Console output or success message
        
    Example:
        >>> import vibe4d
        >>> vibe4d.execute("bpy.ops.mesh.primitive_cube_add()")
        >>> vibe4d.execute("print('Hello from Blender!')")
    """
    try :
        context =_get_context ()
        success ,result =tools_manager .handle_tool_call ("execute",{
        "code":code 
        },context )

        if success :
            return result ["result"]
        else :
            raise RuntimeError (f"Execution failed: {result['result']}")

    except Exception as e :
        logger .error (f"Execute API error: {str(e)}")
        raise 


def scene_context ()->Dict [str ,Any ]:
    """
    Get current scene context information.
    
    Returns:
        Dictionary containing scene information
        
    Example:
        >>> import vibe4d
        >>> context = vibe4d.scene_context()
        >>> print(f"Scene: {context['scene_name']}")
        >>> print(f"Objects: {len(context['objects'])}")
    """
    try :
        context =_get_context ()
        success ,result =tools_manager .handle_tool_call ("scene_context",{},context )

        if success :
            return result ["result"]
        else :
            raise RuntimeError (f"Scene context failed: {result['result']}")

    except Exception as e :
        logger .error (f"Scene context API error: {str(e)}")
        raise 


def get_query_formats ()->Dict [str ,str ]:
    """
    Get available query output formats.
    
    Returns:
        Dictionary of format names and descriptions
    """
    return {
    "csv":"Comma-separated values format",
    "json":"JSON format with structured data",
    "table":"Human-readable table format"
    }


def table_counts ()->Dict [str ,int ]:
    """
    Get counts of available data tables for querying.
    
    Returns:
        Dictionary of table names and their row counts
    """
    try :
        context =_get_context ()
        from ..engine .query import scene_query_engine 
        result =scene_query_engine .get_all_table_counts (context )


        if result .get ("status")=="success":
            return result ["table_counts"]
        else :
            logger .error (f"Table counts error: {result.get('error', 'Unknown error')}")
            return {}
    except Exception as e :
        logger .error (f"Table counts API error: {str(e)}")
        return {}


def viewport (shading_mode :str =None )->Dict [str ,Any ]:
    """
    Capture current viewport screenshot.
    
    Args:
        shading_mode: Viewport shading mode ("WIREFRAME", "SOLID", "MATERIAL", "RENDERED")
        
    Returns:
        Dictionary containing viewport capture data
        
    Example:
        >>> import vibe4d
        >>> result = vibe4d.viewport("RENDERED")
        >>> print(f"Captured {result['width']}x{result['height']} viewport")
    """
    try :
        context =_get_context ()
        arguments ={}
        if shading_mode :
            arguments ["shading_mode"]=shading_mode 

        from ..engine .tools import tools_manager 
        success ,result =tools_manager .handle_tool_call ("viewport",arguments ,context )

        if success :
            return result 
        else :
            raise RuntimeError (f"Viewport capture failed: {result}")

    except Exception as e :
        logger .error (f"Viewport API error: {str(e)}")
        raise 


def add_viewport_render (shading_mode :str =None )->Dict [str ,Any ]:
    """
    Capture current viewport screenshot with specific shading mode and return as base64-encoded PNG image.
    
    This function captures the active 3D viewport with a specific shading mode, temporarily switching
    the viewport to the requested shading before capturing.
    
    Args:
        shading_mode: Viewport shading mode to use for capture:
                     - "WIREFRAME": Wireframe display
                     - "SOLID": Solid shading  
                     - "MATERIAL": Material preview shading
                     - "RENDERED": Rendered shading (uses render engine)
                     If None, uses current viewport shading
        
    Returns:
        Dictionary containing:
        - data_uri: Base64-encoded PNG data URI
        - width: Actual viewport width in pixels
        - height: Actual viewport height in pixels
        - original_viewport_size: [width, height] array
        - size_bytes: Size of PNG data in bytes
        - format: Image format ("PNG")
        - shading_mode: The shading mode used for capture
        
    Example:
        >>> import vibe4d
        >>> # Capture in rendered mode
        >>> result = vibe4d.add_viewport_render("RENDERED")
        >>> print(f"Captured {result['width']}x{result['height']} viewport in {result['shading_mode']} mode")
        >>> 
        >>> # Capture in material preview mode
        >>> result = vibe4d.add_viewport_render("MATERIAL")
        >>> 
        >>> # Use current shading mode
        >>> result = vibe4d.add_viewport_render()
    """
    try :
        context =_get_context ()
        arguments ={}
        if shading_mode :
            arguments ["shading_mode"]=shading_mode 

        from ..engine .tools import tools_manager 
        success ,result =tools_manager .handle_tool_call ("add_viewport_render",arguments ,context )

        if success :
            return result 
        else :
            raise RuntimeError (f"Viewport render capture failed: {result}")

    except Exception as e :
        logger .error (f"Add viewport render API error: {str(e)}")
        raise 


def see_viewport (shading_mode :str =None )->Dict [str ,Any ]:
    """
    Alias for add_viewport_render - captures viewport with optional shading mode.
    
    Args:
        shading_mode: Viewport shading mode to use for capture
        
    Returns:
        Dictionary containing viewport capture data
    """
    return add_viewport_render (shading_mode )


def see_render ()->Dict [str ,Any ]:
    """
    Render current scene with active camera and current settings, return as base64-encoded PNG image.
    
    This function renders the current scene using the active camera and current render settings,
    capturing the final rendered output exactly as it would appear when manually rendering.
    
    Returns:
        Dictionary containing:
        - data_uri: Base64-encoded PNG data URI of the rendered image
        - width: Actual render width in pixels
        - height: Actual render height in pixels  
        - render_resolution: [width, height] array of render settings
        - render_percentage: Render resolution percentage
        - size_bytes: Size of PNG data in bytes
        - format: Image format ("PNG")
        - render_engine: Render engine used (e.g., "CYCLES", "EEVEE")
        - camera_name: Name of the camera used for rendering
        - frame: Current frame number that was rendered
        
    Example:
        >>> import vibe4d
        >>> result = vibe4d.see_render()
        >>> print(f"Rendered {result['width']}x{result['height']} image using {result['render_engine']}")
        >>> print(f"Camera: {result['camera_name']}, Frame: {result['frame']}")
        
    Note:
        - Requires an active camera in the scene
        - Uses current render settings (resolution, engine, etc.)
        - Renders at the current frame
        - Temporarily changes output format to PNG for capture
        - May take time depending on render complexity and settings
    """
    try :
        context =_get_context ()
        from ..engine .tools import tools_manager 
        success ,result =tools_manager .handle_tool_call ("see_render",{},context )

        if success :

            render_data =result ["result"]
            logger .info (f"Render capture completed: {render_data['width']}x{render_data['height']}")
            return render_data 
        else :
            error_msg =f"Render failed: {result['result']}"
            logger .error (error_msg )
            raise RuntimeError (error_msg )

    except Exception as e :
        error_msg =f"Failed to render scene: {str(e)}"
        logger .error (error_msg )
        raise RuntimeError (error_msg )


def render_async (
scene_name :Optional [str ]=None ,
camera_name :Optional [str ]=None ,
output_path :Optional [str ]=None 
)->Dict [str ,Any ]:
    """
    Start an asynchronous render operation that runs in the background.
    
    This function starts a render operation that runs asynchronously, allowing you to
    continue working while the render completes. Use get_render_result() to check
    completion status and retrieve the result.
    
    Args:
        scene_name: Name of scene to render (None for current scene)
        camera_name: Name of camera to use (None for scene's active camera)
        output_path: Custom output path (None for temporary file)
        
    Returns:
        Dictionary containing:
        - render_id: Unique identifier for tracking this render
        - status: "started" indicating render has begun
        - message: Human-readable status message
        - scene_name: Name of scene being rendered
        - camera_name: Name of camera being used
        
    Example:
        >>> import vibe4d
        >>> # Start async render with default settings
        >>> result = vibe4d.render_async()
        >>> render_id = result['render_id']
        >>> print(f"Started render: {render_id}")
        >>> 
        >>> # Start render with specific camera
        >>> result = vibe4d.render_async(camera_name="Camera.001")
        >>> 
        >>> # Start render with custom output path
        >>> result = vibe4d.render_async(output_path="/tmp/my_render.png")
        
    Note:
        - Returns immediately without waiting for render completion
        - Use get_render_result() to check status and get final result
        - Use list_active_renders() to see all running renders
        - Use cancel_render() to stop a render in progress
    """
    try :
        context =_get_context ()
        arguments ={}
        if scene_name :
            arguments ["scene_name"]=scene_name 
        if camera_name :
            arguments ["camera_name"]=camera_name 
        if output_path :
            arguments ["output_path"]=output_path 

        from ..engine .tools import tools_manager 
        success ,result =tools_manager .handle_tool_call ("render_async",arguments ,context )

        if success :
            return result ["result"]
        else :
            raise RuntimeError (f"Async render failed: {result['result']}")

    except Exception as e :
        logger .error (f"Async render API error: {str(e)}")
        raise 


def get_render_result (render_id :str )->Dict [str ,Any ]:
    """
    Get the result of an asynchronous render operation.
    
    This function checks the status of an async render and returns the result
    if completed, or status information if still in progress.
    
    Args:
        render_id: Render ID returned from render_async()
        
    Returns:
        Dictionary containing either:
        - Complete render result (if finished): data_uri, width, height, etc.
        - Status information (if still rendering): status, render_id
        
    Example:
        >>> import vibe4d
        >>> # Start async render
        >>> result = vibe4d.render_async()
        >>> render_id = result['render_id']
        >>> 
        >>> # Check result (may need to wait/retry)
        >>> result = vibe4d.get_render_result(render_id)
        >>> if result.get('status') == 'rendering':
        >>>     print("Still rendering...")
        >>> else:
        >>>     print(f"Render complete: {result['width']}x{result['height']}")
        
    Note:
        - Returns immediately with current status
        - If render is complete, includes full result data like see_render()
        - If still rendering, returns status information
        - If render failed or doesn't exist, raises RuntimeError
    """
    try :
        context =_get_context ()
        from ..engine .tools import tools_manager 
        success ,result =tools_manager .handle_tool_call ("get_render_result",{
        "render_id":render_id 
        },context )

        if success :
            return result ["result"]
        else :
            raise RuntimeError (f"Get render result failed: {result['result']}")

    except Exception as e :
        logger .error (f"Get render result API error: {str(e)}")
        raise 


def cancel_render (render_id :str )->str :
    """
    Cancel an active asynchronous render operation.
    
    This function stops a render that is currently in progress and cleans up
    any associated resources.
    
    Args:
        render_id: Render ID returned from render_async()
        
    Returns:
        Success message string
        
    Example:
        >>> import vibe4d
        >>> # Start async render
        >>> result = vibe4d.render_async()
        >>> render_id = result['render_id']
        >>> 
        >>> # Cancel the render
        >>> message = vibe4d.cancel_render(render_id)
        >>> print(message)  # "Render render_1_... cancelled successfully"
        
    Note:
        - Stops the render process immediately
        - Cleans up temporary files and resources
        - Returns success message if cancellation worked
        - Raises RuntimeError if render doesn't exist or can't be cancelled
    """
    try :
        context =_get_context ()
        from ..engine .tools import tools_manager 
        success ,result =tools_manager .handle_tool_call ("cancel_render",{
        "render_id":render_id 
        },context )

        if success :
            return result ["result"]
        else :
            raise RuntimeError (f"Cancel render failed: {result['result']}")

    except Exception as e :
        logger .error (f"Cancel render API error: {str(e)}")
        raise 


def list_active_renders ()->Dict [str ,Any ]:
    """
    List all currently active asynchronous render operations.
    
    This function returns information about all renders that are currently
    in progress or starting up.
    
    Returns:
        Dictionary containing:
        - active_renders: List of render IDs that are currently active
        - count: Number of active renders
        
    Example:
        >>> import vibe4d
        >>> # Start a few renders
        >>> render1 = vibe4d.render_async()
        >>> render2 = vibe4d.render_async(camera_name="Camera.001")
        >>> 
        >>> # List active renders
        >>> active = vibe4d.list_active_renders()
        >>> print(f"Active renders: {active['count']}")
        >>> for render_id in active['active_renders']:
        >>>     print(f"  - {render_id}")
        
    Note:
        - Only includes renders that are currently starting or rendering
        - Completed, failed, or cancelled renders are not included
        - Use get_render_result() to check status of specific renders
    """
    try :
        context =_get_context ()
        from ..engine .tools import tools_manager 
        success ,result =tools_manager .handle_tool_call ("list_active_renders",{},context )

        if success :
            return result ["result"]
        else :
            raise RuntimeError (f"List active renders failed: {result['result']}")

    except Exception as e :
        logger .error (f"List active renders API error: {str(e)}")
        raise 


def render_with_callback (
on_complete :Optional [callable ]=None ,
on_error :Optional [callable ]=None ,
scene_name :Optional [str ]=None ,
camera_name :Optional [str ]=None ,
output_path :Optional [str ]=None 
)->str :
    """
    Start an asynchronous render with custom callback functions.
    
    This is a lower-level function that allows you to specify custom callback
    functions that will be called when the render completes or fails.
    
    Args:
        on_complete: Function to call when render completes successfully
                    Receives render result dictionary as argument
        on_error: Function to call when render fails
                 Receives error message string as argument
        scene_name: Name of scene to render (None for current scene)
        camera_name: Name of camera to use (None for scene's active camera)
        output_path: Custom output path (None for temporary file)
        
    Returns:
        Render ID string for tracking
        
    Example:
        >>> import vibe4d
        >>> 
        >>> def on_render_done(result):
        >>>     print(f"Render finished: {result['width']}x{result['height']}")
        >>> 
        >>> def on_render_error(error):
        >>>     print(f"Render failed: {error}")
        >>> 
        >>> render_id = vibe4d.render_with_callback(
        >>>     on_complete=on_render_done,
        >>>     on_error=on_render_error
        >>> )
        
    Note:
        - This is a more advanced function for custom integration
        - Callbacks are called from Blender's main thread
        - Most users should use render_async() and get_render_result() instead
    """
    try :
        from ..engine .render_manager import render_manager 


        context =_get_context ()

        render_id =render_manager .start_render_with_callback (
        scene_name =scene_name ,
        camera_name =camera_name ,
        on_complete =on_complete ,
        on_error =on_error ,
        output_path =output_path 
        )

        if not render_id :
            raise RuntimeError ("Failed to start render with callback")

        return render_id 

    except Exception as e :
        logger .error (f"Render with callback API error: {str(e)}")
        raise 