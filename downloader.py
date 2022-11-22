from concurrent.futures import ThreadPoolExecutor, as_completed
#from console import progress, tasks
from rich.progress import DownloadColumn, Progress, TransferSpeedColumn
from rich.console import Console
import requests
import time
import os
import uuid


'''
TODO:
    > Add single part download for websites that don't support multi-part
    > Consider connection count limit
'''

console = Console()

class Download:
    '''main Download class that handles downloading and merging the files'''
    WRITE_CHUNK_SIZE = 1000 * 1000 * 2
    TEMP_FILES = r"temp/"
    os.mkdir(TEMP_FILES)
    def __init__(self, url, name, **kwargs) -> None:
        self.url = url
        self.name = name
        self.config = kwargs
        self.ranges = dict()
        self.is_downloadable = self.initial_check()  # main programm checks this before calling start()


    def initial_check(self):
        '''Checks for downloadabilty of file and also sets up some initial data like size and parts'''
        try:
            req = requests.get(self.url, stream=True)
            if req.status_code not in range(200, 300):
                raise requests.exceptions.ConnectionError
            if "Content-Length" in req.headers:
                self.size = int(req.headers['Content-Length'])
                self.ranges = {uuid.uuid4().hex:chunk for chunk in self.chunkify(self.size)}
            else:
                self.size = 0
                self.ranges = [None]
            return True
            
        except requests.exceptions.ConnectionError:
            print('Connection Error')
            return False
        except:
            print('Unknown Error')
            return False

    def chunkify(self, size, parts=6) -> list:
        '''divides a range into n sub ranges'''
        chunk = size // (self.config.get('threads') or parts)
        part = -1
        result = list()
        while size >= chunk:
            size -= chunk
            result.append((part+1, part+chunk))
            part += chunk
        result.append((part+1, part+size))
        return result
    
    def worker(self, id: str) -> None: # downloads and write chunk into temp file
        headers = {'Range': f'bytes={self.ranges[id][0]}-{self.ranges[id][1]}'}
        while True:
            try:
                chunk = requests.get(self.url, headers=headers, stream=True)
                if(chunk.status_code not in range(200, 300)):
                    raise requests.ConnectTimeout
                if int(chunk.headers['Content-Length']) != (self.ranges[id][1] - self.ranges[id][0])+1:
                    raise Exception
                with open(Download.TEMP_FILES+id, 'wb') as file:
                    for content in chunk.iter_content(Download.WRITE_CHUNK_SIZE):
                        #file.write(content)
                        #self.progress.update(self.task, advance=file.write(content))
                        self.progress.advance(self.task, file.write(content))
                return
            except requests.ConnectTimeout:
                time.sleep(5)
            #except:
            #    return
    
    def cleanup(self):
        with open(self.name, 'wb') as f:
            for part in self.ranges:
                with open(Download.TEMP_FILES+part, 'rb') as file:
                    f.write(file.read())
                os.remove(f'{Download.TEMP_FILES+part}')

    
    def start(self):
        self.start_time = time.time()
        columns = (*Progress.get_default_columns(), DownloadColumn(), TransferSpeedColumn())
        with Progress(*columns ,console=console, auto_refresh=True) as self.progress:
            self.task = self.progress.add_task("[red]Downloading...", total=self.size)
            with ThreadPoolExecutor(max_workers=6) as self.exc:
                self.workers = {self.exc.submit(self.worker, r): r for r in self.ranges}
                for _ in as_completed(self.workers):
                    pass
        with console.status("Joining Files"):
            self.cleanup()
        console.print("Done!")