import xml.etree.ElementTree as ET
from typing import Dict, List, Any
import zipfile
from pathlib import Path
import html as html_module


class IFlowParser:
    """Parses SAP CPI iFlow XML files and extracts BPMN structure"""

    NAMESPACES = {
        'bpmn2': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
        'ifl': 'http:///com.sap.ifl.model/Ifl.xsd',
        'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI'
    }

    # All BPMN element types to extract from a process
    COMPONENT_TYPES = [
        'bpmn2:startEvent',
        'bpmn2:endEvent',
        'bpmn2:serviceTask',
        'bpmn2:callActivity',
        'bpmn2:exclusiveGateway',
        'bpmn2:parallelGateway',
        'bpmn2:inclusiveGateway',
        'bpmn2:subProcess',
        'bpmn2:intermediateCatchEvent',
        'bpmn2:intermediateThrowEvent',
        'bpmn2:boundaryEvent',
        'bpmn2:userTask',
        'bpmn2:task',
    ]

    def __init__(self):
        self.root = None
        self.filename = ""

    def parse(self, input_path: str) -> Dict[str, Any]:
        """Main entry point - parse ZIP or folder"""
        path = Path(input_path)

        if path.is_file() and path.suffix == '.zip':
            return self.parse_zip(str(path))
        elif path.is_dir():
            return self.parse_folder(str(path))
        else:
            raise ValueError(f"Invalid input: {input_path}. Must be a ZIP file or folder.")

    def parse_zip(self, zip_path: str) -> Dict[str, Any]:
        """Extract and parse .iflw file from ZIP"""
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            iflw_files = [f for f in zip_ref.namelist() if f.endswith('.iflw')]

            if not iflw_files:
                raise ValueError("No .iflw file found in ZIP")

            iflw_path = iflw_files[0]
            with zip_ref.open(iflw_path) as iflw_file:
                xml_content = iflw_file.read().decode('utf-8')
                self.filename = Path(iflw_path).name
                return self.parse_xml(xml_content)

    def parse_folder(self, folder_path: str) -> Dict[str, Any]:
        """Parse .iflw file from extracted folder"""
        folder = Path(folder_path)

        iflw_files = list(folder.rglob('*.iflw'))

        if not iflw_files:
            raise ValueError(f"No .iflw file found in folder: {folder_path}")

        iflw_file = iflw_files[0]
        with open(iflw_file, 'r', encoding='utf-8') as f:
            xml_content = f.read()
            self.filename = iflw_file.name
            return self.parse_xml(xml_content)

    def parse_xml(self, xml_content: str) -> Dict[str, Any]:
        """Parse iFlow XML content"""
        self.root = ET.fromstring(xml_content)

        iflow_meta = self._extract_iflow_metadata(self.root)

        return {
            'filename': self.filename,
            'iflow_name': iflow_meta.get('name', self.filename.replace('.iflw', '')),
            'iflow_description': iflow_meta.get('description', ''),
            'iflow_settings': iflow_meta,
            'participants': self._extract_participants(self.root),
            'processes': self._extract_processes(self.root),
            'message_flows': self._extract_message_flows(self.root)
        }

    def _extract_iflow_metadata(self, root: ET.Element) -> Dict[str, Any]:
        """Extract iFlow-level metadata from the collaboration element"""
        meta = {}
        collaboration = root.find('.//bpmn2:collaboration', self.NAMESPACES)
        if collaboration is not None:
            meta['name'] = collaboration.get('name', '')
            ext = collaboration.find('bpmn2:extensionElements', self.NAMESPACES)
            if ext is not None:
                for prop in ext.findall('.//ifl:property', self.NAMESPACES):
                    key_e = prop.find('key')
                    val_e = prop.find('value')
                    if key_e is not None and val_e is not None:
                        k = key_e.text or ''
                        v = self._extract_value_content(val_e)
                        if k:
                            meta[k] = v
        return meta

    def _extract_participants(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract all participants (senders/receivers/processes)"""
        participants = []

        for participant in root.findall('.//bpmn2:participant', self.NAMESPACES):
            participant_id = participant.get('id', '')
            participant_name = participant.get('name', '')
            ifl_type = participant.get('{http:///com.sap.ifl.model/Ifl.xsd}type', '')
            process_ref = participant.get('processRef', '')

            # Extract participant-level properties
            properties = {}
            ext = participant.find('bpmn2:extensionElements', self.NAMESPACES)
            if ext is not None:
                for prop in ext.findall('.//ifl:property', self.NAMESPACES):
                    key_e = prop.find('key')
                    val_e = prop.find('value')
                    if key_e is not None and val_e is not None:
                        k = key_e.text or ''
                        v = self._extract_value_content(val_e)
                        if k:
                            properties[k] = v

            participants.append({
                'id': participant_id,
                'name': participant_name,
                'type': ifl_type,
                'processRef': process_ref,
                'category': self._categorize_participant(ifl_type),
                'properties': properties
            })

        return participants

    def _categorize_participant(self, participant_type: str) -> str:
        """Categorize participant"""
        pt = participant_type.lower()
        if 'endpointsender' in pt:
            return 'sender'
        elif 'endpointreceiv' in pt:
            return 'receiver'
        elif 'integrationprocess' in pt:
            return 'process'
        else:
            return 'unknown'

    def _extract_processes(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract all process flows"""
        processes = []

        for process in root.findall('.//bpmn2:process', self.NAMESPACES):
            process_id = process.get('id', '')
            process_name = process.get('name', '')

            # Try to get process name from participant reference
            participant_name = self._find_participant_name_for_process(root, process_id)
            if participant_name:
                process_name = participant_name

            # Extract all component types
            all_elements = []
            for comp_type in self.COMPONENT_TYPES:
                for element in process.findall(f'.//{comp_type}', self.NAMESPACES):
                    bpmn_type = comp_type.split(':')[1]
                    component = {
                        'id': element.get('id', ''),
                        'name': element.get('name', ''),
                        'bpmnType': bpmn_type,
                        'properties': self._extract_element_properties(element),
                        'attachedToRef': element.get('attachedToRef', ''),
                        'cancelActivity': element.get('cancelActivity', 'true'),
                    }
                    # For boundary events, grab event definitions
                    if bpmn_type in ('intermediateCatchEvent', 'intermediateThrowEvent', 'boundaryEvent', 'startEvent', 'endEvent'):
                        component['eventDefinitions'] = self._extract_event_definitions(element)
                    all_elements.append(component)

            sequence_flows = self._extract_sequence_flows(process)

            processes.append({
                'id': process_id,
                'name': process_name,
                'elements': all_elements,
                # Legacy buckets kept for backward compat
                'start_events': [e for e in all_elements if e['bpmnType'] == 'startEvent'],
                'end_events': [e for e in all_elements if e['bpmnType'] == 'endEvent'],
                'service_tasks': [e for e in all_elements if e['bpmnType'] == 'serviceTask'],
                'call_activities': [e for e in all_elements if e['bpmnType'] == 'callActivity'],
                'exclusive_gateways': [e for e in all_elements if e['bpmnType'] == 'exclusiveGateway'],
                'parallel_gateways': [e for e in all_elements if e['bpmnType'] == 'parallelGateway'],
                'inclusive_gateways': [e for e in all_elements if e['bpmnType'] == 'inclusiveGateway'],
                'intermediate_events': [e for e in all_elements if e['bpmnType'] in ('intermediateCatchEvent', 'intermediateThrowEvent')],
                'boundary_events': [e for e in all_elements if e['bpmnType'] == 'boundaryEvent'],
                'sub_processes': [e for e in all_elements if e['bpmnType'] == 'subProcess'],
                'sequence_flows': sequence_flows
            })

        return processes

    def _find_participant_name_for_process(self, root: ET.Element, process_id: str) -> str:
        """Find the participant name that references this process"""
        for participant in root.findall('.//bpmn2:participant', self.NAMESPACES):
            if participant.get('processRef', '') == process_id:
                return participant.get('name', '')
        return ''

    def _extract_element_properties(self, element: ET.Element) -> Dict[str, str]:
        """Extract ifl:property elements from extensionElements"""
        properties = {}
        ext_elements = element.find('bpmn2:extensionElements', self.NAMESPACES)
        if ext_elements is not None:
            for prop in ext_elements.findall('.//ifl:property', self.NAMESPACES):
                key_elem = prop.find('key')
                value_elem = prop.find('value')
                if key_elem is not None and value_elem is not None:
                    key = key_elem.text or ''
                    value = self._extract_value_content(value_elem)
                    if key:
                        properties[key] = value
        return properties

    def _extract_value_content(self, value_elem: ET.Element) -> str:
        """Extract property value preserving plain text, CDATA, and nested XML."""
        if value_elem is None:
            return ''

        text_value = (value_elem.text or '').strip()
        if text_value:
            return html_module.unescape(text_value)

        if list(value_elem):
            parts = []
            for child in value_elem:
                parts.append(ET.tostring(child, encoding='unicode', method='xml'))
            return html_module.unescape(''.join(parts).strip())

        return ''

    def _extract_event_definitions(self, element: ET.Element) -> List[str]:
        """Extract event definition types (error, timer, message, escalation, etc.)"""
        definitions = []
        for child in element:
            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if tag.endswith('EventDefinition'):
                definitions.append(tag.replace('EventDefinition', ''))
        return definitions

    def _extract_sequence_flows(self, process: ET.Element) -> List[Dict[str, Any]]:
        """Extract sequence flows (connections between components)"""
        flows = []

        for flow in process.findall('.//bpmn2:sequenceFlow', self.NAMESPACES):
            flows.append({
                'id': flow.get('id', ''),
                'name': flow.get('name', ''),
                'source': flow.get('sourceRef', ''),
                'target': flow.get('targetRef', ''),
                'condition': self._extract_condition(flow)
            })

        return flows

    def _extract_condition(self, flow: ET.Element) -> str:
        """Extract condition expression from sequence flow"""
        condition_elem = flow.find('bpmn2:conditionExpression', self.NAMESPACES)
        if condition_elem is not None and condition_elem.text:
            return condition_elem.text.strip()
        return ''

    def _extract_message_flows(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract message flows (connections to external systems)"""
        message_flows = []

        for msg_flow in root.findall('.//bpmn2:messageFlow', self.NAMESPACES):
            properties = {}
            ext_elements = msg_flow.find('bpmn2:extensionElements', self.NAMESPACES)
            if ext_elements is not None:
                for prop in ext_elements.findall('.//ifl:property', self.NAMESPACES):
                    key_elem = prop.find('key')
                    value_elem = prop.find('value')
                    if key_elem is not None and value_elem is not None:
                        key = key_elem.text or ''
                        value = self._extract_value_content(value_elem)
                        if key:
                            properties[key] = value

            message_flows.append({
                'id': msg_flow.get('id', ''),
                'name': msg_flow.get('name', ''),
                'source': msg_flow.get('sourceRef', ''),
                'target': msg_flow.get('targetRef', ''),
                'properties': properties
            })

        return message_flows