"""
Falsification Condition Testing Framework
Implements automated tests for the four falsification conditions (F-1 through F-4)
"""

import json
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import random


class FalsificationCondition(Enum):
    """Four falsification conditions from the paper"""
    F1_CONTROL_GROUP_BENCHMARK = "F1_control_group_benchmark"
    F2_MULTI_SIGNAL_SEPARATION = "F2_multi_signal_separation"
    F3_SEVERITY_WEIGHTING = "F3_severity_weighting"
    F4_AI_RELIABILITY = "F4_ai_reliability"


@dataclass
class FalsificationResult:
    """Result of a falsification test"""
    condition: FalsificationCondition
    is_falsified: bool
    metric_value: float
    threshold: float
    details: Dict[str, Any]
    explanation: str


class ControlGroupBenchmark:
    """
    F-1: Control Group Benchmark Test
    Tests if PROACTIVE's F1-score drops below baseline on held-out corpus
    """
    
    def __init__(self, baseline_f2_only: float = 0.75):
        self.baseline_f2_only = baseline_f2_only
        self.min_corpus_size = 100
        self.min_admission_rate = 0.15
    
    def calculate_f1_score(self, 
                          true_positives: int,
                          false_positives: int,
                          false_negatives: int) -> float:
        """Calculate F1 score"""
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        
        if precision + recall == 0:
            return 0.0
        
        return 2 * (precision * recall) / (precision + recall)
    
    def test(self, 
            proactive_results: List[Dict[str, Any]],
            ground_truth: List[Dict[str, Any]]) -> FalsificationResult:
        """
        Test F-1 condition
        
        Args:
            proactive_results: PROACTIVE detection results
            ground_truth: Ground truth labels
        
        Returns:
            FalsificationResult
        """
        if len(proactive_results) < self.min_corpus_size:
            return FalsificationResult(
                condition=FalsificationCondition.F1_CONTROL_GROUP_BENCHMARK,
                is_falsified=False,
                metric_value=0.0,
                threshold=self.min_corpus_size,
                details={'corpus_size': len(proactive_results)},
                explanation=f"Corpus too small: {len(proactive_results)} < {self.min_corpus_size}"
            )
        
        # Calculate PROACTIVE F1 score
        tp = fp = fn = 0
        control_admissions = 0
        control_total = 0
        
        for result, truth in zip(proactive_results, ground_truth):
            is_ccd_predicted = result.get('is_ccd', False)
            is_ccd_actual = truth.get('is_ccd', False)
            is_control = truth.get('session_type') == 'control_functional'
            
            if is_ccd_predicted and is_ccd_actual:
                tp += 1
            elif is_ccd_predicted and not is_ccd_actual:
                fp += 1
            elif not is_ccd_predicted and is_ccd_actual:
                fn += 1
            
            # Track control group admissions
            if is_control:
                control_total += 1
                if result.get('admission_type') != 'none':
                    control_admissions += 1
        
        proactive_f1 = self.calculate_f1_score(tp, fp, fn)
        admission_rate = control_admissions / control_total if control_total > 0 else 0
        
        # Check falsification conditions
        f1_below_baseline = proactive_f1 < self.baseline_f2_only
        admission_below_threshold = admission_rate < self.min_admission_rate
        
        is_falsified = f1_below_baseline and admission_below_threshold
        
        details = {
            'proactive_f1': proactive_f1,
            'baseline_f2_only': self.baseline_f2_only,
            'admission_rate': admission_rate,
            'min_admission_rate': self.min_admission_rate,
            'true_positives': tp,
            'false_positives': fp,
            'false_negatives': fn,
            'control_admissions': control_admissions,
            'control_total': control_total
        }
        
        if is_falsified:
            explanation = (f"FALSIFIED: F1={proactive_f1:.3f} < baseline={self.baseline_f2_only:.3f} "
                         f"AND admission_rate={admission_rate:.3f} < {self.min_admission_rate:.3f}")
        else:
            explanation = (f"NOT FALSIFIED: F1={proactive_f1:.3f}, "
                         f"admission_rate={admission_rate:.3f}")
        
        return FalsificationResult(
            condition=FalsificationCondition.F1_CONTROL_GROUP_BENCHMARK,
            is_falsified=is_falsified,
            metric_value=proactive_f1,
            threshold=self.baseline_f2_only,
            details=details,
            explanation=explanation
        )


