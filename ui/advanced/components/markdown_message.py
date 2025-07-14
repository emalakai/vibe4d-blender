"""
Markdown Message component for displaying AI responses with markdown formatting.
Uses a simple custom parser to render formatted text.
"""

import blf 
import bpy 
import bgl 
import gpu 
from gpu_extras .batch import batch_for_shader 
import logging 
import os 
import array 
import time 
import math 
from typing import TYPE_CHECKING ,List ,Dict ,Any 
from gpu .types import Buffer 

from .base import UIComponent 
from ..theme import get_themed_style 
from .message import wrap_text_blf 
from .image import ImageComponent ,ImageFit ,ImagePosition 
from ..styles import FontSizes ,MarkdownLayout 
from ..coordinates import CoordinateSystem 

if TYPE_CHECKING :
    from ..renderer import UIRenderer 

logger =logging .getLogger (__name__ )


MARKDOWN_LINE_HEIGHT_MULTIPLIER =1.5 
MIN_LINE_HEIGHT =8 


FONT_BASELINE_OFFSET_RATIO =0.3 


def _get_consistent_line_height (font_size :int )->int :
    """Get consistent line height based on font size, not variable text measurements."""

    base_height =font_size 

    line_height =math .ceil (base_height *MARKDOWN_LINE_HEIGHT_MULTIPLIER )

    return max (MIN_LINE_HEIGHT ,line_height )


class MarkdownElement :
    """Represents a formatted text element from markdown parsing."""

    def __init__ (self ,text :str ,element_type :str ='text',level :int =0 ):
        self .text =text 
        self .element_type =element_type 
        self .level =level 
        self .font_size =FontSizes .Default 
        self .color =(0.9 ,0.9 ,0.9 ,1.0 )
        self .is_bold =False 
        self .is_italic =False 
        self .is_code =False 
        self .block_type =None 


        self .is_animated =False 
        self .animation_start_time =None 


        self .formatted_parts =[]

    def set_formatted_parts (self ,parts ):
        """Set formatted parts for mixed inline formatting."""
        self .formatted_parts =parts 

    def start_animation (self ):
        """Start animation for this element."""
        self .is_animated =True 
        self .animation_start_time =time .time ()

    def stop_animation (self ):
        """Stop animation for this element."""
        self .is_animated =False 
        self .animation_start_time =None 

    def get_animation_progress (self )->float :
        """Get animation progress (0.0 to 1.0) for gradient positioning."""
        if not self .is_animated or self .animation_start_time is None :
            return 0.0 


        cycle_duration =0.8 

        elapsed =time .time ()-self .animation_start_time 
        progress =(elapsed %cycle_duration )/cycle_duration 

        return progress 

    def apply_formatting (self ,base_font_size :int ,base_color :tuple ):
        """Apply formatting based on element type."""
        self .color =base_color 

        if self .element_type =='heading':

            self .font_size =int (base_font_size *MarkdownLayout .HEADING_SIZE_MULTIPLIERS .get (self .level ,1.0 ))
            self .is_bold =True 
        elif self .element_type =='code'or self .element_type =='code_block':
            self .font_size =int (base_font_size *MarkdownLayout .CODE_FONT_SIZE_MULTIPLIER )
            self .color =(0.8 ,1.0 ,0.8 ,1.0 )
        elif self .element_type =='bold':
            self .is_bold =True 
        elif self .element_type =='italic':
            self .is_italic =True 
        elif self .element_type =='list_item':
            self .font_size =base_font_size 

            if not self .text .startswith ('• ')and not self .text .startswith ('- ')and not self .text .startswith ('* '):

                if not (len (self .text )>2 and self .text [0 ].isdigit ()and self .text [1 :3 ]=='. '):
                    self .text ="• "+self .text 
        elif self .element_type =='block':

            self .font_size =int (base_font_size *MarkdownLayout .CODE_FONT_SIZE_MULTIPLIER )
            self .color =(0.6 ,0.6 ,0.6 ,1.0 )


            if self ._is_in_progress_block ():
                self .start_animation ()
        else :

            self .font_size =base_font_size 

    def _is_in_progress_block (self )->bool :
        """Check if this block represents an in-progress action."""
        if not self .block_type :
            return False 

        text_lower =self .text .lower ()


        completed_indicators =[
        'code executed','execution complete','executed successfully',
        'scene read','scene analyzed','analysis complete',
        'found results','search completed','search finished',
        'image analyzed','image processing complete',
        'viewport captured','viewport capture complete','screenshot captured',
        'render captured','render complete','render finished','rendered successfully',
        'properties read','settings read',
        'tool completed','tool finished','execution done',
        'scene modified','scene updated','objects created',
        'objects added','modification complete','update complete',
        'code execution failed','execution failed','scene reading failed',
        'scene analysis failed','web search failed','image analysis failed',
        'viewport capture failed','render failed','properties reading failed',
        'render settings reading failed','nodes analysis failed','tool failed'
        ]


        if any (indicator in text_lower for indicator in completed_indicators ):
            return False 


        in_progress_indicators =[
        'writing code','reading scene','analyzing scene','querying',
        'planning','thinking','processing','searching web','searching',
        'analyzing image','processing image','reading image',
        'capturing viewport','viewport capture','taking screenshot',
        'capturing render','render capture',
        'rendering scene','rendering','scene render',
        'writing','generating text','finding','locating',
        'using tool','analyzing data','processing data',
        'modifying scene','updating scene','creating objects','adding objects'
        ]

        return any (indicator in text_lower for indicator in in_progress_indicators )


