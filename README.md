# 📊 SAP CPI iFlow Analyzer (IS-iFlow-Automation)

> **An enterprise-grade, offline analysis and documentation tool for SAP Cloud Platform Integration (CPI) iFlows.**

The SAP CPI iFlow Analyzer is a robust Python-based utility that extracts, parses, and provides deep insights into CPI integration flows directly from source code without requiring live tenant access. It processes exported `.iflw` files or packaged `.zip` archives to generate interactive HTML visualizations, complexity metrics, and static documentation.

---

## 🎯 Value Proposition

Integrating this tool into our enterprise development lifecycle provides several key advantages:

- **Automated Documentation:** Instantly generates interactive HTML visualizers, ASCII structure trees, and JSON API models representing complex iFlow configurations.
- **Quality Assurance & Code Review:** Automatically calculates an iFlow "Complexity Score" (out of 100). It surfaces warnings regarding missing error handling setups, excessive Groovy script usage, and deeply nested routing—allowing developers to refactor _before_ deployment.
- **Faster Onboarding:** Quickly untangle large, legacy integrations. New developers can utilize the visualizer's dynamic subflow call-graph highlights and searchable nodes to understand data flow instantly.
- **Native CI/CD Integration:** Runs completely offline. Integrate it into Jenkins, GitLab, or GitHub Actions pipelines to generate build-time integration reports or automatically gate pull requests based on complexity thresholds.

---

## ✨ Core Features

- **Multi-Format Processing:** Natively parses individual `.iflw` BPMN properties, entirely packaged `.zip` archives, or locally extracted workspace folders.
- **Deep Complexity Analysis:** Evaluates component usage (Routers, Content Modifiers, Adapters, Script structures), detects Exception Subflow handlers, formats scorecards, and provides actionable tuning recommendations.
- **Groovy Script Inspection:** Automatically correlates script nodes with physical Groovy files, parsing them securely to extract key operational insights within the context of the flow.
- **Interactive HTML Visualization:** Compiles an offline, self-contained HTML page featuring:
  - Dynamic runtime data binding for maximum responsive speeds.
  - Live component text searching with node/connection context framing.
  - Visual subflow call-path tracking.
- **Multiple Artifact Generators:**
  - Generates comprehensive `.json` schemas of all parsed metrics for custom automation chains.
  - Emits terminal-friendly ASCII text trees of the structural architecture.
  - Granular CLI controls (`--no-html`, `--no-text`, `--no-json`) for optimized batch execution.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip (Python package installer)

### Installation

Clone the repository and install the standard dependencies:

```bash
git clone <repository_url>
cd IS-Iflow-automation
pip install -r requirements.txt
```

---

## 💻 Usage & CLI Guide

To analyze an iFlow project, pass the path of the `.zip` archive or extracted directory to the core processor:

```bash
python src/main.py <path_to_iflw_zip_or_folder>
```

### Advanced Examples

Generate all reports (JSON, HTML View, Text) into a specific CI artifacts folder:

```bash
python src/main.py my_iflow.zip --output-dir ./reports
```

Run purely for console complexity validation (ideal for fast CI gating), skipping file generations:

```bash
python src/main.py ./extracted_src_folder --no-html --no-json --verbose
```

**Available CLI Flags:**

- `--output-dir`, `-o`: Output directory destination (default: `output/`).
- `--no-html`: Skip rendering the interactive HTML visualization page.
- `--no-text`: Skip standard output structural text tree generation.
- `--no-json`: Skip `.json` metric data export generation.
- `--verbose`, `-v`: Display verbose runtime processing logs.

---

## 📁 Architecture & Project Structure

The project is built on a modular extractor-generator architecture:

- **`analyzer/`**: Core BPMN parsing engine (`iflow_parser.py`), component metadata tagging (`component_extractor.py`), and heuristic scoring methodologies (`complexity_analyzer.py`).
- **`generators/`**: Interprets the intermediate representations into target formats (`html_generator.py`, `json_exporter.py`).
- **`templates/`**: Hosts the core dynamic HTML frame (`visualization.html`) built for offline portability.

```text
sap-cpi-iflow-analyzer
├── src
│   ├── __init__.py
│   ├── analyzer
│   │   ├── __init__.py
│   │   ├── iflow_parser.py
│   │   ├── groovy_analyzer.py
│   │   ├── component_extractor.py
│   │   └── flow_builder.py
│   ├── generators
│   │   ├── __init__.py
│   │   ├── html_generator.py
│   │   ├── json_exporter.py
│   │   └── text_generator.py
│   ├── templates
│   │   ├── __init__.py
│   │   └── visualization.html
│   └── main.py
├── output
│   └── .gitkeep
├── requirements.txt
├── setup.py
├── .gitignore
└── README.md

```

## 🤝 Contributing

Contributions are welcome. Please ensure that updates to internal parsing mechanisms are accompanied by relevant unit checks in the `tests/` directory prior to opening a Pull Request.

## 📄 License

This enterprise template complies with the MIT License policies. See the LICENSE file for formal details.
