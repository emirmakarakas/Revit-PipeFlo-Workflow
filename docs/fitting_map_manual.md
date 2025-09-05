# User Manual: The Fitting Map and Keyword Matching

## 1. Introduction

This document explains how to use the `fitting_map.csv` file to accurately translate the fitting and valve names from your Revit model into the corresponding component names in your Pipe-Flo schematic. The `universal_imparter.py` script uses a simple but powerful keyword matching system to automate this process.

Correctly configuring this file is essential for a successful data import.

## 2. The Core Concept: How Keyword Matching Works

The `universal_imparter.py` script needs a way to understand which fitting in Revit corresponds to which fitting in Pipe-Flo. Since Revit family names can be long, complex, or inconsistent, the script uses a **keyword-based lookup system**.

Here's the logic the script follows for every fitting it encounters from Revit:

1. **Read the Map**: The script first reads the `fitting_map.csv` and loads all the `keyword` and `pipeflo_name` pairs into its memory.  
2. **Get Revit Fitting Name**: When processing a pipe run, the script gets the list of fitting names that were exported from Revit (e.g., `Threaded-Elbow_Malleable iron` or `BFV-10300-LUG-150mm`).  
3. **Search for Keywords**: For each Revit fitting name, the script checks against every `keyword` from the fitting map. It looks to see if the `keyword` string exists *anywhere* inside the Revit fitting name.  
4. **First Match Wins**: The search is performed in the order of the rows in your `fitting_map.csv`. As soon as the script finds a keyword that is present in the Revit name, it stops searching and uses the corresponding `pipeflo_name` for that entry.  
5. **Assign to Pipe-Flo**: The script then finds the fitting with that exact `pipeflo_name` from your `TEMPLATE_PIPE` in Pipe-Flo and installs it on the correct pipe run.  

> If no keyword in the entire `fitting_map.csv` is found within the Revit fitting's name, the script will generate an error, and the fitting will not be installed in Pipe-Flo.

---

## 3. How to Configure Your `fitting_map.csv`

The `fitting_map.csv` file has two simple columns:

* **`keyword`**: A unique text string that the script will search for. This should be a distinctive part of the name of your fitting families in Revit.  
* **`pipeflo_name`**: The exact, case-sensitive name of the corresponding fitting in your Pipe-Flo model's fitting library (i.e., installed on your `TEMPLATE_PIPE`).  

### Steps to Set Up Your Map

1. **Identify Your Revit Naming Convention**: Look at the fitting names in your Revit project. Find a consistent, unique part of the name for each type of fitting. This will be your keyword.  
2. **Get the Exact Pipe-Flo Name**: In Pipe-Flo, open the properties for the fittings on your `TEMPLATE_PIPE` and copy the exact `description` or name.
3. **Create the Mapping**: Open `fitting_map.csv` and add a new row for each fitting type.  
   * In the `keyword` column, put the unique string from the Revit name.  
   * In the `pipeflo_name` column, put the exact name from Pipe-Flo.
   * If you cant find a relevant pipeflo fitting for your revit fitting or if you think that a revit fitting has negligible loss and not worth taking it into account, simply dont add it to the mapping

### Example Scenario

Suppose your Revit model has fittings named:

* `MAGI-GEN`  
* `MAGI-PEX`  
* `CVSF`  
* `BFV`  
* `TEE-13106_CS`  
* `TRANSITION-11109-0001`  
* `Threaded-Elbow_Malleable iron`  
* `ELBOW-12506`  
* `EN 10253-3 Plug`  
* `OUTLET-1030040001`  
* `TEE`  
* `ELBOW`  
* `Reducer`  
* `Plug`  

And your Pipe-Flo `TEMPLATE_PIPE` has fittings named:

* `Reducer - Contraction`  
* `Pipe Bend - r/d 1`  
* `Butterfly`  
* `Tee - Flow Thru Branch`  
* `Reducer - Enlargement`  
* `Elbow - Standard 90°`  
* `Plug`  
* `Exit - Rounded`  
* `Std Tee Thru`  
* `Std Elbow 90`  

Your `fitting_map.csv` should look like this:

| keyword                        | pipeflo_name               |
| :----------------------------- | :------------------------ |
| MAGI-GEN                        | Reducer - Contraction     |
| MAGI-PEX                        | Pipe Bend - r/d 1         |
| CVSF                            | Butterfly                 |
| BFV                             | Butterfly                 |
| TEE-13106_CS                     | Tee - Flow Thru Branch    |
| TRANSITION-11109-0001           | Reducer - Enlargement     |
| Threaded-Elbow_Malleable iron   | Elbow - Standard 90°      |
| ELBOW-12506                     | Elbow - Standard 90°      |
| EN 10253-3 Plug                  | Plug                      |
| OUTLET-1030040001                | Exit - Rounded            |
| TEE                             | Std Tee Thru              |
| ELBOW                           | Std Elbow 90              |
| Reducer                         | Reducer - Enlargement     |
| Plug                            | Plug                      |

**How the script processes this:**

* `MAGI-**GEN**` → maps to **Reducer - Contraction**  
* `MAGI-**PEX**` → maps to **Pipe Bend - r/d 1**  
* `CVSF` → maps to **Butterfly**  
* `BFV` → maps to **Butterfly**  
* `TEE-13106_CS` → maps to **Tee - Flow Thru Branch**  
* `TRANSITION-11109-0001` → maps to **Reducer - Enlargement**  
* `Threaded-Elbow_Malleable iron` → maps to **Elbow - Standard 90°**  
* `ELBOW-12506` → maps to **Elbow - Standard 90°**  
* `EN 10253-3 Plug` → maps to **Plug**  
* `OUTLET-1030040001` → maps to **Exit - Rounded**  
* `TEE` → maps to **Std Tee Thru**  
* `ELBOW` → maps to **Std Elbow 90**  
* `Reducer` → maps to **Reducer - Enlargement**  
* `Plug` → maps to **Plug**

---

## 4. Best Practices & Troubleshooting

* **Be Specific with Keywords**: Avoid incorrect matches by using as specific keywords as necessary. For example, use `Tee-Reducing` and `Tee-Standard` rather than just `Tee`.  
* **Order Matters**: The script uses the *first* match it finds. Place your most specific keywords at the top of the CSV file to ensure correct mapping before more generic ones.  
* **Check for Errors**: After running `universal_imparter.py`, check the output log. Errors will indicate any Revit fitting names that did not match a keyword, so you can fix your map.  
* **Case Sensitivity**: Keyword matching is case-sensitive. Ensure your keywords match the case of the Revit family names exactly.