class BlockIconManager :
    """Manager for loading and caching block icons using the unified ImageComponent."""

    def __init__ (self ):
        self .icon_components ={}

    def get_icon_component (self ,icon_name :str ):
        """Get or create an ImageComponent for the specified icon."""
        if icon_name not in self .icon_components :


            self .icon_components [icon_name ]=ImageComponent (
            image_path =f"{icon_name}.png",
            x =0 ,y =0 ,width =MarkdownLayout .BLOCK_ICON_SIZE (),height =MarkdownLayout .BLOCK_ICON_SIZE (),
            fit =ImageFit .CONTAIN ,
            position =ImagePosition .CENTER 
            )
        return self .icon_components [icon_name ]

    def get_block_icon_texture (self ,block_type :str ):
        """Get icon texture for a block type."""
        if not block_type :
            return None 



        icon_mapping ={
        'reading':'scene',
        'planning':'brain',
        'coding':'code',
        'executing':'code',
        'fixing':'bug',
        'web_search':'globe',
        'tool':'settings',
        'processing':'brain',
        'scene':'scene',
        'image':'image',
        'write':'pen',
        'search':'search',
        'viewport_capture':'image',
        'render_capture':'image',
        }

        icon_name =icon_mapping .get (block_type )
        if not icon_name :
            return None 


        try :
            icon_component =self .get_icon_component (icon_name )

            if not icon_component .image_loaded and not icon_component ._texture_creation_attempted :
                icon_component ._ensure_gpu_texture ()
            return icon_component .image_texture if icon_component .image_loaded else None 
        except Exception as e :
            logger .error (f"Failed to load icon {icon_name}: {str(e)}")
            return None 

    def cleanup (self ):
        """Clean up resources."""
        for icon_component in self .icon_components .values ():
            icon_component .cleanup ()
        self .icon_components .clear ()



block_icon_manager =BlockIconManager ()


