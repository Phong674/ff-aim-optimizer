import os
import time
import random
import threading
import subprocess
import math
import struct
import json
import hashlib
import base64
import socket
import re
import sys
from ctypes import *
from collections import deque

PKG = "com.dts.freefireth"
LIB = "libUE4.so"
VERSION = "9.9.9_ULTIMATE"
BUILD_DATE = "2026_06_02"

class Crypto:
    @staticmethod
    def xor_cipher(data, key):
        return bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])
    
    @staticmethod
    def obfuscate_string(s):
        return base64.b64encode(s.encode()).decode()
    
    @staticmethod
    def deobfuscate_string(s):
        return base64.b64decode(s.encode()).decode()

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
    def read_uint32(pid, addr):
        if pid == 0:
            return 0
        try:
            with open(f"/proc/{pid}/mem", "rb", buffering=0) as mem:
                mem.seek(addr)
                data = mem.read(4)
                if len(data) == 4:
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
    def pattern_scan(pid, pattern, mask, start, end):
        if pid == 0:
            return 0
        try:
            mem = open(f"/proc/{pid}/mem", "rb", buffering=0)
            mem.seek(start)
            size = end - start
            data = mem.read(size)
            pattern_bytes = bytes([int(p, 16) for p in pattern.split()])
            for i in range(len(data) - len(pattern_bytes)):
                found = True
                for j in range(len(pattern_bytes)):
                    if mask[j] == 'x' and data[i+j] != pattern_bytes[j]:
                        found = False
                        break
                if found:
                    mem.close()
                    return start + i
            mem.close()
        except:
            pass
        return 0

class Vector2:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

class Vector3:
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

class PlayerData:
    def __init__(self):
        self.actor = 0
        self.position = Vector3()
        self.head_position = Vector3()
        self.health = 0
        self.max_health = 0
        self.team = 0
        self.distance = 999999.0
        self.name = ""
        self.is_bot = False
        self.is_knocked = False
        self.weapon_id = 0
        self.vehicle_id = 0

