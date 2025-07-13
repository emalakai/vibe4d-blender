"""
Component registry system for better component lifecycle management.
Provides automatic registration, cleanup, and batch operations.
"""

import logging 
from typing import Dict ,List ,Set ,Type ,Optional ,Callable ,Any 
from weakref import WeakSet 
from enum import Enum 

from .base import UIComponent 

logger =logging .getLogger (__name__ )


class ComponentState (Enum ):
    """Component lifecycle states."""
    CREATED ="created"
    MOUNTED ="mounted"
    UPDATED ="updated"
    UNMOUNTED ="unmounted"
    DESTROYED ="destroyed"


class ComponentRegistry :
    """Registry for managing UI component lifecycle."""

    def __init__ (self ):
        self ._components :WeakSet [UIComponent ]=WeakSet ()
        self ._components_by_type :Dict [Type ,List [UIComponent ]]={}
        self ._components_by_id :Dict [str ,UIComponent ]={}
        self ._component_states :Dict [UIComponent ,ComponentState ]={}
        self ._update_queue :Set [UIComponent ]=set ()
        self ._lifecycle_callbacks :Dict [ComponentState ,List [Callable ]]={
        state :[]for state in ComponentState 
        }

    def register (self ,component :UIComponent ,component_id :Optional [str ]=None )->str :
        """Register a component with optional ID."""
        self ._components .add (component )


        comp_type =type (component )
        if comp_type not in self ._components_by_type :
            self ._components_by_type [comp_type ]=[]
        self ._components_by_type [comp_type ].append (component )


        if component_id :
            if component_id in self ._components_by_id :
                logger .warning (f"Component ID '{component_id}' already exists, replacing")
            self ._components_by_id [component_id ]=component 
            final_id =component_id 
        else :

            final_id =f"{comp_type.__name__}_{id(component)}"
            self ._components_by_id [final_id ]=component 


        self ._component_states [component ]=ComponentState .CREATED 
        self ._trigger_lifecycle_callbacks (ComponentState .CREATED ,component )

        return final_id 

    def unregister (self ,component :UIComponent ):
        """Unregister a component."""
        if component not in self ._components :
            return 


        self ._component_states [component ]=ComponentState .DESTROYED 
        self ._trigger_lifecycle_callbacks (ComponentState .DESTROYED ,component )


        self ._components .discard (component )

        comp_type =type (component )
        if comp_type in self ._components_by_type :
            try :
                self ._components_by_type [comp_type ].remove (component )
            except ValueError :
                pass 


        for comp_id ,comp in list (self ._components_by_id .items ()):
            if comp is component :
                del self ._components_by_id [comp_id ]
                break 


        self ._component_states .pop (component ,None )
        self ._update_queue .discard (component )

    def get_by_id (self ,component_id :str )->Optional [UIComponent ]:
        """Get component by ID."""
        return self ._components_by_id .get (component_id )

    def get_by_type (self ,component_type :Type [UIComponent ])->List [UIComponent ]:
        """Get all components of a specific type."""
        return self ._components_by_type .get (component_type ,[]).copy ()

    def get_all (self )->List [UIComponent ]:
        """Get all registered components."""
        return list (self ._components )

    def mark_for_update (self ,component :UIComponent ):
        """Mark a component for update in the next cycle."""
        if component in self ._components :
            self ._update_queue .add (component )

    def process_updates (self ):
        """Process all queued component updates."""
        if not self ._update_queue :
            return 

        for component in list (self ._update_queue ):
            if component in self ._components :
                self ._component_states [component ]=ComponentState .UPDATED 
                self ._trigger_lifecycle_callbacks (ComponentState .UPDATED ,component )


                if hasattr (component ,'update_layout'):
                    try :
                        component .update_layout ()
                    except Exception as e :
                        logger .error (f"Error updating component: {e}")

        self ._update_queue .clear ()

    def cleanup_all (self ):
        """Clean up all registered components."""
        for component in list (self ._components ):
            self .unregister (component )

    def add_lifecycle_callback (self ,state :ComponentState ,callback :Callable ):
        """Add a callback for component lifecycle events."""
        self ._lifecycle_callbacks [state ].append (callback )

    def remove_lifecycle_callback (self ,state :ComponentState ,callback :Callable ):
        """Remove a lifecycle callback."""
        try :
            self ._lifecycle_callbacks [state ].remove (callback )
        except ValueError :
            pass 

    def _trigger_lifecycle_callbacks (self ,state :ComponentState ,component :UIComponent ):
        """Trigger callbacks for a lifecycle state."""
        for callback in self ._lifecycle_callbacks [state ]:
            try :
                callback (component ,state )
            except Exception as e :
                logger .error (f"Error in lifecycle callback: {e}")

    def get_stats (self )->Dict [str ,Any ]:
        """Get registry statistics."""
        return {
        'total_components':len (self ._components ),
        'components_by_type':{
        comp_type .__name__ :len (components )
        for comp_type ,components in self ._components_by_type .items ()
        },
        'pending_updates':len (self ._update_queue ),
        'component_states':{
        state .value :sum (1 for s in self ._component_states .values ()if s ==state )
        for state in ComponentState 
        }
        }



component_registry =ComponentRegistry ()