import csv
import os
import json

# --- User Settings ---
# In your PIPE-FLO model, create a pipe with this exact name.
# Manually add ALL the fittings you will use in your CSV to this one pipe.
TEMPLATE_PIPE_NAME = config['template_pipe_name']
# The name of the CSV file containing the fitting keyword map.
FITTING_MAP_CSV = config['fitting_map_path']
PROCESSED_DATA_CSV = config['processed_data_path']

def get_flo_fitting_name(revit_name, keyword_map):
    """
    Finds the corresponding PIPE-FLO fitting name by checking if any keyword 
    from the map is present in the Revit fitting name.
    
    Args:
        revit_name (str): The name of the fitting from the Revit CSV.
        keyword_map (dict): The dictionary mapping keywords to PIPE-FLO names.
        
    Returns:
        str or None: The PIPE-FLO name if a match is found, otherwise None.
    """
    for keyword, flo_name in keyword_map.items():
        if keyword in revit_name:
            return flo_name
    return None

def initialize_system_data_by_type():
    """
    Reads a CSV file to update the PIPE-FLO model, handling sparse data.
    """
    updates = 0
    errors = 0
    fitting_library = {}
    fitting_keyword_map = {}

    # --- NEW: Load Fitting Keyword Map from CSV ---
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        map_filepath = os.path.join(script_dir, FITTING_MAP_CSV)
        with open(map_filepath, 'r') as map_file:
            reader = csv.reader(map_file)
            next(reader) # Skip header
            for row in reader:
                if row and len(row) >= 2:
                    fitting_keyword_map[row[0].strip()] = row[1].strip()
        print(f"Successfully loaded {len(fitting_keyword_map)} mappings from '{FITTING_MAP_CSV}'.")
    except FileNotFoundError:
        print(f"FATAL ERROR: The fitting map file '{FITTING_MAP_CSV}' was not found. Please create it.")
        return
    # --------------------------------------------------
    
    try:
        print(f"Building fitting library from '{TEMPLATE_PIPE_NAME}'...")
        template_pipe = pipeflo().doc().get_pipe(TEMPLATE_PIPE_NAME)
        fittings_on_template = template_pipe.get_installed_fittings()
        
        if not fittings_on_template:
            print(f"FATAL ERROR: No fittings found on the template pipe '{TEMPLATE_PIPE_NAME}'. Please add fittings to it.")
            return

        for fitting in fittings_on_template:
            fitting_library[fitting.description] = fitting
        
        print(f"Library built successfully with {len(fitting_library)} fittings.")
        
    except RuntimeError:
        print(f"FATAL ERROR: The template pipe named '{TEMPLATE_PIPE_NAME}' was not found. Please create it.")
        return
    
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        csv_filepath = os.path.join(script_dir, PROCESSED_DATA_CSV)

        with open(csv_filepath, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',') 
            next(reader)  # Skip header row
            
            print('Starting system initialization...')
            
            for row_num, data_row in enumerate(reader, 2):
                if not any(field.strip() for field in data_row):
                    continue

                try:
                    device_type = data_row[0].strip().lower()

                    if device_type == 'pipe':
                        name = data_row[1].strip()
                        if not name: continue

                        # --- MODIFICATION 1: Find the pipe first and fail early if it doesn't exist ---
                        try:
                            pipe_obj = pipeflo().doc().get_pipe(name)
                        except RuntimeError:
                            print(f'ERROR (Row {row_num}): Did not find pipe: {name}')
                            errors += 1
                            continue # Skip to the next row in the CSV

                        # If we get here, the pipe was found.
                        # Now we'll update each property individually.
                        pipe_updated_successfully = False

                        # --- MODIFICATION 2: Update each property in its own try/except block ---

                        # Update Length
                        try:
                            length_str = data_row[3].strip()
                            if length_str:
                                pipe_obj.set_length(length(float(length_str), meters_length))
                                pipe_updated_successfully = True
                        except (ValueError, RuntimeError) as e:
                            print(f'ERROR (Row {row_num}, Pipe {name}): Could not set length. Invalid value "{length_str}". Details: {e}')
                            errors += 1
                        
                        # Update Specification
                        try:
                            spec_str = data_row[4].strip()
                            if spec_str:
                                pipe_obj.set_specification(spec_str)
                                pipe_updated_successfully = True
                        except RuntimeError as e:
                            print(f'ERROR (Row {row_num}, Pipe {name}): Could not set specification to "{spec_str}". Does it exist in PIPE-FLO? Details: {e}')
                            errors += 1

                        # Update Size
                        try:
                            size_str = data_row[5].strip()
                            if size_str:
                                pipe_obj.set_pipe_size(size_str + ' mm')
                                pipe_updated_successfully = True
                        except RuntimeError as e:
                            # For context, get the spec name for a better error message
                            spec_str = pipe_obj.specification()
                            print(f'ERROR (Row {row_num}, Pipe {name}): Could not set size to "{size_str}". Is it a valid size for spec "{spec_str}"? Details: {e}')
                            errors += 1

                        # Update Fittings (This logic is already robust but is now in its own block)
                        try:
                            fittings_list_str = data_row[6].strip()
                            if fittings_list_str:
                                fittings_to_install = []
                                revit_fitting_names = [fname.strip() for fname in fittings_list_str.split(';')]

                                for revit_name in revit_fitting_names:
                                    pipeflo_name = get_flo_fitting_name(revit_name, fitting_keyword_map)
                                    if pipeflo_name:
                                        fitting_obj = fitting_library.get(pipeflo_name)
                                        if fitting_obj:
                                            fittings_to_install.append(fitting_obj)
                                        else:
                                            # Specific error for a fitting not in the template library
                                            print(f'ERROR (Row {row_num}, Pipe {name}): Fitting "{pipeflo_name}" not found in the template library. Please add it to "{TEMPLATE_PIPE_NAME}".')
                                            errors += 1
                                    else:
                                        # Specific error for a fitting keyword that doesn't match
                                        print(f'ERROR (Row {row_num}, Pipe {name}): Revit fitting "{revit_name}" did not match any keyword in "{FITTING_MAP_CSV}".')
                                        errors += 1
                                
                                if fittings_to_install:
                                    pipe_obj.set_installed_fittings(fittings_to_install)
                                    pipe_updated_successfully = True
                        except RuntimeError as e:
                            print(f'ERROR (Row {row_num}, Pipe {name}): A critical error occurred while setting fittings. Details: {e}')
                            errors += 1

                        # --- MODIFICATION 3: Report success at the end ---
                        if pipe_updated_successfully:
                            print(f"Updated Pipe: {name}")
                            updates += 1
                    
                    elif device_type == 'node':
                        name = data_row[1].strip()
                        elevation_str = data_row[2].strip()
                        if name and elevation_str:
                            try:
                                node_obj = pipeflo().doc().get_node(name)
                                node_obj.set_elevation(elevation(float(elevation_str), meters_elevation))
                                print(f"Updated Node: {name}")
                                updates += 1
                            except RuntimeError:
                                print(f'ERROR (Row {row_num}): Did not find node: {name}')
                                errors += 1
                    
                    elif device_type == 'heatsourcesink':
                        name = data_row[1].strip()
                        if not name: continue

                        try:
                            hss_obj = pipeflo().doc().get_heat_source_sink(name)
                            
                            inlet_elev_str = data_row[7].strip()
                            if inlet_elev_str:
                                hss_obj.set_inlet_elevation(elevation(float(inlet_elev_str), meters_elevation))

                            outlet_elev_str = data_row[8].strip()
                            if outlet_elev_str:
                                hss_obj.set_outlet_elevation(elevation(float(outlet_elev_str), meters_elevation))

                            fcd_name_str = data_row[9].strip()
                            if fcd_name_str:
                                hss_obj.set_linked_device(device_link(fcd_name_str))

                            temp_tol_str = data_row[10].strip()
                            if temp_tol_str:
                                hss_obj.set_temperature_tolerance(temperature_tolerance(float(temp_tol_str), kelvin_delta))
                            
                            thermal_calc_mode_str = data_row[11].strip()
                            if thermal_calc_mode_str:
                                heat_transfer_rate_val = float(data_row[12])
                                thermal_flow_rate_val = float(data_row[13])
                                flow_rate_source_bool = data_row[14].strip().upper() == 'TRUE'
                                
                                calc_mode_obj = None
                                if thermal_calc_mode_str == 'calculate_heat_transfer_rate':
                                    calc_mode_obj = calculate_heat_transfer_rate
                                elif thermal_calc_mode_str == 'calculate_flow_rate':
                                    calc_mode_obj = calculate_flow_rate

                                if calc_mode_obj:
                                    hss_obj.set_thermal_calculation(thermal_calculation(
                                        calc_mode_obj, 
                                        heat_transfer_rate(heat_transfer_rate_val, kw_htr), 
                                        flow_rate(thermal_flow_rate_val, m3hr), 
                                        flow_rate_source_bool
                                    ))
                            
                            print(f"Updated HeatSourceSink: {name}")
                            updates += 1
                        except RuntimeError:
                            print(f'ERROR (Row {row_num}): Did not find heat source/sink: {name}')
                            errors += 1

                    elif device_type == 'lineup':
                        lineupname_ = data_row[1].strip()
                        if lineupname_:
                            try:
                                pipeflo().doc().set_current_lineup(lineupname_)
                                print(f"Set active lineup to: {lineupname_}")
                                updates += 1
                            except RuntimeError:
                                print(f'ERROR (Row {row_num}): Did not find lineup: {lineupname_}')
                                errors += 1

                    elif device_type == 'controlvalve':
                        name = data_row[1].strip()
                        if not name: continue

                        try:
                            cv_obj = pipeflo().doc().get_control_valve(name)
                            
                            elevation_str = data_row[2].strip()
                            if elevation_str:
                                cv_obj.set_elevation(elevation(float(elevation_str), meters_elevation))
                            
                            cv_mode_str = data_row[15].strip().lower()
                            cv_setpoint_str = data_row[16].strip()

                            if cv_mode_str and cv_setpoint_str:
                                op_obj = None
                                setpoint_val = float(cv_setpoint_str)
                                
                                if cv_mode_str == 'flow_rate':
                                    op_obj = operation(flow_rate(setpoint_val, m3hr))
                                elif cv_mode_str == 'temperature_control':
                                    op_obj = operation(temperature_control)
                                
                                if op_obj:
                                    cv_obj.set_operation(op_obj)
                                else:
                                    print(f"WARNING (Row {row_num}): Unknown cv_mode '{data_row[15]}' for {name}.")
                            min_dp_str = data_row[17].strip()
                            if min_dp_str:
                                cv_obj.set_min_dp(dp(float(min_dp_str), kPa))
                            
                            max_dp_str = data_row[18].strip()
                            if max_dp_str:
                                cv_obj.set_max_dp(dp(float(max_dp_str), kPa))

                            print(f"Updated Control Valve: {name}")
                            updates += 1
                        except RuntimeError:
                            print(f'ERROR (Row {row_num}): Did not find Control Valve: {name}')
                            errors += 1
                
                except (ValueError, IndexError) as e:
                    print(f'ERROR (Row {row_num}): Invalid data format. Row: {data_row}. Details: {e}')
                    errors += 1
    
    except FileNotFoundError:
        print(f'FATAL ERROR: The CSV file was not found.')
        return
        
    print('-------------------------------------------')
    print('Full System Initialization Complete.')
    print(f'Updates: {updates}')
    print(f'Errors: {errors}')
    print('-------------------------------------------')

# Call the main function
initialize_system_data_by_type()
