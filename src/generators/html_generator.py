from typing import Dict, List, Any
from pathlib import Path
import json


class HTMLGenerator:
    """Generates interactive HTML visualization"""
    
    def __init__(self):
        """Initialize the HTML generator"""
        self.template_path = Path(__file__).parent.parent / 'templates' / 'visualization.html'
    
    def generate(self, flow_tree: List[Dict[str, Any]], raw_data: Dict[str, Any], output_path: str):
        """
        Generate interactive HTML visualization
        
        Args:
            flow_tree: Hierarchical flow tree structure
            raw_data: Original parsed data
            output_path: Path to output HTML file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load template
        if self.template_path.exists():
            with open(self.template_path, 'r', encoding='utf-8') as f:
                template = f.read()
        else:
            # Use embedded template if file not found
            template = self._get_default_template()
        
        # Prepare data for JavaScript
        flow_data = json.dumps(flow_tree, indent=2)
        metadata = {
            'filename': raw_data.get('filename', 'Unknown'),
            'processes': len(raw_data.get('processes', [])),
            'participants': len(raw_data.get('participants', []))
        }
        metadata_json = json.dumps(metadata, indent=2)
        
        # Replace placeholders
        html_content = template.replace('{{FLOW_DATA}}', flow_data)
        html_content = html_content.replace('{{METADATA}}', metadata_json)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _get_default_template(self) -> str:
        """Return embedded HTML template"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SAP CPI iFlow Visualization</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; height: 100vh; background: #f5f5f5; }
        #sidebar { width: 400px; background: white; border-right: 1px solid #ddd; overflow-y: auto; }
        #content { flex: 1; padding: 20px; overflow-y: auto; }
        #header { background: #0078d4; color: white; padding: 20px; }
        #header h1 { font-size: 24px; margin-bottom: 10px; }
        #header p { font-size: 14px; opacity: 0.9; }
        #tree { padding: 20px; }
        .tree-node { margin-left: 20px; margin-bottom: 5px; cursor: pointer; user-select: none; }
        .tree-node:hover { background: #f0f0f0; }
        .tree-node.selected { background: #e3f2fd; }
        .node-icon { display: inline-block; width: 20px; }
        .node-label { font-size: 14px; }
        .node-type { color: #666; font-size: 12px; margin-left: 5px; }
        #details { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        #details h2 { color: #0078d4; margin-bottom: 15px; }
        #details .section { margin-bottom: 20px; }
        #details .section h3 { font-size: 16px; color: #333; margin-bottom: 10px; }
        #details .section p { color: #666; line-height: 1.6; }
        #details .detail-item { background: #f9f9f9; padding: 10px; margin: 5px 0; border-left: 3px solid #0078d4; }
        #details .detail-label { font-weight: bold; color: #333; }
        #details .detail-value { color: #666; margin-top: 5px; }
        .empty-state { text-align: center; padding: 40px; color: #999; }
    </style>
</head>
<body>
    <div id="sidebar">
        <div id="header">
            <h1>🔄 SAP CPI iFlow</h1>
            <p id="metadata"></p>
        </div>
        <div id="tree"></div>
    </div>
    <div id="content">
        <div id="details">
            <div class="empty-state">
                <h2>👈 Select a node from the tree</h2>
                <p>Click on any node in the left panel to view its details</p>
            </div>
        </div>
    </div>

    <script>
        const flowData = {{FLOW_DATA}};
        const metadata = {{METADATA}};
        
        // Display metadata
        document.getElementById('metadata').textContent = 
            `File: ${metadata.filename} | Processes: ${metadata.processes} | Participants: ${metadata.participants}`;
        
        // Render tree
        function renderTree(nodes, container, level = 0) {
            nodes.forEach(node => {
                const div = document.createElement('div');
                div.className = 'tree-node';
                div.style.marginLeft = (level * 20) + 'px';
                div.innerHTML = `
                    <span class="node-icon">${getIcon(node.type)}</span>
                    <span class="node-label">${node.name}</span>
                    <span class="node-type">(${node.type})</span>
                `;
                div.onclick = (e) => {
                    e.stopPropagation();
                    document.querySelectorAll('.tree-node').forEach(n => n.classList.remove('selected'));
                    div.classList.add('selected');
                    showDetails(node);
                };
                container.appendChild(div);
                
                if (node.children && node.children.length > 0) {
                    renderTree(node.children, container, level + 1);
                }
            });
        }
        
        function getIcon(type) {
            const icons = {
                'Sender': '📥',
                'Receiver': '📤',
                'StartEvent': '▶️',
                'EndEvent': '⏹️',
                'ContentModifier': '✏️',
                'GroovyScript': '📜',
                'Router': '🔀',
                'RequestReply': '🔄',
                'CallActivity': '📞',
                'ServiceTask': '⚙️'
            };
            return icons[type] || '📦';
        }
        
        function showDetails(node) {
            const detailsDiv = document.getElementById('details');
            let html = `<h2>${getIcon(node.type)} ${node.name}</h2>`;
            html += `<div class="section"><p><strong>Type:</strong> ${node.type}</p></div>`;
            
            if (node.summary) {
                html += `<div class="section"><h3>Summary</h3><p>${node.summary}</p></div>`;
            }
            
            if (node.details && Object.keys(node.details).length > 0) {
                html += `<div class="section"><h3>Details</h3>`;
                for (const [key, value] of Object.entries(node.details)) {
                    if (Array.isArray(value) && value.length > 0) {
                        html += `<div class="detail-item">
                            <div class="detail-label">${formatLabel(key)}</div>
                            <div class="detail-value">${value.join(', ')}</div>
                        </div>`;
                    } else if (typeof value === 'object' && value !== null) {
                        html += `<div class="detail-item">
                            <div class="detail-label">${formatLabel(key)}</div>
                            <div class="detail-value">${JSON.stringify(value, null, 2)}</div>
                        </div>`;
                    } else if (value && value !== '' && value !== false) {
                        html += `<div class="detail-item">
                            <div class="detail-label">${formatLabel(key)}</div>
                            <div class="detail-value">${value}</div>
                        </div>`;
                    }
                }
                html += `</div>`;
            }
            
            detailsDiv.innerHTML = html;
        }
        
        function formatLabel(str) {
            return str.replace(/([A-Z])/g, ' $1').replace(/^./, s => s.toUpperCase());
        }
        
        renderTree(flowData, document.getElementById('tree'));
    </script>
</body>
</html>'''