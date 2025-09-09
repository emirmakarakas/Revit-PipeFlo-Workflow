import csv
import os
import copy

# --- Configuration Data ---

# Define the CSV headers based on the template.csv file.
HEADERS = [
    "device_type", "name", "elevation", "length", "spec", "size", "fittings",
    "inlet elevation", "outlet elevation", "Flow Control Device", "Temp Tolerance",
    "Thermal Calculation Mode", "Heat Transfer Rate", "Thermal Flow Rate", "Source",
    "Control Valve model", "Control Valve setpoint", "Control Valve min dP",
    "Control Valve max dP"
]

# Define the required parameters for each device type.
DEVICE_PARAMETERS = {
    "pipe": ["name", "length", "spec", "size", "fittings"],
    "node": ["name", "elevation"],
    "heatsourcesink": [
        "name", "inlet elevation", "outlet elevation", "Flow Control Device",
        "Temp Tolerance", "Thermal Calculation Mode", "Heat Transfer Rate",
        "Thermal Flow Rate", "Source"
    ],
    "controlvalve": [
        "name", "elevation", "Control Valve model", "Control Valve setpoint",
        "Control Valve min dP", "Control Valve max dP"
    ],
    "lineup": ["name"]
}

# --- Help and Guidance Texts ---

PARAMETER_HELP = {
    "name": "The exact name of the device in your Pipe-Flo model.",
    "length": "The total length of the pipe in METERS.",
    "spec": "The pipe's material specification (must match Pipe-Flo).",
    "size": "The nominal pipe diameter. The script adds 'mm' automatically.",
    "fittings": "A list of fittings, separated by a semicolon (;).",
    "elevation": "The device's elevation in METERS.",
    "inlet elevation": "The elevation of the device's inlet in METERS.",
    "outlet elevation": "The elevation of the device's outlet in METERS.",
    "Flow Control Device": "The name of a linked Flow Control Device in Pipe-Flo.",
    "Temp Tolerance": "The temperature tolerance value in KELVIN.",
    "Thermal Calculation Mode": "Determines how thermal properties are calculated.",
    "Heat Transfer Rate": "The heat transfer rate in KILOWATTS (kW).",
    "Thermal Flow Rate": "The flow rate for thermal calculations in CUBIC METERS PER HOUR (m³/hr).",
    "Source": "Enter 'yes' if the flow rate is a source, otherwise 'no'.",
    "Control Valve model": "The operational mode of the valve.",
    "Control Valve setpoint": "The target setpoint. Units depend on the valve model.",
    "Control Valve min dP": "Minimum design pressure drop in KILOPASCALS (kPa).",
    "Control Valve max dP": "Maximum design pressure drop in KILOPASCALS (kPa)."
}

PARAMETER_HINTS = {
    "spec": "e.g., Carbon Steel - Schedule 40",
    "fittings": "e.g., Std Elbow 90; Reducer; Butterfly Valve",
    "size": "e.g., 150",
    "length": "e.g., 55.4"
}

# --- Input Validation Rules ---

VALIDATION_RULES = {
    "Thermal Calculation Mode": ["calculate_heat_transfer_rate", "calculate_flow_rate"],
    "Control Valve model": ["flow_rate", "temperature_control"],
    "numeric": ["length", "elevation", "inlet elevation", "outlet elevation", "size",
                "Temp Tolerance", "Heat Transfer Rate", "Thermal Flow Rate",
                "Control Valve setpoint", "Control Valve min dP", "Control Valve max dP"],
    "boolean": ["Source"]
}


# --- UI and Display Functions ---

def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_data(data):
    """Displays the current CSV data in a formatted table."""
    if not data:
        print("CSV is currently empty.\n")
        return

    print("--- Current CSV Data ---")
    print(f"{'Row':<5}{'Device Type':<15}{'Name':<30}")
    print("-" * 50)
    for i, row in enumerate(data):
        print(f"{i+1:<5}{row.get('device_type', ''):<15}{row.get('name', ''):<30}")
    print("\n" + "=" * 50 + "\n")

def show_instructions():
    """Displays a detailed help message for the user."""
    clear_screen()
    print("""
    --- How to Use This Tool ---

    This application helps you build a CSV file for the Pipe-Flo import script.

    1.  **Add Device**: Choose this to add a new component like a pipe, node, or valve.
        The tool will guide you through the required parameters for that device.

    2.  **Contextual Help**: When prompted for any parameter, you can type '?'
        and press Enter to get a detailed explanation of what's required.
        
    3.  **Copy Device**: You can duplicate any existing row to quickly create a new, similar entry.

    4.  **Edit/Delete**: If you make a mistake, you can easily edit or delete any row
        you have previously entered.

    5.  **Save and Exit**: Once you are finished, this option will save your work
        to a CSV file in the same directory where this script is running.

    Press Enter to return to the main menu...
    """)
    input()


