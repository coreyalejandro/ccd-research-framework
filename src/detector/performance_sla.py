"""
Performance SLA Monitoring for CCD Detection
Ensures <100ms detection latency and <2s end-to-end response time
"""

import time
import functools
from typing import Callable, Any, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for SLA tracking"""
    operation: str
    start_time: float
    end_time: float
    duration_ms: float
    sla_threshold_ms: float
    sla_met: bool
    timestamp: str


class SLAMonitor:
    """
    Monitor and enforce performance SLAs
    
    SLA Requirements:
    - Detection latency: <100ms
    - End-to-end response: <2s (2000ms)
    """
    
    # SLA thresholds in milliseconds
    DETECTION_SLA_MS = 100
    END_TO_END_SLA_MS = 2000
    
    def __init__(self):
        self.metrics_history = []
        self.sla_violations = []
    
    def measure_performance(self,
                          operation: str,
                          sla_threshold_ms: Optional[float] = None) -> Callable:
        """
        Decorator to measure operation performance against SLA
        
        Args:
            operation: Name of operation being measured
            sla_threshold_ms: SLA threshold in milliseconds (optional)
        
        Returns:
            Decorated function with performance monitoring
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                start_time = time.perf_counter()
                
                try:
                    result = func(*args, **kwargs)
                    
                    end_time = time.perf_counter()
                    duration_ms = (end_time - start_time) * 1000
                    
                    # Determine SLA threshold
                    threshold = sla_threshold_ms
                    if threshold is None:
                        if 'detect' in operation.lower():
                            threshold = self.DETECTION_SLA_MS
                        else:
                            threshold = self.END_TO_END_SLA_MS
                    
                    sla_met = duration_ms <= threshold
                    
                    # Record metrics
                    metrics = PerformanceMetrics(
                        operation=operation,
                        start_time=start_time,
                        end_time=end_time,
                        duration_ms=duration_ms,
                        sla_threshold_ms=threshold,
                        sla_met=sla_met,
                        timestamp=datetime.now().isoformat()
                    )
                    
                    self.metrics_history.append(metrics)
                    
                    if not sla_met:
                        self.sla_violations.append(metrics)
                        logger.warning(
                            f"SLA violation: {operation} took {duration_ms:.2f}ms "
                            f"(threshold: {threshold}ms)"
                        )
                    else:
                        logger.debug(
                            f"SLA met: {operation} took {duration_ms:.2f}ms "
                            f"(threshold: {threshold}ms)"
                        )
                    
                    return result
                    
                except Exception as e:
                    end_time = time.perf_counter()
                    duration_ms = (end_time - start_time) * 1000
                    logger.error(
                        f"Error in {operation} after {duration_ms:.2f}ms: {str(e)}"
                    )
                    raise
            
            return wrapper
        return decorator
    
    def get_sla_compliance_rate(self, operation: Optional[str] = None) -> float:
        """
        Calculate SLA compliance rate
        
        Args:
            operation: Filter by specific operation (optional)
        
        Returns:
            Compliance rate (0.0 to 1.0)
        """
        if operation:
            metrics = [m for m in self.metrics_history if m.operation == operation]
        else:
            metrics = self.metrics_history
        
        if not metrics:
            return 1.0
        
        met_count = sum(1 for m in metrics if m.sla_met)
        return met_count / len(metrics)
    
    def get_average_latency(self, operation: Optional[str] = None) -> float:
        """
        Calculate average latency in milliseconds
        
        Args:
            operation: Filter by specific operation (optional)
        
        Returns:
            Average latency in ms
        """
        if operation:
            metrics = [m for m in self.metrics_history if m.operation == operation]
        else:
            metrics = self.metrics_history
        
        if not metrics:
            return 0.0
        
        return sum(m.duration_ms for m in metrics) / len(metrics)
    
    def get_p95_latency(self, operation: Optional[str] = None) -> float:
        """
        Calculate 95th percentile latency
        
        Args:
            operation: Filter by specific operation (optional)
        
        Returns:
            P95 latency in ms
        """
        if operation:
            metrics = [m for m in self.metrics_history if m.operation == operation]
        else:
            metrics = self.metrics_history
        
        if not metrics:
            return 0.0
        
        sorted_durations = sorted(m.duration_ms for m in metrics)
        p95_index = int(len(sorted_durations) * 0.95)
        return sorted_durations[p95_index] if p95_index < len(sorted_durations) else sorted_durations[-1]
    
    def get_sla_report(self) -> Dict[str, Any]:
        """Generate comprehensive SLA report"""
        return {
            'total_operations': len(self.metrics_history),
            'sla_violations': len(self.sla_violations),
            'compliance_rate': self.get_sla_compliance_rate(),
            'average_latency_ms': self.get_average_latency(),
            'p95_latency_ms': self.get_p95_latency(),
            'detection_compliance': self.get_sla_compliance_rate('ccd_detection'),
            'detection_avg_latency': self.get_average_latency('ccd_detection'),
            'end_to_end_compliance': self.get_sla_compliance_rate('end_to_end'),
            'end_to_end_avg_latency': self.get_average_latency('end_to_end'),
            'recent_violations': [
                {
                    'operation': v.operation,
                    'duration_ms': v.duration_ms,
                    'threshold_ms': v.sla_threshold_ms,
                    'timestamp': v.timestamp
                }
                for v in self.sla_violations[-10:]  # Last 10 violations
            ]
        }
    
    def reset_metrics(self):
        """Reset all metrics (useful for testing)"""
        self.metrics_history = []
        self.sla_violations = []


# Global SLA monitor instance
sla_monitor = SLAMonitor()


# Convenience decorators
def measure_detection_sla(func: Callable) -> Callable:
    """Decorator for CCD detection operations (<100ms SLA)"""
    return sla_monitor.measure_performance('ccd_detection', sla_monitor.DETECTION_SLA_MS)(func)


def measure_end_to_end_sla(func: Callable) -> Callable:
    """Decorator for end-to-end operations (<2s SLA)"""
    return sla_monitor.measure_performance('end_to_end', sla_monitor.END_TO_END_SLA_MS)(func)


if __name__ == "__main__":
    # Example usage
    import time
    
    @measure_detection_sla
    def fast_detection():
        time.sleep(0.05)  # 50ms - meets SLA
        return "detected"
    
    @measure_detection_sla
    def slow_detection():
        time.sleep(0.15)  # 150ms - violates SLA
        return "detected"
    
    # Test SLA monitoring
    print("Testing SLA monitoring...")
    
    for i in range(5):
        fast_detection()
    
    for i in range(2):
        slow_detection()
    
    # Generate report
    report = sla_monitor.get_sla_report()
    print(f"\nSLA Report:")
    print(f"  Total operations: {report['total_operations']}")
    print(f"  SLA violations: {report['sla_violations']}")
    print(f"  Compliance rate: {report['compliance_rate']:.2%}")
    print(f"  Average latency: {report['average_latency_ms']:.2f}ms")
    print(f"  P95 latency: {report['p95_latency_ms']:.2f}ms")

# Made with Bob
