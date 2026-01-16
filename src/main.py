#!/usr/bin/env python3
"""
SAP CPI iFlow Analyzer - Main Entry Point
"""
import sys
from pathlib import Path
from analyzer.iflow_parser import IFlowParser
from analyzer.component_extractor import ComponentExtractor
from analyzer.flow_builder import FlowBuilder
from generators.json_exporter import JSONExporter
from generators.html_generator import HTMLGenerator
from generators.text_generator import TextGenerator


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python src/main.py <path_to_iflow_zip_or_folder>")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    print(f"📊 Analyzing SAP CPI iFlow: {input_path}")
    print("=" * 80)
    
    # Step 1: Parse iFlow XML
    print("\n🔍 Step 1: Parsing iFlow XML...")
    iflow_parser = IFlowParser()
    raw_data = iflow_parser.parse(input_path)
    print(f"✅ Found {len(raw_data['processes'])} process(es)")
    print(f"✅ Found {len(raw_data['participants'])} participant(s)")
    
    # Step 2: Extract and normalize components
    print("\n🔍 Step 2: Extracting components...")
    component_extractor = ComponentExtractor()
    # Pass zip path if input is a zip file for Groovy script loading
    zip_path = input_path if input_path.endswith('.zip') else None
    normalized_components = component_extractor.extract(raw_data, zip_path)
    print(f"✅ Extracted {len(normalized_components)} component(s)")
    
    # Step 3: Build flow tree structure
    print("\n🔍 Step 3: Building flow tree...")
    flow_builder = FlowBuilder()
    flow_tree = flow_builder.build(normalized_components)
    print(f"✅ Built flow tree with {len(flow_tree)} root node(s)")
    
    # Step 4: Generate outputs
    print("\n📝 Step 4: Generating outputs...")
    
    # Create output directory
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    # Generate JSON
    json_output = output_dir / 'iflow_analysis.json'
    json_exporter = JSONExporter()
    json_exporter.export(flow_tree, str(json_output))
    print(f"✅ JSON exported to: {json_output}")
    
    # Generate text tree
    text_output = output_dir / 'iflow_tree.txt'
    text_generator = TextGenerator()
    text_generator.generate(flow_tree, str(text_output))
    print(f"✅ Text tree exported to: {text_output}")
    
    # Generate HTML visualization
    html_output = output_dir / 'iflow_visualization.html'
    html_generator = HTMLGenerator()
    html_generator.generate(flow_tree, raw_data, str(html_output))
    print(f"✅ HTML visualization exported to: {html_output}")
    
    print("\n" + "=" * 80)
    print("✅ Analysis complete!")
    print(f"🌐 Open {html_output.absolute()} in your browser to view the interactive visualization.")


if __name__ == '__main__':
    main()