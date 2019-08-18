import os
import sys
import logging.config
import simplejson as json
import pandas
from PageScraper import PageScraper
from APILookup import APILookup
from DistanceCalc import DistanceCalc
from HelperFunctions import HelperFunctions
from GetNearest import GetNearest
from collections import defaultdict
"""Read Firestations web page data """
"""Project Classes"""
""" Other Imports"""


class DatabaseLoadError(Exception):
    """Database Exception

    Keyword arguments:
    Exception -- Exception
    """
    def __init__(self, data):
        self.data = data

    def __str__(self):
        return repr(self.data)


class FirestationIngestError(Exception):
    """FirestationIngestError Exception

    Keyword arguments:
    Exception -- Exception
    """
    def __init__(self, data):
        self.data = data

    def __str__(self):
        return repr(self.data)


############################################################
# Main
############################################################
def main():
    """Main process

    """
    try:

        LOGGER.info('Started run. main:')
        lkp_addresses_file = configImport["firestation.lookup_addresses_file"]

        firestation_nearest_json_File = configImport["firestation.json_file"]
        """firestation_nearest_json_with_travel = configImport["firestation.json_file_with_travel"]"""

        LOGGER.debug("firestation URL : %s ", FIRESTATION_URL)
        LOGGER.debug("Postcode api URL : %s ", POSTCODE_API_URL)
        LOGGER.debug("TEMP_FILE : %s ", TEMP_FILE)
        LOGGER.debug("csv_file : %s ", CSV_FILE)
        LOGGER.debug("lkp_addresses_file : %s ", lkp_addresses_file)
        LOGGER.debug("number_closest : %s ", str(NUMBER_CLOSEST))

        fs_pagescraper = PageScraper(FIRESTATION_URL)
        firestatiom_html = fs_pagescraper.get_pagedata(FORM_VALUE)

        """TODO Deal with changes and updates"""

        fs_pagescraper.write_table_to_temp(TEMP_FILE)
        the_table = fs_pagescraper.get_table(TABLE_CLASS)

        fs_pagescraper.save_tab_as_list()
        fs_pagescraper.write_csv(CSV_FILE)

        """read back firestation data in to do calcs"""
        df_fs = pandas.read_csv(CSV_FILE)

        """get lat/lon for the file of lookup addresses"""
        df_lkp = get_lat_long_lkp_addresses(lkp_addresses_file)

        """Process lookups to get top n, get as json fragment"""
        process_lkp_list(df_lkp,
                         df_fs,
                         top_n=NUMBER_CLOSEST,
                         json_file=firestation_nearest_json_File,
                         b_travel=B_TRAVEL)

        """Process lookups to get top n, and get travel time as json fragment"""
        """process_lkp_list_with_travel(df_lkp, df_fs, top_n=NUMBER_CLOSEST, 
        json_file=firestation_nearest_json_with_travel)"""

        LOGGER.info('Completed run.')

    except FirestationIngestError as recex:
        LOGGER.error("An Exception occurred Firestation Ingest  ")
        LOGGER.error(recex.data)
        raise FirestationIngestError(recex)

    except Exception:
        LOGGER.error("An Exception occurred Firestation Ingest ")
        LOGGER.error(str(sys.exc_info()[0]))
        LOGGER.error(str(sys.exc_info()[1]))
        # print getattr(e, 'message', repr(e))
        # print(e.message)
        raise Exception("!")

############################################################
# TODO - Get accuracy based on font colour
############################################################
def get_accuracy(row_string):
    """get table from html page

    Keyword arguments:
    row_string -- html row string
    """

   # WHITE = plot is accurate(i.e.on correct building) - style='color:white;'
   #  RED = plot is not accurate(i.e. not on correct building) - style='color:red;'
   #  YELLOW = plot is very rough(i.e.only at start of street)- style='color:yellow;'
   #  BLUE = no plot - can you help?- style='color:blue;'
   #  """

############################################################
# Process the base addresses, get lat/lon from postcode
############################################################
def get_lat_long_lkp_addresses(lkp_addresses_file):
    """Get firestation lookup addresses from file

    Keyword arguments:
    lkp_addresses_file -- file of lookup addresses
    """

    # Cater for numeric string fields
    df = pandas.read_csv(lkp_addresses_file,
                         dtype={'address1': 'S100', 'address2': 'S100'})

    lat_list = []
    lon_list = []

    for index, row in df.iterrows():

        pc_json = UO_API_LOOKUP.do_postcode_lookup(row['postcode'])

        json_str = json.dumps(pc_json)
        resp = json.loads(json_str)

        lat_value = resp['result']['latitude']
        lon_value = resp['result']['longitude']

        lon_list.append(resp['result']['longitude'])
        lat_list.append(resp['result']['latitude'])

    df['longitude'] = lon_list
    df['latitude'] = lat_list

    return df


