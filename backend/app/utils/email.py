"""
Email utilities for sending thermal analysis reports
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
from datetime import datetime
import os

from app.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
    
    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """Send an email with optional HTML body and attachments"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.username
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            # Add text body
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML body if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                        
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {os.path.basename(file_path)}'
                        )
                        msg.attach(part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_emails}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def send_thermal_analysis_report(
        self,
        analysis_results: dict,
        batch_summary: dict,
        critical_alerts: List[dict]
    ) -> bool:
        """Send thermal analysis report to chief engineer"""
        
        # Generate email content
        subject = self._generate_email_subject(batch_summary, critical_alerts)
        text_body = self._generate_text_body(analysis_results, batch_summary, critical_alerts)
        html_body = self._generate_html_body(analysis_results, batch_summary, critical_alerts)
        
        # Send to chief engineer
        recipient = settings.CHIEF_ENGINEER_EMAIL
        if not recipient or recipient == "tata.power.chief@example.com":
            logger.warning("Chief engineer email not configured - skipping email")
            return False
        
        return self.send_email(
            to_emails=[recipient],
            subject=subject,
            body=text_body,
            html_body=html_body
        )
    
    def _generate_email_subject(self, batch_summary: dict, critical_alerts: List[dict]) -> str:
        """Generate email subject based on analysis results"""
        total_images = batch_summary.get('total_images', 0)
        critical_count = len(critical_alerts)
        
        if critical_count > 0:
            return f"🚨 URGENT: {critical_count} Critical Thermal Issues Detected - {total_images} Images Analyzed"
        else:
            return f"✅ Thermal Inspection Complete - {total_images} Images Analyzed (No Critical Issues)"
    
    def _generate_text_body(
        self,
        analysis_results: dict,
        batch_summary: dict,
        critical_alerts: List[dict]
    ) -> str:
        """Generate plain text email body"""
        
        body = f"""
Thermal Inspection Analysis Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

BATCH SUMMARY
=============
Total Images Processed: {batch_summary.get('total_images', 0)}
Processing Duration: {batch_summary.get('processing_duration', 'N/A')}
Substation: {batch_summary.get('substation_name', 'Unknown')}
Batch ID: {batch_summary.get('batch_id', 'N/A')}

ANALYSIS RESULTS
================
Good Quality Images: {analysis_results.get('good_quality_count', 0)}
Poor Quality Images: {analysis_results.get('poor_quality_count', 0)}
Total Components Detected: {analysis_results.get('total_components', 0)}
Total Hotspots Found: {analysis_results.get('total_hotspots', 0)}

RISK ASSESSMENT
===============
Critical Issues: {analysis_results.get('critical_count', 0)}
Potential Issues: {analysis_results.get('potential_count', 0)}
Normal Readings: {analysis_results.get('normal_count', 0)}

"""
        
        if critical_alerts:
            body += "\nCRITICAL ALERTS REQUIRING IMMEDIATE ATTENTION\n"
            body += "=" * 45 + "\n"
            for i, alert in enumerate(critical_alerts, 1):
                body += f"""
{i}. {alert.get('component_type', 'Unknown Component')}
   Temperature: {alert.get('max_temperature', 'N/A')}°C
   Location: {alert.get('location', 'N/A')}
   Confidence: {alert.get('confidence', 0)*100:.1f}%
   Risk Level: {alert.get('risk_level', 'High')}
"""
        
        body += f"""

NEXT STEPS
==========
{'- Immediate inspection required for critical alerts' if critical_alerts else '- Continue routine monitoring'}
- Review detailed analysis in the thermal inspection dashboard
- Schedule maintenance if necessary

Report generated by Thermal Inspection AI System
For technical support, contact: [Your Contact Information]
"""
        
        return body
    
    def _generate_html_body(
        self,
        analysis_results: dict,
        batch_summary: dict,
        critical_alerts: List[dict]
    ) -> str:
        """Generate HTML email body for better formatting"""
        
        # Determine alert color based on critical count
        alert_color = "#dc3545" if critical_alerts else "#28a745"
        alert_status = "CRITICAL ISSUES DETECTED" if critical_alerts else "ALL SYSTEMS NORMAL"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: {alert_color}; color: white; padding: 15px; border-radius: 5px; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .critical {{ background-color: #fff5f5; border-left: 4px solid #dc3545; }}
        .normal {{ background-color: #f8fff8; border-left: 4px solid #28a745; }}
        .metric {{ display: inline-block; margin: 10px 15px; text-align: center; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
        .metric-label {{ font-size: 12px; color: #666; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>🔥 Thermal Inspection Analysis Report</h2>
        <p>Status: {alert_status}</p>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="section">
        <h3>📊 Batch Summary</h3>
        <div class="metric">
            <div class="metric-value">{batch_summary.get('total_images', 0)}</div>
            <div class="metric-label">Images Processed</div>
        </div>
        <div class="metric">
            <div class="metric-value">{analysis_results.get('total_components', 0)}</div>
            <div class="metric-label">Components Detected</div>
        </div>
        <div class="metric">
            <div class="metric-value">{analysis_results.get('total_hotspots', 0)}</div>
            <div class="metric-label">Hotspots Found</div>
        </div>
        <div class="metric">
            <div class="metric-value">{len(critical_alerts)}</div>
            <div class="metric-label">Critical Issues</div>
        </div>
        
        <p><strong>Substation:</strong> {batch_summary.get('substation_name', 'Unknown')}</p>
        <p><strong>Processing Duration:</strong> {batch_summary.get('processing_duration', 'N/A')}</p>
    </div>
    
    <div class="section {'critical' if critical_alerts else 'normal'}">
        <h3>⚠️ Risk Assessment</h3>
        <table>
            <tr><th>Risk Level</th><th>Count</th><th>Percentage</th></tr>
            <tr><td>Critical</td><td>{analysis_results.get('critical_count', 0)}</td><td>{analysis_results.get('critical_count', 0)/max(batch_summary.get('total_images', 1), 1)*100:.1f}%</td></tr>
            <tr><td>Potential</td><td>{analysis_results.get('potential_count', 0)}</td><td>{analysis_results.get('potential_count', 0)/max(batch_summary.get('total_images', 1), 1)*100:.1f}%</td></tr>
            <tr><td>Normal</td><td>{analysis_results.get('normal_count', 0)}</td><td>{analysis_results.get('normal_count', 0)/max(batch_summary.get('total_images', 1), 1)*100:.1f}%</td></tr>
        </table>
    </div>
"""
        
        if critical_alerts:
            html += """
    <div class="section critical">
        <h3>🚨 Critical Alerts Requiring Immediate Attention</h3>
        <table>
            <tr><th>Component</th><th>Temperature</th><th>Location</th><th>Risk Level</th><th>Confidence</th></tr>
"""
            for alert in critical_alerts:
                html += f"""
            <tr>
                <td>{alert.get('component_type', 'Unknown')}</td>
                <td>{alert.get('max_temperature', 'N/A')}°C</td>
                <td>{alert.get('location', 'N/A')}</td>
                <td>{alert.get('risk_level', 'High')}</td>
                <td>{alert.get('confidence', 0)*100:.1f}%</td>
            </tr>
"""
            html += """
        </table>
    </div>
"""
        
        html += """
    <div class="section">
        <h3>📋 Next Steps</h3>
        <ul>
"""
        if critical_alerts:
            html += "<li><strong>Immediate Action Required:</strong> Inspect critical alerts within 24 hours</li>"
            html += "<li>Schedule emergency maintenance for critical components</li>"
        else:
            html += "<li>Continue routine monitoring schedule</li>"
            html += "<li>No immediate action required</li>"
        
        html += """
            <li>Review detailed analysis in the thermal inspection dashboard</li>
            <li>Update maintenance logs with findings</li>
        </ul>
    </div>
    
    <div style="margin-top: 30px; padding: 15px; background-color: #f8f9fa; border-radius: 5px; text-align: center;">
        <p><small>Report generated by Thermal Inspection AI System<br>
        For technical support or questions, contact: [Your Contact Information]</small></p>
    </div>
</body>
</html>
"""
        return html

# Global email service instance
email_service = EmailService() 