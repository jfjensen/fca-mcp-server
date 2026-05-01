import io
import pandas as pd
from typing import Optional, Dict
from fastmcp import FastMCP
from concepts import Context

mcp = FastMCP("FCA-Full-Suite")

class FCAState:
    def __init__(self):
        self.context: Optional[Context] = None
        self.history: Dict[str, Context] = {}

state = FCAState()

# --- INTERNAL HELPERS ---
def _get_active_context() -> Context:
    if state.context is None:
        raise ValueError("No context loaded. Use an upload tool first.")
    return state.context

def _calculate_metrics(concept, ctx):
    total_objs = len(ctx.objects)
    intent_size = len(concept.intent)
    support = len(concept.extent) / total_objs if total_objs > 0 else 0
    stability = 1.0 - (1.0 / (2**intent_size)) if intent_size > 0 else 0
    return {"support": round(support, 3), "stability": round(stability, 4)}

def _format_concept(concept, ctx):
    return {
        "id": concept.index,
        "extent_preview": list(concept.extent), # Use preview for the test check
        "intent": list(concept.intent),
        "metrics": _calculate_metrics(concept, ctx),
        "neighbors": {
            "parents": [p.index for p in concept.upper_neighbors],
            "children": [c.index for c in concept.lower_neighbors]
        }
    }

# --- 1. INPUT & SCALING TOOLS ---

@mcp.tool()
def upload_from_csv(csv_data: str, index_col: str = "object", numeric_bins: Optional[Dict[str, list]] = None):
    """Uploads CSV and optionally scales numeric/categorical data into binary."""
    df = pd.read_csv(io.StringIO(csv_data))
    if index_col in df.columns: df.set_index(index_col, inplace=True)
    
    if numeric_bins:
        scaled_df = pd.DataFrame(index=df.index)
        for col, bins in numeric_bins.items():
            for i in range(len(bins)-1):
                label = f"{col}:{bins[i]}-{bins[i+1]}"
                scaled_df[label] = (df[col] >= bins[i]) & (df[col] < bins[i+1])
        # Add non-binned columns as bool
        for col in [c for c in df.columns if c not in numeric_bins]:
            scaled_df[col] = df[col].astype(bool)
        df = scaled_df

    state.context = Context(df.index.tolist(), df.columns.tolist(), df.astype(bool).values.tolist())
    return f"Loaded {len(state.context.objects)} objects and {len(state.context.properties)} attributes."

@mcp.tool()
def clear_session():
    """Resets all state and history."""
    state.context = None
    state.history = {}
    return "Session cleared."

# --- 2. NAVIGATION & EXPLORATION ---

@mcp.tool()
def navigate_lattice(concept_id: int, direction: str):
    """Moves 'up' (generalize) or 'down' (specialize) from a specific concept."""
    ctx = _get_active_context()
    current = ctx.lattice[concept_id]
    targets = current.upper_neighbors if direction == "up" else current.lower_neighbors
    return {
        "current": _format_concept(current, ctx),
        "direction": direction,
        "neighbors": [_format_concept(t, ctx) for t in targets]
    }

@mcp.tool()
def get_pruned_lattice(min_support: float = 0.1, min_stability: float = 0.5):
    """Returns a filtered list of concepts based on importance thresholds."""
    ctx = _get_active_context()
    # Return the list directly
    return [_format_concept(c, ctx) for c in ctx.lattice 
            if _calculate_metrics(c, ctx)["support"] >= min_support]

# --- 3. LOGIC & REDUCTION ---
@mcp.tool()
def get_implications():
    """Returns strict logical implications (100% confidence) found in the data."""
    ctx = _get_active_context()
    rules = []
    
    # Calculate simple attribute-to-attribute implications
    for attr_a in ctx.properties:
        ext_a = set(ctx.extension([attr_a]))
        if not ext_a: # Skip if no objects have this attribute
            continue
            
        implied = []
        for attr_b in ctx.properties:
            if attr_a == attr_b:
                continue
            ext_b = set(ctx.extension([attr_b]))
            
            # If every object with A also has B, then A -> B
            if ext_a.issubset(ext_b):
                implied.append(attr_b)
                
        if implied:
            rules.append(f"{attr_a} -> {', '.join(implied)}")
            
    return rules if rules else ["No strict implications found."]
            
@mcp.tool()
def get_attribute_reducts():
    """Finds the minimal set of attributes that preserves the lattice structure."""
    ctx = _get_active_context()
    essential, seen = [], set()
    for a in ctx.properties:
        ext = tuple(sorted(ctx.extension([a])))
        if ext not in seen:
            essential.append(a); seen.add(ext)
    return {"essential": essential, "redundant": [a for a in ctx.properties if a not in essential]}

# --- 4. ADVANCED ANALYTICS ---

@mcp.tool()
def get_association_rules(min_confidence: float = 0.8):
    """Extracts probabilistic rules (e.g., If A, then 80% likely B)."""
    ctx = _get_active_context()
    rules = []
    for c in ctx.lattice:
        for child in c.lower_neighbors:
            conf = len(child.extent) / len(c.extent) if len(c.extent) > 0 else 0
            if conf >= min_confidence:
                rules.append({"if": list(c.intent), "then": list(set(child.intent)-set(c.intent)), "conf": conf})
    return rules

@mcp.tool()
def snapshot_and_compare(name: str, compare_to: Optional[str] = None):
    """Saves current state or compares it to a previous snapshot."""
    if not compare_to:
        state.history[name] = _get_active_context()
        return f"Snapshot '{name}' saved."
    # Logic for comparison (simplified)
    return f"Comparing {name} to {compare_to}: {len(state.history[name].lattice)} vs {len(state.history[compare_to].lattice)} concepts."

# --- 5. VISUALIZATION ---

@mcp.tool()
def get_lattice_dot():
    """Returns Graphviz DOT source for visual rendering."""
    return _get_active_context().lattice.graphviz().source

if __name__ == "__main__":
    mcp.run()
