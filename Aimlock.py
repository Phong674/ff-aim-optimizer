import os
import time
import random
import threading
import ctypes
import socket
import struct

PKG = "com.dts.freefireth"
LIB = "libUE4.so"

class Memory:
    @staticmethod
    def get_pid():
        return int(os.popen(f"pidof {PKG}").read().strip())
    
    @staticmethod
    def read_uint64(pid, addr):
        with open(f"/proc/{pid}/mem", "rb", buffering=0) as mem:
            mem.seek(addr)
            return struct.unpack("Q", mem.read(8))[0]
    
    @staticmethod
    def write_float(pid, addr, val):
        with open(f"/proc/{pid}/mem", "r+b", buffering=0) as mem:
            mem.seek(addr)
            mem.write(struct.pack("f", val))

class Aim:
    def __init__(self):
        self.pid = Memory.get_pid()
        self.base = self._get_base()
        
    def _get_base(self):
        with open(f"/proc/{self.pid}/maps", "r") as f:
            for line in f:
                if LIB in line:
                    return int(line.split("-")[0], 16)
        return 0
        
    def _scan_actors(self):
        gworld = Memory.read_uint64(self.pid, self.base + 0xF8D498)
        actors = Memory.read_uint64(self.pid, gworld + 0x30)
        count = Memory.read_uint64(self.pid, gworld + 0x38)
        for i in range(min(count, 256)):
            actor = Memory.read_uint64(self.pid, actors + i * 8)
            if actor:
                yield actor
                
    def _is_valid_enemy(self, actor):
        health = Memory.read_uint64(self.pid, actor + 0x2C4)
        team = Memory.read_uint64(self.pid, actor + 0x3F8)
        myteam = Memory.read_uint64(self.pid, self.base + 0x12345)
        return 0 < health < 200 and team != myteam
        
    def aim_at(self, actor):
        pos_x = Memory.read_uint64(self.pid, actor + 0x160)
        pos_y = Memory.read_uint64(self.pid, actor + 0x164)
        pos_z = Memory.read_uint64(self.pid, actor + 0x168)
        head_z = pos_z + 1.65
        view = self.base + 0x2A3B4C
        yaw = random.uniform(-0.8, 0.8)
        pitch = random.uniform(-0.4, 0.4)
        Memory.write_float(self.pid, view, yaw)
        Memory.write_float(self.pid, view + 4, pitch)
        
    def run(self):
        while True:
            for actor in self._scan_actors():
                if self._is_valid_enemy(actor):
                    self.aim_at(actor)
                    break
            time.sleep(0.01)

class AntiBan:
    @staticmethod
    def clean():
        paths = [
            "/data/local/tmp/.xigncode",
            "/data/data/com.dts.freefireth/cache",
            "/storage/emulated/0/Android/data/com.dts.freefireth/cache"
        ]
        for p in paths:
            os.system(f"rm -rf {p}/* 2>/dev/null")
            
    @staticmethod
    def hide_traces():
        os.system("settings put global hidden_api_policy 1")
        os.system("resetprop ro.debuggable 0")
        os.system("resetprop ro.secure 1")
        
    @staticmethod
    def monitor():
        while True:
            AntiBan.clean()
            time.sleep(25)

if __name__ == "__main__":
    t1 = threading.Thread(target=AntiBan.monitor, daemon=True)
    t1.start()
    aim = Aim()
    aim.run()
