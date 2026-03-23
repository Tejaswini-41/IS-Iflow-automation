from typing import Dict, List, Any
import re


class ComplexityAnalyzer:
    """Analyzes overall iFlow complexity and detects anti-patterns"""

    COMPLEXITY_THRESHOLDS = {
        'low': 20,
        'medium': 50,
        'high': 100
    }

    def analyze(self, components: List[Dict[str, Any]], processes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute flow-level complexity metrics and anti-pattern warnings"""

        # Component type counts
        type_counts: Dict[str, int] = {}
        script_complexities = []
        adapter_types = set()
        state = {
            'total_conditions': 0,
            'max_depth': 0,
            'script_count': 0,
            'has_error_handler': False,
        }

        def _walk(nodes, depth=0):
            if depth > state['max_depth']:
                state['max_depth'] = depth
            for node in nodes:
                t = node.get('type', 'Unknown')
                type_counts[t] = type_counts.get(t, 0) + 1

                if t == 'GroovyScript':
                    state['script_count'] += 1
                    cx = node.get('details', {}).get('complexityScore', 0)
                    if cx:
                        script_complexities.append(cx)

                if t == 'Router':
                    conds = node.get('details', {}).get('conditions', [])
                    state['total_conditions'] += len(conds)

                if t in ('Sender', 'Receiver', 'RequestReply'):
                    at = node.get('details', {}).get('adapterType', '')
                    if at:
                        adapter_types.add(at)

                if t == 'EndEvent':
                    defs = node.get('details', {}).get('eventDefinitions', [])
                    if 'error' in [d.lower() for d in defs]:
                        state['has_error_handler'] = True

                _walk(node.get('children', []), depth + 1)

        _walk(components)

        total_components = sum(type_counts.values())
        total_processes = len(processes)
        script_count = state['script_count']
        total_conditions = state['total_conditions']
        max_depth = state['max_depth']
        has_error_handler = state['has_error_handler']
        avg_script_complexity = (sum(script_complexities) / len(script_complexities)) if script_complexities else 0

        # Compute overall score (0-100)
        score = 0
        score += min(total_components * 0.5, 30)       # component volume
        score += min(script_count * 2, 20)              # script density
        score += min(total_conditions * 1.5, 20)        # branching
        score += min(max_depth * 2, 15)                 # depth
        score += min(avg_script_complexity * 0.1, 15)   # script complexity
        score = int(min(score, 100))

        if score < 30:
            complexity_label = 'Low'
            complexity_color = 'green'
        elif score < 65:
            complexity_label = 'Medium'
            complexity_color = 'orange'
        else:
            complexity_label = 'High'
            complexity_color = 'red'

        warnings = self._detect_anti_patterns(
            type_counts, total_components, script_count,
            total_conditions, has_error_handler, max_depth
        )

        recommendations = self._generate_recommendations(warnings, type_counts, adapter_types)

        return {
            'score': score,
            'label': complexity_label,
            'color': complexity_color,
            'total_components': total_components,
            'total_processes': total_processes,
            'script_count': script_count,
            'router_count': type_counts.get('Router', 0),
            'content_modifier_count': type_counts.get('ContentModifier', 0),
            'request_reply_count': type_counts.get('RequestReply', 0),
            'total_conditions': total_conditions,
            'max_depth': max_depth,
            'adapter_types': sorted(adapter_types),
            'type_counts': type_counts,
            'avg_script_complexity': round(avg_script_complexity, 1),
            'has_error_handler': has_error_handler,
            'warnings': warnings,
            'recommendations': recommendations,
        }

    def _detect_anti_patterns(self, type_counts, total, scripts,
                               conditions, has_error_handler, depth) -> List[Dict[str, str]]:
        warnings = []

        if not has_error_handler:
            warnings.append({
                'severity': 'high',
                'title': 'No Error Handling Detected',
                'description': 'No error end events found. Consider adding an Exception Subprocess for robust error handling.'
            })

        if scripts > 30:
            warnings.append({
                'severity': 'medium',
                'title': f'High Script Count ({scripts})',
                'description': 'Many Groovy scripts increase maintenance risk. Consider consolidating logic.'
            })

        if type_counts.get('ContentModifier', 0) > 20:
            warnings.append({
                'severity': 'low',
                'title': f"Excessive Content Modifiers ({type_counts['ContentModifier']})",
                'description': 'Large number of Content Modifiers may indicate overly granular property mapping.'
            })

        if total > 100:
            warnings.append({
                'severity': 'medium',
                'title': f'Large Flow ({total} components)',
                'description': 'This is a very large iFlow. Consider splitting into smaller reusable sub-flows.'
            })

        if depth > 10:
            warnings.append({
                'severity': 'low',
                'title': f'Deep Nesting (depth {depth})',
                'description': 'Deeply nested flow paths can be hard to trace. Consider flattening where possible.'
            })

        return warnings

    def _generate_recommendations(self, warnings, type_counts, adapter_types) -> List[str]:
        recs = []
        severities = {w['severity'] for w in warnings}
        if 'high' in severities:
            recs.append('Add an Exception Subprocess with proper error logging and notification.')
        if type_counts.get('GroovyScript', 0) > 20:
            recs.append('Group related Groovy scripts into shared utility libraries.')
        if 'JMS' in adapter_types:
            recs.append('Ensure JMS queue retention thresholds and expiry periods are configured.')
        if 'Salesforce' in adapter_types:
            recs.append('Validate Salesforce OAuth credentials are managed via Secure Parameters.')
        if type_counts.get('Router', 0) > 5:
            recs.append('Consider documenting router conditions in the iFlow description for maintainability.')
        return recs
