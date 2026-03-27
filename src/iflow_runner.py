"""
Shared analysis pipeline for iFlow processing.
"""
from pathlib import Path
from analyzer.iflow_parser import IFlowParser
from analyzer.component_extractor import ComponentExtractor
from analyzer.flow_builder import FlowBuilder
from analyzer.complexity_analyzer import ComplexityAnalyzer
from generators.json_exporter import JSONExporter
from generators.html_generator import HTMLGenerator
from generators.text_generator import TextGenerator


def analyze_iflow(
    input_path: str,
    output_dir: str = "output",
    generate_html: bool = True,
    generate_text: bool = True,
    generate_json: bool = True,
    logger=None,
):
    """Run the iFlow analysis pipeline and return results and output paths."""

    def log(message: str):
        if logger:
            logger(message)

    log("Parsing iFlow XML...")
    iflow_parser = IFlowParser()
    raw_data = iflow_parser.parse(input_path)

    extractor = ComponentExtractor()
    is_zip = input_path.endswith(".zip")
    zip_path = input_path if is_zip else None

    if not is_zip:
        log("Loading Groovy scripts from folder...")
        extractor.load_scripts_from_folder(input_path)

    log("Extracting components...")
    normalized_components = extractor.extract(raw_data, zip_path)
    actual_components = [c for c in normalized_components if c.get("type") != "SequenceFlow"]

    log("Building flow tree...")
    flow_builder = FlowBuilder()
    flow_tree = flow_builder.build(normalized_components)
    stats = flow_builder.get_statistics()

    log("Analyzing complexity...")
    complexity_analyzer = ComplexityAnalyzer()
    complexity_report = complexity_analyzer.analyze(flow_tree, raw_data.get("processes", []))

    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(exist_ok=True)

    outputs = {}
    if generate_json:
        json_output = output_dir_path / "iflow_analysis.json"
        JSONExporter().export(flow_tree, str(json_output), raw_data, complexity_report)
        outputs["json"] = str(json_output)

    if generate_text:
        text_output = output_dir_path / "iflow_tree.txt"
        TextGenerator().generate(flow_tree, str(text_output))
        outputs["text"] = str(text_output)

    if generate_html:
        html_output = output_dir_path / "iflow_visualization.html"
        HTMLGenerator().generate(flow_tree, raw_data, str(html_output), complexity_report)
        outputs["html"] = str(html_output)

    return {
        "raw_data": raw_data,
        "flow_tree": flow_tree,
        "complexity_report": complexity_report,
        "stats": {
            "root_nodes": len(flow_tree),
            "total_sequence_flows": stats.get("total_sequence_flows", 0),
            "actual_components": len(actual_components),
        },
        "outputs": outputs,
    }
