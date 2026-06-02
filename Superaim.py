import os
import time
import random
import threading
import subprocess
import math
import struct

PKG = "com.dts.freefireth"
LIB = "libUE4.so"

class Memory:
    @staticmethod
    def get_pid():
        try:
            result = subprocess.run(["pidof", PKG], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return int(result.stdout.strip().split()[0])
        except:
            pass
        try:
            for line in os.popen(f"ps -A | grep {PKG}"):
                if PKG in line:
                    return int(line.split()[1])
        except:
            pass
        return 0
    
    @staticmethod
    def read_uint64(pid, addr):
        if pid == 0:
            return 0
        try:
            with open(f"/proc/{pid}/mem", "rb", buffering=0) as mem:
                mem.seek(addr)
                data = mem.read(8)
                if len(data) == 8:
                    return int.from_bytes(data, "little")
        except:
            pass
        return 0

    @staticmethod
    def read_float(pid, addr):
        if pid == 0:
            return 0.0
        try:
            with open(f"/proc/{pid}/mem", "rb", buffering=0) as mem:
                mem.seek(addr)
                data = mem.read(4)
                if len(data) == 4:
                    return struct.unpack("f", data)[0]
        except:
            pass
        return 0.0
    
    @staticmethod
    def write_float(pid, addr, val):
        if pid == 0:
            return False
        try:
            with open(f"/proc/{pid}/mem", "r+b", buffering=0) as mem:
                mem.seek(addr)
                mem.write(val.to_bytes(4, "little"))
            return True
        except:
            return False
    
    @staticmethod
    def write_uint64(pid, addr, val):
        if pid == 0:
            return False
        try:
            with open(f"/proc/{pid}/mem", "r+b", buffering=0) as mem:
                mem.seek(addr)
                mem.write(val.to_bytes(8, "little"))
            return True
        except:
            return False

    @staticmethod
    def read_bytes(pid, addr, size):
        if pid == 0:
            return b''
        try:
            with open(f"/proc/{pid}/mem", "rb", buffering=0) as mem:
                mem.seek(addr)
                return mem.read(size)
        except:
            return b''

    @staticmethod
    def write_bytes(pid, addr, data):
        if pid == 0:
            return False
        try:
            with open(f"/proc/{pid}/mem", "r+b", buffering=0) as mem:
                mem.seek(addr)
                mem.write(data)
            return True
        except:
            return False

class Vector3:
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

class SuperAim:
    def __init__(self):
        self.pid = 0
        self.base = 0
        self.running = True
        self.warmup_phase = True
        self.warmup_start = 0
        
    def warmup(self):
        print("[*] Warmup started - 180 seconds")
        self.warmup_start = time.time()
        for i in range(180, 0, -1):
            if i % 30 == 0:
                print(f"[*] Waiting {i} seconds before activation...")
            time.sleep(1)
        self.warmup_phase = False
        print("[+] Super Aimlock Activated")
        
    def _get_base(self):
        if self.pid == 0:
            return 0
        try:
            with open(f"/proc/{self.pid}/maps", "r") as f:
                for line in f:
                    if LIB in line and "r-xp" in line:
                        return int(line.split("-")[0], 16)
        except:
            pass
        return 0

    def _calc_super_angle(self, local, target):
        delta_x = target.x - local.x
        delta_y = target.y - local.y
        delta_z = (target.z - local.z) + 0.12
        yaw = math.atan2(delta_y, delta_x) * 180.0 / math.pi
        hyp = math.sqrt(delta_x * delta_x + delta_y * delta_y)
        pitch = math.atan2(delta_z, hyp) * 180.0 / math.pi
        if pitch > 89:
            pitch = 89
        if pitch < -89:
            pitch = -89
        return Vector3(pitch, yaw, 0)

    def _get_bone_position_super(self, actor, bone_index):
        bone_array = Memory.read_uint64(self.pid, actor + 0x4D0)
        if bone_array == 0:
            return Vector3(0,0,0)
        x = Memory.read_float(self.pid, bone_array + bone_index * 0x30 + 0x20)
        y = Memory.read_float(self.pid, bone_array + bone_index * 0x30 + 0x24)
        z = Memory.read_float(self.pid, bone_array + bone_index * 0x30 + 0x28)
        return Vector3(x, y, z)

    def _scan_actors_super(self):
        if self.base == 0:
            return
        gworld = Memory.read_uint64(self.pid, self.base + 0x0E45A78)
        if gworld == 0:
            return
        actors = Memory.read_uint64(self.pid, gworld + 0x30)
        if actors == 0:
            return
        count = Memory.read_uint64(self.pid, gworld + 0x38)
        for i in range(min(count, 512)):
            actor = Memory.read_uint64(self.pid, actors + i * 8)
            if actor:
                yield actor

    def _get_local_pawn_super(self):
        gworld = Memory.read_uint64(self.pid, self.base + 0x0E45A78)
        if gworld == 0:
            return 0
        game_instance = Memory.read_uint64(self.pid, gworld + 0x1D0)
        if game_instance == 0:
            return 0
        local_players = Memory.read_uint64(self.pid, game_instance + 0x38)
        if local_players == 0:
            return 0
        player_controller = Memory.read_uint64(self.pid, local_players + 0x30)
        if player_controller == 0:
            return 0
        pawn = Memory.read_uint64(self.pid, player_controller + 0x2A8)
        return pawn

    def _get_local_position_super(self, pawn):
        root_component = Memory.read_uint64(self.pid, pawn + 0x150)
        if root_component == 0:
            return Vector3(0,0,0)
        x = Memory.read_float(self.pid, root_component + 0x160)
        y = Memory.read_float(self.pid, root_component + 0x164)
        z = Memory.read_float(self.pid, root_component + 0x168)
        return Vector3(x, y, z)

    def _set_view_angles_super(self, angles):
        gworld = Memory.read_uint64(self.pid, self.base + 0x0E45A78)
        if gworld == 0:
            return
        game_instance = Memory.read_uint64(self.pid, gworld + 0x1D0)
        if game_instance == 0:
            return
        local_players = Memory.read_uint64(self.pid, game_instance + 0x38)
        if local_players == 0:
            return
        player_controller = Memory.read_uint64(self.pid, local_players + 0x30)
        if player_controller == 0:
            return
        control_rotation = player_controller + 0x2A0
        Memory.write_float(self.pid, control_rotation, angles.x)
        Memory.write_float(self.pid, control_rotation + 4, angles.y)

    def _is_valid_enemy_super(self, actor, local_pawn):
        if actor == local_pawn:
            return False
        health = Memory.read_uint64(self.pid, actor + 0x2C4)
        if health == 0 or health >= 200:
            return False
        if health > 10000:
            return False
        team = Memory.read_uint64(self.pid, actor + 0x3F8)
        local_team = Memory.read_uint64(self.pid, local_pawn + 0x3F8)
        if team == local_team and team != 0:
            return False
        return True

    def _super_no_spread(self):
        weapon_offset = 0x8C0
        gworld = Memory.read_uint64(self.pid, self.base + 0x0E45A78)
        if gworld == 0:
            return
        game_instance = Memory.read_uint64(self.pid, gworld + 0x1D0)
        if game_instance == 0:
            return
        local_players = Memory.read_uint64(self.pid, game_instance + 0x38)
        if local_players == 0:
            return
        player_controller = Memory.read_uint64(self.pid, local_players + 0x30)
        if player_controller == 0:
            return
        pawn = Memory.read_uint64(self.pid, player_controller + 0x2A8)
        if pawn == 0:
            return
        current_weapon = Memory.read_uint64(self.pid, pawn + weapon_offset)
        if current_weapon == 0:
            return
        Memory.write_float(self.pid, current_weapon + 0x2C4, 0.0)
        Memory.write_float(self.pid, current_weapon + 0x2C8, 0.0)
        Memory.write_float(self.pid, current_weapon + 0x2CC, 0.0)

    def _super_recoil(self):
        gworld = Memory.read_uint64(self.pid, self.base + 0x0E45A78)
        if gworld == 0:
            return
        game_instance = Memory.read_uint64(self.pid, gworld + 0x1D0)
        if game_instance == 0:
            return
        local_players = Memory.read_uint64(self.pid, game_instance + 0x38)
        if local_players == 0:
            return
        player_controller = Memory.read_uint64(self.pid, local_players + 0x30)
        if player_controller == 0:
            return
        pawn = Memory.read_uint64(self.pid, player_controller + 0x2A8)
        if pawn == 0:
            return
        current_weapon = Memory.read_uint64(self.pid, pawn + 0x8C0)
        if current_weapon == 0:
            return
        Memory.write_float(self.pid, current_weapon + 0x358, 0.0)
        Memory.write_float(self.pid, current_weapon + 0x35C, 0.0)

    def _super_silent_aim(self, angles):
        gworld = Memory.read_uint64(self.pid, self.base + 0x0E45A78)
        if gworld == 0:
            return
        game_instance = Memory.read_uint64(self.pid, gworld + 0x1D0)
        if game_instance == 0:
            return
        local_players = Memory.read_uint64(self.pid, game_instance + 0x38)
        if local_players == 0:
            return
        player_controller = Memory.read_uint64(self.pid, local_players + 0x30)
        if player_controller == 0:
            return
        control_rotation = player_controller + 0x2A0
        Memory.write_float(self.pid, control_rotation + 0x10, angles.x)
        Memory.write_float(self.pid, control_rotation + 0x14, angles.y)

    def _antiban_super(self):
        try:
            paths = [
                "/data/local/tmp/.xigncode",
                "/data/local/tmp/gg",
                "/data/local/tmp/lspatch",
                "/data/data/com.dts.freefireth/cache",
                "/data/data/com.dts.freefireth/code_cache",
                "/data/data/com.dts.freefireth/no_backup",
                "/storage/emulated/0/Android/data/com.dts.freefireth/cache",
                "/storage/emulated/0/Android/data/com.dts.freefireth/files/.temp",
                "/sdcard/xigncode",
                "/sdcard/cheat"
            ]
            for p in paths:
                subprocess.run(["rm", "-rf", p], stderr=subprocess.DEVNULL, shell=False)
            subprocess.run(["settings", "put", "global", "hidden_api_policy", "1"], stderr=subprocess.DEVNULL)
            subprocess.run(["settings", "put", "global", "development_settings_enabled", "0"], stderr=subprocess.DEVNULL)
            subprocess.run(["cmd", "appops", "set", PKG, "android:read_logs", "ignore"], stderr=subprocess.DEVNULL)
        except:
            pass

    def _memory_guard(self):
        try:
            suspicious_regions = [0x7000000000, 0x6000000000, 0x5000000000]
            for addr in suspicious_regions:
                Memory.write_bytes(self.pid, addr, b'\x00' * 4096)
        except:
            pass

    def run(self):
        warmup_thread = threading.Thread(target=self.warmup, daemon=True)
        warmup_thread.start()
        
        last_clean = 0
        last_guard = 0
        
        while self.running:
            try:
                if self.warmup_phase:
                    time.sleep(0.5)
                    continue
                    
                if self.pid == 0 or self.base == 0:
                    self.pid = Memory.get_pid()
                    self.base = self._get_base()
                    if self.pid == 0:
                        time.sleep(2)
                    continue

                local_pawn = self._get_local_pawn_super()
                if local_pawn == 0:
                    time.sleep(0.03)
                    continue

                local_pos = self._get_local_position_super(local_pawn)
                best_actor = 0
                best_distance = 999999.0
                best_head = Vector3(0,0,0)
                target_count = 0

                for actor in self._scan_actors_super():
                    if self._is_valid_enemy_super(actor, local_pawn):
                        head_pos = self._get_bone_position_super(actor, 8)
                        if head_pos.x == 0 and head_pos.y == 0:
                            head_pos = self._get_bone_position_super(actor, 6)
                        if head_pos.x == 0 and head_pos.y == 0:
                            continue
                        dx = head_pos.x - local_pos.x
                        dy = head_pos.y - local_pos.y
                        dist = math.sqrt(dx*dx + dy*dy)
                        if dist < best_distance and dist < 300.0 and dist > 0.5:
                            best_distance = dist
                            best_actor = actor
                            best_head = head_pos
                            target_count += 1

                if best_actor != 0 and target_count > 0:
                    angles = self._calc_super_angle(local_pos, best_head)
                    random_scale = random.uniform(0.96, 1.04)
                    angles.y *= random_scale
                    angles.x *= random_scale
                    angles.x += random.uniform(-0.05, 0.05)
                    angles.y += random.uniform(-0.1, 0.1)
                    self._set_view_angles_super(angles)
                    self._super_no_spread()
                    self._super_recoil()
                    self._super_silent_aim(angles)
                    time.sleep(0.005)

                now = time.time()
                if now - last_clean > 22:
                    self._antiban_super()
                    last_clean = now
                    
                if now - last_guard > 60:
                    self._memory_guard()
                    last_guard = now

                time.sleep(0.008)
            except:
                time.sleep(0.05)

if __name__ == "__main__":
    print("[*] Super Aimlock v5.0 - Waiting for Free Fire...")
    while Memory.get_pid() == 0:
        time.sleep(2)
    print("[+] Free Fire detected. Loading super modules...")
    time.sleep(1)
    aim = SuperAim()
    aim.run()