class SimpleMarkdownRenderer :
    """Simple markdown renderer that converts markdown to formatted text elements."""

    def __init__ (self ):
        self .elements =[]

    def parse_markdown (self ,markdown_text :str )->List [MarkdownElement ]:
        """Parse markdown text and return list of formatted elements."""
        self .elements =[]

        try :
            self ._parse_simple_markdown (markdown_text )


            if not self .elements and markdown_text .strip ():
                self .elements =[MarkdownElement (markdown_text .strip (),'text')]

        except Exception as e :
            logger .error (f"Error parsing markdown: {e}")

            self .elements =[MarkdownElement (markdown_text ,'text')]

        return self .elements 

    def _parse_simple_markdown (self ,text :str ):
        """Simple markdown parser that handles basic formatting."""
        lines =text .split ('\n')
        in_code_block =False 
        code_lines =[]

        for line in lines :
            line =line .strip ()

            if not line and not in_code_block :

                continue 

            if line .startswith ('```'):
                if in_code_block :

                    code_text ='\n'.join (code_lines )
                    self .elements .append (MarkdownElement (code_text ,'code_block'))
                    code_lines =[]
                    in_code_block =False 
                else :
                    in_code_block =True 
                continue 

            if in_code_block :
                code_lines .append (line )
                continue 


            if line .startswith ('['):

                closing_bracket =line .find (']')
                if closing_bracket !=-1 :

                    block_text =line [1 :closing_bracket ].strip ()
                    block_type =self ._get_block_type (block_text )
                    if block_type :

                        element =MarkdownElement (block_text ,'block')
                        element .block_type =block_type 
                        self .elements .append (element )


                        remaining_text =line [closing_bracket +1 :].strip ()
                        if remaining_text :

                            remaining_text =remaining_text .lstrip ('.!?;,: ')
                            if remaining_text :

                                self ._parse_inline_formatting (remaining_text )
                        continue 


            if line .startswith ('####### '):

                self ._parse_inline_formatting (line )
            elif line .startswith ('###### '):
                heading_text =line [7 :]
                self .elements .append (MarkdownElement (heading_text ,'heading',6 ))
            elif line .startswith ('##### '):
                heading_text =line [6 :]
                self .elements .append (MarkdownElement (heading_text ,'heading',5 ))
            elif line .startswith ('#### '):
                heading_text =line [5 :]
                self .elements .append (MarkdownElement (heading_text ,'heading',4 ))
            elif line .startswith ('### '):
                heading_text =line [4 :]
                self .elements .append (MarkdownElement (heading_text ,'heading',3 ))
            elif line .startswith ('## '):
                heading_text =line [3 :]
                self .elements .append (MarkdownElement (heading_text ,'heading',2 ))
            elif line .startswith ('# '):
                heading_text =line [2 :]
                self .elements .append (MarkdownElement (heading_text ,'heading',1 ))


            elif line .startswith ('- ')or line .startswith ('* '):
                list_text =line 

                self ._parse_inline_formatting_for_element (list_text ,'list_item')
            elif line .startswith ('+ '):
                list_text =line 
                self ._parse_inline_formatting_for_element (list_text ,'list_item')
            elif len (line )>2 and line [0 ].isdigit ()and line [1 :3 ]=='. ':

                list_text =line 
                self ._parse_inline_formatting_for_element (list_text ,'list_item')

            else :

                self ._parse_inline_formatting (line )

    def _get_block_type (self ,block_text :str )->str :
        """Determine block type from text."""
        block_text_lower =block_text .lower ()


        if 'rendering scene'in block_text_lower or 'render captured'in block_text_lower :
            return 'render_capture'
        elif 'render failed'in block_text_lower or 'render error'in block_text_lower :
            return 'render_capture'


        if 'reading scene'in block_text_lower or 'scene read'in block_text_lower :
            return 'reading'
        elif 'analyzing scene'in block_text_lower or 'scene analyzed'in block_text_lower :
            return 'reading'
        elif 'querying'in block_text_lower or 'query'in block_text_lower :
            return 'reading'
        elif 'reading'in block_text_lower and ('properties'in block_text_lower or 'settings'in block_text_lower ):
            return 'reading'


        elif 'planning'in block_text_lower or 'analyzing'in block_text_lower :
            return 'planning'
        elif 'thinking'in block_text_lower or 'processing'in block_text_lower :
            return 'processing'


        elif 'writing code'in block_text_lower or 'coding'in block_text_lower :
            return 'coding'
        elif 'executing code'in block_text_lower or 'executing'in block_text_lower :
            return 'executing'
        elif 'code executed'in block_text_lower or 'execution'in block_text_lower :
            return 'executing'
        elif 'fixing code'in block_text_lower or 'fixing'in block_text_lower :
            return 'fixing'
        elif 'debugging'in block_text_lower or 'debug'in block_text_lower :
            return 'fixing'
        elif 'executed'in block_text_lower or 'complete'in block_text_lower or 'done'in block_text_lower :
            return 'coding'


        elif 'searching web'in block_text_lower or 'web search'in block_text_lower :
            return 'web_search'
        elif 'searching'in block_text_lower and ('internet'in block_text_lower or 'online'in block_text_lower ):
            return 'web_search'
        elif 'finding information'in block_text_lower or 'looking up'in block_text_lower :
            return 'web_search'
        elif 'found'in block_text_lower and 'results'in block_text_lower :
            return 'web_search'


        elif 'capturing viewport'in block_text_lower or 'viewport capturing'in block_text_lower :
            return 'viewport_capture'
        elif 'capturing render'in block_text_lower or 'render capturing'in block_text_lower :
            return 'render_capture'
        elif 'viewport captured'in block_text_lower or 'viewport capture'in block_text_lower :
            return 'viewport_capture'
        elif 'render captured'in block_text_lower or 'render capture'in block_text_lower :
            return 'render_capture'


        elif 'analyzing image'in block_text_lower or 'image analysis'in block_text_lower :
            return 'image'
        elif 'processing image'in block_text_lower or 'image processing'in block_text_lower :
            return 'image'
        elif 'reading image'in block_text_lower or 'image read'in block_text_lower :
            return 'image'


        elif 'writing'in block_text_lower and 'code'not in block_text_lower :
            return 'write'
        elif 'generating text'in block_text_lower or 'text generation'in block_text_lower :
            return 'write'


        elif 'searching'in block_text_lower and 'web'not in block_text_lower :
            return 'search'
        elif 'finding'in block_text_lower or 'locating'in block_text_lower :
            return 'search'


        elif 'using tool'in block_text_lower or 'tool'in block_text_lower :
            return 'tool'
        elif 'analyzing data'in block_text_lower or 'processing data'in block_text_lower :
            return 'processing'


        elif 'modifying scene'in block_text_lower or 'updating scene'in block_text_lower :
            return 'scene'
        elif 'creating objects'in block_text_lower or 'adding objects'in block_text_lower :
            return 'scene'
        elif 'scene'in block_text_lower and ('modified'in block_text_lower or 'updated'in block_text_lower ):
            return 'scene'

        return None 

    def _parse_inline_formatting_for_element (self ,text :str ,base_element_type :str ):
        """Parse inline formatting within a specific element type (like list_item)."""
        if not text :
            if base_element_type =='list_item':
                self .elements .append (MarkdownElement ("",'list_item'))
            return 

        parts =self ._extract_formatting_parts (text )


        element =MarkdownElement (text ,base_element_type )
        element .set_formatted_parts (parts )
        self .elements .append (element )

    def _parse_inline_formatting (self ,text :str ):
        """Parse inline formatting like bold, italic, and code spans."""
        if not text :
            return 

        parts =self ._extract_formatting_parts (text )


        element =MarkdownElement (text ,'text')
        element .set_formatted_parts (parts )
        self .elements .append (element )

    def _extract_formatting_parts (self ,text :str ):
        """Extract formatting parts from text, handling nested and mixed formatting."""
        parts =[]
        current_text =""
        i =0 

        while i <len (text ):
            char =text [i ]


            if char =='`':

                if current_text :
                    parts .append ((current_text ,'text'))
                    current_text =""


                i +=1 
                code_text =""
                found_closing =False 

                while i <len (text ):
                    if text [i ]=='`':
                        parts .append ((code_text ,'code'))
                        i +=1 
                        found_closing =True 
                        break 
                    else :
                        code_text +=text [i ]
                        i +=1 

                if not found_closing :

                    current_text +='`'+code_text 


            elif char =='*'and i +1 <len (text )and text [i +1 ]=='*':

                if current_text :
                    parts .append ((current_text ,'text'))
                    current_text =""


                i +=2 
                bold_text =""
                found_closing =False 

                while i +1 <len (text ):
                    if text [i ]=='*'and text [i +1 ]=='*':
                        parts .append ((bold_text ,'bold'))
                        i +=2 
                        found_closing =True 
                        break 
                    else :
                        bold_text +=text [i ]
                        i +=1 

                if not found_closing :

                    current_text +='**'+bold_text 


            elif char =='*'and not (i >0 and text [i -1 ]=='*')and not (i +1 <len (text )and text [i +1 ]=='*'):

                if current_text :
                    parts .append ((current_text ,'text'))
                    current_text =""


                i +=1 
                italic_text =""
                found_closing =False 

                while i <len (text ):
                    if text [i ]=='*'and not (i +1 <len (text )and text [i +1 ]=='*'):
                        parts .append ((italic_text ,'italic'))
                        i +=1 
                        found_closing =True 
                        break 
                    else :
                        italic_text +=text [i ]
                        i +=1 

                if not found_closing :
                    current_text +='*'+italic_text 

            else :
                current_text +=char 
                i +=1 


        if current_text :
            parts .append ((current_text ,'text'))

        return parts 



