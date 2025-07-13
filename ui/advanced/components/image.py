"""
Comprehensive Image component for displaying PNG images with advanced features.
This component can be reused by other components that need image functionality.
"""

import os 
import logging 
import array 
from typing import Optional ,Union ,Tuple 
from enum import Enum 
import bpy 
import gpu 
from gpu_extras .batch import batch_for_shader 
from gpu .types import Buffer 

from .base import UIComponent 
from ..types import Bounds 

logger =logging .getLogger (__name__ )


class ImageFit (Enum ):
    """Image fitting modes similar to CSS object-fit."""
    FILL ="fill"
    CONTAIN ="contain"
    COVER ="cover"
    SCALE_DOWN ="scale_down"
    NONE ="none"


class ImagePosition (Enum ):
    """Image positioning within container."""
    CENTER ="center"
    TOP_LEFT ="top_left"
    TOP_CENTER ="top_center"
    TOP_RIGHT ="top_right"
    CENTER_LEFT ="center_left"
    CENTER_RIGHT ="center_right"
    BOTTOM_LEFT ="bottom_left"
    BOTTOM_CENTER ="bottom_center"
    BOTTOM_RIGHT ="bottom_right"


class ImageComponent (UIComponent ):
    """Comprehensive image component with advanced features."""

    def __init__ (self ,
    image_path :str ,
    x :int =0 ,
    y :int =0 ,
    width :int =100 ,
    height :int =100 ,
    fit :ImageFit =ImageFit .FILL ,
    position :ImagePosition =ImagePosition .CENTER ,
    corner_radius :int =0 ,
    tint_color :Optional [Tuple [float ,float ,float ,float ]]=None ,
    opacity :float =1.0 ,
    background_color :Optional [Tuple [float ,float ,float ,float ]]=None ,
    border_width :int =0 ,
    border_color :Tuple [float ,float ,float ,float ]=(0.5 ,0.5 ,0.5 ,1.0 )):
        """
        Initialize ImageComponent with advanced features.
        
        Args:
            image_path: Path to image file (relative to addon icons folder or absolute path)
            x, y, width, height: Component bounds
            fit: How image should fit within bounds (ImageFit enum)
            position: How image should be positioned within bounds (ImagePosition enum)
            corner_radius: Radius for rounded corners (0 = no rounding)
            tint_color: Optional color tint to apply to image (RGBA)
            opacity: Overall opacity (0.0 to 1.0)
            background_color: Optional background color behind image
            border_width: Width of border around component
            border_color: Color of border
        """
        super ().__init__ (x ,y ,width ,height )

        self .image_path =image_path 
        self .fit =fit 
        self .position =position 
        self .corner_radius =corner_radius 
        self .tint_color =tint_color 
        self .opacity =opacity 
        self .background_color =background_color 
        self .border_width =border_width 
        self .border_color =border_color 


        self .image_texture =None 
        self .image_loaded =False 
        self .image_data =None 
        self ._texture_creation_attempted =False 
        self .image_width =0 
        self .image_height =0 


        self ._render_bounds =None 
        self ._render_texture_coords =None 


        self ._load_image_data ()

    def set_image (self ,image_path :str ):
        """Change the image being displayed."""
        if self .image_path !=image_path :
            self .cleanup ()
            self .image_path =image_path 
            self .image_texture =None 
            self .image_loaded =False 
            self .image_data =None 
            self ._texture_creation_attempted =False 
            self ._render_bounds =None 
            self ._render_texture_coords =None 
            self ._load_image_data ()

    def set_fit (self ,fit :ImageFit ):
        """Change the image fitting mode."""
        if self .fit !=fit :
            self .fit =fit 
            self ._render_bounds =None 

    def set_image_position (self ,position :ImagePosition ):
        """Change the image positioning within bounds."""
        if self .position !=position :
            self .position =position 
            self ._render_bounds =None 

    def set_position (self ,x :int ,y :int ):
        """Set component position (override base class method)."""
        super ().set_position (x ,y )
        self ._render_bounds =None 

    def set_corner_radius (self ,radius :int ):
        """Change the corner radius."""
        self .corner_radius =radius 

    def set_tint_color (self ,color :Optional [Tuple [float ,float ,float ,float ]]):
        """Change the tint color."""
        self .tint_color =color 

    def set_opacity (self ,opacity :float ):
        """Change the opacity (0.0 to 1.0)."""
        self .opacity =max (0.0 ,min (1.0 ,opacity ))

    def _resolve_image_path (self )->str :
        """Resolve the image path to an absolute path."""
        if os .path .isabs (self .image_path ):
            return self .image_path 


        addon_dir =os .path .dirname (os .path .dirname (__file__ ))
        icon_path =os .path .join (addon_dir ,"icons",self .image_path )
        if os .path .exists (icon_path ):
            return icon_path 


        addon_path =os .path .join (addon_dir ,self .image_path )
        if os .path .exists (addon_path ):
            return addon_path 


        return self .image_path 

    def _load_image_data (self ):
        """Load the PNG image data using Blender's image API (without creating GPU texture)."""
        try :
            resolved_path =self ._resolve_image_path ()

            if not os .path .exists (resolved_path ):
                if resolved_path .startswith ("data:image"):
                    logger .info ("Image is a data URI, skipping loading")
                    return 
                else :
                    logger .error (f"Image file not found: {resolved_path}")
                    return 


            image_name =f"vibe4d_image_{hash(resolved_path) % 10000}"
            if image_name in bpy .data .images :

                try :
                    bpy .data .images .remove (bpy .data .images [image_name ])
                except Exception as e :
                    logger .debug (f"Could not remove existing image {image_name}: {e}")


            self .image_data =bpy .data .images .load (resolved_path )
            self .image_data .name =image_name 


            if self .image_data .pixels is None :
                self .image_data .reload ()


            if self ._is_image_data_valid ()and self .image_data .pixels :
                self .image_width =self .image_data .size [0 ]
                self .image_height =self .image_data .size [1 ]
            else :
                logger .error (f"Failed to load valid pixels for image: {self.image_path}")
                self .image_data =None 

        except Exception as e :
            logger .error (f"Error loading image file {resolved_path}: {e}")
            self .image_data =None 

    def _is_image_data_valid (self )->bool :
        """Check if image_data is still valid and accessible."""
        if not self .image_data :
            return False 

        try :

            _ =self .image_data .name 
            return True 
        except ReferenceError :

            logger .debug (f"Image data for {self.image_path} has been removed")
            self .image_data =None 
            return False 
        except Exception as e :
            logger .debug (f"Image data validation failed for {self.image_path}: {e}")
            self .image_data =None 
            return False 

    def _ensure_gpu_texture (self ):
        """Create GPU texture from loaded image data (lazy initialization)."""

        if self ._texture_creation_attempted :
            return self .image_loaded 

        self ._texture_creation_attempted =True 


        if not self ._is_image_data_valid ():
            logger .warning (f"No valid image data available for: {self.image_path}")
            return False 


        try :
            if not self .image_data .pixels :
                logger .warning (f"No pixel data available for: {self.image_path}")
                return False 
        except ReferenceError :
            logger .warning (f"Image data became invalid while checking pixels: {self.image_path}")
            self .image_data =None 
            return False 

        try :

            if not self ._is_image_data_valid ():
                logger .warning (f"Image data became invalid during texture creation: {self.image_path}")
                return False 

            width =self .image_data .size [0 ]
            height =self .image_data .size [1 ]



            try :
                pixel_data =list (self .image_data .pixels )
            except ReferenceError :
                logger .warning (f"Image data became invalid while accessing pixels: {self.image_path}")
                self .image_data =None 
                return False 


            if self .tint_color :
                tinted_pixels =[]
                for i in range (0 ,len (pixel_data ),4 ):
                    r ,g ,b ,a =pixel_data [i :i +4 ]

                    tinted_pixels .extend ([
                    r *self .tint_color [0 ],
                    g *self .tint_color [1 ],
                    b *self .tint_color [2 ],
                    a *self .tint_color [3 ]
                    ])
                pixel_data =tinted_pixels 


            if self .opacity <1.0 :
                for i in range (3 ,len (pixel_data ),4 ):
                    pixel_data [i ]*=self .opacity 


            pixel_buffer =array .array ('f',pixel_data )
            gpu_buffer =Buffer ('FLOAT',len (pixel_buffer ),pixel_buffer )


            self .image_texture =gpu .types .GPUTexture (
            size =(width ,height ),
            format ='RGBA32F',
            data =gpu_buffer 
            )

            self .image_loaded =True 
            return True 

        except Exception as e :
            logger .error (f"Failed to create GPU texture for image {self.image_path}: {e}")
            self .image_loaded =False 
            return False 

    def _calculate_render_bounds (self )->Tuple [Bounds ,Tuple [float ,float ,float ,float ]]:
        """Calculate actual render bounds and texture coordinates based on fit and position."""
        if self ._render_bounds is not None and self ._render_texture_coords is not None :
            return self ._render_bounds ,self ._render_texture_coords 

        if not self .image_loaded or self .image_width ==0 or self .image_height ==0 :

            self ._render_bounds =self .bounds 
            self ._render_texture_coords =(0.0 ,0.0 ,1.0 ,1.0 )
            return self ._render_bounds ,self ._render_texture_coords 

        container_width =self .bounds .width 
        container_height =self .bounds .height 
        image_width =self .image_width 
        image_height =self .image_height 

        if self .fit ==ImageFit .FILL :

            render_bounds =self .bounds 
            texture_coords =(0.0 ,0.0 ,1.0 ,1.0 )

        elif self .fit ==ImageFit .CONTAIN :

            container_aspect =container_width /container_height 
            image_aspect =image_width /image_height 

            if image_aspect >container_aspect :

                scale =container_width /image_width 
                scaled_height =image_height *scale 
                scaled_width =container_width 
            else :

                scale =container_height /image_height 
                scaled_width =image_width *scale 
                scaled_height =container_height 


            x_offset ,y_offset =self ._calculate_position_offset (
            container_width ,container_height ,scaled_width ,scaled_height 
            )

            render_bounds =Bounds (
            self .bounds .x +x_offset ,
            self .bounds .y +y_offset ,
            scaled_width ,
            scaled_height 
            )
            texture_coords =(0.0 ,0.0 ,1.0 ,1.0 )

        elif self .fit ==ImageFit .COVER :

            container_aspect =container_width /container_height 
            image_aspect =image_width /image_height 

            if image_aspect >container_aspect :

                scale =container_height /image_height 
                scaled_width =image_width *scale 
                scaled_height =container_height 


                crop_ratio =container_width /scaled_width 
                x_crop =(1.0 -crop_ratio )/2.0 
                texture_coords =(x_crop ,0.0 ,1.0 -x_crop ,1.0 )
            else :

                scale =container_width /image_width 
                scaled_height =image_height *scale 
                scaled_width =container_width 


                crop_ratio =container_height /scaled_height 
                y_crop =(1.0 -crop_ratio )/2.0 
                texture_coords =(0.0 ,y_crop ,1.0 ,1.0 -y_crop )

            render_bounds =self .bounds 

        elif self .fit ==ImageFit .SCALE_DOWN :

            if image_width <=container_width and image_height <=container_height :

                x_offset ,y_offset =self ._calculate_position_offset (
                container_width ,container_height ,image_width ,image_height 
                )
                render_bounds =Bounds (
                self .bounds .x +x_offset ,
                self .bounds .y +y_offset ,
                image_width ,
                image_height 
                )
                texture_coords =(0.0 ,0.0 ,1.0 ,1.0 )
            else :

                return self ._calculate_contain_bounds ()

        elif self .fit ==ImageFit .NONE :

            x_offset ,y_offset =self ._calculate_position_offset (
            container_width ,container_height ,image_width ,image_height 
            )
            render_bounds =Bounds (
            self .bounds .x +x_offset ,
            self .bounds .y +y_offset ,
            image_width ,
            image_height 
            )
            texture_coords =(0.0 ,0.0 ,1.0 ,1.0 )

        self ._render_bounds =render_bounds 
        self ._render_texture_coords =texture_coords 
        return render_bounds ,texture_coords 

    def _calculate_contain_bounds (self ):
        """Helper method for contain logic used by scale_down."""
        container_width =self .bounds .width 
        container_height =self .bounds .height 
        image_width =self .image_width 
        image_height =self .image_height 

        container_aspect =container_width /container_height 
        image_aspect =image_width /image_height 

        if image_aspect >container_aspect :
            scale =container_width /image_width 
            scaled_height =image_height *scale 
            scaled_width =container_width 
        else :
            scale =container_height /image_height 
            scaled_width =image_width *scale 
            scaled_height =container_height 

        x_offset ,y_offset =self ._calculate_position_offset (
        container_width ,container_height ,scaled_width ,scaled_height 
        )

        render_bounds =Bounds (
        self .bounds .x +x_offset ,
        self .bounds .y +y_offset ,
        scaled_width ,
        scaled_height 
        )
        return render_bounds ,(0.0 ,0.0 ,1.0 ,1.0 )

    def _calculate_position_offset (self ,container_width :float ,container_height :float ,
    content_width :float ,content_height :float )->Tuple [float ,float ]:
        """Calculate offset for positioning content within container."""
        if self .position ==ImagePosition .CENTER :
            return (container_width -content_width )/2 ,(container_height -content_height )/2 
        elif self .position ==ImagePosition .TOP_LEFT :
            return 0 ,container_height -content_height 
        elif self .position ==ImagePosition .TOP_CENTER :
            return (container_width -content_width )/2 ,container_height -content_height 
        elif self .position ==ImagePosition .TOP_RIGHT :
            return container_width -content_width ,container_height -content_height 
        elif self .position ==ImagePosition .CENTER_LEFT :
            return 0 ,(container_height -content_height )/2 
        elif self .position ==ImagePosition .CENTER_RIGHT :
            return container_width -content_width ,(container_height -content_height )/2 
        elif self .position ==ImagePosition .BOTTOM_LEFT :
            return 0 ,0 
        elif self .position ==ImagePosition .BOTTOM_CENTER :
            return (container_width -content_width )/2 ,0 
        elif self .position ==ImagePosition .BOTTOM_RIGHT :
            return container_width -content_width ,0 
        else :
            return 0 ,0 

    def render (self ,renderer ):
        """Render the image component with all features."""
        if not self .visible :
            return 


        if self .background_color :
            if self .corner_radius >0 :
                renderer .draw_rounded_rect (self .bounds ,self .background_color ,self .corner_radius )
            else :
                renderer .draw_rect (self .bounds ,self .background_color )


        if not self .image_loaded and not self ._texture_creation_attempted and self ._is_image_data_valid ():
            self ._ensure_gpu_texture ()


        if self .image_loaded and self .image_texture :
            try :
                render_bounds ,texture_coords =self ._calculate_render_bounds ()

                if self .corner_radius >0 :

                    renderer .draw_rounded_textured_rect (
                    render_bounds ,
                    self .image_texture ,
                    self .corner_radius ,
                    texture_coords 
                    )
                else :

                    renderer .draw_textured_rect (
                    x =render_bounds .x ,
                    y =render_bounds .y ,
                    width =render_bounds .width ,
                    height =render_bounds .height ,
                    texture =self .image_texture ,
                    texture_coords =texture_coords 
                    )

            except Exception as e :
                logger .error (f"Error rendering image {self.image_path}: {e}")
                self ._render_fallback (renderer )
        else :
            self ._render_fallback (renderer )


        if self .border_width >0 :
            if self .corner_radius >0 :
                renderer .draw_rounded_rect_outline (
                self .bounds ,self .border_color ,self .border_width ,self .corner_radius 
                )
            else :
                renderer .draw_rect_outline (self .bounds ,self .border_color ,self .border_width )

    def _render_fallback (self ,renderer ):
        """Render fallback when image fails to load."""

        placeholder_color =(0.3 ,0.3 ,0.3 ,0.8 )
        if self .corner_radius >0 :
            renderer .draw_rounded_rect (self .bounds ,placeholder_color ,self .corner_radius )
        else :
            renderer .draw_rect (self .bounds ,placeholder_color )


        display_text =os .path .basename (self .image_path )
        if len (display_text )>20 :
            display_text =display_text [:17 ]+"..."

        text_x =self .bounds .x +10 
        text_y =self .bounds .y +self .bounds .height //2 
        renderer .draw_text (display_text ,text_x ,text_y ,16 ,(1.0 ,1.0 ,1.0 ,1.0 ))

    def set_size (self ,width :int ,height :int ):
        """Override set_size to invalidate render calculations."""
        super ().set_size (width ,height )
        self ._render_bounds =None 
        self ._render_texture_coords =None 

    def cleanup (self ):
        """Clean up resources when component is destroyed."""
        if self .image_texture :

            self .image_texture =None 


        if self .image_data :
            try :

                image_name =self .image_data .name 
                if image_name in bpy .data .images :
                    bpy .data .images .remove (self .image_data )
            except ReferenceError :

                logger .debug (f"Image data for {self.image_path} was already removed")
            except Exception as e :
                logger .debug (f"Error during image cleanup for {self.image_path}: {e}")
            finally :
                self .image_data =None 

        self .image_loaded =False 
        self ._texture_creation_attempted =False 
        self ._render_bounds =None 
        self ._render_texture_coords =None 