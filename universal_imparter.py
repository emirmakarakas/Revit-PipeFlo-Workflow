import csv
import os
import json

# This section runs first, creating the 'config' object.
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_filepath = os.path.join(script_dir, 'config.json')
    with open(config_filepath, 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    print("FATAL ERROR: 'config.json' was not found. Please ensure it is in the same folder as the script.")
    exit()

# --- User Settings ---
TEMPLATE_PIPE_NAME = config['template_pipe_name']
FITTING_MAP_CSV = config['fitting_map_path']
PROCESSED_DATA_CSV = config['processed_data_path']

def get_flo_fitting_name(revit_name, keyword_map):
    for keyword, flo_name in keyword_map.items():
        if keyword in revit_name:
            return flo_name
    return None

def safe_float(value, default=None):
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def initialize_system_data_by_type():
    updates = 0
    errors = 0
    fitting_library = {}
    fitting_keyword_map = {}

    # --- Load Fitting Keyword Map ---
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        map_filepath = os.path.join(script_dir, FITTING_MAP_CSV)
        with open(map_filepath, 'r') as map_file:
            reader = csv.reader(map_file)
            next(reader)
            for row in reader:
                if row and len(row) >= 2:
                    fitting_keyword_map[row[0].strip()] = row[1].strip()
            print(f"Successfully loaded {len(fitting_keyword_map)} mappings from '{FITTING_MAP_CSV}'.")
    except FileNotFoundError:
        print(f"INFO: The fitting map file '{FITTING_MAP_CSV}' was not found. Will attempt to use fitting names directly.")

    # --- Build Fitting Library ---
    try:
        print(f"Building fitting library from '{TEMPLATE_PIPE_NAME}'...")
        template_pipe = pipeflo().doc().get_pipe(TEMPLATE_PIPE_NAME)
        fittings_on_template = template_pipe.get_installed_fittings()

        if not fittings_on_template:
            print(f"WARNING: No fittings found on the template pipe '{TEMPLATE_PIPE_NAME}'. No fittings can be installed.")
        else:
            for fitting in fittings_on_template:
                fitting_library[fitting.description] = fitting
            print(f"Library built successfully with {len(fitting_library)} fittings.")

    except RuntimeError:
        print(f"WARNING: The template pipe named '{TEMPLATE_PIPE_NAME}' was not found. The script will continue, but no fittings will be installed.")

    # --- Process Main CSV File ---
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        csv_filepath = os.path.join(script_dir, PROCESSED_DATA_CSV)

        with open(csv_filepath, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            next(reader)

            print('Starting system initialization...')

            for row_num, data_row in enumerate(reader, 2):
                if not any(field.strip() for field in data_row):
                    continue

                try:
                    device_type = data_row[0].strip().lower()

                    # ---------------- PIPE ----------------
                    if device_type == 'pipe':
                        name = data_row[1].strip()
                        if not name:
                            continue
                        try:
                            pipe_obj = pipeflo().doc().get_pipe(name)
                        except RuntimeError:
                            print(f'ERROR (Row {row_num}): Did not find pipe: {name}')
                            errors += 1
                            continue

                        pipe_updated_successfully = False

                        # Update Length
                        length_val = safe_float(data_row[3].strip()) if len(data_row) > 3 else None
                        if length_val is not None:
                            try:
                                pipe_obj.set_length(length(length_val, meters_length))
                                pipe_updated_successfully = True
                            except Exception as e:
                                print(f'ERROR (Row {row_num}, Pipe {name}): Could not set length. Details: {e}')
                                errors += 1

                        # Update Specification
                        if len(data_row) > 4 and data_row[4].strip():
                            try:
                                pipe_obj.set_specification(data_row[4].strip())
                                pipe_updated_successfully = True
                            except Exception as e:
                                print(f'ERROR (Row {row_num}, Pipe {name}): Could not set specification. Details: {e}')
                                errors += 1

                        # Update Size
                        if len(data_row) > 5 and data_row[5].strip():
                            try:
                                pipe_obj.set_pipe_size(data_row[5].strip() + ' mm')
                                pipe_updated_successfully = True
                            except Exception as e:
                                print(f'ERROR (Row {row_num}, Pipe {name}): Could not set size. Details: {e}')
                                errors += 1

                        # Update Fittings
                        if len(data_row) > 6 and data_row[6].strip() and fitting_library:
                            fittings_to_install = []
                            revit_fitting_names = [fname.strip() for fname in data_row[6].split(';')]
                            for revit_name in revit_fitting_names:
                                pipeflo_name = fitting_keyword_map.get(revit_name) or get_flo_fitting_name(revit_name, fitting_keyword_map) or revit_name
                                fitting_obj = fitting_library.get(pipeflo_name)
                                if fitting_obj:
                                    fittings_to_install.append(fitting_obj)
                                else:
                                    print(f'WARNING (Row {row_num}, Pipe {name}): Fitting "{pipeflo_name}" not found in template.')
                            if fittings_to_install:
                                try:
                                    pipe_obj.set_installed_fittings(fittings_to_install)
                                    pipe_updated_successfully = True
                                except Exception as e:
                                    print(f'ERROR (Row {row_num}, Pipe {name}): Failed to set fittings. Details: {e}')
                                    errors += 1

                        if pipe_updated_successfully:
                            print(f"Updated Pipe: {name}")
                            updates += 1

                    # ---------------- NODE ----------------
                    elif device_type == 'node':
                        name = data_row[1].strip()
                        elev_val = safe_float(data_row[2].strip()) if len(data_row) > 2 else None
                        if name and elev_val is not None:
                            try:
                                node_obj = pipeflo().doc().get_node(name)
                                node_obj.set_elevation(elevation(elev_val, meters_elevation))
                                print(f"Updated Node: {name}")
                                updates += 1
                            except Exception as e:
                                print(f'ERROR (Row {row_num}): Could not update node {name}. Details: {e}')
                                errors += 1

                    # ---------------- HEATSOURCESINK ----------------
                    elif device_type == 'heatsourcesink':
                        name = data_row[1].strip()
                        if not name:
                            continue
                        try:
                            hss_obj = pipeflo().doc().get_heat_source_sink(name)

                            inlet_val = safe_float(data_row[7].strip()) if len(data_row) > 7 else None
                            if inlet_val is not None:
                                hss_obj.set_inlet_elevation(elevation(inlet_val, meters_elevation))

                            outlet_val = safe_float(data_row[8].strip()) if len(data_row) > 8 else None
                            if outlet_val is not None:
                                hss_obj.set_outlet_elevation(elevation(outlet_val, meters_elevation))

                            fcd_name_str = data_row[9].strip() if len(data_row) > 9 else ""
                            if fcd_name_str:
                                hss_obj.set_linked_device(device_link(fcd_name_str))

                            temp_tol_val = safe_float(data_row[10].strip()) if len(data_row) > 10 else None
                            if temp_tol_val is not None:
                                hss_obj.set_temperature_tolerance(temperature_tolerance(temp_tol_val, kelvin_delta))

                            if len(data_row) > 11 and data_row[11].strip():
                                heat_transfer_rate_val = safe_float(data_row[12].strip())
                                thermal_flow_rate_val = safe_float(data_row[13].strip())
                                flow_rate_source_bool = (data_row[14].strip().upper() == 'TRUE') if len(data_row) > 14 else False
                                mode = data_row[11].strip()

                                if heat_transfer_rate_val is not None and thermal_flow_rate_val is not None:
                                    if mode == 'calculate_heat_transfer_rate':
                                        calc_mode_obj = calculate_heat_transfer_rate
                                    elif mode == 'calculate_flow_rate':
                                        calc_mode_obj = calculate_flow_rate
                                    else:
                                        calc_mode_obj = None

                                    if calc_mode_obj:
                                        hss_obj.set_thermal_calculation(thermal_calculation(
                                            calc_mode_obj,
                                            heat_transfer_rate(heat_transfer_rate_val, kw_htr),
                                            flow_rate(thermal_flow_rate_val, m3hr),
                                            flow_rate_source_bool
                                        ))

                            print(f"Updated HeatSourceSink: {name}")
                            updates += 1
                        except Exception as e:
                            print(f'ERROR (Row {row_num}): Could not update heat source/sink {name}. Details: {e}')
                            errors += 1

                    # ---------------- LINEUP ----------------
                    elif device_type == 'lineup':
                        lineupname_ = data_row[1].strip()
                        if lineupname_:
                            try:
                                pipeflo().doc().set_current_lineup(lineupname_)
                                print(f"Set active lineup to: {lineupname_}")
                                updates += 1
                            except Exception as e:
                                print(f'ERROR (Row {row_num}): Could not update lineup {lineupname_}. Details: {e}')
                                errors += 1

                    # ---------------- CONTROLVALVE ----------------
                    elif device_type == 'controlvalve':
                        name = data_row[1].strip()
                        if not name:
                            continue
                        try:
                            cv_obj = pipeflo().doc().get_control_valve(name)

                            elev_val = safe_float(data_row[2].strip()) if len(data_row) > 2 else None
                            if elev_val is not None:
                                cv_obj.set_elevation(elevation(elev_val, meters_elevation))

                            cv_mode_str = data_row[15].strip().lower() if len(data_row) > 15 else ""
                            cv_setpoint_val = safe_float(data_row[16].strip()) if len(data_row) > 16 else None
                            if cv_mode_str and cv_setpoint_val is not None:
                                if cv_mode_str == 'flow_rate':
                                    op_obj = operation(flow_rate(cv_setpoint_val, m3hr))
                                elif cv_mode_str == 'temperature_control':
                                    op_obj = operation(temperature_control)
                                else:
                                    op_obj = None
                                if op_obj:
                                    cv_obj.set_operation(op_obj)

                            min_dp_val = safe_float(data_row[17].strip()) if len(data_row) > 17 else None
                            if min_dp_val is not None:
                                cv_obj.set_min_dp(dp(min_dp_val, kPa))

                            max_dp_val = safe_float(data_row[18].strip()) if len(data_row) > 18 else None
                            if max_dp_val is not None:
                                cv_obj.set_max_dp(dp(max_dp_val, kPa))

                            print(f"Updated Control Valve: {name}")
                            updates += 1
                        except Exception as e:
                            print(f'ERROR (Row {row_num}): Could not update control valve {name}. Details: {e}')
                            errors += 1

                except Exception as e:
                    print(f'ERROR (Row {row_num}): Invalid row {data_row}. Details: {e}')
                    errors += 1

    except FileNotFoundError:
        print(f"FATAL ERROR: The processed data file '{PROCESSED_DATA_CSV}' was not found.")
        return

    print('-------------------------------------------')
    print('Full System Initialization Complete.')
    print(f'Updates: {updates}')
    print(f'Errors: {errors}')
    print('-------------------------------------------')

initialize_system_data_by_type()
