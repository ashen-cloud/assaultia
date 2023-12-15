#!/usr/bin/python3

import subprocess
import ctypes
import struct
import sys
import threading
import time
import argparse

from multiprocessing import Pool
from argparse import ArgumentParser

sys.set_int_max_str_digits(10000000)

parser = ArgumentParser()

parser.add_argument("-t", "--test", action=argparse.BooleanOptionalAction, help="Run memory dumping tests")

args = parser.parse_args()


class Dumper:

    pid = None
    mem_file_path = None

    maps = []
    raw_maps = []

    def __init__(self, pid):
        self.pid = pid
        self.maps_file_path = f"/proc/{self.pid}/maps"
        self.mem_file_path = f"/proc/{self.pid}/mem"

    def read_maps(self, include_libs=True):

        with open(self.maps_file_path) as f:
            for line in f:
                parts = line.split()
                if not include_libs and len(parts) > 5:  # last item (6) is library name
                    continue
                addr_range = parts[0].split("-")
                start = int(addr_range[0], 16)
                end = int(addr_range[1], 16)
                self.raw_maps.append(line)
                self.maps.append((start, end))

            return self.maps, self.raw_maps  # maps is a list of tuples containing memory ranges in int format

    def read(self, address, length=4):
        try:
            with open(self.mem_file_path, 'rb') as f:
                f.seek(address)
                data = f.read(length)
                return data
        except OSError:
            pass

    def get_range(self, name):
        for line in self.raw_maps:
            rng = [l.replace(' ' * 7, '') for l in line.strip().split(' ' * 19)]
            if ('[' + name + ']') in rng:
                return rng[0].split(' ')[0].split('-')


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


def test_read():
    global address, pid

    def psearch(name):
        res = subprocess.check_output(['pgrep', name])
        return int(res.decode("utf-8").split('\n')[1])

    t = threading.Thread(target=run_read_test)
    t.daemon = True
    t.start()
    time.sleep(0.5)

    dumper = Dumper(pid)

    maps, raw_maps = dumper.read_maps()

    stack, stack_end = dumper.get_range('stack')

    stack = int(stack, 16)
    stack_end = int(stack_end, 16)

    print('Testing stack extract')

    assert len(range(stack, stack_end)) == 135168

    print('Passed ✓')

    print('Testing read')

    address = int(address, 16)
    print('address index in stack', range(stack, stack_end).index(address))

    res = dumper.read(address, 4)
    res_int = int.from_bytes(res, 'little')

    assert res_int == 1338

    print('Passed ✓')


if __name__ == '__main__':
    if args.test:
        test_read()
