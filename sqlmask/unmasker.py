"""
SQLUnmasker class for unmasking identifiers in SQL queries or other text.
"""
from typing import Dict, Optional, Union, List
import json


class SQLUnmasker:
    """
    A class for unmasking identifiers in SQL queries or other text.
    
    This class provides functionality to unmask identifiers that were previously
    masked using the SQLMasker class. It supports unmasking both standalone identifiers
    and identifiers embedded within text.
    """
    
    def __init__(self, mapping: Optional[Union[Dict[str, str], str]] = None):
        """
        Initialize the SQLUnmasker with an optional mapping.
        
        Args:
            mapping: Either a dictionary mapping original values to masked values,
                    or a path to a JSON file containing such a mapping.
                    If None, an empty mapping is created.
        """
        self.mapping: Dict[str, str] = {}
        self.rev_mapping: Dict[str, str] = {}
        self.direct_replacements: Dict[str, str] = {}
        
        if mapping:
            if isinstance(mapping, str):
                # Load mapping from a JSON file
                with open(mapping, 'r', encoding='utf-8') as f:
                    self.mapping = json.load(f)
            else:
                # Use the provided mapping dictionary
                self.mapping = mapping
                
            # Create a reverse mapping for faster lookups
            self.rev_mapping = {v: k for k, v in self.mapping.items()}
            
            # Precompute direct replacements for efficiency
            self._precompute_replacements()
    
    def _precompute_replacements(self) -> None:
        """
        Precompute direct replacements for efficient string replacement.
        This avoids the need for regex in simple cases.
        """
        # Sort masked identifiers by length (longest first) to avoid partial replacements
        masked_ids = sorted(self.rev_mapping.keys(), key=len, reverse=True)
        
        # Create a dictionary mapping pattern to replacement
        for masked_id in masked_ids:
            original_id = self.rev_mapping[masked_id]
            self.direct_replacements[masked_id] = original_id
            # Also add quoted versions
            self.direct_replacements[f"'{masked_id}'"] = f"'{original_id}'"
            self.direct_replacements[f'"{masked_id}"'] = f'"{original_id}"'
    
    def load_mapping(self, mapping_file: str) -> None:
        """
        Load a mapping from a JSON file.
        
        Args:
            mapping_file: Path to the JSON file containing the mapping.
        """
        with open(mapping_file, 'r', encoding='utf-8') as f:
            self.mapping = json.load(f)
        
        # Create a reverse mapping for faster lookups
        self.rev_mapping = {v: k for k, v in self.mapping.items()}
        
        # Precompute direct replacements
        self._precompute_replacements()
    
    def unmask(self, text: str) -> str:
        """
        Unmask identifiers in the given text.
        
        This method handles various cases:
        1. Standalone masked identifiers (e.g., m123)
        2. Quoted masked identifiers (e.g., 'm123', "m123")
        3. Dot-separated masked identifiers (e.g., m123.m456)
        
        Args:
            text: The text containing masked identifiers to unmask.
            
        Returns:
            The text with masked identifiers replaced by their original values.
        """
        if not text or not isinstance(text, str):
            return text
            
        # If the entire string is a masked value, replace it directly
        if text in self.rev_mapping:
            return self.rev_mapping[text]
        
        # Use direct string replacement for efficiency
        result = text
        
        # Try direct replacements for exact matches
        for pattern, replacement in self.direct_replacements.items():
            if pattern in result:
                # Only replace if it's a whole word (not part of another word)
                # This is a simple check that works for most cases without regex
                parts = result.split(pattern)
                if len(parts) > 1:
                    new_result = parts[0]
                    for i in range(1, len(parts)):
                        # Check if this is a whole word boundary
                        if (i == 1 and (not parts[0] or parts[0][-1].isspace() or not parts[0][-1].isalnum())) or \
                           (i > 1 and (not new_result or new_result[-1].isspace() or not new_result[-1].isalnum())):
                            new_result += replacement + parts[i]
                        else:
                            new_result += pattern + parts[i]
                    result = new_result
        
        return result
    
    def unmask_list(self, items: List[str]) -> List[str]:
        """
        Unmask identifiers in a list of strings.
        
        Args:
            items: A list of strings containing masked identifiers.
            
        Returns:
            A list of strings with masked identifiers replaced by their original values.
        """
        return [self.unmask(item) for item in items]
    
    def unmask_dict(self, data: Dict[str, str]) -> Dict[str, str]:
        """
        Unmask identifiers in a dictionary of strings.
        
        Args:
            data: A dictionary with string values containing masked identifiers.
            
        Returns:
            A dictionary with masked identifiers in values replaced by their original values.
        """
        return {k: self.unmask(v) for k, v in data.items()}
