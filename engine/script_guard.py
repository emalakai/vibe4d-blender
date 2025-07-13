"""
Script guard for safe code execution.

Filters malicious imports and validates code before execution.
"""

import ast 
import re 
from typing import List ,Set ,Tuple ,Optional 
import textwrap 

from ..utils .logger import logger 





DANGEROUS_IMPORTS =[
'os',
'shutil',
'subprocess',
'sys',
'pathlib',
'glob',
'tempfile',
'socket',
'http.client',
'http.server',
'ftplib',
'smtplib',
'poplib',
'imaplib',
'telnetlib',
'xmlrpc.client',
'xmlrpc.server',
'urllib',
'webbrowser',
'asyncio',
'ssl',
'multiprocessing',
'threading',
'ctypes',
'runpy',
'importlib',
'marshal',
'pickle',
'shelve',
'resource',
'pwd',
'grp',
'spwd',
'crypt',
'getpass',
'signal',
'platform',
'syslog',
'configparser',
'plistlib',
'zipfile',
'tarfile',
'gzip',
'bz2',
'sqlite3',
'dbm',
'email',
'mimetypes',
'base64',
'binascii',
'hashlib',
'hmac',
'secrets',
'uuid',
'argparse',
'optparse',
'atexit',
'builtins',
'__builtin__',
'__main__'
]


DANGEROUS_FUNCTIONS =[
'exec',
'eval',
'compile',
'open',
'file',
'input',
'raw_input',
'reload',
'vars',
'locals',
'globals',
'dir'
]


DANGEROUS_ATTRIBUTES =[
'__builtins__',
'__globals__',
'__locals__',
'__dict__',
'__class__',
'__bases__',
'__mro__',
'__subclasses__',
'func_globals',
'func_code',
'gi_frame',
'cr_frame'
]


class ScriptGuard :
    """
    Guards against malicious code execution.
    
    Uses a blocklist approach for imports - any module not explicitly listed
    in DANGEROUS_IMPORTS is allowed to be imported. This enables users to
    import common libraries like numpy, scipy, matplotlib, etc. while still
    blocking access to filesystem, network, and system operations.
    """

    def __init__ (self ):
        self .dangerous_imports =set (DANGEROUS_IMPORTS )
        self .dangerous_functions =set (DANGEROUS_FUNCTIONS )
        self .dangerous_attributes =set (DANGEROUS_ATTRIBUTES )

    def validate_code (self ,code :str )->Tuple [bool ,Optional [str ]]:
        """
        Validate code for security issues.
        
        Args:
            code: Python code to validate
            
        Returns:
            Tuple of (is_safe, error_message)
        """
        try :

            tree =ast .parse (code )


            validator =CodeValidator (self )
            validator .visit (tree )

            if validator .violations :
                error_msg =f"Security violations found: {', '.join(validator.violations)}"
                logger .warning (f"Code validation failed: {error_msg}")
                return False ,error_msg 

            logger .debug ("Code validation passed")
            return True ,None 

        except SyntaxError as e :
            error_msg =f"Syntax error: {str(e)}"
            logger .warning (f"Code validation failed: {error_msg}")
            return False ,error_msg 

        except Exception as e :
            error_msg =f"Validation error: {str(e)}"
            logger .error (f"Code validation failed: {error_msg}")
            return False ,error_msg 

    def extract_python_code (self ,text :str )->str :
        """Extract Python code from markdown code blocks while preserving indentation."""
        lines =text .split ('\n')
        code_lines =[]
        in_code_block =False 

        for line in lines :
            if line .strip ().startswith ('```python'):
                in_code_block =True 
                continue 
            elif line .strip ()=='```'and in_code_block :
                in_code_block =False 
                continue 
            elif in_code_block :
                code_lines .append (line )


        if not code_lines :


            return textwrap .dedent (text ).strip ()


        extracted_code ='\n'.join (code_lines )



        dedented_code =textwrap .dedent (extracted_code )


        return dedented_code .rstrip ()


class CodeValidator (ast .NodeVisitor ):
    """AST visitor to validate code for security issues."""

    def __init__ (self ,guard :ScriptGuard ):
        self .guard =guard 
        self .violations =[]

    def visit_Import (self ,node ):
        """Check import statements."""
        for alias in node .names :

            root_module =alias .name .split ('.')[0 ]
            if root_module in self .guard .dangerous_imports :
                self .violations .append (f"Dangerous import: {alias.name}")
        self .generic_visit (node )

    def visit_ImportFrom (self ,node ):
        """Check from...import statements."""
        if node .module :

            root_module =node .module .split ('.')[0 ]
            if root_module in self .guard .dangerous_imports :
                self .violations .append (f"Dangerous import: {node.module}")
        self .generic_visit (node )

    def visit_Call (self ,node ):
        """Check function calls."""

        if isinstance (node .func ,ast .Name ):
            if node .func .id in self .guard .dangerous_functions :
                self .violations .append (f"Dangerous function call: {node.func.id}")


        elif isinstance (node .func ,ast .Attribute ):
            if node .func .attr in self .guard .dangerous_functions :
                self .violations .append (f"Dangerous method call: {node.func.attr}")

        self .generic_visit (node )

    def visit_Attribute (self ,node ):
        """Check attribute access."""
        if node .attr in self .guard .dangerous_attributes :
            self .violations .append (f"Dangerous attribute access: {node.attr}")
        self .generic_visit (node )

    def visit_Exec (self ,node ):
        """Check exec statements (Python 2)."""
        self .violations .append ("Dangerous exec statement")
        self .generic_visit (node )



script_guard =ScriptGuard ()