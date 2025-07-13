"""
Custom instructions operators for Vibe4D addon.

Handles adding, removing, and managing custom instructions with auto-save.
"""

import bpy 
from bpy .types import Operator 
from bpy .props import StringProperty 

from ..utils .logger import logger 
from ..utils .instructions_manager import instructions_manager 


def get_instructions_properties ():
    """Get the unified custom instructions properties."""
    return "vibe4d_custom_instructions","vibe4d_custom_instructions_index"


class VIBE4D_OT_add_empty_instruction (Operator ):
    """Add new empty custom instruction and select it."""

    bl_idname ="vibe4d.add_empty_instruction"
    bl_label ="Add Empty Instruction"
    bl_description ="Add a new empty custom instruction"
    bl_options ={'REGISTER','UNDO'}

    def execute (self ,context ):
        """Add new empty instruction."""
        try :

            instructions_prop ,index_prop =get_instructions_properties ()


            instructions =getattr (context .scene ,instructions_prop )
            new_instruction =instructions .add ()
            new_instruction .text =""
            new_instruction .enabled =True 


            setattr (context .scene ,index_prop ,len (instructions )-1 )


            instructions_manager .auto_save_instructions (context )

            logger .info ("Added new empty custom instruction")
            self .report ({'INFO'},"Empty instruction added")
            return {'FINISHED'}

        except Exception as e :
            logger .error (f"Failed to add instruction: {str(e)}")
            self .report ({'ERROR'},f"Failed to add instruction: {str(e)}")
            return {'CANCELLED'}


class VIBE4D_OT_add_instruction (Operator ):
    """Add new custom instruction."""

    bl_idname ="vibe4d.add_instruction"
    bl_label ="Add Instruction"
    bl_description ="Add a new custom instruction"
    bl_options ={'REGISTER','UNDO'}

    def execute (self ,context ):
        """Add new instruction."""
        try :
            new_text =context .scene .vibe4d_new_instruction .strip ()

            if not new_text :
                self .report ({'WARNING'},"Please enter instruction text")
                return {'CANCELLED'}


            instructions_prop ,index_prop =get_instructions_properties ()


            instructions =getattr (context .scene ,instructions_prop )
            new_instruction =instructions .add ()
            new_instruction .text =new_text 
            new_instruction .enabled =True 


            setattr (context .scene ,index_prop ,len (instructions )-1 )


            context .scene .vibe4d_new_instruction =""


            instructions_manager .auto_save_instructions (context )

            logger .info (f"Added custom instruction: {new_text[:50]}...")
            self .report ({'INFO'},"Instruction added")
            return {'FINISHED'}

        except Exception as e :
            logger .error (f"Failed to add instruction: {str(e)}")
            self .report ({'ERROR'},f"Failed to add instruction: {str(e)}")
            return {'CANCELLED'}


class VIBE4D_OT_remove_instruction (Operator ):
    """Remove selected custom instruction."""

    bl_idname ="vibe4d.remove_instruction"
    bl_label ="Remove Instruction"
    bl_description ="Remove the selected custom instruction"
    bl_options ={'REGISTER','UNDO'}

    def execute (self ,context ):
        """Remove selected instruction."""
        try :

            instructions_prop ,index_prop =get_instructions_properties ()

            instructions =getattr (context .scene ,instructions_prop )
            index =getattr (context .scene ,index_prop )

            if not instructions or index <0 or index >=len (instructions ):
                self .report ({'WARNING'},"No instruction selected")
                return {'CANCELLED'}


            instruction_text =instructions [index ].text 


            instructions .remove (index )


            if index >=len (instructions )>0 :
                setattr (context .scene ,index_prop ,len (instructions )-1 )
            elif len (instructions )==0 :
                setattr (context .scene ,index_prop ,0 )


            instructions_manager .auto_save_instructions (context )

            logger .info (f"Removed custom instruction: {instruction_text[:50]}...")
            self .report ({'INFO'},"Instruction removed")
            return {'FINISHED'}

        except Exception as e :
            logger .error (f"Failed to remove instruction: {str(e)}")
            self .report ({'ERROR'},f"Failed to remove instruction: {str(e)}")
            return {'CANCELLED'}


