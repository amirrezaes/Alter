import time
from rich.progress import Progress
from rich.layout import Layout
from rich.live import Live
from rich.prompt import Prompt
from rich.text import Text
from threading import Thread
layout = Layout()
progress = Progress()
question = Prompt("hello")
l = Live(layout, refresh_per_second=4)
l.start()
layout.split_column(
    Layout(name="upper", renderable=progress),
    Layout(name="lower", renderable=None)
)


task1 = progress.add_task("[red]Downloading...", total=1000)
task2 = progress.add_task("[green]Processing...", total=1000)
task3 = progress.add_task("[cyan]Cooking...", total=1000)
layout["lower"].update(question.ask)
t1 = Thread(target = layout['lower'].renderable)
t1.start()
while not progress.finished:
    progress.update(task1, advance=0.5)
    progress.update(task2, advance=0.3)
    progress.update(task3, advance=0.9)
    time.sleep(0.02)
    #print(layout)
l.stop()