# SAP CPI iFlow Analyzer

This project is an offline SAP CPI iFlow Analyzer that parses iFlow files and generates a static HTML page visualizing the iFlow structure with detailed insights for each step.

## Project Structure

```
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
├── tests
│   ├── __init__.py
│   ├── test_iflow_parser.py
│   ├── test_groovy_analyzer.py
│   └── fixtures
│       ├── sample.iflw
│       └── sample.groovy
├── examples
│   └── sample_project
│       ├── src
│       │   └── main
│       │       └── resources
│       │           └── scenarioflows
│       │               └── integrationflow
│       └── script
├── output
│   └── .gitkeep
├── requirements.txt
├── setup.py
├── .gitignore
└── README.md
```

## Installation

To install the required dependencies, run:

```
pip install -r requirements.txt
```

## Usage

To analyze an iFlow project, run the following command:

```
python src/main.py <path_to_iflw_file_or_folder>
```

This will parse the specified iFlow files or folder and generate an HTML visualization of the iFlow structure.

## Features

- Parses `.iflw` files to extract flow structures.
- Analyzes Groovy scripts for key operations.
- Generates static HTML pages for visualizing the iFlow structure.
- Exports analysis results to JSON format.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.