# Production Workflow — "Who Are You Afraid Of?" (Isaiah 51:12)

This is the step-by-step guide to producing every missing media file and dropping it into the Remotion project.
**Nothing in this repository is generated footage or audio.** The film becomes real only when you produce the files below.

| What | Count | Tool (recommended) | Goes in |
|---|---|---|---|
| Reference images (character lock) | 5 images | Any photoreal image model (Imagen / Nano Banana, Midjourney v7, GPT-Image, Flux) | kept outside the project |
| Video shots | **22 generations** (24 shots, 2 merged into continuous takes) | **Google Veo 3.x** and **Kling 2.x** | `public/footage/` |
| Narration | 22 short lines | **ElevenLabs** | `public/vo/` |
| Score | 1 track | **Suno** | `public/music/` |
| Sound effects | 17 files | **ElevenLabs Sound Effects** (or any licensed library) | `public/sfx/` |

**Total: 62 files.** Track progress with `npm run assets`, which rewrites `ASSET_CHECKLIST.md` from what's actually on disk.

---

## Step 0 — Set up

```bash
cd isaiah-51-12
npm install
npm run dev        # Remotion Studio: scrub the edit while you add files
```
Install **ffmpeg** (it includes `ffprobe`). `npm run assets` uses it to check durations and resolution.

---

## Step 1 — Lock the characters (5 images, do this first)

AI video drifts faces between generations. The fix is to create one reference image per character and feed it into **every** generation of that character:
- **Kling:** *Image to Video* with the reference as the start frame, or *Elements* with the reference added as an element.
- **Veo:** *Ingredients to video* / *reference images* (Flow or Gemini API), or *Frames to video* with the reference as the first frame.

### 1a. DANIEL — the main character (used in 11 shots)
Generate several and pick one with a natural, ordinary, slightly imperfect face. Save it as `ref_daniel.png`.

```text
Photorealistic medium close-up portrait of a 30-year-old man of mixed Mediterranean descent: olive skin with natural texture and visible pores, short dark-brown hair slightly messy on top, a neatly kept short beard with light stubble on the cheeks, dark brown eyes, a thin pale scar through his left eyebrow, ordinary handsome face, not a model. He wears a charcoal-grey crew-neck t-shirt under an open navy-blue flannel overshirt and a plain black digital wristwatch on his left wrist. Neutral, slightly tired expression. Soft window light, neutral grey background, shot on 50mm, f/2.0, natural color, film-like, no retouching.
```
Also generate a **full-body** version (same prompt, "full-body standing, dark jeans, brown leather boots") as `ref_daniel_full.png`, for the walking and hill shots.

### 1b. Supporting characters (one image each)
- `ref_sam.png`: *Photorealistic portrait of a 24-year-old East-Asian man, slim, short black hair, white button-down shirt with a loosened grey tie and a lanyard ID badge, nervous expression, office light, natural skin texture.*
- `ref_leah.png`: *Photorealistic portrait of a 19-year-old Black woman with natural shoulder-length curly hair, oversized cream hoodie, small gold stud earrings, soft melancholy expression, dim warm bedroom light, natural skin texture.*
- `ref_ray.png`: *Photorealistic portrait of a 40-year-old white man with receding sandy hair, tired eyes, light-blue dress shirt half-buttoned, wedding ring, bathroom mirror light, natural skin texture.*

(The manager in shot s2_01 is kept out of focus and from behind, so he needs no reference.)

---

## Step 2 — Generate the 22 video shots