class VIBE4D_OT_move_instruction (Operator ):
    """Move custom instruction up or down."""

    bl_idname ="vibe4d.move_instruction"
    bl_label ="Move Instruction"
    bl_description ="Move the selected instruction up or down"
    bl_options ={'REGISTER','UNDO'}

    direction :StringProperty (
    name ="Direction",
    description ="Direction to move (UP or DOWN)",
    default ="UP"
    )

    def execute (self ,context ):
        """Move instruction."""
        try :

            instructions_prop ,index_prop =get_instructions_properties ()

            instructions =getattr (context .scene ,instructions_prop )
            index =getattr (context .scene ,index_prop )

            if not instructions or index <0 or index >=len (instructions ):
                self .report ({'WARNING'},"No instruction selected")
                return {'CANCELLED'}

            if self .direction =="UP"and index >0 :

                instructions .move (index ,index -1 )
                setattr (context .scene ,index_prop ,index -1 )

                instructions_manager .auto_save_instructions (context )
                self .report ({'INFO'},"Instruction moved up")

            elif self .direction =="DOWN"and index <len (instructions )-1 :

                instructions .move (index ,index +1 )
                setattr (context .scene ,index_prop ,index +1 )

                instructions_manager .auto_save_instructions (context )
                self .report ({'INFO'},"Instruction moved down")

            else :
                self .report ({'WARNING'},"Cannot move instruction in that direction")
                return {'CANCELLED'}

            return {'FINISHED'}

        except Exception as e :
            logger .error (f"Failed to move instruction: {str(e)}")
            self .report ({'ERROR'},f"Failed to move instruction: {str(e)}")
            return {'CANCELLED'}


class VIBE4D_OT_clear_instruction (Operator ):
    """Clear selected custom instruction text."""

    bl_idname ="vibe4d.clear_instruction"
    bl_label ="Clear Instruction"
    bl_description ="Clear the text of the selected instruction"
    bl_options ={'REGISTER','UNDO'}

    def execute (self ,context ):
        """Clear instruction text."""
        try :

            instructions_prop ,index_prop =get_instructions_properties ()

            instructions =getattr (context .scene ,instructions_prop )
            index =getattr (context .scene ,index_prop )

            if not instructions or index <0 or index >=len (instructions ):
                self .report ({'WARNING'},"No instruction selected")
                return {'CANCELLED'}


            instructions [index ].text =""


            instructions_manager .auto_save_instructions (context )

            logger .info ("Cleared custom instruction text")
            self .report ({'INFO'},"Instruction text cleared")
            return {'FINISHED'}

        except Exception as e :
            logger .error (f"Failed to clear instruction: {str(e)}")
            self .report ({'ERROR'},f"Failed to clear instruction: {str(e)}")
            return {'CANCELLED'}


class VIBE4D_OT_enable_all_instructions (Operator ):
    """Enable all custom instructions."""

    bl_idname ="vibe4d.enable_all_instructions"
    bl_label ="Enable All Instructions"
    bl_description ="Enable all custom instructions"
    bl_options ={'REGISTER','UNDO'}

    def execute (self ,context ):
        """Enable all instructions."""
        try :

            instructions_prop ,_ =get_instructions_properties ()

            instructions =getattr (context .scene ,instructions_prop )

            if not instructions :
                self .report ({'INFO'},"No instructions to enable")
                return {'FINISHED'}


            for instruction in instructions :
                instruction .enabled =True 


            instructions_manager .auto_save_instructions (context )

            logger .info ("Enabled all custom instructions")
            self .report ({'INFO'},f"Enabled {len(instructions)} instructions")
            return {'FINISHED'}

        except Exception as e :
            logger .error (f"Failed to enable all instructions: {str(e)}")
            self .report ({'ERROR'},f"Failed to enable instructions: {str(e)}")
            return {'CANCELLED'}


