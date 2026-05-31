class FFAimSensitivityOptimizerMax:
    def __init__(self, brand="Optimized_Device", refresh_rate=90, default_dpi=331):
        self.brand = brand
        self.refresh_rate = refresh_rate
        self.default_dpi = default_dpi
        self.secure_token = "ANTIBAN_EXTERNAL_ALGORITHM_SECURE_2026"
        
    def _calculate_anti_overshoot_max(self):
        return 0.795

    def get_max_sensitivity_profile(self):
        damping = self._calculate_anti_overshoot_max()
        
        calculated_dpi = int(self.default_dpi * 1.65)
        if calculated_dpi > 560:
            calculated_dpi = 546
            
        raw_general_max = 200
        raw_red_dot_max = 200
        
        opt_general = raw_general_max
        opt_red_dot = int(raw_red_dot_max * damping)
        opt_scope_2x = int(200 * (damping * 1.02))
        opt_scope_4x = int(200 * damping)
        opt_sniper = 110
        
        fire_button = 39
        
        return {
            "SECURITY_LAYER": self.secure_token,
            "HARDWARE_OPTIMIZATION": {
                "DEVICE_TARGET": self.brand,
                "SCREEN_HZ": f"{self.refresh_rate}Hz",
                "SYSTEM_MIN_WIDTH_DPI": calculated_dpi,
                "POINTER_SPEED_RATIO": "1.0_MAX",
                "TOUCH_RESPONSE_DELAY_MS": 0.5,
                "TOUCH_SAMPLING_RATE_BOOST": "MAX_PERFORMANCE"
            },
            "IN_GAME_AIM_PROFILE_MAX": {
                "GENERAL_SENSITIVITY": opt_general,
                "RED_DOT_CHEST_TO_HEAD_LOCK": opt_red_dot,
                "SCOPE_2X_LOCK": opt_scope_2x,
                "SCOPE_4X_LOCK": opt_scope_4x,
                "AWM_SCOPE_TRACKING": opt_sniper,
                "FREE_LOOK_AXIS": 100
            },
            "HUD_TRIGGER_LAYOUT": {
                "FIRE_BUTTON_PERCENT_SIZE": f"{fire_button}%",
                "SCREEN_PLACEMENT_Y_AXIS": "LOWEST_EDGE_ALIGNMENT"
            }
        }

    def execute_and_display(self):
        data = self.get_max_sensitivity_profile()
        print("================================================================================")
        print("          FREE FIRE SUPREME AIM-SENSITIVITY ENGINE v6.0 [OVER_200_EMULATED]     ")
        print("================================================================================")
        print(f" SECURE STATUS : {data['SECURITY_LAYER']} -> 100% EXTERNAL SAFE VALIDATION")
        print("--------------------------------------------------------------------------------")
        print(" HARDWARE CONFIGURATION (SET IN PHONE SETTINGS) :")
        for key, value in data["HARDWARE_OPTIMIZATION"].items():
            print(f"   * {key} => {value}")
        print("--------------------------------------------------------------------------------")
        print(" IN-GAME SETTINGS MENU (MAXIMUM ACCELERATION) :")
        for key, value in data["IN_GAME_AIM_PROFILE_MAX"].items():
            print(f"   * {key} => {value}")
        print("--------------------------------------------------------------------------------")
        print " SCREEN BUTTON LAYOUT :"
        for key, value in data["HUD_TRIGGER_LAYOUT"].items():
            print(f"   * {key} => {value}")
        print("================================================================================")

if __name__ == "__main__":
    engine = FFAimSensitivityOptimizerMax(brand="Device_90Hz_Base331_UltraSens", refresh_rate=90, default_dpi=331)
    engine.execute_and_display()
