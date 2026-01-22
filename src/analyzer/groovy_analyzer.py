import re
from typing import Dict, List, Any


class GroovyAnalyzer:
    """Static analyzer for Groovy scripts in SAP CPI"""
    
    def __init__(self):
        """Initialize the analyzer"""
        pass
    
    def analyze(self, script_content: str) -> Dict[str, Any]:
        """
        Perform static analysis on Groovy script content
        Returns dictionary with analysis results
        """
        if not script_content:
            return {
                'properties_read': [],
                'properties_written': [],
                'headers_read': [],
                'headers_written': [],
                'body_modified': False,
                'external_calls': [],
                'functions': [],
                'variables': [],
                'script_content': '',
                'error': 'Empty script content'
            }
        
        return {
            'properties_read': self._extract_properties_read(script_content),
            'properties_written': self._extract_properties_written(script_content),
            'headers_read': self._extract_headers_read(script_content),
            'headers_written': self._extract_headers_written(script_content),
            'body_modified': self._detect_body_modification(script_content),
            'external_calls': self._detect_external_calls(script_content),
            'functions': self._extract_functions(script_content),
            'variables': self._extract_variables(script_content),
            'script_content': script_content
        }
    
    def _extract_properties_read(self, script: str) -> List[str]:
        """Extract property reads from script"""
        properties = []
        
        # Pattern: message.getProperty("propertyName")
        pattern1 = r'message\.getProperty\s*\(\s*["\']([^"\']+)["\']\s*\)'
        properties.extend(re.findall(pattern1, script))
        
        # Pattern: message.properties.get("propertyName")
        pattern2 = r'message\.properties\.get\s*\(\s*["\']([^"\']+)["\']\s*\)'
        properties.extend(re.findall(pattern2, script))
        
        # Pattern: messageProperties.get("propertyName")
        pattern3 = r'messageProperties\.get\s*\(\s*["\']([^"\']+)["\']\s*\)'
        properties.extend(re.findall(pattern3, script))
        
        return list(set(properties))  # Remove duplicates
    
    def _extract_properties_written(self, script: str) -> List[str]:
        """Extract property writes from script"""
        properties = []
        
        # Pattern: message.setProperty("propertyName", value)
        pattern1 = r'message\.setProperty\s*\(\s*["\']([^"\']+)["\']'
        properties.extend(re.findall(pattern1, script))
        
        # Pattern: message.properties.put("propertyName", value)
        pattern2 = r'message\.properties\.put\s*\(\s*["\']([^"\']+)["\']'
        properties.extend(re.findall(pattern2, script))
        
        # Pattern: messageProperties.put("propertyName", value)
        pattern3 = r'messageProperties\.put\s*\(\s*["\']([^"\']+)["\']'
        properties.extend(re.findall(pattern3, script))
        
        return list(set(properties))
    
    def _extract_headers_read(self, script: str) -> List[str]:
        """Extract header reads from script"""
        headers = []
        
        # Pattern: message.getHeader("headerName")
        pattern1 = r'message\.getHeader\s*\(\s*["\']([^"\']+)["\']\s*\)'
        headers.extend(re.findall(pattern1, script))
        
        # Pattern: message.headers.get("headerName")
        pattern2 = r'message\.headers\.get\s*\(\s*["\']([^"\']+)["\']\s*\)'
        headers.extend(re.findall(pattern2, script))
        
        # Pattern: messageHeaders.get("headerName")
        pattern3 = r'messageHeaders\.get\s*\(\s*["\']([^"\']+)["\']\s*\)'
        headers.extend(re.findall(pattern3, script))
        
        return list(set(headers))
    
    def _extract_headers_written(self, script: str) -> List[str]:
        """Extract header writes from script"""
        headers = []
        
        # Pattern: message.setHeader("headerName", value)
        pattern1 = r'message\.setHeader\s*\(\s*["\']([^"\']+)["\']'
        headers.extend(re.findall(pattern1, script))
        
        # Pattern: message.headers.put("headerName", value)
        pattern2 = r'message\.headers\.put\s*\(\s*["\']([^"\']+)["\']'
        headers.extend(re.findall(pattern2, script))
        
        # Pattern: messageHeaders.put("headerName", value)
        pattern3 = r'messageHeaders\.put\s*\(\s*["\']([^"\']+)["\']'
        headers.extend(re.findall(pattern3, script))
        
        return list(set(headers))
    
    def _detect_body_modification(self, script: str) -> bool:
        """Detect if script modifies message body"""
        # Pattern: message.setBody(...)
        if re.search(r'message\.setBody\s*\(', script):
            return True
        
        # Pattern: message.body = ...
        if re.search(r'message\.body\s*=', script):
            return True
        
        # Pattern: body = ...; message.setBody(body)
        if re.search(r'message\.setBody\s*\([^)]+\)', script):
            return True
        
        return False
    
    def _detect_external_calls(self, script: str) -> List[Dict[str, str]]:
        """Detect external API/HTTP calls in script"""
        calls = []
        
        # Pattern: HTTP/REST calls
        http_pattern = r'(http|https)://[^\s\'"<>]+'
        urls = re.findall(http_pattern, script)
        for url in urls:
            calls.append({
                'type': 'HTTP',
                'target': url
            })
        
        # Pattern: def connection = ... (database connections)
        if re.search(r'def\s+connection\s*=.*DriverManager', script):
            calls.append({
                'type': 'Database',
                'target': 'Database connection detected'
            })
        
        # Pattern: new URL(...).openConnection()
        if re.search(r'new\s+URL\s*\([^)]+\)\.openConnection\(\)', script):
            calls.append({
                'type': 'HTTP',
                'target': 'URL connection detected'
            })
        
        return calls
    
    def _extract_functions(self, script: str) -> List[str]:
        """Extract function/method names from Groovy script"""
        functions = []
        
        # Pattern: def functionName(...) or Message functionName(...)
        function_pattern = r'(?:def|Message|void|String|Integer|Boolean)\s+(\w+)\s*\('
        matches = re.findall(function_pattern, script)
        functions.extend(matches)
        
        return list(set(functions))
    
    def _extract_variables(self, script: str) -> List[str]:
        """Extract variable names from Groovy script"""
        variables = []
        
        # Pattern: def variableName = ...
        def_pattern = r'def\s+(\w+)\s*='
        variables.extend(re.findall(def_pattern, script))
        
        # Pattern: variableName = ... (assignments without def)
        # Only capture if it's a new line or after semicolon
        assign_pattern = r'(?:^|\n|\s)\s*([a-z][a-zA-Z0-9_]*)\s*='
        variables.extend(re.findall(assign_pattern, script))
        
        return list(set(variables))
    
    def generate_summary(self, analysis: Dict[str, Any]) -> str:
        """Generate human-readable summary from analysis"""
        parts = []
        
        if analysis.get('properties_written'):
            parts.append(f"Sets {len(analysis['properties_written'])} properties")
        
        if analysis.get('properties_read'):
            parts.append(f"Reads {len(analysis['properties_read'])} properties")
        
        if analysis.get('headers_written'):
            parts.append(f"Sets {len(analysis['headers_written'])} headers")
        
        if analysis.get('body_modified'):
            parts.append("Modifies message body")
        
        if analysis.get('external_calls'):
            parts.append(f"Makes {len(analysis['external_calls'])} external call(s)")
        
        if parts:
            return "Executes custom logic: " + ", ".join(parts)
        else:
            return "Executes custom Groovy script"