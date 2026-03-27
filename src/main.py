#!/usr/bin/env python3
"""
SAP CPI iFlow Analyzer - Main Entry Point
"""
import sys
import argparse
from pathlib import Path
from iflow_runner import analyze_iflow


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

    try:
        result = analyze_iflow(
            input_path,
            output_dir=args.output_dir,
            generate_html=not args.no_html,
            generate_text=not args.no_text,
            generate_json=not args.no_json,
            logger=print,
        )
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    raw_data = result["raw_data"]
    complexity_report = result["complexity_report"]
    stats = result["stats"]
    outputs = result["outputs"]

    print(f"\n   ✅ iFlow: {raw_data.get('iflow_name', raw_data.get('filename', ''))}")
    print(f"   ✅ Processes  : {len(raw_data.get('processes', []))}")
    print(f"   ✅ Participants: {len(raw_data.get('participants', []))}")
    print(f"   ✅ Msg Flows  : {len(raw_data.get('message_flows', []))}")
    print(f"   ✅ {stats['actual_components']} components extracted")
    print(f"   ✅ {stats['root_nodes']} root node(s), {stats['total_sequence_flows']} sequence flows")
    print(f"   ✅ Complexity: {complexity_report['label']} (score {complexity_report['score']}/100)")

    if "json" in outputs:
        print(f"   ✅ JSON  → {outputs['json']}")
    if "text" in outputs:
        print(f"   ✅ Text  → {outputs['text']}")
    if "html" in outputs:
        print(f"   ✅ HTML  → {outputs['html']}")

    # Print summary table
    print_summary_table(complexity_report, raw_data)

    if "html" in outputs:
        html_output = Path(outputs["html"])
        print(f"\n🌐 Open in browser: {html_output.absolute()}\n")


if __name__ == '__main__':
    main()