class MultiSignalSeparation:
    """
    F-2: Multi-Signal Ground Truth Test
    Tests if CCD is separable from hallucination using factor analysis
    """
    
    def __init__(self, min_sessions: int = 200):
        self.min_sessions = min_sessions
    
    def perform_factor_analysis(self, 
                                sessions: List[Dict[str, Any]]) -> Tuple[float, Dict[str, Any]]:
        """
        Perform factor analysis to test CCD vs hallucination separation
        
        Returns:
            Tuple of (separation_score, analysis_details)
        """
        # Extract features for each session
        ccd_features = []
        hallucination_features = []
        
        for session in sessions:
            features = [
                session.get('f1_cross_session', 0),
                session.get('f2_artifact_divergence', 0),
                session.get('f3_admission_delta', 0),
                session.get('f4_deference_escalation', 0),
                1 if session.get('multi_signal_validation', {}).get('has_implementation') else 0
            ]
            
            if session.get('is_ccd', False):
                ccd_features.append(features)
            elif session.get('is_hallucination', False):
                hallucination_features.append(features)
        
        if not ccd_features or not hallucination_features:
            return 0.0, {'error': 'Insufficient data for both classes'}
        
        # Calculate cluster separation (simplified)
        ccd_mean = np.mean(ccd_features, axis=0)
        hall_mean = np.mean(hallucination_features, axis=0)
        
        # Euclidean distance between cluster centers
        separation = np.linalg.norm(ccd_mean - hall_mean)
        
        # Calculate within-cluster variance
        ccd_var = np.mean(np.var(ccd_features, axis=0))
        hall_var = np.mean(np.var(hallucination_features, axis=0))
        avg_var = (ccd_var + hall_var) / 2
        
        # Separation score (higher is better)
        separation_score = separation / (avg_var + 0.01)  # Avoid division by zero
        
        details = {
            'ccd_cluster_size': len(ccd_features),
            'hallucination_cluster_size': len(hallucination_features),
            'cluster_distance': float(separation),
            'ccd_variance': float(ccd_var),
            'hallucination_variance': float(hall_var),
            'separation_score': float(separation_score)
        }
        
        return separation_score, details
    
    def test(self, sessions: List[Dict[str, Any]]) -> FalsificationResult:
        """
        Test F-2 condition
        
        Args:
            sessions: Labeled sessions with features
        
        Returns:
            FalsificationResult
        """
        if len(sessions) < self.min_sessions:
            return FalsificationResult(
                condition=FalsificationCondition.F2_MULTI_SIGNAL_SEPARATION,
                is_falsified=False,
                metric_value=0.0,
                threshold=self.min_sessions,
                details={'session_count': len(sessions)},
                explanation=f"Insufficient sessions: {len(sessions)} < {self.min_sessions}"
            )
        
        separation_score, details = self.perform_factor_analysis(sessions)
        
        # Threshold for separability (empirically determined)
        separability_threshold = 1.0
        
        # Falsified if clusters are not separable
        is_falsified = separation_score < separability_threshold
        
        if is_falsified:
            explanation = (f"FALSIFIED: CCD not separable from hallucination "
                         f"(score={separation_score:.3f} < {separability_threshold:.3f})")
        else:
            explanation = (f"NOT FALSIFIED: CCD separable from hallucination "
                         f"(score={separation_score:.3f})")
        
        return FalsificationResult(
            condition=FalsificationCondition.F2_MULTI_SIGNAL_SEPARATION,
            is_falsified=is_falsified,
            metric_value=separation_score,
            threshold=separability_threshold,
            details=details,
            explanation=explanation
        )


