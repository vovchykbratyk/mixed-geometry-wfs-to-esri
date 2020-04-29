"""
This tool authenticates a user to a GeoServer upon presenting a valid
PKCS12 cert, issues a query based on various CQL parameters and converts
the mixed-geometry response into a set of feature classes. Alternatively
a user is able to issue a json flat file as an input.
"""


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
    input_file = arcpy.GetParameterAsText(1)  # Input GeoJSON file
    output_name_prefix = arcpy.GetParameterAsText(2)  # Output name prefix
    start_date = arcpy.GetParameter(3)  # Start date
    end_date = arcpy.GetParameter(4)  # End date
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



        cql_raw = {
            'sdate': start_date,
            'edate': end_date,
            'be': be,
            'aor': aor,
            'orgid': orgid,
            'trigraph': trigraph,
            'docid': docid,
            'bbox': bbox
        }
        b_url = "https://gets.geoint.com/geoserver/"

        q = wq.WFSQuery(b_url, **cql_raw)
        print(q.kwargs)
        print(q.user_cql)
        arcpy.AddMessage(q.url)
