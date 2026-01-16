import xml.etree.ElementTree as ET
from typing import Dict, List, Any
import zipfile
from pathlib import Path


class IFlowParser:
    """Parses SAP CPI iFlow XML files and extracts BPMN structure"""
    
    NAMESPACES = {
        'bpmn2': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
        'ifl': 'http:///com.sap.ifl.model/Ifl.xsd',
        'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI'
    }
    
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
            # Find .iflw file
            iflw_files = [f for f in zip_ref.namelist() if f.endswith('.iflw')]
            
            if not iflw_files:
                raise ValueError("No .iflw file found in ZIP")
            
            # Read first .iflw file
            iflw_path = iflw_files[0]
            with zip_ref.open(iflw_path) as iflw_file:
                xml_content = iflw_file.read().decode('utf-8')
                self.filename = Path(iflw_path).name
                return self.parse_xml(xml_content)
    
    def parse_folder(self, folder_path: str) -> Dict[str, Any]:
        """Parse .iflw file from extracted folder"""
        folder = Path(folder_path)
        
        # Search for .iflw files
        iflw_files = list(folder.rglob('*.iflw'))
        
        if not iflw_files:
            raise ValueError(f"No .iflw file found in folder: {folder_path}")
        
        # Read first .iflw file
        iflw_file = iflw_files[0]
        with open(iflw_file, 'r', encoding='utf-8') as f:
            xml_content = f.read()
            self.filename = iflw_file.name
            return self.parse_xml(xml_content)
    
    def parse_xml(self, xml_content: str) -> Dict[str, Any]:
        """Parse iFlow XML content"""
        self.root = ET.fromstring(xml_content)
        
        return {
            'filename': self.filename,
            'participants': self._extract_participants(self.root),
            'processes': self._extract_processes(self.root),
            'message_flows': self._extract_message_flows(self.root)
        }
    
    def _extract_participants(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract all participants (senders/receivers)"""
        participants = []
        
        for participant in root.findall('.//bpmn2:participant', self.NAMESPACES):
            participant_id = participant.get('id', '')
            participant_name = participant.get('name', '')
            
            # Extract IFL component type
            ifl_type = participant.get('{http:///com.sap.ifl.model/Ifl.xsd}type', '')
            
            participants.append({
                'id': participant_id,
                'name': participant_name,
                'type': ifl_type,
                'category': self._categorize_participant(ifl_type)
            })
        
        return participants
    
    def _categorize_participant(self, participant_type: str) -> str:
        """Categorize participant as sender or receiver"""
        if 'EndpointSender' in participant_type:
            return 'sender'
        elif 'EndpointReceiver' in participant_type:
            return 'receiver'
        else:
            return 'unknown'
    
    def _extract_processes(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract all process flows"""
        processes = []
        
        for process in root.findall('.//bpmn2:process', self.NAMESPACES):
            process_id = process.get('id', '')
            process_name = process.get('name', '')
            
            # Extract all flow elements
            start_events = self._extract_components(process, 'bpmn2:startEvent')
            end_events = self._extract_components(process, 'bpmn2:endEvent')
            service_tasks = self._extract_components(process, 'bpmn2:serviceTask')
            call_activities = self._extract_components(process, 'bpmn2:callActivity')
            exclusive_gateways = self._extract_components(process, 'bpmn2:exclusiveGateway')
            sequence_flows = self._extract_sequence_flows(process)
            
            processes.append({
                'id': process_id,
                'name': process_name,
                'start_events': start_events,
                'end_events': end_events,
                'service_tasks': service_tasks,
                'call_activities': call_activities,
                'exclusive_gateways': exclusive_gateways,
                'sequence_flows': sequence_flows
            })
        
        return processes
    
    def _extract_components(self, process: ET.Element, component_type: str) -> List[Dict[str, Any]]:
        """Extract specific component types"""
        components = []
        
        for element in process.findall(f'.//{component_type}', self.NAMESPACES):
            component = {
                'id': element.get('id', ''),
                'name': element.get('name', ''),
                'type': component_type.split(':')[1],
                'properties': {}
            }
            
            # Extract extension elements (properties)
            ext_elements = element.find('bpmn2:extensionElements', self.NAMESPACES)
            if ext_elements is not None:
                for prop in ext_elements.findall('.//ifl:property', self.NAMESPACES):
                    # Properties have <key> and <value> child elements
                    key_elem = prop.find('key')
                    value_elem = prop.find('value')
                    
                    if key_elem is not None and value_elem is not None:
                        key = key_elem.text or ''
                        value = value_elem.text or ''
                        if key:  # Only store non-empty keys
                            component['properties'][key] = value
            
            components.append(component)
        
        return components
    
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
                        value = value_elem.text or ''
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