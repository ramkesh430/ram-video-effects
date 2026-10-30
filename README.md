# Ram's Video Effects

**62 video effects for Claude.** Drop a video (or photo) into Claude, ask for an effect in plain words, and it renders the edit: words behind your head, orbiting reels, spotlights, glass widgets, tier lists, captions, confetti and more.

Made by Ramkesh Gupta ([@ramkesh430](https://github.com/ramkesh430)).

![All effects](all_effects_sheet.jpg)

## Example

One photo turned into a 12-second reel: [ram_couple_effects.mp4](ram_couple_effects.mp4)
(RAM word behind us, golden spotlight, pink neon outline, LOVE magazine cover, FOREVER collage). Plan used: [example_plan.json](example_plan.json).

<img src="original_photo.jpg" width="280">

## Install (one line)

**Mac / Linux** — open Terminal:

```bash
git clone https://github.com/ramkesh430/ram-video-effects && bash ram-video-effects/install.sh
```

**Windows** — open PowerShell:

```powershell
git clone https://github.com/ramkesh430/ram-video-effects; powershell -ExecutionPolicy Bypass -File ram-video-effects\install.ps1
```

The installer sets up Python packages, ffmpeg, the two AI models (person cut-out + face finder), optional fonts, and copies the skill to `~/.claude/skills/ram-video-effects`. Then restart Claude Code.

**Claude app (web / desktop):** download [ram-video-effects.zip](ram-video-effects.zip) and upload it in **Settings → Capabilities → Skills**.

## Use it

Drag your video into Claude and type what you want:

- `/effects orbit from 3 to 6 seconds`
- `/effects spotlight when I say "lights off", with the word FOCUS behind me`
- `/effects backdrop-word RAM for the first 2 seconds, then confetti`
- `/effects red-collage at the end with "ONE CLIP. 62 EFFECTS. ZERO APPS."`

Claude checks a few frames first, fixes anything that covers your face, then renders `yourvideo_effects.mp4` next to the original. Your audio is kept.

Tips:

- Vertical phone videos with you in frame work best. Photos work too (Claude turns them into a slow-zoom clip).
- Say timings in plain words ("when I say 'watch'"); Claude finds the exact second.
- For your own reels in orbit, noise, phone-fan, profile-wall, place-in-grid: give Claude a folder of screenshots.
- Use your real numbers for counters and graphs.

## Run it without Claude

```bash
python fx.py --list                                           # every effect + options
python fx.py in.mp4 check.png --plan plan.json --preview 1.5,4 --debug   # check frames first
python fx.py in.mp4 out.mp4 --plan plan.json                  # render (add --max-short 2160 for 4K)
```

`plan.json`:

```json
[{"fx": "backdrop-word", "start": 0, "end": 3, "text": "RAM"},
 {"fx": "glitter-spotlight", "start": 3, "end": 5.5},
 {"fx": "red-collage", "start": 10, "end": 12, "word": "FOREVER"}]
```

All 62 effects and their options: **[EFFECTS.md](EFFECTS.md)**.

## Effects

noise · lineup · locked-on · orbit · lean-in · backdrop-word · spotlight · the-bill · moody · swipe · todo · comment-box · tap · pause-point · uninstall · reel-frame · shortcut-rain · reject-stamp · countdown · countdown-flip · rabbit-hole · cover-star · scribble · glass-widgets · red-collage · split-headline · pastel-word · check-pills · timeline · headline · headline-box · profile-wall · tier-list · broll-split · phone-fan · dot-reveal · headline-wall · checklist · name-tag · slow-push · carousel-spin · liquid-glass-graph · match-cut · apple-toggles · led-sign · over-the-shoulder-zoom · messages · place-in-grid · countup · glitter-spotlight · confetti · glitch · vhs · captions · progress-bar · poll · whip-zoom · neon-outline · heart-burst · sticker · freeze-bw · split-screen

## Files

| file | what |
|---|---|
| `fx.py` | the effects engine (single file) |
| `SKILL.md` | Claude skill instructions |
| `install.sh` / `install.ps1` | installers |
| `requirements.txt` | Python packages |
| `EFFECTS.md` | every effect and its options |
| `example_plan.json` | the plan behind the example video |
| `ram-video-effects.zip` | skill for upload in the Claude app |

## Honest notes

- These are draft edits. Watch the result before you post.
- No music, sound effects or subtitles are added unless you ask for the `captions` effect.
- If something looks off, tell Claude ("the word covers my face", "too fast") and it re-renders.

## Credits

Person cut-out and face detection: Google MediaPipe (Apache 2.0). Fonts: Google Fonts (SIL OFL / Apache 2.0), downloaded by the installer. Effect ideas inspired by [claude-video-effects](https://github.com/Vibha-Ramprakash/claude-video-effects); this code is written from scratch. Code licence: MIT (see [LICENSE](LICENSE)). The example photo and video are personal and not covered by the licence.
