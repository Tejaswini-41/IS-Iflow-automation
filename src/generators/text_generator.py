from typing import Dict, List, Any
from pathlib import Path


class TextGenerator:
    """Generates text-based tree visualization"""
    
    def __init__(self):
        """Initialize the text generator"""
        pass
    
    def generate(self, flow_tree: List[Dict[str, Any]], output_path: str):
        """
        Generate text tree visualization and save to file
        
        Args:
            flow_tree: Hierarchical flow tree structure
            output_path: Path to output text file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        lines = []
        lines.append("=" * 80)
        lines.append("SAP CPI iFlow - Flow Tree Visualization")
        lines.append("=" * 80)
        lines.append("")
        
        self._print_tree(flow_tree, lines, "")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    def _print_tree(self, tree: List[Dict[str, Any]], output: List[str], indent: str):
        """Recursively print tree structure"""
        for i, node in enumerate(tree):
            is_last = i == len(tree) - 1
            prefix = "└── " if is_last else "├── "
            
            # Build node display
            node_display = f"{node['type']}: {node['name']}"
            if node.get('route_name'):
                node_display += f" [{node['route_name']}]"
            
            output.append(f"{indent}{prefix}{node_display}")
            
            # Add summary
            if node.get('summary'):
                summary_indent = indent + ("    " if is_last else "│   ")
                output.append(f"{summary_indent}📝 {node['summary']}")
            
            # Add condition for router branches
            if node.get('condition'):
                condition_indent = indent + ("    " if is_last else "│   ")
                output.append(f"{condition_indent}🔀 Condition: {node['condition']}")
            
            # Add details
            details = node.get('details', {})
            if details:
                detail_indent = indent + ("    " if is_last else "│   ")
                
                # Show key details based on type
                if node['type'] == 'ContentModifier':
                    if details.get('propertiesSet'):
                        output.append(f"{detail_indent}   Properties: {', '.join(details['propertiesSet'][:3])}")
                    if details.get('headersSet'):
                        output.append(f"{detail_indent}   Headers: {', '.join(details['headersSet'][:3])}")
                
                elif node['type'] == 'GroovyScript':
                    if details.get('propertiesWritten'):
                        output.append(f"{detail_indent}   Writes: {', '.join(details['propertiesWritten'][:3])}")
                    if details.get('propertiesRead'):
                        output.append(f"{detail_indent}   Reads: {', '.join(details['propertiesRead'][:3])}")
                
                elif node['type'] == 'Router':
                    conditions = details.get('conditions', [])
                    if conditions:
                        output.append(f"{detail_indent}   Routes: {len(conditions)}")
                
                elif node['type'] == 'RequestReply':
                    if details.get('targetSystem'):
                        output.append(f"{detail_indent}   Target: {details['targetSystem']}")
            
            # Print children recursively
            if node.get('children'):
                child_indent = indent + ("    " if is_last else "│   ")
                self._print_tree(node['children'], output, child_indent)