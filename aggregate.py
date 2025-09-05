import pandas as pd
import numpy as np
from itertools import combinations
import json


with open('config.json', 'r') as f:
    config = json.load(f)

input_csv_path = config['revit_export_path']
output_csv_path = config['processed_data_path']

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

# --- 3. Define Helper Functions ---
def calculate_length(row):
    """Calculates the 3D length of a pipe segment."""
    return np.sqrt(
        (row['EndX_m'] - row['StartX_m'])**2 +
        (row['EndY_m'] - row['StartY_m'])**2 +
        (row['EndZ_m'] - row['StartZ_m'])**2
    )

# --- MODIFICATION START ---
def aggregate_fittings(series):
    """
    Aggregates all unique fitting instances from a run and returns a
    semi-colon separated string of their names. A shared fitting connecting
    two pipes in the same run is counted only once.
    """
    unique_fittings_with_id = set()
    for item in series:
        if isinstance(item, str):
            for fitting in item.split(';'):
                if fitting:
                    unique_fittings_with_id.add(fitting.strip())
    
    # Now that we have unique instances (e.g., 'Elbow[123]', 'Elbow[456]'),
    # we extract just the names for the final list.
    fitting_names = []
    # Sort the list of unique instances for a consistent output order
    for unique_fitting in sorted(list(unique_fittings_with_id)):
        # Extract the name part before the '[' character
        name_part = unique_fitting.split('[')[0]
        fitting_names.append(name_part)
        
    return "; ".join(fitting_names)
# --- MODIFICATION END ---


def find_farthest_points_elevations(group):
    """
    Finds the two points that are farthest apart in 3D space for a group
    of pipe segments and returns their elevations.
    """
    points = []
    for _, row in group.iterrows():
        points.append((row['StartX_m'], row['StartY_m'], row['StartZ_m']))
        points.append((row['EndX_m'], row['EndY_m'], row['EndZ_m']))
    
    # Remove duplicate points to be more efficient
    unique_points = list(set(points))
    
    if len(unique_points) < 2:
        # Handle cases with a single point (e.g., a single zero-length pipe)
        return unique_points[0][2], unique_points[0][2]

    max_dist = -1
    farthest_pair = (None, None)

    # Find the pair of points with the maximum distance
    for p1, p2 in combinations(unique_points, 2):
        dist = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2 + (p2[2] - p1[2])**2)
        if dist > max_dist:
            max_dist = dist
            farthest_pair = (p1, p2)
            
    # Return the elevations (Z-coordinate) of the two farthest points
    return farthest_pair[0][2], farthest_pair[1][2]

# --- 4. Process and Aggregate the Data ---
df['CalculatedLength_m'] = df.apply(calculate_length, axis=1)

# Group by PipeRunID and apply custom aggregations
grouped = df.groupby('PipeRunID')

# Aggregate simple data first
aggregated_data = grouped.agg(
    TotalLength=('CalculatedLength_m', 'sum'),
    Spec=('SegmentName', lambda x: x.mode().iloc[0] if not x.mode().empty else np.nan),
    Size=('Diameter_mm', lambda x: x.mode().iloc[0] if not x.mode().empty else np.nan),
    Fittings=('ConnectedFittingNames', aggregate_fittings)
).reset_index()

# Now, find the elevations of the start and end points for each group
elevation_data = grouped.apply(find_farthest_points_elevations).reset_index(name='elevations')
elevation_data[['StartElevation_m', 'EndElevation_m']] = pd.DataFrame(elevation_data['elevations'].tolist(), index=elevation_data.index)

# Merge the aggregated data and elevation data
final_aggregated_df = pd.merge(aggregated_data, elevation_data[['PipeRunID', 'StartElevation_m', 'EndElevation_m']], on='PipeRunID')

# --- 5. Create the Pipe and Node DataFrames ---
pipe_data = []
node_data = []

for index, row in final_aggregated_df.iterrows():
    # Pipe Entry
    pipe_entry = {
        'device_type': 'pipe',
        'name': row['PipeRunID'],
        'length': row['TotalLength'],
        'spec': row['Spec'],
        'fittings': row['Fittings'],
        'size': row['Size']
    }
    pipe_data.append(pipe_entry)
    
    # Node Entries
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

try:
    final_output_df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
    print(f" Successfully created formatted CSV file: '{output_csv_path}'")
    print("\n--- Final Data Preview ---")
    print(final_output_df.head(10))
except Exception as e:
    print(f" An error occurred while writing the file: {e}")