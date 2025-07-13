"""
History view for displaying message history.
"""

import logging 
import bpy 
import json 
import urllib .request 
import urllib .parse 
from datetime import datetime ,timedelta 
from typing import Dict ,Any ,List ,Tuple 

from .base_view import BaseView 
from ..layout_manager import LayoutConfig ,LayoutStrategy 
from ..components import Label ,Button ,BackButton 
from ..components .scrollview import ScrollView ,ScrollDirection 
from ..theme import get_themed_style 
from ..unified_styles import Styles 

logger =logging .getLogger (__name__ )


def get_main_padding ():
    return Styles .get_main_padding ()

def get_content_margin ():
    return Styles .get_content_margin ()

def get_scrollview_margin ():
    return Styles .get_scrollview_margin ()

def get_button_height_standard ():
    return Styles .get_button_height_standard ()

def get_button_height_large ():
    return Styles .get_button_height_large ()

def get_new_chat_button_height ():
    return Styles .get_new_chat_button_height ()

def get_button_width_standard ():
    return Styles .get_button_width_standard ()

def get_button_corner_radius_standard ():
    return Styles .get_button_corner_radius_standard ()

def get_button_spacing ():
    return Styles .get_button_spacing ()

def get_item_height_chat ():
    return Styles .get_item_height_chat ()

def get_item_height_label ():
    return Styles .get_item_height_label ()

def get_item_spacing ():
    return Styles .get_item_spacing ()

def get_go_back_button_offset ():
    return Styles .get_go_back_button_offset ()

def get_go_back_button_side_padding ():
    return Styles .get_go_back_button_side_padding ()

def get_go_back_button_icon_size ():
    return Styles .get_go_back_button_icon_size ()

def get_go_back_button_icon_gap ():
    return Styles .get_go_back_button_icon_gap ()

def get_new_chat_button_offset ():
    return Styles .get_new_chat_button_offset ()

def get_history_area_top_offset ():
    return Styles .get_history_area_top_offset ()

def get_history_area_bottom_offset ():
    return Styles .get_history_area_bottom_offset ()


TITLE_MAX_LENGTH =Styles .TITLE_MAX_LENGTH 

