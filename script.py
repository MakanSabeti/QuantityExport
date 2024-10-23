# Revit imports
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from pyrevit import forms
import clr
import json
import os
import System

# Initialize Revit document
doc = __revit__.ActiveUIDocument.Document

# Define the path for saving parameter selection sets
parameter_sets_dir = "C:\Users\SABE15132\AppData\Roaming\CustomExtensions\hatchdata.extension\Hatch.tab\EastHarbour.panel\SaveFunction.pushbutton" 
extraJson = "C:\Users\SABE15132\AppData\Roaming\CustomExtensions\hatchdata.extension\Hatch.tab\EastHarbour.panel\SaveFunction.pushbutton"

# Function to load selection from JSON
def load_selection_from_json(selection_name):
    json_path = os.path.join(parameter_sets_dir, "{}.json".format(selection_name))
    with open(json_path, "r") as json_file:
        return json.load(json_file)

# Function to save selection to JSON
def save_selection_to_json(selection_name, categories, instance_parameters, type_parameters):
    json_path = os.path.join(parameter_sets_dir, "{}.json".format(selection_name))
    with open(json_path, "w") as json_file:
        json.dump({
            "categories": categories,
            "instance_parameters": instance_parameters,
            "type_parameters": type_parameters
        }, json_file)

def save_selection_to_json_two(categories, instance_parameters, type_parameters):
    json_path = os.path.join(extraJson, "saved_parameter_set.json")
    with open(json_path, "w") as json_file:
        json.dump({
            "categories": categories,
            "instance_parameters": instance_parameters,
            "type_parameters": type_parameters
        }, json_file)

# Function to collect model categories
def get_model_categories():
    return [cat.Name for cat in doc.Settings.Categories if cat.CategoryType == CategoryType.Model]

# Function to collect elements from selected categories
def collect_elements(categories):
    elements = []
    for category_name in categories:
        category = next((cat for cat in doc.Settings.Categories if cat.Name == category_name), None)
        if category:
            bic = System.Enum.Parse(BuiltInCategory, category.Id.IntegerValue.ToString())
            elements.extend(FilteredElementCollector(doc).OfCategory(bic).WhereElementIsNotElementType().ToElements())
    return elements

# Function to display selection dialog with manual check mark processing
def select_with_manual_check(options, checked_options, title):
    options_with_checks = [(opt, opt in checked_options) for opt in sorted(options)]
    checked = forms.SelectFromList.show(
        [opt[0] for opt in options_with_checks],
        title=title,
        multiselect=True,
        button_name="Select"
    )
    return checked

# Function to collect parameter values
def get_parameter_values(elements, parameter_names):
    param_data = {param_name: [] for param_name in parameter_names}
    
    for element in elements:
        for param_name in parameter_names:
            param = element.LookupParameter(param_name)
            if param:
                # Handle different storage types
                if param.StorageType == StorageType.String:
                    param_data[param_name].append(param.AsString())
                elif param.StorageType == StorageType.Double:
                    param_data[param_name].append(param.AsDouble())
                elif param.StorageType == StorageType.Integer:
                    param_data[param_name].append(param.AsInteger())
                else:
                    param_data[param_name].append("Other Type")
            else:
                param_data[param_name].append("N/A")
    
    return param_data

# Main function to run the selection
def main():
    # List saved selection sets
    saved_selections = [f.replace(".json", "") for f in os.listdir(parameter_sets_dir) if f.endswith(".json")]
    
    if saved_selections:
        selection_names = saved_selections + ["Create New Selection"]
        selected_name = forms.SelectFromList.show(
            sorted(selection_names),
            title="Select a Saved Selection or Create New",
            multiselect=False,
            button_name="Select"
        )
    else:
        forms.alert("No saved selections found. Creating a new selection...", exitscript=False)
        selected_name = "Create New Selection"

    # Initialize empty lists for selection if creating a new one
    model_categories_selected = []
    instance_parameter_to_select = []
    type_parameter_to_select = []

    # Load existing selection set if one is chosen
    if selected_name != "Create New Selection":
        loaded_selection = load_selection_from_json(selected_name)
        model_categories_selected = loaded_selection.get("categories", [])
        instance_parameter_to_select = loaded_selection.get("instance_parameters", [])
        type_parameter_to_select = loaded_selection.get("type_parameters", [])

    # Model Category Selection
    model_category_names = get_model_categories()
    selected_categories = select_with_manual_check(model_category_names, model_categories_selected, "Select Model Categories")
    
    # Collect elements from the selected categories
    elements = collect_elements(selected_categories)

    # Instance Parameter Selection with Manual Check
    unique_instance_parameter_names = {p.Definition.Name for e in elements for p in e.Parameters}
    selected_instance_parameters = select_with_manual_check(unique_instance_parameter_names, instance_parameter_to_select, "Select Instance Parameters")

    # Get instance parameter values
    instance_param_values = get_parameter_values(elements, selected_instance_parameters)

    # Type Parameter Selection with Manual Check
    unique_type_parameter_names = set()
    for element in elements:
        element_type = doc.GetElement(element.GetTypeId())
        if element_type:
            unique_type_parameter_names.update(p.Definition.Name for p in element_type.Parameters)
    
    selected_type_parameters = select_with_manual_check(unique_type_parameter_names, type_parameter_to_select, "Select Type Parameters")

    # Get type parameter values
    type_param_values = get_parameter_values(elements, selected_type_parameters)

    # Save the selection if needed
    selection_name = forms.ask_for_string(prompt="Enter a name for this selection:", title="Save Selection")
    if selection_name:
        save_selection_to_json(selection_name, selected_categories, instance_param_values, type_param_values)
        save_selection_to_json_two(selected_categories, instance_param_values, type_param_values)

    # For testing, print the selected parameter values
    print("Instance Parameter Values:", instance_param_values)
    print("Type Parameter Values:", type_param_values)

# Run main
main()