############################################################
# Process the list of lookups and get the list of closest n
# firestations for each
############################################################
def process_lkp_list(df_lkp, firestations_df, top_n, json_file, b_travel):
    """Process the list of lookup addresses to get nearest n

    Keyword arguments:
    lkp_list -- base point (lat_value, lon_value)
    firestations_df -- data frame of firestation data
    """
    r_list = defaultdict(list)
    lkp_list = []

    for index, row in df_lkp.iterrows():

        nearest_list = []

        lat_value = row['latitude']
        lon_value = row['longitude']

        LOGGER.debug("process_lkp_list :lat_value: %s", str(lat_value))
        LOGGER.debug("process_lkp_list :lon_value: %s", str(lon_value))

        lkp_list = df_lkp.values[index].tolist()

        base_point = (lat_value, lon_value)  # (lat, lon)

        """Return sorted list of nearest by distance"""
        df_fs_dist_list = UO_GET_NEAREST.create_nearest_list(base_point,
                                              firestations_df=firestations_df)

        lkp_list.append(df_fs_dist_list)

        r_list["lkpaddress"].append(lkp_list)

    """save as json"""
    json.dump(r_list, open(json_file, "w"))

############################################################
# Run
############################################################

if __name__ == "__main__":

    try:

        dirname = os.path.dirname(__file__)
        filename_ini = os.path.join(dirname, 'firestation_ingest.ini')
        UO_HELPER = HelperFunctions()

        configImport = UO_HELPER.load_config(filename_ini)

        LOG_PATH = configImport["logging.log_path"]
        LOG_FILE = configImport["logging.log_file"]
        THE_LOG = LOG_PATH + "\\" + LOG_FILE
        LOGGING_LEVEL = configImport["logging.logginglevel"]
        DISTANCE_MATRIX_API_KEY = configImport["firestation.api_key"]
        POSTCODE_API_URL = configImport["firestation.postcode_api_url"]
        B_TRAVEL = bool(configImport["firestation.b_travel"])
        NUMBER_CLOSEST = configImport["firestation.number_closest"]
        FIRESTATION_URL = configImport["firestation.url"]
        TEMP_FILE = configImport["firestation.temp_file"]
        CSV_FILE = configImport["firestation.csv_file"]
        TABLE_CLASS = configImport["firestation.table_class"]
        FORM_VALUE = configImport["firestation.form_value"]

        LEVELS = {'debug': logging.DEBUG,
                  'info': logging.INFO,
                  'warning': logging.WARNING,
                  'error': logging.ERROR,
                  'critical': logging.CRITICAL}

        # create LOGGER
        LOGGER = logging.getLogger('firestation')
        LEVEL = LEVELS.get(LOGGING_LEVEL, logging.NOTSET)
        logging.basicConfig(level=LEVEL)

        HANDLER = logging.handlers.RotatingFileHandler(THE_LOG, maxBytes=1036288, backupCount=5)
        # create FORMATTER
        FORMATTER = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        HANDLER.setFormatter(FORMATTER)
        LOGGER.addHandler(HANDLER)
        UO_DISTANCE_CALC = DistanceCalc(DISTANCE_MATRIX_API_KEY)
        UO_API_LOOKUP = APILookup(POSTCODE_API_URL)
        UO_GET_NEAREST = GetNearest(top_n=NUMBER_CLOSEST, bln_travel_times=B_TRAVEL, api_key=DISTANCE_MATRIX_API_KEY)

        main()

    except FirestationIngestError as exrec:
        LOGGER.error("Error in ingest - please check:" + str(exrec.data))
        raise Exception("Fire station ingest failed - please check")

    except Exception:
        LOGGER.error("An Exception in : MAIN :" + __name__)
        LOGGER.error(str(sys.exc_info()[0]))
        LOGGER.error(str(sys.exc_info()[1]))
        # print getattr(e, 'message', repr(e))
        # print(e.message)
        raise Exception("Fire station ingest failed - please check")
