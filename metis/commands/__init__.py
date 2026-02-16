from .search import SearchWebCommand
from .generate import GenerateImageCommand
from .sql import ExecuteSQLCommand
from .schedule import ScheduleTaskCommand

command_registry = {
    "search_web": SearchWebCommand,
    "generate_image": GenerateImageCommand,
    "execute_sql": ExecuteSQLCommand,
    "schedule_task": ScheduleTaskCommand,
}