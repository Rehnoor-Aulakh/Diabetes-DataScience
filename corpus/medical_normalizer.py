"""
Certus Clinical Language Engine: Medical Normalizer Pipeline
"""

import json
import re
import os

class UnicodeNormalizer:
    def process(self, text: str) -> str:
        # Standardize quotes, dashes, and whitespace
        text = re.sub(r'[‘’“”]', '"', text)
        text = re.sub(r'[—–]', '-', text)
        text = text.replace('\\xa0', ' ')
        return text.lower()

class BoilerplateCleaner:
    def process(self, text: str) -> str:
        # Remove navigation artifacts and non-medical boilerplate
        boilerplates = [
            r"skip to main content",
            r"print this page",
            r"an official website of the united states government",
            r"get the latest updates and faqs",
            r"search site",
            r"menu"
        ]
        for pattern in boilerplates:
            text = re.sub(pattern, " ", text)
        return text

class EntityCanonicalizer:
    def __init__(self):
        self.ontology = {}
        self.alias_map = {}
        self._load_ontology()
        
    def _load_ontology(self):
        onto_path = os.path.join(os.path.dirname(__file__), 'medical_ontology.json')
        if os.path.exists(onto_path):
            with open(onto_path, 'r', encoding='utf-8') as f:
                self.ontology = json.load(f)
                
            # Create a reverse mapping from lowercase alias to CANONICAL token
            for canonical, data in self.ontology.items():
                for alias in data.get("aliases", []):
                    # Sort aliases by length descending so longer phrases match first
                    self.alias_map[alias.lower()] = canonical
                    
            # Sort keys by length to replace "Hemoglobin A1c" before "A1c"
            self.sorted_aliases = sorted(self.alias_map.keys(), key=len, reverse=True)
        else:
            self.sorted_aliases = []

    def process(self, text: str) -> str:
        for alias in self.sorted_aliases:
            canonical = self.alias_map[alias]
            # Replace as a whole word, allowing for spaces in the alias
            escaped = re.escape(alias)
            # Boundary checks handling punctuation around the alias
            pattern = r'(?<!\w)' + escaped + r'(?!\w)'
            text = re.sub(pattern, canonical, text)
        return text

class UnitNormalizer:
    def process(self, text: str) -> str:
        units = {
            r"mg\s*/\s*dl": "MG_PER_DL",
            r"u\s*/\s*l": "U_PER_L",
            r"ng\s*/\s*ml": "NG_PER_ML",
            r"mmol\s*/\s*l": "MMOL_PER_L",
            r"g\s*/\s*dl": "G_PER_DL",
            r"pg\s*/\s*ml": "PG_PER_ML",
            r"μiu\s*/\s*ml": "UIU_PER_ML",
            r"%": " PERCENT "
        }
        for pattern, replacement in units.items():
            text = re.sub(pattern, f" {replacement} ", text)
        return text

class ReferenceRangeRecognizer:
    def process(self, text: str) -> str:
        # Range: 5.7 - 6.4 -> 5.7_TO_6.4
        text = re.sub(r'(\d+\.?\d*)\s*-\s*(\d+\.?\d*)', r'\1_TO_\2', text)
        return text

class MedicalTokenizer:
    def __init__(self):
        stop_path = os.path.join(os.path.dirname(__file__), 'medical_stopwords.json')
        if os.path.exists(stop_path):
            with open(stop_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.remove_words = set(config.get("remove", []))
                self.keep_words = set(config.get("always_keep", []))
        else:
            self.remove_words = set()
            self.keep_words = set()
            
    def process(self, text: str) -> str:
        # Preserve specific punctuation: operators, underscores (from canonicals), numbers
        # First, add space around operators for safe tokenization
        text = re.sub(r'(>=|<=|>|<|=)', r' \1 ', text)
        
        # Tokenize by finding words, numbers, and operators
        # \w+ catches CANONICAL_ENTITIES and standard words
        # \d+\.\d+ catches decimals
        # [><=] catches operators
        tokens = re.findall(r'[A-Z_a-z0-9\.]+|[><=]+', text)
        
        final_tokens = []
        for t in tokens:
            t_lower = t.lower()
            if t_lower in self.keep_words:
                final_tokens.append(t_lower)
            elif t_lower in self.remove_words:
                continue
            else:
                # If it's all uppercase (Canonical entity like HBA1C or MG_PER_DL), keep it upper
                if t.isupper():
                    final_tokens.append(t)
                else:
                    final_tokens.append(t_lower)
                    
        return " ".join(final_tokens)

class MedicalPipeline:
    def __init__(self):
        self.stages = [
            UnicodeNormalizer(),
            BoilerplateCleaner(),
            EntityCanonicalizer(),
            UnitNormalizer(),
            ReferenceRangeRecognizer(),
            MedicalTokenizer()
        ]
        
    def process_document(self, text: str) -> str:
        if not text:
            return ""
        for stage in self.stages:
            text = stage.process(text)
        return text
        
    def process_corpus(self, docs: list[str]) -> list[str]:
        return [self.process_document(doc) for doc in docs]
