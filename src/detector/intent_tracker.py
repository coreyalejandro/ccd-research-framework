"""
Automated Intent Tracking System for CCD Detection
Replaces human intent logs with automated analysis
"""

import re
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum


class IntentSignal(Enum):
    """Types of intent signals detected"""
    KEYWORD_MATCH = "keyword_match"
    COMMIT_MESSAGE = "commit_message"
    PROMPT_PATTERN = "prompt_pattern"
    DOCUMENTATION = "documentation"
    TEST_EXPECTATION = "test_expectation"


@dataclass
class IntentEvidence:
    """Evidence of user intent for component functionality"""
    signal_type: IntentSignal
    confidence: float  # 0.0 to 1.0
    source: str
    matched_text: str
    component_name: str


class AutomatedIntentTracker:
    """
    Automated intent tracking system (D2c requirement)
    Replaces human intent logs with keyword spotting, commit analysis, and pattern matching
    """
    
    def __init__(self):
        # Keyword patterns indicating expectation of functionality
        self.expectation_keywords = {
            'implementation': [
                r'\bimplement(?:ed|ing|ation)?\b',
                r'\bbuild(?:ing)?\b',
                r'\bcreate(?:d|ing)?\b',
                r'\bdevelop(?:ed|ing)?\b',
                r'\bcode(?:d)?\b',
                r'\bwrite\b',
                r'\badd(?:ed|ing)?\b'
            ],
            'functionality': [
                r'\bwork(?:s|ing)?\b',
                r'\bfunction(?:al|ing)?\b',
                r'\boperational\b',
                r'\bready\b',
                r'\bcomplete(?:d)?\b',
                r'\bfinished\b',
                r'\bdone\b'
            ],
            'verification': [
                r'\btest(?:ed|ing)?\b',
                r'\bverif(?:y|ied|ication)\b',
                r'\bvalidat(?:e|ed|ion)\b',
                r'\bcheck(?:ed|ing)?\b',
                r'\bconfirm(?:ed)?\b'
            ],
            'integration': [
                r'\bintegrat(?:e|ed|ion)\b',
                r'\bconnect(?:ed|ing)?\b',
                r'\blink(?:ed|ing)?\b',
                r'\bhook(?:ed)?\s+up\b',
                r'\bwire(?:d)?\s+up\b'
            ]
        }
        
        # Commit message patterns
        self.commit_patterns = [
            r'^(?:feat|feature):\s*(.+)',
            r'^(?:add|added):\s*(.+)',
            r'^(?:implement|implemented):\s*(.+)',
            r'^(?:create|created):\s*(.+)',
            r'^\[(?:feat|feature)\]\s*(.+)'
        ]
        
        # Prompt patterns indicating intent
        self.prompt_patterns = {
            'direct_request': [
                r'(?:can you|could you|please)\s+(?:implement|build|create|add)\s+(.+)',
                r'(?:i need|i want|we need)\s+(?:to implement|to build|to create|to add)\s+(.+)',
                r'(?:let\'s|lets)\s+(?:implement|build|create|add)\s+(.+)'
            ],
            'status_check': [
                r'(?:is|are)\s+(.+?)\s+(?:working|functional|ready|complete|done)',
                r'(?:how is|what\'s the status of|status of)\s+(.+)',
                r'(?:can you show|show me)\s+(?:the progress on|progress for)\s+(.+)'
            ],
            'verification': [
                r'(?:verify|check|confirm)\s+(?:that\s+)?(.+?)\s+(?:is|are)\s+(?:working|implemented)',
                r'(?:does|do)\s+(.+?)\s+(?:work|function)',
                r'(?:where is|where\'s)\s+(?:the code for|the implementation of)\s+(.+)'
            ]
        }
    
    def extract_component_name(self, text: str) -> Optional[str]:
        """Extract component name from text"""
        # Common component patterns
        patterns = [
            r'(?:the\s+)?([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*(?:\s+(?:server|handler|middleware|system|layer|framework|processor|manager))?)',
            r'`([^`]+)`',
            r'"([^"]+)"',
            r'\'([^\']+)\''
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        return None
    
    def analyze_prompt(self, prompt: str, component_name: Optional[str] = None) -> List[IntentEvidence]:
        """Analyze user prompt for intent signals"""
        evidence = []
        prompt_lower = prompt.lower()
        
        # Extract component if not provided
        if not component_name:
            component_name = self.extract_component_name(prompt)
        
        if not component_name:
            return evidence
        
        # Check keyword patterns
        for category, patterns in self.expectation_keywords.items():
            for pattern in patterns:
                matches = re.finditer(pattern, prompt_lower, re.IGNORECASE)
                for match in matches:
                    confidence = 0.7 if category in ['implementation', 'functionality'] else 0.5
                    evidence.append(IntentEvidence(
                        signal_type=IntentSignal.KEYWORD_MATCH,
                        confidence=confidence,
                        source=f"prompt_keyword_{category}",
                        matched_text=match.group(0),
                        component_name=component_name
                    ))
        
        # Check prompt patterns
        for pattern_type, patterns in self.prompt_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, prompt_lower, re.IGNORECASE)
                if match:
                    confidence = 0.9 if pattern_type == 'direct_request' else 0.7
                    evidence.append(IntentEvidence(
                        signal_type=IntentSignal.PROMPT_PATTERN,
                        confidence=confidence,
                        source=f"prompt_pattern_{pattern_type}",
                        matched_text=match.group(0),
                        component_name=component_name
                    ))
        
        return evidence
    
    def analyze_commit_message(self, commit_message: str, component_name: Optional[str] = None) -> List[IntentEvidence]:
        """Analyze commit message for intent signals"""
        evidence = []
        
        # Extract component if not provided
        if not component_name:
            component_name = self.extract_component_name(commit_message)
        
        if not component_name:
            return evidence
        
        # Check commit patterns
        for pattern in self.commit_patterns:
            match = re.search(pattern, commit_message, re.IGNORECASE)
            if match:
                evidence.append(IntentEvidence(
                    signal_type=IntentSignal.COMMIT_MESSAGE,
                    confidence=0.85,
                    source="commit_message",
                    matched_text=match.group(0),
                    component_name=component_name
                ))
        
        return evidence
    
    def analyze_documentation(self, doc_content: str, component_name: str) -> List[IntentEvidence]:
        """Analyze documentation for intent signals"""
        evidence = []
        doc_lower = doc_content.lower()
        component_lower = component_name.lower()
        
        # Check if component is mentioned in documentation
        if component_lower in doc_lower:
            # Look for implementation claims in docs
            implementation_indicators = [
                r'(?:implements|provides|includes)\s+' + re.escape(component_lower),
                r'' + re.escape(component_lower) + r'\s+(?:is|provides|implements)',
                r'(?:the|our)\s+' + re.escape(component_lower) + r'\s+(?:handles|manages|processes)'
            ]
            
            for pattern in implementation_indicators:
                matches = re.finditer(pattern, doc_lower, re.IGNORECASE)
                for match in matches:
                    evidence.append(IntentEvidence(
                        signal_type=IntentSignal.DOCUMENTATION,
                        confidence=0.6,
                        source="documentation",
                        matched_text=match.group(0),
                        component_name=component_name
                    ))
        
        return evidence
    
    def analyze_test_expectations(self, test_content: str, component_name: str) -> List[IntentEvidence]:
        """Analyze test files for expectations of functionality"""
        evidence = []
        test_lower = test_content.lower()
        component_lower = component_name.lower()
        
        # Test patterns indicating expected functionality
        test_patterns = [
            r'(?:test|it|describe)\s*\(["\'].*' + re.escape(component_lower) + r'.*["\']',
            r'expect\s*\(.*' + re.escape(component_lower) + r'.*\)',
            r'assert.*' + re.escape(component_lower),
            r'should.*' + re.escape(component_lower)
        ]
        
        for pattern in test_patterns:
            matches = re.finditer(pattern, test_lower, re.IGNORECASE)
            for match in matches:
                evidence.append(IntentEvidence(
                    signal_type=IntentSignal.TEST_EXPECTATION,
                    confidence=0.8,
                    source="test_file",
                    matched_text=match.group(0),
                    component_name=component_name
                ))
        
        return evidence
    
    def aggregate_intent_confidence(self, evidence_list: List[IntentEvidence]) -> float:
        """
        Aggregate multiple intent signals into overall confidence score
        Uses weighted average with signal type weights
        """
        if not evidence_list:
            return 0.0
        
        # Weight different signal types
        signal_weights = {
            IntentSignal.PROMPT_PATTERN: 1.0,
            IntentSignal.COMMIT_MESSAGE: 0.9,
            IntentSignal.TEST_EXPECTATION: 0.85,
            IntentSignal.KEYWORD_MATCH: 0.7,
            IntentSignal.DOCUMENTATION: 0.6
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for evidence in evidence_list:
            weight = signal_weights.get(evidence.signal_type, 0.5)
            weighted_sum += evidence.confidence * weight
            total_weight += weight
        
        return min(weighted_sum / total_weight if total_weight > 0 else 0.0, 1.0)
    
    def confirm_user_intent(self,
                           prompts: List[str],
                           commit_messages: Optional[List[str]] = None,
                           documentation: Optional[str] = None,
                           test_files: Optional[List[str]] = None,
                           component_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Confirm user intent for component functionality (D2c requirement)
        Returns intent confirmation with confidence and evidence
        """
        all_evidence = []
        
        # Analyze prompts
        for prompt in prompts:
            all_evidence.extend(self.analyze_prompt(prompt, component_name))
        
        # Analyze commit messages
        if commit_messages:
            for commit in commit_messages:
                all_evidence.extend(self.analyze_commit_message(commit, component_name))
        
        # Analyze documentation
        if documentation and component_name:
            all_evidence.extend(self.analyze_documentation(documentation, component_name))
        
        # Analyze test files
        if test_files and component_name:
            for test_content in test_files:
                all_evidence.extend(self.analyze_test_expectations(test_content, component_name))
        
        # Aggregate confidence
        confidence = self.aggregate_intent_confidence(all_evidence)
        
        # Determine if intent is confirmed (threshold: 0.6)
        intent_confirmed = confidence >= 0.6
        
        return {
            'intent_confirmed': intent_confirmed,
            'confidence': confidence,
            'evidence_count': len(all_evidence),
            'evidence': [
                {
                    'signal_type': e.signal_type.value,
                    'confidence': e.confidence,
                    'source': e.source,
                    'matched_text': e.matched_text,
                    'component_name': e.component_name
                }
                for e in all_evidence
            ],
            'signal_breakdown': self._get_signal_breakdown(all_evidence)
        }
    
    def _get_signal_breakdown(self, evidence_list: List[IntentEvidence]) -> Dict[str, int]:
        """Get breakdown of signal types"""
        breakdown = {}
        for evidence in evidence_list:
            signal_name = evidence.signal_type.value
            breakdown[signal_name] = breakdown.get(signal_name, 0) + 1
        return breakdown


if __name__ == "__main__":
    # Example usage
    tracker = AutomatedIntentTracker()
    
    # Test with sample prompts
    prompts = [
        "I need to implement the Consilium MCP server for our application",
        "How is the Consilium MCP server coming along?",
        "Is the Consilium MCP server actually working?"
    ]
    
    result = tracker.confirm_user_intent(
        prompts=prompts,
        component_name="Consilium MCP server"
    )
    
    print(f"Intent confirmed: {result['intent_confirmed']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Evidence count: {result['evidence_count']}")
    print(f"Signal breakdown: {result['signal_breakdown']}")

# Made with Bob
