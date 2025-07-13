"""
No connection view for when internet is not available.
"""

import logging 
from typing import Dict ,Any 

from .base_view import BaseView 
from ..layout_manager import LayoutConfig ,LayoutStrategy 
from ..components import Label ,Button 
from ..components .image import ImageComponent 
from ..theme import get_themed_style 
from ..styles import FontSizes 
from ..unified_styles import UnifiedStyles as Styles 

logger =logging .getLogger (__name__ )


class NoConnectionView (BaseView ):
    """No connection view for when internet is not available."""



    @property 
    def CONTAINER_PADDING (self ):
        return Styles .get_no_connection_padding ()

    @property 
    def ICON_WIDTH (self ):
        return Styles .get_no_connection_icon_width ()

    @property 
    def ICON_HEIGHT (self ):
        return Styles .get_no_connection_icon_height ()

    @property 
    def TITLE_WIDTH (self ):
        return Styles .get_no_connection_title_width ()

    @property 
    def TITLE_HEIGHT (self ):
        return Styles .get_no_connection_title_height ()

    @property 
    def SUBTITLE_WIDTH (self ):
        return Styles .get_no_connection_subtitle_width ()

    @property 
    def SUBTITLE_HEIGHT (self ):
        return Styles .get_no_connection_subtitle_height ()

    @property 
    def BUTTON_WIDTH (self ):
        return Styles .get_no_connection_button_width ()

    @property 
    def BUTTON_HEIGHT (self ):
        return Styles .get_no_connection_button_height ()

    @property 
    def GAP_LARGE (self ):
        return Styles .get_no_connection_gap_large ()

    @property 
    def GAP_MEDIUM (self ):
        return Styles .get_no_connection_gap_medium ()

    @property 
    def BUTTON_CORNER_RADIUS (self ):
        return Styles .get_no_connection_button_corner_radius ()

    def __init__ (self ):
        super ().__init__ ()

    def create_layout (self ,viewport_width :int ,viewport_height :int )->Dict [str ,Any ]:
        """Create the no connection view layout."""
        layouts ={}
        components ={}


        layout_data =self ._get_no_connection_layout_params (viewport_width ,viewport_height )
        layout_params =layout_data ['params']
        positions =layout_data ['positions']


        main_layout =self ._create_layout_container (
        "main",
        LayoutConfig (
        strategy =LayoutStrategy .ABSOLUTE ,
        padding_top =self .CONTAINER_PADDING ,
        padding_right =self .CONTAINER_PADDING ,
        padding_bottom =self .CONTAINER_PADDING ,
        padding_left =self .CONTAINER_PADDING 
        )
        )
        layouts ['main']=main_layout 


        no_internet_icon =ImageComponent ("nointernet.png",
        layout_params ['center_x']-layout_params ['icon_width']//2 ,
        positions ['icon_y'],
        layout_params ['icon_width'],
        layout_params ['icon_height'])
        components ['no_internet_icon']=no_internet_icon 


        title_text =Label ("No connection",
        layout_params ['center_x']-layout_params ['title_width']//2 ,
        positions ['title_y'],
        layout_params ['title_width'],
        layout_params ['title_height'])
        title_text .style =get_themed_style ("title")
        title_text .style .font_size =FontSizes .Title 
        title_text .style .text_align ="center"
        title_text .style .text_color =(1.0 ,1.0 ,1.0 ,1.0 )
        components ['title_text']=title_text 


        subtitle_text =Label ("Vibe4D cannot work without internet.\nPlease check your connection.",
        layout_params ['center_x']-layout_params ['subtitle_width']//2 ,
        positions ['subtitle_y'],
        layout_params ['subtitle_width'],
        layout_params ['subtitle_height'])
        subtitle_text .style =get_themed_style ("label")
        subtitle_text .style .font_size =FontSizes .Default 
        subtitle_text .style .text_align ="center"
        subtitle_text .style .text_color =(0.8 ,0.8 ,0.8 ,1.0 )
        components ['subtitle_text']=subtitle_text 


        retry_button =Button ("Retry Connection",
        layout_params ['center_x']-layout_params ['button_width']//2 ,
        positions ['button_y'],
        layout_params ['button_width'],
        layout_params ['button_height'],
        corner_radius =self .BUTTON_CORNER_RADIUS ,
        on_click =self ._handle_retry_connection )
        retry_button .style =get_themed_style ("button")
        retry_button .style .background_color =(0.4 ,0.6 ,1.0 ,1.0 )
        components ['retry_button']=retry_button 

        self .components =components 
        self .layouts =layouts 

        return {
        'layouts':layouts ,
        'components':components ,
        'all_components':self ._get_all_components ()
        }

    def update_layout (self ,viewport_width :int ,viewport_height :int ):
        """Update layout positions when viewport changes."""
        layout_data =self ._get_no_connection_layout_params (viewport_width ,viewport_height )
        layout_params =layout_data ['params']
        positions =layout_data ['positions']


        if 'no_internet_icon'in self .components :
            icon =self .components ['no_internet_icon']
            icon .set_position (layout_params ['center_x']-layout_params ['icon_width']//2 ,positions ['icon_y'])
            icon .set_size (layout_params ['icon_width'],layout_params ['icon_height'])


        if 'title_text'in self .components :
            title_text =self .components ['title_text']
            title_text .set_position (layout_params ['center_x']-layout_params ['title_width']//2 ,positions ['title_y'])
            title_text .set_size (layout_params ['title_width'],layout_params ['title_height'])


        if 'subtitle_text'in self .components :
            subtitle_text =self .components ['subtitle_text']
            subtitle_text .set_position (layout_params ['center_x']-layout_params ['subtitle_width']//2 ,positions ['subtitle_y'])
            subtitle_text .set_size (layout_params ['subtitle_width'],layout_params ['subtitle_height'])


        if 'retry_button'in self .components :
            retry_button =self .components ['retry_button']
            retry_button .set_position (layout_params ['center_x']-layout_params ['button_width']//2 ,positions ['button_y'])
            retry_button .set_size (layout_params ['button_width'],layout_params ['button_height'])

    def _get_no_connection_layout_params (self ,viewport_width :int ,viewport_height :int )->Dict [str ,Any ]:
        """Get standardized no connection layout parameters for consistent positioning."""
        layout_params ={
        'center_x':viewport_width //2 ,
        'center_y':viewport_height //2 ,
        'icon_width':self .ICON_WIDTH ,
        'icon_height':self .ICON_HEIGHT ,
        'title_width':self .TITLE_WIDTH ,
        'title_height':self .TITLE_HEIGHT ,
        'subtitle_width':self .SUBTITLE_WIDTH ,
        'subtitle_height':self .SUBTITLE_HEIGHT ,
        'button_width':self .BUTTON_WIDTH ,
        'button_height':self .BUTTON_HEIGHT ,
        'gap_large':self .GAP_LARGE ,
        'gap_medium':self .GAP_MEDIUM ,
        }


        positions ={}
        positions ['icon_y']=layout_params ['center_y']+60 
        positions ['title_y']=positions ['icon_y']-layout_params ['icon_height']-layout_params ['gap_medium']
        positions ['subtitle_y']=positions ['title_y']-layout_params ['title_height']-layout_params ['gap_medium']
        positions ['button_y']=positions ['subtitle_y']-layout_params ['subtitle_height']-layout_params ['gap_large']

        return {'params':layout_params ,'positions':positions }

    def _handle_retry_connection (self ):
        """Handle retry connection button click."""
        logger .info ("Retry connection button clicked")

        try :

            try :
                from ...api .client import api_client 
            except ImportError :

                from vibe4d .api .client import api_client 


            success ,_ =api_client ._make_request ("/v1/license/verify",{"license_key":"test"})

            if success :

                import bpy 
                context =bpy .context 
                is_authenticated =getattr (context .window_manager ,'vibe4d_authenticated',False )

                if is_authenticated :

                    if self .callbacks .get ('on_view_change'):
                        from ..ui_factory import ViewState 
                        self .callbacks ['on_view_change'](ViewState .MAIN )
                        logger .info ("Connection restored - switching to main view")
                else :

                    if self .callbacks .get ('on_view_change'):
                        from ..ui_factory import ViewState 
                        self .callbacks ['on_view_change'](ViewState .AUTH )
                        logger .info ("Connection restored - switching to auth view")
            else :

                logger .warning ("Connection test failed - still no internet")
                self ._update_retry_button_text ("Still no connection")

        except Exception as e :
            logger .error (f"Error testing connection: {e}")
            self ._update_retry_button_text ("Connection failed")

    def _update_retry_button_text (self ,text :str ):
        """Update the retry button text temporarily."""
        if 'retry_button'in self .components :
            retry_button =self .components ['retry_button']
            original_text =retry_button .text 
            retry_button .text =text 


            import bpy 
            def reset_text ():
                if 'retry_button'in self .components :
                    self .components ['retry_button'].text =original_text 
                return None 

            bpy .app .timers .register (reset_text ,first_interval =2.0 )

    def validate_layout_consistency (self ,viewport_width :int ,viewport_height :int )->bool :
        """Validate that all no connection layout functions use consistent parameters."""
        try :

            layout_data =self ._get_no_connection_layout_params (viewport_width ,viewport_height )


            required_param_keys =[
            'center_x','center_y','icon_width','icon_height',
            'title_width','title_height','subtitle_width','subtitle_height',
            'button_width','button_height','gap_large','gap_medium'
            ]

            required_position_keys =['icon_y','title_y','subtitle_y','button_y']

            params_valid =all (key in layout_data ['params']for key in required_param_keys )
            positions_valid =all (key in layout_data ['positions']for key in required_position_keys )


            positions =layout_data ['positions']
            logical_order =(
            positions ['icon_y']>positions ['title_y']>
            positions ['subtitle_y']>positions ['button_y']
            )

            logger .info (f"No connection layout validation: params={params_valid}, positions={positions_valid}, order={logical_order}")
            return params_valid and positions_valid and logical_order 

        except Exception as e :
            logger .error (f"No connection layout validation failed: {e}")
            return False 

    @staticmethod 
    def check_internet_connection ()->bool :
        """Check if internet connection is available."""
        try :
            try :
                from ...api .client import api_client 
            except ImportError :

                from vibe4d .api .client import api_client 


            api_client .timeout =5 
            success ,_ =api_client ._make_request ("/v1/license/verify",{"license_key":"test"})
            api_client .timeout =30 
            return success 
        except Exception as e :
            logger .debug (f"Internet connection check failed: {e}")
            return False 
