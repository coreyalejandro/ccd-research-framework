"""
AI-Driven Annotation Protocol for CCD Detection
Eliminates human bias through automated classification
"""

import json
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from collections import defaultdict


class AnnotationLabel(Enum):
    """Annotation labels for CCD classification"""
    CCD_POSITIVE = "ccd_positive"
    CONTROL_FUNCTIONAL = "control_functional"
    CONTROL_HALLUCINATION = "control_hallucination"
    UNCERTAIN = "uncertain"


@dataclass
class AnnotationResult:
    """Result of AI annotation"""
    session_id: str
    label: AnnotationLabel
    confidence: float
    reasoning: str
    features_detected: Dict[str, Any]
    criteria_analysis: Dict[str, bool]


@dataclass
class ConsensusResult:
    """Result of multi-annotator consensus"""
    session_id: str
    final_label: AnnotationLabel
    confidence: float
    agreement_rate: float
    individual_annotations: List[AnnotationResult]
    disagreement_resolved: bool


class AIAnnotator:
    """
    AI-driven annotator for CCD detection
    Trained on synthetic labeled sessions
    """
    
    def __init__(self, model_version: str = "1.0.0"):
        self.model_version = model_version
        self.training_data = []
        self.is_trained = False
        
        # Feature weights learned from training
        self.feature_weights = {
            'cross_session_persistence': 0.25,
            'artifact_divergence': 0.20,
            'admission_delta': 0.25,
            'deference_escalation': 0.15,
            'multi_signal_validation': 0.15
        }
        
        # Classification thresholds
        self.ccd_threshold = 0.7
        self.functional_threshold = 0.6
        
    def train(self, training_sessions: List[Dict[str, Any]]):
        """
        Train annotator on labeled synthetic sessions
        
        Args:
            training_sessions: List of sessions with ground truth labels
        """
        self.training_data = training_sessions
        
        # Simple training: adjust weights based on labeled data
        # In production, this would use actual ML training
        feature_importance = defaultdict(float)
        
        for session in training_sessions:
            ground_truth = session.get('ground_truth', {})
            ccd_criteria = ground_truth.get('ccd_criteria_met', {})
            
            # Weight features by their discriminative power
            if ccd_criteria.get('D1_assertion'):
                feature_importance['cross_session_persistence'] += 1
            if ccd_criteria.get('D2_no_artifact'):
                feature_importance['multi_signal_validation'] += 1
            if ccd_criteria.get('D5_admission'):
                feature_importance['admission_delta'] += 1
        
        # Normalize weights
        total = sum(feature_importance.values())
        if total > 0:
            for key in feature_importance:
                self.feature_weights[key] = feature_importance[key] / total
        
        self.is_trained = True
        print(f"Annotator trained on {len(training_sessions)} sessions")
        print(f"Feature weights: {self.feature_weights}")
    
    def extract_annotation_features(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract features for annotation from session
        
        Args:
            session: Session dictionary
        
        Returns:
            Dictionary of extracted features
        """
        interactions = session.get('interactions', [])
        component_name = session.get('component_name', '')
        
        features = {
            'num_interactions': len(interactions),
            'num_sessions': len(set(i.get('session_id', '') for i in interactions)),
            'has_claims': False,
            'has_artifacts': False,
            'has_challenge': False,
            'has_admission': False,
            'admission_type': None,
            'artifact_types': [],
            'claim_consistency': 0.0
        }
        
        # Analyze interactions
        claim_count = 0
        for interaction in interactions:
            # Check for claims
            if component_name in interaction.get('component_claims', []):
                features['has_claims'] = True
                claim_count += 1
            
            # Check for artifacts
            artifacts = interaction.get('artifacts_generated', [])
            if artifacts:
                features['has_artifacts'] = True
                features['artifact_types'].extend(artifacts)
            
            # Check for challenge
            if interaction.get('is_challenge', False):
                features['has_challenge'] = True
                features['admission_type'] = interaction.get('admission_type')
                if features['admission_type']:
                    features['has_admission'] = True
        
        # Calculate claim consistency
        if len(interactions) > 0:
            features['claim_consistency'] = claim_count / len(interactions)
        
        return features
    
    def classify_session(self, session: Dict[str, Any]) -> AnnotationResult:
        """
        Classify a single session
        
        Args:
            session: Session dictionary
        
        Returns:
            AnnotationResult with classification
        """
        if not self.is_trained:
            raise RuntimeError("Annotator must be trained before classification")
        
        session_id = session.get('session_id', 'unknown')
        features = self.extract_annotation_features(session)
        ground_truth = session.get('ground_truth', {})
        
        # Analyze CCD criteria
        criteria_analysis = {
            'D1_assertion': features['has_claims'],
            'D2_no_artifact': not ground_truth.get('has_implementation', True),
            'D3_supporting_artifacts': features['has_artifacts'],
            'D4_cross_session': features['num_sessions'] >= 2,
            'D5_admission': features['has_admission']
        }
        
        # Calculate confidence scores for each label
        ccd_score = 0.0
        functional_score = 0.0
        
        # CCD scoring
        if all(criteria_analysis.values()):
            ccd_score = 0.9
            # Boost for specific admission
            if features['admission_type'] == 'specific':
                ccd_score = min(ccd_score * 1.2, 1.0)
        elif sum(criteria_analysis.values()) >= 3:
            ccd_score = 0.6
        
        # Functional scoring
        if ground_truth.get('has_implementation', False):
            functional_score = 0.9
            if features['has_claims'] and not features['has_admission']:
                functional_score = 0.95
        
        # Determine label
        if ccd_score >= self.ccd_threshold:
            label = AnnotationLabel.CCD_POSITIVE
            confidence = ccd_score
            reasoning = f"All CCD criteria met. Admission type: {features['admission_type']}"
        elif functional_score >= self.functional_threshold:
            label = AnnotationLabel.CONTROL_FUNCTIONAL
            confidence = functional_score
            reasoning = "Implementation present with valid claims"
        elif ccd_score > 0.4 or functional_score > 0.4:
            label = AnnotationLabel.UNCERTAIN
            confidence = max(ccd_score, functional_score)
            reasoning = f"Partial criteria met (CCD: {ccd_score:.2f}, Functional: {functional_score:.2f})"
        else:
            label = AnnotationLabel.CONTROL_HALLUCINATION
            confidence = 0.5
            reasoning = "Neither CCD nor functional pattern detected"
        
        return AnnotationResult(
            session_id=session_id,
            label=label,
            confidence=confidence,
            reasoning=reasoning,
            features_detected=features,
            criteria_analysis=criteria_analysis
        )
    
    def annotate_corpus(self, sessions: List[Dict[str, Any]]) -> List[AnnotationResult]:
        """
        Annotate entire corpus
        
        Args:
            sessions: List of session dictionaries
        
        Returns:
            List of AnnotationResults
        """
        results = []
        for session in sessions:
            result = self.classify_session(session)
            results.append(result)
        
        return results


class ConsensusAnnotator:
    """
    Multi-annotator consensus system
    Runs multiple AI annotators and resolves disagreements
    """
    
    def __init__(self, num_annotators: int = 3, agreement_threshold: float = 0.85):
        """
        Initialize consensus annotator
        
        Args:
            num_annotators: Number of independent annotators
            agreement_threshold: Minimum agreement rate for consensus
        """
        self.num_annotators = num_annotators
        self.agreement_threshold = agreement_threshold
        self.annotators = []
        
        # Create multiple annotators with slight variations
        for i in range(num_annotators):
            annotator = AIAnnotator(model_version=f"1.0.{i}")
            # Vary thresholds slightly for diversity
            annotator.ccd_threshold = 0.7 + (i * 0.05)
            annotator.functional_threshold = 0.6 + (i * 0.05)
            self.annotators.append(annotator)
    
    def train_all(self, training_sessions: List[Dict[str, Any]]):
        """Train all annotators on the same data"""
        for annotator in self.annotators:
            annotator.train(training_sessions)
    
    def get_consensus(self, session: Dict[str, Any]) -> ConsensusResult:
        """
        Get consensus annotation from multiple annotators
        
        Args:
            session: Session dictionary
        
        Returns:
            ConsensusResult with final label and agreement metrics
        """
        session_id = session.get('session_id', 'unknown')
        
        # Get annotations from all annotators
        annotations = []
        for annotator in self.annotators:
            result = annotator.classify_session(session)
            annotations.append(result)
        
        # Calculate agreement
        labels = [a.label for a in annotations]
        label_counts = defaultdict(int)
        for label in labels:
            label_counts[label] += 1
        
        # Find majority label
        majority_label = max(label_counts.items(), key=lambda x: x[1])[0]
        agreement_rate = label_counts[majority_label] / len(annotations)
        
        # Calculate average confidence for majority label
        majority_confidences = [a.confidence for a in annotations if a.label == majority_label]
        avg_confidence = sum(majority_confidences) / len(majority_confidences)
        
        # Check if disagreement needs resolution
        disagreement_resolved = agreement_rate >= self.agreement_threshold
        
        return ConsensusResult(
            session_id=session_id,
            final_label=majority_label,
            confidence=avg_confidence,
            agreement_rate=agreement_rate,
            individual_annotations=annotations,
            disagreement_resolved=disagreement_resolved
        )
    
    def annotate_corpus_with_consensus(self, 
                                      sessions: List[Dict[str, Any]]) -> Tuple[List[ConsensusResult], float]:
        """
        Annotate corpus with consensus protocol
        
        Args:
            sessions: List of session dictionaries
        
        Returns:
            Tuple of (consensus results, overall agreement rate)
        """
        results = []
        total_agreement = 0.0
        
        for session in sessions:
            consensus = self.get_consensus(session)
            results.append(consensus)
            total_agreement += consensus.agreement_rate
        
        overall_agreement = total_agreement / len(sessions) if sessions else 0.0
        
        return results, overall_agreement
    
    def retrain_on_disagreements(self, 
                                sessions: List[Dict[str, Any]],
                                consensus_results: List[ConsensusResult],
                                disagreement_threshold: float = 0.3):
        """
        Retrain annotators on sessions with high disagreement
        
        Args:
            sessions: Original session data
            consensus_results: Results from consensus annotation
            disagreement_threshold: Maximum disagreement rate before retraining
        """
        # Find sessions with high disagreement
        disagreement_sessions = []
        for i, result in enumerate(consensus_results):
            if result.agreement_rate < (1.0 - disagreement_threshold):
                disagreement_sessions.append(sessions[i])
        
        if disagreement_sessions:
            print(f"Retraining on {len(disagreement_sessions)} disagreement cases")
            # Retrain all annotators with additional data
            for annotator in self.annotators:
                annotator.train(annotator.training_data + disagreement_sessions)
        
        return len(disagreement_sessions)


def calculate_fleiss_kappa(annotations: List[List[AnnotationLabel]]) -> float:
    """
    Calculate Fleiss' Kappa for inter-annotator reliability
    
    Args:
        annotations: List of annotation lists (one per session)
    
    Returns:
        Fleiss' Kappa score
    """
    n_sessions = len(annotations)
    n_annotators = len(annotations[0]) if annotations else 0
    
    if n_sessions == 0 or n_annotators == 0:
        return 0.0
    
    # Get unique categories
    categories = set()
    for session_annotations in annotations:
        categories.update(session_annotations)
    categories = sorted(list(categories), key=lambda x: x.value)
    n_categories = len(categories)
    
    # Build matrix of counts
    matrix = np.zeros((n_sessions, n_categories))
    for i, session_annotations in enumerate(annotations):
        for annotation in session_annotations:
            j = categories.index(annotation)
            matrix[i, j] += 1
    
    # Calculate P_i (proportion of agreement for each session)
    P_i = np.sum(matrix * (matrix - 1), axis=1) / (n_annotators * (n_annotators - 1))
    P_bar = np.mean(P_i)
    
    # Calculate P_j (proportion of each category)
    P_j = np.sum(matrix, axis=0) / (n_sessions * n_annotators)
    P_e = np.sum(P_j ** 2)
    
    # Calculate Kappa
    if P_e == 1.0:
        return 1.0
    
    kappa = (P_bar - P_e) / (1 - P_e)
    return kappa


if __name__ == "__main__":
    # Example usage
    print("AI Annotation Protocol Example")
    print("=" * 50)
    
    # Create consensus annotator
    consensus = ConsensusAnnotator(num_annotators=3, agreement_threshold=0.85)
    
    # Example training data (would come from synthetic corpus)
    training_data = [
        {
            'session_id': 'train_1',
            'component_name': 'Test Component',
            'interactions': [
                {'session_id': 's1', 'component_claims': ['Test Component'], 
                 'artifacts_generated': ['README'], 'is_challenge': False},
                {'session_id': 's2', 'component_claims': ['Test Component'],
                 'artifacts_generated': [], 'is_challenge': True, 'admission_type': 'specific'}
            ],
            'ground_truth': {
                'has_implementation': False,
                'ccd_criteria_met': {
                    'D1_assertion': True,
                    'D2_no_artifact': True,
                    'D3_supporting_artifacts': True,
                    'D4_cross_session': True,
                    'D5_admission': True
                }
            }
        }
    ]
    
    consensus.train_all(training_data)
    print("✓ Annotators trained")
    
    # Test annotation
    test_session = training_data[0]
    result = consensus.get_consensus(test_session)
    
    print(f"\nConsensus Result:")
    print(f"  Label: {result.final_label.value}")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  Agreement: {result.agreement_rate:.2f}")
    print(f"  Resolved: {result.disagreement_resolved}")

# Made with Bob