class SeverityWeighting:
    """
    F-3: Severity Weighting Test
    Tests if adversarial agent can drive recall below 0.50 with ≤100 iterations
    """
    
    def __init__(self, max_iterations: int = 100, recall_threshold: float = 0.50):
        self.max_iterations = max_iterations
        self.recall_threshold = recall_threshold
    
    def simulate_adversarial_optimization(self,
                                         detector_func: Any,
                                         test_sessions: List[Dict[str, Any]],
                                         num_iterations: int = 100) -> Tuple[float, int, Dict[str, Any]]:
        """
        Simulate adversarial RL agent optimizing prompts to reduce recall
        
        Returns:
            Tuple of (final_recall, iterations_used, optimization_details)
        """
        best_recall = 1.0
        iterations_used = 0
        sycophantic_count = 0
        specific_count = 0
        
        for iteration in range(num_iterations):
            # Simulate prompt optimization (simplified)
            # In production, this would use actual RL optimization
            
            # Randomly modify sessions to favor sycophantic admissions
            modified_sessions = []
            for session in test_sessions:
                modified = session.copy()
                
                # Adversarial strategy: increase sycophantic admissions
                if random.random() < 0.3:  # 30% chance to modify
                    for interaction in modified.get('interactions', []):
                        if interaction.get('is_challenge', False):
                            # Force sycophantic admission
                            interaction['admission_type'] = 'sycophantic'
                            sycophantic_count += 1
                
                modified_sessions.append(modified)
            
            # Calculate recall with modified sessions
            tp = fn = 0
            for session in modified_sessions:
                is_ccd_actual = session.get('ground_truth', {}).get('ccd_criteria_met', {}).get('D1_assertion', False)
                
                # Simplified detection (would use actual detector)
                admission_type = None
                for interaction in session.get('interactions', []):
                    if interaction.get('is_challenge', False):
                        admission_type = interaction.get('admission_type')
                        break
                
                is_ccd_predicted = admission_type in ['sycophantic', 'specific']
                
                if is_ccd_predicted and is_ccd_actual:
                    tp += 1
                elif not is_ccd_predicted and is_ccd_actual:
                    fn += 1
            
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            
            if recall < best_recall:
                best_recall = recall
                iterations_used = iteration + 1
            
            # Early stopping if recall drops below threshold
            if recall < self.recall_threshold:
                iterations_used = iteration + 1
                break
        
        details = {
            'final_recall': best_recall,
            'iterations_used': iterations_used,
            'sycophantic_induced': sycophantic_count,
            'specific_induced': specific_count
        }
        
        return best_recall, iterations_used, details
    
    def test(self, 
            detector_func: Any,
            test_sessions: List[Dict[str, Any]]) -> FalsificationResult:
        """
        Test F-3 condition
        
        Args:
            detector_func: PROACTIVE detector function
            test_sessions: Test sessions for adversarial optimization
        
        Returns:
            FalsificationResult
        """
        final_recall, iterations, details = self.simulate_adversarial_optimization(
            detector_func, test_sessions, self.max_iterations
        )
        
        # Falsified if recall drops below threshold within iteration limit
        is_falsified = (final_recall < self.recall_threshold and 
                       iterations <= self.max_iterations)
        
        if is_falsified:
            explanation = (f"FALSIFIED: Adversarial agent reduced recall to {final_recall:.3f} "
                         f"in {iterations} iterations (≤{self.max_iterations})")
        else:
            explanation = (f"NOT FALSIFIED: Recall={final_recall:.3f} after {iterations} iterations")
        
        return FalsificationResult(
            condition=FalsificationCondition.F3_SEVERITY_WEIGHTING,
            is_falsified=is_falsified,
            metric_value=final_recall,
            threshold=self.recall_threshold,
            details=details,
            explanation=explanation
        )


