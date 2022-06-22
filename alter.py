import argparse
import downloader

parser = argparse.ArgumentParser()
parser.add_argument("-o", "--output", help="name and directory for the output file")
parser.add_argument("url", help="url to download")

args = parser.parse_args()

