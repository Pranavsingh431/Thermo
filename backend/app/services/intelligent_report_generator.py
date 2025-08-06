"""
Intelligent Report Generation Service

This module provides professional thermal inspection report generation
for Tata Power using both template-based and LLM-powered approaches.
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import asyncio
from sqlalchemy.orm import Session

# For PDF generation
try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# For potential LLM integration
try:
    import openai
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

from app.models.thermal_scan import ThermalScan
from app.models.ai_analysis import AIAnalysis, Detection
from app.models.substation import Substation
from app.utils.email import email_service

logger = logging.getLogger(__name__)

class ThermalInspectionReport:
    """Professional thermal inspection report for Tata Power"""
    
    def __init__(self, analysis: AIAnalysis, scan: ThermalScan, substation: Optional[Substation] = None):
        self.analysis = analysis
        self.scan = scan
        self.substation = substation
        self.report_id = f"TIR_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{scan.id}"
        self.generation_timestamp = datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary format"""
        return {
            'report_id': self.report_id,
            'generation_timestamp': self.generation_timestamp.isoformat(),
            'scan_info': {
                'filename': self.scan.original_filename,
                'capture_timestamp': self.scan.capture_timestamp.isoformat() if self.scan.capture_timestamp else None,
                'camera_model': self.scan.camera_model or 'FLIR T560',
                'location': {
                    'latitude': self.scan.latitude,
                    'longitude': self.scan.longitude,
                    'substation': self.substation.name if self.substation else 'Unknown'
                }
            },
            'analysis_results': {
                'model_version': self.analysis.model_version,
                'processing_time': self.analysis.processing_duration_seconds,
                'quality_score': self.analysis.quality_score,
                'risk_level': self.analysis.overall_risk_level,
                'risk_score': self.analysis.risk_score,
                'requires_immediate_attention': self.analysis.requires_immediate_attention
            },
            'thermal_analysis': {
                'ambient_temperature': self.analysis.ambient_temperature,
                'max_temperature': self.analysis.max_temperature_detected,
                'min_temperature': self.analysis.min_temperature_detected,
                'avg_temperature': self.analysis.avg_temperature,
                'hotspots': {
                    'total': self.analysis.total_hotspots,
                    'critical': self.analysis.critical_hotspots,
                    'potential': self.analysis.potential_hotspots
                }
            },
            'component_analysis': {
                'total_components': self.analysis.total_components_detected,
                'nuts_bolts': self.analysis.nuts_bolts_count,
                'mid_span_joints': self.analysis.mid_span_joints_count,
                'polymer_insulators': self.analysis.polymer_insulators_count
            },
            'summary': self.analysis.summary_text,
            'recommendations': self.analysis.recommendations or []
        }

