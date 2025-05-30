# import tool functions
from .tool import download_stats_by_instance_id,download_stats_by_machine_key
from .tool import manual

# for sanity checking the import structure
def hello() -> None:
    print("hello from downloadstats")