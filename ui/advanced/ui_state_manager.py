"""
UI State Manager for robust UI state persistence and recovery.

This module handles saving UI state with the scene and recovering it reliably
when the scene is loaded, using Blender's built-in layout preservation.
"""

import bpy 
import json 
import logging 
import uuid 
import time 
from typing import Dict ,Any ,Optional ,Tuple 
from dataclasses import dataclass ,asdict 

logger =logging .getLogger (__name__ )


@dataclass 
class ViewportConfig :
    """Configuration for a UI viewport with robust identification."""
    area_id :str =""


    width :int =0 
    height :int =0 
    x :int =0 
    y :int =0 


    area_index :int =-1 
    relative_x :float =0.0 
    relative_y :float =0.0 
    relative_width :float =0.0 
    relative_height :float =0.0 
    screen_width :int =0 
    screen_height :int =0 


    viewport_fingerprint :str =""
    area_neighbors :str =""


    show_gizmo :bool =False 
    show_region_ui :bool =False 
    show_region_toolbar :bool =False 
    show_region_header :bool =False 
    show_region_hud :bool =False 
    show_overlays :bool =False 
    shading_type :str ='SOLID'

    lens :float =50.0 
    clip_start :float =0.1 
    clip_end :float =100.0 


@dataclass 
class UIStateData :
    """Complete UI state data."""
    is_active :bool =False 
    viewport_config :ViewportConfig =None 
    current_view :str ="main"
    conversation_state :Dict [str ,Any ]=None 
    layout_version :int =1 

    def __post_init__ (self ):
        if self .viewport_config is None :
            self .viewport_config =ViewportConfig ()
        if self .conversation_state is None :
            self .conversation_state ={}


