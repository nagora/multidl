# -*- coding: utf-8 -*-

import os
import time

import requests

from multidl.downloaders.abstract_downloader import AbstractDownloader
from multidl.constants import DownloadState


class HttpDownloader(AbstractDownloader):

    def __init__(self, url, output, **options):
        super().__init__(url, output, **options)
        self._download_length = 0
        self._downloaded_length = 0
        self.__request = None

    def start(self):
        super().start()

        self.__request = requests.get(self.url, stream=True)
        try:
            self._download_length = int(self.__request.headers['content-length'])
        except (KeyError, ValueError):
            pass

        with open(self.output, "wb") as f:
            for chunk in self.__get_chunk():
                f.write(chunk)
                self._downloaded_length += len(chunk)

        if self.state == DownloadState.canceling:
            self.state = DownloadState.canceled
        elif self.state != DownloadState.error:
            self.state = DownloadState.finished

    def __get_chunk(self):
        try:
            for chunk in self.__request.iter_content(chunk_size=1024):
                state = self.state
                while self.state == DownloadState.paused:
                    time.sleep(0.1)
                    state = self.state

                if state == DownloadState.started and chunk:  # ignore keep-alive chunks
                    yield chunk
                elif state != DownloadState.started:
                    break
        except Exception as e:
            self.state = DownloadState.error
            self._error = e

    def get_progress(self):
        super().get_progress()
        return self._downloaded_length, self._download_length

    def cancel(self):
        super().cancel()
        try:
            os.remove(self.output)
        except OSError:
            pass