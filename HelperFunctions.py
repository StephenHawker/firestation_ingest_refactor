"""HELPER Functions"""
import logging
import urllib.parse as urlparse
import datetime
import codecs
import configparser


class HelperFunctions:
    ############################################################
    # constructor
    ############################################################
    def __init__(self):

        self.name = "Helper Functions"
        self.LOGGER = logging.getLogger(__name__)

    ############################################################
    # str
    ############################################################
    def __str__(self):

        return repr("Helper Functions")

    ############################################################
    # Load Config File
    ############################################################
    def load_config(self, file):
        """Load config file

        Keyword arguments:
        file -- config file path
        config -- config array
        """
        config = {}

        config = config.copy()
        cp = configparser.ConfigParser()
        cp.read(file)
        for sec in cp.sections():
            name = sec.lower()  # string.lower(sec)
            for opt in cp.options(sec):
                config[name + "." + opt.lower()] = cp.get(sec, opt).strip()
        return config

    ############################################################
    # Get query string value from link
    ############################################################
    def get_qs_value(self, url, query_string):
        """get query string from passed url query string

        Keyword arguments:
        url -- href link
        query_string -- query string key to search for
        """
        try:

            parsed = urlparse.urlparse(url)
            qs_value = urlparse.parse_qs(parsed.query)[query_string]

            for k in qs_value:
                return str(k)

        except KeyError:
            return ""
        except Exception:
            raise Exception("Error in get_qs_value - %s %s ", url, query_string)

    ############################################################
    # Get EPOCH days ahead
    ############################################################
    def next_weekday(self, d, weekday):

        days_ahead = weekday - d.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7

        return d + datetime.timedelta(days_ahead)

    ############################################################
    # untangle_utf8
    ############################################################
    def untangle_utf8(self, match):
        """unicode issues...

        Keyword arguments:
        match -- json string with unicode issues...
        """
        escaped = match.group(0)                   # '\\u00e2\\u0082\\u00ac'
        hexstr = escaped.replace(r'\u00', '')      # 'e282ac'
        buffer = codecs.decode(hexstr, "hex")      # b'\xe2\x82\xac'

        try:
            return buffer.decode('utf8')           # '€'

        except UnicodeDecodeError:
            self.LOGGER.error("Could not decode buffer: %s" % buffer)