### Settings for every shot
| Setting | Value |
|---|---|
| Resolution | **1920×1080 (1080p), 16:9**. If a tool only exports 720p, upscale to 1080p (Topaz Video AI, or the tool's own upscaler) before placing it. |
| Format | **MP4 (H.264)**, 24 or 30 fps. Audio is ignored: the project mutes all footage. |
| Duration | Generate the **Gen. length** in the table (always at least the **Min.** the edit uses). |
| Framing | The film adds 2.39:1 letterbox bars (138 px top and bottom). Keep heads and key action in the **middle 80 %** vertically. |
| Takes | Generate 2–4 takes per shot; reject warped hands, morphing faces, or plastic skin. |
| Kling | Model **2.1 Master / 2.5 Turbo Pro or newer**, mode **Professional**, *Creativity / CFG ≈ 0.5*, paste the **Negative prompt** below. |
| Veo | **Veo 3 / 3.1 (Quality)**, 16:9, 1080p. Veo also generates sound; that's fine, because the project mutes it. Append *"No dialogue, no music."* to the prompt. |

**Negative prompt (Kling; for Veo add as "Avoid: …"):**
```text
cartoon, anime, 3D render, CGI, plastic skin, airbrushed, beauty filter, doll face, distorted hands, extra fingers, morphing face, warped features, text, letters, subtitles, watermark, logo, oversaturated, HDR, glowing halo, god rays cliché, cross, dove, angel, jitter, flicker
```

**Every prompt below is complete. Copy the whole block.** Each one already includes the character description and the film's look, so nothing needs to be assembled.

### Shot list overview (generation order: grouped by location and lighting for consistency)

| # | Output file (`public/footage/`) | Engine | Gen. length | Min. used | Reference | On screen |
|---|---|---|---|---|---|---|
| 1 | `s1_01_dark_room_wide.mp4` | Kling | 5 s | 3.5 s | Daniel | 0:00.0–0:03.5 |
| 2 | `s1_02_phone_lights_up.mp4` | Veo | 4 s | 2.7 s | — | 0:03.5–0:06.2 |
| 3 | `s1_03_face_to_eyes.mp4` | Kling | 5 s | 3.8 s | Daniel | 0:06.2–0:10.0 |
| 4 | `s2_01_office_criticism.mp4` | Kling | 10 s | 8.1 s | Sam | 0:11.4–0:19.5 |
| 5 | `s2_02_bedroom_crying.mp4` | Kling | 10 s | 7.8 s | Leah | 0:18.7–0:26.5 |
| 6 | `s2_03_mirror_worry.mp4` | Kling | 10 s | 9.3 s | Ray | 0:25.7–0:35.0 |
| 7 | `s3_01_city_street_slowmo.mp4` | Kling | 10 s | 7.5 s | Daniel (full) | 0:34.0–0:41.5 |
| 8 | `s3_02_city_face_overwhelmed.mp4` | Kling | 5 s | 4.0 s | Daniel | 0:41.5–0:45.5 |
| 9 | `s3_03_grass_field_wide.mp4` | Veo | 8 s | 5.2 s | — | 0:44.3–0:49.5 |
| 10 | `s3_04_grass_closeup_wind.mp4` | Veo | 4 s | 3.0 s | — | 0:49.0–0:52.0 |
| 11 | `s3_05_grass_seasons_timelapse.mp4` | Veo | 4 s | 3.6 s | — | 0:51.4–0:55.0 |
| 12 | `s4_01_sunrise_breaks_clouds.mp4` | Veo | 8 s | 7.5 s | — | 0:53.5–1:01.0 |
| 13 | `s4_02_hill_man_wide.mp4` | Kling | 10 s | 7.2 s | Daniel (full) | 0:59.8–1:07.0 |
| 14 | `s4_03_face_sunlight_cu.mp4` | Kling | 10 s | 6.0 s | Daniel | 1:06.0–1:12.0 |
| 15 | `s4_04_trees_wind_golden.mp4` | Veo | 6 s | 5.0 s | — | 1:11.0–1:16.0 |
| 16 | `s4_05_mountains_clouds_open.mp4` | Veo | 8 s | 6.0 s | — | 1:15.0–1:21.0 |
| 17 | `s4_06_hill_man_back.mp4` | Kling | 5 s | 5.0 s | Daniel (full) | 1:20.0–1:25.0 |
| 18 | `s5_01_bible_table_dolly.mp4` | Kling | 10 s | 9.8 s* | — | 1:23.5–1:35.0 |
| 19 | `s5_02_bible_pages_macro.mp4` | Kling | 10 s | 9.8 s* | — | 1:33.5–1:45.0 |
| 20 | `s6_01_morning_phone_breath.mp4` | Kling | 10 s | 8.5 s | Daniel | 1:44.0–1:52.5 |
| 21 | `s6_02_walks_outside.mp4` | Kling | 5 s | 4.3 s | Daniel (full) | 1:51.7–1:56.0 |
| 22 | `s6_03_walk_toward_sunrise.mp4` | Kling | 5 s | 5.0 s | Daniel (full) | 1:55.0–2:00.0 |

\* The two Bible shots play at 0.85× speed for stillness, so 10 s of footage covers 11.5 s of screen time.
Why two engines: **Kling** handles 10 s clips and image-referenced characters well, and **Veo** is strongest on landscapes, light and macro nature. Either engine can make any shot; just keep the Gen. length.

**Merged shots (saves 2 generations):** the anxious close-up and the extreme close-up of the eyes are now one continuous push-in (`s1_03_face_to_eyes`), and the morning phone moment plus the deep breath are one continuous take (`s6_01_morning_phone_breath`). Continuous takes also play more naturally than a cut between two separate generations.

**Two shots can't be merged:**
- **Scene 2's three people:** different characters and rooms.
- **Wide and close shots of one place:** different lenses. One generation can't give a true wide and a true macro without looking like a digital zoom.

---

### SCENE 1 — THE HOOK · cold, blue, near-dark

#### 1 · `s1_01_dark_room_wide.mp4` · Kling · 5 s · Image-to-video from `ref_daniel.png`
**Camera:** locked-off wide shot, 35 mm, very slow push-in. **Composition:** Daniel on the right third, dark empty space on the left, window behind.
```text
Cinematic wide shot, night, inside a small dark city apartment. A 30-year-old man of mixed Mediterranean descent with olive skin, short dark-brown hair, a short neat beard, a thin scar through his left eyebrow, wearing a charcoal-grey t-shirt under an open navy-blue flannel overshirt and a black digital watch, sits alone on the edge of a worn grey sofa, elbows on his knees, staring at nothing. The only light is cold blue moonlight and distant streetlight through half-closed venetian blinds, casting thin stripes across his face and the wall. A closed laptop and an untouched glass of water on the coffee table; rain on the window, blurred city lights outside. Total stillness, only his slow breathing moves his shoulders. Very slow push-in. Shot on ARRI Alexa with a 35mm anamorphic lens, shallow depth of field, deep blacks, cold desaturated blue grade, natural skin texture, subtle film grain, photorealistic live-action film.
```

#### 2 · `s1_02_phone_lights_up.mp4` · Veo · 4 s · Text-to-video
**Camera:** static 50 mm insert, slight focus pull from the wood grain onto the phone. **Composition:** phone dead-center (the message banner is composited there by Remotion).
```text
Cinematic close insert shot, pitch-dark room at night. A black smartphone lies face-up in the exact center of frame on a dark wooden coffee table. The screen suddenly lights up with a soft blank white glow and the phone vibrates against the wood; the cold light spills across the wood grain. A man's hand, with a black digital wristwatch and the cuff of a navy flannel shirt, slowly reaches in from the right and stops just short of the phone, hesitating. The screen shows no readable text, only a plain glow. Static camera, slight focus pull onto the phone, 50mm lens, shallow depth of field, cold blue tones, photorealistic, subtle film grain. No dialogue, no music.
```

#### 3 · `s1_03_face_to_eyes.mp4` · Kling · 5 s · Image-to-video from `ref_daniel.png`
**Camera:** one continuous slow push-in from a close-up of the face to an extreme close-up of the eyes over the 5 seconds. **Composition:** eyes on the upper third line, face lit from below.
```text
Cinematic close-up at night of a 30-year-old man of mixed Mediterranean descent, olive skin with visible pores, short dark-brown hair, short neat beard, dark brown eyes, thin scar through his left eyebrow, face lit from below only by the cold blue-white light of a phone he is reading. He reads a message: his jaw tightens, he swallows, his breathing becomes shallow and quick, his eyes flick across the screen and then stop. The camera pushes in slowly and continuously until the frame is an extreme close-up of his wet dark-brown eyes, the phone screen's glow reflected in his irises, one slow blink. Understated, realistic anxiety, no overacting. Darkness all around. 50mm macro, shallow depth of field, cold desaturated grade, natural skin texture, subtle film grain, photorealistic live-action film.
```

### SCENE 2 — THE FEAR OF PEOPLE · cold, oppressive, low-key

#### 4 · `s2_01_office_criticism.mp4` · Kling · 10 s · Image-to-video from `ref_sam.png`
**Camera:** over the shoulder from behind the seated manager, 35 mm, slow lateral dolly right with a rack focus onto Sam. **Composition:** manager's shoulder soft in the left foreground, Sam standing center-right.
```text
Cinematic over-the-shoulder shot in a glass-walled corporate office at dusk. In the soft-focus foreground a seated 50-year-old manager with grey temples in a navy suit, seen from behind, taps a printed report and gestures impatiently as he talks. Facing him stands a 24-year-old East-Asian employee, slim, short black hair, white button-down shirt with a loosened grey tie and a lanyard ID badge. The employee's eyes drop to the floor, he nods slightly, his fingers fidget with his badge, and his jaw tightens as he holds back emotion. Colleagues outside the glass glance in and look away. Flat cold fluorescent light and blue dusk through the windows. Slow lateral dolly to the right with a rack focus onto the employee's face. 35mm lens, shallow depth of field, cold desaturated grade, natural skin texture, realistic subtle body language, subtle film grain, photorealistic live-action film.
```

#### 5 · `s2_02_bedroom_crying.mp4` · Kling · 10 s · Image-to-video from `ref_leah.png`
**Camera:** steady handheld feel, 50 mm, slow push-in from a medium shot to a close-up. **Composition:** Leah low in frame on the left, cold window on the right.
```text
Cinematic night shot in a dim teenage bedroom. A 19-year-old Black woman with natural shoulder-length curly hair, an oversized cream hoodie and small gold stud earrings sits on the floor with her back against the bed and her knees drawn up, holding her phone close. The phone's light is the only light on her face, with a cold blue moonlit window behind her. She reads a new message; her lips press together, her eyes fill, and a single tear rolls silently down her cheek. She wipes it with her sleeve and keeps scrolling. Quiet, realistic heartbreak, no sobbing. The phone screen is not readable. Slow push-in from medium shot to close-up, steady handheld, 50mm lens, shallow depth of field, cold desaturated grade, natural skin texture, subtle film grain, photorealistic live-action film.
```

#### 6 · `s2_03_mirror_worry.mp4` · Kling · 10 s · Image-to-video from `ref_ray.png`
**Camera:** over the shoulder into the mirror, 35 mm, very slow push toward the reflection. **Composition:** his real shoulder in the dark foreground, the reflection centered.
```text
Cinematic night shot in a small bathroom, filmed over a man's shoulder into the mirror. A 40-year-old white man with receding sandy hair, tired eyes, a light-blue dress shirt half-buttoned and a wedding ring grips the edges of the sink and stares at his reflection. A single hard cold overhead light, deep shadows under his eyes, the rest of the room in darkness; water drips slowly from the tap. He studies his own face with worry and quiet self-judgement, exhales, looks down at the basin, then forces himself to look back up. Very slow push-in toward the reflection. 35mm lens, shallow depth of field, cold desaturated grade, natural skin texture, realistic micro-expressions, subtle film grain, photorealistic live-action film.
```

### SCENE 3 — THE REALIZATION · night city → open field

#### 7 · `s3_01_city_street_slowmo.mp4` · Kling · 10 s · Image-to-video from `ref_daniel_full.png`
**Camera:** 85 mm long lens tracking backward in front of him, slow motion. **Composition:** Daniel centered, crowd streaming past in soft focus on both sides.
```text
Cinematic slow-motion tracking shot at night on a crowded downtown sidewalk. A 30-year-old man of mixed Mediterranean descent with short dark-brown hair, a short beard, a charcoal t-shirt under an open navy-blue flannel overshirt, dark jeans and brown boots walks slowly toward camera with his hands in his pockets, overwhelmed, eyes unfocused. Dozens of strangers stream past him in both directions, blurred, faces lit by neon signs and headlights. He moves slower than everyone else. Wet pavement reflections, traffic bokeh, steam rising from a street grate. Camera tracks backward in front of him in smooth slow motion. 85mm lens, very shallow depth of field, cyan and sodium-orange city light with cold shadows, natural skin texture, subtle film grain, photorealistic live-action film.
```

#### 8 · `s3_02_city_face_overwhelmed.mp4` · Kling · 5 s · Image-to-video from `ref_daniel.png`
**Camera:** static 50 mm close-up with a slow push-in; pedestrians wipe through the foreground. **Composition:** face center-right, looking up and out of frame left.
```text
Cinematic close-up at night of a 30-year-old man of mixed Mediterranean descent, olive skin, short dark-brown hair, short neat beard, thin scar through his left eyebrow, navy flannel overshirt, standing still on a busy sidewalk while blurred pedestrians pass close in the foreground and background. Neon and streetlights flicker across his face. Exhausted, he slowly lifts his eyes upward as if searching for something, then lets out a long breath. Slow push-in, 50mm lens, shallow depth of field, cool city light, natural skin texture, realistic eyes, subtle film grain, photorealistic live-action film.
```

#### 9 · `s3_03_grass_field_wide.mp4` · Veo · 8 s · Text-to-video
**Camera:** wide, low-altitude slow lateral drift to the right. **Composition:** horizon on the lower third, a lone tree on the right third.
```text
Cinematic extreme wide shot at blue-hour dusk of a vast meadow of tall wild grass across endless rolling hills. Strong wind sweeps long waves through the grass like an ocean. A single lone tree on the distant horizon; heavy grey-blue clouds above with a faint warm band of light at the horizon. No people. Humbling scale. Slow, smooth low-altitude lateral drift to the right. 35mm anamorphic lens, soft cool light, natural color, subtle film grain, photorealistic nature cinematography. No dialogue, no music.
```

#### 10 · `s3_04_grass_closeup_wind.mp4` · Veo · 4 s · Text-to-video
**Camera:** locked-off macro. **Composition:** blades in sharp focus across the frame center, blurred meadow behind.
```text
Cinematic macro close-up of individual blades of tall wild grass and seed heads bending and trembling hard under a gust of wind at dusk, dew drops shaking loose, soft backlight rim-lighting each blade, the meadow behind melting into a soft blur. Locked-off camera, macro lens, very shallow depth of field, natural muted color, subtle film grain, photorealistic. No dialogue, no music.
```

#### 11 · `s3_05_grass_seasons_timelapse.mp4` · Veo · 4 s · Text-to-video
**Camera:** locked-off, ground level. **Composition:** one patch of grass filling the lower two-thirds, sky above.
```text
Locked-off ground-level time-lapse of a single patch of meadow grass passing through the seasons in one continuous shot: fresh green spring shoots grow tall, turn summer gold, brown and wither in autumn, then lie flattened and white with winter frost. Clouds race across the sky and the daylight cycles rapidly. Realistic photographic time-lapse, no morphing, natural color, subtle film grain. No dialogue, no music.
```

### SCENE 4 — GOD SPEAKS · dawn breaks, warmth arrives (God is never depicted: only light, wind and Daniel's face)

#### 12 · `s4_01_sunrise_breaks_clouds.mp4` · Veo · 8 s · Text-to-video
**Camera:** wide, slow upward rise. **Composition:** the break in the clouds on the upper-right third, valley below.
```text
Cinematic wide time-lapse at dawn over a mountain valley: dark, heavy storm clouds slowly part as the sun rises, and the first warm golden sunlight breaks through the gap and sweeps across the valley floor, mist glowing on the hillsides. Natural and majestic but restrained, realistic light, no exaggerated rays. Slow upward camera rise. Cold blue shadows giving way to warm gold. Shot on a large-format cinema camera, subtle film grain, photorealistic nature cinematography. No dialogue, no music.
```

#### 13 · `s4_02_hill_man_wide.mp4` · Kling · 10 s · Image-to-video from `ref_daniel_full.png`
**Camera:** drone pull-back revealing the landscape. **Composition:** Daniel small on the left third, the sunrise on the right.
```text
Cinematic extreme wide drone shot at sunrise. A 30-year-old man with short dark-brown hair, a charcoal t-shirt under an open navy-blue flannel overshirt, dark jeans and brown boots stands alone on a grassy hilltop, seen from behind and slightly to the side, overlooking a vast landscape of misty valleys and distant mountains. The wind moves his overshirt and the grass around him. The sun rises ahead of him, golden backlight, long shadows, atmospheric haze. Slow drone pull-back revealing the immense scale of the land. Anamorphic lens, warm golden grade, subtle film grain, photorealistic live-action film.
```

#### 14 · `s4_03_face_sunlight_cu.mp4` · Kling · 10 s · Image-to-video from `ref_daniel.png`
**Camera:** 50 mm, very slow push-in, focus on the eyes. **Composition:** face center-left, sun from frame left.
```text
Cinematic close-up at sunrise of a 30-year-old man of mixed Mediterranean descent, olive skin with visible pores, short dark-brown hair moving in the wind, short neat beard, dark brown eyes, thin scar through his left eyebrow, navy flannel overshirt. Warm golden sunlight slowly spreads across his face from the left. His eyes are closed, then slowly open; the tension drains from his forehead and jaw, his eyes become wet, and he lets out one long, deep breath. A quiet transformation from fear to peace, completely natural and understated. Very slow push-in, 50mm lens, shallow depth of field, warm golden key with soft natural bounce, natural skin texture, subtle film grain, photorealistic live-action film.
```

#### 15 · `s4_04_trees_wind_golden.mp4` · Veo · 6 s · Text-to-video
**Camera:** low angle looking up, slow lateral drift left. **Composition:** trunk on the left edge, canopy filling the frame.
```text
Cinematic low-angle shot looking up through the canopy of a large old oak tree at sunrise. Leaves rustle and branches sway in a warm morning wind; golden sunlight flickers and dapples through the moving leaves. Slow lateral drift to the left. Natural, warm golden light, shallow depth of field, subtle film grain, photorealistic nature cinematography. No dialogue, no music.
```

#### 16 · `s4_05_mountains_clouds_open.mp4` · Veo · 8 s · Text-to-video
**Camera:** slow forward drone glide with a slight pull-out. **Composition:** peaks along the top third, the valley opening in the center.
```text
Cinematic aerial shot at golden hour of a mountain range rising above a sea of clouds. The clouds below slowly open and drift apart, revealing a sunlit green valley underneath. Peaceful and vast. Slow, smooth forward drone glide with a slight pull-out. Warm gold light with soft blue shadows, natural color, subtle film grain, photorealistic nature cinematography. No dialogue, no music.
```

#### 17 · `s4_06_hill_man_back.mp4` · Kling · 5 s · Image-to-video from `ref_daniel_full.png`
**Camera:** slow push-in from behind. **Composition:** Daniel's back center frame, the sun just right of his head.
```text
Cinematic medium shot from behind of a 30-year-old man with short dark-brown hair in a navy-blue flannel overshirt standing on a grassy hilltop at sunrise, facing the rising sun. His shoulders visibly relax; he lifts his head and takes one slow, deep breath. Wind moves his shirt, his hair and the grass. Strong warm natural backlight with a soft rim on his hair and shoulders. Slow push-in. 50mm lens, shallow depth of field, warm golden grade, subtle film grain, photorealistic live-action film.
```

### SCENE 5 — THE SCRIPTURE · golden morning light (the verse is overlaid, so keep the center calm)

#### 18 · `s5_01_bible_table_dolly.mp4` · Kling · 10 s · Text-to-video
**Camera:** slow dolly-in at a low three-quarter angle. **Composition:** Bible lower-center, sunbeam crossing it diagonally, uncluttered upper half for text.
```text
Cinematic shot of a realistic, well-worn open Bible lying on a rustic oak kitchen table beside a ceramic mug of coffee. Early-morning golden sunlight streams through a window and falls diagonally across the thin pages; dust particles drift slowly in the light beam. Pages slightly curled, the print soft and unreadable. Calm, uncluttered composition with empty space above the book. Slow dolly-in at a low three-quarter angle. 50mm lens, shallow depth of field, warm golden light with soft shadows and gentle haze, subtle film grain, photorealistic.
```

#### 19 · `s5_02_bible_pages_macro.mp4` · Kling · 10 s · Text-to-video
**Camera:** slow lateral slide to the right, macro. **Composition:** page curve across the lower half, soft bokeh above.
```text
Cinematic macro shot gliding slowly across the open pages of a Bible in warm golden morning light. The fine paper texture and gilded page edges catch the light; one page gently lifts in a soft breeze and settles. The printed text is out of focus and unreadable. Soft bokeh highlights fill the upper half of the frame. Slow lateral slide to the right, macro lens, very shallow depth of field, warm gold tones, gentle halation, subtle film grain, photorealistic.
```

### SCENE 6 — THE FINAL EMOTIONAL IMPACT · warm, hopeful sunrise

#### 20 · `s6_01_morning_phone_breath.mp4` · Kling · 10 s · Image-to-video from `ref_daniel.png`
**Camera:** one continuous slow push-in from a medium shot to a medium close-up. **Composition:** Daniel at a table center-left, phone in front of him near the center of frame (the message banner is composited by Remotion).
```text
Cinematic morning shot inside the same small city apartment, now filled with soft warm sunlight through open blinds, plants on the windowsill. A 30-year-old man of mixed Mediterranean descent, olive skin, short dark-brown hair, short neat beard, thin scar through his left eyebrow, wearing a charcoal t-shirt under a navy-blue flannel overshirt (now buttoned) and a black digital watch, sits at the kitchen table. His phone in front of him lights up and vibrates. He looks down at it calmly and reads it, closes his eyes, takes one slow deep breath, a small settled smile forms, and he places the phone face-down on the table, resting his hand on it for a moment. Peaceful, confident, natural. Slow continuous push-in from medium shot to medium close-up. 35mm lens, shallow depth of field, warm golden window light, natural skin texture, subtle film grain, photorealistic live-action film.
```

#### 21 · `s6_02_walks_outside.mp4` · Kling · 5 s · Image-to-video from `ref_daniel_full.png`
**Camera:** tracking from the side and behind, gentle dolly right. **Composition:** doorway on the left, the street and sun on the right.
```text
Cinematic morning shot: a 30-year-old man with short dark-brown hair, a buttoned navy-blue flannel overshirt, dark jeans and brown boots opens the front door of his apartment building and steps out into bright warm sunlight. He squints, lifts his face to the light for a moment, and starts walking down a quiet tree-lined street, unhurried. Camera tracks from the side and slightly behind with a gentle dolly to the right. Warm sunrise backlight with natural lens flare, 35mm lens, shallow depth of field, warm golden grade, subtle film grain, photorealistic live-action film.
```

#### 22 · `s6_03_walk_toward_sunrise.mp4` · Kling · 5 s · Image-to-video from `ref_daniel_full.png`
**Camera:** slow crane up and pull-out. **Composition:** Daniel small in the lower center, the sun just above the horizon, open sky in the center for the end titles.
```text
Cinematic extreme wide shot from behind at sunrise: a man in a navy-blue flannel overshirt and dark jeans walks along an open dirt path through tall golden grass toward a huge sun rising on the horizon. His silhouette is small against the light, a long shadow stretches behind him, wind moves the grass, a few birds cross the sky. Hopeful and peaceful. Wide open sky in the center of the frame. Slow crane up and pull-out. Anamorphic lens, full warm golden backlight, atmospheric haze, subtle film grain, photorealistic live-action film.
```

### After generating each shot
1. Pick the best take. Trim nothing unless the start is bad; if you trim, keep at least the **Min.** length.
2. Upscale to 1920×1080 if needed, and export MP4 H.264.
3. Rename it to the **exact** filename and place it in `public/footage/`.
4. Run `npm run assets`, then check it in `npm run dev`.

---

## Step 3 — Narration (ElevenLabs)

Open **`VOICEOVER_SCRIPT.md`**. It holds all 22 lines with exact timestamps, maximum lengths, delivery notes, ElevenLabs-ready text (with `<break>` pauses), the recommended voice and settings, and a full read-through for auditioning voices.

1. Audition 3 voices with the read-through; pick the warmest and most human one (default: **"Brian"**).
2. Generate each line with the same voice and settings, choosing the best of 3 takes.
3. Save as `public/vo/vo01.mp3` … `public/vo/vo22.mp3`.
4. Run `npm run assets`. Any line longer than its max length is flagged; regenerate it slightly faster.

Ducking is automatic: the music drops to 45 % under every line.

---

## Step 4 — Music (Suno)

Generate in **Suno (v4.5 or newer)**, *Custom* mode, **Instrumental ON**.

**Style of music** (paste into the Style field):
```text
cinematic film score, emotional orchestral, felt piano, atmospheric synth pads, cello drone, slow heartbeat pulse, strings swell, French horn, soft wordless choir, D minor to D major, 60 bpm, restrained, reverent, hopeful climax, Hans Zimmer and Max Richter inspired, no drums, no vocals
```
(If Suno rejects artist names, delete "Hans Zimmer and Max Richter inspired".)

**Lyrics field** (structure tags only; with Instrumental on, these steer the arrangement):
```text
[Intro: near silence, low synth pad, single detuned felt piano notes, distant sub pulse, dread]
[Verse 1: sparse felt piano in D minor, low cello drone, slow heartbeat pulse, heavy and lonely]
[Build: piano finds a simple four-note motif, pianissimo strings enter, harmony lifts toward F major, the first hint of warmth]
[Pre-Chorus: strings swell like a sunrise, French horn states the motif, gentle timpani roll, then a held breath]
[Bridge: solo piano and soft high strings in D major, sustained, reverent, lots of space]
[Chorus: full but gentle climax, strings, horns and soft wordless choir carry the motif, hopeful and courageous]
[Outro: final major chord, long decay into silence]
```

**Emotional map the score must follow** (the film's timing):

| Film time | Feeling | Music |
|---|---|---|
| 0:00–0:12 | Dread, a sleepless night | Near-silence, pad, lone piano notes |
| 0:12–0:35 | Weight of others' opinions | Sparse D-minor piano, cello drone, ≈ 60 bpm heartbeat pulse |
| 0:35–0:55 | Perspective, the grass | Four-note motif, strings enter, lift toward major |
| 0:55–1:25 | Dawn, "God speaks" | Warm orchestral swell, horn motif, timpani roll into 1:17, held breath 1:21–1:25 |
| 1:25–1:45 | The scripture | Restrained: solo piano + high strings, space for the voice |
| 1:45–2:00 | Courage, walking into the sun | Gentle climax with choir, resolving chord by 1:58 |

**Fitting it to the film:**
1. Generate 4–6 versions and pick the one whose **build lands near 0:55** and whose **climax sits after 1:40**.
2. Suno tracks often run 2–4 minutes. In any editor (Audacity, GarageBand, DaVinci Resolve, or Suno's own editor), cut or extend at phrase boundaries so the big swell starts around **0:55** and the climax around **1:45**. Then make the file **at least 120 s** long.
3. Export `public/music/score.mp3` (320 kbps). You don't need to fade the ending: Remotion fades the music to silence by 1:59.2 and lowers it under the narration.

---

## Step 5 — Sound effects (17 files)

The quickest route is **ElevenLabs → Sound Effects** (royalty-free with a paid plan), one prompt per file. Freesound (CC0), Soundly, Epidemic or Artlist work too. Beds marked *loop* are looped automatically by the project.

| File (`public/sfx/`) | Length | ElevenLabs Sound Effects prompt |
|---|---|---|
| `room_tone_night.mp3` | 15 s, loop | Quiet small apartment at night, faint fridge hum, very distant city traffic, room tone |
| `clock_tick.mp3` | 10 s, loop | Soft quiet wall clock ticking in a silent room |
| `phone_buzz.mp3` | 1.5 s | Smartphone vibrating twice on a wooden table, close |
| `anxious_breath.mp3` | 3.5 s | Man's shallow, quickening anxious breathing, close microphone, no voice |
| `sub_drop.mp3` | 3 s | Deep cinematic sub-bass boom impact with long dark tail |
| `heartbeat.mp3` | 10 s, loop | Slow muffled human heartbeat, 60 bpm, deep and soft |
| `office_ambience.mp3` | 10 s, loop | Muffled open-plan office behind glass, keyboards, distant murmur |
| `phone_notifications.mp3` | 3 s | Three soft smartphone message notification pings in a quiet room |
| `bathroom_drip.mp3` | 10 s, loop | Slow water drip from a tap into a sink in a small tiled bathroom at night |
| `city_night_muffled.mp3` | 15 s, loop | Busy city street at night heard as if underwater, muffled traffic and crowd, slow-motion feel |
| `wind_grass.mp3` | 15 s, loop | Strong wind sweeping through a tall-grass meadow |
| `dawn_wind_birds.mp3` | 20 s, loop | Gentle dawn breeze on a hilltop with distant birdsong, peaceful |
| `page_turn.mp3` | 1.5 s | Single thin Bible page turning, close, soft paper |
| `morning_room_birds.mp3` | 10 s, loop | Bright quiet apartment in the morning, birds singing outside an open window |
| `calm_breath.mp3` | 2.5 s | One slow, deep, calm breath in and out, close microphone, no voice |
| `door_open_outside.mp3` | 2 s | Apartment building front door opening onto a quiet morning street |
| `sunrise_outdoor.mp3` | 15 s, loop | Open countryside at sunrise, light breeze, birds, peaceful |

Exact placement, volume and fades are already set in `SFX` in `src/timeline.ts`.

---

## Step 6 — Final check and render

```bash
npm run assets       # ASSET_CHECKLIST.md must say 62 ready, 0 problems, 0 missing
npm run dev          # watch the whole film once in the Studio, with sound
npm run render       # checks timeline + assets (strict), then renders out/who-are-you-afraid-of.mp4
npm run srt          # out/subtitles.srt for YouTube/Vimeo captions
```

`npm run render` refuses to start until every asset is ready, so a draft with slates can't be mistaken for the final film. For a quick preview with whatever exists so far, use `npm run render:draft`.

### Fine-tuning after the real footage is in
- **Phone message position:** if the phone in `s1_02` / `s6_01` isn't at the center, change the `anchor` on `<PhoneNotification>` in `src/scenes/Scenes.tsx` (x/y in pixels, scale).
- **Best part of a clip:** set `trimStart` (seconds) on that shot in `src/timeline.ts`.
- **Cut points or dissolves:** edit `start`, `end` and `dissolve` in `src/timeline.ts`, then run `npm run check`.
- **Grade:** footage that comes out too warm or too cold is corrected by the film-wide grade; adjust the keyframes in `src/components/ColorGrade.tsx` if needed.
