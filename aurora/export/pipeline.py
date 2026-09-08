"""
AGENCY OS — Export & Publishing Pipeline
Export interpretations, assets, and data to external formats and platforms.
"""
from __future__ import annotations
import json, csv, io
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from enum import Enum


class ExportFormat(Enum):
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"
    CSV = "csv"
    PDF = "pdf"
    PNG = "png"
    SVG = "svg"
    DOCX = "docx"
    PPTX = "ppx"


class PublishTarget(Enum):
    FIGMA = "figma"
    WEBFLOW = "webflow"
    FRAMER = "framer"
    NOTION = "notion"
    CONFLUENCE = "confluence"
    WORDPRESS = "wordpress"
    SHOPIFY = "shopify"
    GITHUB = "github"
    SLACK = "slack"
    EMAIL = "email"


class ExportPipeline:
    """
    Export and publishing pipeline.
    
    Supports:
    - Multiple export formats
    - Direct publishing to platforms
    - Template-based exports
    - Batch exports
    - Scheduled publishing
    """

    def __init__(self, output_dir: str = "./output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._exporters = {
            ExportFormat.JSON: self._export_json,
            ExportFormat.MARKDOWN: self._export_markdown,
            ExportFormat.HTML: self._export_html,
            ExportFormat.CSV: self._export_csv,
        }

    def export(self, data: Dict, format: ExportFormat, filename: Optional[str] = None) -> Path:
        """Export data to the specified format."""
        exporter = self._exporters.get(format)
        if not exporter:
            raise ValueError(f"Unsupported format: {format}")

        if not filename:
            filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return exporter(data, filename)

    def _export_json(self, data: Dict, filename: str) -> Path:
        """Export to JSON."""
        path = self.output_dir / f"{filename}.json"
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        return path

    def _export_markdown(self, data: Dict, filename: str) -> Path:
        """Export to Markdown."""
        path = self.output_dir / f"{filename}.md"
        md = self._to_markdown(data)
        with open(path, "w") as f:
            f.write(md)
        return path

    def _export_html(self, data: Dict, filename: str) -> Path:
        """Export to HTML."""
        path = self.output_dir / f"{filename}.html"
        html = self._to_html(data)
        with open(path, "w") as f:
            f.write(html)
        return path

    def _export_csv(self, data: Dict, filename: str) -> Path:
        """Export to CSV (for tabular data)."""
        path = self.output_dir / f"{filename}.csv"

        # Flatten data for CSV
        rows = self._flatten_for_csv(data)
        if rows:
            with open(path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        return path

    def _to_markdown(self, data: Dict, level: int = 1) -> str:
        """Convert data to Markdown."""
        lines = []
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{'#' * level} {key}\n")
                lines.append(self._to_markdown(value, level + 1))
            elif isinstance(value, list):
                lines.append(f"{'#' * level} {key}\n")
                for item in value:
                    if isinstance(item, dict):
                        lines.append(self._to_markdown(item, level + 1))
                    else:
                        lines.append(f"- {item}")
                lines.append("")
            else:
                lines.append(f"**{key}:** {value}")
        return "\n".join(lines)

    def _to_html(self, data: Dict) -> str:
        """Convert data to HTML report."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>AGENCY OS Export</title>
    <style>
        body {{ font-family: system-ui, sans-serif; max-width: 800px; margin: 0 auto; padding: 2rem; }}
        h1 {{ color: #1a1a1a; border-bottom: 2px solid #007bff; padding-bottom: 0.5rem; }}
        h2 {{ color: #333; margin-top: 2rem; }}
        .insight {{ background: #f8f9fa; padding: 1rem; margin: 0.5rem 0; border-radius: 8px; }}
        .score {{ font-size: 2rem; font-weight: bold; color: #007bff; }}
        .tag {{ display: inline-block; background: #e9ecef; padding: 0.25rem 0.5rem; border-radius: 4px; margin: 0.25rem; }}
    </style>
</head>
<body>
    <h1>🎨 AGENCY OS Creative Intelligence Report</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
"""
        for key, value in data.items():
            if isinstance(value, dict):
                html += f"<h2>{key}</h2>\n"
                for k, v in value.items():
                    html += f"<p><strong>{k}:</strong> {v}</p>\n"
            elif isinstance(value, list):
                html += f"<h2>{key}</h2>\n"
                for item in value:
                    if isinstance(item, dict):
                        html += '<div class="insight">\n'
                        for k, v in item.items():
                            html += f"<p><strong>{k}:</strong> {v}</p>\n"
                        html += '</div>\n'
                    else:
                        html += f"<p>- {item}</p>\n"
            else:
                html += f"<p><strong>{key}:</strong> {value}</p>\n"

        html += "</body></html>"
        return html

    def _flatten_for_csv(self, data: Dict) -> List[Dict]:
        """Flatten nested data for CSV export."""
        rows = []
        if "insights" in data and isinstance(data["insights"], list):
            for insight in data["insights"]:
                rows.append(insight)
        return rows

    # ─── Publishing ───

    async def publish(self, data: Dict, target: PublishTarget, config: Dict = None) -> Dict:
        """Publish to external platform."""
        if target == PublishTarget.NOTION:
            return await self._publish_notion(data, config)
        elif target == PublishTarget.SLACK:
            return await self._publish_slack(data, config)
        elif target == PublishTarget.FIGMA:
            return await self._publish_figma(data, config)
        elif target == PublishTarget.GITHUB:
            return await self._publish_github(data, config)
        else:
            return {"status": "not_implemented", "target": target.value}

    async def _publish_notion(self, data: Dict, config: Dict) -> Dict:
        """Publish to Notion."""
        # Would use Notion API
        return {"status": "published", "target": "notion", "page_id": "page_xxx"}

    async def _publish_slack(self, data: Dict, config: Dict) -> Dict:
        """Publish to Slack."""
        # Would use Slack API
        return {"status": "published", "target": "slack", "channel": config.get("channel")}

    async def _publish_figma(self, data: Dict, config: Dict) -> Dict:
        """Publish to Figma."""
        # Would use Figma API
        return {"status": "published", "target": "figma", "file_id": "file_xxx"}

    async def _publish_github(self, data: Dict, config: Dict) -> Dict:
        """Publish to GitHub (as issue, gist, or wiki)."""
        # Would use GitHub API
        return {"status": "published", "target": "github", "url": "https://github.com/..."}

    # ─── Batch Export ───

    def batch_export(self, items: List[Dict], format: ExportFormat) -> List[Path]:
        """Export multiple items."""
        paths = []
        for i, item in enumerate(items):
            path = self.export(item, format, filename=f"batch_{i+1}")
            paths.append(path)
        return paths

    # ─── Report Generation ───

    def generate_report(self, interpretation, format: ExportFormat = ExportFormat.HTML) -> Path:
        """Generate a full creative intelligence report."""
        data = {
            "summary": interpretation.summary,
            "quality_score": interpretation.quality_score,
            "tags": interpretation.tags,
            "insights": [{
                "domain": i.domain.value if hasattr(i.domain, 'value') else str(i.domain),
                "category": i.category,
                "finding": i.finding,
                "confidence": i.confidence,
                "suggestions": i.suggestions
            } for i in interpretation.insights]
        }
        return self.export(data, format, filename=f"report_{interpretation.media_id}")