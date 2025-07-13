"""
GPU rendering system for the UI.
Handles all GPU-based drawing operations including clipping support for scrollable content.
"""

import gpu 
import blf 
import logging 
from gpu_extras .batch import batch_for_shader 
from typing import Tuple ,List ,Optional 

from .types import Bounds 
from .coordinates import CoordinateSystem 

logger =logging .getLogger (__name__ )


class ClipRegion :
    """Represents a clipping region."""
    def __init__ (self ,x :int ,y :int ,width :int ,height :int ):
        self .x =x 
        self .y =y 
        self .width =width 
        self .height =height 


class UIRenderer :
    """Handles all GPU rendering operations with performance optimizations and clipping support."""

    def __init__ (self ):
        self .shader =None 
        self .texture_shader =None 
        self ._setup_shaders ()


        self ._batch_cache ={}
        self ._last_font_size =None 
        self ._font_cache ={}


        self ._clip_stack :List [ClipRegion ]=[]
        self ._current_clip :Optional [ClipRegion ]=None 

    def _setup_shaders (self ):
        """Setup GPU shaders."""
        try :
            self .shader =gpu .shader .from_builtin ('UNIFORM_COLOR')
            self .texture_shader =gpu .shader .from_builtin ('IMAGE')
        except Exception as e :
            logger .error (f"Failed to setup shaders: {e}")
            raise 

    def _get_or_create_rect_batch (self ,bounds :Bounds ):
        """Get or create cached rectangle batch."""
        cache_key =(bounds .x ,bounds .y ,bounds .width ,bounds .height ,'rect')

        if cache_key not in self ._batch_cache :
            vertices =[
            (bounds .x ,bounds .y ),
            (bounds .x +bounds .width ,bounds .y ),
            (bounds .x +bounds .width ,bounds .y +bounds .height ),
            (bounds .x ,bounds .y +bounds .height )
            ]
            indices =[(0 ,1 ,2 ),(2 ,3 ,0 )]
            self ._batch_cache [cache_key ]=batch_for_shader (
            self .shader ,'TRIS',{"pos":vertices },indices =indices 
            )

        return self ._batch_cache [cache_key ]

    def draw_rect (self ,bounds :Bounds ,color :Tuple [float ,float ,float ,float ]):
        """Draw a filled rectangle using centralized coordinate system with caching."""


        gpu_x ,gpu_y =CoordinateSystem .region_to_gpu (bounds .x ,bounds .y )

        vertices =[
        (gpu_x ,gpu_y ),
        (gpu_x +bounds .width ,gpu_y ),
        (gpu_x +bounds .width ,gpu_y +bounds .height ),
        (gpu_x ,gpu_y +bounds .height )
        ]

        indices =[(0 ,1 ,2 ),(2 ,3 ,0 )]

        try :

            batch =batch_for_shader (self .shader ,'TRIS',{"pos":vertices },indices =indices )

            gpu .state .blend_set ('ALPHA')
            self .shader .bind ()
            self .shader .uniform_float ("color",color )
            batch .draw (self .shader )
            gpu .state .blend_set ('NONE')
        except Exception as e :
            logger .error (f"Error drawing rectangle: {e}")

    def draw_rect_outline (self ,bounds :Bounds ,color :Tuple [float ,float ,float ,float ],width :int =1 ):
        """Draw a rectangle outline using filled rectangles for proper thickness support."""
        if width <=0 :
            return 


        gpu_x ,gpu_y =CoordinateSystem .region_to_gpu (bounds .x ,bounds .y )

        try :


            top_bounds =Bounds (bounds .x ,bounds .y +bounds .height -width ,bounds .width ,width )
            self .draw_rect (top_bounds ,color )


            bottom_bounds =Bounds (bounds .x ,bounds .y ,bounds .width ,width )
            self .draw_rect (bottom_bounds ,color )


            left_bounds =Bounds (bounds .x ,bounds .y +width ,width ,bounds .height -2 *width )
            if left_bounds .height >0 :
                self .draw_rect (left_bounds ,color )


            right_bounds =Bounds (bounds .x +bounds .width -width ,bounds .y +width ,width ,bounds .height -2 *width )
            if right_bounds .height >0 :
                self .draw_rect (right_bounds ,color )

        except Exception as e :
            logger .error (f"Error drawing rectangle outline: {e}")

    def draw_line (self ,x1 :int ,y1 :int ,x2 :int ,y2 :int ,color :Tuple [float ,float ,float ,float ]):
        """Draw a line using centralized coordinate system."""

        gpu_x1 ,gpu_y1 =CoordinateSystem .region_to_gpu (x1 ,y1 )
        gpu_x2 ,gpu_y2 =CoordinateSystem .region_to_gpu (x2 ,y2 )

        vertices =[(gpu_x1 ,gpu_y1 ),(gpu_x2 ,gpu_y2 )]

        try :
            batch =batch_for_shader (self .shader ,'LINES',{"pos":vertices })
            self .shader .bind ()
            self .shader .uniform_float ("color",color )
            batch .draw (self .shader )
        except Exception as e :
            logger .error (f"Error drawing line: {e}")

    def draw_text (self ,text :str ,x :int ,y :int ,size :int ,color :Tuple [float ,float ,float ,float ]):
        """Draw text using centralized coordinate system with consistent DPI scaling."""

        gpu_x ,gpu_y =CoordinateSystem .region_to_gpu (x ,y )

        try :
            font_id =0 


            blf .size (font_id ,size )

            blf .position (font_id ,gpu_x ,gpu_y ,0 )
            blf .color (font_id ,*color )
            blf .draw (font_id ,text )
        except Exception as e :
            logger .error (f"Error drawing text: {e}")

    def get_text_dimensions (self ,text :str ,size :int )->Tuple [int ,int ]:
        """Get text dimensions with consistent DPI scaling."""
        cache_key =(text ,size )

        if cache_key not in self ._font_cache :
            try :
                font_id =0 

                blf .size (font_id ,size )

                self ._font_cache [cache_key ]=blf .dimensions (font_id ,text )
            except Exception as e :
                logger .error (f"Error getting text dimensions: {e}")
                self ._font_cache [cache_key ]=(0 ,0 )

        return self ._font_cache [cache_key ]

    def push_clip_rect (self ,x :int ,y :int ,width :int ,height :int ):
        """Push a clipping rectangle onto the clip stack."""

        gpu_x ,gpu_y =CoordinateSystem .region_to_gpu (x ,y )


        new_clip =ClipRegion (gpu_x ,gpu_y ,width ,height )


        if self ._current_clip :

            left =max (self ._current_clip .x ,new_clip .x )
            bottom =max (self ._current_clip .y ,new_clip .y )
            right =min (self ._current_clip .x +self ._current_clip .width ,new_clip .x +new_clip .width )
            top =min (self ._current_clip .y +self ._current_clip .height ,new_clip .y +new_clip .height )


            if right >left and top >bottom :
                new_clip .x =left 
                new_clip .y =bottom 
                new_clip .width =right -left 
                new_clip .height =top -bottom 
            else :

                new_clip .width =0 
                new_clip .height =0 


        if self ._current_clip :
            self ._clip_stack .append (self ._current_clip )

        self ._current_clip =new_clip 
        self ._apply_scissor_test ()

    def pop_clip_rect (self ):
        """Pop the current clipping rectangle from the clip stack."""
        if self ._clip_stack :
            self ._current_clip =self ._clip_stack .pop ()
            self ._apply_scissor_test ()
        else :
            self ._current_clip =None 
            self ._disable_scissor_test ()

    def _apply_scissor_test (self ):
        """Apply the current clipping region using GPU scissor test."""
        if self ._current_clip and self ._current_clip .width >0 and self ._current_clip .height >0 :

            gpu .state .scissor_test_set (True )


            gpu .state .scissor_set (
            int (self ._current_clip .x ),
            int (self ._current_clip .y ),
            int (self ._current_clip .width ),
            int (self ._current_clip .height )
            )
        else :
            self ._disable_scissor_test ()

    def _disable_scissor_test (self ):
        """Disable the scissor test."""
        gpu .state .scissor_test_set (False )

    def is_point_clipped (self ,x :int ,y :int )->bool :
        """Check if a point is clipped by the current clipping region."""
        if not self ._current_clip :
            return False 

        gpu_x ,gpu_y =CoordinateSystem .region_to_gpu (x ,y )

        return (gpu_x <self ._current_clip .x or 
        gpu_x >=self ._current_clip .x +self ._current_clip .width or 
        gpu_y <self ._current_clip .y or 
        gpu_y >=self ._current_clip .y +self ._current_clip .height )

    def is_rect_clipped (self ,bounds :Bounds )->bool :
        """Check if a rectangle is completely clipped."""
        if not self ._current_clip :
            return False 

        gpu_x ,gpu_y =CoordinateSystem .region_to_gpu (bounds .x ,bounds .y )


        return (gpu_x +bounds .width <self ._current_clip .x or 
        gpu_x >=self ._current_clip .x +self ._current_clip .width or 
        gpu_y +bounds .height <self ._current_clip .y or 
        gpu_y >=self ._current_clip .y +self ._current_clip .height )

    def clear_caches (self ):
        """Clear all caches (call when context changes)."""
        self ._batch_cache .clear ()
        self ._font_cache .clear ()
        self ._last_font_size =None 


        self ._clip_stack .clear ()
        self ._current_clip =None 
        self ._disable_scissor_test ()

    def draw_rounded_rect (self ,bounds :Bounds ,color :Tuple [float ,float ,float ,float ],corner_radius :int =0 ):
        """Draw a filled rounded rectangle using centralized coordinate system."""
        if corner_radius <=0 :

            self .draw_rect (bounds ,color )
            return 


        gpu_x ,gpu_y =CoordinateSystem .region_to_gpu (bounds .x ,bounds .y )


        max_radius =min (bounds .width ,bounds .height )//2 
        corner_radius =min (corner_radius ,max_radius )

        if corner_radius <=0 :
            self .draw_rect (bounds ,color )
            return 

        try :
            import math 
            vertices =[]
            indices =[]
            vertex_count =0 


            corner_segments =8 


            center_left =gpu_x +corner_radius 
            center_right =gpu_x +bounds .width -corner_radius 
            center_bottom =gpu_y 
            center_top =gpu_y +bounds .height 

            if center_right >center_left :
                vertices .extend ([
                (center_left ,center_bottom ),
                (center_right ,center_bottom ),
                (center_right ,center_top ),
                (center_left ,center_top )
                ])
                indices .extend ([
                (vertex_count ,vertex_count +1 ,vertex_count +2 ),
                (vertex_count ,vertex_count +2 ,vertex_count +3 )
                ])
                vertex_count +=4 


            left_bottom =gpu_y +corner_radius 
            left_top =gpu_y +bounds .height -corner_radius 

            if left_top >left_bottom :
                vertices .extend ([
                (gpu_x ,left_bottom ),
                (gpu_x +corner_radius ,left_bottom ),
                (gpu_x +corner_radius ,left_top ),
                (gpu_x ,left_top )
                ])
                indices .extend ([
                (vertex_count ,vertex_count +1 ,vertex_count +2 ),
                (vertex_count ,vertex_count +2 ,vertex_count +3 )
                ])
                vertex_count +=4 


            if left_top >left_bottom :
                vertices .extend ([
                (gpu_x +bounds .width -corner_radius ,left_bottom ),
                (gpu_x +bounds .width ,left_bottom ),
                (gpu_x +bounds .width ,left_top ),
                (gpu_x +bounds .width -corner_radius ,left_top )
                ])
                indices .extend ([
                (vertex_count ,vertex_count +1 ,vertex_count +2 ),
                (vertex_count ,vertex_count +2 ,vertex_count +3 )
                ])
                vertex_count +=4 


            corners =[

            {
            'center_x':gpu_x +corner_radius ,
            'center_y':gpu_y +corner_radius ,
            'start_angle':math .pi ,
            'end_angle':3 *math .pi /2 
            },

            {
            'center_x':gpu_x +bounds .width -corner_radius ,
            'center_y':gpu_y +corner_radius ,
            'start_angle':3 *math .pi /2 ,
            'end_angle':2 *math .pi 
            },

            {
            'center_x':gpu_x +bounds .width -corner_radius ,
            'center_y':gpu_y +bounds .height -corner_radius ,
            'start_angle':0 ,
            'end_angle':math .pi /2 
            },

            {
            'center_x':gpu_x +corner_radius ,
            'center_y':gpu_y +bounds .height -corner_radius ,
            'start_angle':math .pi /2 ,
            'end_angle':math .pi 
            }
            ]

            for corner in corners :
                center_x =corner ['center_x']
                center_y =corner ['center_y']
                start_angle =corner ['start_angle']
                end_angle =corner ['end_angle']


                center_vertex_idx =vertex_count 
                vertices .append ((center_x ,center_y ))
                vertex_count +=1 


                for i in range (corner_segments +1 ):
                    angle =start_angle +(end_angle -start_angle )*i /corner_segments 
                    x =center_x +corner_radius *math .cos (angle )
                    y =center_y +corner_radius *math .sin (angle )
                    vertices .append ((x ,y ))

                    if i >0 :

                        indices .append ((center_vertex_idx ,vertex_count -1 ,vertex_count ))

                    vertex_count +=1 

            if vertices and indices :
                batch =batch_for_shader (self .shader ,'TRIS',{"pos":vertices },indices =indices )

                gpu .state .blend_set ('ALPHA')
                self .shader .bind ()
                self .shader .uniform_float ("color",color )
                batch .draw (self .shader )
                gpu .state .blend_set ('NONE')
        except Exception as e :
            logger .error (f"Error drawing rounded rectangle: {e}")

            self .draw_rect (bounds ,color )

    def draw_rounded_rect_outline (self ,bounds :Bounds ,color :Tuple [float ,float ,float ,float ],width :int =1 ,corner_radius :int =0 ):
        """Draw a rounded rectangle outline using filled shapes for proper thickness support."""
        if width <=0 :
            return 

        if corner_radius <=0 :

            self .draw_rect_outline (bounds ,color ,width )
            return 


        max_radius =min (bounds .width ,bounds .height )//2 
        corner_radius =min (corner_radius ,max_radius )

        if corner_radius <=0 :
            self .draw_rect_outline (bounds ,color ,width )
            return 

        try :





            if bounds .height >=width :
                top_bounds =Bounds (
                bounds .x +corner_radius ,
                bounds .y +bounds .height -width ,
                bounds .width -2 *corner_radius ,
                width 
                )
                if top_bounds .width >0 :
                    self .draw_rect (top_bounds ,color )


            if bounds .height >=width :
                bottom_bounds =Bounds (
                bounds .x +corner_radius ,
                bounds .y ,
                bounds .width -2 *corner_radius ,
                width 
                )
                if bottom_bounds .width >0 :
                    self .draw_rect (bottom_bounds ,color )


            if bounds .width >=width :
                left_bounds =Bounds (
                bounds .x ,
                bounds .y +corner_radius ,
                width ,
                bounds .height -2 *corner_radius 
                )
                if left_bounds .height >0 :
                    self .draw_rect (left_bounds ,color )


            if bounds .width >=width :
                right_bounds =Bounds (
                bounds .x +bounds .width -width ,
                bounds .y +corner_radius ,
                width ,
                bounds .height -2 *corner_radius 
                )
                if right_bounds .height >0 :
                    self .draw_rect (right_bounds ,color )


            self ._draw_rounded_corner_borders (bounds ,color ,width ,corner_radius )

        except Exception as e :
            logger .error (f"Error drawing rounded rectangle outline: {e}")

            self .draw_rect_outline (bounds ,color ,width )

    def _draw_rounded_corner_borders (self ,bounds :Bounds ,color :Tuple [float ,float ,float ,float ],width :int ,corner_radius :int ):
        """Draw the corner border segments for thick rounded borders."""
        gpu_x ,gpu_y =CoordinateSystem .region_to_gpu (bounds .x ,bounds .y )

        try :
            import math 
            corner_segments =12 


            corners =[

            {
            'center_x':gpu_x +corner_radius ,
            'center_y':gpu_y +corner_radius ,
            'start_angle':math .pi ,
            'end_angle':3 *math .pi /2 ,
            'outer_radius':corner_radius ,
            'inner_radius':max (0 ,corner_radius -width )
            },

            {
            'center_x':gpu_x +bounds .width -corner_radius ,
            'center_y':gpu_y +corner_radius ,
            'start_angle':3 *math .pi /2 ,
            'end_angle':2 *math .pi ,
            'outer_radius':corner_radius ,
            'inner_radius':max (0 ,corner_radius -width )
            },

            {
            'center_x':gpu_x +bounds .width -corner_radius ,
            'center_y':gpu_y +bounds .height -corner_radius ,
            'start_angle':0 ,
            'end_angle':math .pi /2 ,
            'outer_radius':corner_radius ,
            'inner_radius':max (0 ,corner_radius -width )
            },

            {
            'center_x':gpu_x +corner_radius ,
            'center_y':gpu_y +bounds .height -corner_radius ,
            'start_angle':math .pi /2 ,
            'end_angle':math .pi ,
            'outer_radius':corner_radius ,
            'inner_radius':max (0 ,corner_radius -width )
            }
            ]

            for corner in corners :
                center_x =corner ['center_x']
                center_y =corner ['center_y']
                start_angle =corner ['start_angle']
                end_angle =corner ['end_angle']
                outer_radius =corner ['outer_radius']
                inner_radius =corner ['inner_radius']


                vertices =[]
                indices =[]
                vertex_count =0 


                for i in range (corner_segments +1 ):
                    angle =start_angle +(end_angle -start_angle )*i /corner_segments 


                    outer_x =center_x +outer_radius *math .cos (angle )
                    outer_y =center_y +outer_radius *math .sin (angle )
                    vertices .append ((outer_x ,outer_y ))


                    inner_x =center_x +inner_radius *math .cos (angle )
                    inner_y =center_y +inner_radius *math .sin (angle )
                    vertices .append ((inner_x ,inner_y ))


                    if i >0 :


                        indices .append ((vertex_count -2 ,vertex_count ,vertex_count -1 ))

                        indices .append ((vertex_count ,vertex_count +1 ,vertex_count -1 ))

                    vertex_count +=2 


                if vertices and indices :
                    batch =batch_for_shader (self .shader ,'TRIS',{"pos":vertices },indices =indices )
                    gpu .state .blend_set ('ALPHA')
                    self .shader .bind ()
                    self .shader .uniform_float ("color",color )
                    batch .draw (self .shader )
                    gpu .state .blend_set ('NONE')

        except Exception as e :
            logger .error (f"Error drawing rounded corner borders: {e}")

    def draw_textured_rect (self ,x :int ,y :int ,width :int ,height :int ,texture ,texture_coords =None ):
        """Draw a textured rectangle with optional custom texture coordinates."""

        gpu_x ,gpu_y =CoordinateSystem .region_to_gpu (x ,y )

        vertices =[
        (gpu_x ,gpu_y ),
        (gpu_x +width ,gpu_y ),
        (gpu_x +width ,gpu_y +height ),
        (gpu_x ,gpu_y +height )
        ]


        if texture_coords :

            u_min ,v_min ,u_max ,v_max =texture_coords 
            uvs =[
            (u_min ,v_min ),
            (u_max ,v_min ),
            (u_max ,v_max ),
            (u_min ,v_max )
            ]
        else :

            uvs =[
            (0 ,0 ),
            (1 ,0 ),
            (1 ,1 ),
            (0 ,1 )
            ]

        indices =[(0 ,1 ,2 ),(2 ,3 ,0 )]

        try :
            batch =batch_for_shader (
            self .texture_shader ,'TRIS',
            {"pos":vertices ,"texCoord":uvs },
            indices =indices 
            )

            gpu .state .blend_set ('ALPHA')
            self .texture_shader .bind ()
            self .texture_shader .uniform_sampler ("image",texture )
            batch .draw (self .texture_shader )
            gpu .state .blend_set ('NONE')

        except Exception as e :
            logger .error (f"Error drawing textured rectangle: {e}")

    def draw_rounded_textured_rect (self ,bounds :Bounds ,texture ,corner_radius :int ,texture_coords =None ):
        """Draw a textured rectangle with rounded corners."""
        try :


            if corner_radius >0 :
                logger .warning ("Rounded textured rectangles not yet implemented, falling back to regular texture")


            self .draw_textured_rect (
            bounds .x ,bounds .y ,bounds .width ,bounds .height ,
            texture ,texture_coords 
            )

        except Exception as e :
            logger .error (f"Error drawing rounded textured rectangle: {e}")

            self .draw_textured_rect (bounds .x ,bounds .y ,bounds .width ,bounds .height ,texture ,texture_coords )

    def draw_image (self ,texture ,x :int ,y :int ,width :int ,height :int ):
        """Draw a GPU texture."""
        if not texture :
            return 

        try :

            self .draw_textured_rect (x ,y ,width ,height ,texture )

        except Exception as e :
            logger .error (f"Error drawing texture: {e}")

    def draw_rect_with_bottom_corners_rounded (self ,bounds :Bounds ,color :Tuple [float ,float ,float ,float ],corner_radius :int =0 ):
        """Draw a filled rectangle with only bottom left and bottom right corners rounded."""
        if corner_radius <=0 :

            self .draw_rect (bounds ,color )
            return 


        gpu_x ,gpu_y =CoordinateSystem .region_to_gpu (bounds .x ,bounds .y )


        max_radius =min (bounds .width ,bounds .height )//2 
        corner_radius =min (corner_radius ,max_radius )

        if corner_radius <=0 :
            self .draw_rect (bounds ,color )
            return 

        try :
            import math 
            vertices =[]
            indices =[]
            vertex_count =0 


            corner_segments =8 


            center_left =gpu_x +corner_radius 
            center_right =gpu_x +bounds .width -corner_radius 
            center_bottom =gpu_y 
            center_top =gpu_y +bounds .height 

            if center_right >center_left :
                vertices .extend ([
                (center_left ,center_bottom ),
                (center_right ,center_bottom ),
                (center_right ,center_top ),
                (center_left ,center_top )
                ])
                indices .extend ([
                (vertex_count ,vertex_count +1 ,vertex_count +2 ),
                (vertex_count ,vertex_count +2 ,vertex_count +3 )
                ])
                vertex_count +=4 


            left_bottom =gpu_y +corner_radius 
            left_top =gpu_y +bounds .height 

            if left_top >left_bottom :
                vertices .extend ([
                (gpu_x ,left_bottom ),
                (gpu_x +corner_radius ,left_bottom ),
                (gpu_x +corner_radius ,left_top ),
                (gpu_x ,left_top )
                ])
                indices .extend ([
                (vertex_count ,vertex_count +1 ,vertex_count +2 ),
                (vertex_count ,vertex_count +2 ,vertex_count +3 )
                ])
                vertex_count +=4 


            if left_top >left_bottom :
                vertices .extend ([
                (gpu_x +bounds .width -corner_radius ,left_bottom ),
                (gpu_x +bounds .width ,left_bottom ),
                (gpu_x +bounds .width ,left_top ),
                (gpu_x +bounds .width -corner_radius ,left_top )
                ])
                indices .extend ([
                (vertex_count ,vertex_count +1 ,vertex_count +2 ),
                (vertex_count ,vertex_count +2 ,vertex_count +3 )
                ])
                vertex_count +=4 


            corners =[

            {
            'center_x':gpu_x +corner_radius ,
            'center_y':gpu_y +corner_radius ,
            'start_angle':math .pi ,
            'end_angle':3 *math .pi /2 
            },

            {
            'center_x':gpu_x +bounds .width -corner_radius ,
            'center_y':gpu_y +corner_radius ,
            'start_angle':3 *math .pi /2 ,
            'end_angle':2 *math .pi 
            }
            ]

            for corner in corners :
                center_x =corner ['center_x']
                center_y =corner ['center_y']
                start_angle =corner ['start_angle']
                end_angle =corner ['end_angle']


                center_vertex_idx =vertex_count 
                vertices .append ((center_x ,center_y ))
                vertex_count +=1 


                for i in range (corner_segments +1 ):
                    angle =start_angle +(end_angle -start_angle )*i /corner_segments 
                    x =center_x +corner_radius *math .cos (angle )
                    y =center_y +corner_radius *math .sin (angle )
                    vertices .append ((x ,y ))

                    if i >0 :

                        indices .append ((center_vertex_idx ,vertex_count -1 ,vertex_count ))

                    vertex_count +=1 

            if vertices and indices :
                batch =batch_for_shader (self .shader ,'TRIS',{"pos":vertices },indices =indices )

                gpu .state .blend_set ('ALPHA')
                self .shader .bind ()
                self .shader .uniform_float ("color",color )
                batch .draw (self .shader )
                gpu .state .blend_set ('NONE')
        except Exception as e :
            logger .error (f"Error drawing rectangle with bottom corners rounded: {e}")

            self .draw_rect (bounds ,color )

    def draw_rect_outline_with_bottom_corners_rounded (self ,bounds :Bounds ,color :Tuple [float ,float ,float ,float ],width :int =1 ,corner_radius :int =0 ):
        """Draw a rectangle outline with only bottom left and bottom right corners rounded."""
        if width <=0 :
            return 

        if corner_radius <=0 :

            self .draw_rect_outline (bounds ,color ,width )
            return 


        max_radius =min (bounds .width ,bounds .height )//2 
        corner_radius =min (corner_radius ,max_radius )

        if corner_radius <=0 :
            self .draw_rect_outline (bounds ,color ,width )
            return 

        try :


            if bounds .height >=width :
                top_bounds =Bounds (
                bounds .x ,
                bounds .y +bounds .height -width ,
                bounds .width ,
                width 
                )
                if top_bounds .width >0 :
                    self .draw_rect (top_bounds ,color )


            if bounds .width >=width :
                left_bounds =Bounds (
                bounds .x ,
                bounds .y +corner_radius ,
                width ,
                bounds .height -corner_radius 
                )
                if left_bounds .height >0 :
                    self .draw_rect (left_bounds ,color )


            if bounds .width >=width :
                right_bounds =Bounds (
                bounds .x +bounds .width -width ,
                bounds .y +corner_radius ,
                width ,
                bounds .height -corner_radius 
                )
                if right_bounds .height >0 :
                    self .draw_rect (right_bounds ,color )


            self ._draw_bottom_rounded_corner_borders (bounds ,color ,width ,corner_radius )

        except Exception as e :
            logger .error (f"Error drawing rectangle outline with bottom corners rounded: {e}")

            self .draw_rect_outline (bounds ,color ,width )

    def _draw_bottom_rounded_corner_borders (self ,bounds :Bounds ,color :Tuple [float ,float ,float ,float ],width :int ,corner_radius :int ):
        """Draw the bottom corner border segments for thick rounded borders."""
        gpu_x ,gpu_y =CoordinateSystem .region_to_gpu (bounds .x ,bounds .y )

        try :
            import math 
            corner_segments =12 


            corners =[

            {
            'center_x':gpu_x +corner_radius ,
            'center_y':gpu_y +corner_radius ,
            'start_angle':math .pi ,
            'end_angle':3 *math .pi /2 ,
            'outer_radius':corner_radius ,
            'inner_radius':max (0 ,corner_radius -width )
            },

            {
            'center_x':gpu_x +bounds .width -corner_radius ,
            'center_y':gpu_y +corner_radius ,
            'start_angle':3 *math .pi /2 ,
            'end_angle':2 *math .pi ,
            'outer_radius':corner_radius ,
            'inner_radius':max (0 ,corner_radius -width )
            }
            ]

            for corner in corners :
                center_x =corner ['center_x']
                center_y =corner ['center_y']
                start_angle =corner ['start_angle']
                end_angle =corner ['end_angle']
                outer_radius =corner ['outer_radius']
                inner_radius =corner ['inner_radius']


                vertices =[]
                indices =[]
                vertex_count =0 


                for i in range (corner_segments +1 ):
                    angle =start_angle +(end_angle -start_angle )*i /corner_segments 


                    outer_x =center_x +outer_radius *math .cos (angle )
                    outer_y =center_y +outer_radius *math .sin (angle )
                    vertices .append ((outer_x ,outer_y ))


                    inner_x =center_x +inner_radius *math .cos (angle )
                    inner_y =center_y +inner_radius *math .sin (angle )
                    vertices .append ((inner_x ,inner_y ))


                    if i >0 :


                        indices .append ((vertex_count -2 ,vertex_count ,vertex_count -1 ))

                        indices .append ((vertex_count ,vertex_count +1 ,vertex_count -1 ))

                    vertex_count +=2 


                if vertices and indices :
                    batch =batch_for_shader (self .shader ,'TRIS',{"pos":vertices },indices =indices )
                    gpu .state .blend_set ('ALPHA')
                    self .shader .bind ()
                    self .shader .uniform_float ("color",color )
                    batch .draw (self .shader )
                    gpu .state .blend_set ('NONE')

        except Exception as e :
            logger .error (f"Error drawing bottom rounded corner borders: {e}")