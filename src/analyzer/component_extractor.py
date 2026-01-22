from typing import Dict, List, Any
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET
import html as html_module
from .groovy_analyzer import GroovyAnalyzer


class ComponentExtractor:
    """Extracts and normalizes components from parsed iFlow data"""
    
    def __init__(self):
        self.groovy_analyzer = GroovyAnalyzer()
        self.script_cache = {}
        self.message_flows = []
    
    def extract(self, parsed_data: Dict[str, Any], zip_path: str = None) -> List[Dict[str, Any]]:
        """Extract and normalize all components from parsed data"""
        components = []
        
        # Store message flows for later reference
        self.message_flows = parsed_data.get('message_flows', [])
        
        # Load Groovy scripts if zip_path is provided
        if zip_path:
            self._load_groovy_scripts(zip_path)
        
        # Extract participants (senders/receivers)
        for participant in parsed_data.get('participants', []):
            component = self._normalize_participant(participant)
            components.append(component)
        
        # Extract process components
        for process in parsed_data.get('processes', []):
            # Start events
            for start_event in process.get('start_events', []):
                component = self._normalize_start_event(start_event, process)
                components.append(component)
            
            # Service tasks
            for service_task in process.get('service_tasks', []):
                component = self._normalize_service_task(service_task)
                components.append(component)
            
            # Call activities (subflows)
            for call_activity in process.get('call_activities', []):
                component = self._normalize_call_activity(call_activity)
                components.append(component)
            
            # Exclusive gateways (routers)
            for gateway in process.get('exclusive_gateways', []):
                component = self._normalize_gateway(gateway, process.get('sequence_flows', []))
                components.append(component)
            
            # End events
            for end_event in process.get('end_events', []):
                component = self._normalize_end_event(end_event, process)
                components.append(component)
            
            # Store sequence flows for tree building
            for seq_flow in process.get('sequence_flows', []):
                components.append({
                    'id': seq_flow['id'],
                    'name': seq_flow['name'],
                    'type': 'SequenceFlow',
                    'source': seq_flow['source'],
                    'target': seq_flow['target'],
                    'condition': seq_flow.get('condition', ''),
                    'summary': '',
                    'details': {},
                    'children': []
                })
        
        return components
    
    def _load_groovy_scripts(self, zip_path: str):
        """Load Groovy scripts from ZIP file"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for file_info in zip_ref.filelist:
                    # Look for .groovy files in any location (script, scripts, etc.)
                    if file_info.filename.endswith('.groovy'):
                        script_name = Path(file_info.filename).name
                        with zip_ref.open(file_info.filename) as script_file:
                            script_content = script_file.read().decode('utf-8')
                            self.script_cache[script_name] = script_content
                            print(f"  ✅ Loaded script: {script_name}")
        except Exception as e:
            print(f"  ⚠️  Warning: Could not load Groovy scripts: {e}")
    
    def _normalize_participant(self, participant: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize participant (sender/receiver) to standard format"""
        participant_type = participant.get('type', '')
        category = participant.get('category', '')
        
        # Extract adapter type from properties
        adapter_type = self._detect_adapter_type(participant_type)
        
        summary = self._generate_participant_summary(category, adapter_type)
        
        return {
            'id': participant['id'],
            'name': participant['name'],
            'type': 'Sender' if category == 'sender' else 'Receiver',
            'summary': summary,
            'details': {
                'adapterType': adapter_type,
                'category': category,
                'participantType': participant_type
            },
            'children': []
        }
    
    def _detect_adapter_type(self, participant_type: str) -> str:
        """Detect adapter type from participant type string"""
        type_lower = participant_type.lower()
        
        if 'https' in type_lower or 'http' in type_lower:
            return 'HTTP/HTTPS'
        elif 'processdirect' in type_lower:
            return 'ProcessDirect'
        elif 'sftp' in type_lower:
            return 'SFTP'
        elif 'soap' in type_lower:
            return 'SOAP'
        elif 'idoc' in type_lower:
            return 'IDoc'
        elif 'odata' in type_lower:
            return 'OData'
        elif 'mail' in type_lower or 'smtp' in type_lower:
            return 'Mail'
        elif 'jms' in type_lower:
            return 'JMS'
        elif 'integrationprocess' in type_lower:
            return 'Integration Process'
        else:
            return participant_type
    
    def _normalize_start_event(self, start_event: Dict[str, Any], process: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize start event"""
        process_name = process.get('name', 'Unknown Process')
        return {
            'id': start_event['id'],
            'name': start_event['name'] or f"Start - {process_name}",
            'type': 'StartEvent',
            'summary': f"Entry point of {process_name}",
            'details': {
                'processId': process['id'],
                'processName': process_name
            },
            'children': []
        }
    
    def _normalize_service_task(self, service_task: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize service task (Content Modifier, Groovy Script, etc.)"""
        properties = service_task['properties']
        
        # Check component type in properties
        component_type = properties.get('componentType', '')
        component_name = properties.get('activityType', '')
        script_function = properties.get('scriptFunction', '')
        
        # Detect actual type
        if 'contentmodifier' in component_type.lower() or 'contentmodifier' in component_name.lower():
            return self._normalize_content_modifier(service_task)
        elif 'script' in component_type.lower() or script_function or 'groovy' in str(properties).lower():
            return self._normalize_groovy_script(service_task)
        elif 'requestreply' in component_type.lower():
            return self._normalize_request_reply(service_task)
        elif 'router' in component_type.lower():
            return self._normalize_router_task(service_task)
        else:
            return self._normalize_generic_service_task(service_task)
    
    def _normalize_content_modifier(self, service_task: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Content Modifier"""
        properties = service_task['properties']
        
        # Parse message headers and properties from propertyTable and headerTable
        headers_set = []
        properties_set = []
        body_modified = False
        body_description = ''
        
        # Try to parse propertyTable XML (HTML-encoded)
        property_table = properties.get('propertyTable', '')
        if property_table:
            try:
                # Decode HTML entities if present
                property_table_decoded = html_module.unescape(property_table)
                
                # Wrap in root element if needed
                if not property_table_decoded.startswith('<root>'):
                    property_table_decoded = f'<root>{property_table_decoded}</root>'
                
                root = ET.fromstring(property_table_decoded)
                for row in root.findall('.//row'):
                    cells = {cell.get('id'): cell.text or '' for cell in row.findall('cell')}
                    
                    prop_type = cells.get('Type', '')
                    prop_name = cells.get('Name', '')
                    prop_value = cells.get('Value', '')
                    prop_action = cells.get('Action', 'Create')
                    prop_datatype = cells.get('Datatype', '')
                    
                    if prop_type == 'header' and prop_name:
                        action_str = f"[{prop_action}] " if prop_action != 'Create' else ''
                        value_str = f"${{{prop_value}}}" if prop_value and not prop_value.startswith('$') else (prop_value or '(dynamic)')
                        headers_set.append(f"{action_str}{prop_name} = {value_str}")
                    elif prop_type == 'property' and prop_name:
                        action_str = f"[{prop_action}] " if prop_action != 'Create' else ''
                        value_str = f"${{{prop_value}}}" if prop_value and not prop_value.startswith('$') else (prop_value or '(dynamic)')
                        properties_set.append(f"{action_str}{prop_name} = {value_str}")
            except Exception as e:
                print(f"  ⚠️  Could not parse propertyTable: {e}")
        
        # Try to parse headerTable XML (HTML-encoded)
        header_table = properties.get('headerTable', '')
        if header_table:
            try:
                # Decode HTML entities if present
                header_table_decoded = html_module.unescape(header_table)
                
                # Wrap in root element if needed
                if not header_table_decoded.startswith('<root>'):
                    header_table_decoded = f'<root>{header_table_decoded}</root>'
                
                root = ET.fromstring(header_table_decoded)
                for row in root.findall('.//row'):
                    cells = {cell.get('id'): cell.text or '' for cell in row.findall('cell')}
                    
                    prop_type = cells.get('Type', 'constant')  # Default to constant if not specified
                    prop_name = cells.get('Name', '')
                    prop_value = cells.get('Value', '')
                    prop_action = cells.get('Action', 'Create')
                    
                    if prop_name:
                        action_str = f"[{prop_action}] " if prop_action != 'Create' else ''
                        # Check if type is constant, expression, or xpath
                        if prop_type in ['expression', 'xpath']:
                            value_str = f"(expression: {prop_value})" if prop_value else '(expression)'
                        elif prop_value:
                            value_str = prop_value
                        else:
                            value_str = '(dynamic)'
                        headers_set.append(f"{action_str}{prop_name} = {value_str}")
            except Exception as e:
                print(f"  ⚠️  Could not parse headerTable: {e}")
        
        # Check if body is modified
        body_type = properties.get('bodyType', '')
        message_body = properties.get('messageBody', '')
        
        if body_type or message_body:
            body_modified = True
            
            if body_type == 'constant':
                body_description = 'Sets body to constant value'
            elif body_type == 'expression':
                body_description = 'Sets body using expression/XPath'
            elif message_body:
                preview = message_body[:100] + '...' if len(message_body) > 100 else message_body
                body_description = f'Body: {preview}'
            else:
                body_description = 'Modifies message body'
        
        summary = self._generate_content_modifier_summary(properties_set, headers_set, body_modified, body_type)
        
        return {
            'id': service_task['id'],
            'name': service_task['name'] or 'Content Modifier',
            'type': 'ContentModifier',
            'summary': summary,
            'details': {
                'propertiesSet': properties_set if properties_set else ['No properties set'],
                'headersSet': headers_set if headers_set else ['No headers set'],
                'bodyModified': body_modified,
                'bodyType': body_type if body_type else 'Not modified',
                'bodyDescription': body_description,
                'messageBody': message_body[:200] + '...' if message_body and len(message_body) > 200 else message_body,
                'activityType': properties.get('activityType', 'ContentModifier')
            },
            'children': []
        }
    
    def _normalize_groovy_script(self, service_task: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Groovy Script"""
        properties = service_task['properties']
        script_name = properties.get('script', properties.get('scriptFunction', ''))
        
        # Try to find and analyze the script
        script_analysis = {'error': 'Script not found'}
        
        # Try different script name variations
        script_candidates = [
            script_name,
            f"{script_name}.groovy" if script_name and not script_name.endswith('.groovy') else script_name,
            properties.get('resourceUri', '').split('/')[-1] if properties.get('resourceUri') else ''
        ]
        
        for candidate in script_candidates:
            if candidate and candidate in self.script_cache:
                script_content = self.script_cache[candidate]
                script_analysis = self.groovy_analyzer.analyze(script_content)
                print(f"  ✅ Analyzed script: {candidate}")
                break
        
        summary = self._generate_groovy_summary(script_analysis, script_name)
        
        # Extract function names for display
        functions = script_analysis.get('functions', [])
        function_display = f" ({', '.join(functions)})" if functions else ""
        
        return {
            'id': service_task['id'],
            'name': service_task['name'] or script_name or 'Groovy Script',
            'type': 'GroovyScript',
            'summary': summary,
            'details': {
                'scriptName': script_name,
                'functionNames': functions,
                'variables': script_analysis.get('variables', []),
                'scriptContent': script_analysis.get('script_content', ''),
                'propertiesRead': script_analysis.get('properties_read', []),
                'propertiesWritten': script_analysis.get('properties_written', []),
                'headersRead': script_analysis.get('headers_read', []),
                'headersWritten': script_analysis.get('headers_written', []),
                'bodyModified': script_analysis.get('body_modified', False),
                'externalCalls': script_analysis.get('external_calls', []),
                'scriptAvailable': 'error' not in script_analysis,
                'scriptDisplayName': f"{script_name}{function_display}" if script_name else "Groovy Script"
            },
            'children': []
        }
    
    def _normalize_request_reply(self, service_task: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Request-Reply (external call)"""
        properties = service_task['properties']
        
        adapter_type = properties.get('adapterType', properties.get('componentType', 'Unknown'))
        target_system = properties.get('address', properties.get('url', properties.get('directory', 'Unknown')))
        
        summary = f"Calls external system synchronously via {adapter_type}"
        
        return {
            'id': service_task['id'],
            'name': service_task['name'] or 'Request Reply',
            'type': 'RequestReply',
            'summary': summary,
            'details': {
                'adapterType': adapter_type,
                'targetSystem': target_system,
                'protocol': properties.get('protocol', 'Unknown'),
                'allProperties': {k: v for k, v in properties.items() if v}
            },
            'children': []
        }
    
    def _normalize_router_task(self, service_task: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Router as service task"""
        properties = service_task['properties']
        
        return {
            'id': service_task['id'],
            'name': service_task['name'] or 'Router',
            'type': 'Router',
            'summary': 'Routes message based on conditions',
            'details': {
                'properties': {k: v for k, v in properties.items() if v}
            },
            'children': []
        }
    
    def _normalize_generic_service_task(self, service_task: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize generic service task (usually Request-Reply)"""
        properties = service_task['properties']
        component_type = properties.get('componentType', properties.get('activityType', 'ServiceTask'))
        
        # Check if this is an ExternalCall (Request-Reply)
        if component_type == 'ExternalCall' or properties.get('activityType') == 'ExternalCall':
            return self._normalize_request_reply_from_service_task(service_task)
        
        return {
            'id': service_task['id'],
            'name': service_task['name'] or component_type,
            'type': 'ServiceTask',
            'summary': f"Performs {component_type} operation",
            'details': {
                'componentType': component_type,
                'properties': {k: v for k, v in properties.items() if v}
            },
            'children': []
        }
    
    def _normalize_call_activity(self, call_activity: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Call Activity (subflow/process call)"""
        properties = call_activity['properties']
        
        # Get the actual activity type
        activity_type = properties.get('activityType', '')
        component_type = properties.get('componentType', '')
        
        # Check if it's actually a Content Modifier (Enricher), Groovy Script, etc.
        if 'enricher' in activity_type.lower() or 'contentmodifier' in component_type.lower():
            return self._normalize_content_modifier(call_activity)
        elif 'script' in activity_type.lower() or properties.get('script') or properties.get('scriptFunction'):
            return self._normalize_groovy_script(call_activity)
        elif 'requestreply' in activity_type.lower():
            return self._normalize_request_reply(call_activity)
        
        # Otherwise treat as actual call activity
        subflow_name = properties.get('processId', call_activity['name'])
        
        summary = f"Calls reusable subflow: {subflow_name}"
        
        return {
            'id': call_activity['id'],
            'name': call_activity['name'] or 'Call Activity',
            'type': 'CallActivity',
            'summary': summary,
            'details': {
                'subflowName': subflow_name,
                'activityType': activity_type,
                'componentType': component_type,
                'properties': {k: v for k, v in properties.items() if v}
            },
            'children': []
        }
    
    def _normalize_gateway(self, gateway: Dict[str, Any], sequence_flows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Normalize Exclusive Gateway (router)"""
        # Find all outgoing flows from this gateway
        outgoing_flows = [
            flow for flow in sequence_flows 
            if flow['source'] == gateway['id']
        ]
        
        # Extract conditions
        conditions = []
        for flow in outgoing_flows:
            if flow.get('condition'):
                conditions.append({
                    'route': flow['name'] or flow['target'],
                    'condition': flow['condition']
                })
        
        summary = f"Routes message based on {len(conditions)} condition(s)" if conditions else "Routes message to multiple paths"
        
        return {
            'id': gateway['id'],
            'name': gateway['name'] or 'Router',
            'type': 'Router',
            'summary': summary,
            'details': {
                'conditions': conditions,
                'routeCount': len(outgoing_flows)
            },
            'children': []
        }
    
    def _normalize_end_event(self, end_event: Dict[str, Any], process: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize end event"""
        process_name = process.get('name', 'Unknown Process')
        return {
            'id': end_event['id'],
            'name': end_event['name'] or f"End - {process_name}",
            'type': 'EndEvent',
            'summary': f"End of {process_name}",
            'details': {
                'processId': process['id'],
                'processName': process_name
            },
            'children': []
        }
    
    def _generate_participant_summary(self, category: str, adapter_type: str) -> str:
        """Generate human-readable summary for participant"""
        if category == 'sender':
            return f"Entry point via {adapter_type} adapter"
        elif category == 'receiver':
            return f"Final message delivery via {adapter_type} adapter"
        else:
            return f"Participant using {adapter_type} adapter"
    
    def _generate_content_modifier_summary(self, properties: List[str], headers: List[str], body_modified: bool, body_type: str = '') -> str:
        """Generate summary for Content Modifier"""
        parts = []
        if properties:
            parts.append(f"sets {len(properties)} property/properties")
        if headers:
            parts.append(f"sets {len(headers)} header(s)")
        if body_modified:
            if body_type == 'constant':
                parts.append("sets body to constant")
            elif body_type == 'expression':
                parts.append("sets body using expression")
            else:
                parts.append("modifies message body")
        
        if parts:
            return "Modifies message: " + ", ".join(parts)
        else:
            return "Content Modifier (no modifications detected)"
    
    def _normalize_request_reply_from_service_task(self, service_task: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Request-Reply from ServiceTask with ExternalCall"""
        # Find the message flow that originates from this service task
        message_flow = None
        for flow in self.message_flows:
            if flow['source'] == service_task['id']:
                message_flow = flow
                break
        
        if message_flow:
            flow_props = message_flow.get('properties', {})
            adapter_type = flow_props.get('ComponentType', flow_props.get('TransportProtocol', 'HTTP'))
            url = flow_props.get('httpAddressWithoutQuery', flow_props.get('address', 'Unknown'))
            http_method = flow_props.get('httpMethod', 'GET')
            auth_method = flow_props.get('authenticationMethod', 'None')
            
            summary = f"Calls external system via {adapter_type} - {http_method} {url}"
            
            return {
                'id': service_task['id'],
                'name': service_task['name'] or 'Request Reply',
                'type': 'RequestReply',
                'summary': summary,
                'details': {
                    'adapterType': adapter_type,
                    'url': url,
                    'httpMethod': http_method,
                    'authenticationMethod': auth_method,
                    'targetSystem': flow_props.get('system', 'Unknown'),
                    'protocol': flow_props.get('TransportProtocol', adapter_type)
                },
                'children': []
            }
        else:
            # Fallback if no message flow found
            return {
                'id': service_task['id'],
                'name': service_task['name'] or 'Request Reply',
                'type': 'RequestReply',
                'summary': 'Calls external system (details in message flow)',
                'details': {
                    'note': 'Check message flows for adapter configuration'
                },
                'children': []
            }
    
    def _generate_groovy_summary(self, analysis: Dict[str, Any], script_name: str) -> str:
        """Generate summary for Groovy Script"""
        if 'error' in analysis:
            return f"Executes Groovy script: {script_name} (script file not loaded)"
        
        parts = []
        props_written = analysis.get('properties_written', [])
        props_read = analysis.get('properties_read', [])
        headers_written = analysis.get('headers_written', [])
        body_modified = analysis.get('body_modified', False)
        
        if props_written:
            parts.append(f"sets {len(props_written)} property/properties")
        if props_read:
            parts.append(f"reads {len(props_read)} property/properties")
        if headers_written:
            parts.append(f"sets {len(headers_written)} header(s)")
        if body_modified:
            parts.append("modifies body")
        
        if parts:
            return "Executes custom logic: " + ", ".join(parts)
        else:
            return f"Executes Groovy script: {script_name}"