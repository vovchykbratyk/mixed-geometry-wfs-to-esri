"""
This script contains the main WFS query class and brokers the PKI connection.
"""

from datetime import datetime, timedelta

try:  # check if yapki installed and if not, go get it (Requires site configuration)
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

    def __init__(self, base_url, **kwargs):
        """WFS query constructor"""
        self.base_url = base_url
        self.kwargs = kwargs
        self.user_cql = []

        if 'sdate' in self.kwargs:
            if self.kwargs['sdate']:
                sdate = f"temporal%20%3E%20%27{self.kwargs['sdate'].strftime('%Y-%m-%dT%H:%M:%S')}%27"  # temporal > 'value'
                self.user_cql.append(sdate)
            else:
                sdate = f"temporal%20%3E%20%27{(datetime.now() - timedelta(days=3)).strftime('%Y-%m-%dT%H:%M:%SZ')}%27"
                self.user_cql.append(sdate)
        if 'edate' in self.kwargs:
            if self.kwargs['edate']:
                edate = f"temporal%20%3C%20%27{self.kwargs['edate'].strftime('%Y-%m-%dT%H:%M:%S')}%27"  # temporal < 'value'
                self.user_cql.append(edate)
            else:
                edate = f"temporal%20%3C%20%27{datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}%27"
                self.user_cql.append(edate)
        if 'be' in self.kwargs:
            if len(self.kwargs['be']) > 0:
                be = f"be%20LIKE%20%27{self.kwargs['be'][:10]}%25%27"  # be LIKE 'value%'
                self.user_cql.append(be)
        if 'aor' in self.kwargs:
            if len(self.kwargs['aor']) > 0:
                aor = f"aor%20%3D%20%27{self.kwargs['aor']}%27"  # aor = 'value'
                self.user_cql.append(aor)
        if 'orgid' in self.kwargs:
            if len(self.kwargs['orgid']) > 0:
                orgid = f"orgid%20%3D%20%27{self.kwargs['orgid']}%27"  # orgid = 'value'
                self.user_cql.append(orgid)
        if 'trigraph' in self.kwargs:
            if len(self.kwargs['trigraph']) > 0:
                trigraph = f"trigraph%20%3D%20%27{self.kwargs['trigraph']}%27"  # trigraph = 'value'
                self.user_cql.append(trigraph)
        if 'docid' in self.kwargs:
            if len(self.kwargs['docid']) > 0:
                docid = f"docid%20LIKE%20%27{self.kwargs['docid']}%25%27"  # docid LIKE 'value%'
                self.user_cql.append(docid)
        if 'BBOX' in self.kwargs:
            if len(self.kwargs['BBOX']) > 0:
                bbox = f"AND%20%BBOX(corners, {self.kwargs['BBOX']})"  # AND BBOX(corners, coordinates)
                self.user_cql.append(bbox)

        self.url = self.base_url + str("%20AND%20".join(self.user_cql))

    def do_query(self):
        """
        Uses YAPKI to establish client PKI context and execute query(s).
        """
        s = yapki.Session(cert=yapki.get_windows_cert())
        s.headers.update(yapki.USER_AGENTS['Firefox'])
        r = s.get(self.url)
        return r.json()
