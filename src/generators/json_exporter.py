import json
from typing import Dict, List, Any
from pathlib import Path


class JSONExporter:
    """Exports flow tree to JSON format"""
    
    def __init__(self):
        """Initialize the JSON exporter"""
        pass
    
    def export(self, flow_tree: List[Dict[str, Any]], output_path: str):
        """
        Export flow tree to JSON file
        
        Args:
            flow_tree: Hierarchical flow tree structure
            output_path: Path to output JSON file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to JSON-serializable format
        json_data = {
            'version': '1.0',
            'flow_tree': self._serialize_tree(flow_tree)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    def _serialize_tree(self, tree: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Recursively serialize tree to JSON-safe format"""
        serialized = []
        
        for node in tree:
            serialized_node = {
                'id': node.get('id', ''),
                'name': node.get('name', ''),
                'type': node.get('type', ''),
                'summary': node.get('summary', ''),
                'details': node.get('details', {}),
                'condition': node.get('condition', ''),
                'route_name': node.get('route_name', ''),
                'children': self._serialize_tree(node.get('children', []))
            }
            serialized.append(serialized_node)
        
        return serialized