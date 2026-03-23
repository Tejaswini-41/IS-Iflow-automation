import re
from typing import Dict, List, Any


class GroovyAnalyzer:
    """Static analyzer for Groovy scripts in SAP CPI"""

    def __init__(self):
        pass

    def analyze(self, script_content: str) -> Dict[str, Any]:
        """Perform static analysis on Groovy script content"""
        if not script_content or not script_content.strip():
            return {
                'properties_read': [], 'properties_written': [],
                'headers_read': [], 'headers_written': [],
                'body_modified': False, 'external_calls': [],
                'functions': [], 'variables': [], 'imports': [],
                'has_exception_handling': False, 'has_logging': False,
                'has_json_ops': False, 'has_xml_ops': False,
                'has_base64_ops': False, 'has_sql_ops': False,
                'loc': 0, 'complexity_score': 0,
                'script_content': '', 'error': 'Empty script content'
            }

        lines = script_content.splitlines()
        non_blank_lines = [l for l in lines if l.strip() and not l.strip().startswith('//')]

        return {
            'properties_read': self._extract_properties_read(script_content),
            'properties_written': self._extract_properties_written(script_content),
            'headers_read': self._extract_headers_read(script_content),
            'headers_written': self._extract_headers_written(script_content),
            'body_modified': self._detect_body_modification(script_content),
            'external_calls': self._detect_external_calls(script_content),
            'functions': self._extract_functions(script_content),
            'variables': self._extract_variables(script_content),
            'imports': self._extract_imports(script_content),
            'has_exception_handling': self._detect_exception_handling(script_content),
            'has_logging': self._detect_logging(script_content),
            'has_json_ops': self._detect_json_ops(script_content),
            'has_xml_ops': self._detect_xml_ops(script_content),
            'has_base64_ops': self._detect_base64_ops(script_content),
            'has_sql_ops': self._detect_sql_ops(script_content),
            'loc': len(non_blank_lines),
            'complexity_score': self._calculate_complexity(script_content, non_blank_lines),
            'script_content': script_content,
        }

    # ─── Property / Header access ────────────────────────────────────────────

    def _extract_properties_read(self, script: str) -> List[str]:
        props = []
        patterns = [
            r'message\.getProperty\s*\(\s*["\']([^"\']+)["\']\s*\)',
            r'message\.properties\.get\s*\(\s*["\']([^"\']+)["\']\s*\)',
            r'messageProperties\.get\s*\(\s*["\']([^"\']+)["\']\s*\)',
        ]
        for p in patterns:
            props.extend(re.findall(p, script))
        return sorted(set(props))

    def _extract_properties_written(self, script: str) -> List[str]:
        props = []
        patterns = [
            r'message\.setProperty\s*\(\s*["\']([^"\']+)["\']',
            r'message\.properties\.put\s*\(\s*["\']([^"\']+)["\']',
            r'messageProperties\.put\s*\(\s*["\']([^"\']+)["\']',
        ]
        for p in patterns:
            props.extend(re.findall(p, script))
        return sorted(set(props))

    def _extract_headers_read(self, script: str) -> List[str]:
        hdrs = []
        patterns = [
            r'message\.getHeader\s*\(\s*["\']([^"\']+)["\']\s*\)',
            r'message\.headers\.get\s*\(\s*["\']([^"\']+)["\']\s*\)',
            r'messageHeaders\.get\s*\(\s*["\']([^"\']+)["\']\s*\)',
        ]
        for p in patterns:
            hdrs.extend(re.findall(p, script))
        return sorted(set(hdrs))

    def _extract_headers_written(self, script: str) -> List[str]:
        hdrs = []
        patterns = [
            r'message\.setHeader\s*\(\s*["\']([^"\']+)["\']',
            r'message\.headers\.put\s*\(\s*["\']([^"\']+)["\']',
            r'messageHeaders\.put\s*\(\s*["\']([^"\']+)["\']',
        ]
        for p in patterns:
            hdrs.extend(re.findall(p, script))
        return sorted(set(hdrs))

    def _detect_body_modification(self, script: str) -> bool:
        return bool(
            re.search(r'message\.setBody\s*\(', script) or
            re.search(r'message\.body\s*=', script)
        )

    # ─── External calls ───────────────────────────────────────────────────────

    def _detect_external_calls(self, script: str) -> List[Dict[str, str]]:
        calls = []
        http_pattern = r'(https?://[^\s\'"<>]+)'
        for url in re.findall(http_pattern, script):
            calls.append({'type': 'HTTP', 'target': url})
        if re.search(r'DriverManager\.getConnection', script):
            calls.append({'type': 'Database', 'target': 'JDBC connection'})
        if re.search(r'new\s+URL\s*\(', script):
            calls.append({'type': 'HTTP', 'target': 'URL.openConnection()'})
        return calls

    # ─── Code structure ──────────────────────────────────────────────────────

    def _extract_functions(self, script: str) -> List[str]:
        pattern = r'(?:def|Message|void|String|Integer|Boolean|Map|List|Object)\s+([a-zA-Z_]\w*)\s*\('
        fns = re.findall(pattern, script)
        # Filter out keywords
        keywords = {'if', 'while', 'for', 'switch', 'catch', 'return'}
        return sorted(set(f for f in fns if f not in keywords))

    def _extract_variables(self, script: str) -> List[str]:
        pattern = r'\bdef\s+([a-zA-Z_]\w*)\s*='
        return sorted(set(re.findall(pattern, script)))

    def _extract_imports(self, script: str) -> List[str]:
        return re.findall(r'^import\s+(.+)$', script, re.MULTILINE)

    # ─── Pattern detection ───────────────────────────────────────────────────

    def _detect_exception_handling(self, script: str) -> bool:
        return bool(re.search(r'\btry\s*\{', script) or re.search(r'\bcatch\s*\(', script))

    def _detect_logging(self, script: str) -> bool:
        return bool(re.search(r'\blog\.(info|warn|error|debug|trace)\s*\(', script, re.IGNORECASE))

    def _detect_json_ops(self, script: str) -> bool:
        return bool(
            re.search(r'JsonSlurper|JsonBuilder|JsonOutput|groovy\.json', script) or
            re.search(r'new\s+JsonSlurper', script)
        )

    def _detect_xml_ops(self, script: str) -> bool:
        return bool(
            re.search(r'XmlSlurper|XmlParser|XmlBuilder|groovy\.xml|parseText', script)
        )

    def _detect_base64_ops(self, script: str) -> bool:
        return bool(
            re.search(r'Base64|\.encodeBase64|\.decodeBase64', script)
        )

    def _detect_sql_ops(self, script: str) -> bool:
        return bool(
            re.search(r'\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b', script, re.IGNORECASE) or
            re.search(r'groovy\.sql\.Sql|DriverManager', script)
        )

    # ─── Complexity ──────────────────────────────────────────────────────────

    def _calculate_complexity(self, script: str, non_blank_lines: List[str]) -> int:
        """Simple cyclomatic-style complexity score (1-10 scale)"""
        score = 1
        # Branch points
        score += len(re.findall(r'\b(if|else\s+if|while|for|switch|case|catch|&&|\|\|)\b', script))
        # External integrations
        score += len(re.findall(r'(https?://|DriverManager|new URL)', script)) * 2
        # Long script penalty
        loc = len(non_blank_lines)
        if loc > 100:
            score += 3
        elif loc > 50:
            score += 1
        return min(score, 100)

    def generate_summary(self, analysis: Dict[str, Any]) -> str:
        parts = []
        if analysis.get('properties_written'):
            parts.append(f"Sets {len(analysis['properties_written'])} properties")
        if analysis.get('properties_read'):
            parts.append(f"Reads {len(analysis['properties_read'])} properties")
        if analysis.get('headers_written'):
            parts.append(f"Sets {len(analysis['headers_written'])} headers")
        if analysis.get('body_modified'):
            parts.append("Modifies body")
        if analysis.get('external_calls'):
            parts.append(f"{len(analysis['external_calls'])} external call(s)")
        if analysis.get('has_exception_handling'):
            parts.append("Has error handling")
        if analysis.get('has_json_ops'):
            parts.append("JSON processing")
        if analysis.get('has_xml_ops'):
            parts.append("XML processing")
        if parts:
            return "Executes: " + ", ".join(parts)
        return "Executes custom Groovy script"