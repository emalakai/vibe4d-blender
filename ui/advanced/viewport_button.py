"""
Viewport button for opening/closing the custom UI.
Draws a simple button on all 3D viewports except the one used for custom UI.
"""

import bpy 
import gpu 
import blf 
from gpu_extras .batch import batch_for_shader 
from pathlib import Path 
import logging 
from typing import Optional ,Tuple 
import time 
import math 

from .manager import ui_manager 
from .colors import Colors 
from .coordinates import CoordinateSystem 

logger =logging .getLogger (__name__ )


class ViewportButton :
    """Simple button that appears in all 3D viewports to open/close custom UI."""

    def __init__ (self ):
        self .draw_handler =None 
        self .logo_image =None 
        self .logo_texture =None 
        self .button_size =CoordinateSystem .scale_int (40 )
        self .button_margin =CoordinateSystem .scale_int (10 )
        self .is_hovered =False 
        self .is_pressed =False 
        self .logo_loaded =False 
        self .logo_load_attempted =False 



    def _load_logo_texture (self ):
        """Load the logo texture from the icons directory."""
        if self .logo_load_attempted :
            return 

        self .logo_load_attempted =True 

        try :

            if not hasattr (bpy ,'data')or not hasattr (bpy .data ,'images'):
                logger .warning ("bpy.data.images not available, skipping logo load")
                return 

            addon_dir =Path (__file__ ).parent .parent .parent 
            logo_path =addon_dir /"ui"/"advanced"/"icons"/"logo_tool.png"

            if logo_path .exists ():

                image_name =f"vibe4d_logo_{logo_path.name}"
                if image_name in bpy .data .images :
                    self .logo_image =bpy .data .images [image_name ]
                else :

                    self .logo_image =bpy .data .images .load (str (logo_path ))
                    if self .logo_image :

                        self .logo_image .name =image_name 

                if self .logo_image :

                    try :
                        import gpu .texture 
                        self .logo_texture =gpu .texture .from_image (self .logo_image )
                        self .logo_loaded =True 
                        logger .info (f"Logo texture loaded from {logo_path}")
                    except Exception as e :
                        logger .error (f"Failed to create GPU texture from image: {e}")
                        self .logo_texture =None 
                else :
                    logger .warning (f"Failed to load logo image from {logo_path}")
            else :
                logger .warning (f"Logo file not found at {logo_path}")
        except Exception as e :
            logger .error (f"Error loading logo texture: {e}")

    def enable (self ):
        """Enable the viewport button by adding draw handler."""
        if self .draw_handler is None :
            self .draw_handler =bpy .types .SpaceView3D .draw_handler_add (
            self ._draw_callback ,(),'WINDOW','POST_PIXEL'
            )
            logger .info ("Viewport button enabled")

    def disable (self ):
        """Disable the viewport button by removing draw handler."""
        if self .draw_handler :
            bpy .types .SpaceView3D .draw_handler_remove (self .draw_handler ,'WINDOW')
            self .draw_handler =None 
            logger .info ("Viewport button disabled")


        self ._cleanup_texture ()

    def _cleanup_texture (self ):
        """Clean up texture resources."""
        try :
            if self .logo_texture :

                self .logo_texture =None 

            if self .logo_image and hasattr (bpy ,'data')and hasattr (bpy .data ,'images')and self .logo_image .name in bpy .data .images :

                bpy .data .images .remove (self .logo_image )
                logger .info ("Logo texture cleaned up")
        except Exception as e :
            logger .debug (f"Error cleaning up logo texture: {e}")
        finally :
            self .logo_image =None 
            self .logo_texture =None 
            self .logo_loaded =False 
            self .logo_load_attempted =False 

    def _should_draw_in_area (self ,area )->bool :
        """Check if button should be drawn in this area."""
        if area .type !='VIEW_3D':
            return False 


        if ui_manager .state .target_area and area ==ui_manager .state .target_area :
            return False 

        return True 

    def _get_button_bounds (self ,area )->Tuple [int ,int ,int ,int ]:
        """Get button bounds (x, y, width, height) for the given area."""

        x =self .button_margin 
        y =self .button_margin 
        width =self .button_size 
        height =self .button_size 
        return x ,y ,width ,height 

    def _draw_callback (self ):
        """Draw callback for the viewport button."""
        try :
            context =bpy .context 
            if not context .area or not self ._should_draw_in_area (context .area ):
                return 


            if not self .logo_load_attempted :
                self ._load_logo_texture ()

            area =context .area 
            x ,y ,width ,height =self ._get_button_bounds (area )


            current_time =time .time ()
            if not hasattr (self ,'_last_draw_log_time')or current_time -self ._last_draw_log_time >5.0 :
                self ._last_draw_log_time =current_time 


            is_ui_active =ui_manager .is_ui_active ()

            if is_ui_active :

                bg_color =(0.2 ,0.4 ,0.8 ,0.8 )
            else :

                if self .is_hovered :
                    bg_color =(0.3 ,0.3 ,0.3 ,0.8 )
                else :
                    bg_color =(0.1 ,0.1 ,0.1 ,0.8 )


            self ._draw_rounded_rect (x ,y ,width ,height ,bg_color ,CoordinateSystem .scale_int (6 ))


            if self .logo_loaded and self .logo_texture :
                logo_margin =CoordinateSystem .scale_int (6 )
                logo_x =x +logo_margin 
                logo_y =y +logo_margin 
                logo_size =width -(logo_margin *2 )
                self ._draw_logo (logo_x ,logo_y ,logo_size ,logo_size )
            else :

                font_size =CoordinateSystem .scale_int (16 )
                text_x =x +width //2 -CoordinateSystem .scale_int (8 )
                text_y =y +height //2 -CoordinateSystem .scale_int (8 )
                self ._draw_text ("AI",text_x ,text_y ,font_size ,(1 ,1 ,1 ,1 ))

        except Exception as e :
            logger .error (f"Error in viewport button draw callback: {e}")

    def _draw_rounded_rect (self ,x :int ,y :int ,width :int ,height :int ,color :Tuple [float ,float ,float ,float ],corner_radius :int ):
        """Draw a rounded rectangle."""
        try :

            corner_radius =min (corner_radius ,min (width ,height )//2 )

            vertices =[]
            indices =[]


            segments =8 







            def add_corner_arc (center_x ,center_y ,start_angle ,end_angle ):
                start_idx =len (vertices )

                vertices .append ((center_x ,center_y ))


                for i in range (segments +1 ):
                    angle =start_angle +(end_angle -start_angle )*i /segments 
                    arc_x =center_x +corner_radius *math .cos (angle )
                    arc_y =center_y +corner_radius *math .sin (angle )
                    vertices .append ((arc_x ,arc_y ))


                for i in range (segments ):
                    indices .append ((start_idx ,start_idx +i +1 ,start_idx +i +2 ))

                return start_idx +1 ,start_idx +segments +1 


            bl_start ,bl_end =add_corner_arc (
            x +corner_radius ,y +corner_radius ,
            math .pi ,math .pi *1.5 
            )


            br_start ,br_end =add_corner_arc (
            x +width -corner_radius ,y +corner_radius ,
            math .pi *1.5 ,math .pi *2 
            )


            tr_start ,tr_end =add_corner_arc (
            x +width -corner_radius ,y +height -corner_radius ,
            0 ,math .pi *0.5 
            )


            tl_start ,tl_end =add_corner_arc (
            x +corner_radius ,y +height -corner_radius ,
            math .pi *0.5 ,math .pi 
            )


            center_start =len (vertices )
            vertices .extend ([
            (x +corner_radius ,y +corner_radius ),
            (x +width -corner_radius ,y +corner_radius ),
            (x +width -corner_radius ,y +height -corner_radius ),
            (x +corner_radius ,y +height -corner_radius )
            ])


            indices .extend ([
            (center_start ,center_start +1 ,center_start +2 ),
            (center_start +2 ,center_start +3 ,center_start )
            ])



            bottom_start =len (vertices )
            vertices .extend ([
            (x +corner_radius ,y ),
            (x +width -corner_radius ,y ),
            (x +width -corner_radius ,y +corner_radius ),
            (x +corner_radius ,y +corner_radius )
            ])
            indices .extend ([
            (bottom_start ,bottom_start +1 ,bottom_start +2 ),
            (bottom_start +2 ,bottom_start +3 ,bottom_start )
            ])


            top_start =len (vertices )
            vertices .extend ([
            (x +corner_radius ,y +height -corner_radius ),
            (x +width -corner_radius ,y +height -corner_radius ),
            (x +width -corner_radius ,y +height ),
            (x +corner_radius ,y +height )
            ])
            indices .extend ([
            (top_start ,top_start +1 ,top_start +2 ),
            (top_start +2 ,top_start +3 ,top_start )
            ])


            left_start =len (vertices )
            vertices .extend ([
            (x ,y +corner_radius ),
            (x +corner_radius ,y +corner_radius ),
            (x +corner_radius ,y +height -corner_radius ),
            (x ,y +height -corner_radius )
            ])
            indices .extend ([
            (left_start ,left_start +1 ,left_start +2 ),
            (left_start +2 ,left_start +3 ,left_start )
            ])


            right_start =len (vertices )
            vertices .extend ([
            (x +width -corner_radius ,y +corner_radius ),
            (x +width ,y +corner_radius ),
            (x +width ,y +height -corner_radius ),
            (x +width -corner_radius ,y +height -corner_radius )
            ])
            indices .extend ([
            (right_start ,right_start +1 ,right_start +2 ),
            (right_start +2 ,right_start +3 ,right_start )
            ])


            shader =gpu .shader .from_builtin ('UNIFORM_COLOR')
            batch =batch_for_shader (shader ,'TRIS',{"pos":vertices },indices =indices )

            gpu .state .blend_set ('ALPHA')
            shader .bind ()
            shader .uniform_float ("color",color )
            batch .draw (shader )
            gpu .state .blend_set ('NONE')

        except Exception as e :
            logger .error (f"Error drawing rounded rectangle: {e}")

            vertices =[
            (x ,y ),
            (x +width ,y ),
            (x +width ,y +height ),
            (x ,y +height )
            ]
            indices =[(0 ,1 ,2 ),(2 ,3 ,0 )]

            try :
                shader =gpu .shader .from_builtin ('UNIFORM_COLOR')
                batch =batch_for_shader (shader ,'TRIS',{"pos":vertices },indices =indices )

                gpu .state .blend_set ('ALPHA')
                shader .bind ()
                shader .uniform_float ("color",color )
                batch .draw (shader )
                gpu .state .blend_set ('NONE')
            except Exception as e2 :
                logger .error (f"Error drawing fallback rectangle: {e2}")

    def _draw_logo (self ,x :int ,y :int ,width :int ,height :int ):
        """Draw the logo texture."""
        if not self .logo_loaded or not self .logo_texture :
            return 

        try :
            vertices =[
            (x ,y ),
            (x +width ,y ),
            (x +width ,y +height ),
            (x ,y +height )
            ]

            uvs =[
            (0 ,0 ),
            (1 ,0 ),
            (1 ,1 ),
            (0 ,1 )
            ]

            indices =[(0 ,1 ,2 ),(2 ,3 ,0 )]

            shader =gpu .shader .from_builtin ('IMAGE')
            batch =batch_for_shader (shader ,'TRIS',{"pos":vertices ,"texCoord":uvs },indices =indices )

            gpu .state .blend_set ('ALPHA')
            shader .bind ()
            shader .uniform_sampler ("image",self .logo_texture )
            batch .draw (shader )
            gpu .state .blend_set ('NONE')
        except Exception as e :
            logger .error (f"Error drawing logo: {e}")

            font_size =CoordinateSystem .scale_int (16 )
            text_x =x +width //4 
            text_y =y +height //2 -CoordinateSystem .scale_int (8 )
            self ._draw_text ("AI",text_x ,text_y ,font_size ,(1 ,1 ,1 ,1 ))

    def _draw_text (self ,text :str ,x :int ,y :int ,size :int ,color :Tuple [float ,float ,float ,float ]):
        """Draw text."""
        try :
            font_id =0 
            blf .size (font_id ,size )
            blf .position (font_id ,x ,y ,0 )
            blf .color (font_id ,*color )
            blf .draw (font_id ,text )
        except Exception as e :
            logger .error (f"Error drawing text: {e}")

    def handle_mouse_event (self ,event )->bool :
        """Handle mouse events for the button."""
        try :
            context =bpy .context 
            if not context .area or not self ._should_draw_in_area (context .area ):
                return False 

            area =context .area 
            x ,y ,width ,height =self ._get_button_bounds (area )


            mouse_x ,mouse_y =self ._screen_to_region_coords (event ,area )
            if mouse_x is None or mouse_y is None :
                return False 


            is_over_button =(x <=mouse_x <=x +width and 
            y <=mouse_y <=y +height )


            if is_over_button !=self .is_hovered :
                self .is_hovered =is_over_button 
                area .tag_redraw ()


            if (event .type =='LEFTMOUSE'and event .value =='PRESS'and 
            is_over_button ):
                self ._handle_button_click ()
                return True 

            return False 
        except Exception as e :
            logger .error (f"Error handling mouse event: {e}")
            return False 

    def _screen_to_region_coords (self ,event ,area ):
        """Convert screen coordinates to region coordinates."""
        try :

            for region in area .regions :
                if region .type =='WINDOW':


                    region_x =event .mouse_x -area .x -region .x 
                    region_y =event .mouse_y -area .y -region .y 


                    if 0 <=region_x <=region .width and 0 <=region_y <=region .height :
                        return region_x ,region_y 


            area_x =event .mouse_x -area .x 
            area_y =event .mouse_y -area .y 


            if 0 <=area_x <=area .width and 0 <=area_y <=area .height :
                return area_x ,area_y 

            return None ,None 
        except Exception as e :
            logger .error (f"Error converting screen to region coordinates: {e}")
            return None ,None 

    def _handle_button_click (self ):
        """Handle button click to toggle UI."""
        try :

            bpy .ops .vibe4d .show_advanced_ui ()
        except Exception as e :
            logger .error (f"Error handling button click: {e}")



viewport_button =ViewportButton ()