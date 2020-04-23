from datetime import datetime

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
        """WFS query constructor"""
        self.base_url = base_url
        self.__payload = payload

    def get_payload(self):
        """Payload getter"""
        return self.__payload

    def set_payload(self, **kwargs):
        """
        Payload setter.  Assembles CQL query parameters, URL percent encodes them,
         and returns it as a list object.
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
            self.__payload.append(sdate)
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
        Uses YAPKI to establish client PKI context and execute query(s).
        """
        s = yapki.Session(cert=yapki.get_windows_cert())
        s.headers.update(yapki.USER_AGENTS['Firefox'])
        query_url = self.base_url + "%20AND%20".join(WFSQuery.get_payload(self))
        r = s.get(query_url)
        return r.json()