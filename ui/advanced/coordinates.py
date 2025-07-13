"""
Coordinate system management for the UI.
Provides centralized coordinate conversion utilities.
"""

import bpy 
from typing import Tuple 


class CoordinateSystem :
    """Centralized coordinate system management for the UI.
    
    Uses area coordinates with Y=0 at BOTTOM as the authoritative system.
    This matches Method 3 coordinate conversion and Blender's rendering system.
    """

    @staticmethod 
    def get_ui_scale ()->float :
        """Get the current UI scale from Blender preferences."""
        try :
            return bpy .context .preferences .system .ui_scale 
        except (AttributeError ,RuntimeError ):

            return 1.0 

    @staticmethod 
    def scale_value (value :float )->float :
        """Scale a value by the current UI scale."""
        return value *CoordinateSystem .get_ui_scale ()

    @staticmethod 
    def scale_int (value :int )->int :
        """Scale a value by the current UI scale."""
        return int (value *CoordinateSystem .get_ui_scale ())

    @staticmethod 
    def screen_to_region (screen_x :int ,screen_y :int ,area ,region )->Tuple [int ,int ]:
        """Convert screen coordinates to area coordinates."""
        if not area or not region :
            return screen_x ,screen_y 



        area_x =screen_x -area .x 
        area_y =screen_y -area .y 

        return area_x ,area_y 

    @staticmethod 
    def region_to_gpu (region_x :int ,region_y :int )->Tuple [int ,int ]:
        """Convert area coordinates to GPU coordinates.
        Both use Y=0 at bottom, so this is a direct pass-through.
        """
        return region_x ,region_y 

    @staticmethod 
    def get_region_height ()->int :
        """Get the current area height for coordinate calculations."""
        try :
            area =bpy .context .area 
            return area .height if area else 0 
        except :
            return 0 