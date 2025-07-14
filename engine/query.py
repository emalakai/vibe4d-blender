"""
Query module for scene data querying.

Implements SQL-like query functionality over Blender scene data.
Supports SELECT statements with WHERE clauses, ORDER BY, DISTINCT, aggregates, and LIMIT.
"""

import bpy 
import re 
import csv 
import io 
import json 
from typing import Dict ,Any ,List ,Optional ,Union ,Tuple 
from abc import ABC ,abstractmethod 
from collections import defaultdict 
from mathutils import Vector ,Matrix ,Euler ,Quaternion ,Color 

from ..utils .json_utils import to_json_serializable 


class DataFormatter (ABC ):
    """Abstract base class for data formatters."""

    @abstractmethod 
    def format (self ,data :List [Dict [str ,Any ]])->Any :
        """Format data to specific output format."""
        pass 


class JSONFormatter (DataFormatter ):
    """Format data as JSON."""

    def format (self ,data :List [Dict [str ,Any ]])->List [Dict [str ,Any ]]:
        """Return data as-is for JSON format."""
        return data 


class CSVFormatter (DataFormatter ):
    """Format data as CSV string."""

    def format (self ,data :List [Dict [str ,Any ]])->str :
        """Convert data to CSV format."""
        if not data :
            return ""

        output =io .StringIO ()
        fieldnames =list (data [0 ].keys ())
        writer =csv .DictWriter (output ,fieldnames =fieldnames )

        writer .writeheader ()
        for row in data :

            csv_row ={}
            for key ,value in row .items ():
                if isinstance (value ,(list ,dict )):
                    csv_row [key ]=json .dumps (value )
                elif value is None :
                    csv_row [key ]=""
                elif isinstance (value ,float ):

                    csv_row [key ]=round (value ,6 )
                else :
                    csv_row [key ]=str (value )
            writer .writerow (csv_row )

        return output .getvalue ()


class TableFormatter (DataFormatter ):
    """Format data as ASCII table."""

    def format (self ,data :List [Dict [str ,Any ]])->str :
        """Convert data to ASCII table format."""
        if not data :
            return "No data"


        fieldnames =list (data [0 ].keys ())


        widths ={}
        for field in fieldnames :
            widths [field ]=len (field )
            for row in data :
                value =row .get (field ,"")
                if isinstance (value ,(list ,dict )):
                    value =json .dumps (value )
                elif isinstance (value ,float ):
                    value =round (value ,6 )
                widths [field ]=max (widths [field ],len (str (value )))


        lines =[]


        header =" | ".join (field .ljust (widths [field ])for field in fieldnames )
        lines .append (header )
        lines .append ("-"*len (header ))


        for row in data :
            row_values =[]
            for field in fieldnames :
                value =row .get (field ,"")
                if isinstance (value ,(list ,dict )):
                    value =json .dumps (value )
                elif isinstance (value ,float ):
                    value =round (value ,6 )
                row_values .append (str (value ).ljust (widths [field ]))
            lines .append (" | ".join (row_values ))

        return "\n".join (lines )


class FormatFactory :
    """Factory for creating data formatters."""

    _formatters ={
    'json':JSONFormatter ,
    'csv':CSVFormatter ,
    'table':TableFormatter 
    }

    @classmethod 
    def create_formatter (cls ,format_type :str )->DataFormatter :
        """Create formatter for specified format."""
        format_type =format_type .lower ()
        if format_type not in cls ._formatters :
            available =', '.join (cls ._formatters .keys ())
            raise ValueError (f"Unknown format: {format_type}. Available formats: {available}")

        return cls ._formatters [format_type ]()

    @classmethod 
    def get_available_formats (cls )->List [str ]:
        """Get list of available formats."""
        return list (cls ._formatters .keys ())


class QueryResponse :
    """Standardized query response wrapper."""

    def __init__ (self ,status :str ,data :Any =None ,error :str =None ,
    count :int =0 ,format_type :str ="json"):
        self .status =status 
        self .data =data 
        self .error =error 
        self .count =count 
        self .format_type =format_type 

    def to_dict (self )->Dict [str ,Any ]:
        """Convert response to dictionary."""
        response ={
        "status":self .status ,
        "format":self .format_type ,
        "count":self .count 
        }

        if self .status =="success":
            response ["data"]=self .data 
        else :
            response ["error"]=self .error 

        return response 


class WhereCondition :
    """Represents a single WHERE condition with enhanced operator support."""

    def __init__ (self ,field :str ,operator :str ,value :Any ):
        self .field =field 
        self .operator =operator .upper ()
        self .value =value 
        self .negated =False 

    def evaluate (self ,item :Dict [str ,Any ])->bool :
        """Evaluate condition against an item with comprehensive operator support."""

        if '.'in self .field :
            field_parts =self .field .split ('.')
            current_value =item 


            for part in field_parts :
                if isinstance (current_value ,dict )and part in current_value :
                    current_value =current_value [part ]
                else :

                    if self .operator in ('IS','IS NOT'):
                        current_value =None 
                        break 
                    else :
                        result =False 
                        return not result if self .negated else result 

            item_value =current_value 
        else :

            if self .field not in item :

                if self .operator in ('IS','IS NOT'):
                    item_value =None 
                else :
                    result =False 
                    return not result if self .negated else result 
            else :
                item_value =item [self .field ]


        try :
            if self .operator not in ('IS','IS NOT','IN','NOT IN','BETWEEN','NOT BETWEEN'):
                if isinstance (item_value ,(int ,float ))and isinstance (self .value ,str ):

                    try :
                        if '.'in str (self .value )or 'e'in str (self .value ).lower ():
                            self .value =float (self .value )
                        else :
                            self .value =int (self .value )
                    except ValueError :
                        pass 
                elif isinstance (item_value ,bool )and isinstance (self .value ,str ):
                    self .value =self .value .lower ()in ['true','1','yes','on']
                elif isinstance (item_value ,str )and isinstance (self .value ,(int ,float )):

                    item_value =str (item_value )
        except Exception :
            pass 


        result =False 

        if self .operator =='=':
            result =item_value ==self .value 
        elif self .operator in ('!=','<>'):
            result =item_value !=self .value 
        elif self .operator =='>':
            try :
                result =item_value >self .value 
            except TypeError :
                result =str (item_value )>str (self .value )
        elif self .operator =='<':
            try :
                result =item_value <self .value 
            except TypeError :
                result =str (item_value )<str (self .value )
        elif self .operator =='>=':
            try :
                result =item_value >=self .value 
            except TypeError :
                result =str (item_value )>=str (self .value )
        elif self .operator =='<=':
            try :
                result =item_value <=self .value 
            except TypeError :
                result =str (item_value )<=str (self .value )
        elif self .operator =='LIKE':
            pattern =str (self .value ).replace ('%','.*').replace ('_','.')
            result =bool (re .search (pattern ,str (item_value ),re .IGNORECASE ))
        elif self .operator =='NOT LIKE':
            pattern =str (self .value ).replace ('%','.*').replace ('_','.')
            result =not bool (re .search (pattern ,str (item_value ),re .IGNORECASE ))
        elif self .operator =='ILIKE':

            pattern =str (self .value ).replace ('%','.*').replace ('_','.')
            result =bool (re .search (pattern ,str (item_value ),re .IGNORECASE ))
        elif self .operator =='NOT ILIKE':
            pattern =str (self .value ).replace ('%','.*').replace ('_','.')
            result =not bool (re .search (pattern ,str (item_value ),re .IGNORECASE ))
        elif self .operator =='IN':
            if isinstance (self .value ,(list ,tuple )):
                result =item_value in self .value 
            else :
                result =False 
        elif self .operator =='NOT IN':
            if isinstance (self .value ,(list ,tuple )):
                result =item_value not in self .value 
            else :
                result =True 
        elif self .operator =='IS':
            if self .value is None :
                result =item_value is None 
            else :
                result =item_value ==self .value 
        elif self .operator =='IS NOT':
            if self .value is None :
                result =item_value is not None 
            else :
                result =item_value !=self .value 
        elif self .operator =='BETWEEN':
            if isinstance (self .value ,(list ,tuple ))and len (self .value )==2 :
                try :
                    result =self .value [0 ]<=item_value <=self .value [1 ]
                except TypeError :

                    result =str (self .value [0 ])<=str (item_value )<=str (self .value [1 ])
            else :
                result =False 
        elif self .operator =='NOT BETWEEN':
            if isinstance (self .value ,(list ,tuple ))and len (self .value )==2 :
                try :
                    result =not (self .value [0 ]<=item_value <=self .value [1 ])
                except TypeError :

                    result =not (str (self .value [0 ])<=str (item_value )<=str (self .value [1 ]))
            else :
                result =True 


        return not result if self .negated else result 


class WhereExpression :
    """Represents a WHERE expression with AND/OR logic and enhanced parsing."""

    def __init__ (self ):
        self .conditions =[]
        self .operators =[]
        self .negated =False 

    def add_condition (self ,condition :WhereCondition ,operator :str =None ):
        """Add a condition with optional logical operator."""
        self .conditions .append (condition )


        if operator :
            self .operators .append (operator .upper ())

    def evaluate (self ,item :Dict [str ,Any ])->bool :
        """Evaluate all conditions against an item."""
        if not self .conditions :
            result =True 
        else :
            result =self .conditions [0 ].evaluate (item )

            for i ,operator in enumerate (self .operators ):
                next_result =self .conditions [i +1 ].evaluate (item )
                if operator =='AND':
                    result =result and next_result 
                elif operator =='OR':
                    result =result or next_result 


        return not result if self .negated else result 


class AggregateFunction :
    """Handles aggregate functions with enhanced support for statistical functions."""

    @staticmethod 
    def apply (func_name :str ,field :str ,data :List [Dict [str ,Any ]])->Any :
        """Apply aggregate function to data with comprehensive function support."""
        func_name =func_name .upper ()

        def get_field_value (item ,field ):
            """Extract field value, handling nested fields."""
            if '.'in field :

                field_parts =field .split ('.')
                current_value =item 


                for part in field_parts :
                    if isinstance (current_value ,dict )and part in current_value :
                        current_value =current_value [part ]
                    else :
                        return None 

                return current_value 
            else :

                return item .get (field ,None )

        if func_name =='COUNT':
            if field =='*':
                return len (data )
            else :
                return len ([item for item in data if get_field_value (item ,field )is not None ])


        values =[]
        for item in data :
            value =get_field_value (item ,field )
            if value is not None :
                try :
                    if isinstance (value ,(int ,float )):
                        values .append (float (value ))
                    elif isinstance (value ,str ):

                        try :
                            if '.'in value or 'e'in value .lower ():
                                values .append (float (value ))
                            else :
                                values .append (float (int (value )))
                        except ValueError :

                            continue 
                    elif isinstance (value ,bool ):
                        values .append (float (value ))
                except (ValueError ,TypeError ):
                    continue 

        if not values :
            return None 

        try :
            if func_name =='SUM':
                return sum (values )
            elif func_name =='AVG':
                return sum (values )/len (values )
            elif func_name =='MIN':
                return min (values )
            elif func_name =='MAX':
                return max (values )
            elif func_name =='STDDEV':

                if len (values )<2 :
                    return 0.0 
                mean =sum (values )/len (values )
                variance =sum ((x -mean )**2 for x in values )/(len (values )-1 )
                return variance **0.5 
            elif func_name =='VARIANCE':

                if len (values )<2 :
                    return 0.0 
                mean =sum (values )/len (values )
                return sum ((x -mean )**2 for x in values )/(len (values )-1 )
            else :
                raise ValueError (f"Unsupported aggregate function: {func_name}")

        except Exception as e :
            raise ValueError (f"Error calculating {func_name}: {str(e)}")

        return None 