class UIStateManager :
    """Manages UI state persistence and recovery."""

    def __init__ (self ):
        self .logger =logger 
        self ._area_markers ={}

    def save_ui_state (self ,context ,ui_manager ,target_area =None ):
        """Save current UI state to the scene."""
        try :
            if not target_area and ui_manager .state .target_area :
                target_area =ui_manager .state .target_area 

            if not target_area :
                self .logger .warning ("No target area available for saving UI state")
                return False 


            viewport_config =self ._create_viewport_config (target_area )


            conversation_state ={}
            if hasattr (ui_manager ,'factory')and ui_manager .factory :
                conversation_state =self ._extract_conversation_state (ui_manager .factory )


            current_view ='main'
            if hasattr (ui_manager ,'factory')and ui_manager .factory :
                factory_view =getattr (ui_manager .factory ,'current_view',None )
                if factory_view :
                    current_view =factory_view .value if hasattr (factory_view ,'value')else str (factory_view )


            ui_state =UIStateData (
            is_active =ui_manager .is_ui_active (),
            viewport_config =viewport_config ,
            current_view =current_view ,
            conversation_state =conversation_state ,
            layout_version =1 
            )


            context .scene .vibe4d_ui_active =ui_state .is_active 
            context .scene .vibe4d_ui_viewport_config =json .dumps (asdict (ui_state .viewport_config ))
            context .scene .vibe4d_ui_current_view =ui_state .current_view .value if hasattr (ui_state .current_view ,'value')else str (ui_state .current_view )
            context .scene .vibe4d_ui_conversation_state =json .dumps (ui_state .conversation_state )
            context .scene .vibe4d_ui_layout_version =ui_state .layout_version 


            if target_area :
                self ._mark_ui_area (target_area ,viewport_config .area_id )

            return True 

        except Exception as e :
            self .logger .error (f"Failed to save UI state: {e}")
            import traceback 
            self .logger .error (traceback .format_exc ())
            return False 

    def load_ui_state (self ,context )->Optional [UIStateData ]:
        """Load UI state from the scene."""
        try :

            if not getattr (context .scene ,'vibe4d_ui_active',False ):
                self .logger .debug ("UI was not active in saved state")
                return None 


            viewport_config_json =getattr (context .scene ,'vibe4d_ui_viewport_config','{}')
            viewport_config_dict =json .loads (viewport_config_json )if viewport_config_json else {}
            viewport_config =ViewportConfig (**viewport_config_dict )


            conversation_state_json =getattr (context .scene ,'vibe4d_ui_conversation_state','{}')
            conversation_state =json .loads (conversation_state_json )if conversation_state_json else {}


            ui_state =UIStateData (
            is_active =getattr (context .scene ,'vibe4d_ui_active',False ),
            viewport_config =viewport_config ,
            current_view =getattr (context .scene ,'vibe4d_ui_current_view','main'),
            conversation_state =conversation_state ,
            layout_version =getattr (context .scene ,'vibe4d_ui_layout_version',1 )
            )

            self .logger .info (f"UI state loaded successfully. Active: {ui_state.is_active}, View: {ui_state.current_view}")
            return ui_state 

        except Exception as e :
            self .logger .error (f"Failed to load UI state: {e}")
            return None 

    def find_ui_viewport (self ,context ,ui_state :UIStateData )->Optional [Any ]:
        """Find the specific viewport using comprehensive identification parameters."""
        try :
            config =ui_state .viewport_config 
            screen =context .screen 

            if not config or not config .area_id :
                self .logger .warning ("No viewport configuration available")
                return None 


            target_area =self ._find_by_area_index (screen ,config )
            if target_area :
                self .logger .info (f"✅ Found UI viewport by area index: {config.area_index}")
                return target_area 


            target_area =self ._find_by_relative_position (screen ,config )
            if target_area :
                self .logger .info (f"✅ Found UI viewport by relative position: {config.relative_x:.2%},{config.relative_y:.2%}")
                return target_area 


            target_area =self ._find_by_fingerprint (screen ,config )
            if target_area :
                self .logger .info (f"✅ Found UI viewport by fingerprint matching")
                return target_area 


            target_area =self ._find_by_neighbors (screen ,config )
            if target_area :
                self .logger .info (f"✅ Found UI viewport by neighbor analysis")
                return target_area 


            target_area =self ._find_marked_ui_area (context )
            if target_area :
                self .logger .info (f"✅ Found UI viewport by scene markers")
                return target_area 


            target_area =self ._find_by_dimensions (screen ,config )
            if target_area :
                self .logger .info (f"⚠️ Found UI viewport by dimension fallback")
                return target_area 


            target_area =self ._find_any_suitable_viewport (screen )
            if target_area :
                self .logger .warning (f"⚠️ Using fallback viewport - original identification failed")
                return target_area 

            self .logger .error ("❌ Could not find any suitable viewport for UI recovery")
            return None 

        except Exception as e :
            self .logger .error (f"Error finding UI viewport: {e}")
            return None 

    def recover_ui_state (self ,context ,ui_manager )->bool :
        """Recover UI state and restore the overlay."""
        try :

            ui_state =self .load_ui_state (context )
            if not ui_state or not ui_state .is_active :
                self .logger .debug ("No UI state to recover or UI was not active")
                return False 


            target_area =self .find_ui_viewport (context ,ui_state )
            if not target_area :
                self .logger .error ("Could not find target viewport for UI recovery")
                return False 


            self ._configure_ui_viewport (target_area ,ui_state .viewport_config )


            ui_manager .enable_overlay (target_area )


            if hasattr (ui_manager ,'factory')and ui_manager .factory :
                self ._restore_conversation_state (ui_manager .factory ,ui_state .conversation_state )
                if ui_state .current_view !='main':

                    try :
                        from .ui_factory import ViewState 
                        view_state =ViewState (ui_state .current_view )
                        ui_manager .factory .switch_to_view (view_state )
                    except (ValueError ,AttributeError )as e :
                        self .logger .warning (f"Could not restore view '{ui_state.current_view}': {e}")

                        from .ui_factory import ViewState 
                        ui_manager .factory .switch_to_view (ViewState .MAIN )


            self ._mark_ui_area (target_area ,ui_state .viewport_config .area_id )

            self .logger .info (f"UI state recovered successfully on viewport {target_area.width}x{target_area.height}")
            return True 

        except Exception as e :
            self .logger .error (f"Failed to recover UI state: {e}")
            import traceback 
            self .logger .error (traceback .format_exc ())
            return False 

    def clear_ui_state (self ,context ):
        """Clear saved UI state from the scene."""
        try :
            context .scene .vibe4d_ui_active =False 
            context .scene .vibe4d_ui_viewport_config ="{}"
            context .scene .vibe4d_ui_current_view ="main"
            context .scene .vibe4d_ui_conversation_state ="{}"


            self ._clear_all_area_markers (context )

        except Exception as e :
            self .logger .error (f"Failed to clear UI state: {e}")

    def _create_viewport_config (self ,area )->ViewportConfig :
        """Create comprehensive viewport configuration with robust identification."""
        config =ViewportConfig ()


        config .area_id =str (uuid .uuid4 ())


        context =bpy .context 
        screen =context .screen 
        screen_width =sum (a .width for a in screen .areas if a .y ==0 )
        screen_height =sum (a .height for a in screen .areas if a .x ==0 )


        config .width =area .width 
        config .height =area .height 
        config .x =area .x 
        config .y =area .y 
        config .screen_width =screen_width 
        config .screen_height =screen_height 


        if screen_width >0 :
            config .relative_x =area .x /screen_width 
            config .relative_width =area .width /screen_width 
        if screen_height >0 :
            config .relative_y =area .y /screen_height 
            config .relative_height =area .height /screen_height 


        try :
            config .area_index =list (screen .areas ).index (area )
        except ValueError :
            config .area_index =-1 


        fingerprint_data ={
        'type':area .type ,
        'relative_pos':f"{config.relative_x:.3f},{config.relative_y:.3f}",
        'relative_size':f"{config.relative_width:.3f},{config.relative_height:.3f}",
        'area_index':config .area_index ,
        'total_areas':len (screen .areas )
        }
        config .viewport_fingerprint =json .dumps (fingerprint_data ,sort_keys =True )


        neighbors =self ._analyze_area_neighbors (area ,screen .areas )
        config .area_neighbors =json .dumps (neighbors ,sort_keys =True )


        for space in area .spaces :
            if space .type =='VIEW_3D':
                config .show_gizmo =space .show_gizmo 
                config .show_region_ui =space .show_region_ui 
                config .show_region_toolbar =space .show_region_toolbar 
                config .show_region_header =space .show_region_header 
                config .show_region_hud =space .show_region_hud 
                config .show_overlays =space .overlay .show_overlays 
                config .shading_type =space .shading .type 
                config .lens =space .lens 
                config .clip_start =space .clip_start 
                config .clip_end =space .clip_end 
                break 

        return config 

    def _analyze_area_neighbors (self ,target_area ,all_areas )->Dict [str ,Any ]:
        """Analyze neighboring areas for additional viewport identification."""
        neighbors ={
        'left':[],'right':[],'above':[],'below':[],
        'total_count':len (all_areas ),
        'view3d_count':0 
        }

        try :
            for area in all_areas :
                if area ==target_area :
                    continue 


                if area .type =='VIEW_3D':
                    neighbors ['view3d_count']+=1 



                if (area .y <target_area .y +target_area .height and 
                area .y +area .height >target_area .y and 
                area .x +area .width <=target_area .x ):
                    neighbors ['left'].append ({
                    'type':area .type ,
                    'distance':target_area .x -(area .x +area .width )
                    })


                elif (area .y <target_area .y +target_area .height and 
                area .y +area .height >target_area .y and 
                area .x >=target_area .x +target_area .width ):
                    neighbors ['right'].append ({
                    'type':area .type ,
                    'distance':area .x -(target_area .x +target_area .width )
                    })


                elif (area .x <target_area .x +target_area .width and 
                area .x +area .width >target_area .x and 
                area .y +area .height <=target_area .y ):
                    neighbors ['above'].append ({
                    'type':area .type ,
                    'distance':target_area .y -(area .y +area .height )
                    })


                elif (area .x <target_area .x +target_area .width and 
                area .x +area .width >target_area .x and 
                area .y >=target_area .y +target_area .height ):
                    neighbors ['below'].append ({
                    'type':area .type ,
                    'distance':area .y -(target_area .y +target_area .height )
                    })


            for direction in ['left','right','above','below']:
                neighbors [direction ].sort (key =lambda x :x ['distance'])

                neighbors [direction ]=neighbors [direction ][:2 ]

        except Exception as e :
            self .logger .error (f"Error analyzing area neighbors: {e}")

        return neighbors 

    def _configure_ui_viewport (self ,area ,config :ViewportConfig ):
        """Configure viewport for UI display with enhanced Blender 4.4 optimizations."""
        try :
            for space in area .spaces :
                if space .type =='VIEW_3D':

                    space .show_gizmo =False 
                    space .show_region_ui =False 
                    space .show_region_toolbar =False 
                    space .show_region_header =False 
                    space .show_region_hud =False 
                    space .overlay .show_overlays =False 


                    space .shading .type ='SOLID'
                    space .shading .show_xray =False 
                    space .shading .show_shadows =False 
                    space .shading .show_cavity =False 
                    space .shading .show_object_outline =False 
                    space .shading .show_specular_highlight =False 
                    space .shading .show_backface_culling =True 
                    space .shading .use_world_space_lighting =False 


                    if hasattr (space .shading ,'show_cavity_edge'):
                        space .shading .show_cavity_edge =False 
                    if hasattr (space .shading ,'show_cavity_ridge'):
                        space .shading .show_cavity_ridge =False 
                    if hasattr (space .shading ,'show_cavity_valley'):
                        space .shading .show_cavity_valley =False 


                    if hasattr (space ,'show_region_tool_header'):
                        space .show_region_tool_header =False 
                    if hasattr (space ,'show_region_asset_shelf'):
                        space .show_region_asset_shelf =False 


                    space .shading .use_dof =False 
                    if hasattr (space .shading ,'use_world_space_lighting'):
                        space .shading .use_world_space_lighting =False 


                    space .lens =50 
                    space .clip_start =0.1 
                    space .clip_end =100 


                    if hasattr (space ,'use_local_collections'):

                        pass 


                    if hasattr (space .shading ,'light'):
                        space .shading .light ='FLAT'
                    if hasattr (space .shading ,'color_type'):
                        space .shading .color_type ='SINGLE'

                    break 

        except Exception as e :
            self .logger .error (f"Failed to configure UI viewport: {e}")

    def _mark_ui_area (self ,area ,area_id :str ):
        """Mark an area for identification using scene properties."""
        try :

            context =bpy .context 


            markers_json =getattr (context .scene ,'vibe4d_ui_area_markers','{}')
            try :
                markers =json .loads (markers_json )if markers_json else {}
            except json .JSONDecodeError :
                markers ={}


            area_info ={
            'width':area .width ,
            'height':area .height ,
            'x':area .x ,
            'y':area .y ,
            'marked_time':time .time ()
            }

            markers [area_id ]=area_info 
            self ._area_markers [area_id ]=area_info 


            context .scene .vibe4d_ui_area_markers =json .dumps (markers )

            self .logger .debug (f"Marked UI area with ID: {area_id} at {area.width}x{area.height}")

        except Exception as e :
            self .logger .error (f"Failed to mark UI area: {e}")

    def _find_marked_ui_area (self ,context )->Optional [Any ]:
        """Find area marked as UI area using scene properties."""
        try :

            markers_json =getattr (context .scene ,'vibe4d_ui_area_markers','{}')
            try :
                markers =json .loads (markers_json )if markers_json else {}
            except json .JSONDecodeError :
                self .logger .warning ("Failed to parse area markers JSON")
                return None 

            if not markers :
                return None 


            for area in context .screen .areas :
                if area .type =='VIEW_3D':
                    for area_id ,area_info in markers .items ():

                        width_match =abs (area .width -area_info ['width'])<50 
                        height_match =abs (area .height -area_info ['height'])<50 
                        x_match =abs (area .x -area_info ['x'])<50 
                        y_match =abs (area .y -area_info ['y'])<50 

                        if width_match and height_match and x_match and y_match :
                            self .logger .debug (f"Found marked UI area by characteristics: {area.width}x{area.height}")
                            return area 

            return None 

        except Exception as e :
            self .logger .error (f"Error finding marked UI area: {e}")
            return None 

    def _clear_all_area_markers (self ,context ):
        """Clear all UI area markers from scene properties."""
        try :

            context .scene .vibe4d_ui_area_markers ="{}"


            self ._area_markers .clear ()

            self .logger .debug ("Cleared all UI area markers")

        except Exception as e :
            self .logger .error (f"Error clearing area markers: {e}")

    def _extract_conversation_state (self ,factory )->Dict [str ,Any ]:
        """Extract conversation state from UI factory."""
        state ={}
        try :

            current_view =getattr (factory ,'current_view','main')
            if hasattr (current_view ,'value'):
                state ['current_view']=current_view .value 
            else :
                state ['current_view']=str (current_view )


            if hasattr (factory ,'views')and factory .views :
                for view_name ,view in factory .views .items ():
                    if hasattr (view ,'get_persistent_state'):

                        view_key =view_name .value if hasattr (view_name ,'value')else str (view_name )
                        state [f'{view_key}_state']=view .get_persistent_state ()

        except Exception as e :
            self .logger .error (f"Error extracting conversation state: {e}")

        return state 

    def _restore_conversation_state (self ,factory ,state :Dict [str ,Any ]):
        """Restore conversation state to UI factory."""
        try :
            if not state :
                return 


            if hasattr (factory ,'views')and factory .views :
                for view_name ,view in factory .views .items ():
                    if hasattr (view ,'restore_persistent_state'):

                        view_key =view_name .value if hasattr (view_name ,'value')else str (view_name )
                        view_state =state .get (f'{view_key}_state')
                        if view_state :
                            view .restore_persistent_state (view_state )

        except Exception as e :
            self .logger .error (f"Error restoring conversation state: {e}")

    def _find_by_area_index (self ,screen ,config :ViewportConfig )->Optional [Any ]:
        """Try to find viewport by area index (most precise when layout unchanged)."""
        try :
            if config .area_index <0 or config .area_index >=len (screen .areas ):
                return None 

            area =screen .areas [config .area_index ]
            if area .type =='VIEW_3D':

                size_tolerance =0.5 
                if (abs (area .width -config .width )/max (config .width ,1 )<=size_tolerance and 
                abs (area .height -config .height )/max (config .height ,1 )<=size_tolerance ):
                    return area 

            return None 
        except Exception :
            return None 

    def _find_by_relative_position (self ,screen ,config :ViewportConfig )->Optional [Any ]:
        """Try to find viewport by relative position (handles screen size changes)."""
        try :
            if config .relative_x <0 or config .relative_y <0 :
                return None 


            current_screen_width =sum (a .width for a in screen .areas if a .y ==0 )
            current_screen_height =sum (a .height for a in screen .areas if a .x ==0 )

            if current_screen_width <=0 or current_screen_height <=0 :
                return None 


            expected_x =config .relative_x *current_screen_width 
            expected_y =config .relative_y *current_screen_height 
            expected_width =config .relative_width *current_screen_width 
            expected_height =config .relative_height *current_screen_height 

            best_match =None 
            best_score =float ('inf')

            for area in screen .areas :
                if area .type =='VIEW_3D':

                    pos_diff =abs (area .x -expected_x )+abs (area .y -expected_y )
                    size_diff =abs (area .width -expected_width )+abs (area .height -expected_height )


                    score =pos_diff *2 +size_diff 

                    if score <best_score :
                        best_score =score 
                        best_match =area 


            tolerance =min (current_screen_width ,current_screen_height )*0.1 
            if best_match and best_score <tolerance :
                return best_match 

            return None 
        except Exception :
            return None 

    def _find_by_fingerprint (self ,screen ,config :ViewportConfig )->Optional [Any ]:
        """Try to find viewport by fingerprint matching."""
        try :
            if not config .viewport_fingerprint :
                return None 

            saved_fingerprint =json .loads (config .viewport_fingerprint )

            for i ,area in enumerate (screen .areas ):
                if area .type =='VIEW_3D':

                    current_fingerprint ={
                    'type':area .type ,
                    'area_index':i ,
                    'total_areas':len (screen .areas )
                    }


                    screen_width =sum (a .width for a in screen .areas if a .y ==0 )
                    screen_height =sum (a .height for a in screen .areas if a .x ==0 )
                    if screen_width >0 and screen_height >0 :
                        rel_x =area .x /screen_width 
                        rel_y =area .y /screen_height 
                        rel_w =area .width /screen_width 
                        rel_h =area .height /screen_height 
                        current_fingerprint ['relative_pos']=f"{rel_x:.3f},{rel_y:.3f}"
                        current_fingerprint ['relative_size']=f"{rel_w:.3f},{rel_h:.3f}"


                    if (saved_fingerprint .get ('type')==current_fingerprint .get ('type')and 
                    saved_fingerprint .get ('relative_pos')==current_fingerprint .get ('relative_pos')and 
                    saved_fingerprint .get ('relative_size')==current_fingerprint .get ('relative_size')):
                        return area 

            return None 
        except Exception :
            return None 

    def _find_by_neighbors (self ,screen ,config :ViewportConfig )->Optional [Any ]:
        """Try to find viewport by neighbor analysis."""
        try :
            if not config .area_neighbors :
                return None 

            saved_neighbors =json .loads (config .area_neighbors )

            for area in screen .areas :
                if area .type =='VIEW_3D':
                    current_neighbors =self ._analyze_area_neighbors (area ,screen .areas )


                    score =self ._compare_neighbor_patterns (saved_neighbors ,current_neighbors )


                    if score >0.7 :
                        return area 

            return None 
        except Exception :
            return None 

    def _find_by_dimensions (self ,screen ,config :ViewportConfig )->Optional [Any ]:
        """Try to find viewport by dimension matching (old method)."""
        try :
            if config .width <=0 or config .height <=0 :
                return None 

            for area in screen .areas :
                if area .type =='VIEW_3D':

                    width_match =abs (area .width -config .width )<50 
                    height_match =abs (area .height -config .height )<50 
                    position_match =(abs (area .x -config .x )<50 and 
                    abs (area .y -config .y )<50 )

                    if width_match and height_match and position_match :
                        return area 

            return None 
        except Exception :
            return None 

    def _find_any_suitable_viewport (self ,screen )->Optional [Any ]:
        """Last resort: find any suitable 3D viewport."""
        try :
            suitable_areas =[area for area in screen .areas if area .type =='VIEW_3D']

            if suitable_areas :

                suitable_areas .sort (key =lambda a :a .width *a .height )
                return suitable_areas [0 ]

            return None 
        except Exception :
            return None 

    def _compare_neighbor_patterns (self ,saved_neighbors :Dict ,current_neighbors :Dict )->float :
        """Compare neighbor patterns and return similarity score (0-1)."""
        try :
            total_score =0 
            total_weight =0 


            for direction in ['left','right','above','below']:
                saved_count =len (saved_neighbors .get (direction ,[]))
                current_count =len (current_neighbors .get (direction ,[]))

                if saved_count ==0 and current_count ==0 :
                    total_score +=1 
                elif saved_count ==current_count :
                    total_score +=0.5 


                    saved_types =[n .get ('type')for n in saved_neighbors .get (direction ,[])]
                    current_types =[n .get ('type')for n in current_neighbors .get (direction ,[])]

                    if saved_types ==current_types :
                        total_score +=0.5 

                total_weight +=1 


            if (saved_neighbors .get ('total_count')==current_neighbors .get ('total_count')and 
            saved_neighbors .get ('view3d_count')==current_neighbors .get ('view3d_count')):
                total_score +=1 

            total_weight +=1 

            return total_score /total_weight if total_weight >0 else 0 

        except Exception :
            return 0 



ui_state_manager =UIStateManager ()