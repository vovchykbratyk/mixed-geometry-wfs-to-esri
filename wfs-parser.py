import arcpy
import os
import som_parser as sp
import wfs_query as wq


"""
Testing on static data
"""

if __name__ == '__main__':
    # Overwrite
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
