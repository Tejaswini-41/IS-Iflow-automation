from typing import Dict, List, Any
from pathlib import Path
import json


class HTMLGenerator:
    """Generates interactive HTML visualization"""

    def __init__(self):
        self.template_path = Path(__file__).parent.parent / 'templates' / 'visualization.html'

    def generate(self, flow_tree: List[Dict[str, Any]], raw_data: Dict[str, Any],
                 output_path: str, complexity_report: Dict[str, Any] = None):
        """Generate interactive HTML visualization"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if self.template_path.exists():
            with open(self.template_path, 'r', encoding='utf-8') as f:
                template = f.read()
        else:
            raise FileNotFoundError(f"Template not found: {self.template_path}")

        flow_data = json.dumps(flow_tree, indent=2, default=str)

        metadata = {
            'filename': raw_data.get('filename', 'Unknown'),
            'iflow_name': raw_data.get('iflow_name', raw_data.get('filename', '').replace('.iflw', '')),
            'iflow_description': raw_data.get('iflow_description', ''),
            'processes': len(raw_data.get('processes', [])),
            'participants': len(raw_data.get('participants', [])),
            'message_flows': len(raw_data.get('message_flows', [])),
            'iflow_settings': raw_data.get('iflow_settings', {}),
        }
        metadata_json = json.dumps(metadata, indent=2, default=str)

        stats_json = json.dumps(complexity_report or {}, indent=2, default=str)
        payload_json = json.dumps(
            {
                'metadata': metadata,
                'complexity': complexity_report or {},
                'flow_tree': flow_tree,
                'processes': raw_data.get('processes', []),
            },
            indent=2,
            default=str,
        )
        safe_payload_json = payload_json.replace('</', '<\\/')

        html_content = template.replace('{{FLOW_DATA}}', flow_data)
        html_content = html_content.replace('{{METADATA}}', metadata_json)
        html_content = html_content.replace('{{STATS}}', stats_json)

        runtime_data_script = (
            "<script id=\"iflow-analyzer-data\">"
            f"window.IFLOW_ANALYZER_DATA = {safe_payload_json};"
            "</script>"
        )
        if '</body>' in html_content:
            html_content = html_content.replace('</body>', f'{runtime_data_script}\n</body>', 1)
        else:
            html_content += f'\n{runtime_data_script}\n'

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)