class MarkdownMessageComponent (UIComponent ):
    """Component for displaying AI messages with markdown formatting."""

    def __init__ (self ,markdown_text :str ,x :int =0 ,y :int =0 ,width :int =400 ,height :int =40 ):
        super ().__init__ (x ,y ,width ,height )

        self .markdown_text =markdown_text 
        self .corner_radius =MarkdownLayout .CORNER_RADIUS ()
        self .padding =0 
        self .padding_vertical =0 


        self .renderer =SimpleMarkdownRenderer ()
        self .elements =[]


        self ._cached_wrapped_elements =None 
        self ._cached_width =None 
        self ._cached_markdown =None 


        self ._text_dimension_cache ={}


        self .apply_themed_style ("message")


        self ._parse_markdown ()

        logger .debug (f"MarkdownMessageComponent created with {len(self.elements)} elements")

    def apply_themed_style (self ,style_type :str ="message"):
        """Apply themed style to the message component."""
        try :
            from ..colors import Colors 
            from ..theme import get_themed_style 

            self .style =get_themed_style ("button")
            self .style .background_color =(0.0 ,0.0 ,0.0 ,0.0 )
            self .style .border_color =Colors .Selected 
            self .style .border_width =0 
            self .style .text_color =Colors .Text 
            self .style .font_size =FontSizes .Default 

        except Exception as e :
            logger .warning (f"Could not apply themed style: {e}")
            from ..colors import Colors 
            self .style .background_color =(0.0 ,0.0 ,0.0 ,0.0 )
            self .style .border_color =Colors .Selected 
            self .style .border_width =0 
            self .style .text_color =Colors .Text 
            self .style .font_size =FontSizes .Default 

    def set_markdown (self ,markdown_text :str ):
        """Update the markdown text and reparse."""
        if self .markdown_text !=markdown_text :

            old_width =self .bounds .width 

            self .markdown_text =markdown_text 
            self ._parse_markdown ()
            self ._update_animation_states ()
            self ._invalidate_text_cache ()


            max_width =800 
            required_width ,_ =self .calculate_required_size (max_width )
            if required_width !=old_width :
                self .set_size (required_width ,self .bounds .height )

    def _update_animation_states (self ):
        """Update animation states for elements based on current content."""
        try :
            for element in self .elements :
                if element .element_type =='block':

                    if element ._is_in_progress_block ():
                        if not element .is_animated :
                            element .start_animation ()
                            logger .debug (f"Started animation for tool block: {element.text}")
                    else :
                        if element .is_animated :
                            element .stop_animation ()
                            logger .debug (f"Stopped animation for completed tool block: {element.text}")
        except Exception as e :
            logger .error (f"Error updating animation states: {e}")

    def get_message (self )->str :
        """Get the current markdown text."""
        return self .markdown_text 

    def _parse_markdown (self ):
        """Parse markdown text into formatted elements."""
        self .elements =self .renderer .parse_markdown (self .markdown_text )


        for element in self .elements :
            element .apply_formatting (self .style .font_size ,self .style .text_color )

    def _invalidate_text_cache (self ):
        """Invalidate text dimension cache when needed."""
        self ._text_dimension_cache .clear ()
        self ._invalidate_cache ()

    def _get_text_height_blf (self ,text :str ,font_size :int )->int :
        """Get actual text height using BLF measurements with caching.
        
        NOTE: This method is kept for compatibility and width measurements,
        but should NOT be used for line height calculations as BLF measurements
        can be inconsistent and cause line height instability.
        Use _get_consistent_line_height() for line height calculations instead.
        """
        cache_key =(text ,font_size )
        if cache_key not in self ._text_dimension_cache :
            try :
                blf .size (0 ,font_size )
                dimensions =blf .dimensions (0 ,text )

                self ._text_dimension_cache [cache_key ]=dimensions [1 ]if len (dimensions )>1 else font_size 
            except Exception as e :
                logger .warning (f"Error measuring text height for '{text[:20]}...': {e}")

                self ._text_dimension_cache [cache_key ]=font_size 

        return self ._text_dimension_cache [cache_key ]

    def _get_fs_for_type (self ,typ :str ,base_fs :int )->int :
        """Get font size for a formatting type."""
        if typ =='bold':
            return int (base_fs *MarkdownLayout .BOLD_FONT_SIZE_MULTIPLIER )
        elif typ =='code':
            return int (base_fs *MarkdownLayout .CODE_FONT_SIZE_MULTIPLIER )
        else :
            return base_fs 

    def _calculate_line_height (self ,element )->int :
        """Calculate proper line height for an element using consistent font-size-based approach."""
        if element .element_type =='block':

            return MarkdownLayout .BLOCK_HEIGHT ()



        if element .formatted_parts :

            max_font_size =element .font_size 
            for part_text ,part_type in element .formatted_parts :
                fs =self ._get_fs_for_type (part_type ,element .font_size )
                max_font_size =max (max_font_size ,fs )
            return _get_consistent_line_height (max_font_size )
        else :

            return _get_consistent_line_height (element .font_size )

    def _invalidate_cache (self ):
        """Invalidate the wrapping cache."""
        self ._cached_wrapped_elements =None 
        self ._cached_width =None 
        self ._cached_markdown =None 

    def _get_wrapped_elements (self ,available_width :int )->List [tuple ]:
        """Get wrapped elements with caching."""
        if (self ._cached_wrapped_elements is not None and 
        self ._cached_width ==available_width and 
        self ._cached_markdown ==self .markdown_text ):
            return self ._cached_wrapped_elements 


        wrapped_elements =[]

        for element in self .elements :
            if element .element_type =='block':

                wrapped_elements .append ((element .text ,element ))
            elif element .element_type =='code_block':

                code_lines =element .text .split ('\n')
                for code_line in code_lines :

                    wrapped_code =wrap_text_blf (code_line ,available_width ,element .font_size )
                    for wline in wrapped_code :
                        if wline .strip ():
                            code_element =MarkdownElement (wline ,'code')
                            code_element .apply_formatting (self .style .font_size ,self .style .text_color )
                            wrapped_elements .append ((wline ,code_element ))
            elif element .text .strip ():

                if element .formatted_parts :
                    wrapped_with_formatting =self ._wrap_formatted_text (element ,available_width )
                    wrapped_elements .extend (wrapped_with_formatting )
                else :

                    wrapped_lines =wrap_text_blf (element .text ,available_width ,element .font_size )
                    for line in wrapped_lines :
                        if line .strip ():
                            wrapped_elements .append ((line ,element ))


        self ._cached_wrapped_elements =wrapped_elements 
        self ._cached_width =available_width 
        self ._cached_markdown =self .markdown_text 

        return wrapped_elements 

    def _wrap_formatted_text (self ,element ,available_width :int )->List [tuple ]:
        """Wrap text with mixed formatting while preserving formatting for each line."""

        formatted_spans =[]
        for p_text ,p_type in element .formatted_parts :
            fs =self ._get_fs_for_type (p_type ,element .font_size )
            color =(0.8 ,1.0 ,0.8 ,1.0 )if p_type in ['bold','code']else element .color 
            formatted_spans .append ({'text':p_text ,'type':p_type ,'fs':fs ,'color':color })


        mini_spans =[]
        for span in formatted_spans :
            words =span ['text'].split (' ')
            for ii ,word in enumerate (words ):
                if ii >0 :

                    space_mini ={'text':' ','type':span ['type'],'fs':span ['fs'],'color':span ['color']}
                    mini_spans .append (space_mini )
                if word :
                    word_mini ={'text':word ,'type':span ['type'],'fs':span ['fs'],'color':span ['color']}
                    mini_spans .append (word_mini )


        lines =[]
        current_line =[]
        current_width =0 
        for mini in mini_spans :
            w =self ._measure_text_width (mini ['text'],mini ['fs'])
            if current_width +w >available_width and current_line :
                lines .append (current_line )
                current_line =[]
                current_width =0 


                if mini ['text']==' ':
                    continue 

            current_line .append (mini )
            current_width +=w 
        if current_line :
            lines .append (current_line )


        result =[]
        for line_spans in lines :
            merged_parts =[]
            current_part =None 
            for mini in line_spans :
                if current_part and current_part ['type']==mini ['type']and current_part ['fs']==mini ['fs']and current_part ['color']==mini ['color']:
                    current_part ['text']+=mini ['text']
                else :
                    if current_part :
                        merged_parts .append (current_part )
                    current_part =mini .copy ()
            if current_part :
                merged_parts .append (current_part )


            line_text =''.join (p ['text']for p in merged_parts )
            if not line_text .strip ():
                continue 
            line_parts =[(p ['text'],p ['type'])for p in merged_parts ]


            line_element =MarkdownElement (line_text ,element .element_type ,element .level )
            line_element .set_formatted_parts (line_parts )
            line_element .color =element .color 
            line_element .font_size =element .font_size 

            result .append ((line_text ,line_element ))

        return result 

    def _measure_text_width (self ,text :str ,font_size :int )->float :
        """Measure text width using BLF."""
        blf .size (0 ,font_size )
        return blf .dimensions (0 ,text )[0 ]

    def calculate_required_size (self ,max_width :int )->tuple [int ,int ]:
        """Calculate required size for the markdown content."""
        if not self .elements :
            return (MarkdownLayout .MIN_COMPONENT_WIDTH (),MarkdownLayout .MIN_COMPONENT_HEIGHT ())

        border_and_padding =(self .padding *2 )+(self .style .border_width *2 )
        available_width =max_width -border_and_padding 

        wrapped_elements =self ._get_wrapped_elements (available_width )


        max_line_width =0 
        total_height =0 
        first_block =True 

        try :
            for line_text ,element in wrapped_elements :
                if element .element_type =='block':

                    icon_size =MarkdownLayout .BLOCK_ICON_SIZE ()
                    padding =MarkdownLayout .BLOCK_PADDING ()
                    text_padding =MarkdownLayout .BLOCK_TEXT_PADDING ()


                    blf .size (0 ,element .font_size )


                    try :
                        text_dimensions =blf .dimensions (0 ,element .text )
                        text_width =text_dimensions [0 ]if text_dimensions else len (element .text )*(element .font_size *MarkdownLayout .TEXT_ESTIMATION_FACTOR )
                    except :
                        text_width =len (element .text )*(element .font_size *MarkdownLayout .TEXT_ESTIMATION_FACTOR )


                    content_width =padding +icon_size +text_padding +text_width +padding 
                    block_width =min (max (content_width ,MarkdownLayout .BLOCK_MIN_WIDTH ()),available_width )


                    block_height =MarkdownLayout .BLOCK_HEIGHT ()


                    if first_block :
                        total_height +=block_height 
                        first_block =False 
                    else :
                        total_height +=block_height +MarkdownLayout .BLOCK_MARGIN ()

                    max_line_width =max (max_line_width ,block_width )
                else :

                    if element .formatted_parts :
                        line_width =0 
                        for p_text ,p_type in element .formatted_parts :
                            fs =self ._get_fs_for_type (p_type ,element .font_size )
                            blf .size (0 ,fs )
                            line_width +=blf .dimensions (0 ,p_text )[0 ]
                    else :
                        blf .size (0 ,element .font_size )
                        line_width =blf .dimensions (0 ,line_text )[0 ]

                    max_line_width =max (max_line_width ,line_width )


                    line_height =self ._calculate_line_height (element )
                    total_height +=line_height 
                    first_block =False 

        except Exception as e :
            logger .error (f"Error calculating markdown size: {e}")

            estimated_lines =len (wrapped_elements )
            base_font_size =self .style .font_size 
            estimated_line_height =_get_consistent_line_height (base_font_size )
            total_height =estimated_lines *estimated_line_height 
            max_line_width =available_width 

        content_width =min (max_line_width +border_and_padding ,max_width )
        content_height =total_height +(self .padding_vertical *2 )+(self .style .border_width *2 )

        return (max (MarkdownLayout .MIN_COMPONENT_WIDTH (),content_width ),max (MarkdownLayout .MIN_COMPONENT_HEIGHT (),content_height ))

    def set_size (self ,width :int ,height :int ):
        """Override set_size to invalidate cache when size changes."""
        old_width =self .bounds .width 
        super ().set_size (width ,height )
        if old_width !=width :
            self ._invalidate_text_cache ()

    def render (self ,renderer :'UIRenderer'):
        """Render the markdown message component."""
        if not self .visible :
            return 


        if not self .elements :

            renderer .draw_rounded_rect (self .bounds ,self .style .background_color ,self .corner_radius )
            return 


        renderer .draw_rounded_rect (self .bounds ,self .style .background_color ,self .corner_radius )


        if self .style .border_width >0 :
            renderer .draw_rounded_rect_outline (
            self .bounds ,
            self .style .border_color ,
            self .style .border_width ,
            self .corner_radius 
            )


        text_x =self .bounds .x +self .padding +self .style .border_width 
        text_y =self .bounds .y +self .padding_vertical +self .style .border_width +CoordinateSystem .scale_int (2 )
        text_width =self .bounds .width -(self .padding *2 )-(self .style .border_width *2 )
        text_height =self .bounds .height -(self .padding_vertical *2 )-(self .style .border_width *2 )


        self ._render_markdown_text (renderer ,text_x ,text_y ,text_width ,text_height )

    def _render_markdown_text (self ,renderer :'UIRenderer',x :int ,y :int ,width :int ,height :int ):
        """Render the formatted markdown text."""
        wrapped_elements =self ._get_wrapped_elements (width )

        current_y =y +height 
        first_block =True 

        for line_text ,element in wrapped_elements :
            if element .element_type =='block':

                block_height =MarkdownLayout .BLOCK_HEIGHT ()


                if first_block :
                    current_y -=block_height 
                    first_block =False 
                else :
                    current_y -=block_height +MarkdownLayout .BLOCK_MARGIN ()

                if current_y >=y :
                    self ._render_special_block (renderer ,element ,x ,current_y ,width ,block_height )
            else :

                line_height =self ._calculate_line_height (element )
                current_y -=line_height 
                first_block =False 

                if current_y >=y :

                    if element .formatted_parts :
                        self ._render_mixed_formatting_line (renderer ,line_text ,element ,x ,current_y )
                    else :

                        blf .size (0 ,element .font_size )
                        renderer .draw_text (
                        line_text ,
                        x ,
                        current_y ,
                        element .font_size ,
                        element .color 
                        )


            if current_y <y :
                break 

    def _render_special_block (self ,renderer :'UIRenderer',element ,x :int ,y :int ,width :int ,height :int ):
        """Render a special block with icon and background."""
        from ..types import Bounds 


        icon_size =MarkdownLayout .BLOCK_ICON_SIZE ()
        padding =MarkdownLayout .BLOCK_PADDING ()
        text_padding =MarkdownLayout .BLOCK_TEXT_PADDING ()


        blf .size (0 ,element .font_size )


        try :
            text_dimensions =blf .dimensions (0 ,element .text )
            text_width =text_dimensions [0 ]if text_dimensions else len (element .text )*(element .font_size *MarkdownLayout .TEXT_ESTIMATION_FACTOR )
        except :
            text_width =len (element .text )*(element .font_size *MarkdownLayout .TEXT_ESTIMATION_FACTOR )


        content_width =padding +icon_size +text_padding +text_width +padding +CoordinateSystem .scale_int (8 )


        block_width =min (max (content_width ,MarkdownLayout .BLOCK_MIN_WIDTH ()),width )

        block_x =x 


        block_bounds =Bounds (block_x ,y ,block_width ,height )


        from ..colors import Colors 

        block_bg_color =Colors .lighten_color (Colors .Panel ,5 )


        renderer .draw_rounded_rect (block_bounds ,block_bg_color ,MarkdownLayout .BLOCK_CORNER_RADIUS ())


        if element .is_animated :
            self ._render_animated_gradient (renderer ,block_bounds ,element .get_animation_progress ())


        icon_map ={
        'reading':'scene',
        'planning':'brain',
        'coding':'code',
        'executing':'code',
        'fixing':'bug',
        'web_search':'globe',
        'tool':'settings',
        'processing':'brain',
        'scene':'scene',
        'image':'image',
        'write':'pen',
        'search':'search',
        'viewport_capture':'image',
        'render_capture':'image',
        }
        icon_name =icon_map .get (element .block_type )

        text_start_x =block_x +padding 
        icon_texture =None 

        if icon_name :

            block_icon_manager .get_icon_component (icon_name )


            icon_texture =block_icon_manager .get_block_icon_texture (element .block_type )

        if icon_texture :

            icon_x =text_start_x 
            icon_y =y +(height -icon_size )//2 

            try :
                renderer .draw_image (icon_texture ,icon_x ,icon_y ,icon_size ,icon_size )
                text_start_x +=icon_size +text_padding 
            except Exception as e :
                logger .warning (f"Could not render icon for block {element.block_type}: {e}")


        text_x =text_start_x 


        block_center_y =y +(height //2 )
        baseline_offset =element .font_size *FONT_BASELINE_OFFSET_RATIO 
        text_y =block_center_y -baseline_offset -CoordinateSystem .scale_int (2 )


        blf .size (0 ,element .font_size )
        renderer .draw_text (
        element .text ,
        text_x ,
        text_y ,
        element .font_size ,
        element .color 
        )

    def _render_animated_gradient (self ,renderer :'UIRenderer',block_bounds ,progress :float ):
        """Render an animated gradient overlay for in-progress tool blocks."""
        try :

            gradient_width =block_bounds .width *0.5 
            gradient_center_opacity =0.06 
            corner_radius =MarkdownLayout .BLOCK_CORNER_RADIUS ()


            def ease_in_out_sine (t ):
                """Smooth easing function for natural movement."""
                import math 
                return -(math .cos (math .pi *t )-1 )/2 


            eased_progress =ease_in_out_sine (progress )



            gradient_center_x =block_bounds .x +(block_bounds .width +gradient_width )*eased_progress -gradient_width /2 


            segments =25 


            for i in range (segments ):

                segment_start =gradient_center_x -gradient_width /2 +(i /segments )*gradient_width 
                segment_end =gradient_center_x -gradient_width /2 +((i +1 )/segments )*gradient_width 


                clipped_start =max (segment_start ,block_bounds .x )
                clipped_end =min (segment_end ,block_bounds .x +block_bounds .width )


                if clipped_start >=clipped_end :
                    continue 


                segment_center =(segment_start +segment_end )/2 
                distance_from_gradient_center =abs (segment_center -gradient_center_x )/(gradient_width /2 )


                import math 
                falloff_factor =math .cos (distance_from_gradient_center *math .pi /2 )
                falloff_factor =max (0.0 ,falloff_factor )


                falloff_factor =falloff_factor **1.5 

                opacity =gradient_center_opacity *falloff_factor 


                if opacity <0.005 :
                    continue 




                def create_curved_segment_vertices (segment_start_x ,segment_end_x ):
                    """Create vertices for a segment that follows the rounded corner curve."""
                    vertices =[]


                    left_corner_center_x =block_bounds .x +corner_radius 
                    left_corner_center_y =block_bounds .y +corner_radius 
                    right_corner_center_x =block_bounds .x +block_bounds .width -corner_radius 
                    right_corner_center_y =block_bounds .y +corner_radius 


                    sample_count =8 


                    bottom_vertices =[]
                    for k in range (sample_count ):

                        sample_x =segment_start_x +(k /(sample_count -1 ))*(segment_end_x -segment_start_x )


                        y_offset =0.0 


                        if sample_x <left_corner_center_x :
                            dx =left_corner_center_x -sample_x 
                            if dx <=corner_radius :

                                dy =corner_radius -(corner_radius **2 -dx **2 )**0.5 
                                y_offset =max (y_offset ,dy )


                        if sample_x >right_corner_center_x :
                            dx =sample_x -right_corner_center_x 
                            if dx <=corner_radius :

                                dy =corner_radius -(corner_radius **2 -dx **2 )**0.5 
                                y_offset =max (y_offset ,dy )


                        y_offset +=0.5 

                        bottom_y =block_bounds .y +y_offset 
                        bottom_vertices .append ((sample_x ,bottom_y ))


                    top_vertices =[]
                    for k in range (sample_count ):

                        sample_x =segment_start_x +(k /(sample_count -1 ))*(segment_end_x -segment_start_x )


                        y_offset =0.0 


                        if sample_x <left_corner_center_x :
                            dx =left_corner_center_x -sample_x 
                            if dx <=corner_radius :

                                dy =corner_radius -(corner_radius **2 -dx **2 )**0.5 
                                y_offset =max (y_offset ,dy )


                        if sample_x >right_corner_center_x :
                            dx =sample_x -right_corner_center_x 
                            if dx <=corner_radius :

                                dy =corner_radius -(corner_radius **2 -dx **2 )**0.5 
                                y_offset =max (y_offset ,dy )


                        y_offset +=0.5 

                        top_y =block_bounds .y +block_bounds .height -y_offset 
                        top_vertices .append ((sample_x ,top_y ))



                    vertices =bottom_vertices +list (reversed (top_vertices ))

                    return vertices 


                curved_vertices =create_curved_segment_vertices (clipped_start ,clipped_end )


                if len (curved_vertices )<3 :
                    continue 



                indices =[]
                center_vertex =len (curved_vertices )//2 


                for j in range (len (curved_vertices )-1 ):
                    indices .append ((center_vertex ,j ,j +1 ))

                indices .append ((center_vertex ,len (curved_vertices )-1 ,0 ))


                batch =batch_for_shader (
                renderer .shader ,
                'TRIS',
                {"pos":curved_vertices },
                indices =indices 
                )


                gpu .state .blend_set ('ALPHA')


                renderer .shader .bind ()
                renderer .shader .uniform_float ("color",(1.0 ,1.0 ,1.0 ,opacity ))


                batch .draw (renderer .shader )


                gpu .state .blend_set ('NONE')

        except Exception as e :
            logger .warning (f"Could not render animated gradient: {e}")

    def _render_mixed_formatting_line (self ,renderer :'UIRenderer',line_text :str ,element ,x :int ,y :int ):
        """Render a line with mixed formatting (bold, italic, code within same line)."""
        current_x =x 

        for part_text ,part_type in element .formatted_parts :
            if not part_text :
                continue 


            if part_type =='bold':
                color =(0.8 ,1.0 ,0.8 ,1.0 )
                font_size =self ._get_fs_for_type ('bold',element .font_size )

            elif part_type =='italic':
                color =element .color 
                font_size =element .font_size 

            elif part_type =='code':
                color =(0.8 ,1.0 ,0.8 ,1.0 )
                font_size =self ._get_fs_for_type ('code',element .font_size )
            else :
                color =element .color 
                font_size =element .font_size 


            blf .size (0 ,font_size )
            renderer .draw_text (
            part_text ,
            current_x ,
            y ,
            font_size ,
            color 
            )


            try :
                text_width =blf .dimensions (0 ,part_text )[0 ]
                current_x +=text_width 
            except :

                current_x +=len (part_text )*(font_size *MarkdownLayout .TEXT_ESTIMATION_FACTOR )

    def auto_resize_to_content (self ,max_width :int ):
        """Auto-resize the component to fit the markdown content."""
        required_width ,required_height =self .calculate_required_size (max_width )
        self .set_size (required_width ,required_height )