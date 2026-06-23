"""
Academic Validation Buffer System
Ensures independent falsification testing before benchmark integration
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class ValidationStatus(Enum):
    """Status of academic validation"""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_REVISION = "requires_revision"


class ReviewerRole(Enum):
    """Role of reviewer"""
    INTERNAL_RESEARCHER = "internal_researcher"  # Dr. Voss
    EXTERNAL_ACADEMIC = "external_academic"  # Prof. Tanaka
    VENDOR_REPRESENTATIVE = "vendor_representative"  # Sarah Chen


@dataclass
class ValidationSubmission:
    """Submission for academic validation"""
    submission_id: str
    submitted_by: str
    submission_date: str
    component: str  # e.g., "PROACTIVE detector", "Falsification tests"
    description: str
    falsification_conditions: List[str]
    test_results: Dict[str, Any]
    supporting_data: Dict[str, Any]
    status: ValidationStatus


@dataclass
class ReviewFeedback:
    """Feedback from a reviewer"""
    reviewer_id: str
    reviewer_role: ReviewerRole
    review_date: str
    status: ValidationStatus
    comments: str
    required_changes: List[str]
    approval_conditions: List[str]


@dataclass
class ValidationRecord:
    """Complete validation record"""
    submission: ValidationSubmission
    reviews: List[ReviewFeedback]
    final_status: ValidationStatus
    approval_date: Optional[str]
    integration_approved: bool


class AcademicValidationBuffer:
    """
    Academic validation buffer system
    Implements mandatory independent falsification testing before benchmark integration
    """
    
    def __init__(self):
        self.submissions = []
        self.reviews = []
        self.validation_records = []
        
        # Validation requirements
        self.min_reviews_required = 2  # At least 2 independent reviews
        self.required_reviewer_roles = [
            ReviewerRole.EXTERNAL_ACADEMIC,  # Prof. Tanaka required
            ReviewerRole.INTERNAL_RESEARCHER  # Dr. Voss required
        ]
    
    def submit_for_validation(self,
                             submitted_by: str,
                             component: str,
                             description: str,
                             falsification_conditions: List[str],
                             test_results: Dict[str, Any],
                             supporting_data: Dict[str, Any]) -> str:
        """
        Submit component for academic validation
        
        Args:
            submitted_by: Name of submitter
            component: Component being validated
            description: Description of component
            falsification_conditions: List of falsification conditions tested
            test_results: Results of falsification tests
            supporting_data: Additional supporting data
        
        Returns:
            Submission ID
        """
        submission_id = f"VAL-{len(self.submissions) + 1:04d}"
        
        submission = ValidationSubmission(
            submission_id=submission_id,
            submitted_by=submitted_by,
            submission_date=datetime.now().isoformat(),
            component=component,
            description=description,
            falsification_conditions=falsification_conditions,
            test_results=test_results,
            supporting_data=supporting_data,
            status=ValidationStatus.PENDING
        )
        
        self.submissions.append(submission)
        
        print(f"✓ Submission {submission_id} created for '{component}'")
        print(f"  Falsification conditions: {', '.join(falsification_conditions)}")
        print(f"  Status: {submission.status.value}")
        
        return submission_id
    
    def submit_review(self,
                     submission_id: str,
                     reviewer_id: str,
                     reviewer_role: ReviewerRole,
                     status: ValidationStatus,
                     comments: str,
                     required_changes: Optional[List[str]] = None,
                     approval_conditions: Optional[List[str]] = None) -> bool:
        """
        Submit a review for a validation submission
        
        Args:
            submission_id: ID of submission being reviewed
            reviewer_id: ID of reviewer
            reviewer_role: Role of reviewer
            status: Review status
            comments: Review comments
            required_changes: List of required changes
            approval_conditions: List of conditions for approval
        
        Returns:
            True if review submitted successfully
        """
        # Find submission
        submission = None
        for s in self.submissions:
            if s.submission_id == submission_id:
                submission = s
                break
        
        if not submission:
            print(f"✗ Submission {submission_id} not found")
            return False
        
        # Create review
        review = ReviewFeedback(
            reviewer_id=reviewer_id,
            reviewer_role=reviewer_role,
            review_date=datetime.now().isoformat(),
            status=status,
            comments=comments,
            required_changes=required_changes or [],
            approval_conditions=approval_conditions or []
        )
        
        self.reviews.append({
            'submission_id': submission_id,
            'review': review
        })
        
        # Update submission status
        submission.status = ValidationStatus.IN_REVIEW
        
        print(f"✓ Review submitted for {submission_id} by {reviewer_id}")
        print(f"  Role: {reviewer_role.value}")
        print(f"  Status: {status.value}")
        
        return True
    
    def check_validation_complete(self, submission_id: str) -> bool:
        """
        Check if validation is complete for a submission
        
        Args:
            submission_id: ID of submission
        
        Returns:
            True if validation is complete
        """
        # Get all reviews for this submission
        submission_reviews = [
            r['review'] for r in self.reviews 
            if r['submission_id'] == submission_id
        ]
        
        if len(submission_reviews) < self.min_reviews_required:
            return False
        
        # Check if all required reviewer roles have submitted
        reviewer_roles = set(r.reviewer_role for r in submission_reviews)
        required_roles = set(self.required_reviewer_roles)
        
        if not required_roles.issubset(reviewer_roles):
            return False
        
        # Check if all reviews are approved
        all_approved = all(
            r.status == ValidationStatus.APPROVED 
            for r in submission_reviews
        )
        
        return all_approved
    
    def finalize_validation(self, submission_id: str) -> Optional[ValidationRecord]:
        """
        Finalize validation and create validation record
        
        Args:
            submission_id: ID of submission
        
        Returns:
            ValidationRecord if validation complete, None otherwise
        """
        # Find submission
        submission = None
        for s in self.submissions:
            if s.submission_id == submission_id:
                submission = s
                break
        
        if not submission:
            print(f"✗ Submission {submission_id} not found")
            return None
        
        # Get all reviews
        submission_reviews = [
            r['review'] for r in self.reviews 
            if r['submission_id'] == submission_id
        ]
        
        # Check if validation is complete
        if not self.check_validation_complete(submission_id):
            print(f"✗ Validation not complete for {submission_id}")
            print(f"  Reviews received: {len(submission_reviews)}/{self.min_reviews_required}")
            return None
        
        # Determine final status
        all_approved = all(
            r.status == ValidationStatus.APPROVED 
            for r in submission_reviews
        )
        
        final_status = ValidationStatus.APPROVED if all_approved else ValidationStatus.REQUIRES_REVISION
        
        # Create validation record
        record = ValidationRecord(
            submission=submission,
            reviews=submission_reviews,
            final_status=final_status,
            approval_date=datetime.now().isoformat() if all_approved else None,
            integration_approved=all_approved
        )
        
        self.validation_records.append(record)
        
        # Update submission status
        submission.status = final_status
        
        print(f"✓ Validation finalized for {submission_id}")
        print(f"  Final status: {final_status.value}")
        print(f"  Integration approved: {all_approved}")
        
        return record
    
    def get_validation_status(self, submission_id: str) -> Dict[str, Any]:
        """
        Get current validation status for a submission
        
        Args:
            submission_id: ID of submission
        
        Returns:
            Dictionary with validation status details
        """
        # Find submission
        submission = None
        for s in self.submissions:
            if s.submission_id == submission_id:
                submission = s
                break
        
        if not submission:
            return {'error': f'Submission {submission_id} not found'}
        
        # Get reviews
        submission_reviews = [
            r['review'] for r in self.reviews 
            if r['submission_id'] == submission_id
        ]
        
        # Check completion
        is_complete = self.check_validation_complete(submission_id)
        
        return {
            'submission_id': submission_id,
            'component': submission.component,
            'status': submission.status.value,
            'reviews_received': len(submission_reviews),
            'reviews_required': self.min_reviews_required,
            'validation_complete': is_complete,
            'integration_ready': is_complete and submission.status == ValidationStatus.APPROVED,
            'reviews': [
                {
                    'reviewer_id': r.reviewer_id,
                    'reviewer_role': r.reviewer_role.value,
                    'status': r.status.value,
                    'review_date': r.review_date
                }
                for r in submission_reviews
            ]
        }
    
    def generate_validation_report(self, submission_id: str) -> str:
        """
        Generate comprehensive validation report
        
        Args:
            submission_id: ID of submission
        
        Returns:
            Formatted report string
        """
        status = self.get_validation_status(submission_id)
        
        if 'error' in status:
            return status['error']
        
        report = "=" * 70 + "\n"
        report += "ACADEMIC VALIDATION REPORT\n"
        report += "=" * 70 + "\n\n"
        
        report += f"Submission ID: {status['submission_id']}\n"
        report += f"Component: {status['component']}\n"
        report += f"Status: {status['status']}\n"
        report += f"Validation Complete: {'Yes ✓' if status['validation_complete'] else 'No ✗'}\n"
        report += f"Integration Ready: {'Yes ✓' if status['integration_ready'] else 'No ✗'}\n\n"
        
        report += f"Reviews Received: {status['reviews_received']}/{status['reviews_required']}\n"
        report += "-" * 70 + "\n\n"
        
        for review in status['reviews']:
            report += f"Reviewer: {review['reviewer_id']}\n"
            report += f"  Role: {review['reviewer_role']}\n"
            report += f"  Status: {review['status']}\n"
            report += f"  Date: {review['review_date']}\n\n"
        
        report += "=" * 70 + "\n"
        
        if status['integration_ready']:
            report += "✓ APPROVED FOR SAFETY BENCHMARKS V2.0 INTEGRATION\n"
        else:
            report += "⚠️  NOT YET APPROVED FOR INTEGRATION\n"
        
        report += "=" * 70 + "\n"
        
        return report
    
    def export_validation_records(self, output_path: str):
        """
        Export all validation records to JSON
        
        Args:
            output_path: Path to output file
        """
        records_data = []
        
        for record in self.validation_records:
            records_data.append({
                'submission': asdict(record.submission),
                'reviews': [asdict(r) for r in record.reviews],
                'final_status': record.final_status.value,
                'approval_date': record.approval_date,
                'integration_approved': record.integration_approved
            })
        
        with open(output_path, 'w') as f:
            json.dump({
                'export_date': datetime.now().isoformat(),
                'total_records': len(records_data),
                'records': records_data
            }, f, indent=2)
        
        print(f"✓ Exported {len(records_data)} validation records to {output_path}")


if __name__ == "__main__":
    print("Academic Validation Buffer Example")
    print("=" * 70)
    
    # Create validation buffer
    buffer = AcademicValidationBuffer()
    
    # Submit PROACTIVE detector for validation
    submission_id = buffer.submit_for_validation(
        submitted_by="CCD Research Team",
        component="PROACTIVE Detector v1.0",
        description="Multi-signal CCD detection system with four-feature classification",
        falsification_conditions=["F-1", "F-2", "F-3", "F-4"],
        test_results={
            'F-1': {'is_falsified': False, 'f1_score': 0.89},
            'F-2': {'is_falsified': False, 'separation_score': 1.45},
            'F-3': {'is_falsified': False, 'final_recall': 0.78},
            'F-4': {'is_falsified': False, 'kappa': 0.82}
        },
        supporting_data={
            'corpus_size': 200,
            'ccd_positive_cases': 19,
            'control_cases': 20
        }
    )
    
    print("\n" + "-" * 70 + "\n")
    
    # Submit review from Prof. Tanaka (external academic)
    buffer.submit_review(
        submission_id=submission_id,
        reviewer_id="Prof. Kenji Tanaka",
        reviewer_role=ReviewerRole.EXTERNAL_ACADEMIC,
        status=ValidationStatus.APPROVED,
        comments="Falsification conditions are rigorous and well-tested. Theoretical framework is sound.",
        approval_conditions=["Publish open-source ccd-detector package for replication"]
    )
    
    print("\n" + "-" * 70 + "\n")
    
    # Submit review from Dr. Voss (internal researcher)
    buffer.submit_review(
        submission_id=submission_id,
        reviewer_id="Dr. Elena Voss",
        reviewer_role=ReviewerRole.INTERNAL_RESEARCHER,
        status=ValidationStatus.APPROVED,
        comments="Aligns with Safety Benchmarks v2.0 requirements. Ready for integration.",
        approval_conditions=["Complete phased rollout plan"]
    )
    
    print("\n" + "-" * 70 + "\n")
    
    # Finalize validation
    record = buffer.finalize_validation(submission_id)
    
    print("\n" + "-" * 70 + "\n")
    
    # Generate report
    report = buffer.generate_validation_report(submission_id)
    print(report)

# Made with Bob
