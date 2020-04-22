import arcpy
from datetime import datetime, timedelta
import json
import os
import sys

try:  # check if yapki installed and if not, go get it
    import yapki
except ImportError:
    # import subprocess
    # yapki_folder = "path/to/wheel"
    # yapki_file = "wheel_filename.whl"
    # yapki_wheel = os.path.join(yapki_folder, yapki_wheel)
    # subprocess.call([sys.executable, "-m", "pip", "install", yapki_wheel])
    # import yapki
    pass

"""
URL encoding key
%20 = ' ' (space)
%27 = ' (single quote)
%3D = = (equals)
%3C = < (less than)
%3E = > (greater than)
%25 = % (percent sign)
"""

class WFSQuery:
    """
    Sets up a WFS query (currently only 1.0.0) and obtains a GeoJSON result.
    """

    def __init__(self, base_url, payload):
        """Base WFS object"""
        self.base_url = base_url
        self.__payload = payload

    def get_payload(self):
        return self.__payload

    def set_payload(self, **kwargs):
        """
        Assembles CQL query parameters, URL percent encodes them, and returns it as a list object.
        """
        self.__payload = []
        if 'edate' in kwargs:
            edate = f"temporal%20%3C%20%27{kwargs['edate']}%27"  # temporal < 'value'
            self.__payload.append(edate)
        else:
            edate = f"temporal%20%3C%20%27{datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}%27"
            self.__payload.append(edate)
        if 'sdate' in kwargs:
            sdate = f"temporal%20%3E%20%27{kwargs['sdate']}%27"  # temporal > 'value'
        else:
            sdate = f"temporal%20%3E%20%27{(datetime.now() - timedelta(days=3)).strftime('%Y-%m-%dT%H:%M:%SZ')}%27"
            self.__payload.append(sdate)
        if 'be' in kwargs:
            be = f"be%20LIKE%20%27{kwargs['be']}%25%27"  # be LIKE 'value%'
            self.__payload.append(be)
        if 'aor' in kwargs:
            aor = f"aor%20%3D%20%27{kwargs['aor']}%27"  # aor = 'value'
            self.__payload.append(aor)
        if 'orgid' in kwargs:
            orgid = f"orgid%20%3D%20%27{kwargs['orgid']}%27"  # orgid = 'value'
            self.__payload.append(orgid)
        if 'trigraph' in kwargs:
            trigraph = f"trigraph%20%3D%20%27{kwargs['trigaph']}%27"  # trigraph = 'value'
            self.__payload.append(trigraph)
        if 'docid' in kwargs:
            docid = f"docid%20LIKE%20%27{kwargs['docid']}%25%27"  # docid LIKE 'value%'
            self.__payload.append(docid)
        if 'BBOX' in kwargs:
            bbox = f"AND%20%BBOX(corners, {kwargs['BBOX']})"  # AND BBOX(corners, coordinates)
            self.__payload.append(bbox)

    def do_query(self):
        """
        Use YAPKI to establish session and execute query(s).
        """
        s = yapki.Session(cert=yapki.get_windows_cert())
        s.headers.update(yapki.USER_AGENTS['Firefox'])
        query_url = self.base_url +  "%20AND%20".join(WFSQuery.get_payload())
        r = s.get(query_url)
        return r.json()


