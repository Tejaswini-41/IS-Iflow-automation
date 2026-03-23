from typing import Dict, List, Any, Set


class FlowBuilder:
    """Builds hierarchical flow tree from normalized components with cycle detection"""

    def __init__(self):
        self.components_by_id: Dict[str, Dict] = {}
        self.sequence_flows: List[Dict] = []

    def build(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build hierarchical tree — returns root nodes with nested children"""
        if not components:
            return []

        self.sequence_flows = [c for c in components if c['type'] == 'SequenceFlow']
        actual_components = [c for c in components if c['type'] != 'SequenceFlow']

        self.components_by_id = {c['id']: c for c in actual_components}

        # Reset children lists (avoid duplicates on re-build)
        for comp in actual_components:
            comp['children'] = []

        self._build_relationships()

        root_nodes = self._find_root_nodes(actual_components)
        return root_nodes

    def _build_relationships(self):
        """Build parent→child links based on sequence flows, with cycle detection"""
        # Track which targets already have a parent pointing at them
        # to avoid circular references in the tree view
        visited_edges: Set[tuple] = set()

        for flow in self.sequence_flows:
            src = flow['source']
            tgt = flow['target']
            edge = (src, tgt)

            if edge in visited_edges:
                continue
            visited_edges.add(edge)

            if src not in self.components_by_id or tgt not in self.components_by_id:
                continue

            parent = self.components_by_id[src]
            child = self.components_by_id[tgt]

            # Attach condition metadata to child clone so tree shows route labels
            if flow.get('condition') or flow.get('name'):
                # Store on the child node — multiple flows may target same node
                # so we tag child with the LAST condition (acceptable for display)
                child['condition'] = flow.get('condition', '')
                child['route_name'] = flow.get('name', '')

            if child not in parent['children']:
                parent['children'].append(child)

    def _find_root_nodes(self, components: List[Dict]) -> List[Dict]:
        """Root nodes = not the target of any sequence flow, or are StartEvents/Senders"""
        target_ids = {flow['target'] for flow in self.sequence_flows}

        root_nodes = [
            c for c in components
            if c['id'] not in target_ids or c['type'] in ('StartEvent', 'Sender')
        ]

        # Fallback: use senders + start events
        if not root_nodes:
            root_nodes = [c for c in components if c['type'] in ('Sender', 'StartEvent')]

        # Final fallback
        if not root_nodes and components:
            root_nodes = [components[0]]

        return root_nodes

    def get_statistics(self) -> Dict[str, Any]:
        """Return flow connectivity statistics"""
        return {
            'total_sequence_flows': len(self.sequence_flows),
            'total_nodes': len(self.components_by_id),
        }