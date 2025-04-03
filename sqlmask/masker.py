import re
from typing import Dict, Tuple, List, Set


class SQLMasker:
    def __init__(self):
        self._counter = 1
        self._mapping = {}
        
        # SQL keywords to preserve
        self._keywords = {
            'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'INSERT', 'UPDATE', 'DELETE',
            'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'CROSS', 'GROUP', 'ORDER',
            'BY', 'HAVING', 'LIMIT', 'OFFSET', 'AS', 'ON', 'VALUES', 'INTO', 'SET',
            'WITH', 'OVER', 'PARTITION', 'DESC', 'ASC', 'CASE', 'WHEN', 'THEN', 'END',
            'DISTINCT', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'NOW', 'TRUE', 'FALSE',
            'STRING_AGG', 'RANK', 'INTERVAL', 'NOT', 'NULL', 'IS', 'IN', 'BETWEEN',
            'CREATE', 'TABLE', 'DROP', 'ALTER', 'ADD', 'COLUMN', 'PRIMARY', 'KEY',
            'FOREIGN', 'REFERENCES', 'INDEX', 'UNIQUE', 'DEFAULT', 'CASCADE',
            'UNION'
        }

    def encode(self, sql: str) -> Tuple[str, Dict]:
        """
        Obfuscate a SQL statement while preserving its structure.
        
        Args:
            sql: The SQL statement to obfuscate
            
        Returns:
            Tuple containing:
                - The obfuscated SQL statement
                - Mapping dictionary of original to obfuscated names
        """
        self._counter = 1
        self._mapping = {}
        
        # Tokenize the SQL into components
        tokens = self._tokenize(sql)
        
        # Process each token
        masked_tokens = []
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
                    masked_tokens.append(token_value)
                else:
                    # Handle qualified names (e.g., table.column)
                    parts = token_value.split('.')
                    if len(parts) > 1:
                        masked_parts = []
                        for part in parts:
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

    def decode(self, masked_sql: str, mapping: Dict) -> str:
        """
        Restore original names in an obfuscated SQL statement.
        
        Args:
            masked_sql: The obfuscated SQL statement
            mapping: The mapping dictionary from encode()
            
        Returns:
            The original SQL statement
        """
        # Create reverse mapping
        rev_mapping = {v: k for k, v in mapping.items()}
        
        # Replace all masked elements with their original values
        # Process in order of longest mask first to avoid partial replacements
        result = masked_sql
        
        # First, replace comment masks
        comment_pattern = re.compile(r"(/\*COMMENT\d+\*/|--COMMENT\d+)")
        for match in comment_pattern.finditer(result):
            mask = match.group(0)
            if mask in rev_mapping:
                result = result.replace(mask, rev_mapping[mask])
        
        # Next, replace string literal masks
        string_pattern = re.compile(r"'m\d+'")
        for match in string_pattern.finditer(result):
            mask = match.group(0)
            if mask in rev_mapping:
                result = result.replace(mask, rev_mapping[mask])
        
        # Finally, replace identifier masks
        # Sort masks by length (descending) to avoid partial replacements
        identifier_masks = sorted([m for m in rev_mapping.keys() if m.startswith('m') and not m.startswith("'m")], 
                                key=len, reverse=True)
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
        tokens = []
        remaining = sql
        
        # Define regex patterns for different token types
        patterns = [
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
                match = re.match(pattern, remaining)
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