class HistoryView (BaseView ):
    """History view for displaying message history."""

    def __init__ (self ):
        super ().__init__ ()
        self .chat_sessions =[]
        self ._cached_names ={}

    def create_layout (self ,viewport_width :int ,viewport_height :int )->Dict [str ,Any ]:
        """Create the history view layout."""
        layouts ={}
        components ={}


        main_layout =self ._create_layout_container (
        "main",
        LayoutConfig (
        strategy =LayoutStrategy .ABSOLUTE ,
        padding_top =get_main_padding (),
        padding_right =get_main_padding (),
        padding_bottom =get_main_padding (),
        padding_left =get_main_padding ()
        )
        )
        layouts ['main']=main_layout 


        side_padding =get_go_back_button_side_padding ()
        top_offset =get_go_back_button_offset ()

        go_back_button =BackButton (side_padding ,0 ,on_click =self ._handle_go_back )

        button_y =viewport_height -top_offset -go_back_button .bounds .height 
        go_back_button .set_position (side_padding ,button_y )
        components ['go_back_button']=go_back_button 


        new_chat_button =Button ("+ New Chat",get_content_margin (),viewport_height -get_new_chat_button_offset (),viewport_width -get_scrollview_margin (),get_new_chat_button_height (),
        corner_radius =6 ,on_click =self ._handle_new_chat )

        new_chat_button .style .background_color =Styles .get_themed_color ('bg_primary')
        new_chat_button .style .border_color =Styles .get_themed_color ('border')
        new_chat_button .style .border_width =1 
        new_chat_button .style .text_color =Styles .get_themed_color ('text')
        new_chat_button .style .font_size =Styles .get_font_size ()
        components ['new_chat_button']=new_chat_button 


        history_scrollview =ScrollView (get_content_margin (),get_content_margin (),viewport_width -get_scrollview_margin (),viewport_height -get_history_area_top_offset (),
        reverse_y_coordinate =True )
        history_scrollview .scroll_direction =ScrollDirection .VERTICAL 
        history_scrollview .show_scrollbars =True 
        history_scrollview .style .background_color =(0 ,0 ,0 ,0 )
        history_scrollview .style .border_color =(0 ,0 ,0 ,0 )
        components ['history_scrollview']=history_scrollview 


        try :
            context =bpy .context 


            from ....utils .history_manager import history_manager 
            self .chat_sessions =history_manager .get_all_chats (context )


            self ._current_context =context 

        except Exception as e :
            logger .error (f"Failed to load chat sessions: {str(e)}")
            self .chat_sessions =[]

        self ._populate_chat_list (history_scrollview )

        self .components =components 
        self .layouts =layouts 

        return {
        'layouts':layouts ,
        'components':components ,
        'all_components':self ._get_all_components ()
        }

    def update_layout (self ,viewport_width :int ,viewport_height :int ):
        """Update layout positions when viewport changes."""

        if 'go_back_button'in self .components :
            go_back_button =self .components ['go_back_button']
            side_padding =get_go_back_button_side_padding ()
            top_offset =get_go_back_button_offset ()
            button_y =viewport_height -top_offset -go_back_button .bounds .height 
            go_back_button .set_position (side_padding ,button_y )


        if 'new_chat_button'in self .components :
            new_chat_button =self .components ['new_chat_button']
            new_chat_button .set_position (get_content_margin (),viewport_height -get_new_chat_button_offset ())
            new_chat_button .set_size (viewport_width -get_scrollview_margin (),get_new_chat_button_height ())


        if 'history_scrollview'in self .components :
            history_scrollview =self .components ['history_scrollview']
            history_scrollview .set_size (viewport_width -get_scrollview_margin (),viewport_height -get_history_area_bottom_offset ())
            history_scrollview .set_position (get_content_margin (),0 )


            new_item_width =viewport_width -get_scrollview_margin ()
            for child in history_scrollview .children :
                if hasattr (child ,'set_size'):
                    child .set_size (new_item_width ,child .bounds .height )

    def _populate_chat_list (self ,scrollview :ScrollView ):
        """Populate the scrollview with chat session items."""
        scrollview .clear_children ()

        if not self .chat_sessions :

            label_height =get_item_height_label ()
            label_width =scrollview .bounds .width -get_scrollview_margin ()
            label_x =get_content_margin ()

            label_y =(scrollview .bounds .height -label_height )//2 

            no_chats_label =Label ("No chat history found",label_x ,label_y ,label_width ,label_height )
            no_chats_label .style =get_themed_style ("text")
            no_chats_label .style .text_color =(0.6 ,0.6 ,0.6 ,1.0 )
            no_chats_label .set_text_align ("center")
            scrollview .add_child (no_chats_label )


            scrollview .show_scrollbars =False 
            scrollview .max_scroll_x =0 
            scrollview .max_scroll_y =0 
            scrollview .scroll_x =0 
            scrollview .scroll_y =0 
            return 


        item_height =get_item_height_chat ()
        item_spacing =get_item_spacing ()
        num_sessions =len (self .chat_sessions )
        total_height =num_sessions *item_height +max (0 ,(num_sessions -1 )*item_spacing )


        scrollview .show_scrollbars =True 



        y_position =0 

        for session in self .chat_sessions :
            chat_item =self ._create_chat_item (session ,y_position ,scrollview .bounds .width -get_scrollview_margin (),item_height )
            scrollview .add_child (chat_item )
            y_position +=(item_height +item_spacing )


        scrollview ._update_content_bounds ()


        scrollview .scroll_to_top ()

    def _create_chat_item (self ,session :Dict [str ,Any ],y :int ,width :int ,height :int )->Button :
        """Create a chat item button for a session."""

        chat_button =Button ("",0 ,y ,width ,height ,corner_radius =6 ,
        on_click =lambda :self ._handle_chat_click (session ))


        chat_button .style .background_color =(0 ,0 ,0 ,0 )
        chat_button .style .focus_background_color =(0 ,0 ,0 ,0 )
        chat_button .style .border_color =Styles .get_themed_color ('border')
        chat_button .style .border_width =0 
        chat_button .style .text_color =Styles .get_themed_color ('text')
        chat_button .style .font_size =Styles .get_font_size ()


        session_title =session .get ('title','New conversation')


        button_text =f"{session_title}"
        chat_button .set_text (button_text )
        chat_button .set_text_align ("left")

        return chat_button 

    def _handle_chat_click (self ,session :Dict [str ,Any ]):
        """Handle clicking on a chat session."""

        try :
            context =bpy .context 


            chat_id =session ['chat_id']
            context .scene .vibe4d_current_chat_id =chat_id 


            if self .callbacks .get ('on_view_change'):
                from ..ui_factory import ViewState 
                self .callbacks ['on_view_change'](ViewState .MAIN )

        except Exception as e :
            logger .error (f"Failed to load chat session: {str(e)}")
            import traceback 
            logger .error (traceback .format_exc ())

    def _handle_go_back (self ):
        """Handle go back button click - return to main view."""
        if self .callbacks .get ('on_go_back'):
            self .callbacks ['on_go_back']()
        else :

            if self .callbacks .get ('on_view_change'):
                from ..ui_factory import ViewState 
                self .callbacks ['on_view_change'](ViewState .MAIN )

    def _handle_new_chat (self ):
        """Handle new chat button click - start a new chat."""
        try :
            context =bpy .context 


            from ....utils .history_manager import history_manager 
            new_chat_id =history_manager .create_new_chat (context )

            logger .info (f"✅ Started new chat from history view: {new_chat_id}")


            if self .callbacks .get ('on_view_change'):
                from ..ui_factory import ViewState 
                self .callbacks ['on_view_change'](ViewState .MAIN )
            else :
                logger .warning ("No view change callback registered")

        except Exception as e :
            logger .error (f"Failed to start new chat: {str(e)}")
            import traceback 
            logger .error (traceback .format_exc ())