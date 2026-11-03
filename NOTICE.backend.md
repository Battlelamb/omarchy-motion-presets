# Backend source and asset notice

SPDX-License-Identifier: GPL-3.0-only

Pinned donor: HyDE-Project/HyDE, commit `fa2fd57afc7203b1b5653d3271f3a57ea3873f97`.
Repository licence: GNU GPL v3; the full licence is included in `LICENSE`.

Selector/list/current/explicit-set behavior follows the inspected GPL HyDE animations selector. The reduced-motion behavior is ported to the supported reversible `animations.enabled` scalar. Wraparound rows and the transactional Python adapter are original project code. No donor Lua is evaluated or shipped as executable presets; no curve tables or HyDE duration-scale globals are copied.

## Exact inspected sources

- `https://raw.githubusercontent.com/HyDE-Project/HyDE/fa2fd57afc7203b1b5653d3271f3a57ea3873f97/Configs/.local/lib/hyde/animations.lua` — SHA-256 `9a4b7decfd01e7366280e6aacb0e0c0aef44e74a865150c57ce2564f3de8d5bc`.
- `https://raw.githubusercontent.com/HyDE-Project/HyDE/fa2fd57afc7203b1b5653d3271f3a57ea3873f97/Configs/.local/lib/hyde/rofi.animations.lua` — SHA-256 `de9f8a056c0847b2529f5bb09fd1471fd57dc6be652b63111dbbd7ce51f3f4af`.
- `https://raw.githubusercontent.com/HyDE-Project/HyDE/fa2fd57afc7203b1b5653d3271f3a57ea3873f97/Configs/.local/share/hypr/lua/animations/00-disable.lua` — SHA-256 `d59d64a8092cfc82eb49ad14723c03e4cc4d0ef1eac608b90858923425fc0313`.
- `https://raw.githubusercontent.com/HyDE-Project/HyDE/fa2fd57afc7203b1b5653d3271f3a57ea3873f97/Configs/.local/share/hypr/lua/animations/fast.lua` — SHA-256 `081a86b65a7c58c525f9cf2cfc322fc41ec1e7721d632fe475e85aef84ce3a0e`.
- `https://raw.githubusercontent.com/HyDE-Project/HyDE/fa2fd57afc7203b1b5653d3271f3a57ea3873f97/LICENSE` — SHA-256 `3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986`.
- `/usr/share/omarchy/bin/omarchy-hyprland-toggle` — SHA-256 `32a6ea6bef5529f26f0c0ab836380e1f1ba48b6fb2cbcbea5d0a1a46d37f4f7a`.
- `/usr/share/omarchy/default/hypr/looknfeel.lua` — SHA-256 `4eed2dc9f3ec4d6697c4347cb76fc47e052c1220e97fa03a5385ef9e8831ddb1`.
- `/usr/share/omarchy/default/hypr/toggles/no-animations.lua` — SHA-256 `2ff210d9d1eaf5ed5009e618968ca6490894d423dbbb8acf231ea4683a437486`.
- `/usr/share/hypr/stubs/hl.meta.lua` — SHA-256 `0c3f4c7ef6dab084437ef3b6956b5e268c1ae80271e9b375aa77254047ff851a`.
- `/usr/include/hyprland/src/version.h` — SHA-256 `dbedffa593494a4f610d8a8eaac5a32c2daed3e2e0998f47d875587370397c58`.
- `https://raw.githubusercontent.com/hyprwm/Hyprland/efb50993780079460b0cbed1363e2166a2de1d9f/src/debug/HyprCtl.cpp` — SHA-256 `798b7c6c4c1684557842463d46ac99c96629be4179e0e461dca77670247b91fa`.
- `https://raw.githubusercontent.com/hyprwm/Hyprland/efb50993780079460b0cbed1363e2166a2de1d9f/src/config/lua/ConfigManager.cpp` — SHA-256 `94b5c6891326e7a3e490019d26fd9d6f5b3137fb5318a94dff0a6cb6dfdaf502`.
- `https://raw.githubusercontent.com/hyprwm/Hyprland/efb50993780079460b0cbed1363e2166a2de1d9f/src/config/lua/bindings/LuaBindingsConfigRules.cpp` — SHA-256 `157c3e45b364f3e41b6fd7cf13fd19e7477e8c03a6a75c6c46fde5e2b5715be9`.
- `https://raw.githubusercontent.com/hyprwm/Hyprland/efb50993780079460b0cbed1363e2166a2de1d9f/src/config/lua/types/LuaConfigCssGap.cpp` — SHA-256 `ac91c9593a04ff96274cb6fcb46c62e996845cc03086dd0e831b5aa1d0515423`.
- `https://raw.githubusercontent.com/hyprwm/Hyprland/efb50993780079460b0cbed1363e2166a2de1d9f/src/config/lua/types/LuaConfigString.cpp` — SHA-256 `7f4cb8035764a7a65833bdc4f0ab0d54c4014ee336f5a7075f37ad1301ac1420`.

Installed Omarchy and Hyprland files are **read-only API references**, not vendored
code in the runtime. Hyprland source above is pinned to the exact installed
version-header commit. No installer, init, arbitrary selector Lua, theme rewrite,
Rofi process killing, cloud endpoint, font, wallpaper or ambiguous dataset is
shipped. The Python backend/tests and warm/compact/wraparound additions are
project-authored GPL-3.0-only code. No claim that the original warm filter came
from HyDE is made. The pinned source hashes above identify the inspected references; those snapshots
are not runtime dependencies.

## v0.3.0 additions and API qualification

Named scalar captures/import/export, preferences integration, Off, comparison and
independent timed Preview/Keep are project-authored GPL-3.0-only changes. The
watchdog reuses this project's already hardened Shader Deck transaction/readiness
protocol locally; there is no cross-plugin runtime dependency. No new donor
curve tables, animation speed values, artwork or fonts are shipped.

Additional inspected installed header:
`/usr/include/hyprland/src/config/shared/animation/AnimationTree.hpp`, SHA-256
`7bd902ec92b800a4c2623ddeb87d4a67f55e2c7c6ea920280904838cde689a3f`.
The pinned `LuaBindingsConfigRules.cpp` lines 390–475 expose an animation setter,
while `HyprCtl.cpp` lines 927–959 serialize animation speed to two decimal places.
There is no matching public Lua inverse for exact precision/inheritance restoration.
Accordingly, the requested four curve modes and speed control remain incomplete;
no false exact-restore or six-mode completion claim is made.
