#!/usr/bin/env python3
"""Serve the local book with byte ranges, so video scrubbing works in browsers."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse
import os
import re


class BookHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Accept-Ranges', 'bytes')
        super().end_headers()

    def send_head(self):
        self.remaining = None
        path = self.translate_path(self.path)
        value = self.headers.get('Range', '')
        match = re.fullmatch(r'bytes=(\d*)-(\d*)', value)
        if not match or not os.path.isfile(path):
            return super().send_head()
        file = open(path, 'rb')
        size = os.fstat(file.fileno()).st_size
        lo, hi = match.groups()
        if lo:
            start = int(lo)
            end = min(int(hi), size-1) if hi else size-1
        elif hi:
            start, end = max(0, size-int(hi)), size-1
        else:
            file.close()
            return super().send_head()
        if start >= size or end < start:
            file.close()
            self.send_response(416)
            self.send_header('Content-Range', f'bytes */{size}')
            self.send_header('Content-Length', '0')
            self.end_headers()
            return None
        file.seek(start)
        self.remaining = end-start+1
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(path))
        self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.send_header('Content-Length', str(self.remaining))
        self.end_headers()
        return file

    def copyfile(self, source, outputfile):
        if self.remaining is None:
            return super().copyfile(source, outputfile)
        try:
            while self.remaining:
                data = source.read(min(64*1024, self.remaining))
                if not data:
                    break
                outputfile.write(data)
                self.remaining -= len(data)
        except (BrokenPipeError, ConnectionResetError):
            pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8769)
    args = parser.parse_args()
    directory = Path(__file__).resolve().parents[1] / 'docs'
    server = ThreadingHTTPServer(('127.0.0.1', args.port), partial(BookHandler, directory=str(directory)))
    print(f'Book preview: http://127.0.0.1:{args.port}/', flush=True)
    server.serve_forever()
