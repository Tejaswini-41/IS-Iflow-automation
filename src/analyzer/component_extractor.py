from typing import Dict, List, Any
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET
import html as html_module
from .groovy_analyzer import GroovyAnalyzer


class ComponentExtractor:
    """Extracts and normalizes components from parsed iFlow data"""

    # Expanded adapter type detection map
    ADAPTER_PATTERNS = {
        'Salesforce': ['salesforce', 'sfdc'],
        'HTTPS': ['https'],
        'HTTP': ['http'],
        'JMS': ['jms'],
        'SFTP': ['sftp'],
        'FTP': ['ftp'],
        'SOAP': ['soap'],
        'IDoc': ['idoc'],
        'OData': ['odata'],
        'Mail/SMTP': ['mail', 'smtp'],
        'AMQP': ['amqp'],
        'RFC': ['rfc', 'bapi'],
        'SuccessFactors': ['successfactors', 'sfsf'],
        'Ariba': ['ariba'],
        'XI': ['/xi/', 'xi protocol'],
        'AS2': ['as2'],
        'AS4': ['as4'],
        'ProcessDirect': ['processdirect'],
        'Integration Process': ['integrationprocess'],
    }

    def __init__(self):
        self.groovy_analyzer = GroovyAnalyzer()
        self.script_cache = {}
        self.message_flows = []

    def extract(self, parsed_data: Dict[str, Any], zip_path: str = None) -> List[Dict[str, Any]]:
        """Extract and normalize all components from parsed data"""
        components = []
        self.message_flows = parsed_data.get('message_flows', [])

        if zip_path:
            self._load_groovy_scripts_from_zip(zip_path)
        else:
            # Also try loading from folder if it's a folder input
            self._try_load_groovy_from_folder(parsed_data)

        # Participants (senders / receivers)
        for participant in parsed_data.get('participants', []):
            component = self._normalize_participant(participant)
            if component:
                components.append(component)

        # Process elements
        for process in parsed_data.get('processes', []):
            seq_flows = process.get('sequence_flows', [])

            for element in process.get('elements', []):
                component = self._normalize_element(element, seq_flows)
                if component:
                    components.append(component)

            # Store sequence flows as lightweight connectors
            for seq_flow in seq_flows:
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

    # ─── Script loading ───────────────────────────────────────────────────────

    def _load_groovy_scripts_from_zip(self, zip_path: str):
        try:
            with zipfile.ZipFile(zip_path, 'r') as zr:
                for fi in zr.filelist:
                    if fi.filename.endswith('.groovy'):
                        name = Path(fi.filename).name
                        with zr.open(fi.filename) as sf:
                            self.script_cache[name] = sf.read().decode('utf-8', errors='replace')
                        print(f"  ✅ Loaded script: {name}")
        except Exception as e:
            print(f"  ⚠️  Could not load Groovy scripts from ZIP: {e}")

    def _try_load_groovy_from_folder(self, parsed_data: Dict):
        """Attempt to find scripts relative to iflw file path"""
        filename = parsed_data.get('filename', '')
        if not filename:
            return
        # Scripts are usually in src/main/resources/script/
        # We'll rely on zip_path for folder-based loading too;
        # this is a best-effort in case parse_folder was used
        pass

    def load_scripts_from_folder(self, folder_path: str):
        """Load all Groovy scripts from a folder tree"""
        folder = Path(folder_path)
        for gf in folder.rglob('*.groovy'):
            try:
                content = gf.read_text(encoding='utf-8', errors='replace')
                self.script_cache[gf.name] = content
                print(f"  ✅ Loaded script: {gf.name}")
            except Exception as e:
                print(f"  ⚠️  Could not read {gf.name}: {e}")

    # ─── Routing ─────────────────────────────────────────────────────────────

    def _normalize_element(self, element: Dict[str, Any], seq_flows: List[Dict[str, Any]]) -> Dict[str, Any]:
        btype = element.get('bpmnType', '')
        props = element.get('properties', {})

        if btype == 'startEvent':
            return self._normalize_start_event(element)
        elif btype == 'endEvent':
            return self._normalize_end_event(element)
        elif btype in ('exclusiveGateway', 'parallelGateway', 'inclusiveGateway'):
            return self._normalize_gateway(element, seq_flows, btype)
        elif btype == 'intermediateCatchEvent':
            return self._normalize_intermediate_event(element, 'catch')
        elif btype == 'intermediateThrowEvent':
            return self._normalize_intermediate_event(element, 'throw')
        elif btype == 'boundaryEvent':
            return self._normalize_boundary_event(element)
        elif btype in ('serviceTask', 'callActivity', 'task', 'userTask'):
            return self._normalize_task_element(element)
        elif btype == 'subProcess':
            return self._normalize_subprocess(element)
        else:
            return self._normalize_generic(element)

    # ─── Event normalizers ────────────────────────────────────────────────────

    def _normalize_start_event(self, elem: Dict) -> Dict:
        defs = elem.get('eventDefinitions', [])
        ev_type = defs[0].lower() if defs else 'none'
        return {
            'id': elem['id'],
            'name': elem['name'] or 'Start',
            'type': 'StartEvent',
            'summary': f"Start event ({ev_type})" if ev_type != 'none' else "Flow entry point",
            'details': {'eventDefinitions': defs},
            'children': []
        }

    def _normalize_end_event(self, elem: Dict) -> Dict:
        defs = elem.get('eventDefinitions', [])
        ev_type = defs[0].lower() if defs else 'none'
        label = 'Error end event' if ev_type == 'error' else ('Terminate end event' if ev_type == 'terminate' else 'Flow end')
        return {
            'id': elem['id'],
            'name': elem['name'] or 'End',
            'type': 'EndEvent',
            'summary': label,
            'details': {'eventDefinitions': defs},
            'children': []
        }

    def _normalize_intermediate_event(self, elem: Dict, direction: str) -> Dict:
        defs = elem.get('eventDefinitions', [])
        ev_type = defs[0].lower() if defs else 'intermediate'
        return {
            'id': elem['id'],
            'name': elem['name'] or f"Intermediate {ev_type.title()} Event",
            'type': 'IntermediateEvent',
            'summary': f"{direction.title()} {ev_type} event",
            'details': {'direction': direction, 'eventDefinitions': defs},
            'children': []
        }

    def _normalize_boundary_event(self, elem: Dict) -> Dict:
        defs = elem.get('eventDefinitions', [])
        ev_type = defs[0].lower() if defs else 'boundary'
        return {
            'id': elem['id'],
            'name': elem['name'] or f"Boundary ({ev_type.title()})",
            'type': 'BoundaryEvent',
            'summary': f"Catches {ev_type} events on attached task",
            'details': {
                'eventDefinitions': defs,
                'attachedToRef': elem.get('attachedToRef', ''),
                'cancelActivity': elem.get('cancelActivity', 'true')
            },
            'children': []
        }

    def _normalize_gateway(self, elem: Dict, seq_flows: List, btype: str) -> Dict:
        outgoing = [f for f in seq_flows if f['source'] == elem['id']]
        conditions = [
            {'route': f.get('name') or f['target'], 'condition': f['condition']}
            for f in outgoing if f.get('condition')
        ]
        gtype = 'Parallel' if 'parallel' in btype.lower() else ('Inclusive' if 'inclusive' in btype.lower() else 'Exclusive')
        summary = f"{gtype} gateway: routes to {len(outgoing)} path(s)"
        if conditions:
            summary += f" with {len(conditions)} condition(s)"
        return {
            'id': elem['id'],
            'name': elem['name'] or f'{gtype} Gateway',
            'type': 'Router',
            'summary': summary,
            'details': {
                'gatewayType': gtype,
                'conditions': conditions,
                'routeCount': len(outgoing)
            },
            'children': []
        }

    def _normalize_subprocess(self, elem: Dict) -> Dict:
        return {
            'id': elem['id'],
            'name': elem['name'] or 'Sub Process',
            'type': 'SubProcess',
            'summary': 'Embedded sub-process (contains its own flow)',
            'details': {'properties': {k: v for k, v in elem.get('properties', {}).items() if v}},
            'children': []
        }

    # ─── Task normalizers ─────────────────────────────────────────────────────

    def _normalize_task_element(self, elem: Dict) -> Dict:
        props = elem.get('properties', {})
        comp_type = props.get('componentType', '')
        activity_type = props.get('activityType', '')
        comp_lower = comp_type.lower()
        act_lower = activity_type.lower()

        if 'contentmodifier' in comp_lower or 'contentmodifier' in act_lower or 'enricher' in act_lower:
            return self._normalize_content_modifier(elem)
        elif 'script' in comp_lower or 'script' in act_lower or props.get('script') or props.get('scriptFunction'):
            return self._normalize_groovy_script(elem)
        elif 'requestreply' in act_lower or comp_type == 'ExternalCall' or activity_type == 'ExternalCall':
            return self._normalize_request_reply_task(elem)
        elif 'router' in comp_lower:
            return self._normalize_router_task(elem)
        elif 'splitter' in comp_lower or 'split' in act_lower:
            return self._normalize_generic_typed(elem, 'Splitter', 'Splits message into multiple parts')
        elif 'gather' in comp_lower or 'aggregator' in comp_lower:
            return self._normalize_generic_typed(elem, 'Gather', 'Aggregates/gathers split messages')
        elif 'filter' in comp_lower:
            return self._normalize_generic_typed(elem, 'Filter', 'Filters message content based on condition')
        elif 'validator' in comp_lower or 'validate' in act_lower:
            return self._normalize_generic_typed(elem, 'Validator', 'Validates message against schema/rules')
        elif 'encryptor' in comp_lower or 'encrypt' in act_lower:
            return self._normalize_generic_typed(elem, 'Encryptor', 'Encrypts message content')
        elif 'decryptor' in comp_lower or 'decrypt' in act_lower:
            return self._normalize_generic_typed(elem, 'Decryptor', 'Decrypts message content')
        elif 'datastore' in comp_lower or 'persist' in act_lower:
            return self._normalize_generic_typed(elem, 'DataStoreOperations', 'Persists or reads data from Data Store')
        elif 'xmlmodifier' in comp_lower or 'xmlmod' in act_lower:
            return self._normalize_generic_typed(elem, 'XMLModifier', 'Modifies XML message structure')
        elif 'formatter' in comp_lower:
            return self._normalize_generic_typed(elem, 'Formatter', 'Formats message (CSV/JSON/XML converter)')
        elif 'mapping' in comp_lower or 'mapping' in act_lower:
            return self._normalize_generic_typed(elem, 'Mapping', 'Maps message fields using mapping definition')
        else:
            return self._normalize_generic(elem)

    def _normalize_generic_typed(self, elem: Dict, comp_type: str, summary: str) -> Dict:
        props = elem.get('properties', {})
        return {
            'id': elem['id'],
            'name': elem['name'] or comp_type,
            'type': comp_type,
            'summary': summary,
            'details': {'properties': {k: v for k, v in props.items() if v}},
            'children': []
        }

    def _normalize_content_modifier(self, elem: Dict) -> Dict:
        props = elem.get('properties', {})
        headers_set = []
        properties_set = []
        body_modified = False
        body_type = ''
        body_description = ''

        for table_key in ('propertyTable', 'headerTable'):
            table_xml = props.get(table_key, '')
            if not table_xml:
                continue
            try:
                decoded = html_module.unescape(table_xml)
                if not decoded.strip().startswith('<root>'):
                    decoded = f'<root>{decoded}</root>'
                root = ET.fromstring(decoded)
                for row in root.findall('.//row'):
                    cells = {cell.get('id'): cell.text or '' for cell in row.findall('cell')}
                    p_type = cells.get('Type', 'constant')
                    p_name = cells.get('Name', '')
                    p_value = cells.get('Value', '')
                    p_action = cells.get('Action', 'Create')
                    if not p_name:
                        continue
                    action_str = f"[{p_action}] " if p_action not in ('Create', '') else ''
                    if p_type in ('expression', 'xpath'):
                        value_str = f"(expr: {p_value})" if p_value else '(expression)'
                    elif p_value and p_value.startswith('${'):
                        value_str = p_value
                    elif p_value:
                        value_str = p_value
                    else:
                        value_str = '(dynamic)'

                    entry = f"{action_str}{p_name} = {value_str}"
                    if p_type == 'header' or table_key == 'headerTable':
                        headers_set.append(entry)
                    else:
                        properties_set.append(entry)
            except Exception as e:
                pass

        body_type = props.get('bodyType', '')
        message_body = props.get('messageBody', '')
        if body_type or message_body:
            body_modified = True
            if body_type == 'constant':
                body_description = 'Sets body to constant value'
            elif body_type == 'expression':
                body_description = 'Sets body via expression/XPath'
            else:
                preview = (message_body[:120] + '…') if len(message_body) > 120 else message_body
                body_description = f'Body: {preview}'

        summary_parts = []
        if properties_set:
            summary_parts.append(f"sets {len(properties_set)} propert{'y' if len(properties_set)==1 else 'ies'}")
        if headers_set:
            summary_parts.append(f"sets {len(headers_set)} header{'s' if len(headers_set)!=1 else ''}")
        if body_modified:
            summary_parts.append("modifies body")
        summary = ("Modifies message: " + ", ".join(summary_parts)) if summary_parts else "Content Modifier (no modifications detected)"

        return {
            'id': elem['id'],
            'name': elem['name'] or 'Content Modifier',
            'type': 'ContentModifier',
            'summary': summary,
            'details': {
                'propertiesSet': properties_set or ['No properties set'],
                'headersSet': headers_set or ['No headers set'],
                'bodyModified': body_modified,
                'bodyType': body_type or 'Not modified',
                'bodyDescription': body_description,
                'messageBody': (message_body[:300] + '…') if len(message_body) > 300 else message_body,
            },
            'children': []
        }

    def _normalize_groovy_script(self, elem: Dict) -> Dict:
        props = elem.get('properties', {})
        script_name = props.get('script', props.get('scriptFunction', ''))

        # Try various name patterns to find script in cache
        candidates = [
            script_name,
            f"{script_name}.groovy" if script_name and not script_name.endswith('.groovy') else None,
            props.get('resourceUri', '').split('/')[-1],
        ]

        analysis = {'error': 'Script not found'}
        found_name = None
        for c in candidates:
            if c and c in self.script_cache:
                analysis = self.groovy_analyzer.analyze(self.script_cache[c])
                found_name = c
                print(f"  ✅ Analyzed script: {c}")
                break

        functions = analysis.get('functions', [])
        summary = self.groovy_analyzer.generate_summary(analysis)

        return {
            'id': elem['id'],
            'name': elem['name'] or script_name or 'Groovy Script',
            'type': 'GroovyScript',
            'summary': summary,
            'details': {
                'scriptName': script_name or found_name or 'Unknown',
                'functionNames': functions,
                'variables': analysis.get('variables', []),
                'imports': analysis.get('imports', []),
                'scriptContent': analysis.get('script_content', ''),
                'propertiesRead': analysis.get('properties_read', []),
                'propertiesWritten': analysis.get('properties_written', []),
                'headersRead': analysis.get('headers_read', []),
                'headersWritten': analysis.get('headers_written', []),
                'bodyModified': analysis.get('body_modified', False),
                'externalCalls': analysis.get('external_calls', []),
                'hasExceptionHandling': analysis.get('has_exception_handling', False),
                'hasLogging': analysis.get('has_logging', False),
                'hasJsonOps': analysis.get('has_json_ops', False),
                'hasXmlOps': analysis.get('has_xml_ops', False),
                'hasBase64Ops': analysis.get('has_base64_ops', False),
                'loc': analysis.get('loc', 0),
                'complexityScore': analysis.get('complexity_score', 0),
                'scriptAvailable': 'error' not in analysis,
            },
            'children': []
        }

    def _normalize_request_reply_task(self, elem: Dict) -> Dict:
        props = elem.get('properties', {})

        # Find associated message flow for full adapter details
        message_flow = next((f for f in self.message_flows if f['source'] == elem['id']), None)

        if message_flow:
            fp = message_flow.get('properties', {})
            adapter_type = fp.get('ComponentType', fp.get('TransportProtocol', 'HTTP'))
            url = fp.get('httpAddressWithoutQuery', fp.get('address', fp.get('apexUrl', fp.get('loginUrl', ''))))
            http_method = fp.get('httpMethod', fp.get('apexMethod', 'POST'))
            auth = fp.get('authenticationMethod', fp.get('accountType', 'None'))
            queue = fp.get('QueueName_outbound', '')
            system = fp.get('system', message_flow.get('name', ''))
            summary = f"Calls {system} via {adapter_type}"
            if url:
                summary += f" → {url}"
            details = {
                'adapterType': adapter_type,
                'url': url,
                'httpMethod': http_method,
                'authenticationMethod': auth,
                'targetSystem': system,
                'queueName': queue,
                'allProperties': {k: v for k, v in fp.items() if v and k not in ('cmdVariantUri',)},
            }
        else:
            adapter_type = props.get('adapterType', props.get('componentType', 'Unknown'))
            url = props.get('address', props.get('url', ''))
            summary = f"Calls external system via {adapter_type}"
            details = {
                'adapterType': adapter_type,
                'url': url,
                'allProperties': {k: v for k, v in props.items() if v},
            }

        return {
            'id': elem['id'],
            'name': elem['name'] or 'Request Reply',
            'type': 'RequestReply',
            'summary': summary,
            'details': details,
            'children': []
        }

    def _normalize_router_task(self, elem: Dict) -> Dict:
        props = elem.get('properties', {})
        return {
            'id': elem['id'],
            'name': elem['name'] or 'Router',
            'type': 'Router',
            'summary': 'Routes message based on conditions',
            'details': {'properties': {k: v for k, v in props.items() if v}},
            'children': []
        }

    def _normalize_generic(self, elem: Dict) -> Dict:
        props = elem.get('properties', {})
        ct = props.get('componentType', props.get('activityType', elem.get('bpmnType', 'ServiceTask')))
        return {
            'id': elem['id'],
            'name': elem['name'] or ct,
            'type': 'ServiceTask',
            'summary': f"Performs {ct} operation",
            'details': {'componentType': ct, 'properties': {k: v for k, v in props.items() if v}},
            'children': []
        }

    # ─── Participant normalization ─────────────────────────────────────────────

    def _normalize_participant(self, participant: Dict) -> Dict | None:
        cat = participant.get('category', '')
        if cat == 'process':
            return None  # IntegrationProcess participants are represented by their process

        ifl_type = participant.get('type', '')
        props = participant.get('properties', {})

        # Detect adapter type from message flows that reference this participant
        adapter_type = self._detect_adapter_from_flows(participant['id'], ifl_type)

        if cat == 'sender':
            summary = f"Sends messages via {adapter_type} adapter"
            comp_type = 'Sender'
        elif cat == 'receiver':
            summary = f"Receives messages via {adapter_type} adapter"
            comp_type = 'Receiver'
        else:
            summary = f"Participant: {adapter_type}"
            comp_type = 'Participant'

        return {
            'id': participant['id'],
            'name': participant['name'],
            'type': comp_type,
            'summary': summary,
            'details': {
                'adapterType': adapter_type,
                'category': cat,
                'participantType': ifl_type,
            },
            'children': []
        }

    def _detect_adapter_from_flows(self, participant_id: str, ifl_type: str) -> str:
        """Get adapter type from associated message flows first, then ifl_type string"""
        for flow in self.message_flows:
            if flow.get('target') == participant_id or flow.get('source') == participant_id:
                ct = flow.get('properties', {}).get('ComponentType', '')
                if ct:
                    return ct
                # Try transport protocol
                tp = flow.get('properties', {}).get('TransportProtocol', '')
                if tp and tp not in ('Not Applicable', ''):
                    return tp

        return self._detect_adapter_from_string(ifl_type)

    def _detect_adapter_from_string(self, type_str: str) -> str:
        ts = type_str.lower()
        for adapter, patterns in self.ADAPTER_PATTERNS.items():
            if any(p in ts for p in patterns):
                return adapter
        return type_str or 'Unknown'