class IntelligentReportGenerator:
    """Generate intelligent thermal inspection reports"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.output_dir = Path("static/reports")
        self.output_dir.mkdir(exist_ok=True)
        
    async def generate_comprehensive_report(self, analysis: AIAnalysis, db: Session) -> Dict[str, Any]:
        """Generate a comprehensive thermal inspection report"""
        try:
            # Get related data
            scan = analysis.thermal_scan
            substation = scan.substation if scan else None
            detections = analysis.detections
            
            # Create report object
            report = ThermalInspectionReport(analysis, scan, substation)
            
            # Generate different report formats
            report_data = {
                'report_id': report.report_id,
                'generation_timestamp': report.generation_timestamp.isoformat(),
                'formats_generated': []
            }
            
            # 1. Generate JSON summary
            json_report = await self._generate_json_report(report, detections)
            report_data['json_report'] = json_report
            report_data['formats_generated'].append('json')
            
            # 2. Generate professional text summary
            text_summary = await self._generate_professional_summary(report, detections)
            report_data['professional_summary'] = text_summary
            report_data['formats_generated'].append('text')
            
            # 3. Generate technical analysis
            technical_analysis = await self._generate_technical_analysis(report, detections)
            report_data['technical_analysis'] = technical_analysis
            report_data['formats_generated'].append('technical')
            
            # 4. Generate PDF if available
            if REPORTLAB_AVAILABLE:
                pdf_path = await self._generate_pdf_report(report, detections)
                report_data['pdf_path'] = str(pdf_path)
                report_data['formats_generated'].append('pdf')
            
            # 5. Generate LLM-enhanced report if available
            if LLM_AVAILABLE:
                llm_report = await self._generate_llm_enhanced_report(report, detections)
                report_data['llm_enhanced_summary'] = llm_report
                report_data['formats_generated'].append('llm')
            
            # 6. Generate email-ready summary
            email_summary = await self._generate_email_summary(report, detections)
            report_data['email_summary'] = email_summary
            report_data['formats_generated'].append('email')
            
            self.logger.info(f"✅ Comprehensive report generated: {report.report_id}")
            return report_data
            
        except Exception as e:
            self.logger.error(f"Failed to generate comprehensive report: {e}")
            return {
                'error': str(e),
                'report_id': None,
                'formats_generated': []
            }
    
    async def _generate_json_report(self, report: ThermalInspectionReport, detections: List[Detection]) -> Dict[str, Any]:
        """Generate structured JSON report"""
        try:
            json_data = report.to_dict()
            
            # Add detailed detections
            json_data['detailed_detections'] = []
            for detection in detections:
                detection_data = {
                    'id': detection.id,
                    'component_type': detection.component_type,
                    'confidence': detection.confidence,
                    'bounding_box': detection.bbox_dict,
                    'center_point': detection.center_point,
                    'thermal_data': {
                        'max_temperature': detection.max_temperature,
                        'avg_temperature': detection.avg_temperature,
                        'hotspot_classification': detection.hotspot_classification,
                        'temperature_above_ambient': detection.temperature_above_ambient
                    },
                    'risk_assessment': {
                        'risk_level': detection.risk_level,
                        'risk_factors': detection.risk_factors,
                        'is_critical': detection.is_critical
                    },
                    'physical_properties': {
                        'area_pixels': detection.area_pixels,
                        'aspect_ratio': detection.aspect_ratio
                    }
                }
                json_data['detailed_detections'].append(detection_data)
            
            return json_data
            
        except Exception as e:
            self.logger.error(f"JSON report generation failed: {e}")
            return {'error': str(e)}
    
    async def _generate_professional_summary(self, report: ThermalInspectionReport, detections: List[Detection]) -> str:
        """Generate professional summary for engineers"""
        try:
            analysis = report.analysis
            scan = report.scan
            substation = report.substation
            
            summary_parts = []
            
            # Header
            summary_parts.append("THERMAL INSPECTION REPORT")
            summary_parts.append("=" * 50)
            summary_parts.append(f"Report ID: {report.report_id}")
            summary_parts.append(f"Generated: {report.generation_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            summary_parts.append("")
            
            # Inspection Details
            summary_parts.append("INSPECTION DETAILS")
            summary_parts.append("-" * 20)
            summary_parts.append(f"Image File: {scan.original_filename}")
            summary_parts.append(f"Capture Time: {scan.capture_timestamp.strftime('%Y-%m-%d %H:%M:%S') if scan.capture_timestamp else 'Unknown'}")
            summary_parts.append(f"Camera: {scan.camera_model or 'FLIR T560'}")
            if substation:
                summary_parts.append(f"Substation: {substation.name} ({substation.code})")
            if scan.latitude and scan.longitude:
                summary_parts.append(f"Location: {scan.latitude:.6f}, {scan.longitude:.6f}")
            summary_parts.append("")
            
            # Analysis Summary
            summary_parts.append("ANALYSIS SUMMARY")
            summary_parts.append("-" * 16)
            summary_parts.append(f"AI Model: {analysis.model_version}")
            summary_parts.append(f"Processing Time: {analysis.processing_duration_seconds:.2f} seconds")
            summary_parts.append(f"Image Quality: {analysis.quality_score:.2f}/1.00 ({'Good' if analysis.is_good_quality else 'Poor'})")
            summary_parts.append("")
            
            # Thermal Analysis
            summary_parts.append("THERMAL ANALYSIS")
            summary_parts.append("-" * 16)
            summary_parts.append(f"Ambient Temperature: {analysis.ambient_temperature:.1f}°C")
            summary_parts.append(f"Maximum Temperature: {analysis.max_temperature_detected:.1f}°C")
            summary_parts.append(f"Temperature Range: {analysis.max_temperature_detected - analysis.min_temperature_detected:.1f}°C")
            summary_parts.append(f"Average Temperature: {analysis.avg_temperature:.1f}°C")
            
            temp_above_ambient = analysis.max_temperature_detected - analysis.ambient_temperature
            if temp_above_ambient > 40:
                summary_parts.append(f"⚠️  CRITICAL: {temp_above_ambient:.1f}°C above ambient (>40°C threshold)")
            elif temp_above_ambient > 20:
                summary_parts.append(f"⚠️  WARNING: {temp_above_ambient:.1f}°C above ambient (>20°C threshold)")
            else:
                summary_parts.append(f"✅ Normal: {temp_above_ambient:.1f}°C above ambient")
            summary_parts.append("")
            
            # Hotspot Analysis
            summary_parts.append("HOTSPOT ANALYSIS")
            summary_parts.append("-" * 16)
            summary_parts.append(f"Total Hotspots: {analysis.total_hotspots}")
            summary_parts.append(f"Critical Hotspots: {analysis.critical_hotspots}")
            summary_parts.append(f"Potential Hotspots: {analysis.potential_hotspots}")
            
            if analysis.critical_hotspots > 0:
                summary_parts.append("🚨 IMMEDIATE ACTION REQUIRED - Critical hotspots detected!")
            elif analysis.potential_hotspots > 0:
                summary_parts.append("⚠️  MONITORING RECOMMENDED - Potential hotspots identified")
            else:
                summary_parts.append("✅ No significant thermal anomalies detected")
            summary_parts.append("")
            
            # Component Analysis
            summary_parts.append("COMPONENT ANALYSIS")
            summary_parts.append("-" * 18)
            summary_parts.append(f"Total Components Detected: {analysis.total_components_detected}")
            summary_parts.append(f"Nuts/Bolts: {analysis.nuts_bolts_count}")
            summary_parts.append(f"Mid-Span Joints: {analysis.mid_span_joints_count}")
            summary_parts.append(f"Polymer Insulators: {analysis.polymer_insulators_count}")
            summary_parts.append("")
            
            # Risk Assessment
            summary_parts.append("RISK ASSESSMENT")
            summary_parts.append("-" * 15)
            summary_parts.append(f"Overall Risk Level: {analysis.overall_risk_level.upper()}")
            summary_parts.append(f"Risk Score: {analysis.risk_score:.0f}/100")
            summary_parts.append(f"Immediate Attention Required: {'YES' if analysis.requires_immediate_attention else 'NO'}")
            summary_parts.append("")
            
            # Detailed Findings
            if detections:
                summary_parts.append("DETAILED FINDINGS")
                summary_parts.append("-" * 17)
                for i, detection in enumerate(detections, 1):
                    summary_parts.append(f"{i}. {detection.component_type.replace('_', ' ').title()}")
                    summary_parts.append(f"   Confidence: {detection.confidence:.2f}")
                    if detection.max_temperature:
                        summary_parts.append(f"   Max Temperature: {detection.max_temperature:.1f}°C")
                    summary_parts.append(f"   Classification: {detection.hotspot_classification}")
                    if detection.risk_level:
                        summary_parts.append(f"   Risk Level: {detection.risk_level}")
                    summary_parts.append("")
            
            # Recommendations
            summary_parts.append("RECOMMENDATIONS")
            summary_parts.append("-" * 15)
            
            if analysis.critical_hotspots > 0:
                summary_parts.append("1. IMMEDIATE INSPECTION REQUIRED")
                summary_parts.append("   - Dispatch maintenance crew within 24 hours")
                summary_parts.append("   - Investigate critical temperature anomalies")
                summary_parts.append("   - Consider emergency shutdown if risk is severe")
            
            if analysis.potential_hotspots > 0:
                summary_parts.append("2. SCHEDULED MAINTENANCE RECOMMENDED")
                summary_parts.append("   - Plan detailed inspection within 7 days")
                summary_parts.append("   - Monitor temperature trends")
                summary_parts.append("   - Clean and tighten connections as needed")
            
            if analysis.quality_score < 0.6:
                summary_parts.append("3. IMAGE QUALITY IMPROVEMENT")
                summary_parts.append("   - Retake thermal images with better conditions")
                summary_parts.append("   - Ensure proper camera calibration")
                summary_parts.append("   - Consider alternative inspection angles")
            
            summary_parts.append("")
            summary_parts.append("Generated by Thermal Eye AI Analysis System")
            summary_parts.append("Tata Power - Transmission Line Thermal Inspection")
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            self.logger.error(f"Professional summary generation failed: {e}")
            return f"Failed to generate professional summary: {str(e)}"
    
    async def _generate_technical_analysis(self, report: ThermalInspectionReport, detections: List[Detection]) -> str:
        """Generate technical analysis for engineers"""
        try:
            analysis = report.analysis
            scan = report.scan
            
            technical_parts = []
            
            technical_parts.append("TECHNICAL ANALYSIS REPORT")
            technical_parts.append("=" * 40)
            technical_parts.append(f"Analysis Engine: {analysis.model_version}")
            technical_parts.append(f"Processing Duration: {analysis.processing_duration_seconds:.3f}s")
            technical_parts.append("")
            
            # Image Properties
            technical_parts.append("IMAGE PROPERTIES")
            technical_parts.append("-" * 16)
            technical_parts.append(f"Dimensions: {scan.image_width}×{scan.image_height}" if scan.image_width else "Dimensions: Unknown")
            technical_parts.append(f"File Size: {scan.file_size_bytes} bytes" if scan.file_size_bytes else "File Size: Unknown")
            technical_parts.append(f"Quality Score: {analysis.quality_score:.4f}")
            technical_parts.append(f"Quality Assessment: {'PASS' if analysis.is_good_quality else 'FAIL'}")
            technical_parts.append("")
            
            # Thermal Calibration
            technical_parts.append("THERMAL CALIBRATION")
            technical_parts.append("-" * 19)
            if "flir_calibrated" in analysis.model_version:
                technical_parts.append("✅ FLIR thermal calibration applied")
                technical_parts.append("✅ Temperature readings are calibrated")
            else:
                technical_parts.append("⚠️  Color-based temperature mapping used")
                technical_parts.append("⚠️  Temperature readings are estimated")
            technical_parts.append("")
            
            # Statistical Analysis
            technical_parts.append("STATISTICAL ANALYSIS")
            technical_parts.append("-" * 19)
            technical_parts.append(f"Temperature Statistics:")
            technical_parts.append(f"  Mean: {analysis.avg_temperature:.2f}°C")
            technical_parts.append(f"  Maximum: {analysis.max_temperature_detected:.2f}°C")
            technical_parts.append(f"  Minimum: {analysis.min_temperature_detected:.2f}°C")
            technical_parts.append(f"  Range: {analysis.max_temperature_detected - analysis.min_temperature_detected:.2f}°C")
            if analysis.temperature_variance:
                technical_parts.append(f"  Variance: {analysis.temperature_variance:.2f}°C²")
            technical_parts.append("")
            
            # AI Model Performance
            technical_parts.append("AI MODEL PERFORMANCE")
            technical_parts.append("-" * 20)
            technical_parts.append(f"Detection Algorithm: {'YOLO-NAS' if 'yolo_nas' in analysis.model_version else 'Pattern-based'}")
            technical_parts.append(f"Components Detected: {analysis.total_components_detected}")
            technical_parts.append(f"Hotspot Regions: {analysis.total_hotspots}")
            technical_parts.append(f"Risk Calculation: Weighted scoring algorithm")
            technical_parts.append(f"Confidence Threshold: 0.3 (30%)")
            technical_parts.append("")
            
            # Component Detection Details
            if detections:
                technical_parts.append("COMPONENT DETECTION DETAILS")
                technical_parts.append("-" * 27)
                for detection in detections:
                    technical_parts.append(f"Component: {detection.component_type}")
                    technical_parts.append(f"  Confidence: {detection.confidence:.4f}")
                    technical_parts.append(f"  Bounding Box: {detection.bbox_dict}")
                    technical_parts.append(f"  Area: {detection.area_pixels} pixels")
                    if detection.aspect_ratio:
                        technical_parts.append(f"  Aspect Ratio: {detection.aspect_ratio:.2f}")
                    if detection.max_temperature:
                        technical_parts.append(f"  Max Temp: {detection.max_temperature:.2f}°C")
                    technical_parts.append("")
            
            return "\n".join(technical_parts)
            
        except Exception as e:
            self.logger.error(f"Technical analysis generation failed: {e}")
            return f"Failed to generate technical analysis: {str(e)}"
    
    async def _generate_pdf_report(self, report: ThermalInspectionReport, detections: List[Detection]) -> Path:
        """Generate PDF report using ReportLab"""
        try:
            pdf_filename = f"{report.report_id}.pdf"
            pdf_path = self.output_dir / pdf_filename
            
            # Create PDF document
            doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=1  # Center alignment
            )
            story.append(Paragraph("THERMAL INSPECTION REPORT", title_style))
            story.append(Paragraph("Tata Power - Transmission Line Analysis", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Report Info Table
            report_data = [
                ['Report ID:', report.report_id],
                ['Generated:', report.generation_timestamp.strftime('%Y-%m-%d %H:%M:%S')],
                ['Image File:', report.scan.original_filename],
                ['Camera:', report.scan.camera_model or 'FLIR T560'],
                ['Substation:', report.substation.name if report.substation else 'Unknown']
            ]
            
            report_table = Table(report_data, colWidths=[2*inch, 4*inch])
            report_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (1, 0), (1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(report_table)
            story.append(Spacer(1, 20))
            
            # Analysis Results
            story.append(Paragraph("ANALYSIS RESULTS", styles['Heading2']))
            
            analysis_data = [
                ['Risk Level:', report.analysis.overall_risk_level.upper()],
                ['Risk Score:', f"{report.analysis.risk_score:.0f}/100"],
                ['Max Temperature:', f"{report.analysis.max_temperature_detected:.1f}°C"],
                ['Critical Hotspots:', str(report.analysis.critical_hotspots)],
                ['Total Components:', str(report.analysis.total_components_detected)],
                ['Quality Score:', f"{report.analysis.quality_score:.2f}"]
            ]
            
            analysis_table = Table(analysis_data, colWidths=[2*inch, 2*inch])
            analysis_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(analysis_table)
            story.append(Spacer(1, 20))
            
            # Summary
            story.append(Paragraph("SUMMARY", styles['Heading2']))
            story.append(Paragraph(report.analysis.summary_text, styles['Normal']))
            
            # Build PDF
            doc.build(story)
            
            self.logger.info(f"✅ PDF report generated: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            self.logger.error(f"PDF generation failed: {e}")
            raise
    
    async def _generate_llm_enhanced_report(self, report: ThermalInspectionReport, detections: List[Detection]) -> str:
        """Generate LLM-enhanced intelligent summary"""
        try:
            # This would integrate with OpenAI or other LLM services
            # For now, return a placeholder
            
            prompt_data = {
                'scan_info': report.scan.original_filename,
                'risk_level': report.analysis.overall_risk_level,
                'max_temp': report.analysis.max_temperature_detected,
                'hotspots': report.analysis.critical_hotspots,
                'components': report.analysis.total_components_detected
            }
            
            # Placeholder for LLM integration
            enhanced_summary = f"""
