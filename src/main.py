#!/usr/bin/env python3
"""
SAP CPI iFlow Analyzer - Main Entry Point
"""
import sys
import argparse
from pathlib import Path
from analyzer.iflow_parser import IFlowParser
from analyzer.component_extractor import ComponentExtractor
from analyzer.flow_builder import FlowBuilder
from analyzer.complexity_analyzer import ComplexityAnalyzer
from generators.json_exporter import JSONExporter
from generators.html_generator import HTMLGenerator
from generators.text_generator import TextGenerator


def print_summary_table(complexity_report: dict, raw_data: dict):
    """Print a structured summary to the terminal"""
    print("\n" + "=" * 80)
    print("📊  ANALYSIS SUMMARY")
    print("=" * 80)
    print(f"  iFlow File       : {raw_data.get('filename', 'Unknown')}")
    print(f"  Processes        : {len(raw_data.get('processes', []))}")
    print(f"  Participants     : {len(raw_data.get('participants', []))}")
    print(f"  Message Flows    : {len(raw_data.get('message_flows', []))}")
    print()
    print(f"  Total Components : {complexity_report['total_components']}")
    print(f"  Groovy Scripts   : {complexity_report['script_count']}")
    print(f"  Routers          : {complexity_report['router_count']}")
    print(f"  Content Modifiers: {complexity_report['content_modifier_count']}")
    print(f"  Request-Reply    : {complexity_report['request_reply_count']}")
    print()
    print(f"  Adapters Used    : {', '.join(complexity_report['adapter_types']) or 'None detected'}")
    print(f"  Complexity       : {complexity_report['label']} (score: {complexity_report['score']}/100)")
    print(f"  Error Handling   : {'✅ Yes' if complexity_report['has_error_handler'] else '❌ Not detected'}")

    if complexity_report['warnings']:
        print(f"\n  ⚠️  Warnings ({len(complexity_report['warnings'])}):")
        for w in complexity_report['warnings']:
            icon = '🔴' if w['severity'] == 'high' else ('🟡' if w['severity'] == 'medium' else '🔵')
            print(f"     {icon} {w['title']}")

    if complexity_report['recommendations']:
        print(f"\n  💡 Recommendations:")
        for r in complexity_report['recommendations']:
            print(f"     → {r}")
    print("=" * 80)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='SAP CPI iFlow Analyzer - Analyze and visualize SAP Integration iFlows',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/main.py my_iflow.zip
  python src/main.py ./extracted_iflow_folder
  python src/main.py my_iflow.zip --output-dir ./reports
  python src/main.py my_iflow.zip --no-text --verbose
        """
    )
    parser.add_argument('input', help='Path to iFlow ZIP file or extracted folder')
    parser.add_argument('--output-dir', '-o', default='output', help='Output directory (default: output)')
    parser.add_argument('--no-html', action='store_true', help='Skip HTML visualization generation')
    parser.add_argument('--no-text', action='store_true', help='Skip text tree generation')
    parser.add_argument('--no-json', action='store_true', help='Skip JSON export generation')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show verbose output')

    args = parser.parse_args()
    input_path = args.input

    print(f"\n🔍 SAP CPI iFlow Analyzer")
    print(f"   Input : {input_path}")
    print(f"   Output: {args.output_dir}")
    print("=" * 80)

    # Step 1: Parse iFlow XML
    print("\n📄 Step 1: Parsing iFlow XML...")
    iflow_parser = IFlowParser()
    try:
        raw_data = iflow_parser.parse(input_path)
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    print(f"   ✅ iFlow: {raw_data.get('iflow_name', raw_data.get('filename', ''))}")
    print(f"   ✅ Processes  : {len(raw_data['processes'])}")
    print(f"   ✅ Participants: {len(raw_data['participants'])}")
    print(f"   ✅ Msg Flows  : {len(raw_data['message_flows'])}")

    # Step 2: Load Groovy scripts (folder-based iFlows)
    extractor = ComponentExtractor()
    is_zip = input_path.endswith('.zip')
    zip_path = input_path if is_zip else None

    if not is_zip:
        # Try loading scripts from folder
        print("\n📜 Step 2a: Loading Groovy scripts from folder...")
        extractor.load_scripts_from_folder(input_path)

    # Step 2b: Extract components
    print("\n🔧 Step 2: Extracting components...")
    normalized_components = extractor.extract(raw_data, zip_path)
    actual_comps = [c for c in normalized_components if c['type'] != 'SequenceFlow']
    print(f"   ✅ {len(actual_comps)} components extracted")

    # Step 3: Build flow tree
    print("\n🌳 Step 3: Building flow tree...")
    flow_builder = FlowBuilder()
    flow_tree = flow_builder.build(normalized_components)
    stats = flow_builder.get_statistics()
    print(f"   ✅ {len(flow_tree)} root node(s), {stats['total_sequence_flows']} sequence flows")

    # Step 4: Complexity analysis
    print("\n📊 Step 4: Analyzing complexity...")
    complexity_analyzer = ComplexityAnalyzer()
    complexity_report = complexity_analyzer.analyze(flow_tree, raw_data.get('processes', []))
    print(f"   ✅ Complexity: {complexity_report['label']} (score {complexity_report['score']}/100)")

    # Step 5: Generate outputs
    print("\n📝 Step 5: Generating outputs...")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    if not args.no_json:
        json_output = output_dir / 'iflow_analysis.json'
        json_exporter = JSONExporter()
        json_exporter.export(flow_tree, str(json_output), raw_data, complexity_report)
        print(f"   ✅ JSON  → {json_output}")

    if not args.no_text:
        text_output = output_dir / 'iflow_tree.txt'
        text_generator = TextGenerator()
        text_generator.generate(flow_tree, str(text_output))
        print(f"   ✅ Text  → {text_output}")

    if not args.no_html:
        html_output = output_dir / 'iflow_visualization.html'
        html_generator = HTMLGenerator()
        html_generator.generate(flow_tree, raw_data, str(html_output), complexity_report)
        print(f"   ✅ HTML  → {html_output}")

    # Print summary table
    print_summary_table(complexity_report, raw_data)

    if not args.no_html:
        html_output = output_dir / 'iflow_visualization.html'
        print(f"\n🌐 Open in browser: {html_output.absolute()}\n")


if __name__ == '__main__':
    main()