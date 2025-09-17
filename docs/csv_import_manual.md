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

> **💡 Pro Tip:** If you are not using certain optional parameters, you can simply **hide those columns** in your spreadsheet software (like Excel) to create a cleaner, more focused view of the data you need to enter. The script will still work perfectly.

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

Use this to define heat exchangers or chillers. Thanks to intelligent defaults, you can define a functional component with very little information.

* **`device_type`**: Must be `heatsourcesink`.
* **`name`**: The exact name of the Heat Source/Sink in Pipe-Flo.
* **`Thermal Flow Rate` (Recommended)**: The flow rate for thermal calculations in **cubic meters per hour (m³/hr)**.
    * **Default Value**: If left blank, the script will use a default value of **1.0 m³/hr**.

* **Optional Parameters**:
    * **`Thermal Calculation Mode`**: Defaults to `calculate_heat_transfer_rate`. You can override it with `calculate_flow_rate`.
    * **`Heat Transfer Rate`**: The heat transfer rate in **kilowatts (kW)**. Defaults to **100 kW**.
    * **`inlet elevation` / `outlet elevation`**: Elevations in **meters**.
    * **`Flow Control Device`**: The name of a linked Flow Control Device in Pipe-Flo.
    * **`Temp Tolerance`**: The temperature tolerance value in **Kelvin**.
    * **`Source`**: Defaults to `FALSE`. Enter `TRUE` only if the flow rate is a source.

### **Control Valves**

Use this to set the operational parameters for control valves. The script defaults to the most common configuration (`flow_rate`), so you only need to provide a setpoint.

* **`device_type`**: Must be `controlvalve`.
* **`name`**: The exact name of the Control Valve in Pipe-Flo.
* **`Control Valve setpoint` (Recommended)**: The target setpoint for the valve.
    * When using the default mode, this value is in **cubic meters per hour (m³/hr)**.
    * **Default Value**: If left blank, the script assumes a setpoint of **1.0 m³/hr**.

* **Optional Parameters**:
    * **`Control Valve model`**: Defaults to `flow_rate`. You can override it with `temperature_control`.
    * **`elevation`**: The valve's elevation in **meters**.
    * **`Control Valve min dP`**: Minimum pressure drop in **kilopascals (kPa)**.
    * **`Control Valve max dP`**: Maximum pressure drop in **kilopascals (kPa)**.

### **Lineups**

Use this to change the active lineup in the Pipe-Flo model before a calculation.

* **`device_type`**: Must be `lineup`.
* **`name`**: The exact name of the lineup you want to set as active.

---

## 4. Advanced Usage: Scenario Analysis and Data Overrides

You can use the CSV file to test different operational scenarios by strategically ordering the rows. The script reads the CSV file from **top to bottom**, so if you define the same device multiple times, the parameters from the **last entry it finds** will be applied.

### **Example: Setting Up Scenarios**

| device_type  | name               | ... | Control Valve setpoint |
| :----------- | :----------------- | :-- | :------------------- |
| **`lineup`** | **Summer Operation** |     |                      |
| `controlvalve` | FCV-01             |     | **120** |
|              |                    |     |                      |
| **`lineup`** | **Winter Operation** |     |                      |
| `controlvalve` | FCV-01             |     | **85** |

In this example, after running the script, the active lineup will be "Winter Operation" and the control valve `FCV-01` will have its setpoint updated to `85`.