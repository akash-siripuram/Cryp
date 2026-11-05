# Asset Plan — "Who Are You Afraid Of?" (Isaiah 51:12)

Every file below has an **exact filename** that `src/timeline.ts` expects in `public/`.
Until a file exists, the film renders a clearly labeled **"FOOTAGE NOT YET GENERATED"** slate for that shot (or silence for audio). Nothing is silently replaced by a still.
Run `npm run check` at any point to see which files are still missing and whether the footage clips are long enough.

---

## 0. Production bible (read before generating anything)

### Main character — "DANIEL" (appears in s1, s3, s4, s6)
Use this exact block at the start of **every** Daniel prompt. Generate one reference portrait first (image model) and feed it as the **character / image reference** to every video generation (Runway "References", Kling "Elements", Veo "ingredients", Sora "cameo/character", etc.).

> **DANIEL:** a 30-year-old man of mixed Mediterranean descent, olive skin with natural texture and faint pores, short dark-brown hair slightly messy on top, a neatly kept short beard with light stubble on the cheeks, dark brown eyes, a thin scar through his left eyebrow, an average athletic build. He wears a **charcoal-grey crew-neck t-shirt under an open navy-blue flannel overshirt**, dark jeans, and a plain black digital wristwatch on his left wrist.

Wardrobe stays identical in every Daniel shot (the morning in Scene 6 is the next day; it's the same overshirt, buttoned this time).

### Supporting characters (Scene 2 — distinct people, so the audience sees *themselves*)
- **Young employee "SAM":** 24-year-old East-Asian man, slim, short black hair, white button-down shirt with a loosened grey tie, lanyard ID badge.
- **Manager:** 50-year-old man, grey temples, navy suit without a tie, seen mostly from behind or out of focus. Never cartoonishly evil; tired and impatient.
- **Young woman "LEAH":** 19-year-old Black woman, natural shoulder-length curly hair, oversized cream hoodie, small gold stud earrings.
- **Mirror man "RAY":** 40-year-old white man, receding sandy hair, tired eyes, light-blue dress shirt half-buttoned, wedding ring.

### Global style suffix (append to EVERY prompt)
> Photorealistic live-action cinema, shot on ARRI Alexa 35 with Cooke anamorphic/i lenses, 2.39:1 framing with safe headroom for letterbox, natural skin texture with visible pores, realistic micro-expressions and eye moisture, shallow depth of field, motivated practical lighting, gentle halation on highlights, subtle 35mm film grain, restrained professional color grade, 24fps cinematic motion blur. No text, no logos, no subtitles, no watermark, no CGI look, no plastic skin, no beauty filter, no lens flare overload, no fantasy glow.

### Negative prompt (where supported)
> cartoon, anime, 3D render, CGI, plastic skin, airbrushed, doll face, extra fingers, distorted hands, warped face, text, letters, watermark, logo, oversaturated, HDR look, glowing halo, light rays from heaven cliché, cross, dove, angel, depiction of God, jitter, morphing.

### Generation settings
- Output **1920×1080 (16:9)**, 24 or 30 fps, highest quality tier. Keep the subject in the **middle 1920×803 band**: the film adds 2.39:1 letterbox bars of 138 px top and bottom.
- Generate **at least** the "Min. length" listed (the film checks this). The usual 5 s / 10 s generator options are fine.
- Generate 3–4 takes per shot and pick the one with the most natural face and hands.
- No text on the phone screens: the notification is composited by Remotion (`PhoneNotification.tsx`) so it's always sharp and legible. Frame the phone screen roughly at the **center of the frame**.
- Color: generate *neutral-to-slightly-graded* footage. The film's grade (`ColorGrade.tsx`) moves everything from cold blue (0 s) to golden (120 s) consistently.
- Recommended tools (Nov 2026): Google Veo, Kling, Runway Gen-4+, OpenAI Sora. Use **image-to-video with the Daniel reference** for every Daniel shot to keep his identity locked.

---

## 1. Footage — 24 shots (`public/footage/`)

### SCENE 1 — THE HOOK (0:00–0:12) · cold, blue, near-dark

**`s1_01_dark_room_wide.mp4`** · on screen 0.0–3.5 s · **Min. length 3.5 s (generate 5 s)**
- **Prompt:** DANIEL sits alone on the edge of a worn grey sofa in a small dark city apartment at night, elbows on knees, staring at nothing. The only light is cold blue moonlight and distant streetlight through half-closed venetian blinds, casting thin stripes across his face and the wall. A laptop is closed on the coffee table; a glass of water untouched. Stillness, heavy silence, slight rise and fall of his shoulders as he breathes. [Daniel block] [style suffix]
- **Camera:** locked-off wide on 35 mm, very slow push-in toward him.
- **Lighting:** cold blue moonlight (≈ 6500 K) through blinds, deep blacks, no fill.
- **Environment:** small modern apartment, rain-streaked window, city bokeh outside.
- **SFX:** `room_tone_night`, `clock_tick`.

**`s1_02_phone_lights_up.mp4`** · 3.5–6.2 s · **Min. 2.7 s (generate 5 s)**
- **Prompt:** Close insert shot: a smartphone lying face-up on a dark wooden coffee table in a pitch-dark room suddenly lights up and vibrates slightly, its cold white screen glow spilling onto the wood grain and illuminating DANIEL's hand as it slowly reaches into frame and stops, hesitating, just short of the phone. The screen shows only a soft blank glow — no readable text. Phone centered in frame. [style suffix]
- **Camera:** 50 mm macro-ish insert, static, slight focus pull from the wood grain onto the phone.
- **Lighting:** the phone screen is the only light source.
- **SFX:** `phone_buzz` (night). Remotion composites the "Mark (Manager): *We need to talk tomorrow.*" notification from 3.9 s.

**`s1_03_face_anxiety_cu.mp4`** · 6.2–8.4 s · **Min. 2.2 s (generate 5 s)**
- **Prompt:** Close-up of DANIEL's face lit from below by cold phone-screen light in a dark room. He reads a message; his jaw tightens, he swallows, his breathing becomes shallow and quicker, his eyes flick back and forth over the screen, then stop. A tiny tremor at the corner of his mouth. Absolutely realistic, understated anxiety, no overacting. [Daniel block] [style suffix]
- **Camera:** 50 mm, slow push-in, focus on the eyes.
- **Lighting:** cold blue-white underlight from the phone, darkness behind.
- **SFX:** `anxious_breath`.

**`s1_04_eyes_ecu.mp4`** · 8.4–10.0 s · **Min. 1.6 s (generate 5 s)**
- **Prompt:** Extreme close-up of DANIEL's dark brown eyes, the reflection of a glowing phone screen visible in his wet irises, a slow blink, pupils slightly dilated, faint redness at the rims. The phone light dims and the frame sinks into near-total darkness. [Daniel block: eyes, eyebrow scar visible] [style suffix]
- **Camera:** macro ECU, locked, imperceptible push.
- **Lighting:** a single cold catchlight that fades out.
- **SFX:** `sub_drop` hits as the frame goes black. Remotion adds the "WHO ARE YOU AFRAID OF?" title at 10–12 s.

### SCENE 2 — THE FEAR OF PEOPLE (0:12–0:35) · cold, oppressive, low-key

**`s2_01_office_criticism.mp4`** · 11.4–19.5 s · **Min. 8.1 s (generate 10 s)**
- **Prompt:** In a glass-walled corporate office at dusk, young employee SAM stands rigidly in front of a desk while his MANAGER, seated and out of focus in the foreground, gestures sharply at a printed report and speaks. SAM's eyes drop to the floor, he nods slightly, his fingers fidget with his ID badge; colleagues outside the glass glance in and look away. Fluorescent overhead light, cold blue dusk through the windows. Realistic, subtle humiliation. [SAM + MANAGER blocks] [style suffix]
- **Camera:** over-the-shoulder from behind the manager, 35 mm, slow lateral dolly right, rack focus onto Sam's face.
- **Lighting:** flat, cool fluorescent with blue dusk window light; harsh and unflattering.
- **SFX:** `office_ambience` (muffled), `heartbeat` begins.

**`s2_02_bedroom_crying.mp4`** · 18.7–26.5 s · **Min. 7.8 s (generate 10 s)**
- **Prompt:** Night. LEAH sits on her bedroom floor with her back against the bed, knees drawn up, holding her phone close; its light is the only light on her face. A new message arrives, she reads it, her lips press together, and tears roll silently down her cheek; she wipes them with her hoodie sleeve and keeps scrolling. Fairy lights off, posters in shadow, a cold blue window. Quiet, realistic heartbreak, no sobbing theatrics. Phone screen not readable. [LEAH block] [style suffix]
- **Camera:** 50 mm handheld-steady, slow push-in from mid-shot to close-up.
- **Lighting:** phone glow key, cold blue moon fill from window.
- **SFX:** `phone_notifications` (soft repeated message pings), heartbeat continues.

**`s2_03_mirror_worry.mp4`** · 25.7–35.0 s · **Min. 9.3 s (generate 10 s)**
- **Prompt:** RAY stands at a bathroom sink at night, hands gripping the edges of the basin, staring at himself in the mirror. Water drips from the tap. He studies his own face — the tiredness, the grey — with worry and quiet self-judgement, exhales, looks down, then forces himself to look back up. We see him both directly and in the mirror's reflection. A single cold overhead light, the rest in darkness. [RAY block] [style suffix]
- **Camera:** over-the-shoulder into the mirror, 35 mm, very slow push toward the reflection.
- **Lighting:** single hard top light, cool white, deep shadows under the eyes.
- **SFX:** `bathroom_drip`, heartbeat slows and fades by 35 s.

### SCENE 3 — THE REALIZATION (0:35–0:55) · night city → open field

**`s3_01_city_street_slowmo.mp4`** · 34.0–41.5 s · **Min. 7.5 s (generate 10 s at 120 fps slow-motion if available)**
- **Prompt:** DANIEL walks alone down a crowded downtown sidewalk at night, hands in his jacket pockets, while dozens of strangers stream past him in both directions in slow motion, blurred, faces lit by neon signs and car headlights. He moves slower than everyone else, overwhelmed, eyes unfocused. Wet pavement reflections, traffic bokeh, steam from a street grate. [Daniel block] [style suffix]
- **Camera:** 85 mm long lens, tracking backward in front of him, extreme shallow depth of field, slow motion.
- **Lighting:** mixed neon (cyan, magenta) and sodium-orange streetlights, still cold-dominant.
- **SFX:** `city_night_muffled` (traffic and voices, low-passed as if underwater).

**`s3_02_city_face_overwhelmed.mp4`** · 41.5–45.5 s · **Min. 4.0 s (generate 5 s)**
- **Prompt:** Close-up of DANIEL standing still on a busy night sidewalk as blurred pedestrians flow past in the foreground and background; he slowly lifts his eyes upward, exhausted, searching, the city lights flickering across his face. A long exhale. [Daniel block] [style suffix]
- **Camera:** 50 mm, static, slow push-in; pedestrians wipe through the frame.
- **Lighting:** neon and streetlight, cold.

**`s3_03_grass_field_wide.mp4`** · 44.3–49.5 s · **Min. 5.2 s (generate 10 s)**
- **Prompt:** Vast open meadow of tall wild grass at blue-hour dusk, endless rolling hills, wind sweeping in long waves across the grass like an ocean; a single lone tree on the horizon; heavy grey-blue clouds. No people. Epic and humbling scale. [style suffix]
- **Camera:** wide on 35 mm anamorphic, slow lateral drone/dolly drift right, low altitude.
- **Lighting:** soft cool dusk, faint warm band at the horizon (first hint of warmth).
- **SFX:** `wind_grass`.

**`s3_04_grass_closeup_wind.mp4`** · 49.0–52.0 s · **Min. 3.0 s (generate 5 s)**
- **Prompt:** Macro close-up of individual blades of wild grass bending and trembling under a strong gust of wind, seed heads shaking, dew drops falling, shallow focus with the blurred meadow behind. [style suffix]
- **Camera:** macro, locked off, shallow depth of field.
- **Lighting:** soft dusk backlight rim-lighting the blades.

**`s3_05_grass_seasons_timelapse.mp4`** · 51.4–55.0 s · **Min. 3.6 s (generate 5 s)**
- **Prompt:** Locked-off time-lapse of the same patch of meadow grass passing through the seasons: fresh green spring growth, tall summer gold, browning and withering in autumn, flattened and frost-covered in winter. Clouds race overhead, light cycles rapidly. Seamless, realistic, no CGI morphing. [style suffix]
- **Camera:** locked-off, low ground-level angle.
- **Lighting:** cycling natural daylight.
- **Music:** the score begins turning from tension to warmth here.

### SCENE 4 — GOD SPEAKS (0:55–1:25) · dawn breaks, warmth arrives
*God is never depicted. His presence is told through light, wind and Daniel's face.*

**`s4_01_sunrise_breaks_clouds.mp4`** · 53.5–61.0 s · **Min. 7.5 s (generate 10 s)**
- **Prompt:** Time-lapse of dark heavy storm clouds over a mountain valley parting as the sun rises; the first golden beams break through the gap and sweep across the valley floor, mist glowing on the hillsides. Realistic, natural, majestic but restrained — no cartoon god-rays. [style suffix]
- **Camera:** wide, slow upward tilt/rise.
- **Lighting:** cold blue shadows → warm gold (≈ 3200 K) breaking through.
- **SFX:** `dawn_wind_birds` begins softly.

**`s4_02_hill_man_wide.mp4`** · 59.8–67.0 s · **Min. 7.2 s (generate 10 s)**
- **Prompt:** Extreme wide shot: DANIEL stands small and alone on a grassy hilltop at sunrise, seen from behind and slightly to the side, overlooking a vast landscape of valleys, mist and distant mountains. Wind moves his flannel overshirt and the grass around him. The sun rises in front of him. [Daniel block] [style suffix]
- **Camera:** drone pull-back revealing the scale of the landscape.
- **Lighting:** golden backlight, long shadows, atmospheric haze.

**`s4_03_face_sunlight_cu.mp4`** · 66.0–72.0 s · **Min. 6.0 s (generate 10 s)**
- **Prompt:** Close-up of DANIEL's face as warm golden sunlight slowly falls across it from the side. His eyes are closed, then slowly open; tension drains from his jaw and forehead; his eyes become wet; a slow, deep breath out. A transformation from fear to peace, entirely realistic and understated. Wind stirs his hair. [Daniel block] [style suffix]
- **Camera:** 50 mm, very slow push-in, focus on the eyes.
- **Lighting:** warm sunrise key from frame-left, soft natural bounce, rim light on hair.

**`s4_04_trees_wind_golden.mp4`** · 71.0–76.0 s · **Min. 5.0 s (generate 5 s)**
- **Prompt:** Low-angle shot looking up through the canopy of a large old oak tree, leaves rustling and branches swaying in a warm morning wind, golden sunlight flickering through the leaves. [style suffix]
- **Camera:** slow lateral drift left, low angle.
- **Lighting:** warm sunlight dappling through the leaves.

**`s4_05_mountains_clouds_open.mp4`** · 75.0–81.0 s · **Min. 6.0 s (generate 10 s)**
- **Prompt:** Aerial view of a mountain range at golden hour, a sea of clouds below the peaks slowly opening and drifting apart to reveal a sunlit green valley underneath. Peaceful, vast. [style suffix]
- **Camera:** slow drone glide forward and slight pull-out.
- **Lighting:** warm gold, soft blue shadows.

**`s4_06_hill_man_back.mp4`** · 80.0–85.0 s · **Min. 5.0 s (generate 5 s)**
- **Prompt:** Medium shot from behind DANIEL on the hilltop, sunlight in front of him, his shoulders visibly relaxing as he lifts his head and takes a deep breath; wind moves his shirt and the grass. [Daniel block] [style suffix]
- **Camera:** slow push-in from behind.
- **Lighting:** strong warm backlight, halo-free natural rim.

### SCENE 5 — THE SCRIPTURE (1:25–1:45) · morning light on the Word
*Both shots play at 0.85× speed for extra stillness — a 10 s generation is enough.*

**`s5_01_bible_table_dolly.mp4`** · 83.5–95.0 s · **Min. 9.8 s (generate 10 s)**
- **Prompt:** A realistic, well-worn open Bible lying on a rustic oak kitchen table beside a ceramic mug of coffee, early morning golden sunlight streaming through a window and falling across the thin pages; dust particles drifting slowly in the light beam. Pages slightly curled, gentle handwritten margin notes (not readable). Center of the frame kept calm and uncluttered for overlaid text. [style suffix]
- **Camera:** slow dolly-in at a low 3/4 angle, shallow depth of field.
- **Lighting:** warm low-angle sunbeam, soft shadows, gentle haze.
- **SFX:** `page_turn` at 85.4 s.

**`s5_02_bible_pages_macro.mp4`** · 93.5–105.0 s · **Min. 9.8 s (generate 10 s)**
- **Prompt:** Macro close-up gliding slowly across the open pages of a Bible in golden morning light, the paper's texture and gilded edges visible, a page gently lifting in a soft breeze. Text is out of focus and unreadable. Center kept soft and calm for overlaid typography. [style suffix]
- **Camera:** slow lateral slide right, macro lens, very shallow depth of field.
- **Lighting:** warm gold, soft highlights, slight halation.

### SCENE 6 — THE FINAL EMOTIONAL IMPACT (1:45–2:00) · warm, hopeful sunrise

**`s6_01_morning_phone.mp4`** · 104.0–109.0 s · **Min. 5.0 s (generate 5 s)**
- **Prompt:** The same apartment as in the night scene, now filled with soft warm morning sunlight through open blinds. DANIEL, dressed (flannel overshirt now buttoned), sits at the kitchen table; his phone on the table lights up and vibrates. He looks down at it calmly. The phone screen is a blank glow, centered in the frame. [Daniel block] [style suffix]
- **Camera:** 35 mm, slow push-in from medium to medium close-up.
- **Lighting:** warm golden window light, soft fill, plants on the sill.
- **SFX:** `morning_room_birds`, `phone_buzz` (morning). Remotion composites the new message from 105.8 s.

**`s6_02_breath_phone_down.mp4`** · 109.0–112.5 s · **Min. 3.5 s (generate 5 s)**
- **Prompt:** Close-up of DANIEL reading his phone, closing his eyes, and taking one slow deep breath; a small, settled smile; he places the phone face-down on the table and his hand rests on it for a moment. Peaceful, confident. [Daniel block] [style suffix]
- **Camera:** 50 mm, static.
- **Lighting:** warm sunlight on his face.
- **SFX:** `calm_breath`.

**`s6_03_walks_outside.mp4`** · 111.7–116.0 s · **Min. 4.3 s (generate 5 s)**
- **Prompt:** DANIEL opens his apartment building door and steps out into bright warm morning sunlight, squinting slightly then lifting his face to the light, and starts walking down a tree-lined street. Natural, unhurried. [Daniel block] [style suffix]
- **Camera:** tracking from the side/behind, 35 mm, gentle lateral dolly right.
- **Lighting:** warm sunrise backlight with natural flare.
- **SFX:** `door_open_outside`, `sunrise_outdoor`.

**`s6_04_walk_toward_sunrise.mp4`** · 115.0–120.0 s · **Min. 5.0 s (generate 5 s)**
- **Prompt:** Extreme wide cinematic shot from behind: DANIEL walks along an open path toward a huge golden sunrise on the horizon, his silhouette small against the light, long shadow behind him, wind in the grass, birds crossing the sky. Hopeful, peaceful. Leave the center of the frame airy for the end titles. [Daniel block] [style suffix]
- **Camera:** slow crane up and pull-out.
- **Lighting:** full golden backlight, warm haze.
- Remotion overlays the end card "WHO ARE YOU AFRAID OF? / ISAIAH 51:12 / God is your comfort." and fades to black.

---

## 2. Voiceover (`public/vo/vo01.mp3` … `vo22.mp3`)

The complete script with exact in/out times and direction is in **`VOICEOVER_SCRIPT.md`** (generated from the timeline).

- **Best:** a real voice actor (deep, warm baritone, late 40s). Record each line as its own file; each clip must fit its window.
- **AI option:** a high-quality expressive voice model (for example an ElevenLabs "deep narrative" male voice, stability ≈ 35–45 %, style ≈ 20–30 %). Generate each line separately, choose the most natural of several takes, and avoid any robotic cadence. Ellipses in the script mark the intended pauses.
- Export: MP3 320 kbps or WAV-to-MP3, 48 kHz, mono, peak −3 dBFS, loudness ≈ −16 LUFS per clip. Trim leading silence to ~0.1 s.
- Ducking is automatic: `Soundtrack.tsx` lowers the score to 45 % under every line.

## 3. Score (`public/music/score.mp3`) — one continuous 120 s track

Commission it, license it, or generate it (e.g. a music model with the prompts below, edited together to the cue points). **The cue points matter more than the exact sound.**

| Time | Section | What the music does |
|---|---|---|
| 0:00–0:10 | Dread | Low sustained synth pad, a single detuned felt-piano note every ~2 s, distant sub pulse. Near-silence. |
| 0:10–0:12 | Hit | Silence then a soft sub-boom under the title (the film's `sub_drop` SFX layers on this). |
| 0:12–0:35 | Weight | Restrained felt piano in D minor, sparse low cello drone, heartbeat-tempo pulse (≈ 60 bpm). No melody yet. |
| 0:35–0:55 | Turning | Piano finds a simple 4-note motif; strings enter pianissimo; harmony lifts from D minor toward F major at ~0:50 over the grass time-lapse. |
| 0:55–1:25 | Dawn | Warm orchestral progression: strings swell with sunrise, French horn states the motif at ~1:01, gentle timpani roll into 1:17 ("But through His Word"), then a held breath at 1:21–1:25. |
| 1:25–1:45 | Scripture | Powerful but restrained: solo piano + soft high strings in D major, sustained; leave space for the voice. Small lift at 1:34 for the second phrase. |
| 1:45–1:56 | Courage | Full but gentle climax: strings, choir pad ("ah"), horns carry the motif, building with the walk outside. |
| 1:56–2:00 | Resolve | Final major chord on the end card, decaying to silence by 1:59.5. |

Music-model prompt: *"Cinematic emotional orchestral score, felt piano and atmospheric pads, begins dark and sparse in D minor at 60 bpm, gradually warms into a hopeful D major orchestral swell with strings, French horn and soft choir, restrained, reverent, film-score quality, no drums, no vocals with words."*

## 4. Sound effects (`public/sfx/`)

Source from licensed libraries (Soundly, Artlist, Epidemic, BBC Sound Effects RemArc licence, Freesound CC0). Looping beds should be ≥ 10 s and loop cleanly; the film loops them automatically.

| File | Use | Placement |
|---|---|---|
| `room_tone_night.mp3` | Quiet apartment hum, faint distant traffic (loop) | 0–12 s |
| `clock_tick.mp3` | Soft wall-clock tick (loop) | 0–10 s |
| `phone_buzz.mp3` | Phone vibrating on wood, 1–1.5 s | 3.5 s, 105.6 s |
| `anxious_breath.mp3` | Shallow, quickening breaths, close-mic | 6.3 s |
| `sub_drop.mp3` | Cinematic low sub boom / impact, long tail | 9.9 s |
| `heartbeat.mp3` | Slow muffled heartbeat (loop) | 12–35 s |
| `office_ambience.mp3` | Muffled open-plan office (loop) | 12–19.8 s |
| `phone_notifications.mp3` | Several soft message pings, 2–3 s | 19.6 s |
| `bathroom_drip.mp3` | Tap dripping in a tiled room (loop) | 26.5–35 s |
| `city_night_muffled.mp3` | Busy night street, low-passed / slow-mo feel (loop) | 35–46 s |
| `wind_grass.mp3` | Wind through a tall-grass field (loop) | 45–56 s |
| `dawn_wind_birds.mp3` | Gentle dawn wind + distant birdsong (loop) | 55–86 s |
| `page_turn.mp3` | A single thin Bible page turning | 85.4 s |
| `morning_room_birds.mp3` | Bright room, birds outside a window (loop) | 105–113 s |
| `calm_breath.mp3` | One slow, deep, calm breath | 109.2 s |
| `door_open_outside.mp3` | Front door opening onto a street | 112.4 s |
| `sunrise_outdoor.mp3` | Open-air morning, birds, light breeze (loop) | 112.6–120 s |

Exact volumes, fades and timings are in `SFX` in `src/timeline.ts`.
