import pytest
from main import mcp, state
import json

# --- TEST DATA ---
# Use a slightly more complex set to ensure a multi-layered lattice
BINARY_CSV = """object,predator,mammal,flying,nocturnal
lion,1,1,0,0
shark,1,0,0,0
pigeon,0,0,1,0
bat,1,1,1,1
owl,1,0,1,1
"""

NUMERIC_CSV = """object,strength,speed
warrior,80,40
rogue,30,90
mage,10,20
"""

@pytest.fixture(autouse=True)
async def cleanup():
    await mcp.call_tool("clear_session")
    yield

# Helper to get the raw return value from ToolResult
def unwrap(result):
    # FastMCP ToolResult has a .content list of objects
    # We want the text inside the first content block
    raw_text = result.content[0].text
    try:
        data = json.loads(raw_text)
        # If FastMCP wrapped it in another 'text' key inside JSON:
        if isinstance(data, dict) and "text" in data:
            return json.loads(data["text"])
        return data
    except (json.JSONDecodeError, TypeError):
        return raw_text

@pytest.mark.asyncio
async def test_upload_and_concepts():
    await mcp.call_tool("upload_from_csv", arguments={"csv_data": BINARY_CSV})
    raw_concepts = await mcp.call_tool("get_pruned_lattice", arguments={"min_support": 0.0})
    concepts = unwrap(raw_concepts)
    assert len(concepts) > 0
    assert any("lion" in c["extent_preview"] for c in concepts)

@pytest.mark.asyncio
async def test_numeric_scaling():
    bins = {"strength": [0, 50, 100]}
    await mcp.call_tool("upload_from_csv", arguments={
        "csv_data": NUMERIC_CSV,
        "numeric_bins": bins
    })
    # State check is direct, no unwrapping needed
    assert "strength:0-50" in state.context.properties
    assert "strength:50-100" in state.context.properties

@pytest.mark.asyncio
async def test_lattice_navigation():
    await mcp.call_tool("upload_from_csv", arguments={"csv_data": BINARY_CSV})
    
    # Get all concepts first to find the one with the empty intent (the TOP)
    raw_concepts = await mcp.call_tool("get_pruned_lattice", arguments={"min_support": 0.0})
    concepts = unwrap(raw_concepts)
    
    # Find the 'Top' concept (the one with no attributes/intent)
    top_concept = next(c for c in concepts if len(c["intent"]) == 0)
    top_id = top_concept["id"]

    raw_nav = await mcp.call_tool("navigate_lattice", arguments={"concept_id": top_id, "direction": "down"})
    nav = unwrap(raw_nav)
    
    assert nav["direction"] == "down"
    assert len(nav["neighbors"]) > 0

@pytest.mark.asyncio
async def test_attribute_reducts():
    redundant_data = "object,mammal,has_fur\ndog,1,1\ncat,1,1\nfish,0,0"
    await mcp.call_tool("upload_from_csv", arguments={"csv_data": redundant_data})
    raw_reducts = await mcp.call_tool("get_attribute_reducts")
    reducts = unwrap(raw_reducts)
    assert len(reducts["essential"]) == 1
    assert len(reducts["redundant"]) == 1

@pytest.mark.asyncio
async def test_implications():
    await mcp.call_tool("upload_from_csv", arguments={"csv_data": BINARY_CSV})
    raw_rules = await mcp.call_tool("get_implications")
    rules = unwrap(raw_rules)
    
    assert isinstance(rules, list)
    
    # Print the rules if the test fails so you can see the format
    # (Use 'pytest -s' to see this output)
    print(f"\nGenerated Rules: {rules}")
    
    # Check if 'mammal' implies 'predator'
    # We use lower() and string search to be safe
    found = False
    for r in rules:
        if "mammal" in r.lower() and "predator" in r.lower():
            found = True
            break
            
    assert found, f"Expected mammal -> predator implication, but got: {rules}"

@pytest.mark.asyncio
async def test_association_rules():
    await mcp.call_tool("upload_from_csv", arguments={"csv_data": BINARY_CSV})
    raw_rules = await mcp.call_tool("get_association_rules", arguments={"min_confidence": 0.5})
    rules = unwrap(raw_rules)
    assert len(rules) > 0
    assert "conf" in rules[0]

@pytest.mark.asyncio
async def test_delta_snapshots():
    await mcp.call_tool("upload_from_csv", arguments={"csv_data": "obj,attr\nA,1"})
    await mcp.call_tool("snapshot_and_compare", arguments={"name": "Q1"})
    await mcp.call_tool("upload_from_csv", arguments={"csv_data": "obj,attr\nA,1\nB,1"})
    await mcp.call_tool("snapshot_and_compare", arguments={"name": "Q2"})
    
    raw_comparison = await mcp.call_tool("snapshot_and_compare", arguments={
        "name": "Q2", 
        "compare_to": "Q1"
    })
    comparison = unwrap(raw_comparison)
    assert "Comparing" in comparison

@pytest.mark.asyncio
async def test_dot_generation():
    await mcp.call_tool("upload_from_csv", arguments={"csv_data": BINARY_CSV})
    raw_dot = await mcp.call_tool("get_lattice_dot")
    dot = unwrap(raw_dot)
    # Graphviz DOT often starts with comments or the word 'digraph'
    assert "digraph" in dot or "graph" in dot
    
@pytest.mark.asyncio
async def test_mermaid_generation():
    """Test that the Mermaid.js graph syntax is generated correctly."""
    await mcp.call_tool("upload_from_csv", arguments={"csv_data": BINARY_CSV})
    
    # Call the new Mermaid tool (no arguments needed)
    raw_mermaid = await mcp.call_tool("get_lattice_mermaid")
    mermaid_code = unwrap(raw_mermaid)
    
    # Verify it returns standard Mermaid syntax
    assert isinstance(mermaid_code, str)
    assert "graph BT" in mermaid_code, "Mermaid code should start with the 'graph BT' directive"
    assert "-->" in mermaid_code, "Mermaid code should contain edge connections (-->)"
    
    # Ensure it parsed at least a few concepts
    assert "c0" in mermaid_code
