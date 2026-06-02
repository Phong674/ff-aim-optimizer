#include <Windows.h>
#include <cmath>
#include <random>

#define OFFSET_VIEWANGLES     0x2A3B4C5D
#define OFFSET_ENEMY_LIST     0x5E6F7A8B
#define OFFSET_PLAYER_POS     0x160
#define OFFSET_PLAYER_HEALTH  0x2C4
#define OFFSET_PLAYER_TEAM    0x3F8
#define OFFSET_BONE_MATRIX    0x4D0

std::mt19937 rng(std::chrono::steady_clock::now().time_since_epoch().count());

struct Vector3 {
    float x, y, z;
};

Vector3 CalcAngle(const Vector3& src, const Vector3& dst) {
    Vector3 angles;
    double delta[3] = { src.x - dst.x, src.y - dst.y, src.z - dst.z };
    double hyp = sqrt(delta[0] * delta[0] + delta[1] * delta[1]);
    angles.x = atan2(delta[1], delta[0]) * 180.0 / 3.1415926535897;
    angles.y = atan2(delta[2], hyp) * 180.0 / 3.1415926535897;
    angles.z = 0;
    return angles;
}

float GetRandomFloat(float min, float max) {
    std::uniform_real_distribution<float> dist(min, max);
    return dist(rng);
}

DWORD WINAPI AntiBanRandomizer(LPVOID) {
    while (true) {
        if (GetAsyncKeyState(VK_LBUTTON) & 0x8000) {
            int randSleep = 15 + (rand() % 25);
            Sleep(randSleep);
        }
        Sleep(500 + (rand() % 300));
    }
    return 0;
}

DWORD WINAPI AimlockThread(LPVOID) {
    DWORD gameBase = (DWORD)GetModuleHandle(L"libUE4.so");
    DWORD viewAnglesAddr = gameBase + OFFSET_VIEWANGLES;
    DWORD enemyListAddr = gameBase + OFFSET_ENEMY_LIST;

    while (true) {
        if (GetAsyncKeyState(VK_RBUTTON) & 0x8000) {
            Vector3 localPos = { 0 };
            Vector3 bestTarget = { 0 };
            float bestDistance = 999999.0f;
            int bestHealth = 100;

            for (int i = 0; i < 64; i++) {
                DWORD enemyPtr = *(DWORD*)(enemyListAddr + i * 4);
                if (!enemyPtr) continue;

                int enemyTeam = *(int*)(enemyPtr + OFFSET_PLAYER_TEAM);
                int myTeam = *(int*)(gameBase + 0x12345);
                if (enemyTeam == myTeam) continue;

                int health = *(int*)(enemyPtr + OFFSET_PLAYER_HEALTH);
                if (health <= 0) continue;

                Vector3 enemyPos = *(Vector3*)(enemyPtr + OFFSET_PLAYER_POS);
                float dist = sqrt(enemyPos.x * enemyPos.x + enemyPos.y * enemyPos.y);

                if (dist < bestDistance && dist > 0.5f && dist < 250.0f) {
                    bestDistance = dist;
                    bestTarget = enemyPos;
                    bestHealth = health;
                }
            }

            if (bestDistance < 999998.0f) {
                Vector3 headPos = bestTarget;
                headPos.z += 1.65f; // смещение головы

                Vector3 newAngles = CalcAngle(localPos, headPos);
                
                // плавность 15% и случайный шум
                Vector3 currentAngles = *(Vector3*)viewAnglesAddr;
                float smooth = 0.15f + GetRandomFloat(0.01f, 0.03f);
                newAngles.x = currentAngles.x + (newAngles.x - currentAngles.x) * smooth;
                newAngles.y = currentAngles.y + (newAngles.y - currentAngles.y) * smooth;
                
                newAngles.x += GetRandomFloat(-0.35f, 0.35f);
                newAngles.y += GetRandomFloat(-0.15f, 0.15f);

                *(Vector3*)viewAnglesAddr = newAngles;
            }
        }
        Sleep(1);
    }
    return 0;
}

DWORD WINAPI MemoryCleaner(LPVOID) {
    while (true) {
        HANDLE hProcess = GetCurrentProcess();
        DWORD oldProtect;
        VirtualProtectEx(hProcess, (LPVOID)0x10000000, 0x1000, PAGE_NOACCESS, &oldProtect);
        VirtualProtectEx(hProcess, (LPVOID)0x10000000, 0x1000, oldProtect, &oldProtect);
        Sleep(30000);
    }
    return 0;
}

BOOL APIENTRY DllMain(HMODULE hModule, DWORD ul_reason_for_call, LPVOID lpReserved) {
    if (ul_reason_for_call == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(hModule);
        CreateThread(NULL, 0, AntiBanRandomizer, NULL, 0, NULL);
        CreateThread(NULL, 0, AimlockThread, NULL, 0, NULL);
        CreateThread(NULL, 0, MemoryCleaner, NULL, 0, NULL);
    }
    return TRUE;
}
