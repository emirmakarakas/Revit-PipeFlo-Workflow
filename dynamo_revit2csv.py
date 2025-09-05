# Copyright(c) 2023, Autodesk Inc.
# All rights reserved.

import clr
import System
import csv

# Add Revit API references
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, BuiltInParameter, FamilySymbol
from Autodesk.Revit.DB.Plumbing import Pipe

# Add Revit Services references
clr.AddReference('RevitServices')
import RevitServices
from RevitServices.Persistence import DocumentManager

# Get the current Revit document
doc = DocumentManager.Instance.CurrentDBDocument

# --- Script Inputs ---
# IN[0]: A boolean toggle. Set to 'True' to run the script.
# IN[1]: File path for the output CSV.
run_script = IN[0]
csv_file_path = IN[1]

def export_pipe_data_to_csv(document, file_path):
    pipe_collector = FilteredElementCollector(document).OfClass(Pipe).WhereElementIsNotElementType()
    pipes = pipe_collector.ToElements()
    data_rows = []
    error_pipes = []

    if not pipes:
        return "No pipes found in the project."

    header = ['ElementId', 'StartX_m', 'StartY_m', 'StartZ_m', 'EndX_m', 'EndY_m', 'EndZ_m', 'SystemName', 'PipeRunID', 'SegmentName', 'Diameter_mm', 'ConnectedFittingNames']
    
    FEET_TO_METERS = 0.3048
    FEET_TO_MM = 304.8

    # Define the list of allowed fitting Part Types
    allowed_part_types = ["Elbow", "Tee", "Transition", "Cap", "Valve"]

    for pipe in pipes:
        try:
            element_id = pipe.Id.ToString()
            system_name = pipe.MEPSystem.Name if pipe.MEPSystem and pipe.MEPSystem.Name else "N/A"
            
            pipe_run_id = "N/A"
            param_pipe_run_id = pipe.LookupParameter("PipeRunID")
            if param_pipe_run_id and param_pipe_run_id.HasValue:
                pipe_run_id = param_pipe_run_id.AsString()

            segment_name = "N/A"
            segment_param = pipe.get_Parameter(BuiltInParameter.RBS_PIPE_SEGMENT_PARAM)
            if segment_param and segment_param.HasValue:
                segment_name = segment_param.AsValueString()

            diameter_mm = 0.0
            diameter_param = pipe.get_Parameter(BuiltInParameter.RBS_PIPE_DIAMETER_PARAM)
            if diameter_param:
                diameter_mm = diameter_param.AsDouble() * FEET_TO_MM

            location = pipe.Location
            if not (location and hasattr(location, 'Curve')):
                continue
            
            curve = location.Curve
            start_point = curve.GetEndPoint(0)
            end_point = curve.GetEndPoint(1)

            # --- MODIFICATION START ---
            unique_fittings = {}
            if pipe.ConnectorManager:
                for connector in pipe.ConnectorManager.Connectors:
                    for connected_ref in connector.AllRefs:
                        owner = connected_ref.Owner
                        # Check if the connected element is a fitting or accessory
                        if owner and owner.Category and (owner.Category.Id.IntegerValue == int(BuiltInCategory.OST_PipeFitting) or owner.Category.Id.IntegerValue == int(BuiltInCategory.OST_PipeAccessory)):
                            # Now, check the Part Type of the fitting's family
                            try:
                                family_instance = owner
                                symbol = family_instance.Symbol
                                # Get the Part Type parameter and check if it's in our allowed list
                                part_type_param = symbol.get_Parameter(BuiltInParameter.FAMILY_CONTENT_PART_TYPE)
                                if part_type_param and part_type_param.AsValueString() in allowed_part_types:
                                    if owner.Id not in unique_fittings:
                                        unique_fittings[owner.Id] = owner.Name
                            except:
                                # If any error occurs trying to get Part Type, just skip the fitting
                                continue

            # Format the collected fittings into a "Name[ID]" string
            fitting_details_list = ["{}[{}]".format(name, id.ToString()) for id, name in unique_fittings.items()]
            fitting_names_str = ";".join(fitting_details_list)
            # --- MODIFICATION END ---
            
            data_rows.append([
                element_id,
                start_point.X * FEET_TO_METERS, start_point.Y * FEET_TO_METERS, start_point.Z * FEET_TO_METERS,
                end_point.X * FEET_TO_METERS, end_point.Y * FEET_TO_METERS, end_point.Z * FEET_TO_METERS,
                system_name,
                pipe_run_id,
                segment_name,
                round(diameter_mm, 2),
                fitting_names_str
            ])
        except Exception:
            error_pipes.append(pipe.Id.ToString())
            continue

    # --- Sorting Logic ---
    if data_rows:
        system_name_index = header.index('SystemName')
        pipe_run_id_index = header.index('PipeRunID')
        data_rows.sort(key=lambda row: (row[system_name_index], row[pipe_run_id_index]))

    try:
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)
            writer.writerows(data_rows)
        return "Successfully exported raw data for {} pipes.".format(len(data_rows))
    except Exception as e:
        return "Error writing to CSV file: {}".format(str(e))

if run_script:
    OUT = export_pipe_data_to_csv(doc, csv_file_path)
else:
    OUT = "Set 'True' to run."