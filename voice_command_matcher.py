"""
Configurable Voice Command Matcher

Replaces hard-coded fuzzy matching with a flexible, configurable system
that loads command variants from JSON configuration files.
"""

import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class VoiceCommandMatcher:
    """Configurable matcher for voice commands with multiple matching strategies."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the voice command matcher.
        
        Args:
            config_path: Path to voice command variants JSON file
        """
        self.logger = logging.getLogger(__name__)
        self.command_variants = {}
        self.matching_settings = {}
        
        # Default config path
        if config_path is None:
            config_path = Path(__file__).parent / "voice_command_variants.json"
        
        self.load_variants(config_path)
    
    def load_variants(self, config_path: str) -> bool:
        """
        Load command variants from JSON configuration file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            self.command_variants = config.get('command_variants', {})
            self.matching_settings = config.get('matching_settings', {})
            
            # Set default matching settings
            self.matching_settings.setdefault('enable_exact_matching', True)
            self.matching_settings.setdefault('enable_fuzzy_matching', True)
            self.matching_settings.setdefault('enable_phonetic_matching', True)
            self.matching_settings.setdefault('enable_partial_matching', True)
            self.matching_settings.setdefault('max_character_differences', 1)
            self.matching_settings.setdefault('min_word_length_for_partial', 3)
            self.matching_settings.setdefault('case_sensitive', False)
            
            self.logger.info(f"Loaded voice command variants for {len(self.command_variants)} commands")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load voice command variants from {config_path}: {e}")
            # Load minimal defaults
            self._load_default_variants()
            return False
    
    def _load_default_variants(self):
        """Load minimal default variants if config file fails to load."""
        self.command_variants = {
            'back': {
                'exact_matches': ['back', 'previous', 'backward', 'left'],
                'fuzzy_variants': ['bag', 'pack', 'beck'],
                'phonetic_variants': [],
                'partial_match_variants': []
            },
            'next': {
                'exact_matches': ['next', 'forward', 'advance', 'right'],
                'fuzzy_variants': ['neck', 'text'],
                'phonetic_variants': [],
                'partial_match_variants': []
            },
            'pause': {
                'exact_matches': ['stop', 'pause', 'halt'],
                'fuzzy_variants': ['top', 'shop'],
                'phonetic_variants': [],
                'partial_match_variants': []
            },
            'resume': {
                'exact_matches': ['go', 'play', 'resume', 'start'],
                'fuzzy_variants': ['oh', 'so'],
                'phonetic_variants': [],
                'partial_match_variants': []
            }
        }
        self.matching_settings = {
            'enable_exact_matching': True,
            'enable_fuzzy_matching': True,
            'enable_phonetic_matching': False,
            'enable_partial_matching': False,
            'max_character_differences': 1,
            'min_word_length_for_partial': 3,
            'case_sensitive': False
        }
    
    def find_matching_command(self, text: str) -> Optional[Tuple[str, str, str]]:
        """
        Find the best matching command for the given text.
        
        Args:
            text: The recognized speech text
            
        Returns:
            Tuple of (command, matched_variant, match_type) or None if no match
        """
        if not text:
            return None
        
        # Normalize text
        text_lower = text.lower().strip() if not self.matching_settings['case_sensitive'] else text.strip()
        words = text_lower.split()
        
        # Try different matching strategies in order of preference
        for command, variants in self.command_variants.items():
            
            # 1. Exact word matching (highest priority)
            if self.matching_settings['enable_exact_matching']:
                for word in words:
                    for exact_match in variants.get('exact_matches', []):
                        if word == exact_match.lower():
                            return command, exact_match, 'exact'
            
            # 2. Word boundary matching
            if self.matching_settings['enable_exact_matching']:
                for exact_match in variants.get('exact_matches', []):
                    if re.search(r'\b' + re.escape(exact_match.lower()) + r'\b', text_lower):
                        return command, exact_match, 'word_boundary'
            
            # 3. Fuzzy variant matching
            if self.matching_settings['enable_fuzzy_matching']:
                for fuzzy_variant in variants.get('fuzzy_variants', []):
                    if fuzzy_variant.lower() in text_lower:
                        return command, fuzzy_variant, 'fuzzy'
            
            # 4. Phonetic variant matching
            if self.matching_settings['enable_phonetic_matching']:
                for phonetic_variant in variants.get('phonetic_variants', []):
                    if phonetic_variant.lower() in text_lower:
                        return command, phonetic_variant, 'phonetic'
            
            # 5. Partial matching for short words
            if self.matching_settings['enable_partial_matching']:
                for partial_variant in variants.get('partial_match_variants', []):
                    if partial_variant.lower() in text_lower:
                        return command, partial_variant, 'partial'
                
                # Check if any exact match is at start or end of words
                for exact_match in variants.get('exact_matches', []):
                    if len(exact_match) <= self.matching_settings['min_word_length_for_partial']:
                        for word in words:
                            if word.startswith(exact_match.lower()) or word.endswith(exact_match.lower()):
                                return command, exact_match, 'partial_word'
            
            # 6. Levenshtein distance matching (most permissive)
            if self.matching_settings['enable_fuzzy_matching']:
                max_diff = self.matching_settings['max_character_differences']
                for exact_match in variants.get('exact_matches', []):
                    if len(exact_match) >= 3:  # Only for words of reasonable length
                        for word in words:
                            if (len(word) >= 2 and 
                                abs(len(word) - len(exact_match)) <= max_diff and
                                self._levenshtein_distance(word, exact_match.lower()) <= max_diff):
                                return command, exact_match, 'levenshtein'
        
        return None
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """
        Calculate Levenshtein distance between two strings.
        
        Args:
            s1: First string
            s2: Second string
            
        Returns:
            int: Edit distance between the strings
        """
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def get_available_commands(self) -> List[str]:
        """Get list of available commands."""
        return list(self.command_variants.keys())
    
    def add_custom_variant(self, command: str, variant: str, variant_type: str = 'fuzzy_variants'):
        """
        Add a custom variant for a command at runtime.
        
        Args:
            command: The command to add variant to
            variant: The variant text
            variant_type: Type of variant ('exact_matches', 'fuzzy_variants', etc.)
        """
        if command not in self.command_variants:
            self.command_variants[command] = {
                'exact_matches': [],
                'fuzzy_variants': [],
                'phonetic_variants': [],
                'partial_match_variants': []
            }
        
        if variant_type not in self.command_variants[command]:
            self.command_variants[command][variant_type] = []
        
        if variant not in self.command_variants[command][variant_type]:
            self.command_variants[command][variant_type].append(variant)
            self.logger.info(f"Added custom variant '{variant}' for command '{command}' as {variant_type}")
    
    def get_command_info(self, command: str) -> Dict:
        """Get information about a specific command and its variants."""
        return self.command_variants.get(command, {})
