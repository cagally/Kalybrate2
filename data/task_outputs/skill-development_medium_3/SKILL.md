---
name: Marketing Report Generator
description: This skill should be used when the user asks to "create a marketing report", "generate marketing analytics", "build a marketing dashboard", "create quarterly marketing insights", or needs help with visualizing marketing performance data.
version: 1.0.0
---

# Marketing Report Generation Skill

## Overview

This skill provides comprehensive guidance for creating professional, data-driven marketing reports that align with brand standards and communicate key performance insights effectively.

## Purpose

Generate high-quality marketing reports that:
- Visualize key performance metrics
- Align with brand design guidelines
- Provide actionable insights
- Support strategic decision-making

## When to Use

Use this skill when you need to:
- Create quarterly marketing performance reports
- Generate executive-level marketing dashboards
- Analyze campaign effectiveness
- Visualize marketing channel performance
- Prepare investor or board-level marketing presentations

## Report Generation Workflow

### 1. Data Collection and Preparation

#### Required Data Sources
- Google Analytics
- Social Media Insights
- Ad Platform Performance Metrics
- CRM Sales Data
- Email Marketing Performance

#### Recommended Data Preparation Steps
- Normalize data across platforms
- Remove outliers
- Validate data integrity
- Standardize date ranges

### 2. Chart and Visualization Guidelines

#### Visualization Principles
- Use consistent color palette from brand assets
- Maintain clean, minimalist design
- Prioritize clarity over complexity
- Use appropriate chart types for data

##### Recommended Chart Types
- Line Charts: Trend analysis
- Bar Charts: Comparative performance
- Pie Charts: Composition and distribution
- Scatter Plots: Correlation analysis

### 3. Brand Asset Integration

#### Brand Guidelines
Refer to `references/brand-style-guide.md` for:
- Color usage
- Typography
- Logo placement
- Spacing and alignment

#### Assets Location
- Logo: `assets/logo.png`
- Color Palette: Defined in brand style guide
- Typography: Corporate font family

### 4. Reporting Sections

1. **Executive Summary**
   - High-level performance overview
   - Key achievements and challenges
   - Actionable recommendations

2. **Channel Performance**
   - Detailed metrics for each marketing channel
   - Comparative analysis
   - ROI calculations

3. **Campaign Effectiveness**
   - Individual campaign performance
   - A/B testing insights
   - Cost per acquisition (CPA)

4. **Audience Insights**
   - Demographic analysis
   - Engagement metrics
   - Customer journey mapping

### 5. Report Formatting

- Use corporate PowerPoint template (`assets/marketing-report-template.pptx`)
- Export to PDF for distribution
- Ensure accessibility standards are met

## Tools and Scripts

### Bundled Resources
- **`scripts/data_normalize.py`**: Standardize marketing data
- **`scripts/chart_generator.py`**: Create brand-compliant visualizations
- **`scripts/report_compiler.py`**: Assemble final report document

## Additional Resources

### Reference Files
- **`references/brand-style-guide.md`**: Comprehensive brand design guidelines
- **`references/marketing-kpi-definitions.md`**: Detailed KPI explanations
- **`references/data-source-integrations.md`**: Guide for connecting data sources

### Example Reports
- **`examples/q1_marketing_report.pdf`**: Sample quarterly report
- **`examples/campaign_performance.pptx`**: Campaign analysis template

## Best Practices

1. Always validate data sources
2. Maintain consistent formatting
3. Focus on actionable insights
4. Use clear, concise language
5. Align visuals with brand identity

## Troubleshooting

### Common Challenges
- Inconsistent data formats
- Missing tracking parameters
- Complex visualization requirements

### Recommended Solutions
- Use `scripts/data_normalize.py` for data cleaning
- Cross-reference `references/data-source-integrations.md`
- Consult brand guidelines for design constraints

## Version History

- **1.0.0**: Initial release
  - Basic report generation workflow
  - Brand asset integration
  - Data visualization guidelines

## Contact and Support

For advanced reporting needs or customization, contact the Marketing Analytics team.
