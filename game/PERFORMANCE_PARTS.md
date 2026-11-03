# Performance parts — first playable progression pass

The current upgrade scope is strictly **race-earned mechanical parts**. This feature intentionally does **not** swap body panels, add mesh components, modify cockpit visuals, reskin textures, or provide cosmetic rewards.

## Earning and installation

- Completing a **3-Lap Challenge** pays **150 race credits**.
- A new personal three-lap event record adds **25 bonus credits**.
- The race results panel displays earned credits and the total bank.
- Credits are shared across the fleet. Installed upgrade levels are **per craft**.
- In **Foundry**, open **PERFORMANCE PARTS** and choose the part category. The purchase is installed immediately and affects the next race. The game keeps the selected craft visual model unchanged.
- Free Drive and Time Trial do not currently pay credits. Credits are entirely earned through gameplay; no in-app purchase, network account or premium currency is required.

## Available categories

| Part | Level limit | Applies to physics | Cost per next tier |
|---|---:|---|---|
| Thrust Drive | 3 | +0.75 acceleration and +0.6 m/s forward limit per tier | 125 / 300 / 575 |
| Stability Gyros | 3 | +0.5 lateral grip and +0.025 yaw rate per tier | 125 / 300 / 575 |
| Boost Capacitor | 3 | +0.75 m/s boost bonus and +1.5 recharge per tier | 125 / 300 / 575 |

Each tier represents a fitted performance part, not a generated physical mesh. Upgrades are additive to each vehicle's existing handling profile, so distinctive chassis behavior survives.

## Saves and safety

- Local file: `user://performance_parts.cfg` (separate from existing `user://records.cfg`).
- Race records and the vehicle catalog remain backward-compatible.
- New players start with zero credits and all part tiers at level zero.
- Credit balances cannot go below zero; tier levels are clamped to 0–3.
- The test suite uses a separate `performance_parts_ci_test.cfg` file and removes it after testing.
- An individual three-lap event credits the bank once on finishing; repeat races can earn additional credits.
- A failed save produces no success return from a purchase or payout function.

## QA

`game/tests/performance_parts_test.gd` validates purchase costs, insufficient-funds behavior, tier levels, separate per-craft tuning, saved credits, physics values, and the absence of visual-model changes. The Android pipeline runs this before APK export. Phone review should confirm the new Foundry button is reachable, its full-screen panel works with touch input, and the upgraded car feels stronger without altering its visual appearance.

**Not in this pass:** visual modifications, paint, exterior parts, visual damage, chassis swapping, real CPU opponents, or an expanded career economy.
