import random
import urllib.request

extent = input("What is your file type ?\n")

url = input("Paste Your URL\n")
def Downloader(url):
    name = random.randrange(1,10000)
    filename = str(name) + '.' + extent 
    urllib.request.urlretrieve(url,filename)
        
Downloader(url)
