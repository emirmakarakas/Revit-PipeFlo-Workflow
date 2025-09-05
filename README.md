# Revit-to-PipeFlo Workflow Automation

This project provides a set of scripts to automate the transfer of hydraulic data from a Revit 3D model to Pipe-Flo for analysis. The core of this workflow is the "digital link" concept, which uses a unique `PipeRunID` to ensure data integrity from the initial design schematic through to the final analysis.

## Features
* **Data Integrity**: Establishes a reliable link between the 2D schematic and the 3D model.
* **Automated Extraction**: Uses a Dynamo script to pull accurate geometric and component data directly from Revit.
* **Intelligent Aggregation**: A Python script automatically calculates total pipe run lengths, finds start/end elevations, and compiles a complete list of unique fittings for each run.
* **Streamlined Analysis**: Populates a Pipe-Flo schematic with accurate data from the 3D model in seconds, saving considerable time and reducing manual entry errors.

---

## ⚙️ Prerequisites

Before you begin, ensure you have the following installed:
* Autodesk Revit & Dynamo
* Python 3 (with the `pandas` and `numpy` libraries installed)
* Pipe-Flo Professional
* Git (for version control)

---

## 🚀 Setup and Configuration

Follow these steps once to prepare your project and local environment.

### 1. Clone the Repository

Clone this repository to your local machine using Git Bash or another terminal:

```bash
git clone https://github.com/emirmakarakas/Revit-PipeFlo-Workflow.git
```

### 2. Set Up the `PipeRunID` Parameter in Revit

This shared parameter is the key to the entire workflow. You must create and add it to your Revit project.

#### **Create the Shared Parameter**

1. In Revit, go to the **Manage** tab → **Shared Parameters**.
2. Create a new **Group** (e.g., `Hydraulic Analysis`).
3. Under that group, create a new **Parameter** with the following properties:
   * **Name**: `PipeRunID`
   * **Discipline**: Common
   * **Type of Parameter**: Text

#### **Add the Parameter to Your Project**

1. Go to the **Manage** tab → **Project Parameters** → **Add**.
2. Select **Shared parameter**, click **Select...**, and choose the `PipeRunID` you just created.
3. In the "Parameter Properties" window, under **Categories** on the right, scroll down and check the boxes for:
   * **Pipes**
   * **Pipe Fittings**
4. Click **OK**. The `PipeRunID` parameter will now appear in the Properties panel for any pipe or fitting you select.

### 3. Configure the Project Paths

You must tell the scripts where to find and save your project files.

1. Find the file named `config.template.json`.
2. Make a copy of this file and rename it to `config.json`.
3. Open `config.json` in a text editor and replace the placeholder paths with the actual full paths for your project files.


## 📘 How to Use the Workflow

Follow these steps for each project analysis.

### ✅ **Step 1: Initial Schematic Design & Setup in Pipe-Flo**

**Who:** Design Engineer

Before any 3D modeling, the hydraulic foundation must be built in Pipe-Flo. This initial setup is the most critical phase as it defines the data structure for the entire project.

1. **Create the 2D Schematic**: Draw the complete hydraulic schematic in Pipe-Flo. This drawing will serve as the definitive master plan.  
2. **Assign `PipeRunID`s**: Name each **pipe** in the schematic using the unique `PipeRunID` (e.g., `CHW-S-P1-J1`). [cite_start]This ID is the "digital link" that connects all workflow stages[cite: 6].  
3. **Define Materials and Sizes**: Set up all required pipe material specifications in Pipe-Flo. You must ensure that these specifications include all valid pipe sizes that will be used in the Revit model to prevent data import errors later.  
4. **Create the Template Pipe**: In the Pipe-Flo model, create one pipe named exactly **`TEMPLATE_PIPE`**. This pipe acts as a library; it must have every single fitting that will be used across the project installed on it. The import script uses this template to identify and assign fittings correctly.  
5. **Establish Node Naming Convention**: This is essential for the script to update elevations automatically. The `aggregate.py` script generates node names using a specific format: `[PipeRunID]_StartNode` and `[PipeRunID]_EndNode`. You **must** follow this exact convention when naming the nodes in your Pipe-Flo schematic.  
    * For a pipe run named `CHW-S-P1-J1`, its corresponding nodes must be named `CHW-S-P1-J1_StartNode` and `CHW-S-P1-J1_EndNode`.  
    * **Important**: Where multiple pipes connect, a single node will serve as the "end" for one pipe and the "start" for another. You must name the node according to its primary function in the junction or simply ensure a consistent naming that the script can reference. For example, the node connecting `PipeA` and `PipeB` could be named `PipeA_EndNode`, and `PipeB` would connect to that same node.

### ✅ Step 2: Assign PipeRunIDs in Revit

A **Pipe Run** is defined as the entire length of pipe between two major components or junctions.

1. For each logical run in your project, select all the pipes and fittings that belong to that single run.
2. In the **Properties** panel, find the **`PipeRunID`** parameter.
3. Enter the unique ID (e.g., `CHW-S-P1-J1`) that you have defined on your 2D schematic. This step is critical for the automation to work.

### ✅ Step 3: Export Data Using Dynamo

This step extracts the raw data from your Revit model.

1. Open your project in Revit and launch Dynamo.
2. Open the `Home.dyn` script from this repository.
3. You will see three main nodes: a **Boolean** toggle, a **String** input box, and the main **Python Script** node.
4. In the **String** node, enter the full file path where the script should save the data.
   * 💡 **Pro Tip**: Copy the `"revit_export_path"` value from your `config.json` file and paste it directly into this **String** node to ensure consistency.
5. Ensure the **Boolean** toggle is set to `True` and click **Run**.

### ✅ Step 4: Process the Raw Data

This step takes the raw data from Revit and consolidates it by `PipeRunID`.

* Run the `aggregate.py` script. It will read the file specified in your `config.json` and create the final, structured CSV file at the location you defined.

### ✅ Step 5: Import Data into Pipe-Flo

This final step populates your Pipe-Flo schematic.

1. Open your corresponding schematic in Pipe-Flo. Ensure each pipe is named with the correct `PipeRunID`.
2. Confirm you have a pipe named **`TEMPLATE_PIPE`** that contains all the fittings used in your project.
3. Run the `universal_imparter.py` script from within Pipe-Flo.

The script will find each pipe by its `PipeRunID` and automatically update its length,material,size and list of fittings based on the data from your 3D Revit model.

## 📚 Documentation

For a detailed guide on how to manually edit the CSV file to import data for various devices and manage different operational scenarios, please see the **[CSV Import Manual](./docs/csv_import_manual.md)**.

## 📎 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 👤 Author

Developed by [Emir Karakas](https://github.com/emirmakarakas)

---

## 💬 Feedback

If you find bugs or want to contribute improvements, feel free to [open an issue](https://github.com/emirmakarakas/Revit-PipeFlo-Workflow/issues) or submit a pull request.

