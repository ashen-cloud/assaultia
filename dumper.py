#!/usr/bin/python3

import subprocess
import ctypes
import struct
import sys
import threading
import time

from multiprocessing import Pool

sys.set_int_max_str_digits(10000000)


class Dumper:

    pid = None
    mem_file_path = None

    def __init__(self, pid):
        self.pid = pid
        self.maps_file_path = f"/proc/{self.pid}/maps"
        self.mem_file_path = f"/proc/{self.pid}/mem"

    def read_maps(self, include_libs=True):

        maps = []
        raw = []

        with open(self.maps_file_path) as f:
            for line in f:
                parts = line.split()
                if not include_libs and len(parts) > 5:  # last item (6) is library name
                    continue
                addr_range = parts[0].split("-")
                start = int(addr_range[0], 16)
                end = int(addr_range[1], 16)
                raw.append(line)
                maps.append((start, end))

            return maps, raw  # maps is a list of tuples containing memory ranges in int format

    def read(self, address, length=4):
        try:
            with open(self.mem_file_path, 'rb') as f:
                f.seek(address)
                data = f.read(length)
                return data
        except OSError:
            pass


if __name__ == '__main__':
    def psearch(name):
        res = subprocess.check_output(['pgrep', name])
        return int(res.decode("utf-8").split('\n')[1])

    address = None
    pid = None

    def run_read_test():
        global address, pid
        with subprocess.Popen(['./test/mem'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=0) as r:
            for line in r.stdout:
                txt = line.strip()
                if 'Address' in txt:
                    address = txt.split(' ')[1]
                if 'PID' in txt:
                    pid = txt.split(' ')[1]
        return pid, address

    t = threading.Thread(target=run_read_test)
    t.daemon = True
    t.start()
    time.sleep(0.5)

    dumper = Dumper(pid)

    maps, raw_maps = dumper.read_maps()

    def get_stack():
        for line in raw_maps:
            rng = [l.replace(' ' * 7, '') for l in line.strip().split(' ' * 19)]
            if '[stack]' in rng:
                return rng[0].split(' ')[0].split('-')

    stack, stack_end = get_stack()

    stack = int(stack, 16)
    stack_end = int(stack_end, 16)

    address = int(address, 16)
    print('address index in stack', range(stack, stack_end).index(address))

    while True:
        res = dumper.read(address, 4)
        print(int.from_bytes(res, 'little'))
        time.sleep(1)