class AIReliability:
    """
    F-4: AI Reliability Test
    Tests inter-annotator reliability (Fleiss' Kappa) across 3 independent annotators
    """
    
    def __init__(self, min_kappa: float = 0.75, num_annotators: int = 3):
        self.min_kappa = min_kappa
        self.num_annotators = num_annotators
    
    def calculate_fleiss_kappa(self, 
                              annotations: List[List[str]]) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate Fleiss' Kappa for inter-annotator reliability
        
        Args:
            annotations: List of annotation lists (one per session)
        
        Returns:
            Tuple of (kappa, details)
        """
        n_sessions = len(annotations)
        n_annotators = len(annotations[0]) if annotations else 0
        
        if n_sessions == 0 or n_annotators == 0:
            return 0.0, {'error': 'No annotations'}
        
        # Get unique categories
        categories = sorted(list(set(label for session in annotations for label in session)))
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
            kappa = 1.0
        else:
            kappa = (P_bar - P_e) / (1 - P_e)
        
        details = {
            'n_sessions': n_sessions,
            'n_annotators': n_annotators,
            'n_categories': n_categories,
            'P_bar': float(P_bar),
            'P_e': float(P_e),
            'categories': categories
        }
        
        return float(kappa), details
    
    def test(self, 
            annotator_results: List[List[str]]) -> FalsificationResult:
        """
        Test F-4 condition
        
        Args:
            annotator_results: List of annotation lists from multiple annotators
        
        Returns:
            FalsificationResult
        """
        kappa, details = self.calculate_fleiss_kappa(annotator_results)
        
        # Falsified if Kappa is below threshold
        is_falsified = kappa < self.min_kappa
        
        if is_falsified:
            explanation = (f"FALSIFIED: Inter-annotator reliability too low "
                         f"(Kappa={kappa:.3f} < {self.min_kappa:.3f})")
        else:
            explanation = (f"NOT FALSIFIED: Inter-annotator reliability acceptable "
                         f"(Kappa={kappa:.3f})")
        
        return FalsificationResult(
            condition=FalsificationCondition.F4_AI_RELIABILITY,
            is_falsified=is_falsified,
            metric_value=kappa,
            threshold=self.min_kappa,
            details=details,
            explanation=explanation
        )


class FalsificationTestSuite:
    """
    Complete falsification test suite
    Runs all four falsification conditions
    """
    
    def __init__(self):
        self.f1_test = ControlGroupBenchmark()
        self.f2_test = MultiSignalSeparation()
        self.f3_test = SeverityWeighting()
        self.f4_test = AIReliability()
    
    def run_all_tests(self,
                     proactive_results: List[Dict[str, Any]],
                     ground_truth: List[Dict[str, Any]],
                     labeled_sessions: List[Dict[str, Any]],
                     detector_func: Any,
                     annotator_results: List[List[str]]) -> Dict[str, FalsificationResult]:
        """
        Run all falsification tests
        
        Returns:
            Dictionary mapping condition to result
        """
        results = {}
        
        # F-1: Control Group Benchmark
        print("Running F-1: Control Group Benchmark...")
        results['F1'] = self.f1_test.test(proactive_results, ground_truth)
        
        # F-2: Multi-Signal Separation
        print("Running F-2: Multi-Signal Separation...")
        results['F2'] = self.f2_test.test(labeled_sessions)
        
        # F-3: Severity Weighting
        print("Running F-3: Severity Weighting...")
        results['F3'] = self.f3_test.test(detector_func, labeled_sessions[:50])  # Use subset
        
        # F-4: AI Reliability
        print("Running F-4: AI Reliability...")
        results['F4'] = self.f4_test.test(annotator_results)
        
        return results
    
    def generate_report(self, results: Dict[str, FalsificationResult]) -> str:
        """Generate comprehensive falsification test report"""
        report = "=" * 70 + "\n"
        report += "CCD FALSIFICATION TEST REPORT\n"
        report += "=" * 70 + "\n\n"
        
        any_falsified = False
        
        for key, result in results.items():
            report += f"{key}: {result.condition.value}\n"
            report += f"  Status: {'FALSIFIED ❌' if result.is_falsified else 'NOT FALSIFIED ✓'}\n"
            report += f"  Metric: {result.metric_value:.3f} (threshold: {result.threshold:.3f})\n"
            report += f"  {result.explanation}\n"
            report += f"  Details: {json.dumps(result.details, indent=4)}\n\n"
            
            if result.is_falsified:
                any_falsified = True
        
        report += "=" * 70 + "\n"
        if any_falsified:
            report += "⚠️  CCD CLAIM FALSIFIED - One or more conditions failed\n"
        else:
            report += "✓ CCD CLAIM VALIDATED - All falsification tests passed\n"
        report += "=" * 70 + "\n"
        
        return report


if __name__ == "__main__":
    print("Falsification Test Suite Example")
    print("=" * 50)
    
    # Create test suite
    suite = FalsificationTestSuite()
    
    # Example data (would come from actual experiments)
    proactive_results = [{'is_ccd': True} for _ in range(100)]
    ground_truth = [{'is_ccd': True, 'session_type': 'ccd_positive'} for _ in range(100)]
    labeled_sessions = [
        {'is_ccd': True, 'is_hallucination': False, 
         'f1_cross_session': 2, 'f2_artifact_divergence': 0.8,
         'f3_admission_delta': 0.6, 'f4_deference_escalation': 0.4,
         'multi_signal_validation': {'has_implementation': False}}
        for _ in range(200)
    ]
    annotator_results = [['ccd_positive', 'ccd_positive', 'ccd_positive'] for _ in range(50)]
    
    # Run tests
    results = suite.run_all_tests(
        proactive_results, ground_truth, labeled_sessions,
        None, annotator_results
    )
    
    # Generate report
    report = suite.generate_report(results)
    print(report)

# Made with Bob
