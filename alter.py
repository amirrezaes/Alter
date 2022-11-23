import argparse
import threading
import downloader
import itertools

parser = argparse.ArgumentParser()
parser.add_argument("-o", "--output", nargs="*", help="name and directory for the output file")
parser.add_argument("url", nargs="+", help="url to download")
args = parser.parse_args()

threads = []
for task in itertools.zip_longest(args.url, args.output, fillvalue=None):
    task = downloader.Download(task[0], task[1])
    threads.append(threading.Thread(target=task.start))
