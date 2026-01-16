from typing import Dict, List, Any


class FlowBuilder:
    """Builds hierarchical flow tree from normalized components"""
    
    def __init__(self):
        """Initialize the flow builder"""
        self.components_by_id = {}
        self.sequence_flows = []
    
    def build(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build hierarchical tree structure from flat component list
        Returns list of root nodes with nested children
        """
        if not components:
            return []
        
        # Separate sequence flows from components
        self.sequence_flows = [c for c in components if c['type'] == 'SequenceFlow']
        actual_components = [c for c in components if c['type'] != 'SequenceFlow']
        
        # Index components by ID
        self.components_by_id = {c['id']: c for c in actual_components}
        
        # Build parent-child relationships
        self._build_relationships(actual_components)
        
        # Find root nodes (components with no incoming flows)
        root_nodes = self._find_root_nodes(actual_components)
        
        return root_nodes
    
    def _build_relationships(self, components: List[Dict[str, Any]]):
        """Build parent-child relationships based on sequence flows"""
        for flow in self.sequence_flows:
            source_id = flow['source']
            target_id = flow['target']
            
            if source_id in self.components_by_id and target_id in self.components_by_id:
                parent = self.components_by_id[source_id]
                child = self.components_by_id[target_id]
                
                # Add flow information to child
                if flow['condition']:
                    child['condition'] = flow['condition']
                    child['route_name'] = flow['name']
                
                # Add child to parent's children list
                if child not in parent['children']:
                    parent['children'].append(child)
    
    def _find_root_nodes(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find components that have no incoming flows (root nodes)"""
        # Get all target IDs (components that are targets of flows)
        target_ids = set(flow['target'] for flow in self.sequence_flows)
        
        # Root nodes are components not in target_ids, or StartEvent types
        root_nodes = []
        for component in components:
            if component['id'] not in target_ids or component['type'] == 'StartEvent':
                root_nodes.append(component)
        
        # If no roots found, return all Sender participants and StartEvents
        if not root_nodes:
            root_nodes = [c for c in components if c['type'] in ['Sender', 'StartEvent']]
        
        # If still no roots, return first component
        if not root_nodes and components:
            root_nodes = [components[0]]
        
        return root_nodes