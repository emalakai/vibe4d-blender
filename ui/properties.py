"""
Essential properties for Vibe4D addon.
Defines only the core properties needed for the advanced UI and addon functionality.
"""

import bpy 
from bpy .props import StringProperty ,BoolProperty ,IntProperty ,EnumProperty ,CollectionProperty ,FloatProperty 
from bpy .types import Scene ,PropertyGroup ,WindowManager 


class VIBE4D_ChatMessage (PropertyGroup ):
    """Individual chat message for conversation history."""

    role :EnumProperty (
    name ="Role",
    description ="Who sent this message",
    items =[
    ('system','System','System message'),
    ('user','User','Message from user'),
    ('assistant','Assistant','Message from AI assistant'),
    ('tool','Tool','Tool response message'),
    ('error','Error','Error message')
    ],
    default ='user'
    )

    content :StringProperty (
    name ="Content",
    description ="Message content",
    default =""
    )

    timestamp :StringProperty (
    name ="Timestamp",
    description ="When this message was created",
    default =""
    )

    message_id :StringProperty (
    name ="Message ID",
    description ="Unique identifier for this message",
    default =""
    )

    chat_id :StringProperty (
    name ="Chat ID",
    description ="Unique identifier for the chat this message belongs to",
    default =""
    )


    tool_calls_json :StringProperty (
    name ="Tool Calls JSON",
    description ="JSON string of tool calls (for assistant messages)",
    default =""
    )


    image_data :StringProperty (
    name ="Image Data",
    description ="Base64 encoded image data URI (for messages with images)",
    default =""
    )


    tool_call_id :StringProperty (
    name ="Tool Call ID",
    description ="ID of the tool call this response corresponds to (for tool messages)",
    default =""
    )


class VIBE4D_CustomInstruction (PropertyGroup ):
    """A custom instruction item."""

    text :StringProperty (
    name ="Instruction",
    description ="Custom instruction text",
    default =""
    )

    enabled :BoolProperty (
    name ="Enabled",
    description ="Whether this instruction is active",
    default =True 
    )


