import pandas as pd
import numpy as np
import json
import math
from collections import defaultdict, deque

# --- Define normalizer first ---
def normalize_path(path_str):
    """
    Accepts either:
    - Absolute Windows path with single backslashes,
    - Path with forward slashes,
    - Just a filename.
    Returns a fully normalized absolute path.
    """
    if not path_str:
        return path_str

    # Make sure we treat the script folder as base if only filename provided
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Replace single backslashes with forward slashes
    fixed = path_str.replace('\\', '/')

    # If it’s just a filename, join with script_dir
    if not os.path.isabs(fixed):
        fixed = os.path.join(script_dir, fixed)

    # Collapse any .. and normalize slashes
    return os.path.normpath(fixed)

# --- Load config.json ---
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_filepath = os.path.join(script_dir, 'config.json')
    with open(config_filepath, 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    print("FATAL ERROR: 'config.json' was not found. Please ensure it is in the same folder as the script.")
    exit()

input_csv_path = normalize_path(config['revit_export_path'])
output_csv_path = normalize_path(config['processed_data_path'])

# --- 1. Define the target header structure ---
output_columns = [
    'device_type', 'name', 'elevation', 'length', 'spec', 'size', 'fittings',
    'inlet elevation', 'outlet elevation', 'Flow Control Device', 'Temp Tolerance',
    'Thermal Calculation Mode', 'Heat Transfer Rate', 'Thermal Flow Rate',
    'Source', 'Control Valve model', 'Control Valve setpoint', 'Control Valve min dP',
    'Control Valve max dP'
]

# --- 2. Load and process the raw data from Dynamo ---
try:
    df = pd.read_csv(input_csv_path)
except FileNotFoundError:
    print(f"Error: Input file from Dynamo ('{input_csv_path}') not found.")
    print("Please ensure you have run the Dynamo script first.")
    exit()

# --- 3. Helper Functions ---
def calculate_length(row):
    """Calculates the 3D length of a pipe segment."""
    return np.sqrt(
        (row['EndX_m'] - row['StartX_m'])**2 +
        (row['EndY_m'] - row['StartY_m'])**2 +
        (row['EndZ_m'] - row['StartZ_m'])**2
    )

def aggregate_fittings(series):
    """
    Aggregates all unique fitting instances from a run and returns a
    semi-colon separated string of their names.
    """
    unique_fittings_with_id = set()
    for item in series:
        if isinstance(item, str):
            for fitting in item.split(';'):
                if fitting:
                    unique_fittings_with_id.add(fitting.strip())
    fitting_names = []
    for unique_fitting in sorted(list(unique_fittings_with_id)):
        name_part = unique_fitting.split('[')[0]
        fitting_names.append(name_part)
    return "; ".join(fitting_names)

def _snap_point(pt, tol=0.001):
    """Snap a coordinate to a tolerance grid to merge near-coincident points."""
    return (round(pt[0]/tol)*tol, round(pt[1]/tol)*tol, round(pt[2]/tol)*tol)

def find_run_end_elevations(group, tol=0.001):
    """
    Determine start/end elevations for a PipeRunID, accounting for fittings.
    """
    # --- Single-segment run: just return its actual endpoints ---
    if len(group) == 1:
        row = group.iloc[0]
        return row['StartZ_m'], row['EndZ_m']

    adj = defaultdict(set)
    node_z = {}

    for _, row in group.iterrows():
        p1 = _snap_point((row['StartX_m'], row['StartY_m'], row['StartZ_m']), tol)
        p2 = _snap_point((row['EndX_m'], row['EndY_m'], row['EndZ_m']), tol)
        node_z[p1] = p1[2]
        node_z[p2] = p2[2]

        adj[p1].add(p2)
        adj[p2].add(p1)

        fittings = row['ConnectedFittingNames']
        if isinstance(fittings, str) and fittings.strip():
            for f in fittings.split(';'):
                f = f.strip()
                if f:
                    adj[p1].add(f); adj[f].add(p1)
                    adj[p2].add(f); adj[f].add(p2)
                    # approximate fitting elevation as average of connected ends
                    node_z[f] = (p1[2] + p2[2]) / 2

    if not adj:
        return 0.0, 0.0

    degrees = {n: len(neigh) for n, neigh in adj.items()}
    endpoints = [n for n,d in degrees.items() if d == 1]

    def farthest_pair(start_node):
        seen = {start_node: 0}
        q = deque([start_node])
        farthest = start_node
        while q:
            u = q.popleft()
            for v in adj[u]:
                if v not in seen:
                    seen[v] = seen[u] + 1
                    q.append(v)
                    if seen[v] > seen[farthest]:
                        farthest = v
        return farthest, seen

    if len(endpoints) >= 2:
        a, _ = farthest_pair(endpoints[0])
        b, _ = farthest_pair(a)
        za, zb = node_z[a], node_z[b]
        return (za, zb) if za <= zb else (zb, za)

    # fallback for loops or messy runs: return vertical range
    zs = [z for z in node_z.values()]
    return (min(zs), max(zs))

# --- 4. Process and Aggregate the Data ---
df['CalculatedLength_m'] = df.apply(calculate_length, axis=1)

grouped = df.groupby('PipeRunID')

aggregated_data = grouped.agg(
    TotalLength=('CalculatedLength_m', 'sum'),
    Spec=('SegmentName', lambda x: x.mode().iloc[0] if not x.mode().empty else np.nan),
    Size=('Diameter_mm', lambda x: x.mode().iloc[0] if not x.mode().empty else np.nan),
    Fittings=('ConnectedFittingNames', aggregate_fittings)
).reset_index()

elevation_data = grouped.apply(find_run_end_elevations).reset_index(name='elevations')
elevation_data[['StartElevation_m', 'EndElevation_m']] = pd.DataFrame(
    elevation_data['elevations'].tolist(), index=elevation_data.index
)

final_aggregated_df = pd.merge(
    aggregated_data,
    elevation_data[['PipeRunID', 'StartElevation_m', 'EndElevation_m']],
    on='PipeRunID'
)

# --- 5. Create the Pipe and Node DataFrames ---
pipe_data = []
node_data = []

for _, row in final_aggregated_df.iterrows():
    pipe_entry = {
        'device_type': 'pipe',
        'name': row['PipeRunID'],
        'length': row['TotalLength'],
        'spec': row['Spec'],
        'fittings': row['Fittings'],
        'size': row['Size']
    }
    pipe_data.append(pipe_entry)

    start_node = {
        'device_type': 'node',
        'name': f"{row['PipeRunID']}_StartNode",
        'elevation': row['StartElevation_m']
    }
    end_node = {
        'device_type': 'node',
        'name': f"{row['PipeRunID']}_EndNode",
        'elevation': row['EndElevation_m']
    }
    node_data.extend([start_node, end_node])

pipe_output_df = pd.DataFrame(pipe_data, columns=output_columns)
node_output_df = pd.DataFrame(node_data, columns=output_columns)


# --- 6. Combine and Save ---
final_output_df = pd.concat([pipe_output_df, node_output_df], ignore_index=True).fillna('')

# --- MODIFICATION: Get and print the unique fittings list ---
all_fittings_series = df['ConnectedFittingNames'].dropna().str.split(';').explode()
unique_fitting_names = all_fittings_series.str.split('[').str[0].str.strip().unique()
all_fittings_str = "; ".join(sorted(unique_fitting_names))

try:
    final_output_df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
    print(f" Successfully created formatted CSV file: '{output_csv_path}'")
    print("\n--- Final Data Preview ---")
    print(final_output_df.head(10))
    
    print("\n--- Unique Fittings Reference List ---")
    print(f"Here is a clean list of all unique fittings found in the Revit export:\n\n{all_fittings_str}")


except Exception as e:
    print(f" An error occurred while writing the file: {e}")
    