import argparse
import logging
import os

from wazuh_testing.qa_docs.lib.config import Config
from wazuh_testing.qa_docs.lib.index_data import IndexData
from wazuh_testing.qa_docs.lib.sanity import Sanity
from wazuh_testing.qa_docs.doc_generator import DocGenerator

VERSION = '0.1'
CONFIG_PATH = 'wazuh_testing/qa_docs/config.yaml'

def start_logging(folder, debug_level=logging.INFO):
    LOG_PATH = os.path.join(folder, os.path.splitext(os.path.basename(__file__))[0]+".log")
    if not os.path.exists(folder):
        os.makedirs(folder)
    logging.basicConfig(filename=LOG_PATH, level=debug_level)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', help="Run a sanity check", action='store_true', dest='sanity')
    parser.add_argument('-v', help="Print version", action='store_true', dest="version")
    parser.add_argument('-t', help="Test configuration", action='store_true', dest='test_config')
    parser.add_argument('-d', help="Enable debug messages.", action='count', dest='debug_level')
    parser.add_argument('-i', help="Indexes the data to elasticsearch.", dest='index_name')
    parser.add_argument('-l', help="Indexes the data and launch the application.", dest='launch_app')
    parser.add_argument('-T', help="Test name or path to parse.", dest='test_input')
    parser.add_argument('-o', help="Output directory path.", dest='output_path')
    args = parser.parse_args()

    if args.debug_level:
        start_logging("wazuh_testing/qa_docs/logs", logging.DEBUG)
    else:
        start_logging("wazuh_testing/qa_docs/logs")

    if args.version:
        print(f"qa-docs v{VERSION}")
    elif args.test_config:
        Config(CONFIG_PATH)
    elif args.sanity:
        sanity = Sanity(Config(CONFIG_PATH))
        sanity.run()
    elif args.index_name:
        indexData = IndexData(args.index_name, Config(CONFIG_PATH))
        indexData.run()
    elif args.launch_app:
        indexData = IndexData(args.launch_app, Config(CONFIG_PATH))
        indexData.run()
        os.chdir('wazuh_testing/qa_docs/Search-UI')
        os.system("ELASTICSEARCH_HOST=http://localhost:9200 npm start")
    else:
        docs = DocGenerator(Config(CONFIG_PATH))
        if args.test_input:
            docs = DocGenerator(Config(CONFIG_PATH, args.test_input, args.output_path))
        docs.run()

    if __name__ == '__main__':
        main()