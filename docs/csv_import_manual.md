# User Manual: Editing the CSV for Pipe-Flo Data Import

## 1. Introduction

This document is a guide for manually editing the `processed_data_for_pipeflo.csv` file. While the primary purpose of our automated workflow is to populate pipe and node data directly from Revit, this CSV file can be extended to import data for a wide variety of other devices in Pipe-Flo, such as control valves and heat sources.

The `universal_imparter.py` script is designed to read this CSV file and update your Pipe-Flo model accordingly. Understanding how to structure this file allows you to perform powerful, bulk data updates.

## 2. The Core Concept: `device_type`

The most important column in the CSV is the first one: **`device_type`**. This column tells the script what kind of component you are defining in that row. The script then knows which subsequent columns to read to get the data for that specific device.

The script recognizes the following `device_type`s:

* `pipe`
* `node`
* `heatsourcesink`
* `controlvalve`
* `lineup`

**Golden Rule**: For any given row, you only need to fill in the columns relevant to that `device_type`. All other columns in that row can be left blank.

## 3. Parameter Guide by Device Type

Below is a detailed breakdown of the parameters for each device type. The column headers mentioned here are the exact headers in the CSV file.

### **Pipes**

The `aggregate.py` script generates these rows automatically. You would typically only edit them to override a calculated value.

* **`device_type`**: Must be `pipe`.
* **`name`**: The exact `PipeRunID` of the pipe in your Pipe-Flo model (e.g., `CHW-S-P1-J1`).
* **`length`**: The pipe's total length in **meters**.
* **`spec`**: The pipe's material specification (e.g., `Carbon Steel - Schedule 40`). This must match an existing specification in Pipe-Flo.
* **`size`**: The nominal pipe diameter. The script appends " mm" to this value, so just enter the number (e.g., `150`). This size must be valid for the specified material.
* **`fittings`**: A list of fittings separated by a semicolon (`;`). Each fitting name must correspond to a name in your `fitting_map.csv` file (e.g., `Std Elbow 90; Reducer; Butterfly Valve`).

### **Nodes**

These rows are also generated automatically by the `aggregate.py` script.

* **`device_type`**: Must be `node`.
* **`name`**: The exact name of the node in Pipe-Flo. This must follow the convention: `[PipeRunID]_StartNode` or `[PipeRunID]_EndNode`.
* **`elevation`**: The node's elevation in **meters**.

### **Heat Source / Sink**

Use this to define heat exchangers, chillers, or any component that adds or removes heat.

* **`device_type`**: Must be `heatsourcesink`.
* **`name`**: The exact name of the Heat Source/Sink in Pipe-Flo.
* **`inlet elevation`**: The elevation of the device's inlet in **meters**.
* **`outlet elevation`**: The elevation of the device's outlet in **meters**.
* **`Flow Control Device`**: The name of a linked Flow Control Device in Pipe-Flo.
* **`Temp Tolerance`**: The temperature tolerance value in **Kelvin**.
* **`Thermal Calculation Mode`**: Determines how the device's thermal properties are calculated. You must use one of these exact phrases:
  * `calculate_heat_transfer_rate`
  * `calculate_flow_rate`
* **`Heat Transfer Rate`**: The heat transfer rate in **kilowatts (kW)**.
* **`Thermal Flow Rate`**: The flow rate for thermal calculations in **cubic meters per hour (m³/hr)**.
* **`Source`**: Enter `TRUE` if the flow rate is a source, otherwise leave blank or enter `FALSE`.

### **Control Valves**

Use this to set the operational parameters for control valves in your system.

* **`device_type`**: Must be `controlvalve`.
* **`name`**: The exact name of the Control Valve in Pipe-Flo.
* **`elevation`**: The valve's elevation in **meters**.
* **`Control Valve model`**: The operational mode of the valve. You must use one of these exact phrases:
  * `flow_rate`
  * `temperature_control`
* **`Control Valve setpoint`**: The target setpoint for the valve. If the model is `flow_rate`, this value is in **cubic meters per hour (m³/hr)**.
* **`Control Valve min dP`**: The minimum design pressure drop across the valve in **kilopascals (kPa)**.
* **`Control Valve max dP`**: The maximum design pressure drop across the valve in **kilopascals (kPa)**.

### **Lineups**

Use this to change the active lineup in the Pipe-Flo model before a calculation.

* **`device_type`**: Must be `lineup`.
* **`name`**: The exact name of the lineup you want to set as active.

---
## 4. Advanced Usage: Scenario Analysis and Data Overrides

You can use the CSV file to test different operational scenarios (e.g., summer vs. winter conditions) by strategically ordering the rows.

### **How it Works**

The `universal_imparter.py` script reads the CSV file from **top to bottom**. If you define the same device multiple times, the script will apply the parameters from the **last entry it finds**. This allows you to set up different scenarios and switch between them.

### **Default Lineup Behavior**

If you do **not** add any row with `device_type` set to `lineup`, the script will apply all changes to the currently active lineup in your Pipe-Flo model. By default, this is typically the **"Design Case"** lineup.

### **Example: Setting Up Scenarios**

To manage multiple scenarios, you can add `lineup` rows followed by the specific device parameters for that scenario.

1. Add a `lineup` row to specify the scenario (e.g., "Summer Operation").
2. Immediately after, add rows for any devices (`heatsourcesink`, `controlvalve`, etc.) with the parameters for that specific scenario.
3. To switch to a different scenario, simply add another `lineup` row (e.g., "Winter Operation") followed by the new parameters for the same devices.

By re-running the script, Pipe-Flo will be updated with the settings from the last defined lineup and its corresponding device parameters.

---
## 5. Example CSV Structure

Here is a sample of what a completed `processed_data_for_pipeflo.csv` file might look like, including a scenario setup. Notice how only the relevant columns are filled for each row.

| device_type      | name                    | elevation | length | spec           | size | fittings                    | ... | Control Valve model | Control Valve setpoint |
| :--------------- | :--------------------- | :------- | :---- | :------------- | :-- | :-------------------------- | :-- | :----------------- | :------------------- |
| `pipe`           | CHW-S-P1-J1            |          | 55.4  | Carbon Steel   | 150  | Std Elbow 90; Reducer       |     |                    |                      |
| `node`           | CHW-S-P1-J1_StartNode  | 3.5      |       |                |      |                             |     |                    |                      |
| `node`           | CHW-S-P1-J1_EndNode    | 10.2     |       |                |      |                             |     |                    |                      |
| `heatsourcesink` | Chiller-1              |          |       |                |      |                             |     |                    |                      |
| ...              |                        |          |       |                |      |                             |     |                    |                      |
| **`lineup`**     | **Summer Operation**    |          |       |                |      |                             |     |                    |                      |
| `controlvalve`   | FCV-01                 | 4.1      |       |                |      |                             |     | `flow_rate`        | **120**              |
|                  |                        |          |       |                |      |                             |     |                    |                      |
| **`lineup`**     | **Winter Operation**    |          |       |                |      |                             |     |                    |                      |
| `controlvalve`   | FCV-01                 | 4.1      |       |                |      |                             |     | `flow_rate`        | **85**               |


In this example, after running the script, the active lineup will be "Winter Operation" and the control valve `FCV-01` will have its setpoint updated to `85`.