import json
from logging import LogRecord, Handler, DEBUG
from os.path import abspath, exists as file_exists

from atomic_operator.utils.logger import Event, LogParam

from py_attire_schema.schemas import ExecutionCategory, ExecutionData, AttireLog, AttireTarget, Procedure, \
    ProcedureId, Step, OutputItem


# Writes a new log file for each execution event
# Every atomic with output causes file i/o reading existing log content
# Injecting new log output in parsed JSON
# Then overwriting existing log file
#
# Predictable behavior and easier reading chosen over raw performance
# If I/O or memory use becomes an issue, refactor
class AttireFileHandler(Handler):

    def __init__(self, base_filename='attire', encoding=None):
        Handler.__init__(self)
        self.execution_id = None
        self.procedure_name_obj = {}
        self.encoding = encoding
        self.base_filename = base_filename
        # default to be overwritten
        self.filename = self.base_filename + ".json"
        self.temp_attire_log_data = AttireLog(attire_version='1.1')

    def emit(self, record: LogRecord):
        # only act on categorized logged events
        if hasattr(record, LogParam.EVENT.value):
            exec_id = self.get_execution_id_log_record(record)

            event = getattr(record, LogParam.EVENT.value)

            # temporary stateful cache of execution data
            if event == Event.ATOMIC_RUN_EXEC:
                self.temp_attire_log_data.execution_data = self.get_atomic_exec_data(record)
            # write execution data to file in addition to atomic output once writing actual atomic test results
            elif event == Event.ATOMIC_TEST_COMPLETE:
                attire_log_data = self.get_attire_log_file_content(exec_id)
                if attire_log_data is not None:
                    self.record_event_to_log_file(attire_log_data, self.get_atomic_test_as_procedure(record))

    def get_attire_log_file_content(self, execution_id: str):
        self.filename = self.get_attire_log_file_name(execution_id)
        if file_exists(self.filename):
            with open(self.filename) as f:
                log_file_data = f.read()

            return AttireLog.parse_obj(json.loads(log_file_data))
        elif isinstance(self.temp_attire_log_data, AttireLog):
            return self.temp_attire_log_data
        return None

    def record_event_to_log_file(self, attire_log_data: AttireLog, event_procedure: Procedure):
        attire_log_data.procedures.append(event_procedure)
        with open(self.filename, "w") as f:
            f.write(attire_log_data.json())

    def get_attire_log_file_name(self, execution_id: str):
        return abspath(self.base_filename + "-" + execution_id + ".json")

    def get_atomic_exec_data(self, record) -> ExecutionData:
        command = self.get_command_from_log_record(record)
        execution_id = self.get_execution_id_log_record(record)
        exec_data = ExecutionData(command="atomic-operator run --techniques " + command,
                                  execution_id=str(execution_id),
                                  source='Atomic Operator')
        exec_category = ExecutionCategory(name="Atomic Red Team", abbreviation="ART")
        target_ip = self.get_host_ip_log_record(record)
        target_host_name = self.get_host_name_log_record(record)
        exec_target = AttireTarget(ip=target_ip, host=target_host_name)
        exec_data.category = exec_category
        exec_data.target = exec_target
        exec_time = self.get_time_from_log_record(record)
        exec_data.time_generated = exec_time
        return exec_data

    def get_atomic_test_as_procedure(self, record: LogRecord) -> Procedure:
        procedure_name = self.get_procedure_name_record(record)
        procedure_description = self.get_procedure_description_record(record)
        procedure_guid = self.get_procedure_guid_record(record)
        executor_command = self.get_executor_command(record)
        executor = self.get_executor(record)
        technique_id = self.get_technique_id(record)
        time_start = self.get_time_start(record)
        time_stop = self.get_time_stop(record)
        stdout_capture = self.get_output(record)
        stderr_capture = self.get_errors(record)
        new_procedure = Procedure(procedure_name=procedure_name, procedure_description=procedure_description,
                                  mitre_technique_id=technique_id, order=1)
        procedure_uuid = ProcedureId(type="guid", id=procedure_guid)
        new_procedure.procedure_id = procedure_uuid
        step = Step(command=executor_command, executor=executor, order=1, time_start=time_start,
                    time_stop=time_stop)
        output_list = []
        if stdout_capture:
            output_list.append(OutputItem(content=stdout_capture.__str__(), level="stdout", type='Console'))
        if stderr_capture:
            output_list.append(OutputItem(content=stderr_capture.__str__(), level="stderr", type='Console'))

        step_list = [step]
        new_procedure.steps = step_list
        step.output = output_list
        return new_procedure

    def get_command_from_log_record(self, record: LogRecord):
        return getattr(record, LogParam.OPERATOR_COMMAND.value)

    def get_time_from_log_record(self, record: LogRecord):
        return getattr(record, LogParam.TIME_STAMP.value)

    def get_host_ip_log_record(self, record: LogRecord):
        return getattr(record, LogParam.TARGET_IP.value)

    def get_host_name_log_record(self, record: LogRecord):
        return getattr(record, LogParam.TARGET_HOST_NAME.value)

    def get_execution_id_log_record(self, record: LogRecord):
        return getattr(record, LogParam.EXECUTION_ID.value)

    def get_executor_log_record(self, record: LogRecord):
        return getattr(record, LogParam.EXECUTOR.value)

    def get_procedure_name_record(self, record: LogRecord):
        name = getattr(record, LogParam.PROCEDURE_NAME.value)
        if name not in self.procedure_name_obj:
            self.procedure_name_obj[name] = 0
        self.procedure_name_obj[name] += 1
        if self.procedure_name_obj[name] > 1:
            name += " (" + str(self.procedure_name_obj[name]) + ")"
        return name

    def get_procedure_description_record(self, record: LogRecord):
        return getattr(record, LogParam.PROCEDURE_DESCRIPTION.value)

    def get_procedure_guid_record(self, record: LogRecord):
        return getattr(record, LogParam.PROCEDURE_GUID.value)

    def get_executor_command(self, record: LogRecord):
        return getattr(record, LogParam.EXECUTOR_COMMAND.value)

    def get_executor(self, record: LogRecord):
        return getattr(record, LogParam.EXECUTOR.value)

    def get_technique_id(self, record: LogRecord):
        return getattr(record, LogParam.EVENT_TECHNIQUE_ID.value)

    def get_output(self, record: LogRecord):
        return getattr(record, LogParam.STD_OUTPUT.value)

    def get_errors(self, record: LogRecord):
        return getattr(record, LogParam.STD_ERROR.value)

    def get_time_start(self, record: LogRecord):
        return getattr(record, LogParam.TIME_START.value)

    def get_time_stop(self, record: LogRecord):
        return getattr(record, LogParam.TIME_STOP.value)
