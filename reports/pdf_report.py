"""
PDF Audit Report Generator Module
Compiles an academic/enterprise-grade PDF report using ReportLab.
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether

class PDFReportGenerator:
    """Generates comprehensive PDF reports for the Data-Quality Analyzer."""

    @staticmethod
    def generate_report(quality_summary, model_comparison, consolidated_df, top_n=15):
        """
        Builds PDF binary stream.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0F172A"),
            spaceAfter=6
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#475569"),
            spaceAfter=14
        )
        h2_style = ParagraphStyle(
            "SectionH2",
            parent=styles["Heading2"],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#1E3A8A"),
            spaceBefore=12,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            "BodyDark",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#1E293B")
        )
        table_text = ParagraphStyle(
            "TableTxt",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#0F172A")
        )
        disclaimer_style = ParagraphStyle(
            "Disclaimer",
            parent=styles["Italic"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#B91C1C"),
            spaceBefore=10
        )

        elements = []

        # Header Title
        elements.append(Paragraph("AI-Based Database Data-Quality Audit Report", title_style))
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elements.append(Paragraph(
            f"Generated: <b>{now_str}</b> | Environment: <b>Hybrid Oracle SQL/PLSQL + Scikit-Learn ML</b> | Target: <b>College Student DB</b>",
            subtitle_style
        ))
        elements.append(Spacer(1, 8))

        # 1. Executive Summary Table
        elements.append(Paragraph("1. Executive Summary & Quality Score", h2_style))
        score = quality_summary.get("score", 0.0)
        grade = quality_summary.get("grade", "N/A")
        total_rec = quality_summary.get("total_records", 0)
        dedup_issues = quality_summary.get("deduplicated_issues", 0)
        sevs = quality_summary.get("severity_counts", {})

        summary_data = [
            [Paragraph("<b>Metric</b>", table_text), Paragraph("<b>Value</b>", table_text),
             Paragraph("<b>Metric</b>", table_text), Paragraph("<b>Value</b>", table_text)],
            [Paragraph("Overall Quality Score", table_text), Paragraph(f"<b>{score} / 100</b>", table_text),
             Paragraph("Academic Rating Grade", table_text), Paragraph(f"<b>{grade}</b>", table_text)],
            [Paragraph("Total Records Analyzed", table_text), Paragraph(str(total_rec), table_text),
             Paragraph("Deduplicated Issue Flags", table_text), Paragraph(str(dedup_issues), table_text)],
            [Paragraph("High Severity (Critical)", table_text), Paragraph(str(sevs.get("HIGH", 0)), table_text),
             Paragraph("Medium Severity (Anomalous)", table_text), Paragraph(str(sevs.get("MEDIUM", 0)), table_text)],
            [Paragraph("Low Severity (Formatting)", table_text), Paragraph(str(sevs.get("LOW", 0)), table_text),
             Paragraph("Status", table_text), Paragraph("Audit Complete", table_text)]
        ]

        t_summary = Table(summary_data, colWidths=[140, 130, 140, 130])
        t_summary.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(t_summary)
        elements.append(Spacer(1, 10))

        # 2. Quality Dimensions
        elements.append(Paragraph("2. Quality Dimension Breakdown", h2_style))
        dims = quality_summary.get("dimension_scores", {})
        dim_data = [
            [Paragraph("<b>Dimension</b>", table_text), Paragraph("<b>Compliance Score</b>", table_text), Paragraph("<b>Target Threshold</b>", table_text)],
            [Paragraph("Completeness (Null checks)", table_text), Paragraph(f"{dims.get('Completeness', 100.0)}%", table_text), Paragraph("≥ 98.0%", table_text)],
            [Paragraph("Uniqueness (Duplicate constraints)", table_text), Paragraph(f"{dims.get('Uniqueness', 100.0)}%", table_text), Paragraph("≥ 99.0%", table_text)],
            [Paragraph("Validity (Range & Domain checks)", table_text), Paragraph(f"{dims.get('Validity', 100.0)}%", table_text), Paragraph("≥ 95.0%", table_text)],
            [Paragraph("Consistency (Cross-field & ML patterns)", table_text), Paragraph(f"{dims.get('Consistency', 100.0)}%", table_text), Paragraph("≥ 90.0%", table_text)],
        ]
        t_dim = Table(dim_data, colWidths=[200, 170, 170])
        t_dim.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#EEF2F6")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(t_dim)
        elements.append(Spacer(1, 10))

        # 3. Model Comparison
        elements.append(Paragraph("3. Unsupervised Machine Learning Comparative Analysis", h2_style))
        mc = model_comparison or {}
        ml_comp_data = [
            [Paragraph("<b>Model / Ensemble Metric</b>", table_text), Paragraph("<b>Observed Count</b>", table_text), Paragraph("<b>Description</b>", table_text)],
            [Paragraph("Isolation Forest Flags", table_text), Paragraph(str(mc.get("isolation_forest_total", 0)), table_text), Paragraph("Tree-partitioning multivariate outliers", table_text)],
            [Paragraph("DBSCAN Noise Records", table_text), Paragraph(str(mc.get("dbscan_total", 0)), table_text), Paragraph("Density-based noise cluster (-1)", table_text)],
            [Paragraph("Coincident Flags (Both Models)", table_text), Paragraph(str(mc.get("both_count", 0)), table_text), Paragraph("Confirmed outliers by both unsupervised engines", table_text)],
            [Paragraph("Jaccard Similarity Index", table_text), Paragraph(str(mc.get("jaccard_similarity", 0.0)), table_text), Paragraph("Intersection over union between models", table_text)],
        ]
        t_ml = Table(ml_comp_data, colWidths=[180, 100, 260])
        t_ml.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#EEF2F6")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(t_ml)
        elements.append(Spacer(1, 10))

        # 4. Top Suspicious Records
        elements.append(Paragraph(f"4. Key Suspicious Records Sample (Top {top_n})", h2_style))
        if consolidated_df is not None and not consolidated_df.empty:
            rec_headers = [
                Paragraph("<b>Rec ID</b>", table_text),
                Paragraph("<b>Table</b>", table_text),
                Paragraph("<b>Engine</b>", table_text),
                Paragraph("<b>Sev</b>", table_text),
                Paragraph("<b>Reason / Evidence Explanation</b>", table_text)
            ]
            rec_rows = [rec_headers]
            sample = consolidated_df.head(top_n)
            for _, r in sample.iterrows():
                rec_rows.append([
                    Paragraph(str(r.get("RECORD_ID", "")), table_text),
                    Paragraph(str(r.get("TABLE_NAME", "")), table_text),
                    Paragraph(str(r.get("DETECTION_METHOD", "")), table_text),
                    Paragraph(str(r.get("SEVERITY", "")), table_text),
                    Paragraph(str(r.get("EXPLANATION", ""))[:140], table_text)
                ])

            t_recs = Table(rec_rows, colWidths=[65, 65, 110, 45, 255])
            t_recs.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('PADDING', (0, 0), (-1, -1), 3),
            ]))
            elements.append(t_recs)
        else:
            elements.append(Paragraph("No records flagged as suspicious.", body_style))

        # Governance Note
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(
            "<b>Data Governance Notice:</b> A machine learning anomaly is a statistical outlier warranting review, "
            "not automatically an invalid database entry. Flagged records should undergo human verification or domain review "
            "prior to applying remedial transformations or removal.",
            disclaimer_style
        ))

        # Build document
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

