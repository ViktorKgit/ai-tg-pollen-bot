# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Telegram bot for pollen level tracking (birch, alder) in Vitebsk, Belarus. Data sourced from Open-Meteo Air Quality API.

## Commands

**Run in scheduled mode (default, for GitHub Actions):**
```bash
python bot.py
```
Checks for pending `/check` commands, sends notification to `TELEGRAM_CHAT_ID`, exits.

**Run in polling mode (for interactive `/check` command):**
```bash
python bot.py poll
```
Long-running process that responds to `/start` and `/check` commands.

**Install dependencies:**
```bash
pip install requests
```

## Architecture

**Two execution modes:**
1. **Schedule mode** (default) — single run, sends notification, exits. Used by GitHub Actions cron job.
2. **Poll mode** (`poll` argument) — infinite loop with long-polling, handles interactive commands.

**Environment loading:** The bot reads `.env` directly (line 7-14) instead of using `python-dotenv`. This was done to avoid encoding issues on Windows. Do not switch to dotenv library without testing.

**Location:** Vitebsk coordinates are hardcoded (`LAT = 55.19`, `LON = 30.20`). To change location, modify these values.

**Pollen types available in API:** `birch_pollen`, `alder_pollen`. Hazelnut (`hazel_pollen`, `filbert_pollen`, `cobnut_pollen`) is not supported by Open-Meteo.

**Threshold logic:**
- `> 100` — DANGER (red emoji)
- `> 10` — Moderate (yellow emoji)
- `≤ 10` — Low (green emoji)

## GitHub Actions

**Secrets required:**
- `POLLEN_BOT_TOKEN` — Telegram bot token from @BotFather
- `POLLEN_CHAT_ID` — Recipient chat ID

**Schedule:** Currently `0 7 * * *` = 10:00 AM Belarus time (UTC+3).

Manual test run available via Actions → Pollen Bot → Run workflow.
