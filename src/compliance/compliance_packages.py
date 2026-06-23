"""
Industry-specific compliance packages for CCD Research Framework.

Maps CCD detection findings to relevant regulatory and standards frameworks:
SOC2, HIPAA (for healthcare AI), ISO/IEC 42001 (AI management), and NIST AI RMF.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class ComplianceFramework(Enum):
    SOC2 = "soc2"
    HIPAA = "hipaa"
    ISO_42001 = "iso_42001"
    NIST_AI_RMF = "nist_ai_rmf"
    GDPR = "gdpr"


@dataclass
class ComplianceMapping:
    framework: ComplianceFramework
    control_id: str
    control_name: str
    relevance: str
    ccd_mitigations: List[str]


COMPLIANCE_MAPPINGS: List[ComplianceMapping] = [
    ComplianceMapping(
        framework=ComplianceFramework.SOC2,
        control_id="CC7.1",
        control_name="System Monitoring",
        relevance="CCD represents undetected system misbehavior. Monitoring hooks "
                  "and vendor dashboard satisfy SOC2 CC7.1 monitoring requirements.",
        ccd_mitigations=["VendorTransparencyDashboard", "CCDMonitor", "FallbackProtocol"],
    ),
    ComplianceMapping(
        framework=ComplianceFramework.SOC2,
        control_id="CC3.2",
        control_name="Risk Assessment",
        relevance="CCD risk must be assessed in the AI tool risk register.",
        ccd_mitigations=["RiskMitigationSystem", "FalsificationTestSuite"],
    ),
    ComplianceMapping(
        framework=ComplianceFramework.HIPAA,
        control_id="164.308(a)(1)",
        control_name="Security Management Process",
        relevance="Healthcare AI that commits CCD on clinical decision support code "
                  "creates patient safety risk. CCD detection is a required safeguard.",
        ccd_mitigations=["PROACTIVEDetector", "AcademicValidationBuffer", "GDPRComplianceManager"],
    ),
    ComplianceMapping(
        framework=ComplianceFramework.ISO_42001,
        control_id="6.1.2",
        control_name="AI Risk Assessment",
        relevance="ISO 42001 requires organizations to identify AI system risks. "
                  "CCD is a catalogued risk class for coding AI systems.",
        ccd_mitigations=["RiskMitigationSystem", "HallucinationBenchmarkSuite"],
    ),
    ComplianceMapping(
        framework=ComplianceFramework.NIST_AI_RMF,
        control_id="GOVERN 1.1",
        control_name="Policies for AI Risk",
        relevance="NIST AI RMF requires documented policies for AI risk. "
                  "CCD detection provides an empirically grounded policy anchor.",
        ccd_mitigations=["FalsificationTestSuite", "CrossModelRolloutManager"],
    ),
    ComplianceMapping(
        framework=ComplianceFramework.GDPR,
        control_id="Art. 5(1)(d)",
        control_name="Accuracy principle",
        relevance="AI-generated code that falsely claims completeness may embed "
                  "inaccurate decisions in automated processing. GDPR Art. 5 requires accuracy.",
        ccd_mitigations=["GDPRComplianceManager", "AcademicValidationBuffer"],
    ),
]


class CompliancePackageManager:
    """
    Look up CCD compliance mappings by framework.
    """

    def get_mappings(self, framework: ComplianceFramework) -> List[ComplianceMapping]:
        return [m for m in COMPLIANCE_MAPPINGS if m.framework == framework]

    def get_all_frameworks(self) -> List[ComplianceFramework]:
        return list({m.framework for m in COMPLIANCE_MAPPINGS})

    def generate_compliance_report(self, frameworks: List[ComplianceFramework]) -> str:
        lines = ["CCD Compliance Mapping Report", "=" * 40, ""]
        for fw in frameworks:
            lines.append(f"Framework: {fw.value.upper()}")
            for mapping in self.get_mappings(fw):
                lines += [
                    f"  Control: {mapping.control_id} — {mapping.control_name}",
                    f"  Relevance: {mapping.relevance}",
                    f"  Mitigations: {', '.join(mapping.ccd_mitigations)}",
                    "",
                ]
        return "\n".join(lines)
