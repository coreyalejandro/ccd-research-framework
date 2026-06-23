"""
User Notification System for CCD Detection
Provides warnings, verification prompts, and feedback collection
"""

from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json


class NotificationLevel(Enum):
    """Severity levels for notifications"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class InterventionType(Enum):
    """Types of interventions"""
    WARNING_ONLY = "warning_only"
    VERIFICATION_PROMPT = "verification_prompt"
    CODE_REVIEW_REQUIRED = "code_review_required"
    BLOCK_EXECUTION = "block_execution"


@dataclass
class CCDNotification:
    """Notification for CCD detection"""
    notification_id: str
    timestamp: str
    level: NotificationLevel
    component_name: str
    session_id: str
    ccd_confidence: float
    severity_weight: float
    admission_type: str
    message: str
    intervention_type: InterventionType
    verification_options: List[str]
    user_response: Optional[str] = None
    feedback_provided: bool = False


@dataclass
class UserFeedback:
    """User feedback on CCD detection"""
    notification_id: str
    timestamp: str
    is_false_positive: bool
    user_comment: str
    component_actually_exists: bool
    user_satisfaction: int  # 1-5 scale


class NotificationSystem:
    """
    User notification system for CCD detection
    Implements warning UI, verification prompts, and feedback collection
    """
    
    def __init__(self):
        self.notifications = []
        self.feedback_history = []
        self.notification_counter = 0
        
        # Intervention thresholds
        self.WARNING_THRESHOLD = 0.7
        self.VERIFICATION_THRESHOLD = 0.85
        self.CRITICAL_THRESHOLD = 0.95
    
    def create_notification(self,
                          component_name: str,
                          session_id: str,
                          ccd_confidence: float,
                          severity_weight: float,
                          admission_type: str,
                          context: Optional[Dict[str, Any]] = None) -> CCDNotification:
        """
        Create a notification for CCD detection
        
        Args:
            component_name: Name of component with suspected CCD
            session_id: Session identifier
            ccd_confidence: Confidence score (0.0-1.0)
            severity_weight: Severity multiplier (1.0 or 1.5)
            admission_type: Type of admission (sycophantic/specific)
            context: Additional context information
        
        Returns:
            CCDNotification object
        """
        self.notification_counter += 1
        notification_id = f"CCD-{self.notification_counter:06d}"
        
        # Determine notification level and intervention type
        level, intervention = self._determine_intervention(
            ccd_confidence, severity_weight
        )
        
        # Generate user-friendly message
        message = self._generate_message(
            component_name, ccd_confidence, admission_type, context
        )
        
        # Generate verification options
        verification_options = self._generate_verification_options(
            component_name, intervention
        )
        
        notification = CCDNotification(
            notification_id=notification_id,
            timestamp=datetime.now().isoformat(),
            level=level,
            component_name=component_name,
            session_id=session_id,
            ccd_confidence=ccd_confidence,
            severity_weight=severity_weight,
            admission_type=admission_type,
            message=message,
            intervention_type=intervention,
            verification_options=verification_options
        )
        
        self.notifications.append(notification)
        return notification
    
    def _determine_intervention(self,
                                confidence: float,
                                severity: float) -> tuple[NotificationLevel, InterventionType]:
        """Determine appropriate intervention based on confidence and severity"""
        adjusted_confidence = confidence * severity
        
        if adjusted_confidence >= self.CRITICAL_THRESHOLD:
            return NotificationLevel.CRITICAL, InterventionType.CODE_REVIEW_REQUIRED
        elif adjusted_confidence >= self.VERIFICATION_THRESHOLD:
            return NotificationLevel.WARNING, InterventionType.VERIFICATION_PROMPT
        elif adjusted_confidence >= self.WARNING_THRESHOLD:
            return NotificationLevel.WARNING, InterventionType.WARNING_ONLY
        else:
            return NotificationLevel.INFO, InterventionType.WARNING_ONLY
    
    def _generate_message(self,
                         component_name: str,
                         confidence: float,
                         admission_type: str,
                         context: Optional[Dict[str, Any]] = None) -> str:
        """Generate user-friendly notification message"""
        if admission_type == "specific":
            message = (
                f"⚠️ **Construct-Confidence Deception Detected**\n\n"
                f"The coding assistant claimed that **{component_name}** is implemented, "
                f"but when challenged, it specifically admitted that key components are missing.\n\n"
                f"**Confidence**: {confidence:.0%}\n"
                f"**Severity**: High (Specific Admission)\n\n"
                f"**What this means**: The assistant may have created documentation or "
                f"described the component as if it exists, but the actual implementation "
                f"is incomplete or missing.\n\n"
                f"**Recommended Action**: Verify the component exists and functions as expected "
                f"before relying on it in production code."
            )
        else:  # sycophantic
            message = (
                f"⚠️ **Potential Construct-Confidence Deception**\n\n"
                f"The coding assistant claimed that **{component_name}** is implemented, "
                f"but when challenged, it gave a vague or uncertain response.\n\n"
                f"**Confidence**: {confidence:.0%}\n"
                f"**Severity**: Medium (Sycophantic Admission)\n\n"
                f"**What this means**: The assistant may be uncertain about the actual "
                f"implementation status of this component.\n\n"
                f"**Recommended Action**: Verify the component exists and review its "
                f"implementation before proceeding."
            )
        
        if context:
            message += f"\n\n**Additional Context**:\n"
            for key, value in context.items():
                message += f"- {key}: {value}\n"
        
        return message
    
    def _generate_verification_options(self,
                                      component_name: str,
                                      intervention: InterventionType) -> List[str]:
        """Generate verification options for user"""
        base_options = [
            f"Run automated verification for {component_name}",
            f"Review code for {component_name}",
            f"Check git history for {component_name}",
            "Provide feedback on this detection"
        ]
        
        if intervention == InterventionType.CODE_REVIEW_REQUIRED:
            base_options.insert(0, "⚠️ REQUIRED: Manual code review before proceeding")
        elif intervention == InterventionType.VERIFICATION_PROMPT:
            base_options.insert(0, "Verify component exists and works")
        
        return base_options
    
    def display_notification(self, notification: CCDNotification) -> str:
        """
        Generate display-ready notification
        
        Returns:
            Formatted notification string (Markdown)
        """
        display = f"""
{'='*70}
{notification.message}
{'='*70}