class VIBE4D_OT_disable_all_instructions (Operator ):
    """Disable all custom instructions."""

    bl_idname ="vibe4d.disable_all_instructions"
    bl_label ="Disable All Instructions"
    bl_description ="Disable all custom instructions"
    bl_options ={'REGISTER','UNDO'}

    def execute (self ,context ):
        """Disable all instructions."""
        try :

            instructions_prop ,_ =get_instructions_properties ()

            instructions =getattr (context .scene ,instructions_prop )

            if not instructions :
                self .report ({'INFO'},"No instructions to disable")
                return {'FINISHED'}


            for instruction in instructions :
                instruction .enabled =False 


            instructions_manager .auto_save_instructions (context )

            logger .info ("Disabled all custom instructions")
            self .report ({'INFO'},f"Disabled {len(instructions)} instructions")
            return {'FINISHED'}

        except Exception as e :
            logger .error (f"Failed to disable all instructions: {str(e)}")
            self .report ({'ERROR'},f"Failed to disable instructions: {str(e)}")
            return {'CANCELLED'}


class VIBE4D_OT_clear_all_instructions (Operator ):
    """Clear all custom instructions."""

    bl_idname ="vibe4d.clear_all_instructions"
    bl_label ="Clear All Instructions"
    bl_description ="Remove all custom instructions"
    bl_options ={'REGISTER','UNDO'}

    def invoke (self ,context ,event ):
        """Show confirmation dialog."""
        return context .window_manager .invoke_confirm (self ,event )

    def execute (self ,context ):
        """Clear all instructions."""
        try :

            instructions_prop ,index_prop =get_instructions_properties ()

            instructions =getattr (context .scene ,instructions_prop )

            if not instructions :
                self .report ({'INFO'},"No instructions to clear")
                return {'FINISHED'}

            instruction_count =len (instructions )


            instructions .clear ()
            setattr (context .scene ,index_prop ,0 )


            instructions_manager .auto_save_instructions (context )

            logger .info ("Cleared all custom instructions")
            self .report ({'INFO'},f"Cleared {instruction_count} instructions")
            return {'FINISHED'}

        except Exception as e :
            logger .error (f"Failed to clear all instructions: {str(e)}")
            self .report ({'ERROR'},f"Failed to clear instructions: {str(e)}")
            return {'CANCELLED'}


class VIBE4D_OT_save_instructions (Operator ):
    """Manually save custom instructions (for testing)."""

    bl_idname ="vibe4d.save_instructions"
    bl_label ="Save Instructions"
    bl_description ="Manually save custom instructions to persistent storage"
    bl_options ={'REGISTER'}

    def execute (self ,context ):
        """Save instructions to storage."""
        try :
            success =instructions_manager .save_instructions (context )

            if success :
                logger .info ("Manually saved custom instructions")
                self .report ({'INFO'},"Instructions saved to storage")
                return {'FINISHED'}
            else :
                self .report ({'ERROR'},"Failed to save instructions")
                return {'CANCELLED'}

        except Exception as e :
            logger .error (f"Manual save instructions failed: {str(e)}")
            self .report ({'ERROR'},f"Save failed: {str(e)}")
            return {'CANCELLED'}


class VIBE4D_OT_load_instructions (Operator ):
    """Manually load custom instructions (for testing)."""

    bl_idname ="vibe4d.load_instructions"
    bl_label ="Load Instructions"
    bl_description ="Manually load custom instructions from persistent storage"
    bl_options ={'REGISTER'}

    def execute (self ,context ):
        """Load instructions from storage."""
        try :
            success =instructions_manager .initialize_instructions (context )

            if success :
                logger .info ("Manually loaded custom instructions")
                self .report ({'INFO'},"Instructions loaded from storage")
                return {'FINISHED'}
            else :
                self .report ({'ERROR'},"Failed to load instructions")
                return {'CANCELLED'}

        except Exception as e :
            logger .error (f"Manual load instructions failed: {str(e)}")
            self .report ({'ERROR'},f"Load failed: {str(e)}")
            return {'CANCELLED'}



classes =[
VIBE4D_OT_add_empty_instruction ,
VIBE4D_OT_add_instruction ,
VIBE4D_OT_remove_instruction ,
VIBE4D_OT_move_instruction ,
VIBE4D_OT_clear_instruction ,
VIBE4D_OT_enable_all_instructions ,
VIBE4D_OT_disable_all_instructions ,
VIBE4D_OT_clear_all_instructions ,
VIBE4D_OT_save_instructions ,
VIBE4D_OT_load_instructions ,
]