class SOMFeatures:
    """
    Base SOM class
    """

    def __init__(self, gdb, fc_prefix, fields, sr, json_input):
        self.gdb = gdb
        self.fc_prefix = fc_prefix
        self.fields = fields
        self.sr = sr
        self.json_input = json.load(json_input)  # change to json.loads() for production use

    def convert_gj_to_esri(self, geometry):
        """
        Converts GeoJSON geometric types and coordinates to Esri-compatible types and geometries, returned
        in a dictionary object.
        """
        if geometry['type'] == "Point":
            return {
                "type": "POINT",
                "coords": arcpy.Point(geometry['coordinates'][0], geometry['coordinates'][1])
            }
        elif geometry['type'] == "LineString":
            esri_polyline = arcpy.Polyline(arcpy.Array([arcpy.Point(*coords) for coords in geometry['coordinates']]), self.sr)
            return {
                "type": "POLYLINE",
                "coords": esri_polyline
            }
        elif geometry['type'] == "Polygon":
            for c in geometry['coordinates']:
                return {
                    "type": "POLYGON",
                    "coords": arcpy.Polygon(arcpy.Array([arcpy.Point(*coords) for coords in c]), self.sr)
                }
        else:
            raise Exception("Feature is not a point, line or polygon.")

    @staticmethod
    def clean_html(string, clean_class=False):
        """
        This method can be invoked to remove raw HTML tags and duplicative security classification that are stored
        in GETS postgresql.
        """
        import re
        cleaned = re.sub(r'<.*?>', "", string)  # remove < HTML CONTENT >
        if clean_class:
            return re.sub(r"\(.*?\)", "", cleaned, 1)[:253]  # remove field's sec class
        else:
            return cleaned[:253]

    @staticmethod
    def timestamp():
        # Get "now" in ISO format for naming feature classes dynamically
        return datetime.now().strftime('%Y%m%dT%H%M%S')

    def parse_json(self):
        """
        Crawls the JSON response, extracting necessary attributes.
        """
        point_rows = []
        polyline_rows = []
        polygon_rows = []
        feats = self.json_input['features']
        for f in feats:
            if f.get('geometry') is not None:  # ignore parent report objects
                # Get/assign the geometric info.
                geoinfo = SOMFeatures.convert_gj_to_esri(self, f.get('geometry'))
                geotype = geoinfo.get('type')
                esri_geom = geoinfo.get('coords')
                # Get/assign the attributes.
                props = f.get('properties')
                row_sec_class = props.get('classification')
                row_temporal = props.get('temporal')[:19]
                row_temporalend = props.get('temporalend')[:19]
                row_cc = props.get('trigraph')
                row_be = props.get('be')
                row_title = props.get('title')
                row_acty = props.get('activity')
                row_cmnt = props.get('comment')
                row_confidence = float(props.get('confidence'))
                row_desc = props.get('description')
                row_entityid = props.get('entityid')
                row_equipcode = props.get('equipmentcode')
                row_itemtype = props.get('item_type')
                row_movobj = props.get('movementobject')
                row_movobjcnt = props.get('movementobjectcount')
                row_name = props.get('name')
                row_summary = props.get('summary')
                row_analysis = SOMFeatures.clean_html(props.get('analysis'), clean_class=True)
                row_timestamp = props.get('timestamp')[:19]
                row_type = props.get('type')
                row_mgrs = props.get('mgrs')
                row_orgid = props.get('orgid')
                row_aor = props.get('aor')
                row_link = props.get('link')
                row_sensor = props.get('sensor')
                row_docid = props.get('docid')
                row_src_class = props.get('classificationsource')
                row_declass = props.get('declassifyon')
                # Build the row object.
                new_row = [esri_geom, row_sec_class, row_temporal, row_temporalend, row_cc,
                           row_be, row_title, row_acty, row_cmnt, row_confidence,
                           row_desc, row_entityid, row_equipcode, row_itemtype, row_movobj,
                           row_movobjcnt, row_name, row_summary, row_analysis, row_timestamp,
                           row_type, row_mgrs, row_orgid, row_aor, row_link,
                           row_sensor, row_docid, row_src_class, row_declass]
                # Sort the rows into geometric primitives.
                if geotype == "POINT":
                    point_rows.append(new_row)
                elif geotype == "POLYLINE":
                    polyline_rows.append(new_row)
                elif geotype == "POLYGON":
                    polygon_rows.append(new_row)
        return point_rows, polyline_rows, polygon_rows

    def get_fieldmap_list(self):
        return [f[0] for f in self.fields]

    def make_featureclass(self, rows, fc_name, geo_type, geo_token):
        """

        :param rows:
        :param fc_name:
        :param geo_type:
        :param geo_token:
        :return:
        """
        if not arcpy.Exists(fc_name):
            fc = arcpy.CreateFeatureclass_management(self.gdb, fc_name, geo_type, spatial_reference=self.sr)
            arcpy.AddFields_management(fc, self.fields)
        else:
            fc = fc_name
        fl = SOMFeatures.get_fieldmap_list(self)
        fl.insert(0, geo_token)
        fieldmap = tuple(fl)
        with arcpy.da.InsertCursor(fc, fieldmap) as cursor:
            for row in rows:
                cursor.insertRow(row)
        fc_stats = {
            "name": fc_name,
            "rows": len(rows)
        }
        return fc_stats

    def make_features(self, parsed_json):
        """
        Coordinates make_featureclass method for each geometric type.
        """
        # If any of the parsed JSON lists contain more than 0 rows, create a unique feature class for it.
        token_point = "SHAPE@XY"
        token_other = "SHAPE@"
        now = SOMFeatures.timestamp()
        stats = []

        if len(parsed_json[0]) > 0:
            point_rows = parsed_json[0]
            point_fc_name = self.fc_prefix + f"{now}_p"
            point_fc = SOMFeatures.make_featureclass(self, point_rows, point_fc_name, "POINT", token_point)
            stats.append(point_fc)
        if len(parsed_json[1]) > 0:
            polyline_rows = parsed_json[1]
            polyline_fc_name = self.fc_prefix + f"{now}_l"
            polyline_fc = SOMFeatures.make_featureclass(self, polyline_rows, polyline_fc_name, "POLYLINE", token_other)
            stats.append(polyline_fc)
        if len(parsed_json[2]) > 0:
            polygon_rows = parsed_json[2]
            polygon_fc_name = self.fc_prefix + f"{now}_a"
            polygon_fc = SOMFeatures.make_featureclass(self, polygon_rows, polygon_fc_name, "POLYGON", token_other)
            stats.append(polygon_fc)

        return stats

"""
Testing off static data
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

    json_dir = "C:/Users/ericc/PycharmProjects/mixed-geometry-wfs-to-esri"
    json_file = "gets_response.json"
    gr = os.path.join(json_dir, json_file)

    gdb_dir = "C:/Temp"
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
        gets_data = SOMFeatures(geodatabase, "testrun", field_list, spatial_ref, gets_json_file)

    parsed_gets_data = gets_data.parse_json()
    feature_classes = gets_data.make_features(parsed_gets_data)

    for fcs in feature_classes:
        print(f"Feature class name: {fcs['name']} | Rows: {fcs['rows']}")