class QueryParser :
    """Enhanced and robust SQL-like query parser."""


    OPERATORS ={
    'OR':1 ,
    'AND':2 ,
    'NOT':3 ,
    'IN':4 ,'NOT IN':4 ,
    'LIKE':4 ,'NOT LIKE':4 ,'ILIKE':4 ,'NOT ILIKE':4 ,
    'IS':4 ,'IS NOT':4 ,
    'BETWEEN':4 ,'NOT BETWEEN':4 ,
    '=':5 ,'!=':5 ,'<>':5 ,
    '<':5 ,'<=':5 ,'>':5 ,'>=':5 
    }


    NULL_OPERATORS ={'IS','IS NOT'}

    @staticmethod 
    def parse_select (query :str )->Tuple [List [str ],bool ,Dict [str ,str ],Dict [str ,str ]]:
        """Parse SELECT clause, return (fields, distinct, aggregates, aliases)."""
        try :
            select_match =re .search (r'SELECT\s+(.*?)\s+FROM',query ,re .IGNORECASE |re .DOTALL )
            if not select_match :
                raise ValueError ("Invalid SELECT clause. Expected format: SELECT fields FROM table")

            select_clause =select_match .group (1 ).strip ()
            if not select_clause :
                raise ValueError ("Empty SELECT clause")

            distinct =select_clause .upper ().startswith ('DISTINCT')

            if distinct :
                select_clause =select_clause [8 :].strip ()
                if not select_clause :
                    raise ValueError ("Empty field list after DISTINCT")


            aggregates ={}
            aliases ={}
            fields =[]


            field_parts =QueryParser ._split_select_fields (select_clause )

            for field in field_parts :
                field =field .strip ()
                if not field :
                    continue 


                alias_match =re .search (r'(.+?)\s+AS\s+([a-zA-Z_][a-zA-Z0-9_]*)',field ,re .IGNORECASE )
                if alias_match :
                    original_field =alias_match .group (1 ).strip ()
                    alias_name =alias_match .group (2 ).strip ()


                    agg_match =re .match (r'(COUNT|SUM|AVG|MIN|MAX|STDDEV|VARIANCE)\s*\(\s*(.*?)\s*\)',original_field ,re .IGNORECASE )
                    if agg_match :
                        func_name =agg_match .group (1 ).upper ()
                        field_name =agg_match .group (2 ).strip ()
                        if field_name =='*'and func_name !='COUNT':
                            raise ValueError (f"Function {func_name} cannot be used with *")
                        aggregates [alias_name ]=(func_name ,field_name )
                        aliases [alias_name ]=f"{func_name}({field_name})"
                    else :
                        aliases [alias_name ]=original_field 

                    fields .append (alias_name )
                else :

                    agg_match =re .match (r'(COUNT|SUM|AVG|MIN|MAX|STDDEV|VARIANCE)\s*\(\s*(.*?)\s*\)',field ,re .IGNORECASE )
                    if agg_match :
                        func_name =agg_match .group (1 ).upper ()
                        field_name =agg_match .group (2 ).strip ()
                        if field_name =='*'and func_name !='COUNT':
                            raise ValueError (f"Function {func_name} cannot be used with *")
                        alias =f"{func_name}({field_name})"
                        aggregates [alias ]=(func_name ,field_name )
                        fields .append (alias )
                    else :

                        if not QueryParser ._is_valid_field_name (field ):
                            raise ValueError (f"Invalid field name: {field}")
                        fields .append (field )

            if not fields :
                raise ValueError ("No valid fields found in SELECT clause")

            return fields ,distinct ,aggregates ,aliases 

        except Exception as e :
            raise ValueError (f"Error parsing SELECT clause: {str(e)}")

    @staticmethod 
    def _split_select_fields (select_clause :str )->List [str ]:
        """Split SELECT fields respecting parentheses and quoted strings."""
        fields =[]
        current_field =""
        paren_depth =0 
        in_quotes =False 
        quote_char =None 

        i =0 
        while i <len (select_clause ):
            char =select_clause [i ]

            if char in ('"',"'")and not in_quotes :
                in_quotes =True 
                quote_char =char 
                current_field +=char 
            elif char ==quote_char and in_quotes :

                if i +1 <len (select_clause )and select_clause [i +1 ]==quote_char :
                    current_field +=char *2 
                    i +=1 
                else :
                    in_quotes =False 
                    quote_char =None 
                    current_field +=char 
            elif not in_quotes :
                if char =='(':
                    paren_depth +=1 
                    current_field +=char 
                elif char ==')':
                    paren_depth -=1 
                    current_field +=char 
                elif char ==','and paren_depth ==0 :
                    fields .append (current_field .strip ())
                    current_field =""
                else :
                    current_field +=char 
            else :
                current_field +=char 

            i +=1 

        if current_field .strip ():
            fields .append (current_field .strip ())

        if paren_depth !=0 :
            raise ValueError ("Mismatched parentheses in SELECT clause")

        if in_quotes :
            raise ValueError (f"Unclosed quote in SELECT clause")

        return fields 

    @staticmethod 
    def _is_valid_field_name (field :str )->bool :
        """Check if field name is valid."""
        if not field or field =='*':
            return field =='*'


        if (field .startswith ('"')and field .endswith ('"'))or (field .startswith ("'")and field .endswith ("'")):
            inner =field [1 :-1 ]
            return len (inner )>0 and not inner .count (field [0 ])>0 


        return re .match (r'^[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*$',field )is not None 

    @staticmethod 
    def parse_where (where_str :str )->'WhereExpression':
        """Parse WHERE clause with simplified but working logic."""
        if not where_str or not where_str .strip ():
            return WhereExpression ()

        where_str =where_str .strip ()
        expression =WhereExpression ()



        conditions_with_ops =QueryParser ._split_where_conditions (where_str )

        for i ,(condition_str ,operator )in enumerate (conditions_with_ops ):
            condition_str =condition_str .strip ()
            if condition_str :
                try :
                    condition =QueryParser ._parse_condition (condition_str )
                    expression .conditions .append (condition )

                    if operator and i <len (conditions_with_ops )-1 :
                        expression .operators .append (operator )
                except Exception as e :
                    raise ValueError (f"Error parsing condition '{condition_str}': {str(e)}")

        return expression 

    @staticmethod 
    def _split_where_conditions (where_str :str )->List [Tuple [str ,str ]]:
        """Split WHERE string into conditions and operators, respecting quotes."""
        conditions_with_ops =[]
        current_condition =""
        i =0 

        while i <len (where_str ):
            char =where_str [i ]


            if char in ('"',"'"):
                quote_char =char 
                current_condition +=char 
                i +=1 


                while i <len (where_str ):
                    char =where_str [i ]
                    current_condition +=char 
                    if char ==quote_char :

                        if i +1 <len (where_str )and where_str [i +1 ]==quote_char :
                            i +=2 
                            current_condition +=quote_char 
                        else :
                            i +=1 
                            break 
                    else :
                        i +=1 
                continue 


            if i +3 <=len (where_str )and where_str [i :i +3 ].upper ()=='AND':

                if (i ==0 or where_str [i -1 ].isspace ())and (i +3 >=len (where_str )or where_str [i +3 ].isspace ()):
                    conditions_with_ops .append ((current_condition .strip (),'AND'))
                    current_condition =""
                    i +=3 

                    while i <len (where_str )and where_str [i ].isspace ():
                        i +=1 
                    continue 
            elif i +2 <=len (where_str )and where_str [i :i +2 ].upper ()=='OR':

                if (i ==0 or where_str [i -1 ].isspace ())and (i +2 >=len (where_str )or where_str [i +2 ].isspace ()):
                    conditions_with_ops .append ((current_condition .strip (),'OR'))
                    current_condition =""
                    i +=2 

                    while i <len (where_str )and where_str [i ].isspace ():
                        i +=1 
                    continue 

            current_condition +=char 
            i +=1 


        if current_condition .strip ():
            conditions_with_ops .append ((current_condition .strip (),None ))

        return conditions_with_ops 

    @staticmethod 
    def parse_order_by (query :str )->List [Tuple [str ,str ]]:
        """Parse ORDER BY clause with enhanced validation."""
        order_match =re .search (r'ORDER\s+BY\s+(.*?)(?:\s+LIMIT|\s*$)',query ,re .IGNORECASE )
        if not order_match :
            return []

        try :
            order_clause =order_match .group (1 ).strip ()
            if not order_clause :
                raise ValueError ("Empty ORDER BY clause")

            order_fields =[]


            field_parts =QueryParser ._split_order_fields (order_clause )

            for field_spec in field_parts :
                field_spec =field_spec .strip ()
                if not field_spec :
                    continue 

                parts =field_spec .split ()

                if len (parts )==1 :
                    field_name =parts [0 ]
                    direction ='ASC'
                elif len (parts )==2 :
                    field_name =parts [0 ]
                    direction =parts [1 ].upper ()
                    if direction not in ('ASC','DESC'):
                        raise ValueError (f"Invalid sort direction: {direction}. Use ASC or DESC")
                else :
                    raise ValueError (f"Invalid ORDER BY specification: {field_spec}")

                if not QueryParser ._is_valid_field_name (field_name )and field_name !='*':
                    raise ValueError (f"Invalid field name in ORDER BY: {field_name}")

                order_fields .append ((field_name ,direction ))

            return order_fields 

        except Exception as e :
            raise ValueError (f"Error parsing ORDER BY clause: {str(e)}")

    @staticmethod 
    def _split_order_fields (order_clause :str )->List [str ]:
        """Split ORDER BY fields respecting function calls."""
        fields =[]
        current_field =""
        paren_depth =0 
        in_quotes =False 
        quote_char =None 

        for char in order_clause :
            if char in ('"',"'")and not in_quotes :
                in_quotes =True 
                quote_char =char 
                current_field +=char 
            elif char ==quote_char and in_quotes :
                in_quotes =False 
                quote_char =None 
                current_field +=char 
            elif not in_quotes :
                if char =='(':
                    paren_depth +=1 
                    current_field +=char 
                elif char ==')':
                    paren_depth -=1 
                    current_field +=char 
                elif char ==','and paren_depth ==0 :
                    fields .append (current_field .strip ())
                    current_field =""
                else :
                    current_field +=char 
            else :
                current_field +=char 

        if current_field .strip ():
            fields .append (current_field .strip ())

        return fields 

    @staticmethod 
    def parse_group_by (query :str )->List [str ]:
        """Parse GROUP BY clause with enhanced validation."""
        group_match =re .search (r'GROUP\s+BY\s+(.*?)(?:\s+HAVING|\s+ORDER|\s+LIMIT|\s*$)',query ,re .IGNORECASE )
        if not group_match :
            return []

        try :
            group_clause =group_match .group (1 ).strip ()
            if not group_clause :
                raise ValueError ("Empty GROUP BY clause")


            fields =[field .strip ()for field in group_clause .split (',')]

            for field in fields :
                if not field :
                    raise ValueError ("Empty field name in GROUP BY")
                if not QueryParser ._is_valid_field_name (field ):
                    raise ValueError (f"Invalid field name in GROUP BY: {field}")

            return fields 

        except Exception as e :
            raise ValueError (f"Error parsing GROUP BY clause: {str(e)}")

    @staticmethod 
    def validate_query_syntax (query :str )->Tuple [bool ,str ]:
        """Validate overall query syntax and return (is_valid, error_message)."""
        try :
            query =query .strip ()
            if not query :
                return False ,"Empty query"


            if not re .search (r'SELECT\s+.+\s+FROM\s+\w+',query ,re .IGNORECASE ):
                return False ,"Query must have SELECT ... FROM ... structure"


            if not QueryParser ._check_balanced_parentheses (query ):
                return False ,"Unbalanced parentheses in query"


            if not QueryParser ._check_balanced_quotes (query ):
                return False ,"Unbalanced quotes in query"


            try :
                QueryParser .parse_select (query )
            except Exception as e :
                return False ,f"SELECT clause error: {str(e)}"

            where_match =re .search (r'WHERE\s+(.*?)(?:\s+GROUP|\s+ORDER|\s+LIMIT|\s*$)',query ,re .IGNORECASE )
            if where_match :
                try :
                    QueryParser .parse_where (where_match .group (1 ))
                except Exception as e :
                    return False ,f"WHERE clause error: {str(e)}"

            try :
                QueryParser .parse_order_by (query )
            except Exception as e :
                return False ,f"ORDER BY clause error: {str(e)}"

            try :
                QueryParser .parse_group_by (query )
            except Exception as e :
                return False ,f"GROUP BY clause error: {str(e)}"

            return True ,""

        except Exception as e :
            return False ,f"Query validation error: {str(e)}"

    @staticmethod 
    def _check_balanced_parentheses (text :str )->bool :
        """Check if parentheses are balanced in the text."""
        count =0 
        in_quotes =False 
        quote_char =None 

        for char in text :
            if char in ('"',"'")and not in_quotes :
                in_quotes =True 
                quote_char =char 
            elif char ==quote_char and in_quotes :
                in_quotes =False 
                quote_char =None 
            elif not in_quotes :
                if char =='(':
                    count +=1 
                elif char ==')':
                    count -=1 
                    if count <0 :
                        return False 

        return count ==0 

    @staticmethod 
    def _check_balanced_quotes (text :str )->bool :
        """Check if quotes are balanced in the text."""
        single_quote_count =0 
        double_quote_count =0 
        i =0 

        while i <len (text ):
            char =text [i ]
            if char =="'":

                if i +1 <len (text )and text [i +1 ]=="'":
                    i +=1 
                else :
                    single_quote_count +=1 
            elif char =='"':

                if i +1 <len (text )and text [i +1 ]=='"':
                    i +=1 
                else :
                    double_quote_count +=1 
            i +=1 

        return single_quote_count %2 ==0 and double_quote_count %2 ==0 

    @staticmethod 
    def _parse_condition (condition_str :str )->'WhereCondition':
        """Parse a single condition with enhanced operator support."""
        condition_str =condition_str .strip ()
        if not condition_str :
            raise ValueError ("Empty condition")

        try :

            is_null_match =re .match (r'(\w+(?:\.\w+)?)\s+IS\s+NOT\s+NULL',condition_str ,re .IGNORECASE )
            if is_null_match :
                field =is_null_match .group (1 ).strip ()
                return WhereCondition (field ,'IS NOT',None )

            is_null_match =re .match (r'(\w+(?:\.\w+)?)\s+IS\s+NULL',condition_str ,re .IGNORECASE )
            if is_null_match :
                field =is_null_match .group (1 ).strip ()
                return WhereCondition (field ,'IS',None )


            between_match =re .match (r'(\w+(?:\.\w+)?)\s+(?:NOT\s+)?BETWEEN\s+(.+?)\s+AND\s+(.+)',condition_str ,re .IGNORECASE )
            if between_match :
                field =between_match .group (1 ).strip ()
                value1 =QueryParser ._parse_value (between_match .group (2 ).strip ())
                value2 =QueryParser ._parse_value (between_match .group (3 ).strip ())
                operator ='NOT BETWEEN'if 'NOT BETWEEN'in condition_str .upper ()else 'BETWEEN'
                return WhereCondition (field ,operator ,(value1 ,value2 ))


            in_match =re .match (r'(\w+(?:\.\w+)?)\s+(NOT\s+)?IN\s*\((.*?)\)',condition_str ,re .IGNORECASE )
            if in_match :
                field =in_match .group (1 ).strip ()
                is_not =bool (in_match .group (2 ))
                values_str =in_match .group (3 ).strip ()


                values =QueryParser ._parse_in_values (values_str )
                operator ='NOT IN'if is_not else 'IN'
                return WhereCondition (field ,operator ,values )


            operators =['>=','<=','!=','<>','>','<','=','NOT LIKE','NOT ILIKE','LIKE','ILIKE']

            for op in operators :

                pattern =f'\\s*{re.escape(op)}\\s*'
                if re .search (pattern ,condition_str ,re .IGNORECASE ):
                    parts =re .split (pattern ,condition_str ,flags =re .IGNORECASE )
                    if len (parts )==2 :
                        field =parts [0 ].strip ()
                        value_str =parts [1 ].strip ()

                        if not field :
                            raise ValueError (f"Missing field name in condition: {condition_str}")

                        value =QueryParser ._parse_value (value_str )
                        return WhereCondition (field ,op .upper (),value )

            raise ValueError (f"No valid operator found in condition: {condition_str}")

        except Exception as e :
            raise ValueError (f"Error parsing condition '{condition_str}': {str(e)}")

    @staticmethod 
    def _parse_value (value_str :str )->Any :
        """Parse a value string into appropriate Python type."""
        value_str =value_str .strip ()
        if not value_str :
            return ""


        if value_str .upper ()=='NULL':
            return None 


        if value_str .upper ()in ('TRUE','FALSE'):
            return value_str .upper ()=='TRUE'


        if (value_str .startswith ('"')and value_str .endswith ('"'))or (value_str .startswith ("'")and value_str .endswith ("'")):
            return QueryParser ._unescape_string (value_str [1 :-1 ])


        try :
            if '.'in value_str or 'e'in value_str .lower ():
                return float (value_str )
            else :
                return int (value_str )
        except ValueError :
            pass 


        return value_str 

    @staticmethod 
    def _unescape_string (s :str )->str :
        """Unescape a quoted string."""

        s =s .replace ("''","'").replace ('""','"')

        s =s .replace ('\\n','\n').replace ('\\t','\t').replace ('\\r','\r')
        s =s .replace ('\\\\','\\')
        return s 

    @staticmethod 
    def _parse_in_values (values_str :str )->List [Any ]:
        """Parse comma-separated values for IN operator."""
        if not values_str .strip ():
            return []

        values =[]
        current_value =""
        in_quotes =False 
        quote_char =None 
        paren_depth =0 

        i =0 
        while i <len (values_str ):
            char =values_str [i ]

            if char in ('"',"'")and not in_quotes :
                in_quotes =True 
                quote_char =char 
                current_value +=char 
            elif char ==quote_char and in_quotes :
                if i +1 <len (values_str )and values_str [i +1 ]==quote_char :
                    current_value +=char *2 
                    i +=1 
                else :
                    in_quotes =False 
                    quote_char =None 
                    current_value +=char 
            elif not in_quotes :
                if char =='(':
                    paren_depth +=1 
                    current_value +=char 
                elif char ==')':
                    paren_depth -=1 
                    current_value +=char 
                elif char ==','and paren_depth ==0 :
                    if current_value .strip ():
                        values .append (QueryParser ._parse_value (current_value .strip ()))
                    current_value =""
                else :
                    current_value +=char 
            else :
                current_value +=char 

            i +=1 

        if current_value .strip ():
            values .append (QueryParser ._parse_value (current_value .strip ()))

        return values 


