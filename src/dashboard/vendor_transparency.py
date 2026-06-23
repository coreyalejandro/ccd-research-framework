"""
Vendor Transparency Dashboard for Azure Customers
Real-time CCD vs. Hallucination breakdown with severity metrics
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum


class FailureType(Enum):
    """Types of AI safety failures"""
    CCD = "construct_confidence_deception"
    HALLUCINATION = "hallucination"
    FUNCTIONAL = "functional"
    UNKNOWN = "unknown"


@dataclass
class FailureMetrics:
    """Metrics for a specific failure type"""
    failure_type: FailureType
    count: int
    percentage: float
    avg_severity: float
    support_tickets: int
    resolution_time_avg: float  # hours


@dataclass
class DashboardData:
    """Complete dashboard data structure"""
    timestamp: str
    time_period: str  # e.g., "last_24h", "last_7d", "last_30d"
    total_interactions: int
    failure_breakdown: List[FailureMetrics]
    severity_distribution: Dict[str, int]
    top_components: List[Dict[str, Any]]
    trend_data: List[Dict[str, Any]]
    customer_impact: Dict[str, Any]


class VendorTransparencyDashboard:
    """
    Real-time dashboard for Azure customers showing CCD detection metrics
    Implements vendor transparency enhancements from the plan
    """
    
    def __init__(self):
        self.data_store = []
        self.severity_multipliers = {
            'sycophantic': 1.0,
            'specific': 1.5,
            'none': 0.0
        }
    
    def record_interaction(self,
                          session_id: str,
                          component_name: str,
                          failure_type: FailureType,
                          admission_type: str,
                          severity_weight: float,
                          support_ticket_id: Optional[str] = None):
        """
        Record an interaction for dashboard tracking
        
        Args:
            session_id: Unique session identifier
            component_name: Component involved
            failure_type: Type of failure detected
            admission_type: Type of admission (sycophantic/specific/none)
            severity_weight: Calculated severity weight
            support_ticket_id: Associated support ticket if any
        """
        record = {
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'component_name': component_name,
            'failure_type': failure_type.value,
            'admission_type': admission_type,
            'severity_weight': severity_weight,
            'support_ticket_id': support_ticket_id
        }
        self.data_store.append(record)
    
    def calculate_failure_breakdown(self, 
                                   time_period: str = "last_24h") -> List[FailureMetrics]:
        """
        Calculate breakdown of failure types
        
        Args:
            time_period: Time period for analysis
        
        Returns:
            List of FailureMetrics
        """
        # Filter data by time period
        cutoff = self._get_time_cutoff(time_period)
        filtered_data = [
            r for r in self.data_store 
            if datetime.fromisoformat(r['timestamp']) >= cutoff
        ]
        
        if not filtered_data:
            return []
        
        # Count failures by type
        failure_counts = defaultdict(int)
        severity_sums = defaultdict(float)
        ticket_counts = defaultdict(int)
        
        for record in filtered_data:
            ftype = record['failure_type']
            failure_counts[ftype] += 1
            severity_sums[ftype] += record['severity_weight']
            if record.get('support_ticket_id'):
                ticket_counts[ftype] += 1
        
        total = len(filtered_data)
        
        # Build metrics
        metrics = []
        for ftype_str, count in failure_counts.items():
            try:
                ftype = FailureType(ftype_str)
            except ValueError:
                ftype = FailureType.UNKNOWN
            
            metrics.append(FailureMetrics(
                failure_type=ftype,
                count=count,
                percentage=(count / total) * 100,
                avg_severity=severity_sums[ftype_str] / count if count > 0 else 0.0,
                support_tickets=ticket_counts[ftype_str],
                resolution_time_avg=self._estimate_resolution_time(ftype_str)
            ))
        
        return sorted(metrics, key=lambda x: x.count, reverse=True)
    
    def calculate_severity_distribution(self, 
                                       time_period: str = "last_24h") -> Dict[str, int]:
        """
        Calculate distribution of severity multipliers
        
        Returns:
            Dictionary mapping severity level to count
        """
        cutoff = self._get_time_cutoff(time_period)
        filtered_data = [
            r for r in self.data_store 
            if datetime.fromisoformat(r['timestamp']) >= cutoff
        ]
        
        distribution = {
            'none (0.0x)': 0,
            'sycophantic (1.0x)': 0,
            'specific (1.5x)': 0
        }
        
        for record in filtered_data:
            admission = record.get('admission_type', 'none')
            if admission == 'sycophantic':
                distribution['sycophantic (1.0x)'] += 1
            elif admission == 'specific':
                distribution['specific (1.5x)'] += 1
            else:
                distribution['none (0.0x)'] += 1
        
        return distribution
    
    def get_top_components(self, 
                          time_period: str = "last_24h",
                          limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top components with CCD issues
        
        Returns:
            List of component dictionaries with metrics
        """
        cutoff = self._get_time_cutoff(time_period)
        filtered_data = [
            r for r in self.data_store 
            if datetime.fromisoformat(r['timestamp']) >= cutoff
            and r['failure_type'] == FailureType.CCD.value
        ]
        
        component_metrics = defaultdict(lambda: {
            'count': 0,
            'severity_sum': 0.0,
            'tickets': 0
        })
        
        for record in filtered_data:
            comp = record['component_name']
            component_metrics[comp]['count'] += 1
            component_metrics[comp]['severity_sum'] += record['severity_weight']
            if record.get('support_ticket_id'):
                component_metrics[comp]['tickets'] += 1
        
        # Convert to list and sort
        components = []
        for comp, metrics in component_metrics.items():
            components.append({
                'component_name': comp,
                'ccd_count': metrics['count'],
                'avg_severity': metrics['severity_sum'] / metrics['count'],
                'support_tickets': metrics['tickets']
            })
        
        return sorted(components, key=lambda x: x['ccd_count'], reverse=True)[:limit]
    
    def calculate_trend_data(self, 
                            time_period: str = "last_7d",
                            granularity: str = "daily") -> List[Dict[str, Any]]:
        """
        Calculate trend data over time
        
        Args:
            time_period: Overall time period
            granularity: "hourly" or "daily"
        
        Returns:
            List of time-series data points
        """
        cutoff = self._get_time_cutoff(time_period)
        filtered_data = [
            r for r in self.data_store 
            if datetime.fromisoformat(r['timestamp']) >= cutoff
        ]
        
        # Group by time buckets
        time_buckets = defaultdict(lambda: {
            'ccd_count': 0,
            'hallucination_count': 0,
            'functional_count': 0,
            'total': 0
        })
        
        for record in filtered_data:
            timestamp = datetime.fromisoformat(record['timestamp'])
            
            if granularity == "hourly":
                bucket = timestamp.replace(minute=0, second=0, microsecond=0)
            else:  # daily
                bucket = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
            
            bucket_key = bucket.isoformat()
            time_buckets[bucket_key]['total'] += 1
            
            ftype = record['failure_type']
            if ftype == FailureType.CCD.value:
                time_buckets[bucket_key]['ccd_count'] += 1
            elif ftype == FailureType.HALLUCINATION.value:
                time_buckets[bucket_key]['hallucination_count'] += 1
            elif ftype == FailureType.FUNCTIONAL.value:
                time_buckets[bucket_key]['functional_count'] += 1
        
        # Convert to list and sort by time
        trend_data = []
        for bucket_key, metrics in sorted(time_buckets.items()):
            trend_data.append({
                'timestamp': bucket_key,
                'ccd_count': metrics['ccd_count'],
                'hallucination_count': metrics['hallucination_count'],
                'functional_count': metrics['functional_count'],
                'total': metrics['total']
            })
        
        return trend_data
    
    def calculate_customer_impact(self, 
                                 time_period: str = "last_24h") -> Dict[str, Any]:
        """
        Calculate customer impact metrics
        
        Returns:
            Dictionary with impact metrics
        """
        cutoff = self._get_time_cutoff(time_period)
        filtered_data = [
            r for r in self.data_store 
            if datetime.fromisoformat(r['timestamp']) >= cutoff
        ]
        
        total_interactions = len(filtered_data)
        ccd_interactions = sum(1 for r in filtered_data if r['failure_type'] == FailureType.CCD.value)
        support_tickets = sum(1 for r in filtered_data if r.get('support_ticket_id'))
        
        # Calculate average severity
        total_severity = sum(r['severity_weight'] for r in filtered_data)
        avg_severity = total_severity / total_interactions if total_interactions > 0 else 0.0
        
        # Estimate time saved by CCD detection
        time_saved_hours = ccd_interactions * 2.5  # Assume 2.5 hours saved per detected CCD
        
        return {
            'total_interactions': total_interactions,
            'ccd_detected': ccd_interactions,
            'ccd_rate': (ccd_interactions / total_interactions * 100) if total_interactions > 0 else 0.0,
            'support_tickets_generated': support_tickets,
            'support_ticket_rate': (support_tickets / total_interactions * 100) if total_interactions > 0 else 0.0,
            'avg_severity_weight': avg_severity,
            'estimated_time_saved_hours': time_saved_hours,
            'estimated_cost_saved_usd': time_saved_hours * 150  # Assume $150/hour developer time
        }
    
    def generate_dashboard_data(self, time_period: str = "last_24h") -> DashboardData:
        """
        Generate complete dashboard data
        
        Args:
            time_period: Time period for analysis
        
        Returns:
            DashboardData object
        """
        cutoff = self._get_time_cutoff(time_period)
        filtered_data = [
            r for r in self.data_store 
            if datetime.fromisoformat(r['timestamp']) >= cutoff
        ]
        
        return DashboardData(
            timestamp=datetime.now().isoformat(),
            time_period=time_period,
            total_interactions=len(filtered_data),
            failure_breakdown=self.calculate_failure_breakdown(time_period),
            severity_distribution=self.calculate_severity_distribution(time_period),
            top_components=self.get_top_components(time_period),
            trend_data=self.calculate_trend_data(time_period),
            customer_impact=self.calculate_customer_impact(time_period)
        )
    
    def export_dashboard_json(self, time_period: str = "last_24h") -> str:
        """
        Export dashboard data as JSON
        
        Returns:
            JSON string
        """
        dashboard_data = self.generate_dashboard_data(time_period)
        
        # Convert to dict with proper serialization
        data_dict = {
            'timestamp': dashboard_data.timestamp,
            'time_period': dashboard_data.time_period,
            'total_interactions': dashboard_data.total_interactions,
            'failure_breakdown': [
                {
                    'failure_type': m.failure_type.value,
                    'count': m.count,
                    'percentage': round(m.percentage, 2),
                    'avg_severity': round(m.avg_severity, 2),
                    'support_tickets': m.support_tickets,
                    'resolution_time_avg': round(m.resolution_time_avg, 2)
                }
                for m in dashboard_data.failure_breakdown
            ],
            'severity_distribution': dashboard_data.severity_distribution,
            'top_components': dashboard_data.top_components,
            'trend_data': dashboard_data.trend_data,
            'customer_impact': dashboard_data.customer_impact
        }
        
        return json.dumps(data_dict, indent=2)
    
    def generate_html_dashboard(self, time_period: str = "last_24h") -> str:
        """
        Generate HTML dashboard for web display
        
        Returns:
            HTML string
        """
        dashboard_data = self.generate_dashboard_data(time_period)
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>CCD Transparency Dashboard - Azure</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #0078d4;
            border-bottom: 3px solid #0078d4;
            padding-bottom: 10px;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .metric-card.ccd {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}
        .metric-card.functional {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }}
        .metric-value {{
            font-size: 36px;
            font-weight: bold;
            margin: 10px 0;
        }}
        .metric-label {{
            font-size: 14px;
            opacity: 0.9;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #0078d4;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .severity-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }}
        .severity-none {{
            background-color: #e0e0e0;
            color: #666;
        }}
        .severity-sycophantic {{
            background-color: #fff3cd;
            color: #856404;
        }}
        .severity-specific {{
            background-color: #f8d7da;
            color: #721c24;
        }}
        .timestamp {{
            color: #666;
            font-size: 14px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 CCD Transparency Dashboard</h1>
        <p class="timestamp">Generated: {dashboard_data.timestamp} | Period: {time_period}</p>
        
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-label">Total Interactions</div>
                <div class="metric-value">{dashboard_data.total_interactions:,}</div>
            </div>
            <div class="metric-card ccd">
                <div class="metric-label">CCD Detected</div>
                <div class="metric-value">{dashboard_data.customer_impact['ccd_detected']}</div>
                <div class="metric-label">{dashboard_data.customer_impact['ccd_rate']:.1f}% of total</div>
            </div>
            <div class="metric-card functional">
                <div class="metric-label">Support Tickets</div>
                <div class="metric-value">{dashboard_data.customer_impact['support_tickets_generated']}</div>
                <div class="metric-label">{dashboard_data.customer_impact['support_ticket_rate']:.1f}% rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Time Saved</div>
                <div class="metric-value">{dashboard_data.customer_impact['estimated_time_saved_hours']:.0f}h</div>
                <div class="metric-label">${dashboard_data.customer_impact['estimated_cost_saved_usd']:,.0f} saved</div>
            </div>
        </div>
        
        <h2>Failure Type Breakdown</h2>
        <table>
            <thead>
                <tr>
                    <th>Failure Type</th>
                    <th>Count</th>
                    <th>Percentage</th>
                    <th>Avg Severity</th>
                    <th>Support Tickets</th>
                    <th>Avg Resolution Time</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for metric in dashboard_data.failure_breakdown:
            html += f"""
                <tr>
                    <td><strong>{metric.failure_type.value.replace('_', ' ').title()}</strong></td>
                    <td>{metric.count}</td>
                    <td>{metric.percentage:.1f}%</td>
                    <td>{metric.avg_severity:.2f}x</td>
                    <td>{metric.support_tickets}</td>
                    <td>{metric.resolution_time_avg:.1f}h</td>
                </tr>
"""
        
        html += """
            </tbody>
        </table>
        
        <h2>Severity Distribution</h2>
        <table>
            <thead>
                <tr>
                    <th>Severity Level</th>
                    <th>Count</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for severity, count in dashboard_data.severity_distribution.items():
            badge_class = 'severity-none'
            if 'sycophantic' in severity:
                badge_class = 'severity-sycophantic'
            elif 'specific' in severity:
                badge_class = 'severity-specific'
            
            html += f"""
                <tr>
                    <td><span class="severity-badge {badge_class}">{severity}</span></td>
                    <td>{count}</td>
                </tr>
"""
        
        html += """
            </tbody>
        </table>
        
        <h2>Top Components with CCD Issues</h2>
        <table>
            <thead>
                <tr>
                    <th>Component</th>
                    <th>CCD Count</th>
                    <th>Avg Severity</th>
                    <th>Support Tickets</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for comp in dashboard_data.top_components[:10]:
            html += f"""
                <tr>
                    <td><strong>{comp['component_name']}</strong></td>
                    <td>{comp['ccd_count']}</td>
                    <td>{comp['avg_severity']:.2f}x</td>
                    <td>{comp['support_tickets']}</td>
                </tr>
"""
        
        html += """
            </tbody>
        </table>
    </div>
</body>
</html>
"""
        
        return html
    
    def _get_time_cutoff(self, time_period: str) -> datetime:
        """Get cutoff datetime for time period"""
        now = datetime.now()
        
        if time_period == "last_1h":
            return now - timedelta(hours=1)
        elif time_period == "last_24h":
            return now - timedelta(hours=24)
        elif time_period == "last_7d":
            return now - timedelta(days=7)
        elif time_period == "last_30d":
            return now - timedelta(days=30)
        else:
            return now - timedelta(hours=24)  # default
    
    def _estimate_resolution_time(self, failure_type: str) -> float:
        """Estimate average resolution time in hours"""
        # Simplified estimation
        if failure_type == FailureType.CCD.value:
            return 4.5
        elif failure_type == FailureType.HALLUCINATION.value:
            return 2.0
        else:
            return 1.0


if __name__ == "__main__":
    print("Vendor Transparency Dashboard Example")
    print("=" * 50)
    
    # Create dashboard
    dashboard = VendorTransparencyDashboard()
    
    # Simulate some interactions
    for i in range(100):
        dashboard.record_interaction(
            session_id=f"session_{i}",
            component_name=f"Component_{i % 10}",
            failure_type=FailureType.CCD if i % 3 == 0 else FailureType.FUNCTIONAL,
            admission_type='specific' if i % 5 == 0 else 'sycophantic',
            severity_weight=1.5 if i % 5 == 0 else 1.0,
            support_ticket_id=f"ticket_{i}" if i % 10 == 0 else None
        )
    
    # Generate dashboard
    data = dashboard.generate_dashboard_data("last_24h")
    print(f"\nTotal interactions: {data.total_interactions}")
    print(f"CCD detected: {data.customer_impact['ccd_detected']}")
    print(f"Time saved: {data.customer_impact['estimated_time_saved_hours']:.0f} hours")
    
    # Export JSON
    json_output = dashboard.export_dashboard_json("last_24h")
    print(f"\nJSON output length: {len(json_output)} characters")
    
    # Generate HTML
    html_output = dashboard.generate_html_dashboard("last_24h")
    print(f"HTML output length: {len(html_output)} characters")
    print("\n✓ Dashboard generated successfully")

# Made with Bob
