import pytest
import logging
import os.path
import random
import string
import re
import os
import json

from atomic_operator.utils.logger import LogParam, Event
from atomic_operator_attire_logger.attire_file_handler import AttireFileHandler

root_directory = "../tests"
attire_file_regex = re.compile('^attire-.+json$')


@pytest.fixture
def attire_logger():
    logging.basicConfig(
        format='%(message)s',
        level=logging.INFO,
        datefmt='%m/%d/%Y %I:%M:%S %p'
    )

    attire_logger = logging.getLogger('test')
    attire_logger.setLevel(logging.INFO)
    ah = AttireFileHandler(encoding="utf8")
    ah.setLevel(logging.INFO)

    formatter = logging.Formatter('%(message)s')
    ah.setFormatter(formatter)

    attire_logger.addHandler(ah)

    return attire_logger


def valid_json_log_file_exists(filename):
    try:
        with open(filename) as json_data:
            d = json.load(json_data)
            return True

    except:
        print("Can't open file")
        return False


def attire_files_exist_in_test_dir():
    for root, dirs, files in os.walk(root_directory):
        for file in files:
            if attire_file_regex.match(file):
                return True

    return False


def test_emit_basic_log_doesnt_write_output(attire_logger):
    attire_logger.info("do nothing")

    assert not attire_files_exist_in_test_dir()


def test_emit_log_writes_file(attire_logger):
    attire_logger.info(f"Running 1 atomics test",
                       extra={
                           LogParam.EVENT.value: Event.ATOMIC_RUN_EXEC.value,
                           LogParam.OPERATOR_COMMAND.value: "atomic-operator run --techniques T1033 ",
                           LogParam.TIME_STAMP.value: "2022-04-08T02:00:00.000Z",
                           LogParam.TARGET_HOST_NAME: "test-hostname",
                           LogParam.TARGET_IP.value: "192.168.1.10",
                           LogParam.EXECUTION_ID.value: "TEST_EXEC_ID1"
                       })

    attire_logger.info(f"Atomic test complete TEST NAME",
                       extra={
                           LogParam.EVENT.value: Event.ATOMIC_TEST_COMPLETE.value,
                           LogParam.PROCEDURE_NAME.value: "Test Procedure",
                           LogParam.PROCEDURE_DESCRIPTION.value: "Procedure Description",
                           LogParam.PROCEDURE_GUID.value: "1111-test",
                           LogParam.EXECUTOR_COMMAND.value: "dir",
                           LogParam.EXECUTOR.value: "cmd",
                           LogParam.EVENT_TECHNIQUE_ID.value: "T1053",
                           LogParam.TIME_START.value: "2022-04-08T02:00:01.000Z",
                           LogParam.TIME_STOP.value: "2022-04-09T02:00:02.000Z",
                           LogParam.STD_OUTPUT.value: "some\nmulti\nline\noutput",
                           LogParam.EXECUTION_ID.value: "TEST_EXEC_ID1",
                           LogParam.STD_ERROR.value: "some\nmulti\nline\noutput"

                       })

    assert valid_json_log_file_exists("attire-TEST_EXEC_ID1.json")
    os.remove("attire-TEST_EXEC_ID1.json")


def test_write_a_ton_of_data(attire_logger):
    attire_logger.info(f"Running 1 atomics",
                       extra={
                           LogParam.EVENT.value: Event.ATOMIC_RUN_EXEC.value,
                           LogParam.OPERATOR_COMMAND.value: "atomic-operator command-line args test2",
                           LogParam.TIME_STAMP.value: "2022-04-08T03:00:00.000Z",
                           LogParam.TARGET_HOST_NAME: "test-hostname",
                           LogParam.TARGET_IP.value: "192.168.1.10",
                           LogParam.EXECUTION_ID.value: "TEST_EXEC_ID2"
                       })

    letters = string.printable
    for x in range(200):
        attire_logger.info(f"Atomic test complete TEST NAME(" + str(x) + ")",
                           extra={
                               LogParam.EVENT.value: Event.ATOMIC_TEST_COMPLETE.value,
                               LogParam.PROCEDURE_NAME.value: "Test Procedure (" + str(x) + ")",
                               LogParam.PROCEDURE_DESCRIPTION.value: "Procedure Description",
                               LogParam.PROCEDURE_GUID.value: "1111-test" + str(x),
                               LogParam.EXECUTOR_COMMAND.value: "dir",
                               LogParam.EXECUTOR.value: "cmd",
                               LogParam.EVENT_TECHNIQUE_ID.value: "T1053",
                               LogParam.TIME_START.value: "2022-04-08T02:00:01.000Z",
                               LogParam.TIME_STOP.value: "2022-04-09T02:00:02.000Z",
                               LogParam.STD_OUTPUT.value: ''.join(
                                   random.choice(letters) for i in range(random.randint(0, 9000))),
                               LogParam.EXECUTION_ID.value: "TEST_EXEC_ID2",
                               LogParam.STD_ERROR.value: "some\nmulti\nline\noutput"

                           })

    assert valid_json_log_file_exists("attire-TEST_EXEC_ID2.json")
    os.remove("attire-TEST_EXEC_ID2.json")
