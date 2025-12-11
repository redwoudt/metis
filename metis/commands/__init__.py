from .search import SearchWebCommand
from .generate import GenerateImageCommand
from .sql import ExecuteSqlCommand
from .schedule import ScheduleTaskCommand

command_registry = {
    "search_web": SearchWebCommand,
    "generate_image": GenerateImageCommand,
    "execute_sql": ExecuteSqlCommand,
    "schedule_task": ScheduleTaskCommand,
}