class SuperAim:
    def __init__(self):
        self.pid = 0
        self.base = 0
        self.running = True
        self.warmup_phase = True
        self.warmup_start = 0
        self.kill_count = 0
        self.headshot_count = 0
        self.bullet_fired = 0
        self.bullet_hit = 0
        self.fov = 30.0
        self.smoothness = 0.12
        self.aim_hotkey = "RBUTTON"
        self.aim_mode = "HEAD"  # HEAD, CHEST, LEG
        self.visible_check = True
        self.prediction = True
        self.silent_aim = True
        self.trigger_bot = False
        self.trigger_delay = 0
        self.rcs_enabled = True
        self.rcs_intensity = 0.85
        
        self.bone_indices = {
            "HEAD": 8,
            "NECK": 7,
            "CHEST": 6,
            "PELVIS": 1,
            "LEFT_SHOULDER": 13,
            "RIGHT_SHOULDER": 14,
            "LEFT_KNEE": 24,
            "RIGHT_KNEE": 25
        }
        
        self.offsets = {
            "GWorld": 0x0E45A78,
            "GNames": 0x0F8D4A0,
            "GObjects": 0x0F8D498,
            "PersistentLevel": 0x30,
            "Actors": 0x98,
            "ActorCount": 0xA0,
            "PlayerController": 0x30,
            "LocalPlayers": 0x38,
            "PlayerCameraManager": 0x2F8,
            "ControlRotation": 0x2A0,
            "RootComponent": 0x150,
            "RelativeLocation": 0x160,
            "Mesh": 0x2A8,
            "BoneArray": 0x4D0,
            "Health": 0x2C4,
            "MaxHealth": 0x2C8,
            "Team": 0x3F8,
            "PlayerName": 0x408,
            "CurrentWeapon": 0x8C0,
            "WeaponSpread": 0x2C4,
            "WeaponRecoil": 0x358,
            "Pawn": 0x2A8,
            "AcknowledgedPawn": 0x2A0,
            "PlayerState": 0x240,
            "bIsDBNO": 0x4B0,
            "bIsDead": 0x4B4,
            "VehicleCommon": 0x8F0
        }

    def warmup(self):
        print(f"[*] ========================================")
        print(f"[*] SUPER AIMLOCK ULTIMATE v{VERSION}")
        print(f"[*] BUILD: {BUILD_DATE}")
        print(f"[*] ========================================")
        print(f"[*] Warmup started - 180 seconds")
        print(f"[*] AntiBan protection loaded")
        print(f"[*] Memory guard active")
        print(f"[*] ========================================")
        self.warmup_start = time.time()
        for i in range(180, 0, -1):
            if i % 10 == 0:
                print(f"[*] Initializing in {i} seconds...")
            if i % 30 == 0:
                self._security_check()
            time.sleep(1)
        self.warmup_phase = False
        print(f"[+] ========================================")
        print(f"[+] SUPER AIMLOCK ACTIVATED")
        print(f"[+] Headshot mode: {self.aim_mode}")
        print(f"[+] FOV: {self.fov}")
        print(f"[+] Smoothness: {self.smoothness}")
        print(f"[+] Silent Aim: {self.silent_aim}")
        print(f"[+] RCS: {self.rcs_enabled}")
        print(f"[+] ========================================")

    def _security_check(self):
        try:
            subprocess.run(["settings", "put", "global", "hidden_api_policy", "1"], stderr=subprocess.DEVNULL)
            subprocess.run(["settings", "put", "global", "development_settings_enabled", "0"], stderr=subprocess.DEVNULL)
        except:
            pass

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

    def _calc_angle(self, src, dst):
        delta_x = dst.x - src.x
        delta_y = dst.y - src.y
        delta_z = dst.z - src.z
        yaw = math.atan2(delta_y, delta_x) * 180.0 / math.pi
        hyp = math.sqrt(delta_x * delta_x + delta_y * delta_y)
        pitch = math.atan2(delta_z, hyp) * 180.0 / math.pi
        if pitch > 89:
            pitch = 89
        if pitch < -89:
            pitch = -89
        return Vector2(pitch, yaw)

    def _normalize_angle(self, angle):
        while angle.x > 89:
            angle.x -= 180
        while angle.x < -89:
            angle.x += 180
        while angle.y > 180:
            angle.y -= 360
        while angle.y < -180:
            angle.y += 360
        return angle

    def _get_bone_position(self, actor, bone_name):
        bone_index = self.bone_indices.get(bone_name, 8)
        bone_array = Memory.read_uint64(self.pid, actor + self.offsets["Mesh"] + self.offsets["BoneArray"])
        if bone_array == 0:
            return Vector3(0,0,0)
        x = Memory.read_float(self.pid, bone_array + bone_index * 0x30 + 0x20)
        y = Memory.read_float(self.pid, bone_array + bone_index * 0x30 + 0x24)
        z = Memory.read_float(self.pid, bone_array + bone_index * 0x30 + 0x28)
        return Vector3(x, y, z)

    def _world_to_screen(self, world_pos, screen_size):
        camera = self._get_camera()
        if camera == 0:
            return Vector2(0,0)
        rotation = self._get_camera_rotation()
        if rotation.x == 0 and rotation.y == 0:
            return Vector2(0,0)
        delta = Vector3(
            world_pos.x - camera.x,
            world_pos.y - camera.y,
            world_pos.z - camera.z
        )
        cos_y = math.cos(rotation.y * math.pi / 180.0)
        sin_y = math.sin(rotation.y * math.pi / 180.0)
        cos_p = math.cos(rotation.x * math.pi / 180.0)
        sin_p = math.sin(rotation.x * math.pi / 180.0)
        x = delta.x * cos_y - delta.y * sin_y
        y = delta.x * sin_y + delta.y * cos_y
        z = delta.z
        screen_x = (x / z) * 1000 + screen_size.x / 2
        screen_y = (y / z) * 1000 + screen_size.y / 2
        return Vector2(screen_x, screen_y)

    def _get_camera(self):
        gworld = Memory.read_uint64(self.pid, self.base + self.offsets["GWorld"])
        if gworld == 0:
            return 0
        game_instance = Memory.read_uint64(self.pid, gworld + 0x1D0)
        if game_instance == 0:
            return 0
        local_players = Memory.read_uint64(self.pid, game_instance + self.offsets["LocalPlayers"])
        if local_players == 0:
            return 0
        player_controller = Memory.read_uint64(self.pid, local_players + 0x30)
        if player_controller == 0:
            return 0
        camera_manager = Memory.read_uint64(self.pid, player_controller + self.offsets["PlayerCameraManager"])
        if camera_manager == 0:
            return 0
        camera_pos = Memory.read_uint64(self.pid, camera_manager + 0x240)
        return camera_pos

    def _get_camera_rotation(self):
        gworld = Memory.read_uint64(self.pid, self.base + self.offsets["GWorld"])
        if gworld == 0:
            return Vector2(0,0)
        game_instance = Memory.read_uint64(self.pid, gworld + 0x1D0)
        if game_instance == 0:
            return Vector2(0,0)
        local_players = Memory.read_uint64(self.pid, game_instance + self.offsets["LocalPlayers"])
        if local_players == 0:
            return Vector2(0,0)
        player_controller = Memory.read_uint64(self.pid, local_players + 0x30)
        if player_controller == 0:
            return Vector2(0,0)
        pitch = Memory.read_float(self.pid, player_controller + self.offsets["ControlRotation"])
        yaw = Memory.read_float(self.pid, player_controller + self.offsets["ControlRotation"] + 4)
        return Vector2(pitch, yaw)

    def _scan_players(self):
        if self.base == 0:
            return []
        gworld = Memory.read_uint64(self.pid, self.base + self.offsets["GWorld"])
        if gworld == 0:
            return []
        actors = Memory.read_uint64(self.pid, gworld + self.offsets["Actors"])
        if actors == 0:
            return []
        count = Memory.read_uint64(self.pid, gworld + self.offsets["ActorCount"])
        players = []
        for i in range(min(count, 512)):
            actor = Memory.read_uint64(self.pid, actors + i * 8)
            if actor and actor != self.local_pawn:
                health = Memory.read_uint32(self.pid, actor + self.offsets["Health"])
                if 0 < health < 200:
                    player = PlayerData()
                    player.actor = actor
                    player.health = health
                    player.max_health = Memory.read_uint32(self.pid, actor + self.offsets["MaxHealth"])
                    player.team = Memory.read_uint32(self.pid, actor + self.offsets["Team"])
                    player.is_knocked = Memory.read_uint32(self.pid, actor + self.offsets["bIsDBNO"]) == 1
                    root = Memory.read_uint64(self.pid, actor + self.offsets["RootComponent"])
                    if root:
                        player.position.x = Memory.read_float(self.pid, root + self.offsets["RelativeLocation"])
                        player.position.y = Memory.read_float(self.pid, root + self.offsets["RelativeLocation"] + 4)
                        player.position.z = Memory.read_float(self.pid, root + self.offsets["RelativeLocation"] + 8)
                    head = self._get_bone_position(actor, self.aim_mode)
                    if head.x != 0:
                        player.head_position = head
                    else:
                        player.head_position = player.position
                        player.head_position.z += 1.65
                    dx = player.head_position.x - self.local_pos.x
                    dy = player.head_position.y - self.local_pos.y
                    player.distance = math.sqrt(dx*dx + dy*dy)
                    players.append(player)
        return players

    def _get_local_data(self):
        gworld = Memory.read_uint64(self.pid, self.base + self.offsets["GWorld"])
        if gworld == 0:
            return (0, Vector3(0,0,0))
        game_instance = Memory.read_uint64(self.pid, gworld + 0x1D0)
        if game_instance == 0:
            return (0, Vector3(0,0,0))
        local_players = Memory.read_uint64(self.pid, game_instance + self.offsets["LocalPlayers"])
        if local_players == 0:
            return (0, Vector3(0,0,0))
        player_controller = Memory.read_uint64(self.pid, local_players + 0x30)
        if player_controller == 0:
            return (0, Vector3(0,0,0))
        pawn = Memory.read_uint64(self.pid, player_controller + self.offsets["Pawn"])
        if pawn == 0:
            return (0, Vector3(0,0,0))
        root = Memory.read_uint64(self.pid, pawn + self.offsets["RootComponent"])
        if root == 0:
            return (pawn, Vector3(0,0,0))
        x = Memory.read_float(self.pid, root + self.offsets["RelativeLocation"])
        y = Memory.read_float(self.pid, root + self.offsets["RelativeLocation"] + 4)
        z = Memory.read_float(self.pid, root + self.offsets["RelativeLocation"] + 8)
        return (pawn, Vector3(x, y, z))

    def _set_view_angles(self, angles):
        gworld = Memory.read_uint64(self.pid, self.base + self.offsets["GWorld"])
        if gworld == 0:
            return
        game_instance = Memory.read_uint64(self.pid, gworld + 0x1D0)
        if game_instance == 0:
            return
        local_players = Memory.read_uint64(self.pid, game_instance + self.offsets["LocalPlayers"])
        if local_players == 0:
            return
        player_controller = Memory.read_uint64(self.pid, local_players + 0x30)
        if player_controller == 0:
            return
        Memory.write_float(self.pid, player_controller + self.offsets["ControlRotation"], angles.x)
        Memory.write_float(self.pid, player_controller + self.offsets["ControlRotation"] + 4, angles.y)

    def _super_no_spread(self):
        gworld = Memory.read_uint64(self.pid, self.base + self.offsets["GWorld"])
        if gworld == 0:
            return
        game_instance = Memory.read_uint64(self.pid, gworld + 0x1D0)
        if game_instance == 0:
            return
        local_players = Memory.read_uint64(self.pid, game_instance + self.offsets["LocalPlayers"])
        if local_players == 0:
            return
        player_controller = Memory.read_uint64(self.pid, local_players + 0x30)
        if player_controller == 0:
            return
        pawn = Memory.read_uint64(self.pid, player_controller + self.offsets["Pawn"])
        if pawn == 0:
            return
        current_weapon = Memory.read_uint64(self.pid, pawn + self.offsets["CurrentWeapon"])
        if current_weapon == 0:
            return
        Memory.write_float(self.pid, current_weapon + self.offsets["WeaponSpread"], 0.0)
        Memory.write_float(self.pid, current_weapon + self.offsets["WeaponSpread"] + 4, 0.0)
        Memory.write_float(self.pid, current_weapon + self.offsets["WeaponSpread"] + 8, 0.0)

    def _super_rcs(self, current_angle, shot_count):
        if not self.rcs_enabled:
            return current_angle
        recoil_x = shot_count * 0.015 * self.rcs_intensity
        recoil_y = shot_count * 0.008 * self.rcs_intensity
        current_angle.x -= recoil_x
        current_angle.y -= recoil_y
        return current_angle

    def _trigger_bot_check(self, target):
        if not self.trigger_bot:
            return False
        time.sleep(self.trigger_delay / 1000.0)
        return True

    def _prediction_calc(self, target_pos, target_vel, bullet_speed=800.0):
        if not self.prediction:
            return target_pos
        distance = target_pos.distance(self.local_pos)
        travel_time = distance / bullet_speed
        predicted = Vector3(
            target_pos.x + target_vel.x * travel_time,
            target_pos.y + target_vel.y * travel_time,
            target_pos.z + target_vel.z * travel_time
        )
        return predicted

    def _visibility_check(self, actor):
        if not self.visible_check:
            return True
        actor_pos = Memory.read_uint64(self.pid, actor + 0x150)
        if actor_pos == 0:
            return True
        actor_z = Memory.read_float(self.pid, actor_pos + 0x168)
        local_z = self.local_pos.z
        if abs(actor_z - local_z) > 500:
            return False
        return True

    def _ultra_antiban(self):
        try:
            suspicious_paths = [
                "/data/local/tmp/.xigncode",
                "/data/local/tmp/gg",
                "/data/local/tmp/lspatch",
                "/data/local/tmp/cheat",
                "/data/local/tmp/hack",
                "/data/local/tmp/mod",
                "/data/local/tmp/temp",
                "/data/data/com.dts.freefireth/cache",
                "/data/data/com.dts.freefireth/code_cache",
                "/data/data/com.dts.freefireth/no_backup",
                "/storage/emulated/0/Android/data/com.dts.freefireth/cache",
                "/storage/emulated/0/Android/data/com.dts.freefireth/files/.temp",
                "/sdcard/xigncode",
                "/sdcard/cheat",
                "/sdcard/hack",
                "/sdcard/mod",
                "/sdcard/gg"
            ]
            for p in suspicious_paths:
                subprocess.run(["rm", "-rf", p], stderr=subprocess.DEVNULL, shell=False)
            subprocess.run(["settings", "put", "global", "hidden_api_policy", "1"], stderr=subprocess.DEVNULL)
            subprocess.run(["settings", "put", "global", "development_settings_enabled", "0"], stderr=subprocess.DEVNULL)
            subprocess.run(["cmd", "appops", "set", PKG, "android:read_logs", "ignore"], stderr=subprocess.DEVNULL)
            subprocess.run(["cmd", "appops", "set", PKG, "android:get_usage_stats", "ignore"], stderr=subprocess.DEVNULL)
        except:
            pass

    def _memory_guard(self):
        try:
            guard_regions = [
                (0x7000000000, 4096),
                (0x6000000000, 4096),
                (0x5000000000, 4096)
            ]
            for addr, size in guard_regions:
                Memory.write_bytes(self.pid, addr, b'\x00' * size)
        except:
            pass

    def _stats_update(self):
        pass

    def run(self):
        warmup_thread = threading.Thread(target=self.warmup, daemon=True)
        warmup_thread.start()
        
        last_clean = 0
        last_guard = 0
        last_stats = 0
        shot_counter = 0
        
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
                
                self.local_pawn, self.local_pos = self._get_local_data()
                if self.local_pawn == 0:
                    time.sleep(0.03)
                    continue
                
                players = self._scan_players()
                best_target = None
                best_fov_score = 999999.0
                
                current_angles = self._get_camera_rotation()
                
                for player in players:
                    if player.team == self.local_team:
                        continue
                    if player.is_knocked:
                        continue
                    if not self._visibility_check(player.actor):
                        continue
                    
                    aim_pos = player.head_position if self.aim_mode == "HEAD" else player.position
                    target_angle = self._calc_angle(self.local_pos, aim_pos)
                    delta_yaw = abs(target_angle.y - current_angles.y)
                    delta_pitch = abs(target_angle.x - current_angles.x)
                    fov_score = math.sqrt(delta_yaw*delta_yaw + delta_pitch*delta_pitch)
                    
                    if fov_score < best_fov_score and fov_score < self.fov:
                        best_fov_score = fov_score
                        best_target = player
                
                if best_target:
                    aim_pos = best_target.head_position if self.aim_mode == "HEAD" else best_target.position
                    target_angle = self._calc_angle(self.local_pos, aim_pos)
                    target_angle = self._normalize_angle(target_angle)
                    target_angle = self._super_rcs(target_angle, shot_counter)
                    
                    smooth_factor = self.smoothness + random.uniform(-0.02, 0.02)
                    new_pitch = current_angles.x + (target_angle.x - current_angles.x) * smooth_factor
                    new_yaw = current_angles.y + (target_angle.y - current_angles.y) * smooth_factor
                    
                    random_noise = 0.03
                    new_pitch += random.uniform(-random_noise, random_noise)
                    new_yaw += random.uniform(-random_noise, random_noise)
                    
                    self._set_view_angles(Vector2(new_pitch, new_yaw))
                    self._super_no_spread()
                    
                    if self.silent_aim:
                        Memory.write_float(self.pid, self.base + 0x0D2B3F0 + 0x10, new_pitch)
                        Memory.write_float(self.pid, self.base + 0x0D2B3F0 + 0x14, new_yaw)
                    
                    if self.trigger_bot and best_fov_score < 5:
                        shot_counter += 1
                    else:
                        shot_counter = max(0, shot_counter - 1)
                
                now = time.time()
                if now - last_clean > 20:
                    self._ultra_antiban()
                    last_clean = now
                    
                if now - last_guard > 45:
                    self._memory_guard()
                    last_guard = now
                    
                if now - last_stats > 300:
                    self._stats_update()
                    last_stats = now
                
                time.sleep(0.008)
            except Exception as e:
                time.sleep(0.05)

if __name__ == "__main__":
    print("[*] ========================================")
    print("[*] SUPER AIMLOCK ULTIMATE v9.9.9")
    print("[*] Loading ultimate modules...")
    print("[*] ========================================")
    
    while Memory.get_pid() == 0:
        print("[*] Waiting for Free Fire...")
        time.sleep(3)
    
    print("[+] Free Fire detected!")
    time.sleep(1)
    
    aim = SuperAim()
    aim.run()
