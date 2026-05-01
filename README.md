# FCA Expert MCP Server
A powerful Formal Concept Analysis (FCA) server for MCP-compatible clients (Claude, OpenCode, etc.). This tool allows LLMs to perform mathematical data clustering, identify logical implications, and navigate hierarchical structures within binary and numeric datasets.

## Manual Installation Guide
1. Prerequisites
* Python 3.10+
* Graphviz (Optional, required for lattice visualization)
   * macOS: brew install graphviz
   * Ubuntu: sudo apt-get install graphviz
   * Windows: choco install graphviz

2. Setup
Clone the repository and install the dependencies:
```Bash
git clone https://github.com/your-username/fca-mcp-server.git
cd fca-mcp-server
python3 -m venv venv
```
You can now perform a basic installation:
```Bash
venv/bin/pip install .
```
Or a development installation:
```Bash
venv/bin/pip install -e ".[dev]"
```

### How to Run Tests
The project includes a comprehensive test suite covering all tools from data ingestion to delta analysis.

```Bash
# Run all tests with verbose output
venv/bin/pytest test_fca_expert.py -v
```

### Configuring MCP Clients
**Claude Desktop / Claude Code**
Add the following to your `claude_desktop_config.json`:
```JSON
{
  "mcpServers": {
    "fca-expert": {
      "command": "python",
      "args": ["/path/to/fca-mcp-server/main.py"]
    }
  }
}
```
Or something like this:
```JSON
{
  "mcpServers": {
    "fca-expert": {
      "command": "/path/to/fca-mcp-server/venv/bin/python",
      "args": ["/path/to/fca-mcp-server/main.py"]
    }
  }
}
```

**OpenCode / IDEs**
1. Open your MCP Settings in the IDE.
2. Add a new Python-based MCP server.
3. Point the entry file to main.py.

**MCPHost**
Create a config file for MCPHost:
```JSON
{
  "mcpServers": {
    "fca-expert": {
      "type": "local",
      "command": [
      	"/path/to/fca-mcp-server/venv/bin/python3", 
      	"/path/to/fca-mcp-server/main.py"
	]
    }
  }
}
```
Run MCPHost with this config file:
```Bash
export OLLAMA_HOST=http://127.0.0.1:11434
mcphost -m ollama:qwen3.5:9b --config .mcphost.json
```

## Example LLM Prompts
Once the server is connected, try these prompts to test the various functionalities:
1. Data Ingestion & Scaling
```
I have a binary dataset of animals.
object,predator,mammal,flying
lion,1,1,0
shark,1,0,0
pigeon,0,0,1
bat,1,1,1
Please upload this to the FCA server. Once it is loaded, prune the lattice with 0.0 minimum support and describe the top 3 most stable concepts you find.
```

2. Logical Extraction
```
Based on the animal data currently loaded in the session, what are the strict logical implications? After that, calculate the probabilistic association rules with a minimum confidence of 0.5. Explain the difference between the hard and soft rules you found.
```

3. Redundancy & Navigation
```
I want to clean up this data. Are there any attribute reducts we can apply to simplify the lattice? Also, start at the 'Top' concept and navigate down one level to show me its immediate sub-categories.
```

4. The Advanced Numeric Test (Scaling & Snapshots)
```
Clear the current FCA session. I have new RPG character data:
object,strength,speed
warrior,80,40
rogue,30,90
mage,10,20
Upload this data, but you must scale 'strength' into bins [0, 50, 100] and 'speed' into bins [0, 50, 100]. Once uploaded, save this state as a snapshot named 'V1'. Then, tell me what binary attributes were generated.
```

5. Showing the Lattice
```
Show the lattice. Print the absolute complete, raw, unedited string. Do NOT truncate it, do NOT summarize it, and do NOT use comments like '// Additional connections'. I need every single character of the output.
```

## Core FCA Concepts for Users
* Extent: The set of objects that belong to a concept.
* Intent: The set of attributes shared by all objects in that concept.
* Stability: A metric (0-1) indicating how robust a concept is. High stability means the concept represents a significant pattern, not noise.
* Implication: A strict rule ($A \implies B$) found in the data where every object having attribute A also possesses attribute B.
* Reduct: The minimum set of attributes needed to represent the data without losing any logical structure.

## Key Tools Included
Tool                    | Description
------------------------|--------------------------------------------------------------
`upload_from_csv`       | Ingests data with optional numeric/categorical scaling.
`Maps_lattice`          | Move up/down the hierarchy to explore data subsets.
`get_attribute_reducts` | Simplifies the dataset by removing redundant columns.
`get_association_rules` | Finds probabilistic "soft" rules in the data.
`snapshot_and_compare`  | Tracks how concepts change between two different data states.
`get_lattice_dot`       | Generates a Hasse diagram for visualization.

## License
MIT
