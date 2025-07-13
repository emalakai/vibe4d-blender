from .coordinates import CoordinateSystem 
from .unified_styles import Styles as UnifiedStyles 
import bpy 

def get_scaled_font_size ()->int :
    """Get the base font size scaled by the UI scale factor."""
    return UnifiedStyles .get_font_size ()

class FontSizesMeta (type ):
    """Metaclass to enable class properties for FontSizes."""
    @property 
    def Default (cls )->int :
        return UnifiedStyles .get_font_size ()

    @property 
    def Title (cls )->int :
        return UnifiedStyles .get_font_size ("title")

class FontSizes (metaclass =FontSizesMeta ):
    """Dynamic font sizes that scale with UI scale factor."""
    pass 

class MarkdownLayout :
    """Layout constants for markdown message components."""

    @classmethod 
    def CORNER_RADIUS (cls )->int :
        return UnifiedStyles .get_markdown_corner_radius ()

    @classmethod 
    def PADDING (cls )->int :
        return UnifiedStyles .get_markdown_padding ()


    @classmethod 
    def BLOCK_ICON_SIZE (cls )->int :
        return UnifiedStyles .get_markdown_block_icon_size ()

    @classmethod 
    def BLOCK_PADDING (cls )->int :
        return UnifiedStyles .get_markdown_block_padding ()

    @classmethod 
    def BLOCK_TEXT_PADDING (cls )->int :
        return UnifiedStyles .get_markdown_block_text_padding ()

    @classmethod 
    def BLOCK_HEIGHT (cls )->int :
        return UnifiedStyles .get_markdown_block_height ()

    @classmethod 
    def BLOCK_MARGIN (cls )->int :
        return UnifiedStyles .get_markdown_block_margin ()

    @classmethod 
    def BLOCK_CORNER_RADIUS (cls )->int :
        return UnifiedStyles .get_markdown_block_corner_radius ()

    @classmethod 
    def BLOCK_MIN_WIDTH (cls )->int :
        return UnifiedStyles .get_markdown_block_min_width ()


    LINE_HEIGHT_ADDITION =UnifiedStyles .LINE_HEIGHT_ADDITION 
    TEXT_ESTIMATION_FACTOR =UnifiedStyles .TEXT_ESTIMATION_FACTOR 


    HEADING_SIZE_MULTIPLIERS =UnifiedStyles .HEADING_SIZE_MULTIPLIERS 


    CODE_FONT_SIZE_MULTIPLIER =UnifiedStyles .CODE_FONT_SIZE_MULTIPLIER 
    INLINE_CODE_FONT_SIZE_MULTIPLIER =UnifiedStyles .INLINE_CODE_FONT_SIZE_MULTIPLIER 
    BOLD_FONT_SIZE_MULTIPLIER =UnifiedStyles .BOLD_FONT_SIZE_MULTIPLIER 


    @classmethod 
    def MIN_COMPONENT_WIDTH (cls )->int :
        return UnifiedStyles .get_markdown_min_component_width ()

    @classmethod 
    def MIN_COMPONENT_HEIGHT (cls )->int :
        return UnifiedStyles .get_markdown_min_component_height ()


class _StyledLabel :
    def __init__ (self ):

        self .a =10 
