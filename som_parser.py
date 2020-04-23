import arcpy
from datetime import datetime
import json


class SOMFeatures:
    """
    Base SOM class
    """

    def __init__(self, gdb, fc_prefix, fields, sr, json_input):
        """
        Esri SOM object constructor
        """
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
            esri_polyline = arcpy.Polyline(arcpy.Array([arcpy.Point(*coords) for coords in geometry['coordinates']]),
                                           self.sr)
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
        Reusable feature class creation logic
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
        Orchestrates make_featureclass() per geometric primitive
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