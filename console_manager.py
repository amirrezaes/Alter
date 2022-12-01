from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, DownloadColumn, TransferSpeedColumn
from rich.prompt import Prompt
console = Console()
columns = (*Progress.get_default_columns(), DownloadColumn(), TransferSpeedColumn())
root_p = Progress(*columns, console=console, auto_refresh=True)
user_input = Prompt.ask