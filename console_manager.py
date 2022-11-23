from rich.console import Console
from rich.progress import Progress, DownloadColumn, TransferSpeedColumn
console = Console()
columns = (*Progress.get_default_columns(), DownloadColumn(), TransferSpeedColumn())
root_p = Progress(*columns, console=console, auto_refresh=5)
