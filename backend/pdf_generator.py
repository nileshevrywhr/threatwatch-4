"""
PDF Report Generator for ThreatWatch Intelligence Reports
Professional hybrid-style reports with Executive Summary + Detailed Analysis + Article Appendix
"""
import os
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics import renderPDF

class ThreatWatchPDFGenerator:
    """
    Professional PDF report generator for threat intelligence analysis
    """
    
    def __init__(self, cache_dir: str = "/tmp/threatwatch_reports"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Professional styling
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for professional appearance"""
        
        # Title style
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#1a1a1a'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader', 
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.HexColor('#2c3e50'),
            fontName='Helvetica-Bold'
        ))
        
        # Subsection header style
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading2'], 
            fontSize=14,
            spaceAfter=8,
            spaceBefore=12,
            textColor=colors.HexColor('#34495e'),
            fontName='Helvetica-Bold'
        ))
        
        # Executive summary style
        self.styles.add(ParagraphStyle(
            name='ExecutiveSummary',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leading=14,
            textColor=colors.HexColor('#2c3e50'),
            alignment=TA_JUSTIFY
        ))
        
        # Threat item style
        self.styles.add(ParagraphStyle(
            name='ThreatItem',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=4,
            leftIndent=20,
            bulletIndent=10,
            textColor=colors.HexColor('#e74c3c')
        ))
        
        # Article content style
        self.styles.add(ParagraphStyle(
            name='ArticleContent',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=4,
            leading=11,
            textColor=colors.HexColor('#4a4a4a'),
            alignment=TA_JUSTIFY
        ))
        
        # Metadata style
        self.styles.add(ParagraphStyle(
            name='Metadata',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=2,
            textColor=colors.HexColor('#7f8c8d'),
            fontName='Helvetica-Oblique'
        ))

    def generate_report(self, scan_data: Dict[str, Any]) -> str:
        """
        Generate a comprehensive PDF report from scan data
        
        Args:
            scan_data: Quick scan result data from API
            
        Returns:
            File path to generated PDF
        """
        # Generate cache key from scan data
        cache_key = self._generate_cache_key(scan_data)
        pdf_path = self.cache_dir / f"{cache_key}.pdf"
        
        # Return cached version if exists and recent
        if pdf_path.exists() and self._is_cache_valid(pdf_path):
            return str(pdf_path)
        
        # Generate filename
        query = scan_data.get('query', 'unknown')
        safe_query = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).strip()
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = f"ThreatWatch_Report_{safe_query}_{date_str}.pdf"
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
            title=f"ThreatWatch Intelligence Report - {query}",
            author="ThreatWatch",
            subject=f"Threat Intelligence Analysis for {query}"
        )
        
        # Build report content
        story = []
        
        # Add report sections
        self._add_header(story, scan_data)
        self._add_executive_summary(story, scan_data)
        self._add_key_metrics(story, scan_data)
        
        # Page break before detailed analysis
        story.append(PageBreak())
        
        self._add_detailed_analysis(story, scan_data)
        self._add_recommendations(story, scan_data)
        
        # Page break before appendix
        story.append(PageBreak())
        
        self._add_article_appendix(story, scan_data)
        self._add_footer_info(story, scan_data)
        
        # Build PDF
        doc.build(story)
        
        return str(pdf_path)
    
    def _generate_cache_key(self, scan_data: Dict[str, Any]) -> str:
        """Generate unique cache key for scan data"""
        content = f"{scan_data.get('query', '')}{scan_data.get('timestamp', '')}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_cache_valid(self, pdf_path: Path, max_age_hours: int = 48) -> bool:
        """Check if cached PDF is still valid"""
        if not pdf_path.exists():
            return False
        
        file_age = datetime.now() - datetime.fromtimestamp(pdf_path.stat().st_mtime)
        return file_age.total_seconds() < (max_age_hours * 3600)
    
    def _add_header(self, story: List, scan_data: Dict[str, Any]):
        """Add report header with title and metadata"""
        query = scan_data.get('query', 'Unknown Query')
        timestamp = scan_data.get('timestamp')
        
        # Format timestamp
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_date = dt.strftime('%B %d, %Y at %I:%M %p UTC')
            except:
                formatted_date = "Recent"
        else:
            formatted_date = datetime.now().strftime('%B %d, %Y at %I:%M %p UTC')
        
        # Title
        story.append(Paragraph("ThreatWatch Intelligence Report", self.styles['ReportTitle']))
        story.append(Spacer(1, 12))
        
        # Query and date info
        header_data = [
            ['Search Query:', query],
            ['Generated:', formatted_date],
            ['Report Type:', 'Enhanced Google Search Analysis'],
            ['Status:', 'Confidential - Internal Use Only']
        ]
        
        header_table = Table(header_data, colWidths=[1.5*inch, 4*inch])
        header_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2c3e50')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LINEBELOW', (0, -1), (-1, -1), 1, colors.HexColor('#bdc3c7')),
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 20))
    
    def _add_executive_summary(self, story: List, scan_data: Dict[str, Any]):
        """Add executive summary section"""
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        
        # Extract executive summary from AI analysis
        summary_text = scan_data.get('summary', '')
        exec_summary = self._extract_section(summary_text, 'EXECUTIVE SUMMARY')
        
        if exec_summary:
            story.append(Paragraph(exec_summary, self.styles['ExecutiveSummary']))
        else:
            # Fallback summary
            query = scan_data.get('query', 'the specified query')
            articles_count = len(scan_data.get('discovered_links', []))
            fallback_summary = f"""
            This report analyzes recent threat intelligence related to "{query}" based on {articles_count} 
            news articles discovered through comprehensive Google search analysis. The research covers the 
            latest security incidents, vulnerabilities, and threat vectors to provide actionable intelligence 
            for security professionals.
            """
            story.append(Paragraph(fallback_summary.strip(), self.styles['ExecutiveSummary']))
        
        story.append(Spacer(1, 12))
    
    def _add_key_metrics(self, story: List, scan_data: Dict[str, Any]):
        """Add key metrics visualization including cost breakdown"""
        story.append(Paragraph("Key Metrics & Cost Analysis", self.styles['SectionHeader']))
        
        # Gather metrics
        search_metadata = scan_data.get('search_metadata', {})
        articles_analyzed = search_metadata.get('articles_analyzed', len(scan_data.get('discovered_links', [])))
        total_results = search_metadata.get('total_results', '0')
        key_threats_count = len(scan_data.get('key_threats', []))
        
        # Create metrics table
        metrics_data = [
            ['Metric', 'Value', 'Description'],
            ['Articles Analyzed', str(articles_analyzed), 'News articles processed by AI'],
            ['Total Search Results', f"{int(total_results):,}" if str(total_results).isdigit() else str(total_results), 'Total Google search matches'],
            ['Key Threats Identified', str(key_threats_count), 'Critical threats extracted from analysis'],
            ['Search Timeframe', '7 days', 'Recent articles from past week'],
            ['Analysis Method', 'AI-Powered (GPT-4o)', 'Advanced language model analysis']
        ]
        
        metrics_table = Table(metrics_data, colWidths=[2*inch, 1.5*inch, 2.5*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        
        story.append(metrics_table)
        story.append(Spacer(1, 15))
        
        # Add cost breakdown section
        self._add_cost_breakdown(story, scan_data)
        story.append(Spacer(1, 20))
    
    def _add_detailed_analysis(self, story: List, scan_data: Dict[str, Any]):
        """Add detailed AI analysis section"""
        story.append(Paragraph("Detailed Threat Analysis", self.styles['SectionHeader']))
        
        summary_text = scan_data.get('summary', '')
        
        # Extract and display key threats
        key_threats_section = self._extract_section(summary_text, 'KEY THREATS')
        if key_threats_section:
            story.append(Paragraph("Identified Threats:", self.styles['SubsectionHeader']))
            # Process bullet points
            threats = [line.strip() for line in key_threats_section.split('\n') if line.strip().startswith('•')]
            for threat in threats:
                clean_threat = threat.replace('•', '').strip()
                story.append(Paragraph(f"• {clean_threat}", self.styles['ThreatItem']))
            story.append(Spacer(1, 12))
        
        # Extract and display security implications
        implications_section = self._extract_section(summary_text, 'SECURITY IMPLICATIONS')
        if implications_section:
            story.append(Paragraph("Security Implications:", self.styles['SubsectionHeader']))
            implications = [line.strip() for line in implications_section.split('\n') if line.strip().startswith('•')]
            for implication in implications:
                clean_implication = implication.replace('•', '').strip()
                story.append(Paragraph(f"• {clean_implication}", self.styles['ExecutiveSummary']))
            story.append(Spacer(1, 12))
    
    def _add_recommendations(self, story: List, scan_data: Dict[str, Any]):
        """Add actionable recommendations section"""
        story.append(Paragraph("Actionable Recommendations", self.styles['SectionHeader']))
        
        summary_text = scan_data.get('summary', '')
        recommendations_section = self._extract_section(summary_text, 'RECOMMENDATIONS')
        
        if recommendations_section:
            recommendations = [line.strip() for line in recommendations_section.split('\n') if line.strip().startswith('•')]
            for i, rec in enumerate(recommendations, 1):
                clean_rec = rec.replace('•', '').strip()
                story.append(Paragraph(f"{i}. {clean_rec}", self.styles['ExecutiveSummary']))
            story.append(Spacer(1, 12))
        else:
            # Fallback recommendations
            fallback_recs = [
                "Implement continuous monitoring for the identified threat vectors",
                "Review and update security policies based on discovered vulnerabilities", 
                "Conduct security awareness training for staff on latest attack methods",
                "Enhance detection capabilities for the identified threat patterns"
            ]
            for i, rec in enumerate(fallback_recs, 1):
                story.append(Paragraph(f"{i}. {rec}", self.styles['ExecutiveSummary']))
    
    def _add_article_appendix(self, story: List, scan_data: Dict[str, Any]):
        """Add detailed article appendix"""
        story.append(Paragraph("Article Appendix", self.styles['SectionHeader']))
        story.append(Paragraph("Detailed information on all analyzed news articles:", self.styles['ExecutiveSummary']))
        story.append(Spacer(1, 12))
        
        discovered_links = scan_data.get('discovered_links', [])
        
        for i, article in enumerate(discovered_links, 1):
            # Article header
            title = article.get('title', 'Unknown Title')
            story.append(Paragraph(f"Article {i}: {title}", self.styles['SubsectionHeader']))
            
            # Article metadata table
            metadata = [
                ['Source:', article.get('source', 'Unknown')],
                ['URL:', article.get('url', 'N/A')],
                ['Date:', article.get('date', 'N/A')],
                ['Severity:', article.get('severity', 'Medium')]
            ]
            
            metadata_table = Table(metadata, colWidths=[1*inch, 4.5*inch])
            metadata_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2c3e50')),
            ]))
            
            story.append(metadata_table)
            story.append(Spacer(1, 6))
            
            # Article snippet
            snippet = article.get('snippet', 'No preview available')
            story.append(Paragraph(f"Preview: {snippet}", self.styles['ArticleContent']))
            story.append(Spacer(1, 12))
    
    def _add_footer_info(self, story: List, scan_data: Dict[str, Any]):
        """Add footer information and disclaimers"""
        story.append(Spacer(1, 20))
        
        # Disclaimer
        disclaimer = """
        <b>Disclaimer:</b> This report is generated through automated analysis of publicly available news sources. 
        The information provided should be used for situational awareness and should be verified through additional 
        sources before taking action. ThreatWatch is not responsible for the accuracy of third-party content or 
        any actions taken based on this report.
        """
        
        story.append(Paragraph("Report Information", self.styles['SubsectionHeader']))
        story.append(Paragraph(disclaimer, self.styles['Metadata']))
        
        # Generation info
        generation_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        footer_text = f"Generated by ThreatWatch Intelligence Platform on {generation_time}"
        story.append(Spacer(1, 12))
        story.append(Paragraph(footer_text, self.styles['Metadata']))
    
    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract a specific section from AI analysis text"""
        if not text or section_name not in text:
            return ""
        
        lines = text.split('\n')
        in_section = False
        section_content = []
        
        for line in lines:
            if section_name in line.upper():
                in_section = True
                continue
            elif in_section and any(header in line.upper() for header in ['RECOMMENDATIONS:', 'SECURITY IMPLICATIONS:', 'KEY THREATS:', 'EXECUTIVE SUMMARY:']):
                if line.upper().strip().endswith(':'):
                    break
            elif in_section:
                if line.strip():
                    section_content.append(line.strip())
        
        return '\n'.join(section_content)
    
    def cleanup_old_reports(self, max_age_hours: int = 48):
        """Clean up old cached reports"""
        now = datetime.now()
        
        for pdf_file in self.cache_dir.glob("*.pdf"):
            file_age = now - datetime.fromtimestamp(pdf_file.stat().st_mtime) 
            if file_age.total_seconds() > (max_age_hours * 3600):
                try:
                    pdf_file.unlink()
                    print(f"Cleaned up old report: {pdf_file.name}")
                except Exception as e:
                    print(f"Error cleaning up {pdf_file.name}: {e}")

    def get_public_filename(self, scan_data: Dict[str, Any]) -> str:
        """Generate user-friendly filename for downloads"""
        query = scan_data.get('query', 'unknown')
        safe_query = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).replace(' ', '_').strip()
        date_str = datetime.now().strftime('%Y-%m-%d')
        return f"ThreatWatch_Report_{safe_query}_{date_str}.pdf"