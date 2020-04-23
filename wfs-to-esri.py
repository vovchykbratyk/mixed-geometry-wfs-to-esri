import arcpy
import os
import som_parser as sp
import wfs_query as wq
import arcpy


class ToolValidator(object):
    """
    Class for validating a tool's parameter values and controlling
    the behavior of the tool's dialog.
    """

    def __init__(self):
        """
        Setup arcpy and the list of tool parameters.

        -------------------
        Parameter List
        -------------------
        * 0: Select whether file or service (Value list: JSON/GeoJSON File; GETS WFS)
        * 1: File input (File: If 0 = JSON/GeoJSON File)
        * 2: Start date (Date) - Optional; defaults to (today - 5 days)
        * 3: Stop date (Date) - Optional; defaults to today
        * 4: Country Code (String) - Optional
        * 5: BE (String) - Optional
        * 6: Organization (String) - Optional
        * 7: AOR - Optional (Value List)
        * 8: Suppress Sensor? (True/False) - Issues a NOT for a particular sensor
        * 9: Max Features to Return (Int) - Optional; defaults to 5000
        * 10: Output Name Prefix (String)

        -------------------
        Parameter Logic
        -------------------
        * Start/Stop dates will always be included
        * If 0 == JSON/GeoJSON File, only enable self.params[10] (output name).
        * If 0 == GETS WFS, Disable self.params[1]; Enable self.params[2-10]
        * If Country Code AND BE AND Organization AND AOR are false, fetch BBOX of current view.
        """
        self.params = arcpy.GetParameterInfo()

    def initializeParameters(self):
        """
        Refine the properties of a tool's parameters. This method is
        called when the tool is opened.
        """

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self):
        """Modify the values and properties of parameters before internal
        validation is performed. This method is called whenever a parameter
        has been changed."""
        if self.params[0].value == "JSON/GeoJSON File":
            self.params[1].enabled = True
            self.params[2].enabled = False
        elif self.params[0].value == "GETS WFS":
            self.params[1].enabled = False
            self.params[2].enabled = True

    def updateMessages(self):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""

"""
Testing on static data
"""

if __name__ == '__main__':
    # Set overwrite
    arcpy.env.overwriteOutput = True

    # Test parameters
    field_list = [
        ['secclass', 'TEXT', 'Classification', 64],
        ['temporal', 'TEXT', 'Temporal', 32],
        ['temporalend', 'TEXT', 'TemporalEnd', 32],
        ['cc', 'TEXT', 'Country Code', 12],
        ['be', 'TEXT', 'BeNum', 32],
        ['title', 'TEXT', 'Title', 255],
        ['activity', 'TEXT', 'Activity', 255],
        ['cmnt', 'TEXT', 'Comment', 255],
        ['confidence', 'FLOAT', 'Confidence'],
        ['description', 'TEXT', 'Temporal', 255],
        ['entityid', 'TEXT', 'EntityID', 64],
        ['equipmentcode', 'TEXT', 'EquipmentCode', 64],
        ['item_type', 'TEXT', 'ItemType', 64],
        ['movobj', 'TEXT', 'MovementObj', 64],
        ['movobjcnt', 'TEXT', 'MovemtnObjCnt', 64],
        ['name', 'TEXT', 'Name', 64],
        ['summary', 'TEXT', 'Temporal', 255],
        ['analysis', 'TEXT', 'Temporal', 255],
        ['timestamp', 'TEXT', 'Temporal', 32],
        ['type', 'TEXT', 'Temporal', 64],
        ['mgrs', 'TEXT', 'Temporal', 64],
        ['orgid', 'TEXT', 'Temporal', 32],
        ['aor', 'TEXT', 'Temporal', 32],
        ['link', 'TEXT', 'Report Link', 255],
        ['sensor', 'TEXT', 'Sensor', 64],
        ['docid', 'TEXT', 'DOCID', 255],
        ['src_class', 'TEXT', 'ClassSource', 64],
        ['declassifyon', 'TEXT', 'DeclassOn', 64]
    ]
    wfs_in = arcpy.GetParameter(0)  # Get whether input is a file or a service call

    if wfs_in == "File":






    json_dir = os.getcwd()
    json_file = "gets_response.json"
    gr = os.path.join(json_dir, json_file)

    gdb_dir = os.getcwd()
    gdb_name = "test_gdb"

    geodatabase = os.path.join(gdb_dir, gdb_name + ".gdb")

    if not arcpy.Exists(geodatabase):
        g = arcpy.CreateFileGDB_management(gdb_dir, gdb_name)
    else:
        g = geodatabase

    # Set environment
    arcpy.env.workspace = geodatabase

    spatial_ref = arcpy.SpatialReference(4236)

    with open(gr, "r") as gets_json_file:
        gets_data = sp.SOMFeatures(geodatabase, "testrun", field_list, spatial_ref, gets_json_file)

    parsed_gets_data = gets_data.parse_json()
    feature_classes = gets_data.make_features(parsed_gets_data)

    for fcs in feature_classes:
        print(f"Feature class name: {fcs['name']} | Rows: {fcs['rows']}")
