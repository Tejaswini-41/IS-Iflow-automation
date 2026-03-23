from typing import Dict, List, Any
import json
from pathlib import Path
from datetime import datetime


class JSONExporter:
    """Exports flow tree and analysis metrics as JSON"""

    def export(self, flow_tree: List[Dict[str, Any]], output_path: str,
               raw_data: Dict[str, Any] = None, complexity_report: Dict[str, Any] = None):
        """Export full analysis to JSON"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'filename': raw_data.get('filename', '') if raw_data else '',
                'iflow_name': raw_data.get('iflow_name', '') if raw_data else '',
                'iflow_description': raw_data.get('iflow_description', '') if raw_data else '',
                'process_count': len(raw_data.get('processes', [])) if raw_data else 0,
                'participant_count': len(raw_data.get('participants', [])) if raw_data else 0,
                'message_flow_count': len(raw_data.get('message_flows', [])) if raw_data else 0,
            },
            'complexity': complexity_report or {},
            'flow_tree': flow_tree,
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, default=str)