class SceneQueryEngine :
    """Handles SQL-like queries over scene data."""

    def __init__ (self ):
        """Initialize with available tables."""
        self .available_tables ={

        'objects':'Scene objects with transform and type data',
        'materials':'Material data including nodes and properties',
        'meshes':'Mesh geometry data',
        'lights':'Light objects and properties',
        'cameras':'Camera objects and settings',
        'collections':'Collection hierarchy and contents',
        'scenes':'Scene data and settings',
        'worlds':'World shader and environment data',
        'images':'Image data blocks',
        'render_settings':'Render engine settings and configuration',


        'nodes':'All nodes from shader, geometry, and compositor trees',
        'shader_nodes':'Shader nodes from materials and worlds',
        'geometry_nodes':'Geometry nodes from modifiers and node groups',
        'compositor_nodes':'Compositor nodes from scenes',
        'node_connections':'Connections between nodes (node links)',
        'node_sockets':'Input and output sockets of all nodes',
        'node_trees':'Information about node trees and their contents',
        'node_groups':'Node groups and their usage',


        'modifiers':'Object modifiers and their properties',
        'animations':'Animation data including keyframes and fcurves',
        'textures':'Texture data blocks (legacy textures)',
        'drivers':'Driver expressions and dependencies',
        'constraints':'Object and bone constraints',
        'custom_properties':'Custom properties from all data blocks',


        'tables':'Meta-table listing all available tables'
        }

    def _validate_field_exists (self ,field :str ,sample_data :List [Dict [str ,Any ]])->bool :
        """Validate that a field (including nested fields) exists in the data."""
        if not sample_data :
            return True 

        if field =='*':
            return True 


        for item in sample_data [:5 ]:
            if '.'in field :

                field_parts =field .split ('.')
                current_value =item 


                for part in field_parts :
                    if isinstance (current_value ,dict )and part in current_value :
                        current_value =current_value [part ]
                    else :
                        break 
                else :

                    return True 
            else :

                if field in item :
                    return True 

        return False 

    def _get_available_fields (self ,sample_data :List [Dict [str ,Any ]],max_depth :int =3 )->List [str ]:
        """Get all available fields including nested ones from sample data."""
        if not sample_data :
            return []

        fields =set ()

        def extract_fields (obj ,prefix ="",depth =0 ):
            if depth >max_depth :
                return 

            if isinstance (obj ,dict ):
                for key ,value in obj .items ():
                    full_key =f"{prefix}.{key}"if prefix else key 
                    fields .add (full_key )


                    if isinstance (value ,dict ):
                        extract_fields (value ,full_key ,depth +1 )
                    elif isinstance (value ,list )and value and isinstance (value [0 ],dict ):

                        extract_fields (value [0 ],full_key ,depth +1 )


        for item in sample_data [:3 ]:
            extract_fields (item )

        return sorted (fields )

    def execute_query (self ,expr :str ,limit :int ,context ,
    format_type :str ="json")->Dict [str ,Any ]:
        """Execute enhanced SQL-like query over scene data with robust error handling."""
        try :

            if format_type .lower ()not in FormatFactory .get_available_formats ():
                available =', '.join (FormatFactory .get_available_formats ())
                return QueryResponse (
                status ="error",
                error =f"Unknown format: {format_type}. Available formats: {available}",
                format_type =format_type 
                ).to_dict ()


            is_valid ,validation_error =QueryParser .validate_query_syntax (expr )
            if not is_valid :
                return QueryResponse (
                status ="error",
                error =f"Query syntax error: {validation_error}",
                format_type =format_type 
                ).to_dict ()


            from_match =re .search (r'FROM\s+(\w+)',expr ,re .IGNORECASE )
            if not from_match :
                return QueryResponse (
                status ="error",
                error ="Invalid query format. Expected: SELECT fields FROM table [WHERE conditions] [ORDER BY field] [LIMIT n]",
                format_type =format_type 
                ).to_dict ()

            table =from_match .group (1 ).strip ().lower ()


            if table not in self .available_tables :
                available =', '.join (sorted (self .available_tables .keys ()))
                return QueryResponse (
                status ="error",
                error =f"Unknown table: '{table}'. Available tables: {available}",
                format_type =format_type 
                ).to_dict ()


            try :
                fields ,distinct ,aggregates ,aliases =QueryParser .parse_select (expr )
            except Exception as e :
                return QueryResponse (
                status ="error",
                error =f"SELECT clause error: {str(e)}",
                format_type =format_type 
                ).to_dict ()


            where_expression =WhereExpression ()
            where_match =re .search (r'WHERE\s+(.*?)(?:\s+GROUP|\s+ORDER|\s+LIMIT|\s*$)',expr ,re .IGNORECASE )
            if where_match :
                try :
                    where_clause =where_match .group (1 ).strip ()

                    where_clause =where_clause .rstrip (';')
                    where_expression =QueryParser .parse_where (where_clause )
                except Exception as e :
                    return QueryResponse (
                    status ="error",
                    error =f"WHERE clause error: {str(e)}",
                    format_type =format_type 
                    ).to_dict ()


            try :
                group_by_fields =QueryParser .parse_group_by (expr )
            except Exception as e :
                return QueryResponse (
                status ="error",
                error =f"GROUP BY clause error: {str(e)}",
                format_type =format_type 
                ).to_dict ()


            try :
                order_by_fields =QueryParser .parse_order_by (expr )
            except Exception as e :
                return QueryResponse (
                status ="error",
                error =f"ORDER BY clause error: {str(e)}",
                format_type =format_type 
                ).to_dict ()


            try :
                data =self ._get_table_data (table ,context )
            except Exception as e :
                return QueryResponse (
                status ="error",
                error =f"Error loading data from table '{table}': {str(e)}",
                format_type =format_type 
                ).to_dict ()


            if data and fields !=['*']:

                for field in fields :
                    if field not in aggregates and field not in aliases :
                        if not self ._validate_field_exists (field ,data ):
                            available_fields =self ._get_available_fields (data )

                            if len (available_fields )>20 :
                                available_sample =available_fields [:20 ]+["..."]
                            else :
                                available_sample =available_fields 

                            return QueryResponse (
                            status ="error",
                            error =f"Field '{field}' not found in table '{table}'. Available fields: {', '.join(available_sample)}",
                            format_type =format_type 
                            ).to_dict ()


            if where_expression .conditions :
                try :
                    filtered_data =[]
                    for item in data :
                        if where_expression .evaluate (item ):
                            filtered_data .append (item )
                    data =filtered_data 
                except Exception as e :
                    return QueryResponse (
                    status ="error",
                    error =f"Error applying WHERE clause: {str(e)}",
                    format_type =format_type 
                    ).to_dict ()


            if group_by_fields :
                try :
                    data =self ._apply_group_by (data ,group_by_fields ,aggregates ,aliases )
                except Exception as e :
                    return QueryResponse (
                    status ="error",
                    error =f"Error applying GROUP BY: {str(e)}",
                    format_type =format_type 
                    ).to_dict ()
            elif aggregates :

                try :
                    data =self ._apply_aggregates (data ,aggregates ,aliases )
                except Exception as e :
                    return QueryResponse (
                    status ="error",
                    error =f"Error applying aggregate functions: {str(e)}",
                    format_type =format_type 
                    ).to_dict ()


            if distinct and not group_by_fields :
                try :
                    data =self ._apply_distinct (data ,fields )
                except Exception as e :
                    return QueryResponse (
                    status ="error",
                    error =f"Error applying DISTINCT: {str(e)}",
                    format_type =format_type 
                    ).to_dict ()


            resolved_order_fields =[]
            for field ,direction in order_by_fields :

                if field in aliases :

                    if field in aggregates :
                        resolved_order_fields .append ((field ,direction ))
                    else :
                        resolved_order_fields .append ((aliases [field ],direction ))
                else :
                    resolved_order_fields .append ((field ,direction ))


            if resolved_order_fields :
                try :
                    data =self ._apply_order_by (data ,resolved_order_fields )
                except Exception as e :
                    return QueryResponse (
                    status ="error",
                    error =f"Error applying ORDER BY: {str(e)}",
                    format_type =format_type 
                    ).to_dict ()


            original_count =len (data )
            if limit >0 :
                data =data [:limit ]


            if fields !=["*"]and not aggregates :
                try :
                    data =self ._select_fields (data ,fields )
                except Exception as e :
                    return QueryResponse (
                    status ="error",
                    error =f"Error selecting fields: {str(e)}",
                    format_type =format_type 
                    ).to_dict ()


            try :
                formatter =FormatFactory .create_formatter (format_type )
                formatted_data =formatter .format (data )
            except Exception as e :
                return QueryResponse (
                status ="error",
                error =f"Error formatting output: {str(e)}",
                format_type =format_type 
                ).to_dict ()

            return QueryResponse (
            status ="success",
            data =formatted_data ,
            count =len (data ),
            format_type =format_type .lower ()
            ).to_dict ()

        except Exception as e :
            return QueryResponse (
            status ="error",
            error =f"Unexpected error executing query: {str(e)}",
            format_type =format_type 
            ).to_dict ()

    def _apply_group_by (self ,data :List [Dict [str ,Any ]],group_fields :List [str ],
    aggregates :Dict [str ,Tuple [str ,str ]],aliases :Dict [str ,str ])->List [Dict [str ,Any ]]:
        """Apply GROUP BY with aggregates."""
        groups =defaultdict (list )

        def get_field_value (item ,field ):
            """Extract field value, handling nested fields."""
            if '.'in field :

                field_parts =field .split ('.')
                current_value =item 


                for part in field_parts :
                    if isinstance (current_value ,dict )and part in current_value :
                        current_value =current_value [part ]
                    else :
                        return None 

                return current_value 
            else :

                return item .get (field ,None )


        for item in data :
            key =tuple (get_field_value (item ,field )for field in group_fields )
            groups [key ].append (item )


        result =[]
        for key ,group_items in groups .items ():
            group_result ={}


            for i ,field in enumerate (group_fields ):
                group_result [field ]=key [i ]


            for alias ,(func_name ,field_name )in aggregates .items ():
                group_result [alias ]=AggregateFunction .apply (func_name ,field_name ,group_items )

            result .append (group_result )

        return result 

    def _apply_aggregates (self ,data :List [Dict [str ,Any ]],
    aggregates :Dict [str ,Tuple [str ,str ]],aliases :Dict [str ,str ])->List [Dict [str ,Any ]]:
        """Apply aggregates to entire dataset."""
        result ={}

        for alias ,(func_name ,field_name )in aggregates .items ():
            result [alias ]=AggregateFunction .apply (func_name ,field_name ,data )

        return [result ]if result else []

    def _apply_distinct (self ,data :List [Dict [str ,Any ]],fields :List [str ])->List [Dict [str ,Any ]]:
        """Apply DISTINCT to selected fields."""
        def get_field_value (item ,field ):
            """Extract field value, handling nested fields."""
            if '.'in field :

                field_parts =field .split ('.')
                current_value =item 


                for part in field_parts :
                    if isinstance (current_value ,dict )and part in current_value :
                        current_value =current_value [part ]
                    else :
                        return None 

                return current_value 
            else :

                return item .get (field ,None )

        if fields ==['*']:

            seen =set ()
            result =[]
            for item in data :
                key =tuple (sorted (item .items ()))
                if key not in seen :
                    seen .add (key )
                    result .append (item )
            return result 
        else :

            seen =set ()
            result =[]
            for item in data :
                key =tuple (get_field_value (item ,field )for field in fields )
                if key not in seen :
                    seen .add (key )
                    result .append (item )
            return result 

    def _apply_order_by (self ,data :List [Dict [str ,Any ]],
    order_fields :List [Tuple [str ,str ]])->List [Dict [str ,Any ]]:
        """Apply ORDER BY sorting."""
        if not order_fields or not data :
            return data 

        def get_field_value (item ,field ):
            """Extract field value, handling nested fields."""
            if '.'in field :

                field_parts =field .split ('.')
                current_value =item 


                for part in field_parts :
                    if isinstance (current_value ,dict )and part in current_value :
                        current_value =current_value [part ]
                    else :
                        return None 

                return current_value 
            else :

                return item .get (field ,None )

        def sort_key (item ):
            """Generate sort key for multi-field sorting."""
            key =[]
            for field ,direction in order_fields :
                value =get_field_value (item ,field )


                if value is None :

                    if direction =='ASC':
                        key .append ((1 ,""))
                    else :
                        key .append ((1 ,""))
                else :

                    if isinstance (value ,(list ,dict )):
                        value =str (value )
                    elif isinstance (value ,bool ):
                        value =int (value )


                    if direction =='DESC':
                        if isinstance (value ,(int ,float )):
                            key .append ((0 ,-value ))
                        else :

                            key .append ((0 ,value ))
                    else :
                        key .append ((0 ,value ))

            return key 



        def final_sort_key (item ):
            key =[]
            for field ,direction in order_fields :
                value =get_field_value (item ,field )

                if value is None :
                    key .append ((1 ,""))
                else :
                    if isinstance (value ,(list ,dict )):
                        value =str (value )
                    elif isinstance (value ,bool ):
                        value =int (value )

                    if direction =='DESC':
                        if isinstance (value ,(int ,float )):
                            key .append ((0 ,-value ))
                        else :

                            key .append ((0 ,ReverseString (str (value ))))
                    else :
                        key .append ((0 ,value ))

            return key 


        class ReverseString :
            def __init__ (self ,s ):
                self .s =str (s )

            def __lt__ (self ,other ):
                return self .s >other .s 

            def __gt__ (self ,other ):
                return self .s <other .s 

            def __eq__ (self ,other ):
                return self .s ==other .s 

            def __le__ (self ,other ):
                return self .s >=other .s 

            def __ge__ (self ,other ):
                return self .s <=other .s 

            def __ne__ (self ,other ):
                return self .s !=other .s 

        try :
            data .sort (key =final_sort_key )
        except Exception as e :

            for field ,direction in reversed (order_fields ):
                data .sort (
                key =lambda x ,f =field :(
                1 if get_field_value (x ,f )is None else 0 ,
                get_field_value (x ,f )or ""
                ),
                reverse =(direction =='DESC')
                )

        return data 

    def get_table_schema (self ,table_name :str ,context )->Dict [str ,Any ]:
        """Get schema information for a table."""
        if table_name .lower ()not in self .available_tables :
            available =', '.join (self .available_tables .keys ())
            raise ValueError (f"Unknown table: {table_name}. Available tables: {available}")


        data =self ._get_table_data (table_name .lower (),context )
        if not data :
            return {"fields":[],"sample_count":0 }


        fields ={}
        for item in data [:10 ]:
            for field ,value in item .items ():
                if field not in fields :
                    fields [field ]={
                    "type":type (value ).__name__ ,
                    "nullable":False ,
                    "sample_values":[]
                    }

                if value is None :
                    fields [field ]["nullable"]=True 
                elif len (fields [field ]["sample_values"])<3 :
                    fields [field ]["sample_values"].append (value )

        return {
        "table":table_name .lower (),
        "description":self .available_tables [table_name .lower ()],
        "fields":fields ,
        "sample_count":len (data )
        }

    def get_supported_formats (self )->List [str ]:
        """Get list of supported output formats."""
        return FormatFactory .get_available_formats ()

    def get_comprehensive_schema (self ,context ,format_type :str ="json",
    include_sample_data :bool =False ,
    max_sample_size :int =3 )->Dict [str ,Any ]:
        """
        Get comprehensive schema information for all tables in LLM-friendly format.
        
        Args:
            context: Blender context
            format_type: Output format ('json', 'csv', 'table')
            include_sample_data: Whether to include sample values for each field
            max_sample_size: Maximum number of sample values per field
            
        Returns:
            Comprehensive schema data in requested format
        """
        try :

            if format_type .lower ()not in FormatFactory .get_available_formats ():
                available =', '.join (FormatFactory .get_available_formats ())
                return {
                "status":"error",
                "error":f"Unknown format: {format_type}. Available formats: {available}",
                "format":format_type 
                }

            schema_data ={
            "status":"success",
            "format":format_type .lower (),
            "generated_at":bpy .context .scene .frame_current ,
            "total_tables":len (self .available_tables ),
            "tables":[]
            }

            total_elements =0 


            for table_name ,description in self .available_tables .items ():
                try :

                    if table_name =='tables':

                        table_data =self ._get_tables_data (context )
                        count =len (table_data )
                        fields_info ={
                        "table":{"type":"str","description":"Table name","nullable":False },
                        "description":{"type":"str","description":"Table description","nullable":False }
                        }
                    else :
                        table_data =self ._get_table_data (table_name ,context )
                        count =len (table_data )if table_data else 0 


                        fields_info =self ._analyze_table_fields (table_data ,include_sample_data ,max_sample_size )

                    total_elements +=count 

                    table_info ={
                    "name":table_name ,
                    "description":description ,
                    "count":count ,
                    "fields":fields_info ,
                    "field_count":len (fields_info )
                    }

                    schema_data ["tables"].append (table_info )

                except Exception as e :

                    error_table_info ={
                    "name":table_name ,
                    "description":description ,
                    "count":0 ,
                    "fields":{},
                    "field_count":0 ,
                    "error":str (e )
                    }
                    schema_data ["tables"].append (error_table_info )

            schema_data ["total_elements"]=total_elements 


            if format_type .lower ()=="json":
                return schema_data 
            elif format_type .lower ()in ["csv","table"]:

                return self ._format_schema_for_export (schema_data ,format_type .lower ())

            return schema_data 

        except Exception as e :
            return {
            "status":"error",
            "error":f"Failed to get comprehensive schema: {str(e)}",
            "format":format_type ,
            "tables":[]
            }

    def get_llm_friendly_schema_summary (self ,context )->str :
        """
        Get a lightweight text summary of all tables optimized for LLM consumption.
        This version doesn't load actual table data to avoid performance issues on large scenes.
        
        Args:
            context: Blender context
            
        Returns:
            LLM-friendly text summary of database schema with examples
        """
        try :
            lines =[]

            lines .append ("# Scene Context")
            lines .append ("## Basic data")


            try :
                from .tools import tools_manager 

                scene_context =tools_manager .handle_tool_call ("scene_context",{},context )[1 ]["result"]


                import json 
                scene_json =json .dumps (scene_context ,indent =None ,separators =(',',':'))
                lines .append (scene_json )

            except Exception as e :
                print (f"Error getting scene context: {e}")
                lines .append (f"{len(self.available_tables)} tables available")

            lines .append ("")
            lines .append ("## Available Tables")


            for table_name ,description in self .available_tables .items ():
                if table_name =='tables':
                    continue 
                lines .append (f"- **{table_name}**: {description}")

            lines .append ("")
            lines .append ("## Query Examples")
            lines .append ("### Essential Patterns")
            lines .append ("```sql")
            lines .append ("-- Explore any table structure")
            lines .append ("SELECT * FROM table_name LIMIT 3")
            lines .append ("")
            lines .append ("-- Count and group data")
            lines .append ("SELECT type, COUNT(*) FROM objects GROUP BY type")
            lines .append ("SELECT node_type, COUNT(*) FROM shader_nodes GROUP BY node_type ORDER BY COUNT(*) DESC")
            lines .append ("")
            lines .append ("-- Find specific objects/materials")
            lines .append ("SELECT name, location, type FROM objects WHERE name LIKE '%Cube%'")
            lines .append ("SELECT name, metallic, roughness FROM materials WHERE use_nodes = true")
            lines .append ("```")

            lines .append ("")
            lines .append ("### Node System Queries")
            lines .append ("```sql")
            lines .append ("-- Find nodes by type with properties")
            lines .append ("SELECT tree_owner, node_name, properties FROM shader_nodes WHERE node_type = 'BSDF_PRINCIPLED'")
            lines .append ("")
            lines .append ("-- Node connections and relationships")
            lines .append ("SELECT node_name, connected_node, socket_name FROM node_connections WHERE tree_owner = 'Material.001'")
            lines .append ("")
            lines .append ("-- Image textures with file paths")
            lines .append ("SELECT tree_owner, node_name, properties FROM shader_nodes WHERE node_type = 'TEX_IMAGE'")
            lines .append ("")
            lines .append ("-- Disconnected/unused nodes")
            lines .append ("SELECT node_name, tree_owner FROM nodes WHERE connections.total_input_links = 0 AND connections.total_output_links = 0")
            lines .append ("```")

            lines .append ("")
            lines .append ("### Advanced Patterns")
            lines .append ("```sql")
            lines .append ("-- Objects with specific modifiers")
            lines .append ("SELECT object_name, modifier_type FROM modifiers WHERE modifier_type = 'NODES' AND show_viewport = true")
            lines .append ("")
            lines .append ("-- Animation and keyframe data")
            lines .append ("SELECT object_name, data_path, keyframes_count FROM animations WHERE keyframes_count > 2")
            lines .append ("")
            lines .append ("-- Node tree complexity analysis")
            lines .append ("SELECT tree_name, tree_type, nodes_count, links_count FROM node_trees ORDER BY nodes_count DESC LIMIT 10")
            lines .append ("```")

            lines .append ("")
            lines .append ("### Important Tips for Querying")
            lines .append ("- Always start with exploration of table structure")
            lines .append ("- Node properties are nested JSON - access with `properties` field")
            lines .append ("- Use `LIMIT` for large datasets, `WHERE` for focused queries")
            lines .append ("- Use `SELECT * FROM table_name LIMIT 3` to see available fields")

            return "\n".join (lines )

        except Exception as e :
            return f"Error generating schema summary: {str(e)}"

    def _analyze_table_fields (self ,data :List [Dict [str ,Any ]],
    include_samples :bool =False ,
    max_samples :int =3 )->Dict [str ,Dict [str ,Any ]]:
        """
        Analyze table data to extract comprehensive field information.
        
        Args:
            data: Table data to analyze
            include_samples: Whether to include sample values
            max_samples: Maximum sample values per field
            
        Returns:
            Dictionary of field information
        """
        if not data :
            return {}

        fields_info ={}


        for item in data :
            for field_name ,value in item .items ():
                if field_name not in fields_info :
                    fields_info [field_name ]={
                    "type":"unknown",
                    "nullable":False ,
                    "sample_values":[]if include_samples else None ,
                    "description":self ._get_field_description (field_name )
                    }

                field_info =fields_info [field_name ]


                if value is None :
                    field_info ["nullable"]=True 
                else :
                    value_type =self ._get_friendly_type_name (value )
                    if field_info ["type"]=="unknown":
                        field_info ["type"]=value_type 
                    elif field_info ["type"]!=value_type and value_type !="unknown":

                        field_info ["type"]="mixed"


                if include_samples and field_info ["sample_values"]is not None :
                    if len (field_info ["sample_values"])<max_samples and value is not None :
                        if value not in field_info ["sample_values"]:
                            field_info ["sample_values"].append (value )

        return fields_info 

    def _get_friendly_type_name (self ,value :Any )->str :
        """Get user-friendly type name for a value."""
        if value is None :
            return "null"
        elif isinstance (value ,bool ):
            return "boolean"
        elif isinstance (value ,int ):
            return "integer"
        elif isinstance (value ,float ):
            return "float"
        elif isinstance (value ,str ):
            return "string"
        elif isinstance (value ,list ):
            if value :
                element_type =self ._get_friendly_type_name (value [0 ])
                return f"array[{element_type}]"
            return "array"
        elif isinstance (value ,dict ):
            return "object"
        elif isinstance (value ,(Vector ,Euler ,Quaternion )):
            return "vector"
        elif isinstance (value ,Matrix ):
            return "matrix"
        elif isinstance (value ,Color ):
            return "color"
        else :
            return type (value ).__name__ .lower ()

    def _get_field_description (self ,field_name :str )->str :
        """Get human-readable description for common field names."""
        descriptions ={
        "name":"Object or data block name",
        "type":"Object or data type",
        "location":"3D position coordinates",
        "rotation":"Rotation in Euler angles",
        "scale":"Scale factors for X, Y, Z axes",
        "visible":"Visibility state in viewport",
        "selected":"Selection state",
        "active":"Whether this is the active object/item",
        "users":"Number of references to this data block",
        "vertices":"Number of vertices in mesh",
        "faces":"Number of faces/polygons in mesh",
        "edges":"Number of edges in mesh",
        "materials":"List of assigned materials",
        "energy":"Light energy/intensity",
        "color":"Color value (RGB or RGBA)",
        "focal_length":"Camera focal length in mm",
        "resolution_x":"Horizontal resolution in pixels",
        "resolution_y":"Vertical resolution in pixels",
        "frame_start":"Animation start frame",
        "frame_end":"Animation end frame",
        "frame_current":"Current frame number",
        "render_engine":"Active render engine",
        "use_nodes":"Whether node-based shading is enabled",
        "node_count":"Number of nodes in node tree",
        "filepath":"File path or location",
        "width":"Width dimension",
        "height":"Height dimension",
        "channels":"Number of color channels",
        "depth":"Bit depth of image data",
        "samples":"Number of render samples",
        "metallic":"Metallic factor (0.0 to 1.0)",
        "roughness":"Surface roughness (0.0 to 1.0)",
        "fps":"Frames per second",
        "clip_start":"Near clipping distance",
        "clip_end":"Far clipping distance"
        }
        return descriptions .get (field_name ,"")

    def _format_schema_for_export (self ,schema_data :Dict [str ,Any ],format_type :str )->Dict [str ,Any ]:
        """Format schema data for CSV or table export."""

        flattened_data =[]

        for table in schema_data ["tables"]:
            for field_name ,field_info in table .get ("fields",{}).items ():
                row ={
                "table_name":table ["name"],
                "table_description":table ["description"],
                "table_count":table ["count"],
                "field_name":field_name ,
                "field_type":field_info .get ("type","unknown"),
                "field_nullable":field_info .get ("nullable",False ),
                "field_description":field_info .get ("description",""),
                "sample_values":json .dumps (field_info .get ("sample_values",[]))if field_info .get ("sample_values")else ""
                }
                flattened_data .append (row )


        formatter =FormatFactory .create_formatter (format_type )
        formatted_content =formatter .format (flattened_data )

        return {
        **schema_data ,
        "formatted_content":formatted_content ,
        "flattened_rows":len (flattened_data )
        }

    def _generate_markdown_schema (self ,context )->str :
        """Generate markdown documentation for the schema."""
        schema_data =self .get_comprehensive_schema (context ,include_sample_data =True )

        if schema_data ["status"]!="success":
            return f"# Error\n\n{schema_data.get('error', 'Failed to generate schema')}"

        lines =[]
        lines .append ("# Blender Scene Database Schema")
        lines .append ("")
        lines .append (f"**Total Tables:** {schema_data['total_tables']}")
        lines .append (f"**Total Elements:** {schema_data['total_elements']}")
        lines .append ("")
        lines .append ("## Tables Overview")
        lines .append ("")


        for table in schema_data ["tables"]:
            lines .append (f"- [{table['name']}](#{table['name'].lower()}) ({table['count']} rows) - {table['description']}")

        lines .append ("")
        lines .append ("## Detailed Schema")
        lines .append ("")

        for table in schema_data ["tables"]:
            lines .append (f"### {table['name']}")
            lines .append ("")
            lines .append (f"**Description:** {table['description']}")
            lines .append (f"**Row Count:** {table['count']}")

            if "error"in table :
                lines .append (f"**Error:** {table['error']}")
            else :
                lines .append ("")
                lines .append ("| Field | Type | Nullable | Description | Sample Values |")
                lines .append ("|-------|------|----------|-------------|---------------|")

                for field_name ,field_info in table ["fields"].items ():
                    nullable ="Yes"if field_info .get ("nullable",False )else "No"
                    description =field_info .get ("description","")
                    samples =field_info .get ("sample_values",[])
                    sample_str =", ".join (str (s )for s in samples [:3 ])if samples else ""

                    lines .append (f"| {field_name} | {field_info['type']} | {nullable} | {description} | {sample_str} |")

            lines .append ("")

        return "\n".join (lines )

    def get_all_table_counts (self ,context )->Dict [str ,Any ]:
        """
        Get counts of elements in all available tables.
        
        Args:
            context: Blender context
            
        Returns:
            Dictionary with table names as keys and counts as values,
            plus summary information
        """
        try :
            table_counts ={}
            total_elements =0 
            errors =[]

            for table_name in self .available_tables .keys ():
                try :

                    if table_name =='tables':
                        table_counts [table_name ]=len (self .available_tables )
                        total_elements +=len (self .available_tables )
                        continue 

                    data =self ._get_table_data (table_name ,context )
                    count =len (data )if data else 0 
                    table_counts [table_name ]=count 
                    total_elements +=count 

                except Exception as e :
                    errors .append (f"Error getting count for table '{table_name}': {str(e)}")
                    table_counts [table_name ]=0 

            return {
            "status":"success",
            "table_counts":table_counts ,
            "total_tables":len (self .available_tables ),
            "total_elements":total_elements ,
            "errors":errors if errors else None 
            }

        except Exception as e :
            return {
            "status":"error",
            "error":f"Failed to get table counts: {str(e)}",
            "table_counts":{},
            "total_tables":0 ,
            "total_elements":0 
            }

    def _get_table_data (self ,table :str ,context )->List [Dict [str ,Any ]]:
        """Get data for a specific table."""
        if table =="objects":
            return self ._get_objects_data (context )
        elif table =="materials":
            return self ._get_materials_data (context )
        elif table =="meshes":
            return self ._get_meshes_data (context )
        elif table =="lights":
            return self ._get_lights_data (context )
        elif table =="cameras":
            return self ._get_cameras_data (context )
        elif table =="collections":
            return self ._get_collections_data (context )
        elif table =="scenes":
            return self ._get_scenes_data (context )
        elif table =="worlds":
            return self ._get_worlds_data (context )
        elif table =="images":
            return self ._get_images_data (context )
        elif table =="render_settings":
            return self ._get_render_settings_data (context )
        elif table =="nodes":
            return self ._get_nodes_data (context )
        elif table =="shader_nodes":
            return self ._get_shader_nodes_data (context )
        elif table =="geometry_nodes":
            return self ._get_geometry_nodes_data (context )
        elif table =="compositor_nodes":
            return self ._get_compositor_nodes_data (context )
        elif table =="node_connections":
            return self ._get_node_connections_data (context )
        elif table =="node_sockets":
            return self ._get_node_sockets_data (context )
        elif table =="node_trees":
            return self ._get_node_trees_data (context )
        elif table =="node_groups":
            return self ._get_node_groups_data (context )
        elif table =="modifiers":
            return self ._get_modifiers_data (context )
        elif table =="animations":
            return self ._get_animations_data (context )
        elif table =="textures":
            return self ._get_textures_data (context )
        elif table =="drivers":
            return self ._get_drivers_data (context )
        elif table =="constraints":
            return self ._get_constraints_data (context )
        elif table =="custom_properties":
            return self ._get_custom_properties_data (context )
        elif table =="tables":
            return self ._get_tables_data (context )
        else :
            available =', '.join (self .available_tables .keys ())
            raise ValueError (f"Unknown table: {table}. Available tables: {available}")

    def _get_objects_data (self ,context )->List [Dict [str ,Any ]]:
        """Get objects data."""
        objects_data =[]
        for obj in context .scene .objects :
            obj_data ={
            "name":obj .name ,
            "type":obj .type ,
            "location":to_json_serializable (obj .location ),
            "rotation":to_json_serializable (obj .rotation_euler ),
            "scale":to_json_serializable (obj .scale ),
            "visible":obj .visible_get (),
            "selected":obj .select_get (),
            "active":obj ==context .active_object ,
            "data_name":obj .data .name if obj .data else None ,
            "parent":obj .parent .name if obj .parent else None ,
            "collection":obj .users_collection [0 ].name if obj .users_collection else None 
            }


            if obj .type =='MESH'and obj .data :
                obj_data ["vertices"]=len (obj .data .vertices )
                obj_data ["faces"]=len (obj .data .polygons )
                obj_data ["materials"]=[mat .name for mat in obj .data .materials if mat ]
            elif obj .type =='LIGHT'and obj .data :
                obj_data ["light_type"]=obj .data .type 
                obj_data ["energy"]=obj .data .energy 
                obj_data ["color"]=to_json_serializable (obj .data .color )
            elif obj .type =='CAMERA'and obj .data :
                obj_data ["focal_length"]=obj .data .lens 
                obj_data ["sensor_width"]=obj .data .sensor_width 

            objects_data .append (obj_data )

        return objects_data 

    def _get_materials_data (self ,context )->List [Dict [str ,Any ]]:
        """Get materials data."""
        materials_data =[]
        for mat in bpy .data .materials :
            mat_data ={
            "name":mat .name ,
            "use_nodes":mat .use_nodes ,
            "users":mat .users ,
            "diffuse_color":to_json_serializable (mat .diffuse_color ),
            "metallic":mat .metallic ,
            "roughness":mat .roughness ,
            "blend_method":mat .blend_method 
            }


            if hasattr (mat ,'alpha'):
                mat_data ["alpha"]=mat .alpha 


            if mat .use_nodes and mat .node_tree :
                mat_data ["node_count"]=len (mat .node_tree .nodes )
                mat_data ["output_nodes"]=[n .name for n in mat .node_tree .nodes if n .type =='OUTPUT_MATERIAL']


                for node in mat .node_tree .nodes :
                    if node .type =='BSDF_PRINCIPLED':
                        if 'Alpha'in node .inputs :
                            mat_data ["alpha"]=node .inputs ['Alpha'].default_value 
                        break 

            materials_data .append (mat_data )

        return materials_data 

    def _get_meshes_data (self ,context )->List [Dict [str ,Any ]]:
        """Get mesh data."""
        meshes_data =[]
        for mesh in bpy .data .meshes :
            mesh_data ={
            "name":mesh .name ,
            "vertices":len (mesh .vertices ),
            "edges":len (mesh .edges ),
            "faces":len (mesh .polygons ),
            "users":mesh .users ,
            "materials":[mat .name for mat in mesh .materials if mat ]
            }
            meshes_data .append (mesh_data )

        return meshes_data 

    def _get_lights_data (self ,context )->List [Dict [str ,Any ]]:
        """Get lights data."""
        lights_data =[]
        for light in bpy .data .lights :
            light_data ={
            "name":light .name ,
            "type":light .type ,
            "energy":light .energy ,
            "color":to_json_serializable (light .color ),
            "users":light .users 
            }


            if light .type =='SUN':
                light_data ["angle"]=light .angle 
            elif light .type in ['POINT','SPOT']:
                light_data ["shadow_soft_size"]=light .shadow_soft_size 
            elif light .type =='AREA':
                light_data ["size"]=light .size 
                light_data ["shape"]=light .shape 

            lights_data .append (light_data )

        return lights_data 

    def _get_cameras_data (self ,context )->List [Dict [str ,Any ]]:
        """Get cameras data."""
        cameras_data =[]
        for cam in bpy .data .cameras :
            cam_data ={
            "name":cam .name ,
            "type":cam .type ,
            "focal_length":cam .lens ,
            "sensor_width":cam .sensor_width ,
            "sensor_height":cam .sensor_height ,
            "clip_start":cam .clip_start ,
            "clip_end":cam .clip_end ,
            "users":cam .users 
            }
            cameras_data .append (cam_data )

        return cameras_data 

    def _get_collections_data (self ,context )->List [Dict [str ,Any ]]:
        """Get collections data."""
        collections_data =[]
        for coll in bpy .data .collections :
            coll_data ={
            "name":coll .name ,
            "objects":[obj .name for obj in coll .objects ],
            "object_count":len (coll .objects ),
            "children":[child .name for child in coll .children ],
            "hide_viewport":coll .hide_viewport ,
            "hide_render":coll .hide_render 
            }
            collections_data .append (coll_data )

        return collections_data 

    def _get_scenes_data (self ,context )->List [Dict [str ,Any ]]:
        """Get scenes data."""
        scenes_data =[]
        for scene in bpy .data .scenes :
            scene_data ={
            "name":scene .name ,
            "frame_start":scene .frame_start ,
            "frame_end":scene .frame_end ,
            "frame_current":scene .frame_current ,
            "render_engine":scene .render .engine ,
            "resolution_x":scene .render .resolution_x ,
            "resolution_y":scene .render .resolution_y ,
            "fps":scene .render .fps ,
            "object_count":len (scene .objects ),
            "active":scene ==context .scene 
            }
            scenes_data .append (scene_data )

        return scenes_data 

    def _get_worlds_data (self ,context )->List [Dict [str ,Any ]]:
        """Get world data."""
        worlds_data =[]
        for world in bpy .data .worlds :
            world_data ={
            "name":world .name ,
            "use_nodes":world .use_nodes ,
            "users":world .users 
            }


            if world .use_nodes and world .node_tree :
                world_data ["node_count"]=len (world .node_tree .nodes )
                world_data ["output_nodes"]=[n .name for n in world .node_tree .nodes if n .type =='OUTPUT_WORLD']


                for node in world .node_tree .nodes :
                    if node .type =='BACKGROUND':
                        if 'Color'in node .inputs :
                            world_data ["background_color"]=to_json_serializable (node .inputs ['Color'].default_value )
                        if 'Strength'in node .inputs :
                            world_data ["background_strength"]=node .inputs ['Strength'].default_value 
                        break 
            else :
                if hasattr (world ,'color'):
                    world_data ["color"]=to_json_serializable (world .color )

            worlds_data .append (world_data )

        return worlds_data 

    def _get_images_data (self ,context )->List [Dict [str ,Any ]]:
        """Get image data."""
        images_data =[]
        for img in bpy .data .images :
            img_data ={
            "name":img .name ,
            "filepath":img .filepath ,
            "width":img .size [0 ]if img .size else 0 ,
            "height":img .size [1 ]if img .size else 0 ,
            "channels":img .channels ,
            "depth":img .depth ,
            "users":img .users ,
            "has_data":img .has_data ,
            "is_dirty":img .is_dirty ,
            "packed":img .packed_file is not None 
            }


            colorspace ="unknown"


            if img .name in ['Render Result','Viewer Node']:
                colorspace ="render"
            else :

                try :
                    if hasattr (img ,'colorspace_settings')and img .colorspace_settings :
                        cs_name =str (img .colorspace_settings .name )
                        if cs_name and cs_name .strip ()and cs_name !='0':
                            colorspace =cs_name 
                        else :
                            colorspace ="sRGB"
                except :
                    colorspace ="sRGB"

            img_data ["colorspace"]=colorspace 
            images_data .append (img_data )

        return images_data 

    def _get_render_settings_data (self ,context )->List [Dict [str ,Any ]]:
        """Get render settings data."""
        render_settings_data =[]

        for scene in bpy .data .scenes :
            render =scene .render 

            render_data ={
            "scene_name":scene .name ,
            "render_engine":render .engine ,
            "resolution_x":render .resolution_x ,
            "resolution_y":render .resolution_y ,
            "resolution_percentage":render .resolution_percentage ,
            "fps":render .fps ,
            "frame_start":scene .frame_start ,
            "frame_end":scene .frame_end ,
            "frame_current":scene .frame_current ,
            "filepath":render .filepath ,
            "image_format":render .image_settings .file_format ,
            "color_mode":render .image_settings .color_mode ,
            "color_depth":render .image_settings .color_depth ,
            "active":scene ==context .scene ,

            "samples":None ,
            "preview_samples":None ,
            "use_denoising":None ,
            "device":None ,
            "tile_size":None ,
            "use_adaptive_sampling":None ,
            "taa_render_samples":None ,
            "taa_samples":None ,
            "use_bloom":None ,
            "use_ssr":None ,
            "use_motion_blur":None ,
            "use_volumetric_lights":None 
            }


            if render .engine =='CYCLES':
                cycles =scene .cycles 
                render_data .update ({
                "samples":getattr (cycles ,'samples',None ),
                "preview_samples":getattr (cycles ,'preview_samples',None ),
                "use_denoising":getattr (cycles ,'use_denoising',None ),
                "device":getattr (cycles ,'device',None ),
                "tile_size":getattr (cycles ,'tile_size',None ),
                "use_adaptive_sampling":getattr (cycles ,'use_adaptive_sampling',None )
                })
            elif render .engine =='BLENDER_EEVEE'or render .engine =='BLENDER_EEVEE_NEXT':
                eevee =scene .eevee 
                render_data .update ({
                "taa_render_samples":getattr (eevee ,'taa_render_samples',None ),
                "taa_samples":getattr (eevee ,'taa_samples',None ),
                "use_bloom":getattr (eevee ,'use_bloom',None ),
                "use_ssr":getattr (eevee ,'use_ssr',None ),
                "use_motion_blur":getattr (eevee ,'use_motion_blur',None ),
                "use_volumetric_lights":getattr (eevee ,'use_volumetric_lights',None )
                })

            render_settings_data .append (render_data )

        return render_settings_data 

    def _get_nodes_data (self ,context )->List [Dict [str ,Any ]]:
        """Get comprehensive nodes data from shader, geometry, and compositor node trees."""
        nodes_data =[]


        for material in bpy .data .materials :
            if material .use_nodes and material .node_tree :
                node_tree =material .node_tree 
                for node in node_tree .nodes :
                    node_data =self ._extract_node_data (
                    node ,
                    tree_type ="SHADER",
                    tree_owner =material .name ,
                    tree_owner_type ="MATERIAL",
                    node_tree =node_tree 
                    )
                    nodes_data .append (node_data )


        for world in bpy .data .worlds :
            if world .use_nodes and world .node_tree :
                node_tree =world .node_tree 
                for node in node_tree .nodes :
                    node_data =self ._extract_node_data (
                    node ,
                    tree_type ="SHADER",
                    tree_owner =world .name ,
                    tree_owner_type ="WORLD",
                    node_tree =node_tree 
                    )
                    nodes_data .append (node_data )


        for obj in bpy .data .objects :
            for modifier in obj .modifiers :
                if modifier .type =='NODES'and modifier .node_group :
                    node_tree =modifier .node_group 
                    for node in node_tree .nodes :
                        node_data =self ._extract_node_data (
                        node ,
                        tree_type ="GEOMETRY",
                        tree_owner =f"{obj.name}.{modifier.name}",
                        tree_owner_type ="MODIFIER",
                        node_tree =node_tree 
                        )
                        nodes_data .append (node_data )


        for node_group in bpy .data .node_groups :
            if node_group .type =='GEOMETRY':
                for node in node_group .nodes :
                    node_data =self ._extract_node_data (
                    node ,
                    tree_type ="GEOMETRY",
                    tree_owner =node_group .name ,
                    tree_owner_type ="NODE_GROUP",
                    node_tree =node_group 
                    )
                    nodes_data .append (node_data )


        for scene in bpy .data .scenes :
            if scene .use_nodes and scene .node_tree :
                node_tree =scene .node_tree 
                for node in node_tree .nodes :
                    node_data =self ._extract_node_data (
                    node ,
                    tree_type ="COMPOSITOR",
                    tree_owner =scene .name ,
                    tree_owner_type ="SCENE",
                    node_tree =node_tree 
                    )
                    nodes_data .append (node_data )

        return nodes_data 

    def _extract_node_data (self ,node ,tree_type :str ,tree_owner :str ,
    tree_owner_type :str ,node_tree )->Dict [str ,Any ]:
        """Extract comprehensive data from a single node."""


        node_data ={

        "tree_type":tree_type ,
        "tree_owner":tree_owner ,
        "tree_owner_type":tree_owner_type ,
        "tree_name":node_tree .name if hasattr (node_tree ,'name')else tree_owner ,


        "node_name":node .name ,
        "node_type":node .type ,
        "node_bl_idname":node .bl_idname ,
        "node_category":self ._get_node_category (node .type ),
        "node_description":self ._get_node_description (node .type ),


        "location_x":round (node .location .x ,2 ),
        "location_y":round (node .location .y ,2 ),
        "width":round (node .width ,2 ),
        "height":round (node .height ,2 ),
        "hide":node .hide ,
        "mute":node .mute ,
        "select":node .select ,
        "label":node .label or "",
        "color":to_json_serializable (node .color )if hasattr (node ,'color')else None ,
        "use_custom_color":getattr (node ,'use_custom_color',False ),


        "inputs_count":len (node .inputs ),
        "outputs_count":len (node .outputs ),
        "input_sockets":self ._extract_socket_info (node .inputs ),
        "output_sockets":self ._extract_socket_info (node .outputs ),


        "connections":self ._extract_node_connections (node ,node_tree ),
        "is_output_node":self ._is_output_node (node ),
        "is_input_node":self ._is_input_node (node ),


        "properties":self ._extract_node_properties (node ),
        }


        if hasattr (node ,'parent')and node .parent :
            node_data ["parent_node"]=node .parent .name 


        if hasattr (node ,'parent')and node .parent and node .parent .type =='FRAME':
            node_data ["frame_name"]=node .parent .name 

        return node_data 

    def _extract_socket_info (self ,sockets )->List [Dict [str ,Any ]]:
        """Extract information about node sockets."""
        socket_info =[]

        for socket in sockets :
            socket_data ={
            "name":socket .name ,
            "type":socket .type ,
            "bl_idname":socket .bl_idname ,
            "enabled":socket .enabled ,
            "hide":socket .hide ,
            "hide_value":getattr (socket ,'hide_value',False ),
            "is_linked":socket .is_linked ,
            "is_output":socket .is_output ,
            "default_value":None ,
            "links_count":len (socket .links )if hasattr (socket ,'links')else 0 ,
            }


            if hasattr (socket ,'default_value')and not socket .is_linked :
                try :
                    default_val =socket .default_value 
                    if hasattr (default_val ,'__len__')and not isinstance (default_val ,str ):

                        socket_data ["default_value"]=to_json_serializable (default_val )
                    else :

                        socket_data ["default_value"]=default_val 
                except :
                    socket_data ["default_value"]=None 

            socket_info .append (socket_data )

        return socket_info 

    def _extract_node_connections (self ,node ,node_tree )->Dict [str ,Any ]:
        """Extract connection information for a node."""
        connections ={
        "input_connections":[],
        "output_connections":[],
        "total_input_links":0 ,
        "total_output_links":0 ,
        }


        for socket in node .inputs :
            for link in socket .links :
                if link .is_valid :
                    connections ["input_connections"].append ({
                    "socket_name":socket .name ,
                    "socket_type":socket .type ,
                    "from_node":link .from_node .name ,
                    "from_socket":link .from_socket .name ,
                    "from_socket_type":link .from_socket .type ,
                    })
                    connections ["total_input_links"]+=1 


        for socket in node .outputs :
            for link in socket .links :
                if link .is_valid :
                    connections ["output_connections"].append ({
                    "socket_name":socket .name ,
                    "socket_type":socket .type ,
                    "to_node":link .to_node .name ,
                    "to_socket":link .to_socket .name ,
                    "to_socket_type":link .to_socket .type ,
                    })
                    connections ["total_output_links"]+=1 

        return connections 

    def _extract_node_properties (self ,node )->Dict [str ,Any ]:
        """Extract type-specific properties from a node."""
        properties ={}


        if node .type =='BSDF_PRINCIPLED':
            properties .update ({
            "distribution":getattr (node ,'distribution','MULTISCATTER_GGX'),
            "subsurface_method":getattr (node ,'subsurface_method','RANDOM_WALK'),
            })
        elif node .type =='TEX_IMAGE':
            properties .update ({
            "image_name":node .image .name if node .image else None ,
            "image_filepath":node .image .filepath if node .image else None ,
            "interpolation":getattr (node ,'interpolation','Linear'),
            "projection":getattr (node ,'projection','FLAT'),
            "extension":getattr (node ,'extension','REPEAT'),
            })
        elif node .type =='TEX_NOISE':
            properties .update ({
            "noise_dimensions":getattr (node ,'noise_dimensions','3D'),
            "noise_type":getattr (node ,'noise_type','FBM'),
            "normalize":getattr (node ,'normalize',True ),
            })
        elif node .type =='MAPPING':
            properties .update ({
            "vector_type":getattr (node ,'vector_type','POINT'),
            })
        elif node .type =='BACKGROUND':
            properties .update ({
            "shader_type":"background",
            })
        elif node .type in ['COMPOSITE','VIEWER']:
            properties .update ({
            "use_alpha":getattr (node ,'use_alpha',False ),
            })
        elif node .type =='MIX':
            properties .update ({
            "data_type":getattr (node ,'data_type','FLOAT'),
            "blend_type":getattr (node ,'blend_type','MIX'),
            "use_clamp":getattr (node ,'use_clamp',False ),
            })
        elif node .type =='MATH':
            properties .update ({
            "operation":getattr (node ,'operation','ADD'),
            "use_clamp":getattr (node ,'use_clamp',False ),
            })
        elif node .type =='VECT_MATH':
            properties .update ({
            "operation":getattr (node ,'operation','ADD'),
            })
        elif node .type =='COLORMANAGEMENT':
            properties .update ({
            "from_color_space":getattr (node ,'from_color_space',''),
            "to_color_space":getattr (node ,'to_color_space',''),
            })
        elif node .type =='OUTPUT_MATERIAL':
            properties .update ({
            "is_active_output":getattr (node ,'is_active_output',True ),
            "target":getattr (node ,'target','ALL'),
            })
        elif node .type =='OUTPUT_WORLD':
            properties .update ({
            "is_active_output":getattr (node ,'is_active_output',True ),
            "target":getattr (node ,'target','ALL'),
            })


        if node .type .startswith ('GEO_'):
            properties .update ({
            "geometry_node_type":node .type ,
            })


        if hasattr (node ,'keys'):
            for key in node .keys ():
                if not key .startswith ('_'):
                    try :
                        properties [f"custom_{key}"]=to_json_serializable (node [key ])
                    except :
                        properties [f"custom_{key}"]=str (node [key ])

        return properties 

    def _get_node_category (self ,node_type :str )->str :
        """Get the category for a node type."""
        categories ={

        'BSDF_PRINCIPLED':'Shader',
        'BSDF_DIFFUSE':'Shader',
        'BSDF_GLOSSY':'Shader',
        'BSDF_TRANSPARENT':'Shader',
        'BSDF_TRANSLUCENT':'Shader',
        'BSDF_GLASS':'Shader',
        'BSDF_EMISSION':'Shader',
        'SUBSURFACE_SCATTERING':'Shader',
        'VOLUME_ABSORPTION':'Shader',
        'VOLUME_SCATTER':'Shader',
        'HOLDOUT':'Shader',


        'TEX_IMAGE':'Texture',
        'TEX_NOISE':'Texture',
        'TEX_WAVE':'Texture',
        'TEX_VORONOI':'Texture',
        'TEX_MUSGRAVE':'Texture',
        'TEX_GRADIENT':'Texture',
        'TEX_MAGIC':'Texture',
        'TEX_CHECKER':'Texture',
        'TEX_BRICK':'Texture',
        'TEX_COORD':'Texture',
        'TEX_ENVIRONMENT':'Texture',
        'TEX_SKY':'Texture',
        'TEX_IES':'Texture',
        'TEX_POINTDENSITY':'Texture',


        'MAPPING':'Vector',
        'VECT_MATH':'Vector',
        'VECT_TRANSFORM':'Vector',
        'NORMAL':'Vector',
        'NORMAL_MAP':'Vector',
        'CURVE_VEC':'Vector',
        'DISPLACEMENT':'Vector',
        'VECTOR_DISPLACEMENT':'Vector',
        'BUMP':'Vector',


        'MIX':'Color',
        'INVERT':'Color',
        'CURVE_RGB':'Color',
        'BRIGHTCONTRAST':'Color',
        'GAMMA':'Color',
        'HUE_SAT':'Color',
        'RGB':'Color',
        'BLACKBODY':'Color',
        'WAVELENGTH':'Color',
        'COLORMANAGEMENT':'Color',


        'MATH':'Converter',
        'RGBTOBW':'Converter',
        'VALTORGB':'Converter',
        'COMBINE_COLOR':'Converter',
        'SEPARATE_COLOR':'Converter',
        'COMBINE_XYZ':'Converter',
        'SEPARATE_XYZ':'Converter',
        'COMBINE_RGB':'Converter',
        'SEPARATE_RGB':'Converter',
        'COMBINE_HSV':'Converter',
        'SEPARATE_HSV':'Converter',
        'WAVELENGTH':'Converter',
        'BLACKBODY':'Converter',
        'CLAMP':'Converter',
        'MAP_RANGE':'Converter',
        'FLOATCURVE':'Converter',


        'OUTPUT_MATERIAL':'Output',
        'OUTPUT_WORLD':'Output',
        'OUTPUT_LIGHT':'Output',


        'ATTRIBUTE':'Input',
        'CAMERA':'Input',
        'FRESNEL':'Input',
        'GEOMETRY':'Input',
        'HAIR_INFO':'Input',
        'LAYER_WEIGHT':'Input',
        'LIGHT_PATH':'Input',
        'OBJECT_INFO':'Input',
        'PARTICLE_INFO':'Input',
        'TANGENT':'Input',
        'UVMAP':'Input',
        'VERTEX_COLOR':'Input',
        'WIREFRAME':'Input',
        'AMBIENT_OCCLUSION':'Input',
        'BEVEL':'Input',


        'COMPOSITE':'Compositor',
        'VIEWER':'Compositor',
        'SPLITVIEWER':'Compositor',
        'OUTPUT_FILE':'Compositor',
        'LEVELS':'Compositor',
        'BLUR':'Compositor',
        'FILTER':'Compositor',
        'GLARE':'Compositor',
        'TONEMAP':'Compositor',
        'LENSDIST':'Compositor',
        'COLORBALANCE':'Compositor',
        'HUECORRECT':'Compositor',
        'MOVIEDISTORTION':'Compositor',
        'STABILIZE2D':'Compositor',
        'TRANSFORM':'Compositor',
        'TRANSLATE':'Compositor',
        'ROTATE':'Compositor',
        'SCALE':'Compositor',
        'FLIP':'Compositor',
        'CROP':'Compositor',
        'MASK':'Compositor',
        'KEYINGSCREEN':'Compositor',
        'KEYING':'Compositor',
        'CHANNELMATTE':'Compositor',
        'COLORMATTE':'Compositor',
        'DIFFMATTE':'Compositor',
        'DISTANCEMATTE':'Compositor',
        'LUMAKEY':'Compositor',
        'CHROMAMATTE':'Compositor',
        'COLORSPILL':'Compositor',
        'BOKEHBLUR':'Compositor',
        'BOKEHIMAGE':'Compositor',
        'SWITCH':'Compositor',
        'FRAME':'Layout',
        'REROUTE':'Layout',
        'GROUP':'Group',
        'GROUP_INPUT':'Group',
        'GROUP_OUTPUT':'Group',
        }


        if node_type .startswith ('GEO_'):
            return 'Geometry'

        return categories .get (node_type ,'Unknown')

    def _get_node_description (self ,node_type :str )->str :
        """Get a human-readable description for a node type."""
        descriptions ={
        'BSDF_PRINCIPLED':'Physically-based surface shader',
        'BSDF_DIFFUSE':'Lambertian diffuse surface shader',
        'BSDF_GLOSSY':'Glossy reflection surface shader',
        'BSDF_TRANSPARENT':'Transparent surface shader',
        'BSDF_TRANSLUCENT':'Translucent surface shader',
        'BSDF_GLASS':'Glass surface shader',
        'BSDF_EMISSION':'Emission surface shader',
        'TEX_IMAGE':'Image texture node',
        'TEX_NOISE':'Noise texture generator',
        'TEX_WAVE':'Wave texture generator',
        'TEX_VORONOI':'Voronoi texture generator',
        'TEX_MUSGRAVE':'Musgrave texture generator',
        'TEX_GRADIENT':'Gradient texture generator',
        'TEX_MAGIC':'Magic texture generator',
        'TEX_CHECKER':'Checker texture generator',
        'TEX_BRICK':'Brick texture generator',
        'MAPPING':'Coordinate mapping and transformation',
        'VECT_MATH':'Vector mathematics operations',
        'MATH':'Mathematical operations',
        'MIX':'Mix or blend values/colors',
        'INVERT':'Invert colors',
        'CURVE_RGB':'RGB color curves',
        'BRIGHTCONTRAST':'Brightness and contrast adjustment',
        'GAMMA':'Gamma correction',
        'HUE_SAT':'Hue/saturation adjustment',
        'RGB':'RGB color input',
        'BLACKBODY':'Blackbody emission color',
        'WAVELENGTH':'Wavelength to color conversion',
        'COLORMANAGEMENT':'Color space conversion',
        'RGBTOBW':'RGB to black and white conversion',
        'VALTORGB':'Value to RGB conversion (ColorRamp)',
        'COMBINE_COLOR':'Combine color channels',
        'SEPARATE_COLOR':'Separate color channels',
        'COMBINE_XYZ':'Combine XYZ vector',
        'SEPARATE_XYZ':'Separate XYZ vector',
        'CLAMP':'Clamp values to range',
        'MAP_RANGE':'Map value range',
        'OUTPUT_MATERIAL':'Material output',
        'OUTPUT_WORLD':'World output',
        'OUTPUT_LIGHT':'Light output',
        'ATTRIBUTE':'Geometry attribute input',
        'CAMERA':'Camera data input',
        'FRESNEL':'Fresnel effect input',
        'GEOMETRY':'Geometry data input',
        'LAYER_WEIGHT':'Layer weight input',
        'LIGHT_PATH':'Light path input',
        'OBJECT_INFO':'Object information input',
        'UVMAP':'UV map input',
        'VERTEX_COLOR':'Vertex color input',
        'WIREFRAME':'Wireframe input',
        'AMBIENT_OCCLUSION':'Ambient occlusion input',
        'BEVEL':'Bevel input',
        'COMPOSITE':'Composite output',
        'VIEWER':'Viewer output',
        'BLUR':'Blur filter',
        'FILTER':'Filter operations',
        'GLARE':'Glare effect',
        'TONEMAP':'Tone mapping',
        'COLORBALANCE':'Color balance adjustment',
        'HUECORRECT':'Hue correction',
        'TRANSFORM':'Transform operations',
        'TRANSLATE':'Translation transform',
        'ROTATE':'Rotation transform',
        'SCALE':'Scale transform',
        'FLIP':'Flip transform',
        'CROP':'Crop operation',
        'MASK':'Mask operation',
        'KEYING':'Keying/chroma key',
        'KEYINGSCREEN':'Keying screen',
        'CHANNELMATTE':'Channel matte',
        'COLORMATTE':'Color matte',
        'DIFFMATTE':'Difference matte',
        'DISTANCEMATTE':'Distance matte',
        'LUMAKEY':'Luma key',
        'CHROMAMATTE':'Chroma matte',
        'COLORSPILL':'Color spill suppression',
        'BOKEHBLUR':'Bokeh blur',
        'BOKEHIMAGE':'Bokeh image',
        'SWITCH':'Switch input',
        'FRAME':'Frame for organization',
        'REROUTE':'Reroute connection',
        'GROUP':'Node group',
        'GROUP_INPUT':'Group input',
        'GROUP_OUTPUT':'Group output',
        }

        if node_type .startswith ('GEO_'):
            return f'Geometry node: {node_type}'

        return descriptions .get (node_type ,f'Node type: {node_type}')

    def _is_output_node (self ,node )->bool :
        """Check if node is an output node."""
        output_types ={
        'OUTPUT_MATERIAL','OUTPUT_WORLD','OUTPUT_LIGHT',
        'COMPOSITE','VIEWER','SPLITVIEWER','OUTPUT_FILE',
        'GROUP_OUTPUT'
        }
        return node .type in output_types 

    def _is_input_node (self ,node )->bool :
        """Check if node is an input node."""
        input_types ={
        'ATTRIBUTE','CAMERA','FRESNEL','GEOMETRY','HAIR_INFO',
        'LAYER_WEIGHT','LIGHT_PATH','OBJECT_INFO','PARTICLE_INFO',
        'TANGENT','UVMAP','VERTEX_COLOR','WIREFRAME','AMBIENT_OCCLUSION',
        'BEVEL','TEX_COORD','RGB','VALUE','GROUP_INPUT',
        'RENDER_LAYERS','IMAGE','MOVIECLIP','MASK','TIME'
        }
        return node .type in input_types 

    def _get_tables_data (self ,context )->List [Dict [str ,Any ]]:
        """Get meta information about available tables."""
        tables_data =[]
        for table_name ,description in self .available_tables .items ():
            tables_data .append ({
            "table":table_name ,
            "description":description 
            })
        return tables_data 

    def _select_fields (self ,data :List [Dict ],fields :List [str ])->List [Dict ]:
        """Select specific fields from data, including nested fields."""
        selected_data =[]

        for item in data :
            selected_item ={}
            for field in fields :
                field =field .strip ()

                if '.'in field :

                    field_parts =field .split ('.')
                    current_value =item 


                    for part in field_parts :
                        if isinstance (current_value ,dict )and part in current_value :
                            current_value =current_value [part ]
                        else :
                            current_value =None 
                            break 

                    selected_item [field ]=current_value 
                else :

                    if field in item :
                        selected_item [field ]=item [field ]
                    else :
                        selected_item [field ]=None 

            selected_data .append (selected_item )

        return selected_data 

    def _get_shader_nodes_data (self ,context )->List [Dict [str ,Any ]]:
        """Get only shader nodes from materials and worlds."""
        all_nodes =self ._get_nodes_data (context )
        return [node for node in all_nodes if node ['tree_type']=='SHADER']

    def _get_geometry_nodes_data (self ,context )->List [Dict [str ,Any ]]:
        """Get only geometry nodes from modifiers and node groups."""
        all_nodes =self ._get_nodes_data (context )
        return [node for node in all_nodes if node ['tree_type']=='GEOMETRY']

    def _get_compositor_nodes_data (self ,context )->List [Dict [str ,Any ]]:
        """Get only compositor nodes from scenes."""
        all_nodes =self ._get_nodes_data (context )
        return [node for node in all_nodes if node ['tree_type']=='COMPOSITOR']

    def _get_node_connections_data (self ,context )->List [Dict [str ,Any ]]:
        """Get flattened connection data between nodes."""
        connections_data =[]
        all_nodes =self ._get_nodes_data (context )

        for node in all_nodes :
            node_id =f"{node['tree_owner']}.{node['node_name']}"


            for connection in node ['connections']['input_connections']:
                connections_data .append ({
                'connection_type':'input',
                'tree_type':node ['tree_type'],
                'tree_owner':node ['tree_owner'],
                'tree_owner_type':node ['tree_owner_type'],
                'node_name':node ['node_name'],
                'node_id':node_id ,
                'socket_name':connection ['socket_name'],
                'socket_type':connection ['socket_type'],
                'connected_node':connection ['from_node'],
                'connected_socket':connection ['from_socket'],
                'connected_socket_type':connection ['from_socket_type'],
                'connected_node_id':f"{node['tree_owner']}.{connection['from_node']}"
                })


            for connection in node ['connections']['output_connections']:
                connections_data .append ({
                'connection_type':'output',
                'tree_type':node ['tree_type'],
                'tree_owner':node ['tree_owner'],
                'tree_owner_type':node ['tree_owner_type'],
                'node_name':node ['node_name'],
                'node_id':node_id ,
                'socket_name':connection ['socket_name'],
                'socket_type':connection ['socket_type'],
                'connected_node':connection ['to_node'],
                'connected_socket':connection ['to_socket'],
                'connected_socket_type':connection ['to_socket_type'],
                'connected_node_id':f"{node['tree_owner']}.{connection['to_node']}"
                })

        return connections_data 

    def _get_node_sockets_data (self ,context )->List [Dict [str ,Any ]]:
        """Get flattened socket data from all nodes."""
        sockets_data =[]
        all_nodes =self ._get_nodes_data (context )

        for node in all_nodes :
            node_id =f"{node['tree_owner']}.{node['node_name']}"


            for socket in node ['input_sockets']:
                sockets_data .append ({
                'socket_direction':'input',
                'tree_type':node ['tree_type'],
                'tree_owner':node ['tree_owner'],
                'tree_owner_type':node ['tree_owner_type'],
                'node_name':node ['node_name'],
                'node_id':node_id ,
                'node_type':node ['node_type'],
                'socket_name':socket ['name'],
                'socket_type':socket ['type'],
                'socket_bl_idname':socket ['bl_idname'],
                'enabled':socket ['enabled'],
                'hide':socket ['hide'],
                'hide_value':socket ['hide_value'],
                'is_linked':socket ['is_linked'],
                'default_value':socket ['default_value'],
                'links_count':socket ['links_count']
                })


            for socket in node ['output_sockets']:
                sockets_data .append ({
                'socket_direction':'output',
                'tree_type':node ['tree_type'],
                'tree_owner':node ['tree_owner'],
                'tree_owner_type':node ['tree_owner_type'],
                'node_name':node ['node_name'],
                'node_id':node_id ,
                'node_type':node ['node_type'],
                'socket_name':socket ['name'],
                'socket_type':socket ['type'],
                'socket_bl_idname':socket ['bl_idname'],
                'enabled':socket ['enabled'],
                'hide':socket ['hide'],
                'hide_value':socket ['hide_value'],
                'is_linked':socket ['is_linked'],
                'default_value':socket ['default_value'],
                'links_count':socket ['links_count']
                })

        return sockets_data 

    def _get_node_trees_data (self ,context )->List [Dict [str ,Any ]]:
        """Get information about node trees and their contents."""
        trees_data =[]


        for material in bpy .data .materials :
            if material .use_nodes and material .node_tree :
                tree =material .node_tree 
                trees_data .append ({
                'tree_name':tree .name ,
                'tree_type':'SHADER',
                'owner_name':material .name ,
                'owner_type':'MATERIAL',
                'nodes_count':len (tree .nodes ),
                'links_count':len (tree .links ),
                'input_nodes':[n .name for n in tree .nodes if self ._is_input_node (n )],
                'output_nodes':[n .name for n in tree .nodes if self ._is_output_node (n )],
                'node_types':list (set (n .type for n in tree .nodes )),
                'active_output':next ((n .name for n in tree .nodes if n .type =='OUTPUT_MATERIAL'and getattr (n ,'is_active_output',True )),None )
                })


        for world in bpy .data .worlds :
            if world .use_nodes and world .node_tree :
                tree =world .node_tree 
                trees_data .append ({
                'tree_name':tree .name ,
                'tree_type':'SHADER',
                'owner_name':world .name ,
                'owner_type':'WORLD',
                'nodes_count':len (tree .nodes ),
                'links_count':len (tree .links ),
                'input_nodes':[n .name for n in tree .nodes if self ._is_input_node (n )],
                'output_nodes':[n .name for n in tree .nodes if self ._is_output_node (n )],
                'node_types':list (set (n .type for n in tree .nodes )),
                'active_output':next ((n .name for n in tree .nodes if n .type =='OUTPUT_WORLD'and getattr (n ,'is_active_output',True )),None )
                })


        for obj in bpy .data .objects :
            for modifier in obj .modifiers :
                if modifier .type =='NODES'and modifier .node_group :
                    tree =modifier .node_group 
                    trees_data .append ({
                    'tree_name':tree .name ,
                    'tree_type':'GEOMETRY',
                    'owner_name':f"{obj.name}.{modifier.name}",
                    'owner_type':'MODIFIER',
                    'nodes_count':len (tree .nodes ),
                    'links_count':len (tree .links ),
                    'input_nodes':[n .name for n in tree .nodes if n .type =='GROUP_INPUT'],
                    'output_nodes':[n .name for n in tree .nodes if n .type =='GROUP_OUTPUT'],
                    'node_types':list (set (n .type for n in tree .nodes )),
                    'active_output':next ((n .name for n in tree .nodes if n .type =='GROUP_OUTPUT'),None )
                    })


        for node_group in bpy .data .node_groups :
            if node_group .type =='GEOMETRY':
                trees_data .append ({
                'tree_name':node_group .name ,
                'tree_type':'GEOMETRY',
                'owner_name':node_group .name ,
                'owner_type':'NODE_GROUP',
                'nodes_count':len (node_group .nodes ),
                'links_count':len (node_group .links ),
                'input_nodes':[n .name for n in node_group .nodes if n .type =='GROUP_INPUT'],
                'output_nodes':[n .name for n in node_group .nodes if n .type =='GROUP_OUTPUT'],
                'node_types':list (set (n .type for n in node_group .nodes )),
                'active_output':next ((n .name for n in node_group .nodes if n .type =='GROUP_OUTPUT'),None )
                })


        for scene in bpy .data .scenes :
            if scene .use_nodes and scene .node_tree :
                tree =scene .node_tree 
                trees_data .append ({
                'tree_name':tree .name ,
                'tree_type':'COMPOSITOR',
                'owner_name':scene .name ,
                'owner_type':'SCENE',
                'nodes_count':len (tree .nodes ),
                'links_count':len (tree .links ),
                'input_nodes':[n .name for n in tree .nodes if self ._is_input_node (n )],
                'output_nodes':[n .name for n in tree .nodes if self ._is_output_node (n )],
                'node_types':list (set (n .type for n in tree .nodes )),
                'active_output':next ((n .name for n in tree .nodes if n .type =='COMPOSITE'),None )
                })

        return trees_data 

    def _get_node_groups_data (self ,context )->List [Dict [str ,Any ]]:
        """Get information about node groups and their usage."""
        groups_data =[]

        for node_group in bpy .data .node_groups :
            group_data ={
            'name':node_group .name ,
            'type':node_group .type ,
            'users':node_group .users ,
            'nodes_count':len (node_group .nodes ),
            'links_count':len (node_group .links ),
            'inputs_count':len (node_group .inputs )if hasattr (node_group ,'inputs')else 0 ,
            'outputs_count':len (node_group .outputs )if hasattr (node_group ,'outputs')else 0 ,
            'interface_inputs':[],
            'interface_outputs':[],
            'used_in_materials':[],
            'used_in_modifiers':[],
            'used_in_worlds':[],
            'used_in_scenes':[],
            'nested_groups':[]
            }


            if hasattr (node_group ,'inputs'):
                for inp in node_group .inputs :
                    group_data ['interface_inputs'].append ({
                    'name':inp .name ,
                    'type':inp .type ,
                    'bl_socket_idname':inp .bl_socket_idname ,
                    'default_value':to_json_serializable (getattr (inp ,'default_value',None ))
                    })

            if hasattr (node_group ,'outputs'):
                for out in node_group .outputs :
                    group_data ['interface_outputs'].append ({
                    'name':out .name ,
                    'type':out .type ,
                    'bl_socket_idname':out .bl_socket_idname 
                    })


            for material in bpy .data .materials :
                if material .use_nodes and material .node_tree :
                    for node in material .node_tree .nodes :
                        if node .type =='GROUP'and node .node_tree ==node_group :
                            group_data ['used_in_materials'].append (material .name )

            for obj in bpy .data .objects :
                for modifier in obj .modifiers :
                    if modifier .type =='NODES'and modifier .node_group ==node_group :
                        group_data ['used_in_modifiers'].append (f"{obj.name}.{modifier.name}")

            for world in bpy .data .worlds :
                if world .use_nodes and world .node_tree :
                    for node in world .node_tree .nodes :
                        if node .type =='GROUP'and node .node_tree ==node_group :
                            group_data ['used_in_worlds'].append (world .name )

            for scene in bpy .data .scenes :
                if scene .use_nodes and scene .node_tree :
                    for node in scene .node_tree .nodes :
                        if node .type =='GROUP'and node .node_tree ==node_group :
                            group_data ['used_in_scenes'].append (scene .name )


            for node in node_group .nodes :
                if node .type =='GROUP'and node .node_tree :
                    group_data ['nested_groups'].append (node .node_tree .name )

            groups_data .append (group_data )

        return groups_data 

    def _get_modifiers_data (self ,context )->List [Dict [str ,Any ]]:
        """Get object modifiers and their properties."""
        modifiers_data =[]

        for obj in bpy .data .objects :
            for modifier in obj .modifiers :
                mod_data ={
                'object_name':obj .name ,
                'modifier_name':modifier .name ,
                'modifier_type':modifier .type ,
                'show_viewport':modifier .show_viewport ,
                'show_render':modifier .show_render ,
                'show_in_editmode':modifier .show_in_editmode ,
                'show_on_cage':modifier .show_on_cage ,
                'use_apply_on_spline':getattr (modifier ,'use_apply_on_spline',None ),
                'is_active':modifier ==obj .modifiers .active 
                }


                if modifier .type =='NODES':
                    mod_data .update ({
                    'node_group':modifier .node_group .name if modifier .node_group else None ,
                    'node_group_users':modifier .node_group .users if modifier .node_group else 0 
                    })
                elif modifier .type =='SUBSURF':
                    mod_data .update ({
                    'levels':modifier .levels ,
                    'render_levels':modifier .render_levels ,
                    'subdivision_type':modifier .subdivision_type 
                    })
                elif modifier .type =='MIRROR':
                    mod_data .update ({
                    'use_axis_x':modifier .use_axis [0 ],
                    'use_axis_y':modifier .use_axis [1 ],
                    'use_axis_z':modifier .use_axis [2 ],
                    'mirror_object':modifier .mirror_object .name if modifier .mirror_object else None 
                    })
                elif modifier .type =='ARRAY':
                    mod_data .update ({
                    'count':modifier .count ,
                    'use_relative_offset':modifier .use_relative_offset ,
                    'use_constant_offset':modifier .use_constant_offset ,
                    'use_object_offset':modifier .use_object_offset ,
                    'offset_object':modifier .offset_object .name if modifier .offset_object else None 
                    })
                elif modifier .type =='SOLIDIFY':
                    mod_data .update ({
                    'thickness':modifier .thickness ,
                    'offset':modifier .offset ,
                    'use_even_offset':modifier .use_even_offset 
                    })
                elif modifier .type =='BEVEL':
                    mod_data .update ({
                    'width':modifier .width ,
                    'segments':modifier .segments ,
                    'limit_method':modifier .limit_method 
                    })

                modifiers_data .append (mod_data )

        return modifiers_data 

    def _get_animations_data (self ,context )->List [Dict [str ,Any ]]:
        """Get animation data including keyframes and fcurves."""
        animations_data =[]


        for obj in bpy .data .objects :
            if obj .animation_data and obj .animation_data .action :
                action =obj .animation_data .action 

                for fcurve in action .fcurves :
                    anim_data ={
                    'object_name':obj .name ,
                    'object_type':obj .type ,
                    'action_name':action .name ,
                    'data_path':fcurve .data_path ,
                    'array_index':fcurve .array_index ,
                    'keyframes_count':len (fcurve .keyframe_points ),
                    'extrapolation':fcurve .extrapolation ,
                    'auto_smoothing':fcurve .auto_smoothing ,
                    'keyframe_values':[],
                    'keyframe_frames':[],
                    'modifiers_count':len (fcurve .modifiers )
                    }


                    for keyframe in fcurve .keyframe_points :
                        anim_data ['keyframe_frames'].append (keyframe .co .x )
                        anim_data ['keyframe_values'].append (keyframe .co .y )

                    animations_data .append (anim_data )


        for material in bpy .data .materials :
            if material .animation_data and material .animation_data .action :
                action =material .animation_data .action 

                for fcurve in action .fcurves :
                    anim_data ={
                    'object_name':material .name ,
                    'object_type':'MATERIAL',
                    'action_name':action .name ,
                    'data_path':fcurve .data_path ,
                    'array_index':fcurve .array_index ,
                    'keyframes_count':len (fcurve .keyframe_points ),
                    'extrapolation':fcurve .extrapolation ,
                    'auto_smoothing':fcurve .auto_smoothing ,
                    'keyframe_values':[],
                    'keyframe_frames':[],
                    'modifiers_count':len (fcurve .modifiers )
                    }

                    for keyframe in fcurve .keyframe_points :
                        anim_data ['keyframe_frames'].append (keyframe .co .x )
                        anim_data ['keyframe_values'].append (keyframe .co .y )

                    animations_data .append (anim_data )

        return animations_data 

    def _get_textures_data (self ,context )->List [Dict [str ,Any ]]:
        """Get legacy texture data blocks."""
        textures_data =[]

        for texture in bpy .data .textures :
            tex_data ={
            'name':texture .name ,
            'type':texture .type ,
            'users':texture .users ,
            'use_nodes':getattr (texture ,'use_nodes',False ),
            'noise_basis':getattr (texture ,'noise_basis',None ),
            'noise_type':getattr (texture ,'noise_type',None ),
            'noise_scale':getattr (texture ,'noise_scale',None ),
            'turbulence':getattr (texture ,'turbulence',None ),
            'contrast':getattr (texture ,'contrast',None ),
            'brightness':getattr (texture ,'brightness',None ),
            'saturation':getattr (texture ,'saturation',None ),
            }


            if texture .type =='IMAGE'and hasattr (texture ,'image'):
                tex_data ['image_name']=texture .image .name if texture .image else None 
                tex_data ['image_filepath']=texture .image .filepath if texture .image else None 

            textures_data .append (tex_data )

        return textures_data 

    def _get_drivers_data (self ,context )->List [Dict [str ,Any ]]:
        """Get driver expressions and dependencies."""
        drivers_data =[]

        def extract_drivers_from_id (data_block ,block_name ,block_type ):
            if data_block .animation_data and data_block .animation_data .drivers :
                for driver in data_block .animation_data .drivers :
                    driver_data ={
                    'owner_name':block_name ,
                    'owner_type':block_type ,
                    'data_path':driver .data_path ,
                    'array_index':driver .array_index ,
                    'expression':driver .driver .expression ,
                    'type':driver .driver .type ,
                    'variables_count':len (driver .driver .variables ),
                    'variables':[]
                    }

                    for var in driver .driver .variables :
                        var_data ={
                        'name':var .name ,
                        'type':var .type ,
                        'targets':[]
                        }

                        for target in var .targets :
                            target_data ={
                            'id_type':target .id_type ,
                            'id':target .id .name if target .id else None ,
                            'data_path':target .data_path ,
                            'transform_type':getattr (target ,'transform_type',None ),
                            'transform_space':getattr (target ,'transform_space',None ),
                            'rotation_mode':getattr (target ,'rotation_mode',None )
                            }
                            var_data ['targets'].append (target_data )

                        driver_data ['variables'].append (var_data )

                    drivers_data .append (driver_data )


        for obj in bpy .data .objects :
            extract_drivers_from_id (obj ,obj .name ,'OBJECT')

        for material in bpy .data .materials :
            extract_drivers_from_id (material ,material .name ,'MATERIAL')

        for world in bpy .data .worlds :
            extract_drivers_from_id (world ,world .name ,'WORLD')

        for scene in bpy .data .scenes :
            extract_drivers_from_id (scene ,scene .name ,'SCENE')

        return drivers_data 

    def _get_constraints_data (self ,context )->List [Dict [str ,Any ]]:
        """Get object and bone constraints."""
        constraints_data =[]


        for obj in bpy .data .objects :
            for constraint in obj .constraints :
                const_data ={
                'owner_name':obj .name ,
                'owner_type':'OBJECT',
                'constraint_name':constraint .name ,
                'constraint_type':constraint .type ,
                'enabled':not constraint .mute ,
                'influence':constraint .influence ,
                'target':constraint .target .name if hasattr (constraint ,'target')and constraint .target else None ,
                'subtarget':getattr (constraint ,'subtarget',None ),
                'is_valid':constraint .is_valid 
                }


                if constraint .type =='COPY_LOCATION':
                    const_data .update ({
                    'use_x':constraint .use_x ,
                    'use_y':constraint .use_y ,
                    'use_z':constraint .use_z ,
                    'invert_x':constraint .invert_x ,
                    'invert_y':constraint .invert_y ,
                    'invert_z':constraint .invert_z 
                    })
                elif constraint .type =='COPY_ROTATION':
                    const_data .update ({
                    'use_x':constraint .use_x ,
                    'use_y':constraint .use_y ,
                    'use_z':constraint .use_z ,
                    'invert_x':constraint .invert_x ,
                    'invert_y':constraint .invert_y ,
                    'invert_z':constraint .invert_z 
                    })
                elif constraint .type =='COPY_SCALE':
                    const_data .update ({
                    'use_x':constraint .use_x ,
                    'use_y':constraint .use_y ,
                    'use_z':constraint .use_z 
                    })
                elif constraint .type =='TRACK_TO':
                    const_data .update ({
                    'track_axis':constraint .track_axis ,
                    'up_axis':constraint .up_axis 
                    })
                elif constraint .type =='LIMIT_LOCATION':
                    const_data .update ({
                    'use_min_x':constraint .use_min_x ,
                    'use_max_x':constraint .use_max_x ,
                    'min_x':constraint .min_x ,
                    'max_x':constraint .max_x ,
                    'use_min_y':constraint .use_min_y ,
                    'use_max_y':constraint .use_max_y ,
                    'min_y':constraint .min_y ,
                    'max_y':constraint .max_y ,
                    'use_min_z':constraint .use_min_z ,
                    'use_max_z':constraint .use_max_z ,
                    'min_z':constraint .min_z ,
                    'max_z':constraint .max_z 
                    })

                constraints_data .append (const_data )


        for obj in bpy .data .objects :
            if obj .type =='ARMATURE'and obj .pose :
                for bone in obj .pose .bones :
                    for constraint in bone .constraints :
                        const_data ={
                        'owner_name':f"{obj.name}.{bone.name}",
                        'owner_type':'BONE',
                        'constraint_name':constraint .name ,
                        'constraint_type':constraint .type ,
                        'enabled':not constraint .mute ,
                        'influence':constraint .influence ,
                        'target':constraint .target .name if hasattr (constraint ,'target')and constraint .target else None ,
                        'subtarget':getattr (constraint ,'subtarget',None ),
                        'is_valid':constraint .is_valid 
                        }

                        constraints_data .append (const_data )

        return constraints_data 

    def _get_custom_properties_data (self ,context )->List [Dict [str ,Any ]]:
        """Get custom properties from all data blocks."""
        custom_props_data =[]

        def extract_custom_props (data_block ,block_name ,block_type ):
            if hasattr (data_block ,'keys'):
                for key in data_block .keys ():
                    if not key .startswith ('_'):
                        prop_data ={
                        'owner_name':block_name ,
                        'owner_type':block_type ,
                        'property_name':key ,
                        'property_value':to_json_serializable (data_block [key ]),
                        'property_type':type (data_block [key ]).__name__ 
                        }


                        if hasattr (data_block ,'id_properties_ui')and key in data_block .id_properties_ui ():
                            ui_data =data_block .id_properties_ui (key )
                            prop_data .update ({
                            'description':getattr (ui_data ,'description',''),
                            'min':getattr (ui_data ,'min',None ),
                            'max':getattr (ui_data ,'max',None ),
                            'soft_min':getattr (ui_data ,'soft_min',None ),
                            'soft_max':getattr (ui_data ,'soft_max',None ),
                            'step':getattr (ui_data ,'step',None ),
                            'precision':getattr (ui_data ,'precision',None ),
                            'subtype':getattr (ui_data ,'subtype',None )
                            })

                        custom_props_data .append (prop_data )


        for obj in bpy .data .objects :
            extract_custom_props (obj ,obj .name ,'OBJECT')

        for material in bpy .data .materials :
            extract_custom_props (material ,material .name ,'MATERIAL')

        for mesh in bpy .data .meshes :
            extract_custom_props (mesh ,mesh .name ,'MESH')

        for scene in bpy .data .scenes :
            extract_custom_props (scene ,scene .name ,'SCENE')

        for world in bpy .data .worlds :
            extract_custom_props (world ,world .name ,'WORLD')

        for camera in bpy .data .cameras :
            extract_custom_props (camera ,camera .name ,'CAMERA')

        for light in bpy .data .lights :
            extract_custom_props (light ,light .name ,'LIGHT')

        return custom_props_data 

    def get_lightweight_table_counts (self ,context )->Dict [str ,Any ]:
        """
        Get basic table counts without loading all table data.
        Much faster than get_all_table_counts for large scenes.
        
        Args:
            context: Blender context
            
        Returns:
            Dictionary with basic counts for major tables
        """
        try :
            counts ={}
            total_elements =0 


            counts ['objects']=len (context .scene .objects )
            counts ['materials']=len (bpy .data .materials )
            counts ['meshes']=len (bpy .data .meshes )
            counts ['lights']=len (bpy .data .lights )
            counts ['cameras']=len (bpy .data .cameras )
            counts ['collections']=len (bpy .data .collections )
            counts ['scenes']=len (bpy .data .scenes )
            counts ['worlds']=len (bpy .data .worlds )
            counts ['images']=len (bpy .data .images )
            counts ['textures']=len (bpy .data .textures )
            counts ['node_groups']=len (bpy .data .node_groups )
            counts ['tables']=len (self .available_tables )


            node_count =0 
            for material in bpy .data .materials :
                if material .use_nodes and material .node_tree :
                    node_count +=len (material .node_tree .nodes )
            for world in bpy .data .worlds :
                if world .use_nodes and world .node_tree :
                    node_count +=len (world .node_tree .nodes )
            for scene in bpy .data .scenes :
                if scene .use_nodes and scene .node_tree :
                    node_count +=len (scene .node_tree .nodes )
            for node_group in bpy .data .node_groups :
                node_count +=len (node_group .nodes )
            for obj in bpy .data .objects :
                for modifier in obj .modifiers :
                    if modifier .type =='NODES'and modifier .node_group :
                        node_count +=len (modifier .node_group .nodes )

            counts ['nodes']=node_count 
            counts ['shader_nodes']=node_count 
            counts ['geometry_nodes']=0 
            counts ['compositor_nodes']=0 


            modifier_count =sum (len (obj .modifiers )for obj in bpy .data .objects )
            counts ['modifiers']=modifier_count 


            animation_count =0 
            for obj in bpy .data .objects :
                if obj .animation_data and obj .animation_data .action :
                    animation_count +=len (obj .animation_data .action .fcurves )
            counts ['animations']=animation_count 


            total_elements =sum (counts .values ())

            return {
            "status":"success",
            "table_counts":counts ,
            "total_tables":len (self .available_tables ),
            "total_elements":total_elements ,
            "method":"lightweight"
            }

        except Exception as e :
            return {
            "status":"error",
            "error":f"Failed to get lightweight table counts: {str(e)}",
            "table_counts":{},
            "total_tables":0 ,
            "total_elements":0 
            }



scene_query_engine =SceneQueryEngine ()