# --- Core Logic ---

def get_choice_from_options(param, options):
    """Presents a numbered menu for a list of options and returns the chosen string."""
    print(f"  - Please choose a '{param}':")
    for i, opt in enumerate(options):
        print(f"    {i+1}. {opt}")
    
    choice = ""
    while not choice.isdigit() or not 1 <= int(choice) <= len(options):
        choice = input(f"    Enter choice (1-{len(options)}): ")
    return options[int(choice)-1]

def get_validated_input(param):
    """Gets and validates user input for a specific parameter, showing a menu if applicable."""
    # Check if the parameter has a predefined list of choices
    if param in VALIDATION_RULES and param not in VALIDATION_RULES['numeric'] and param not in VALIDATION_RULES['boolean']:
        return get_choice_from_options(param, VALIDATION_RULES[param])

    # Otherwise, fall back to text-based input
    prompt = f"  - Enter value for '{param}'"
    if param in PARAMETER_HINTS:
        prompt += f" {PARAMETER_HINTS[param]}"
    prompt += ": "

    while True:
        value = input(prompt)
        if value.strip() == '?':
            print(f"      HELP: {PARAMETER_HELP.get(param, 'No details available.')}")
            continue

        # --- Validation Checks ---
        if param in VALIDATION_RULES['numeric']:
            if value.strip() == "": return ""
            try:
                float(value)
                return value
            except ValueError:
                print("      ERROR: This value must be a number.")
        elif param in VALIDATION_RULES['boolean']:
            if value.lower() in ['y', 'yes', 'true']: return 'TRUE'
            elif value.lower() in ['n', 'no', 'false', '']: return 'FALSE'
            else: print("      ERROR: Please enter 'yes' or 'no'.")
        else:
            return value

def add_device(data):
    """Guides the user to add a new device row with validation."""
    clear_screen()
    print("--- Add New Device ---")
    
    device_options = list(DEVICE_PARAMETERS.keys())
    for i, dtype in enumerate(device_options):
        print(f"{i+1}. {dtype}")
    
    choice = ""
    while not choice.isdigit() or not 1 <= int(choice) <= len(device_options):
        choice = input(f"Choose a device type (1-{len(device_options)}): ")
    
    device_type = device_options[int(choice)-1]
    
    new_row = {header: "" for header in HEADERS}
    new_row["device_type"] = device_type
    required_params = DEVICE_PARAMETERS[device_type]

    print(f"\nPlease provide the following parameters for '{device_type}'. Type '?' for help.")
    for param in required_params:
        new_row[param] = get_validated_input(param)

    data.append(new_row)
    print(f"\nSuccessfully added '{device_type}' device.")
    input("Press Enter to continue...")

def edit_device(data):
    """Allows the user to edit a specific row and field."""
    if not data:
        print("No data to edit.")
        input("Press Enter to continue...")
        return

    try:
        display_data(data)
        row_num_str = input("Enter the row number to edit (or 'c' to cancel): ")
        if row_num_str.lower() == 'c': return
        row_num = int(row_num_str)
        if not 1 <= row_num <= len(data):
            print("Invalid row number.")
            input("Press Enter to continue...")
            return

        row_index = row_num - 1
        selected_row = data[row_index]
        device_type = selected_row['device_type']
        
        print(f"\n--- Editing Row {row_num} (device_type: {device_type}) ---")
        
        relevant_params = ["device_type"] + DEVICE_PARAMETERS.get(device_type, [])
        for i, param in enumerate(relevant_params):
            print(f"  {i+1}. {param}: {selected_row.get(param, '')}")

        field_num_str = input("\nEnter the number of the field to edit (or 'c' to cancel): ")
        if field_num_str.lower() == 'c': return
        field_num = int(field_num_str)

        if not 1 <= field_num <= len(relevant_params):
            print("Invalid field number.")
            input("Press Enter to continue...")
            return
        
        field_to_edit = relevant_params[field_num - 1]
        
        print(f"\nCurrent value for '{field_to_edit}' is '{selected_row.get(field_to_edit, '')}'")
        new_value = get_validated_input(field_to_edit)

        if field_to_edit == 'device_type':
            if new_value.lower() in DEVICE_PARAMETERS:
                old_params = DEVICE_PARAMETERS.get(selected_row['device_type'], [])
                new_params = DEVICE_PARAMETERS.get(new_value.lower(), [])
                for p in old_params:
                    if p not in new_params:
                       selected_row[p] = ""
                selected_row['device_type'] = new_value.lower()
            else:
                print("Invalid new device_type. No change made.")
        else:
             selected_row[field_to_edit] = new_value
        
        print("\nRow updated successfully.")

    except ValueError:
        print("Invalid input. Please enter a number.")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    input("Press Enter to continue...")

