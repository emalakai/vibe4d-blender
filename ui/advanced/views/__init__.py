"""
View system for different UI pages.
Separates UI logic into distinct view classes for better organization.
"""

from .base_view import BaseView 
from .auth_view import AuthView 
from .main_view import MainView 
from .history_view import HistoryView 
from .settings_view import SettingsView 
from .no_connection_view import NoConnectionView 

__all__ =[
'BaseView',
'AuthView',
'MainView',
'HistoryView',
'SettingsView',
'NoConnectionView',
]