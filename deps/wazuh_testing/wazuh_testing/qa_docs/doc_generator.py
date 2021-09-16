# Copyright (C) 2015-2021, Wazuh Inc.
# Created by Wazuh, Inc. <info@wazuh.com>.
# This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

import os
import re
import json
import yaml
from wazuh_testing.qa_docs.lib.config import Config, Mode
from wazuh_testing.qa_docs.lib.code_parser import CodeParser
from wazuh_testing.qa_docs.lib.utils import clean_folder
from wazuh_testing.qa_docs import QADOCS_LOGGER
from wazuh_testing.tools.logging import Logging
from wazuh_testing.tools.exceptions import QAValueError

class DocGenerator:
    """
    brief: Main class of DocGenerator tool.
    It´s in charge of walk every test file, and every group file to dump the parsed documentation.
    """
    LOGGER = Logging.get_logger(QADOCS_LOGGER)

    def __init__(self, config):
        self.conf = config
        self.parser = CodeParser(self.conf)
        self.__id_counter = 0
        self.ignore_regex = []
        for ignore_regex in self.conf.ignore_paths:
            self.ignore_regex.append(re.compile(ignore_regex))
        self.include_regex = []
        if self.conf.mode == Mode.DEFAULT:
            for include_regex in self.conf.include_regex:
                self.include_regex.append(re.compile(include_regex))

    def is_valid_folder(self, path):
        """
        brief: Checks if a path should be ignored because it is in the ignore list.
        args:
            - "path (str): Folder location to be controlled"
        returns: "boolean: False if the path should be ignored. True otherwise."
        """
        for regex in self.ignore_regex:
            if regex.match(path):
                DocGenerator.LOGGER.warning(f"Folder validation: {regex} not matching with {path}")
                return False

        return True

    def is_valid_file(self, file):
        """
        brief: Checks if a file name should be ignored because it's in the ignore list
        or doesn´t match with the regexes.
        args:
            - "file (str): File name to be controlled"
        returns: "boolean: False if the file should be ignored. True otherwise."
        """

        for regex in self.ignore_regex:
            if regex.match(file):
                DocGenerator.LOGGER.warning(f"File validation: {regex} not matching with {file}")
                return False

        for regex in self.include_regex:
            if regex.match(file):
                DocGenerator.LOGGER.warning(f"File validation: {regex} not matching with {file}")
                return True

        return False

    def is_group_file(self, path):
        """
        brief: Checks if a file path should be considered as a file containing group information.
        args:
            - "path (str): File location to be controlled"
        returns: "boolean: True if the file is a group file. False otherwise."
        """

        for group_file in self.conf.group_files:
            if path == group_file:
                return True

        return False

    def get_group_doc_path(self, group):
        """
        brief: Returns the name of the group file in the documentation output based on the original file name.
        returns: "string: The name of the documentation group file"
        """
        base_path = os.path.join(self.conf.documentation_path, os.path.basename(self.scan_path))
        doc_path = os.path.join(base_path, group['name']+".group")

        return doc_path

    def get_test_doc_path(self, path):
        """
        brief: Returns the name of the test file in the documentation output based on the original file name.
        args:
            - "path (str): The original file name"
        returns: "string: The name of the documentation test file"
        """
        base_path = os.path.join(self.conf.documentation_path, os.path.basename(self.scan_path))
        relative_path = path.replace(self.scan_path, "")
        doc_path = os.path.splitext(base_path + relative_path)[0]

        return doc_path

    def dump_output(self, content, doc_path):
        """
        brief: Creates a JSON and a YAML file with the parsed content of a test module.
        It also creates the containing folder if it doesn´t exists.
        args:
            - "content (dict): The parsed content of a test file."
            - "doc_path (string): The path where the information should be dumped."
        """
        if not os.path.exists(os.path.dirname(doc_path)):
            DocGenerator.LOGGER.debug('Creating documentation folder')
            os.makedirs(os.path.dirname(doc_path))

        try:
            DocGenerator.LOGGER.debug(f"Writing {doc_path}.json")
            with open(doc_path + ".json", "w+") as out_file:
                out_file.write(json.dumps(content, indent=4))
        except IOError:
            raise QAValueError(f"Cannot write in {doc_path}.json", DocGenerator.LOGGER.error)

        try:
            DocGenerator.LOGGER.debug(f"Writing {doc_path}.yaml")
            with open(doc_path + ".yaml", "w+") as out_file:
                out_file.write(yaml.dump(content))
        except IOError:
            raise QAValueError(f"Cannot write in {doc_path}.yaml", DocGenerator.LOGGER.error)

    def create_group(self, path, group_id):
        """
        brief: Parses the content of a group file and dumps the content into a file.
        args:
            - "path (string): The path of the group file to be parsed."
            - "group_id (string): The id of the group where the new group belongs."
        return "integer: The ID of the new generated group document.
        """
        self.__id_counter = self.__id_counter + 1
        group = self.parser.parse_group(path, self.__id_counter, group_id)

        if group:
            doc_path = self.get_group_doc_path(group)
            self.dump_output(group, doc_path)
            DocGenerator.LOGGER.debug(f"New group file '{doc_path}' was created with ID:{self.__id_counter}")
            return self.__id_counter
        else:
            DocGenerator.LOGGER.warning(f"Content for {path} is empty, ignoring it")
            return None

    def create_test(self, path, group_id):
        """
        brief: Parses the content of a test file and dumps the content into a file.
        args:
            - "path (string): The path of the test file to be parsed."
            - "group_id (string): The id of the group where the new test belongs."
        return "integer: The ID of the new generated test document.
        """
        self.__id_counter = self.__id_counter + 1
        test = self.parser.parse_test(path, self.__id_counter, group_id)

        if test:
            if self.conf.mode == Mode.DEFAULT:
                doc_path = self.get_test_doc_path(path)
            elif self.conf.mode == Mode.SINGLE_TEST:
                doc_path = self.conf.documentation_path
                if self.print_test_info(test) is None:
                    # 
                    return
            self.dump_output(test, doc_path)
            DocGenerator.LOGGER.debug(f"New documentation file '{doc_path}' was created with ID:{self.__id_counter}")
            return self.__id_counter
        else:
            DocGenerator.LOGGER.warning(f"Content for {path} is empty, ignoring it")
            return None

    def parse_folder(self, path, group_id):
        """
        brief: Search in a specific folder to parse possible group files and each test file.
        args:
            - "path (string): The path of the folder to be parsed."
            - "group_id (string): The id of the group where the new elements belong."
        """
        if not os.path.exists(path):
            DocGenerator.LOGGER.warning(f"Include path '{path}' doesn´t exist")
            return

        if not self.is_valid_folder(path):
            DocGenerator.LOGGER.debug(f"Ignoring files on '{path}'")
            return

        (root, folders, files) = next(os.walk(path))
        for file in files:
            if self.is_group_file(file):
                new_group = self.create_group(os.path.join(root, file), group_id)
                if new_group:
                    group_id = new_group
                    break

        for file in files:
            if self.is_valid_file(file):
                self.create_test(os.path.join(root, file), group_id)

        for folder in folders:
            self.parse_folder(os.path.join(root, folder), group_id)

    def locate_test(self):
        """
        brief: try to get the test path
        """
        complete_test_name = f"{self.conf.test_name}.py"
        DocGenerator.LOGGER.info(f"Looking for {complete_test_name}")

        for root, dirnames, filenames in os.walk(self.conf.project_path, topdown=True):
            for filename in filenames:
                if filename == complete_test_name:
                    return os.path.join(root, complete_test_name)

        print('test does not exist')
        return None

    def print_test_info(self, test):
        """
        brief: Print the test info to standard output. If an output path is specified,
               the output is redirected to `output_path/test_info.json`.
        """
        # dump into file
        if self.conf.documentation_path:
            test_info = {}
            # Need to be changed, it is hardcoded
            test_info['test_path'] = self.test_path[6:]

            for field in self.conf.module_info:
                for name, schema_field in field.items():
                    test_info[name] = test[schema_field]

            for field in self.conf.test_info:
                for name, schema_field in field.items():
                    test_info[name] = test['tests'][0][schema_field]
            
            # If output path does not exist, it is created
            if not os.path.exists(self.conf.documentation_path):
                os.mkdir(self.conf.documentation_path)

            # Dump data
            with open(os.path.join(self.conf.documentation_path, f"{self.conf.test_name}.json"), 'w') as fp:
                fp.write(json.dumps(test_info, indent=4))
                fp.write('\n')
        else:
            # Use the key that QACTL needs
            for field in self.conf.module_info:
                for name, schema_field in field.items():
                    print(str(name)+": "+str(test[schema_field]))

            for field in self.conf.test_info:
                for name, schema_field in field.items():
                    print(str(name)+": "+str(test['tests'][0][schema_field]))
                    
            return None

    def run(self):
        """
        brief: Run a complete scan of each include path to parse every test and group found.
               Normal mode: expected behaviour, Single test mode: found the test required and par it
        """
        if self.conf.mode == Mode.DEFAULT:
            DocGenerator.LOGGER.info("Starting documentation parsing")
            DocGenerator.LOGGER.debug(f"Cleaning doc folder located in {self.conf.documentation_path}")
            clean_folder(self.conf.documentation_path)

            for path in self.conf.include_paths:
                self.scan_path = path
                DocGenerator.LOGGER.debug(f"Going to parse files on '{path}'")
                self.parse_folder(path, self.__id_counter)

        elif self.conf.mode == Mode.SINGLE_TEST:
            DocGenerator.LOGGER.info("Starting test documentation parsing")
            self.test_path = self.locate_test()
            
            if self.test_path:
                DocGenerator.LOGGER.debug(f"Parsing '{self.conf.test_name}'")
                self.create_test(self.test_path, 0)
            else:
                DocGenerator.LOGGER.error(f"'{self.conf.test_name}' could not be found")