def delete_device(data):
    """Deletes a specified row from the data."""
    if not data:
        print("No data to delete.")
        input("Press Enter to continue...")
        return
    try:
        display_data(data)
        row_num_str = input("Enter the row number to delete (or 'c' to cancel): ")
        if row_num_str.lower() == 'c': return
        
        row_num = int(row_num_str)
        if 1 <= row_num <= len(data):
            deleted_item = data.pop(row_num - 1)
            print(f"Successfully deleted row {row_num} (Device: {deleted_item.get('name', 'N/A')}).")
        else:
            print("Invalid row number.")
    except ValueError:
        print("Invalid input. Please enter a number.")
    input("Press Enter to continue...")

def copy_device(data):
    """Copies an existing row to create a new row."""
    if not data:
        print("No data to copy.")
        input("Press Enter to continue...")
        return
    try:
        display_data(data)
        row_num_str = input("Enter the row number to copy (or 'c' to cancel): ")
        if row_num_str.lower() == 'c': return

        row_num = int(row_num_str)
        if 1 <= row_num <= len(data):
            original_row = data[row_num - 1]
            new_row = copy.deepcopy(original_row)
            data.append(new_row)
            print(f"Successfully copied row {row_num}. A new row has been added at the end.")
        else:
            print("Invalid row number.")
    except ValueError:
        print("Invalid input. Please enter a number.")
    input("Press Enter to continue...")

def save_to_csv(data):
    """Saves the in-memory data to a CSV file."""
    if not data:
        print("No data to save.")
        input("Press Enter to continue...")
        return
    
    filename = input("Enter filename to save as (e.g., 'output.csv'): ")
    if not filename.endswith('.csv'): filename += '.csv'
        
    try:
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=HEADERS)
            writer.writeheader()
            writer.writerows(data)
        print(f"Data successfully saved to '{filename}'.")
    except IOError as e:
        print(f"Error saving file: {e}")

def load_from_csv():
    """Loads data from an existing CSV file."""
    filename = input("Enter the filename of the CSV to load (e.g., 'input.csv'): ")
    if not filename.endswith('.csv'):
        filename += '.csv'
    
    try:
        with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            if not set(HEADERS).issubset(set(reader.fieldnames or [])):
                 print(f"ERROR: The CSV headers do not match the required format.")
                 missing = list(set(HEADERS) - set(reader.fieldnames or []))
                 print(f"The following required headers are missing: {', '.join(missing)}")
                 input("Press Enter to continue...")
                 return []
            
            loaded_data = list(reader)
            print(f"Successfully loaded {len(loaded_data)} rows from '{filename}'.")
            input("Press Enter to continue...")
            return loaded_data
    except FileNotFoundError:
        print(f"ERROR: File '{filename}' not found.")
        print("Please make sure the CSV file is in the same directory as the script.")
        input("Press Enter to continue...")
        return []
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        input("Press Enter to continue...")
        return []

# --- Main Application Loop ---

def main():
    """Main function to run the application loop."""
    data = []
    
    while True:
        clear_screen()
        print("--- Welcome to the CSV Builder ---")
        print("1. Load an existing CSV file")
        print("2. Create a new CSV from scratch")
        print("3. Exit")
        
        start_choice = input("Enter your choice (1-3): ")
        if start_choice == '1':
            data = load_from_csv()
            break 
        elif start_choice == '2':
            break 
        elif start_choice == '3':
            return 
        else:
            print("Invalid choice. Please try again.")
            input("Press Enter to continue...")

    while True:
        clear_screen()
        display_data(data)
        print("--- CSV Builder Menu ---")
        print("1. Add new device")
        print("2. Edit existing device")
        print("3. Delete device")
        print("4. Copy existing device")
        print("5. Save to CSV and Exit")
        print("6. Help / Instructions")
        print("7. Exit without saving")
        
        choice = input("Enter your choice (1-7): ")

        if choice == '1':
            add_device(data)
        elif choice == '2':
            edit_device(data)
        elif choice == '3':
            delete_device(data)
        elif choice == '4':
            copy_device(data)
        elif choice == '5':
            save_to_csv(data)
            break
        elif choice == '6':
            show_instructions()
        elif choice == '7':
            print("Exiting application.")
            break
        else:
            print("Invalid choice. Please try again.")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main()

