from rich.console import Console
from rich.progress import Progress, DownloadColumn, TransferSpeedColumn
console = Console()
tasks = dict()
columns = (*Progress.get_default_columns(), DownloadColumn(), TransferSpeedColumn())
with Progress(*columns ,console=console, auto_refresh=5) as progress:
    while tasks:
        for task in tasks:
            progress.update(task, advance=tasks[task])
            tasks[task] = 0

