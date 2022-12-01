import argparse
import threading
import downloader
import itertools
from console_manager import user_input, root_p

RUNNING = True

parser = argparse.ArgumentParser()
parser.add_argument("-o", "--output", nargs="*", help="name and directory for the output file")
parser.add_argument("url", nargs="+", help="url to download")
args = parser.parse_args()

threads = []
for task in itertools.zip_longest(args.url, args.output, fillvalue=None):
    task = downloader.Download(task[0], task[1])
    threads.append(threading.Thread(target=task.start))

for thread in threads:
    thread.start()
for thread in threads:
    thread.join()

# This part will be implemented later on
''''
def hook():
    while RUNNING:
        choice = user_input("Select what you wanna do? ADD/STOP", console=root_p.console, choices=["A", "S"])
        if choice == "A":
            url = user_input("url: ",console=root_p.console)
            name = user_input("name: ", console=root_p.console)
            task = downloader.Download(url, name)
            threads.append(threading.Thread(target=task))
        elif choice == "S":
            return

input_thread = threading.Thread(target=hook)
input_thread.start()
while any(thread.is_alive for thread in threads):
    pass
RUNNING = False
'''