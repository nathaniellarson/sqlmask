import re
from typing import Dict, Tuple, List, Set, Optional, Pattern, Match


class SQLMasker:
    """
    A class for masking and unmasking SQL statements while preserving structure.
    
    This class provides functionality to obfuscate SQL statements by masking identifiers,
    string literals, and comments, while preserving SQL keywords and structure.
    """
    
    def __init__(self, existing_mapping: Optional[Dict[str, str]] = None) -> None:
        """Initialize the SQLMasker with default settings.
        
        Args:
            existing_mapping: Optional dictionary mapping original values to masked values
        """
        self._counter: int = 1
        self._mapping: Dict[str, str] = {}
        
        # If an existing mapping is provided, use it and adjust the counter
        if existing_mapping:
            self._mapping = existing_mapping.copy()
            # Find the highest counter value in the existing mapping
            max_counter = 0
            for masked_value in self._mapping.values():
                if masked_value.startswith("'m") and masked_value.endswith("'"):
                    try:
                        counter_val = int(masked_value.strip("'m"))
                        max_counter = max(max_counter, counter_val)
                    except ValueError:
                        pass
                elif masked_value.startswith("m"):
                    try:
                        counter_val = int(masked_value[1:])
                        max_counter = max(max_counter, counter_val)
                    except ValueError:
                        pass
                elif masked_value.startswith("--COMMENT") or "COMMENT" in masked_value:
                    try:
                        counter_val = int(masked_value.replace("--COMMENT", "").replace("/*COMMENT", "").replace("*/", ""))
                        max_counter = max(max_counter, counter_val)
                    except ValueError:
                        pass
            # Set the counter to one more than the highest value found
            if max_counter > 0:
                self._counter = max_counter + 1
        
        # SQL keywords to preserve
        self._keywords: Set[str] = {
            # Standard SQL keywords
            'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'INSERT', 'UPDATE', 'DELETE',
            'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'CROSS', 'GROUP', 'ORDER',
            'BY', 'HAVING', 'LIMIT', 'OFFSET', 'AS', 'ON', 'VALUES', 'INTO', 'SET',
            'WITH', 'OVER', 'PARTITION', 'DESC', 'ASC', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END',
            'DISTINCT', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'NOW', 'TRUE', 'FALSE',
            'STRING_AGG', 'RANK', 'INTERVAL', 'NOT', 'NULL', 'IS', 'IN', 'BETWEEN',
            'CREATE', 'TABLE', 'DROP', 'ALTER', 'ADD', 'COLUMN', 'PRIMARY', 'KEY',
            'FOREIGN', 'REFERENCES', 'INDEX', 'UNIQUE', 'DEFAULT', 'CASCADE',
            'UNION', 'INT', 'ALL', 'PIVOT', 'FOR', 'QUALIFY', 'LIKE',
            
            # Google BigQuery data types
            'INT64', 'NUMERIC', 'FLOAT64', 'BOOL', 'STRING', 'BYTES', 'DATE', 
            'DATETIME', 'TIME', 'TIMESTAMP', 'ARRAY', 'STRUCT', 'GEOGRAPHY',
            'JSON', 'BIGNUMERIC', 'INTERVAL',
            
            # Google BigQuery functions
            'CAST', 'SAFE_CAST', 'PARSE_DATE', 'PARSE_TIME', 'PARSE_TIMESTAMP',
            'FORMAT', 'CONCAT', 'SUBSTR', 'SUBSTRING', 'TRIM', 'LTRIM', 'RTRIM',
            'REPLACE', 'REGEXP_EXTRACT', 'REGEXP_CONTAINS', 'REGEXP_REPLACE',
            'LOWER', 'UPPER', 'INITCAP', 'LPAD', 'RPAD', 'LEFT', 'RIGHT',
            'CHAR_LENGTH', 'CHARACTER_LENGTH', 'LENGTH', 'STARTS_WITH', 'ENDS_WITH',
            'CONTAINS', 'OCTET_LENGTH', 'BYTE_LENGTH', 'SPLIT', 'ARRAY_LENGTH',
            'ARRAY_TO_STRING', 'GENERATE_ARRAY', 'GENERATE_DATE_ARRAY',
            'ARRAY_CONCAT', 'ARRAY_REVERSE', 'ARRAY', 'UNNEST',
            'EXTRACT', 'DATE', 'DATETIME', 'TIME', 'TIMESTAMP',
            'CURRENT_DATE', 'CURRENT_DATETIME', 'CURRENT_TIME', 'CURRENT_TIMESTAMP',
            'DATE_ADD', 'DATE_SUB', 'DATE_DIFF', 'DATE_TRUNC', 'DATE_FROM_UNIX_DATE',
            'FORMAT_DATE', 'PARSE_DATE', 'UNIX_DATE',
            'DATETIME_ADD', 'DATETIME_SUB', 'DATETIME_DIFF', 'DATETIME_TRUNC',
            'FORMAT_DATETIME', 'PARSE_DATETIME',
            'TIME_ADD', 'TIME_SUB', 'TIME_DIFF', 'TIME_TRUNC',
            'FORMAT_TIME', 'PARSE_TIME',
            'TIMESTAMP_ADD', 'TIMESTAMP_SUB', 'TIMESTAMP_DIFF', 'TIMESTAMP_TRUNC',
            'FORMAT_TIMESTAMP', 'PARSE_TIMESTAMP', 'UNIX_SECONDS', 'UNIX_MILLIS',
            'TIMESTAMP_SECONDS', 'TIMESTAMP_MILLIS',
            'ABS', 'SIGN', 'IS_INF', 'IS_NAN', 'IEEE_DIVIDE', 'RAND',
            'ROUND', 'TRUNC', 'CEIL', 'CEILING', 'FLOOR',
            'COS', 'COSH', 'ACOS', 'ACOSH', 'SIN', 'SINH', 'ASIN', 'ASINH',
            'TAN', 'TANH', 'ATAN', 'ATANH', 'ATAN2',
            'DIV', 'MOD', 'POW', 'POWER', 'SQRT', 'CBRT',
            'EXP', 'LN', 'LOG', 'LOG10',
            'GREATEST', 'LEAST', 'IF', 'IFNULL', 'NULLIF', 'COALESCE',
            'TO_JSON_STRING', 'FROM_JSON', 'JSON_EXTRACT', 'JSON_EXTRACT_SCALAR',
            'JSON_QUERY', 'JSON_VALUE', 'JSON_EXTRACT_ARRAY',
            'ST_GEOGPOINT', 'ST_MAKELINE', 'ST_MAKEPOLYGON', 'ST_MAKEPOLYGONORIENTED',
            'ST_DISTANCE', 'ST_DWITHIN', 'ST_EQUALS', 'ST_INTERSECTS', 'ST_CONTAINS',
            'ST_WITHIN', 'ST_COVERS', 'ST_COVEREDBY', 'ST_DISJOINT', 'ST_TOUCHES',
            'ST_INTERSECTSBOX', 'ST_UNION_AGG', 'ST_CENTROID', 'ST_AREA', 'ST_LENGTH',
            'ST_PERIMETER', 'ST_BOUNDARY', 'ST_BUFFER', 'ST_CLOSESTPOINT',
            'ST_SIMPLIFY', 'ST_SNAPTOGRID', 'ST_DIFFERENCE', 'ST_INTERSECTION',
            'ST_UNION', 'ST_DIMENSION', 'ST_GEOMETRYTYPE', 'ST_NUMPOINTS',
            'ST_ISEMPTY', 'ST_ISCOLLECTION', 'ST_ASTEXT', 'ST_ASGEOJSON',
            'SAFE', 'ERROR', 'ANY_VALUE', 'COUNTIF', 'LOGICAL_AND', 'LOGICAL_OR',
            'APPROX_COUNT_DISTINCT', 'APPROX_QUANTILES', 'APPROX_TOP_COUNT',
            'APPROX_TOP_SUM', 'HLL_COUNT.INIT', 'HLL_COUNT.MERGE',
            'HLL_COUNT.MERGE_PARTIAL', 'HLL_COUNT.EXTRACT',
            'BIT_COUNT', 'BIT_AND', 'BIT_OR', 'BIT_XOR',
            'CORR', 'COVAR_POP', 'COVAR_SAMP', 'STDDEV_POP', 'STDDEV_SAMP',
            'STDDEV', 'VAR_POP', 'VAR_SAMP', 'VARIANCE',
            'PERCENTILE_CONT', 'PERCENTILE_DISC',
            'ARRAY_AGG', 'STRING_AGG',
            'LAG', 'LEAD', 'FIRST_VALUE', 'LAST_VALUE', 'NTH_VALUE',
            'RANK', 'DENSE_RANK', 'PERCENT_RANK', 'CUME_DIST', 'NTILE', 'ROW_NUMBER',
            'NET.IP_FROM_STRING', 'NET.SAFE_IP_FROM_STRING', 'NET.IP_TO_STRING',
            'NET.IP_NET_MASK', 'NET.IP_TRUNC', 'NET.IPV4_FROM_INT64', 'NET.IPV4_TO_INT64',
            'NET.HOST', 'NET.PUBLIC_SUFFIX', 'NET.REG_DOMAIN',
            'ML.PREDICT', 'ML.EVALUATE', 'ML.ROC_CURVE', 'ML.CONFUSION_MATRIX',
            'ML.FEATURE_INFO', 'ML.WEIGHTS', 'ML.TRANSFORM', 'ML.GENERATE_TEXT',
            'SESSION_USER', 'CURRENT_USER', 'GENERATE_UUID', 'MD5', 'SHA1', 'SHA256',
            'SHA512', 'FARM_FINGERPRINT', 'TO_BASE32', 'TO_BASE64', 'FROM_BASE32',
            'FROM_BASE64', 'TO_HEX', 'FROM_HEX'
        }

    def encode(self, sql: str, reset_mapping: bool = False) -> Tuple[str, Dict[str, str]]:
        """
        Obfuscate a SQL statement while preserving its structure.
        
        Args:
            sql: The SQL statement to obfuscate
            reset_mapping: If True, reset the mapping before encoding
        
        Returns:
            Tuple containing:
                - The obfuscated SQL statement
                - Mapping dictionary of original to obfuscated names
        """
        if reset_mapping:
            self.reset()
        
        # Tokenize the SQL into components
        tokens = self._tokenize(sql)
        
        # Process each token
        masked_tokens: List[str] = []
        for token_type, token_value in tokens:
            if token_type == 'COMMENT':
                # Mask comments
                if token_value not in self._mapping:
                    masked = f"--COMMENT{self._counter}" if token_value.startswith('--') else f"/*COMMENT{self._counter}*/"
                    self._mapping[token_value] = masked
                    self._counter += 1
                masked_tokens.append(self._mapping[token_value])
            elif token_type == 'STRING':
                # Mask string literals
                if token_value not in self._mapping:
                    masked = f"'m{self._counter}'"
                    self._mapping[token_value] = masked
                    self._counter += 1
                masked_tokens.append(self._mapping[token_value])
            elif token_type == 'IDENTIFIER':
                # Mask identifiers
                if token_value.upper() in self._keywords:
                    # Preserve the original case of SQL keywords
                    masked_tokens.append(token_value)
                else:
                    # Handle qualified names (e.g., table.column)
                    parts = token_value.split('.')
                    if len(parts) > 1:
                        masked_parts: List[str] = []
                        for part in parts:
                            if part.upper() in self._keywords:
                                # Preserve the original case of SQL keywords
                                masked_parts.append(part)
                            else:
                                if part not in self._mapping:
                                    masked = f"m{self._counter}"
                                    self._mapping[part] = masked
                                    self._counter += 1
                                masked_parts.append(self._mapping[part])
                        masked_tokens.append('.'.join(masked_parts))
                    else:
                        if token_value not in self._mapping:
                            masked = f"m{self._counter}"
                            self._mapping[token_value] = masked
                            self._counter += 1
                        masked_tokens.append(self._mapping[token_value])
            else:
                # Keep other tokens as is
                masked_tokens.append(token_value)
        
        # Join the tokens back into a SQL string
        masked_sql = ''.join(masked_tokens)
        
        return masked_sql, self._mapping

    def reset(self) -> None:
        """
        Reset the masker state by clearing the mapping and resetting the counter.
        """
        self._counter = 1
        self._mapping = {}

    def decode(self, masked_sql: str, mapping: Dict[str, str]) -> str:
        """
        Restore original names in an obfuscated SQL statement.
        
        Args:
            masked_sql: The obfuscated SQL statement
            mapping: The mapping dictionary from encode()
            
        Returns:
            The original SQL statement
        """
        # Create reverse mapping
        rev_mapping: Dict[str, str] = {v: k for k, v in mapping.items()}
        
        # Replace all masked elements with their original values
        # Process in order of longest mask first to avoid partial replacements
        result = masked_sql
        
        # First, replace comment masks
        comment_pattern: Pattern = re.compile(r"(/\*COMMENT\d+\*/|--COMMENT\d+)")
        for match in comment_pattern.finditer(result):
            mask = match.group(0)
            if mask in rev_mapping:
                result = result.replace(mask, rev_mapping[mask])
        
        # Next, replace string literal masks
        string_pattern: Pattern = re.compile(r"'m\d+'")
        for match in string_pattern.finditer(result):
            mask = match.group(0)
            if mask in rev_mapping:
                result = result.replace(mask, rev_mapping[mask])
        
        # Finally, replace identifier masks
        # Sort masks by length (descending) to avoid partial replacements
        identifier_masks: List[str] = sorted(
            [m for m in rev_mapping.keys() if m.startswith('m') and not m.startswith("'m")], 
            key=len, 
            reverse=True
        )
        for mask in identifier_masks:
            # Replace only whole identifiers, not parts of other identifiers
            pattern = re.compile(r'\b' + re.escape(mask) + r'\b')
            result = pattern.sub(rev_mapping[mask], result)
        
        return result

    def _tokenize(self, sql: str) -> List[Tuple[str, str]]:
        """
        Tokenize SQL into components for masking.
        
        Args:
            sql: The SQL statement to tokenize
            
        Returns:
            List of (token_type, token_value) tuples
        """
        tokens: List[Tuple[str, str]] = []
        remaining = sql
        
        # Define regex patterns for different token types
        patterns: List[Tuple[str, str]] = [
            ('COMMENT', r'/\*[\s\S]*?\*/'),  # Multiline comments
            ('COMMENT', r'--[^\n]*'),        # Inline comments
            ('STRING', r"'[^']*'"),          # String literals
            ('IDENTIFIER', r'\b[a-zA-Z_][a-zA-Z0-9_.]*\b'),  # Identifiers (including qualified names)
            ('WHITESPACE', r'\s+'),          # Whitespace
            ('PUNCTUATION', r'[.,;:()=<>+\-*/!?@#$%^&[\]{}|\\]')  # Punctuation and operators
        ]
        
        while remaining:
            matched = False
            for token_type, pattern in patterns:
                match: Optional[Match] = re.match(pattern, remaining)
                if match:
                    token_value = match.group(0)
                    tokens.append((token_type, token_value))
                    remaining = remaining[len(token_value):]
                    matched = True
                    break
            
            if not matched:
                # If no pattern matches, take the next character as is
                tokens.append(('OTHER', remaining[0]))
                remaining = remaining[1:]
        
        return tokens
