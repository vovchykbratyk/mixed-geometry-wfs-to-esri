import arcpy
from datetime import datetime, timedelta
import json
import os
import som_parser as sp
import wfs_query as wq


if __name__ == '__main__':
    # Set environment variables
    current_project = arcpy.mp.ArcGISProject('current')
    current_db = current_project.defaultGeodatabase

    arcpy.env.overwriteOutput = True

    # Fields
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

    # Parameters
    input_type = arcpy.GetParameter(0)  # Choice of file or service call
    input_file = arcpy.GetParameter(1)  # Input GeoJSON file
    output_name_prefix = arcpy.GetParameterAsText(2)  # Output name prefix
    sdate = arcpy.GetParameter(3)  # Start date
    edate = arcpy.GetParameter(4)  # End date
    be = arcpy.GetParameterAsText(5)  # BE Number
    aor = arcpy.GetParameterAsText(6)  # AOR
    orgid = arcpy.GetParameterAsText(7)  # Organization ID
    trigraph = arcpy.GetParameterAsText(8)  # Country Code (ISO-3)
    docid = arcpy.GetParameterAsText(9)  # DOCID
    bbox = arcpy.GetParameterAsText(10)  # Bounding Box

    sr = arcpy.SpatialReference(4326)

    if input_type == "File":
        with open(input_file, 'r') as jf:
            gets_data = sp.SOMFeatures(current_db, output_name_prefix, field_list, sr, jf)
            parsed_gets_data = gets_data.parse_json()
            feature_classes = gets_data.make_features(parsed_gets_data)

            for fcs in feature_classes:
                arcpy.AddMessage(f"Created feature class {fcs['name']} with {fcs['rows']} rows.")
    elif input_type == "GETS WFS Query":
        json_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config/gets.json')
        try:
            with open(json_file) as f:
                config_json = json.load(f)
                gets_base_url = config_json['gets_server']
        except IOError:
            arcpy.AddError('Configuration file %s not found.' % json_file)
        except ValueError:
            arcpy.AddError('Configuration file %s is not valid JSON.' %
                           json_file)

        payload_raw = {
            'sdate': sdate,
            'edate': edate,
            'be': be,
            'aor': aor,
            'orgid': orgid,
            'trigraph': trigraph,
            'docid': docid,
            'bbox': bbox
        }
        payload_items = {k: v for k, v in payload_raw.items() if v is not None}
        q = wq.WFSQuery(base_url=gets_base_url, payload=payload_items)
        print(q)
        arcpy.AddMessage(f"Issuing query to: \n{q}")