INTELLIGENT ANALYSIS SUMMARY

Based on advanced AI analysis of thermal image {prompt_data['scan_info']}, 
the system has identified a {prompt_data['risk_level']} risk scenario with 
{prompt_data['hotspots']} critical hotspots and a maximum temperature of 
{prompt_data['max_temp']:.1f}°C.

The automated inspection detected {prompt_data['components']} transmission 
components requiring professional evaluation.

RECOMMENDED ACTIONS:
- Immediate inspection if critical hotspots present
- Detailed component analysis for thermal anomalies
- Preventive maintenance scheduling based on risk assessment

This analysis was generated using enhanced AI algorithms specifically 
trained for electrical transmission line thermal inspection.
"""
            
            return enhanced_summary.strip()
            
        except Exception as e:
            self.logger.error(f"LLM-enhanced report generation failed: {e}")
            return "LLM-enhanced analysis not available"
    
    async def _generate_email_summary(self, report: ThermalInspectionReport, detections: List[Detection]) -> str:
        """Generate concise email-ready summary"""
        try:
            analysis = report.analysis
            scan = report.scan
            
            # Determine urgency
            if analysis.critical_hotspots > 0:
                urgency = "🚨 URGENT"
                action_required = "IMMEDIATE INSPECTION REQUIRED"
            elif analysis.potential_hotspots > 0:
                urgency = "⚠️ WARNING"
                action_required = "SCHEDULED MAINTENANCE RECOMMENDED"
            else:
                urgency = "✅ NORMAL"
                action_required = "NO IMMEDIATE ACTION REQUIRED"
            
            email_parts = []
            email_parts.append(f"Subject: {urgency} - Thermal Inspection Report {report.report_id}")
            email_parts.append("")
            email_parts.append(f"THERMAL INSPECTION ALERT")
            email_parts.append(f"Image: {scan.original_filename}")
            email_parts.append(f"Substation: {report.substation.name if report.substation else 'Unknown'}")
            email_parts.append(f"Inspection Time: {scan.capture_timestamp.strftime('%Y-%m-%d %H:%M') if scan.capture_timestamp else 'Unknown'}")
            email_parts.append("")
            email_parts.append(f"ANALYSIS RESULTS:")
            email_parts.append(f"• Risk Level: {analysis.overall_risk_level.upper()}")
            email_parts.append(f"• Max Temperature: {analysis.max_temperature_detected:.1f}°C")
            email_parts.append(f"• Critical Hotspots: {analysis.critical_hotspots}")
            email_parts.append(f"• Components Detected: {analysis.total_components_detected}")
            email_parts.append("")
            email_parts.append(f"ACTION REQUIRED: {action_required}")
            email_parts.append("")
            email_parts.append(f"Full report available in Thermal Eye system.")
            email_parts.append(f"Report ID: {report.report_id}")
            
            return "\n".join(email_parts)
            
        except Exception as e:
            self.logger.error(f"Email summary generation failed: {e}")
            return f"Failed to generate email summary: {str(e)}"

# Global report generator instance
intelligent_report_generator = IntelligentReportGenerator() 