def register_properties ():
    """Register all Vibe4D properties."""


    bpy .utils .register_class (VIBE4D_ChatMessage )
    bpy .utils .register_class (VIBE4D_CustomInstruction )


    Scene .vibe4d_model =StringProperty (
    name ="Model",
    description ="AI model to use for all interactions",
    default ="gpt-4.1-mini"
    )

    Scene .vibe4d_prompt =StringProperty (
    name ="Prompt",
    description ="Current prompt input",
    default =""
    )

    Scene .vibe4d_output_content =StringProperty (
    name ="Output Content",
    description ="Generated output content",
    default =""
    )

    Scene .vibe4d_final_code =StringProperty (
    name ="Final Code",
    description ="Final generated code",
    default =""
    )

    Scene .vibe4d_guide_content =StringProperty (
    name ="Guide Content",
    description ="Generated guide content",
    default =""
    )

    Scene .vibe4d_last_error =StringProperty (
    name ="Last Error",
    description ="Last error message",
    default =""
    )

    Scene .vibe4d_console_output =StringProperty (
    name ="Console Output",
    description ="Console output from code execution",
    default =""
    )

    Scene .vibe4d_is_generating =BoolProperty (
    name ="Is Generating",
    description ="Whether AI is currently generating",
    default =False 
    )

    Scene .vibe4d_execution_pending =BoolProperty (
    name ="Execution Pending",
    description ="Whether code execution is pending",
    default =False 
    )


    Scene .vibe4d_chat_messages =CollectionProperty (
    type =VIBE4D_ChatMessage ,
    name ="Chat Messages",
    description ="Collection of chat messages"
    )

    Scene .vibe4d_chat_messages_index =IntProperty (
    name ="Chat Messages Index",
    description ="Current index in chat messages collection",
    default =0 ,
    min =0 
    )


    Scene .vibe4d_current_chat_id =StringProperty (
    name ="Current Chat ID",
    description ="Current chat identifier",
    default =""
    )


    Scene .vibe4d_current_text_input =StringProperty (
    name ="Current Text Input",
    description ="Current unsent text input",
    default =""
    )


    Scene .vibe4d_custom_instructions =CollectionProperty (
    type =VIBE4D_CustomInstruction ,
    name ="Custom Instructions",
    description ="Collection of custom instructions"
    )

    Scene .vibe4d_custom_instructions_index =IntProperty (
    name ="Custom Instructions Index",
    description ="Current index in custom instructions collection",
    default =0 ,
    min =0 
    )


    Scene .vibe4d_ui_active =BoolProperty (
    name ="UI Active",
    description ="Whether the UI overlay is currently active",
    default =False 
    )

    Scene .vibe4d_ui_viewport_config =StringProperty (
    name ="UI Viewport Config",
    description ="Saved viewport configuration for UI state persistence",
    default ="{}"
    )

    Scene .vibe4d_ui_current_view =StringProperty (
    name ="UI Current View",
    description ="Current view state for UI persistence",
    default ="main"
    )

    Scene .vibe4d_ui_conversation_state =StringProperty (
    name ="UI Conversation State",
    description ="Saved conversation state for UI persistence",
    default ="{}"
    )

    Scene .vibe4d_ui_layout_version =IntProperty (
    name ="UI Layout Version",
    description ="Version of the UI layout for compatibility",
    default =1 
    )

    Scene .vibe4d_ui_area_markers =StringProperty (
    name ="UI Area Markers",
    description ="JSON data for tracking UI area identification",
    default ="{}"
    )


    WindowManager .vibe4d_authenticated =BoolProperty (
    name ="Authenticated",
    description ="Whether user is authenticated",
    default =False 
    )

    WindowManager .vibe4d_user_id =StringProperty (
    name ="User ID",
    description ="Authenticated user ID",
    default =""
    )

    WindowManager .vibe4d_user_token =StringProperty (
    name ="User Token",
    description ="Authentication token",
    default =""
    )

    WindowManager .vibe4d_user_email =StringProperty (
    name ="User Email",
    description ="Authenticated user email",
    default =""
    )

    WindowManager .vibe4d_user_plan =StringProperty (
    name ="User Plan",
    description ="User subscription plan",
    default =""
    )

    WindowManager .vibe4d_status =StringProperty (
    name ="Status",
    description ="Current authentication/connection status",
    default =""
    )

    WindowManager .vibe4d_network_error =BoolProperty (
    name ="Network Error",
    description ="Whether there's a network connectivity issue",
    default =False 
    )


    WindowManager .vibe4d_current_usage =IntProperty (
    name ="Current Usage",
    description ="Current usage count",
    default =0 
    )

    WindowManager .vibe4d_usage_limit =IntProperty (
    name ="Usage Limit",
    description ="Usage limit for current plan",
    default =0 
    )

    WindowManager .vibe4d_limit_type =StringProperty (
    name ="Limit Type",
    description ="Type of usage limit (daily, monthly, etc.)",
    default =""
    )

    WindowManager .vibe4d_plan_id =StringProperty (
    name ="Plan ID",
    description ="Plan identifier",
    default =""
    )

    WindowManager .vibe4d_plan_name =StringProperty (
    name ="Plan Name",
    description ="Plan display name",
    default =""
    )

    WindowManager .vibe4d_allowed =BoolProperty (
    name ="Allowed",
    description ="Whether user is allowed to make requests",
    default =True 
    )

    WindowManager .vibe4d_usage_percentage =FloatProperty (
    name ="Usage Percentage",
    description ="Usage as percentage of limit",
    default =0.0 ,
    min =0.0 ,
    max =100.0 
    )

    WindowManager .vibe4d_remaining_requests =IntProperty (
    name ="Remaining Requests",
    description ="Number of remaining requests",
    default =0 
    )

    WindowManager .vibe4d_remember_credentials =BoolProperty (
    name ="Remember Credentials",
    description ="Remember login credentials",
    default =False 
    )

    WindowManager .vibe4d_ui_was_active =BoolProperty (
    name ="UI Was Active",
    description ="Tracks if UI was previously active for state recovery",
    default =False 
    )


    Scene .vibe4d_generation_progress =IntProperty (
    name ="Generation Progress",
    description ="Current generation progress percentage",
    default =0 ,
    min =0 ,
    max =100 
    )

    Scene .vibe4d_generation_stage =StringProperty (
    name ="Generation Stage",
    description ="Current generation stage description",
    default =""
    )


def unregister_properties ():
    """Unregister all Vibe4D properties."""


    properties_to_remove =[
    'vibe4d_model','vibe4d_prompt','vibe4d_output_content','vibe4d_final_code',
    'vibe4d_guide_content','vibe4d_last_error','vibe4d_console_output',
    'vibe4d_is_generating','vibe4d_execution_pending',
    'vibe4d_chat_messages','vibe4d_chat_messages_index',
    'vibe4d_current_chat_id','vibe4d_current_text_input',
    'vibe4d_custom_instructions','vibe4d_custom_instructions_index',
    'vibe4d_ui_active','vibe4d_ui_viewport_config','vibe4d_ui_current_view',
    'vibe4d_ui_conversation_state','vibe4d_ui_layout_version','vibe4d_ui_area_markers',
    'vibe4d_generation_progress','vibe4d_generation_stage'
    ]

    for prop_name in properties_to_remove :
        if hasattr (Scene ,prop_name ):
            delattr (Scene ,prop_name )


    wm_properties_to_remove =[
    'vibe4d_authenticated','vibe4d_user_id','vibe4d_user_token','vibe4d_user_email',
    'vibe4d_user_plan','vibe4d_status','vibe4d_network_error','vibe4d_current_usage',
    'vibe4d_usage_limit','vibe4d_limit_type','vibe4d_plan_id','vibe4d_plan_name',
    'vibe4d_allowed','vibe4d_usage_percentage','vibe4d_remaining_requests',
    'vibe4d_remember_credentials','vibe4d_ui_was_active'
    ]

    for prop_name in wm_properties_to_remove :
        if hasattr (WindowManager ,prop_name ):
            delattr (WindowManager ,prop_name )


    try :
        bpy .utils .unregister_class (VIBE4D_CustomInstruction )
        bpy .utils .unregister_class (VIBE4D_ChatMessage )
    except :
        pass 