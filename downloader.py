from concurrent.futures import ThreadPoolExecutor, as_completed
from console_manager import root_p, console
import requests
import time
import os
import uuid


'''
TODO:
    > Add single part download for websites that don't support multi-part
    > Consider connection count limit
'''


class Download:
    '''main Download class that handles downloading and merging the files'''
    WRITE_CHUNK_SIZE = 1000 * 1000 * 10
    TEMP_FILES = r"temp/"
    try:
        os.mkdir(TEMP_FILES)
    except FileExistsError:
        pass

    def __init__(self, url, name, **kwargs) -> None:
        self.url = url
        self.name = name
        self.config = kwargs
        self.ranges = dict()
        self.progress = root_p

    def initial_check(self):
        '''Checks for downloadabilty of file and also sets up some initial data like size and parts'''
        try:
            req = requests.get(self.url, stream=True)
            if req.status_code not in range(200, 300):
                raise requests.exceptions.ConnectionError
            if "Content-Length" in req.headers:
                self.size = int(req.headers['Content-Length'])
                self.ranges = {uuid.uuid4().hex: chunk for chunk in self.chunkify(self.size)}
            else:
                self.size = 0
                self.ranges = [None]
            return True

        except requests.exceptions.ConnectionError:
            console.print(f'Connection Error {self.name}')
            return False
        except Exception:
            console.print(f'Unknown Error {self.name}')
            return False

    def chunkify(self, size, parts=6) -> list:
        '''divides a range into n sub ranges'''
        chunk = size // (self.config.get('threads') or parts)
        part = -1
        result = list()
        while size >= chunk:
            size -= chunk
            result.append((part + 1, part + chunk))
            part += chunk
        result.append((part + 1, part + size))
        return result

    def worker(self, id: str) -> None:
        ''' downloads and write chunk into temp file '''
        headers = {'Range': f'bytes={self.ranges[id][0]}-{self.ranges[id][1]}'}
        while True:
            try:
                chunk = requests.get(self.url, headers=headers, stream=True)
                if(chunk.status_code not in range(200, 300)):
                    raise requests.ConnectTimeout
                if int(chunk.headers['Content-Length']) != (self.ranges[id][1] - self.ranges[id][0]) + 1:
                    raise Exception
                with open(Download.TEMP_FILES + id, 'wb') as file:
                    for content in chunk.iter_content(Download.WRITE_CHUNK_SIZE):
                        self.progress.advance(self.task, file.write(content))
                return
            except requests.ConnectTimeout:
                time.sleep(5)

    def cleanup(self):
        '''join the temp files and remove them'''
        self.progress.update(self.task, description=f"Joining {self.name}")
        with open(self.name, 'wb') as f:
            for part in self.ranges:
                with open(Download.TEMP_FILES + part, 'rb') as file:
                    f.write(file.read())
                os.remove(f'{Download.TEMP_FILES + part}')
        self.progress.update(self.task, description=f"Done {self.name}")

    def start(self):
        '''download starts here as well as terminal output managment'''
        self.is_downloadable = self.initial_check()  # main programm checks this before calling start()
        if not self.is_downloadable:
            return

        self.start_time = time.time()
        self.progress.start()
        self.task = self.progress.add_task(f"[red]Downloading {self.name}", total=self.size)

        with ThreadPoolExecutor(max_workers=6) as self.exc:
            self.workers = {self.exc.submit(self.worker, r): r for r in self.ranges}
            for _ in as_completed(self.workers):
                pass

        self.cleanup()
        if self.progress.finished:  # chekc to see if any taks left undone
            self.progress.stop()
