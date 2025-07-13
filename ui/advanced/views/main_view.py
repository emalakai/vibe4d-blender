"""
Main view for the AI chat interface.
"""

import logging 
from typing import Dict ,Any 
import time 
import re 

from .base_view import BaseView 
from ..layout_manager import LayoutConfig ,LayoutStrategy ,LayoutConstraints ,FlexDirection ,JustifyContent ,AlignItems 
from ..components import Label ,TextInput ,Button 
from ..components .send_button import SendButton 
from ..components .dropdown import ModelDropdown 
from ..components .icon_button import IconButton 
from ..components .scrollview import ScrollView ,ScrollDirection 
from ..theme import get_themed_style 
from ..types import Bounds 
from ..unified_styles import Styles 
from ..coordinates import CoordinateSystem 

logger =logging .getLogger (__name__ )


class MainView (BaseView ):
    """Main view for the AI chat interface."""



    @property 
    def INPUT_AREA_HEIGHT (self ):
        return Styles .get_input_area_height ()

    @property 
    def HEADER_HEIGHT (self ):
        return Styles .get_header_height ()

    @property 
    def VIEWPORT_MARGIN (self ):
        return Styles .get_viewport_margin ()

    @property 
    def VIEWPORT_PADDING_SMALL (self ):
        return Styles .get_viewport_padding_small ()

    @property 
    def CONTAINER_PADDING (self ):
        return Styles .get_container_padding ()

    @property 
    def BUTTON_MARGIN (self ):
        return Styles .get_button_margin ()

    @property 
    def MIN_BUTTON_MARGIN (self ):
        return Styles .get_min_button_margin ()

    @property 
    def HEADER_GAP (self ):
        return Styles .get_header_gap ()

    @property 
    def BUTTON_GAP (self ):
        return Styles .get_button_gap ()

    @property 
    def MESSAGE_GAP (self ):
        return Styles .get_message_gap ()

    @property 
    def MESSAGE_PADDING (self ):
        return Styles .get_message_padding ()

    @property 
    def MESSAGE_AREA_PADDING (self ):
        return Styles .get_message_area_padding ()

    @property 
    def HEADER_VERTICAL_MARGIN (self ):
        return Styles .get_header_vertical_margin ()

    @property 
    def DROPDOWN_WIDTH (self ):
        return Styles .get_dropdown_width ()

    @property 
    def DROPDOWN_HEIGHT (self ):
        return Styles .get_dropdown_height ()

    @property 
    def DROPDOWN_CORNER_RADIUS (self ):
        return Styles .get_dropdown_corner_radius ()

    @property 
    def DROPDOWN_PADDING_HORIZONTAL (self ):
        return Styles .get_dropdown_padding_horizontal ()

    @property 
    def DROPDOWN_PADDING_VERTICAL (self ):
        return Styles .get_dropdown_padding_vertical ()

    @property 
    def DROPDOWN_ICON_GAP (self ):
        return Styles .get_dropdown_icon_gap ()

    @property 
    def HEADER_PADDING_HORIZONTAL (self ):
        return Styles .get_header_padding_horizontal ()

    @property 
    def HEADER_PADDING_VERTICAL (self ):
        return Styles .get_header_padding_vertical ()

    @property 
    def HEADER_ICON_BUTTON_SIZE (self ):
        return Styles .get_header_icon_button_size ()

    @property 
    def HEADER_ICON_BUTTON_CORNER_RADIUS (self ):
        return Styles .get_header_icon_button_corner_radius ()

    @property 
    def HEADER_ICON_BUTTON_SPACING (self ):
        return Styles .get_header_icon_button_spacing ()

    @property 
    def HEADER_ICON_SIZE (self ):
        return Styles .get_header_icon_size ()

    @property 
    def SEND_BUTTON_SIZE (self ):
        return Styles .get_send_button_size ()

    @property 
    def SEND_BUTTON_CORNER_RADIUS (self ):
        return Styles .get_send_button_corner_radius ()

    @property 
    def SEND_BUTTON_ICON_SIZE (self ):
        return Styles .get_send_button_icon_size ()

    @property 
    def SEND_BUTTON_SPACING (self ):
        return Styles .get_send_button_spacing ()

    @property 
    def TEXT_INPUT_MARGIN (self ):
        return Styles .get_text_input_margin ()

    @property 
    def TEXT_INPUT_MAX_HEIGHT (self ):
        return Styles .get_text_input_max_height ()

    @property 
    def MIN_MESSAGE_HEIGHT (self ):
        return Styles .get_min_message_height ()

    @property 
    def SCROLLBAR_BUFFER (self ):
        return Styles .get_scrollbar_buffer ()

    @property 
    def BUTTON_CORNER_RADIUS (self ):
        return Styles .get_button_corner_radius ()

    @property 
    def TEXT_INPUT_CORNER_RADIUS (self ):
        return Styles .get_text_input_corner_radius ()

    @property 
    def TEXT_INPUT_PADDING (self ):
        return Styles .get_text_input_padding ()

    @property 
    def TEXT_INPUT_BORDER_WIDTH (self ):
        return Styles .get_text_input_border_width ()

    @property 
    def TEXT_INPUT_CONTENT_PADDING_LEFT (self ):
        return Styles .get_text_input_content_padding_left ()

    @property 
    def TEXT_INPUT_CONTENT_PADDING_RIGHT_OFFSET (self ):
        return Styles .get_text_input_content_padding_right_offset ()

    @property 
    def MESSAGE_BORDER_WIDTH (self ):
        return Styles .get_message_border_width ()

    @property 
    def MESSAGE_AREA_SPACING (self ):
        return CoordinateSystem .scale_int (20 )

    @property 
    def BUTTON_CONTAINER_HEIGHT (self ):
        return Styles .get_button_container_height ()

    @property 
    def BUTTON_CONTAINER_WIDTH_ESTIMATE (self ):
        return Styles .get_button_container_width_estimate ()

    def create_layout (self ,viewport_width :int ,viewport_height :int )->Dict [str ,Any ]:
        """Create the main UI layout with automated positioning."""


        layouts =self ._setup_layouts (viewport_width ,viewport_height )


        components =self ._create_components ()


        self ._setup_unfocus_handlers (components )


        self ._organize_components (layouts ,components )


        self .components =components 
        self .layouts =layouts 


        self ._update_all_layouts (viewport_width ,viewport_height ,components )


        self ._load_existing_chat_history ()


        self ._setup_text_input_change_handler ()

        return {
        'layouts':layouts ,
        'components':components ,
        'all_components':self ._get_all_components ()
        }

    def update_layout (self ,viewport_width :int ,viewport_height :int ):
        """Update layout positions when viewport changes."""
        if self .components :
            self ._update_all_layouts (viewport_width ,viewport_height ,self .components )

    def get_focused_component (self ):
        """Get the component that should be focused by default."""
        return self .components .get ('text_input')

    def get_send_text (self )->str :
        """Get text from the text input component."""
        text_input =self .components .get ('text_input')
        if text_input and hasattr (text_input ,'get_text'):
            return text_input .get_text ().strip ()
        return ""

    def clear_send_text (self ):
        """Clear text from the text input component."""
        text_input =self .components .get ('text_input')
        if text_input and hasattr (text_input ,'set_text'):
            text_input .set_text ("")

    def get_message_scrollview (self ):
        """Get the message scrollview component."""
        return self .components .get ('message_scrollview')

    def _setup_layouts (self ,viewport_width :int ,viewport_height :int )->Dict [str ,str ]:
        """Set up layout containers."""
        layouts ={}


        main_layout =self ._create_layout_container (
        "main",
        LayoutConfig (
        strategy =LayoutStrategy .ABSOLUTE ,
        padding_top =0 ,
        padding_right =0 ,
        padding_bottom =0 ,
        padding_left =0 
        )
        )
        layouts ['main']=main_layout 


        header_layout =self ._create_layout_container (
        "header",
        LayoutConfig (
        strategy =LayoutStrategy .FLEX_HORIZONTAL ,
        direction =FlexDirection .ROW ,
        justify_content =JustifyContent .SPACE_BETWEEN ,
        align_items =AlignItems .CENTER ,
        gap =self .HEADER_GAP ,
        padding_top =0 ,
        padding_right =0 ,
        padding_bottom =0 ,
        padding_left =0 
        )
        )
        layouts ['header']=header_layout 


        buttons_layout =self ._create_layout_container (
        "header_buttons",
        LayoutConfig (
        strategy =LayoutStrategy .FLEX_HORIZONTAL ,
        direction =FlexDirection .ROW ,
        justify_content =JustifyContent .END ,
        align_items =AlignItems .CENTER ,
        gap =self .BUTTON_GAP ,
        padding_top =0 ,
        padding_right =0 ,
        padding_bottom =0 ,
        padding_left =0 
        )
        )
        layouts ['header_buttons']=buttons_layout 


        message_layout =self ._create_layout_container (
        "message_area",
        LayoutConfig (
        strategy =LayoutStrategy .ABSOLUTE ,
        padding_top =0 ,
        padding_right =0 ,
        padding_bottom =0 ,
        padding_left =0 
        )
        )
        layouts ['message_area']=message_layout 


        input_layout =self ._create_layout_container (
        "input_area",
        LayoutConfig (
        strategy =LayoutStrategy .ABSOLUTE ,
        padding_top =0 ,
        padding_right =0 ,
        padding_bottom =0 ,
        padding_left =0 
        )
        )
        layouts ['input_area']=input_layout 

        return layouts 

    def _create_components (self )->Dict [str ,Any ]:
        """Create all UI components."""
        components ={}


        send_button_size =self .SEND_BUTTON_SIZE 
        send_button_corner_radius =self .SEND_BUTTON_CORNER_RADIUS 
        send_button_spacing =self .SEND_BUTTON_SPACING 


        model_options =["GPT 4.1","GPT 4.1 Mini","GPT 4.1 Nano"]
        model_dropdown =ModelDropdown (
        model_options ,
        0 ,0 ,self .DROPDOWN_WIDTH ,self .DROPDOWN_HEIGHT ,
        on_change =self .callbacks .get ('on_model_change')
        )


        try :
            import bpy 
            context =bpy .context 


            current_model =getattr (context .scene ,'vibe4d_model','gpt-4.1-mini')


            model_reverse_mapping ={
            "gpt-4.1":"GPT 4.1",
            "gpt-4.1-mini":"GPT 4.1 Mini",
            "gpt-4.1-nano":"GPT 4.1 Nano"
            }

            display_model =model_reverse_mapping .get (current_model ,"GPT 4.1 Mini")


            if display_model in model_options :
                model_dropdown .selected_index =model_options .index (display_model )
            else :
                model_dropdown .selected_index =1 

        except Exception as e :
            model_dropdown .selected_index =1 

        components ['model_dropdown']=model_dropdown 


        button_size =self .HEADER_ICON_BUTTON_SIZE 
        button_corner_radius =self .HEADER_ICON_BUTTON_CORNER_RADIUS 

        add_button =IconButton ("new",0 ,0 ,button_size ,button_size ,
        corner_radius =button_corner_radius ,on_click =self ._handle_add_click )
        history_button =IconButton ("history",0 ,0 ,button_size ,button_size ,
        corner_radius =button_corner_radius ,on_click =self ._handle_history_click )
        settings_button =IconButton ("settings",0 ,0 ,button_size ,button_size ,
        corner_radius =button_corner_radius ,on_click =self ._handle_settings_click )

        components ['add_button']=add_button 
        components ['history_button']=history_button 
        components ['settings_button']=settings_button 


        message_scrollview =ScrollView (0 ,0 ,600 ,400 ,reverse_y_coordinate =False )

        message_scrollview .style =get_themed_style ("input")
        message_scrollview .style .background_color =(0 ,0 ,0 ,0 )
        message_scrollview .style .border_color =(0 ,0 ,0 ,0 )
        message_scrollview .style .border_width =0 

        message_scrollview .scroll_direction =ScrollDirection .VERTICAL 
        message_scrollview .show_scrollbars =True 
        components ['message_scrollview']=message_scrollview 



        text_input_content_padding_right_offset =self .TEXT_INPUT_CONTENT_PADDING_RIGHT_OFFSET 
        text_input_content_padding_left =self .TEXT_INPUT_CONTENT_PADDING_LEFT 
        text_input_max_height =self .TEXT_INPUT_MAX_HEIGHT 
        text_input_corner_radius =self .TEXT_INPUT_CORNER_RADIUS 
        text_input_padding =self .TEXT_INPUT_PADDING 
        text_input_border_width =self .TEXT_INPUT_BORDER_WIDTH 

        text_input =TextInput (
        placeholder ="What would you like me to do?",
        multiline =True ,
        min_height =20 ,
        max_height =text_input_max_height ,
        corner_radius =text_input_corner_radius ,
        content_padding_right =send_button_size +(send_button_spacing *2 ),
        content_padding_left =text_input_content_padding_left 
        )
        text_input .style =get_themed_style ("input")
        text_input .style .padding =text_input_padding 
        text_input .style .border_width =text_input_border_width 

        text_input .on_submit =self .callbacks .get ('on_send')
        components ['text_input']=text_input 


        send_button =SendButton ("",0 ,0 ,send_button_size ,send_button_size ,
        corner_radius =send_button_corner_radius ,on_click =self .callbacks .get ('on_send'))
        components ['send_button']=send_button 

        return components 

    def _calculate_send_button_size (self )->int :
        """Calculate the send button size based on text input single-line height."""

        temp_text_input =TextInput (multiline =False ,height =CoordinateSystem .scale_int (33 ))
        temp_text_input .style =get_themed_style ("input")
        temp_text_input .style .padding =self .TEXT_INPUT_PADDING 
        temp_text_input .style .border_width =self .TEXT_INPUT_BORDER_WIDTH 


        LINE_HEIGHT_MULTIPLIER =1.21 


        line_height =int (temp_text_input .style .font_size *LINE_HEIGHT_MULTIPLIER )


        total_padding_vertical =(temp_text_input .style .padding *2 )+(temp_text_input .style .border_width *2 )


        single_line_height =line_height +total_padding_vertical 

        send_button_size =max (CoordinateSystem .scale_int (11 ),int (single_line_height ))


        if send_button_size %2 !=0 :
            send_button_size +=1 

        return send_button_size 

    def _organize_components (self ,layouts :Dict [str ,str ],components :Dict [str ,Any ]):
        """Organize components into their respective layouts."""


        self .layout_manager .add_component (layouts ['header'],components ['model_dropdown'])


        self .layout_manager .add_component (layouts ['header_buttons'],components ['add_button'])
        self .layout_manager .add_component (layouts ['header_buttons'],components ['history_button'])
        self .layout_manager .add_component (layouts ['header_buttons'],components ['settings_button'])


        self .layout_manager .add_component (
        layouts ['message_area'],
        components ['message_scrollview'],
        LayoutConstraints (
        left =0 ,
        right =0 ,
        top =0 ,
        bottom =0 
        )
        )


        self .layout_manager .add_component (
        layouts ['input_area'],
        components ['text_input'],
        LayoutConstraints (
        left =0 ,
        right =0 ,
        bottom =0 ,
        top =0 
        )
        )


        send_button =components ['send_button']
        send_button_spacing =self .SEND_BUTTON_SPACING 

        self .layout_manager .add_component (
        layouts ['input_area'],
        send_button ,
        LayoutConstraints (
        right =send_button_spacing ,
        bottom =send_button_spacing +CoordinateSystem .scale_int (2 )
        )
        )

    def _update_all_layouts (self ,viewport_width :int ,viewport_height :int ,components :Dict [str ,Any ]):
        """Update all layout positions."""


        message_scrollview =components .get ('message_scrollview')
        old_scrollview_width =message_scrollview .bounds .width if message_scrollview else 0 


        buttons_container_bounds =Bounds (0 ,0 ,self .BUTTON_CONTAINER_WIDTH_ESTIMATE ,self .BUTTON_CONTAINER_HEIGHT )
        self .layout_manager .update_layout (self .layouts ['header_buttons'],buttons_container_bounds )


        buttons_components =self .layout_manager .containers [self .layouts ['header_buttons']]
        if buttons_components :


            button_gap =self .BUTTON_GAP 
            total_width =sum (comp .bounds .width for comp in buttons_components )+(len (buttons_components )-1 )*button_gap 


            buttons_container_bounds =Bounds (0 ,0 ,total_width ,self .BUTTON_CONTAINER_HEIGHT )
            self .layout_manager .update_layout (self .layouts ['header_buttons'],buttons_container_bounds )


        main_bounds =Bounds (0 ,0 ,viewport_width ,viewport_height )
        self .layout_manager .update_layout (self .layouts ['main'],main_bounds )





        viewport_margin =self .VIEWPORT_MARGIN 
        header_height =self .HEADER_HEIGHT 
        header_y =viewport_height -header_height -viewport_margin 

        header_bounds =Bounds (
        viewport_margin ,
        header_y ,
        viewport_width -(viewport_margin *2 ),
        header_height 
        )



        header_padding_horizontal =self .HEADER_PADDING_HORIZONTAL 
        header_padding_vertical =self .HEADER_PADDING_VERTICAL 


        content_x =header_bounds .x +header_padding_horizontal 
        content_y =header_bounds .y +header_padding_vertical 
        content_width =header_bounds .width -(header_padding_horizontal *2 )
        content_height =header_bounds .height -(header_padding_vertical *2 )

        dropdown =components .get ('model_dropdown')
        if dropdown :

            dropdown .set_position (content_x ,content_y )


        if buttons_components :
            buttons_start_x =content_x +content_width -total_width 
            current_x =buttons_start_x 
            for comp in buttons_components :
                comp .set_position (current_x ,content_y )
                current_x +=comp .bounds .width +button_gap 



        input_area_height =self .INPUT_AREA_HEIGHT 
        text_input_margin =self .TEXT_INPUT_MARGIN 
        input_bounds =Bounds (
        viewport_margin +text_input_margin ,
        viewport_margin +text_input_margin ,
        viewport_width -(viewport_margin *2 )-(text_input_margin *2 ),
        input_area_height 
        )
        self .layout_manager .update_layout (self .layouts ['input_area'],input_bounds )


        message_area_spacing =self .MESSAGE_AREA_SPACING 
        message_y =input_bounds .y +input_bounds .height +message_area_spacing 

        header_vertical_margin =self .HEADER_VERTICAL_MARGIN 
        min_message_height =self .MIN_MESSAGE_HEIGHT 
        message_height =header_bounds .y -message_y -header_vertical_margin 

        message_bounds =Bounds (
        0 ,
        message_y ,
        viewport_width ,
        max (min_message_height ,message_height )
        )


        self .layout_manager .update_layout (self .layouts ['message_area'],message_bounds )


        if message_scrollview :
            new_scrollview_width =message_scrollview .bounds .width 
            new_scrollview_height =message_scrollview .bounds .height 


            is_empty_state =(len (message_scrollview .children )==1 and 
            hasattr (message_scrollview .children [0 ],'get_text')and 
            message_scrollview .children [0 ].get_text ()=="Ready when you are.")

            if is_empty_state :

                self ._update_empty_chat_message_position (message_scrollview )
            elif old_scrollview_width !=new_scrollview_width and message_scrollview .children :



                message_padding =self .MESSAGE_PADDING 

                max_width =new_scrollview_width -(message_padding *2 )
                if message_scrollview .show_scrollbars :
                    max_width -=message_scrollview .scrollbar_width 


                for child in message_scrollview .children :
                    if hasattr (child ,'auto_resize_to_content'):
                        child .auto_resize_to_content (max_width )


                message_padding =self .MESSAGE_PADDING 




                current_y =0 


                for i in range (len (message_scrollview .children )):
                    child =message_scrollview .children [i ]



                    is_ai_message =(hasattr (child ,'style')and 
                    getattr (child .style ,'border_width',0 )==0 )


                    if is_ai_message :

                        message_x =message_padding 
                    else :

                        message_x =new_scrollview_width -child .bounds .width -message_padding 


                    if i ==0 :

                        message_y =0 
                        current_y =child .bounds .height 
                    else :

                        message_y =current_y 


                    child .set_position (message_x ,message_y )


                    if i <len (message_scrollview .children )-1 :

                        next_child =message_scrollview .children [i +1 ]


                        current_is_ai =is_ai_message 
                        next_is_ai =(hasattr (next_child ,'style')and 
                        getattr (next_child .style ,'border_width',0 )==0 )


                        if current_is_ai ==next_is_ai :

                            message_gap =Styles .get_same_role_message_gap ()
                        else :

                            message_gap =Styles .get_different_role_message_gap ()

                        if i >0 :
                            current_y +=child .bounds .height +message_gap 
                    else :

                        if i >0 :
                            current_y +=child .bounds .height 


                message_scrollview ._update_content_bounds ()


                if hasattr (message_scrollview ,'invalidate'):
                    message_scrollview .invalidate ()


                try :
                    import bpy 
                    if hasattr (bpy .context ,'area')and bpy .context .area :
                        bpy .context .area .tag_redraw ()
                except :
                    pass 


            for child in message_scrollview .children :
                if hasattr (child ,'update_layout'):
                    child .update_layout ()

                if hasattr (child ,'invalidate'):
                    child .invalidate ()

    def _handle_add_click (self ):
        """Handle add button click - start a new chat session."""
        logger .info ("Add button clicked - starting new chat session")


        if self .callbacks .get ('on_stop_generation'):
            self .callbacks ['on_stop_generation']()
            logger .info ("Stopped ongoing generation via callback")


        if 'message_scrollview'in self .components :
            message_scrollview =self .components ['message_scrollview']
            message_scrollview .children .clear ()
            message_scrollview ._update_content_bounds ()

            self ._show_empty_chat_message (message_scrollview )
            logger .info ("Cleared message scrollview UI and showed empty state")


        try :
            import bpy 
            context =bpy .context 


            from ....utils .history_manager import history_manager 
            new_chat_id =history_manager .create_new_chat (context )

            logger .info (f"✅ Started new chat: {new_chat_id}")

        except Exception as e :
            logger .error (f"Failed to start new chat: {str(e)}")


        if self .callbacks .get ('on_add'):
            self .callbacks ['on_add']()

        logger .info ("Ready for new chat session")

    def _handle_history_click (self ):
        """Handle history button click - switch to history view."""
        if self .callbacks .get ('on_view_change'):
            from ..ui_factory import ViewState 
            self .callbacks ['on_view_change'](ViewState .HISTORY )


        if self .callbacks .get ('on_history'):
            self .callbacks ['on_history']()

    def _handle_settings_click (self ):
        """Handle settings button click - switch to settings view."""
        if self .callbacks .get ('on_view_change'):
            from ..ui_factory import ViewState 
            self .callbacks ['on_view_change'](ViewState .SETTINGS )


        if self .callbacks .get ('on_settings'):
            self .callbacks ['on_settings']()

    def _setup_unfocus_handlers (self ,components :Dict [str ,Any ]):
        """Set up click handlers to unfocus text input for components that don't have specific handlers."""

        def create_unfocus_click_handler ():
            """Create a generic unfocus handler that removes focus from text input."""
            def handle_unfocus_click ():
                text_input =components .get ('text_input')
                if text_input and hasattr (text_input ,'ui_state')and text_input .ui_state :
                    text_input .ui_state .set_focus (None )
            return handle_unfocus_click 


        message_scrollview =components .get ('message_scrollview')
        if message_scrollview :

            original_handle_event =message_scrollview .handle_event 

            def scrollview_handle_event (event ):
                try :

                    handled =original_handle_event (event )
                    if handled :
                        return True 


                    from ..types import EventType 
                    if (event .event_type ==EventType .MOUSE_PRESS and 
                    message_scrollview .bounds .contains_point (event .mouse_x ,event .mouse_y )):

                        logger .info (f"ScrollView unfocus handler triggered: mouse at ({event.mouse_x}, {event.mouse_y})")
                        text_input =components .get ('text_input')
                        if text_input and hasattr (text_input ,'ui_state')and text_input .ui_state :
                            logger .info ("Unfocusing text input via ScrollView click")
                            text_input .ui_state .set_focus (None )
                        return True 

                    return False 
                except Exception as e :
                    logger .error (f"Error in scrollview handle_event handler: {e}")
                    return False 

            message_scrollview .handle_event =scrollview_handle_event 

    def _convert_tool_message_to_block_format (self ,content :str )->str :
        """Convert a simplified tool response message back to block format for proper rendering."""
        try :
            original_content =content 
            content_lower =content .lower ().strip ()


            if not content .strip ()or content .strip ()in ['{}','{"status": "success"}','null','None']:
                return "[Tool completed]"


            try :
                import json 
                parsed_json =json .loads (content )
                if isinstance (parsed_json ,dict ):

                    status =parsed_json .get ('status','')
                    result =parsed_json .get ('result','')

                    if status =='success':
                        if isinstance (result ,str )and result .strip ():

                            content_lower =result .lower ().strip ()
                        else :
                            return "[Tool completed]"
                    elif status =='error':
                        if isinstance (result ,str )and result .strip ():

                            content_lower =result .lower ().strip ()
                        else :
                            return "[Tool failed]"
                    else :

                        if isinstance (result ,str )and result .strip ():
                            content_lower =result .lower ().strip ()
                        else :
                            return "[Tool completed]"
            except (json .JSONDecodeError ,TypeError ):

                pass 



            found_pattern =re .search (r'found\s+(\d+)\s+results?',content_lower )
            if found_pattern :
                result_count =found_pattern .group (1 )
                logger .debug (f"🔍 Web search pattern matched: 'found {result_count} results' -> '[Found results]'")
                return "[Found results]"


            results_pattern =re .search (r'(\d+)\s+results?\s+found',content_lower )
            if results_pattern :
                result_count =results_pattern .group (1 )
                logger .debug (f"🔍 Web search pattern matched: '{result_count} results found' -> '[Found results]'")
                return "[Found results]"


            tool_message_mapping ={

            "code executed successfully":"[Code executed]",
            "code execution completed":"[Code executed]",
            "code executed":"[Code executed]",
            "execution completed":"[Code executed]",
            "code execution failed":"[Code execution failed]",
            "execution failed":"[Code execution failed]",


            "scene read successfully":"[Scene read]",
            "scene data retrieved":"[Scene read]",
            "scene analyzed":"[Scene analyzed]",
            "scene reading failed":"[Scene reading failed]",
            "scene analysis failed":"[Scene analysis failed]",
            "query executed successfully":"[Scene read]",
            "query completed":"[Scene read]",
            "query failed":"[Scene reading failed]",


            "scene context retrieved":"[Scene analyzed]",
            "scene context completed":"[Scene analyzed]",
            "scene context failed":"[Scene analysis failed]",


            "viewport captured successfully":"[Viewport captured]",
            "viewport capture completed":"[Viewport captured]",
            "captured image successfully":"[Viewport captured]",
            "image captured":"[Viewport captured]",
            "viewport capture failed":"[Viewport capture failed]",
            "image capture failed":"[Viewport capture failed]",


            "render captured successfully":"[Render captured]",
            "render completed":"[Render captured]",
            "render capture failed":"[Render failed]",
            "render failed":"[Render failed]",
            "see render completed":"[Render captured]",
            "see render failed":"[Render failed]",


            "render async started":"[Render started]",
            "render async completed":"[Render completed]",
            "render async failed":"[Render failed]",
            "async render completed":"[Render completed]",
            "async render failed":"[Render failed]",
            "render result retrieved":"[Render completed]",
            "render cancelled":"[Render cancelled]",
            "cancel render completed":"[Render cancelled]",


            "web search completed":"[Found results]",
            "search results found":"[Found results]",
            "web search failed":"[Web search failed]",
            "no results found":"[Web search failed]",
            "web search preview completed":"[Found results]",
            "web search preview failed":"[Web search failed]",
            "found results":"[Found results]",
            "search completed":"[Found results]",
            "search successful":"[Found results]",
            "search results retrieved":"[Found results]",
            "web search success":"[Found results]",
            "web search successful":"[Found results]",


            "properties read successfully":"[Properties read]",
            "custom properties retrieved":"[Properties read]",
            "properties reading failed":"[Properties reading failed]",
            "custom props completed":"[Properties read]",
            "custom props failed":"[Properties reading failed]",


            "render settings read successfully":"[Render settings read]",
            "render settings retrieved":"[Render settings read]",
            "render settings reading failed":"[Render settings reading failed]",
            "render settings completed":"[Render settings read]",
            "render settings failed":"[Render settings reading failed]",


            "scene graph analyzed":"[Scene analyzed]",
            "scene graph completed":"[Scene analyzed]",
            "scene graph failed":"[Scene analysis failed]",


            "nodes analyzed successfully":"[Nodes analyzed]",
            "node graph analyzed":"[Nodes analyzed]",
            "nodes analysis failed":"[Nodes analysis failed]",
            "nodes graph completed":"[Nodes analyzed]",
            "nodes graph failed":"[Nodes analysis failed]",


            "image analyzed successfully":"[Image analyzed]",
            "image analysis completed":"[Image analyzed]",
            "image analysis failed":"[Image analysis failed]",


            "tool executed successfully":"[Tool completed]",
            "tool execution completed":"[Tool completed]",
            "tool response received":"[Tool completed]",
            "tool execution failed":"[Tool failed]",
            "tool failed":"[Tool failed]",
            "tool completed":"[Tool completed]",


            "active renders listed":"[Render status]",
            "list active renders completed":"[Render status]",
            "list active renders failed":"[Render status failed]",
            }


            if content_lower in tool_message_mapping :
                result =tool_message_mapping [content_lower ]
                logger .debug (f"🔧 Exact tool message match: '{content_lower}' -> '{result}'")
                return result 


            for message_pattern ,block_format in tool_message_mapping .items ():
                if message_pattern in content_lower :
                    logger .debug (f"🔧 Partial tool message match: '{message_pattern}' in '{content_lower}' -> '{block_format}'")
                    return block_format 


            if "executed"in content_lower and "code"in content_lower :
                return "[Code executed]"if "success"in content_lower or "completed"in content_lower else "[Code execution failed]"
            elif "captured"in content_lower and ("viewport"in content_lower or "image"in content_lower ):
                return "[Viewport captured]"if "success"in content_lower or "completed"in content_lower else "[Viewport capture failed]"
            elif "render"in content_lower :
                if "captured"in content_lower :
                    return "[Render captured]"if "success"in content_lower or "completed"in content_lower else "[Render failed]"
                elif "async"in content_lower or "started"in content_lower :
                    return "[Render started]"if "success"in content_lower or "started"in content_lower else "[Render failed]"
                elif "cancelled"in content_lower :
                    return "[Render cancelled]"
                elif "active"in content_lower or "list"in content_lower :
                    return "[Render status]"if "success"in content_lower or "completed"in content_lower else "[Render status failed]"
                elif "operation"in content_lower and ("completed"in content_lower or "success"in content_lower ):
                    return "[Render completed]"
                else :
                    return "[Render completed]"if "success"in content_lower or "completed"in content_lower else "[Render failed]"
            elif "scene"in content_lower and ("read"in content_lower or "analyzed"in content_lower or "context"in content_lower or "graph"in content_lower ):
                return "[Scene analyzed]"if "success"in content_lower or "completed"in content_lower else "[Scene analysis failed]"
            elif "query"in content_lower or "querying"in content_lower :
                return "[Scene read]"if "success"in content_lower or "completed"in content_lower else "[Scene reading failed]"
            elif "search"in content_lower and ("web"in content_lower or "found"in content_lower or "results"in content_lower ):

                if "found"in content_lower and "results"in content_lower :
                    logger .debug (f"🔍 Web search pattern detected: 'found' + 'results' in '{content_lower}' -> '[Found results]'")
                    return "[Found results]"
                elif "search"in content_lower and ("completed"in content_lower or "success"in content_lower ):
                    logger .debug (f"🔍 Web search pattern detected: 'search' + 'completed/success' in '{content_lower}' -> '[Found results]'")
                    return "[Found results]"
                elif "search"in content_lower and ("failed"in content_lower or "error"in content_lower ):
                    logger .debug (f"🔍 Web search pattern detected: 'search' + 'failed/error' in '{content_lower}' -> '[Web search failed]'")
                    return "[Web search failed]"
                else :
                    logger .debug (f"🔍 Web search pattern detected: generic search in '{content_lower}' -> '[Found results]'")
                    return "[Found results]"if "success"in content_lower or "completed"in content_lower else "[Web search failed]"
            elif "properties"in content_lower and ("read"in content_lower or "custom"in content_lower or "props"in content_lower ):

                if "were read"in content_lower or "read"in content_lower :
                    return "[Properties read]"
                else :
                    return "[Properties read]"if "success"in content_lower or "completed"in content_lower else "[Properties reading failed]"
            elif "nodes"in content_lower and ("analyzed"in content_lower or "graph"in content_lower ):

                return "[Nodes analyzed]"
            elif "image"in content_lower and "analyzed"in content_lower :
                return "[Image analyzed]"if "success"in content_lower or "completed"in content_lower else "[Image analysis failed]"
            elif "viewport"in content_lower :
                return "[Viewport captured]"if "success"in content_lower or "completed"in content_lower else "[Viewport capture failed]"
            elif "tool"in content_lower :
                return "[Tool completed]"if "success"in content_lower or "completed"in content_lower else "[Tool failed]"
            elif "error"in content_lower or "failed"in content_lower :
                return "[Tool failed]"
            elif "success"in content_lower or "completed"in content_lower :
                return "[Tool completed]"


            if (content .strip ().startswith ('{')and content .strip ().endswith ('}'))or content .strip ().startswith ('[')and content .strip ().endswith (']'):
                return "[Tool completed]"


            if len (content .strip ())<5 or content .strip ().isdigit ():
                return "[Tool completed]"



            logger .debug (f"🔧 No tool message pattern matched for: '{original_content}' -> keeping original")
            return original_content 

        except Exception as e :
            logger .error (f"Error converting tool message to block format: {str(e)}")
            return content 

    def _load_existing_chat_history (self ):
        """Load existing chat messages from the current chat into the message scrollview."""
        try :
            import bpy 
            context =bpy .context 


            if not context or not context .scene :
                logger .warning ("⚠️ No valid scene context found - showing empty chat")
                message_scrollview =self .get_message_scrollview ()
                if message_scrollview :
                    message_scrollview .clear_children ()
                    self ._show_empty_chat_message (message_scrollview )
                return 


            scene_name =context .scene .name 
            if scene_name =="Scene":

                from ....utils .scene_handler import scene_handler 
                file_new_just_happened =scene_handler .check_and_clear_file_new_flag ()

                if file_new_just_happened :

                    all_chat_messages =context .scene .vibe4d_chat_messages 
                    if len (all_chat_messages )>0 :

                        context .scene .vibe4d_chat_messages .clear ()
                        context .scene .vibe4d_current_chat_id =""
                        context .scene .vibe4d_current_text_input =""


                        message_scrollview =self .get_message_scrollview ()
                        if message_scrollview :
                            message_scrollview .clear_children ()
                            self ._show_empty_chat_message (message_scrollview )

                        return 
                    else :

                        message_scrollview =self .get_message_scrollview ()
                        if message_scrollview :
                            message_scrollview .clear_children ()
                            self ._show_empty_chat_message (message_scrollview )
                        return 
                else :


                    current_chat_id =getattr (context .scene ,'vibe4d_current_chat_id','')
                    if not current_chat_id :
                        message_scrollview =self .get_message_scrollview ()
                        if message_scrollview :
                            message_scrollview .clear_children ()
                            self ._show_empty_chat_message (message_scrollview )
                        return 




            from ....utils .history_manager import history_manager 


            current_chat_id =getattr (context .scene ,'vibe4d_current_chat_id','')

            if not current_chat_id :
                logger .info (f"📋 No current chat ID in scene {context.scene.name} - showing empty chat")
                message_scrollview =self .get_message_scrollview ()
                if message_scrollview :
                    message_scrollview .clear_children ()
                    self ._show_empty_chat_message (message_scrollview )
                return 


            openai_messages =history_manager .get_chat_messages (context )


            message_scrollview =self .get_message_scrollview ()
            if not message_scrollview :
                logger .warning ("⚠️ No message scrollview found")
                return 


            message_scrollview .clear_children ()

            if not openai_messages :

                logger .info (f"📋 No messages found for chat {current_chat_id} in scene {context.scene.name} - showing empty chat")
                self ._show_empty_chat_message (message_scrollview )

                self ._restore_unsent_text_for_current_chat ()
                return 


            non_system_messages =[msg for msg in openai_messages if msg .get ('role')!='system']


            ui_manager =None 
            if hasattr (self .callbacks .get ('on_send'),'__self__'):
                ui_manager =self .callbacks ['on_send'].__self__ 
                if hasattr (ui_manager ,'factory'):
                    factory =ui_manager .factory 


                    i =0 
                    while i <len (non_system_messages ):
                        current_msg =non_system_messages [i ]


                        if current_msg .get ('role')=='user':
                            self ._add_message_to_ui (factory ,current_msg ,is_ai_response =False )
                            i +=1 
                            continue 


                        elif current_msg .get ('role')=='assistant':
                            tool_calls =current_msg .get ('tool_calls',[])
                            assistant_content =self ._extract_content_from_message (current_msg )


                            tool_responses =[]
                            if tool_calls :

                                for call in tool_calls :
                                    call_id =call .get ('id')
                                    if call_id :

                                        for j in range (i +1 ,len (non_system_messages )):
                                            response_msg =non_system_messages [j ]
                                            if (response_msg .get ('role')=='tool'and 
                                            response_msg .get ('tool_call_id')==call_id ):
                                                tool_responses .append (response_msg )
                                                break 


                            if assistant_content or tool_calls :
                                self ._add_message_to_ui (factory ,current_msg ,is_ai_response =True )
                                i +=1 


                                for tool_response in tool_responses :
                                    self ._add_message_to_ui (factory ,tool_response ,is_ai_response =True ,is_tool_message =True )

                                    if tool_response in non_system_messages [i :]:
                                        response_index =non_system_messages .index (tool_response ,i )
                                        if response_index <len (non_system_messages ):
                                            non_system_messages .pop (response_index )
                                continue 
                            else :

                                i +=1 
                                continue 


                        elif current_msg .get ('role')=='tool':
                            self ._add_message_to_ui (factory ,current_msg ,is_ai_response =True ,is_tool_message =True )
                            i +=1 
                            continue 

                        else :

                            self ._add_message_to_ui (factory ,current_msg ,is_ai_response =True )
                            i +=1 
                            continue 


                    self ._restore_unsent_text_for_current_chat ()
                    return 


            logger .warning ("Factory not available, using fallback method")
            self ._load_messages_fallback (non_system_messages ,message_scrollview )


            self ._restore_unsent_text_for_current_chat ()

        except Exception as e :
            logger .error (f"Failed to load existing chat history: {str(e)}")
            import traceback 
            logger .error (traceback .format_exc ())

            try :
                message_scrollview =self .get_message_scrollview ()
                if message_scrollview :
                    message_scrollview .clear_children ()
                    self ._show_empty_chat_message (message_scrollview )
                    logger .info ("Showed empty chat due to error loading history")
            except :
                pass 

    def _restore_unsent_text_for_current_chat (self ):
        """Restore unsent text for the current chat."""
        try :
            import bpy 
            context =bpy .context 
            from ....utils .history_manager import history_manager 
            current_chat_id =getattr (context .scene ,'vibe4d_current_chat_id','')
            if current_chat_id :
                history_manager .restore_unsent_text (context ,current_chat_id )
                logger .debug (f"Restored unsent text for current chat: {current_chat_id}")
        except Exception as e :
            logger .debug (f"Could not restore unsent text for current chat: {e}")

    def _setup_text_input_change_handler (self ):
        """Set up handler to save unsent text when text changes."""
        try :
            text_input =self .components .get ('text_input')
            if text_input and hasattr (text_input ,'on_change'):

                original_on_change =text_input .on_change 

                def combined_on_change (text ):

                    if original_on_change :
                        original_on_change (text )


                    self ._save_unsent_text_on_change (text )

                text_input .on_change =combined_on_change 
                logger .debug ("Set up text input change handler for unsent text saving")
        except Exception as e :
            logger .debug (f"Could not set up text input change handler: {e}")

    def _save_unsent_text_on_change (self ,text ):
        """Save unsent text when text input changes."""
        try :
            import bpy 
            context =bpy .context 
            from ....utils .history_manager import history_manager 
            current_chat_id =getattr (context .scene ,'vibe4d_current_chat_id','')
            if current_chat_id :
                history_manager .save_unsent_text (context ,current_chat_id ,text )
        except Exception as e :
            logger .debug (f"Could not save unsent text on change: {e}")

    def _load_messages_fallback (self ,messages :list ,message_scrollview ):
        """Fallback method for loading messages when factory is not available."""
        try :
            logger .info ("Using fallback method to load messages")


            from ..components import Label 
            from ..theme import get_themed_style 

            for msg in messages :
                is_tool_message =msg .get ('role')=='tool'
                content =msg .get ('content','')


                if is_tool_message :
                    display_content =self ._convert_tool_message_to_block_format (content )
                else :
                    display_content =content 


                label_height =40 
                label_width =message_scrollview .bounds .width -40 
                label_x =20 
                label_y =len (message_scrollview .children )*(label_height +10 )

                message_label =Label (display_content ,label_x ,label_y ,label_width ,label_height )
                message_label .style =get_themed_style ("text")
                message_label .set_text_align ("left")

                message_scrollview .add_child (message_label )


            message_scrollview ._update_content_bounds ()

        except Exception as e :
            logger .error (f"Failed to load messages using fallback method: {str(e)}")
            import traceback 
            logger .error (traceback .format_exc ())

    def _convert_multimodal_to_markdown (self ,content_list :list )->str :
        """Convert multimodal content to markdown for display."""
        try :
            parts =[]
            for item in content_list :
                if isinstance (item ,dict ):
                    if item .get ('type')=='text':
                        parts .append (item .get ('text',''))
                    elif item .get ('type')=='image_url':

                        parts .append ('[Image]')
                else :
                    parts .append (str (item ))
            return '\n'.join (parts )
        except Exception as e :
            logger .error (f"Failed to convert multimodal content: {str(e)}")
            return str (content_list )

    def _show_empty_chat_message (self ,message_scrollview :ScrollView ):
        """Show the 'Ready when you are.' message for empty chat state."""
        try :

            label_height =30 

            message_padding =self .MESSAGE_PADDING 
            label_width =message_scrollview .bounds .width -(message_padding *2 )
            label_x =(message_scrollview .bounds .width -label_width )//2 

            label_y =(message_scrollview .bounds .height -label_height )//2 


            empty_state_label =Label ("Ready when you are.",label_x ,label_y ,label_width ,label_height )
            empty_state_label .style =get_themed_style ("text")
            empty_state_label .style .text_color =(0.6 ,0.6 ,0.6 ,1.0 )
            empty_state_label .set_text_align ("center")


            message_scrollview .add_child (empty_state_label )


            message_scrollview .show_scrollbars =False 
            message_scrollview .max_scroll_x =0 
            message_scrollview .max_scroll_y =0 
            message_scrollview .scroll_x =0 
            message_scrollview .scroll_y =0 

        except Exception as e :
            logger .error (f"❌ Failed to show empty chat message: {str(e)}")
            import traceback 
            logger .error (traceback .format_exc ())

    def _update_empty_chat_message_position (self ,message_scrollview :ScrollView ):
        """Update the position of the empty chat message to keep it centered."""
        try :
            if not message_scrollview .children :
                return 


            empty_state_label =message_scrollview .children [0 ]


            if not (hasattr (empty_state_label ,'get_text')and 
            empty_state_label .get_text ()=="Ready when you are."):
                return 


            label_height =30 

            message_padding =self .MESSAGE_PADDING 
            label_width =message_scrollview .bounds .width -(message_padding *2 )
            label_x =(message_scrollview .bounds .width -label_width )//2 
            label_y =(message_scrollview .bounds .height -label_height )//2 


            empty_state_label .set_position (label_x ,label_y )
            empty_state_label .set_size (label_width ,label_height )


            message_scrollview ._update_content_bounds ()

            logger .debug ("✅ Updated empty chat message position for new scrollview size")

        except Exception as e :
            logger .error (f"❌ Failed to update empty chat message position: {str(e)}")
            import traceback 
            logger .error (traceback .format_exc ())

    def _add_message_to_ui (self ,factory ,message ,is_ai_response =False ,is_tool_message =False ):
        """Add a single message to the UI using the factory methods."""
        try :
            content =self ._extract_content_from_message (message )


            if isinstance (content ,list ):

                display_content =""

                for item in content :
                    if isinstance (item ,dict ):
                        if item .get ('type')=='text':
                            display_content =item .get ('text','')
                        elif item .get ('type')=='image_url':

                            if not display_content :
                                display_content ="[Image captured]"


                content =display_content 


            has_image =False 
            legacy_image_data =None 
            if hasattr (message ,'image_data')and getattr (message ,'image_data'):
                has_image =True 
                legacy_image_data =getattr (message ,'image_data')

            if has_image and legacy_image_data :


                factory .add_message_to_scrollview (
                self .components ,content ,is_ai_response =is_ai_response 
                )
            elif is_tool_message :

                block_content =self ._convert_tool_message_to_block_format (content )
                factory .add_markdown_message_to_scrollview (
                self .components ,block_content ,is_ai_response =True 
                )
                logger .debug (f"🔧 Added tool message: '{content}' -> '{block_content}'")
            elif is_ai_response :

                factory .add_markdown_message_to_scrollview (
                self .components ,content ,is_ai_response =True 
                )
            else :

                factory .add_message_to_scrollview (
                self .components ,content ,is_ai_response =False 
                )

        except Exception as e :
            logger .error (f"Failed to add message to UI: {str(e)}")
            import traceback 
            logger .error (traceback .format_exc ())

    def _extract_content_from_message (self ,message ):
        """Extract content from a message, handling both dict and object formats."""
        try :

            if isinstance (message ,dict ):
                return message .get ('content','')


            elif hasattr (message ,'content'):
                return getattr (message ,'content','')


            else :
                return str (message )

        except Exception as e :
            logger .error (f"Failed to extract content from message: {str(e)}")
            return str (message )