**Notification ID**: {notification.notification_id}
**Timestamp**: {notification.timestamp}
**Session**: {notification.session_id}

**Verification Options**:
"""
        for i, option in enumerate(notification.verification_options, 1):
            display += f"{i}. {option}\n"
        
        display += f"\n{'='*70}\n"
        
        return display
    
    def collect_feedback(self,
                        notification_id: str,
                        is_false_positive: bool,
                        user_comment: str,
                        component_actually_exists: bool,
                        user_satisfaction: int) -> UserFeedback:
        """
        Collect user feedback on CCD detection
        
        Args:
            notification_id: ID of notification being reviewed
            is_false_positive: Whether detection was incorrect
            user_comment: Free-text user comment
            component_actually_exists: Whether component actually exists
            user_satisfaction: Satisfaction rating (1-5)
        
        Returns:
            UserFeedback object
        """
        feedback = UserFeedback(
            notification_id=notification_id,
            timestamp=datetime.now().isoformat(),
            is_false_positive=is_false_positive,
            user_comment=user_comment,
            component_actually_exists=component_actually_exists,
            user_satisfaction=user_satisfaction
        )
        
        self.feedback_history.append(feedback)
        
        # Update notification
        for notification in self.notifications:
            if notification.notification_id == notification_id:
                notification.feedback_provided = True
                notification.user_response = "feedback_collected"
                break
        
        return feedback
    
    def get_false_positive_rate(self) -> float:
        """Calculate false positive rate from user feedback"""
        if not self.feedback_history:
            return 0.0
        
        false_positives = sum(1 for f in self.feedback_history if f.is_false_positive)
        return false_positives / len(self.feedback_history)
    
    def get_user_satisfaction_score(self) -> float:
        """Calculate average user satisfaction (1-5 scale)"""
        if not self.feedback_history:
            return 0.0
        
        total_satisfaction = sum(f.user_satisfaction for f in self.feedback_history)
        return total_satisfaction / len(self.feedback_history)
    
    def generate_feedback_report(self) -> Dict[str, Any]:
        """Generate comprehensive feedback report"""
        if not self.feedback_history:
            return {
                'total_feedback': 0,
                'message': 'No feedback collected yet'
            }
        
        return {
            'total_feedback': len(self.feedback_history),
            'false_positive_rate': self.get_false_positive_rate(),
            'average_satisfaction': self.get_user_satisfaction_score(),
            'components_verified_exist': sum(
                1 for f in self.feedback_history if f.component_actually_exists
            ),
            'components_verified_missing': sum(
                1 for f in self.feedback_history if not f.component_actually_exists
            ),
            'feedback_by_notification': [
                {
                    'notification_id': f.notification_id,
                    'is_false_positive': f.is_false_positive,
                    'component_exists': f.component_actually_exists,
                    'satisfaction': f.user_satisfaction,
                    'comment': f.user_comment
                }
                for f in self.feedback_history
            ]
        }
    
    def export_notifications(self, filepath: str):
        """Export notifications to JSON file"""
        data = {
            'export_timestamp': datetime.now().isoformat(),
            'total_notifications': len(self.notifications),
            'notifications': [
                {
                    'notification_id': n.notification_id,
                    'timestamp': n.timestamp,
                    'level': n.level.value,
                    'component_name': n.component_name,
                    'session_id': n.session_id,
                    'ccd_confidence': n.ccd_confidence,
                    'severity_weight': n.severity_weight,
                    'admission_type': n.admission_type,
                    'intervention_type': n.intervention_type.value,
                    'feedback_provided': n.feedback_provided
                }
                for n in self.notifications
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)


# Global notification system instance
notification_system = NotificationSystem()


def notify_ccd_detection(component_name: str,
                        session_id: str,
                        ccd_confidence: float,
                        severity_weight: float,
                        admission_type: str,
                        display_callback: Optional[Callable] = None) -> CCDNotification:
    """
    Convenience function to create and display CCD notification
    
    Args:
        component_name: Component with suspected CCD
        session_id: Session identifier
        ccd_confidence: Detection confidence
        severity_weight: Severity multiplier
        admission_type: Type of admission
        display_callback: Optional callback to display notification
    
    Returns:
        CCDNotification object
    """
    notification = notification_system.create_notification(
        component_name=component_name,
        session_id=session_id,
        ccd_confidence=ccd_confidence,
        severity_weight=severity_weight,
        admission_type=admission_type
    )
    
    if display_callback:
        display_text = notification_system.display_notification(notification)
        display_callback(display_text)
    
    return notification


if __name__ == "__main__":
    # Example usage
    print("User Notification System Example")
    print("=" * 70)
    
    # Create notification for high-confidence CCD
    notification = notification_system.create_notification(
        component_name="Consilium MCP Server",
        session_id="session_12345",
        ccd_confidence=0.92,
        severity_weight=1.5,
        admission_type="specific",
        context={
            "sessions_with_claims": 3,
            "artifacts_found": "README.md, API_SPEC.md",
            "implementation_files": "None"
        }
    )
    
    # Display notification
    print(notification_system.display_notification(notification))
    
    # Simulate user feedback
    feedback = notification_system.collect_feedback(
        notification_id=notification.notification_id,
        is_false_positive=False,
        user_comment="Confirmed - component was only documented, not implemented",
        component_actually_exists=False,
        user_satisfaction=5
    )
    
    print(f"\nFeedback collected: {feedback.notification_id}")
    print(f"False positive: {feedback.is_false_positive}")
    print(f"User satisfaction: {feedback.user_satisfaction}/5")
    
    # Generate feedback report
    report = notification_system.generate_feedback_report()
    print(f"\nFeedback Report:")
    print(f"  Total feedback: {report['total_feedback']}")
    print(f"  False positive rate: {report['false_positive_rate']:.1%}")
    print(f"  Average satisfaction: {report['average_satisfaction']:.1f}/5")

# Made with Bob
