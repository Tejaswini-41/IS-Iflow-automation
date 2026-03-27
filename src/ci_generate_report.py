"""CI-friendly entry point to generate iFlow reports."""
import argparse
import os
from iflow_runner import analyze_iflow


def main():
    parser = argparse.ArgumentParser(
        description="Generate iFlow analysis reports for CI pipelines"
    )
    parser.add_argument("input", help="Path to iFlow ZIP file or extracted folder")
    parser.add_argument(
        "--output-dir",
        "-o",
        default="output",
        help="Output directory (default: output)",
    )
    parser.add_argument("--no-html", action="store_true", help="Skip HTML generation")
    parser.add_argument("--no-text", action="store_true", help="Skip text generation")
    parser.add_argument("--no-json", action="store_true", help="Skip JSON export")

    args = parser.parse_args()

    result = analyze_iflow(
        args.input,
        output_dir=args.output_dir,
        generate_html=not args.no_html,
        generate_text=not args.no_text,
        generate_json=not args.no_json,
        logger=print,
    )

    html_path = result.get("outputs", {}).get("html")
    if html_path:
        print(f"HTML report generated at: {html_path}")

    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path and html_path:
        with open(summary_path, "a", encoding="utf-8") as summary_file:
            summary_file.write("iFlow HTML report generated.\n")
            summary_file.write(f"Path: {html_path}\n")


if __name__ == "__main__":
    main()
