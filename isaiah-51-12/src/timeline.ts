/**
 * Single source of truth for the film's timing.
 * Every value is in SECONDS; helpers convert to frames at FPS.
 * scripts/verify.ts checks this file (coverage, overlaps, duration, assets).
 */

export const FPS = 30;
export const WIDTH = 1920;
export const HEIGHT = 1080;
export const DURATION_SECONDS = 120;
export const DURATION_FRAMES = DURATION_SECONDS * FPS; // 3600

export const f = (seconds: number) => Math.round(seconds * FPS);

export type Move =
	| 'push-in'
	| 'pull-out'
	| 'drift-left'
	| 'drift-right'
	| 'rise'
	| 'static';

export type Shot = {
	id: string;
	scene: number;
	file: string; // relative to /public
	start: number;
	end: number;
	/** Dissolve length into this shot. 0 = hard cut. */
	dissolve: number;
	/** Extra virtual-camera motion layered on top of the footage's own movement. */
	move: Move;
	/** Footage seek offset in seconds (use the best part of a clip). */
	trimStart?: number;
	/** Slow-motion / speed-ramp factor passed to the video. */
	playbackRate?: number;
};

export type Scene = {
	number: number;
	title: string;
	start: number;
	end: number;
};

export const SCENES: Scene[] = [
	{number: 1, title: 'The Hook', start: 0, end: 12},
	{number: 2, title: 'The Fear of People', start: 12, end: 35},
	{number: 3, title: 'The Realization', start: 35, end: 55},
	{number: 4, title: 'God Speaks', start: 55, end: 85},
	{number: 5, title: 'The Scripture', start: 85, end: 105},
	{number: 6, title: 'The Final Emotional Impact', start: 105, end: 120},
];

export const SHOTS: Shot[] = [
	// SCENE 1 — THE HOOK
	{id: 's1_01', scene: 1, file: 'footage/s1_01_dark_room_wide.mp4', start: 0, end: 3.5, dissolve: 0, move: 'push-in'},
	{id: 's1_02', scene: 1, file: 'footage/s1_02_phone_lights_up.mp4', start: 3.5, end: 6.2, dissolve: 0, move: 'static'},
	// One continuous take: anxious close-up pushing in to an extreme close-up of the eyes.
	{id: 's1_03', scene: 1, file: 'footage/s1_03_face_to_eyes.mp4', start: 6.2, end: 10, dissolve: 0, move: 'push-in'},
	// 10–12: near-black title card (no footage)

	// SCENE 2 — THE FEAR OF PEOPLE
	{id: 's2_01', scene: 2, file: 'footage/s2_01_office_criticism.mp4', start: 12, end: 19.5, dissolve: 0.6, move: 'drift-right'},
	{id: 's2_02', scene: 2, file: 'footage/s2_02_bedroom_crying.mp4', start: 19.5, end: 26.5, dissolve: 0.8, move: 'push-in'},
	{id: 's2_03', scene: 2, file: 'footage/s2_03_mirror_worry.mp4', start: 26.5, end: 35, dissolve: 0.8, move: 'push-in'},

	// SCENE 3 — THE REALIZATION
	{id: 's3_01', scene: 3, file: 'footage/s3_01_city_street_slowmo.mp4', start: 35, end: 41.5, dissolve: 1.0, move: 'drift-left'},
	{id: 's3_02', scene: 3, file: 'footage/s3_02_city_face_overwhelmed.mp4', start: 41.5, end: 45.5, dissolve: 0, move: 'push-in'},
	{id: 's3_03', scene: 3, file: 'footage/s3_03_grass_field_wide.mp4', start: 45.5, end: 49.5, dissolve: 1.2, move: 'drift-right'},
	{id: 's3_04', scene: 3, file: 'footage/s3_04_grass_closeup_wind.mp4', start: 49.5, end: 52, dissolve: 0.5, move: 'static'},
	{id: 's3_05', scene: 3, file: 'footage/s3_05_grass_seasons_timelapse.mp4', start: 52, end: 55, dissolve: 0.6, move: 'static'},

	// SCENE 4 — GOD SPEAKS
	{id: 's4_01', scene: 4, file: 'footage/s4_01_sunrise_breaks_clouds.mp4', start: 55, end: 61, dissolve: 1.5, move: 'rise'},
	{id: 's4_02', scene: 4, file: 'footage/s4_02_hill_man_wide.mp4', start: 61, end: 67, dissolve: 1.2, move: 'pull-out'},
	{id: 's4_03', scene: 4, file: 'footage/s4_03_face_sunlight_cu.mp4', start: 67, end: 72, dissolve: 1.0, move: 'push-in'},
	{id: 's4_04', scene: 4, file: 'footage/s4_04_trees_wind_golden.mp4', start: 72, end: 76, dissolve: 1.0, move: 'drift-left'},
	{id: 's4_05', scene: 4, file: 'footage/s4_05_mountains_clouds_open.mp4', start: 76, end: 81, dissolve: 1.0, move: 'pull-out'},
	{id: 's4_06', scene: 4, file: 'footage/s4_06_hill_man_back.mp4', start: 81, end: 85, dissolve: 1.0, move: 'push-in'},

	// SCENE 5 — THE SCRIPTURE
	{id: 's5_01', scene: 5, file: 'footage/s5_01_bible_table_dolly.mp4', start: 85, end: 95, dissolve: 1.5, move: 'push-in', playbackRate: 0.85},
	{id: 's5_02', scene: 5, file: 'footage/s5_02_bible_pages_macro.mp4', start: 95, end: 105, dissolve: 1.5, move: 'drift-right', playbackRate: 0.85},

	// SCENE 6 — THE FINAL EMOTIONAL IMPACT
	// One continuous take: phone lights up, he reads, breathes, puts it down.
	{id: 's6_01', scene: 6, file: 'footage/s6_01_morning_phone_breath.mp4', start: 105, end: 112.5, dissolve: 1.0, move: 'push-in'},
	{id: 's6_02', scene: 6, file: 'footage/s6_02_walks_outside.mp4', start: 112.5, end: 116, dissolve: 0.8, move: 'drift-right'},
	{id: 's6_03', scene: 6, file: 'footage/s6_03_walk_toward_sunrise.mp4', start: 116, end: 120, dissolve: 1.0, move: 'pull-out'},
];

export type Cue = {
	id: string;
	scene: number;
	text: string;
	start: number;
	end: number;
	file: string; // voiceover clip, relative to /public
	/** Hide the subtitle when the same words are already on screen (scripture). */
	subtitle: boolean;
	direction: string;
};

export const CUES: Cue[] = [
	// SCENE 1
	{id: 'vo01', scene: 1, start: 1.4, end: 5.0, subtitle: true, text: 'Have you ever been so afraid of what someone might say…', direction: 'Slow, low, almost a whisper. Lean in.'},
	{id: 'vo02', scene: 1, start: 5.4, end: 8.8, subtitle: true, text: '…that you forgot who is watching over you?', direction: 'Let the question hang. Breath before "watching".'},
	// SCENE 2
	{id: 'vo03', scene: 2, start: 13.0, end: 17.6, subtitle: true, text: 'We fear their judgment. Their rejection. Their criticism.', direction: 'Three beats, each heavier. Half-second gap between.'},
	{id: 'vo04', scene: 2, start: 18.6, end: 21.6, subtitle: true, text: 'We replay their words in our minds.', direction: 'Tired, intimate.'},
	{id: 'vo05', scene: 2, start: 22.4, end: 25.4, subtitle: true, text: 'We lose sleep over their opinions.', direction: 'Quiet. Almost confessional.'},
	{id: 'vo06', scene: 2, start: 26.8, end: 33.6, subtitle: true, text: "Sometimes, one person's words can make us question our entire worth.", direction: 'Slow. Pause after "Sometimes". Land softly on "worth".'},
	// SCENE 3
	{id: 'vo07', scene: 3, start: 36.4, end: 39.0, subtitle: true, text: 'But think about this…', direction: 'A turn. Gentle, curious, not preachy.'},
	{id: 'vo08', scene: 3, start: 40.0, end: 44.6, subtitle: true, text: 'The very people whose opinions control your happiness…', direction: 'Measured, building.'},
	{id: 'vo09', scene: 3, start: 45.6, end: 47.6, subtitle: true, text: 'They are human too.', direction: 'Simple. Compassionate.'},
	{id: 'vo10', scene: 3, start: 48.2, end: 50.2, subtitle: true, text: 'They are temporary.', direction: 'Slight weight on "temporary".'},
	{id: 'vo11', scene: 3, start: 50.8, end: 54.6, subtitle: true, text: 'Like grass that grows today… and withers tomorrow.', direction: 'Wistful. Let "withers" fade.'},
	// SCENE 4
	{id: 'vo12', scene: 4, start: 60.0, end: 64.0, subtitle: true, text: 'And then… God speaks.', direction: 'Long pause after "And then". Warmth enters the voice.'},
	{id: 'vo13', scene: 4, start: 67.0, end: 70.6, subtitle: true, text: 'Not through the voices that condemn you.', direction: 'Firm but kind.'},
	{id: 'vo14', scene: 4, start: 71.6, end: 75.0, subtitle: true, text: 'Not through the people who judge you.', direction: 'Same rhythm as previous line.'},
	{id: 'vo15', scene: 4, start: 77.0, end: 81.0, subtitle: true, text: 'But through His Word.', direction: 'Quiet conviction. The emotional pivot of the film.'},
	// SCENE 5 — scripture appears on screen, so subtitles are suppressed
	{id: 'vo16', scene: 5, start: 87.0, end: 92.0, subtitle: false, text: 'I, even I, am he who comforts you.', direction: 'Reverent. Very slow. Every word deliberate.'},
	{id: 'vo17', scene: 5, start: 94.0, end: 101.6, subtitle: false, text: 'Who are you that you fear mere mortals, human beings who are but grass?', direction: 'Tender challenge, not rebuke. Slight break on "but grass".'},
	// SCENE 6
	{id: 'vo18', scene: 6, start: 105.4, end: 107.0, subtitle: true, text: 'People may judge you.', direction: 'Calm, settled.'},
	{id: 'vo19', scene: 6, start: 107.3, end: 108.9, subtitle: true, text: 'People may reject you.', direction: 'Same calm. No fear left.'},
	{id: 'vo20', scene: 6, start: 109.2, end: 113.2, subtitle: true, text: "But don't let temporary voices become greater than the eternal God who comforts you.", direction: 'Rising courage; weight on "eternal".'},
	{id: 'vo21', scene: 6, start: 113.6, end: 115.0, subtitle: true, text: 'Stop fearing people.', direction: 'Direct, warm, a friend speaking.'},
	{id: 'vo22', scene: 6, start: 115.3, end: 117.2, subtitle: true, text: 'Remember who walks with you.', direction: 'Softest line of the film. Smile in the voice.'},
].map((c) => ({...c, file: `vo/${c.id}.mp3`}));

export type Sfx = {
	id: string;
	file: string;
	start: number;
	end: number;
	volume: number;
	fadeIn: number;
	fadeOut: number;
	loop?: boolean;
};

export const SFX: Sfx[] = [
	{id: 'room_tone_night', file: 'sfx/room_tone_night.mp3', start: 0, end: 12, volume: 0.35, fadeIn: 0.5, fadeOut: 1.5, loop: true},
	{id: 'clock_tick', file: 'sfx/clock_tick.mp3', start: 0, end: 10, volume: 0.18, fadeIn: 0.3, fadeOut: 0.3, loop: true},
	{id: 'phone_buzz_night', file: 'sfx/phone_buzz.mp3', start: 3.5, end: 5.0, volume: 0.7, fadeIn: 0, fadeOut: 0.2},
	{id: 'anxious_breath', file: 'sfx/anxious_breath.mp3', start: 6.3, end: 9.6, volume: 0.45, fadeIn: 0.2, fadeOut: 0.6},
	{id: 'sub_drop', file: 'sfx/sub_drop.mp3', start: 9.9, end: 12, volume: 0.6, fadeIn: 0, fadeOut: 1.2},
	{id: 'heartbeat', file: 'sfx/heartbeat.mp3', start: 12, end: 35, volume: 0.32, fadeIn: 1.5, fadeOut: 2.5, loop: true},
	{id: 'office_ambience', file: 'sfx/office_ambience.mp3', start: 12, end: 19.8, volume: 0.22, fadeIn: 0.6, fadeOut: 0.6, loop: true},
	{id: 'phone_notifications', file: 'sfx/phone_notifications.mp3', start: 19.6, end: 23, volume: 0.3, fadeIn: 0, fadeOut: 0.5},
	{id: 'bathroom_drip', file: 'sfx/bathroom_drip.mp3', start: 26.5, end: 35, volume: 0.15, fadeIn: 0.8, fadeOut: 1, loop: true},
	{id: 'city_night_slowmo', file: 'sfx/city_night_muffled.mp3', start: 35, end: 46, volume: 0.35, fadeIn: 1, fadeOut: 1.5, loop: true},
	{id: 'wind_grass', file: 'sfx/wind_grass.mp3', start: 45, end: 56, volume: 0.35, fadeIn: 1.2, fadeOut: 2, loop: true},
	{id: 'dawn_wind_birds', file: 'sfx/dawn_wind_birds.mp3', start: 55, end: 86, volume: 0.25, fadeIn: 2.5, fadeOut: 2, loop: true},
	{id: 'page_turn', file: 'sfx/page_turn.mp3', start: 85.4, end: 87, volume: 0.45, fadeIn: 0, fadeOut: 0.3},
	{id: 'morning_room', file: 'sfx/morning_room_birds.mp3', start: 105, end: 113, volume: 0.25, fadeIn: 1, fadeOut: 1, loop: true},
	{id: 'phone_buzz_morning', file: 'sfx/phone_buzz.mp3', start: 105.6, end: 107, volume: 0.45, fadeIn: 0, fadeOut: 0.2},
	{id: 'calm_breath', file: 'sfx/calm_breath.mp3', start: 109.2, end: 111.8, volume: 0.4, fadeIn: 0.2, fadeOut: 0.5},
	{id: 'door_open', file: 'sfx/door_open_outside.mp3', start: 112.4, end: 114.5, volume: 0.35, fadeIn: 0, fadeOut: 0.6},
	{id: 'sunrise_outdoor', file: 'sfx/sunrise_outdoor.mp3', start: 112.6, end: 120, volume: 0.3, fadeIn: 1, fadeOut: 2.5, loop: true},
];

/** One continuous 120 s score composed to the cue sheet in PRODUCTION_WORKFLOW.md. */
export const MUSIC_FILE = 'music/score.mp3';

/** Music bed level (before VO ducking) as [seconds, volume] keyframes. */
export const MUSIC_LEVELS: [number, number][] = [
	[0, 0],
	[1.5, 0.35],
	[35, 0.4],
	[55, 0.5],
	[85, 0.45],
	[105, 0.6],
	[116.5, 0.8],
	[119.2, 0],
	[120, 0],
];
/** Music multiplier while the narrator speaks. */
export const DUCK = 0.45;
export const DUCK_RAMP = 0.35;

/** Phone notifications drawn as a crisp overlay on the phone-insert shots. */
export const PHONE_MESSAGES = [
	{id: 'night', start: 3.9, end: 6.2, sender: 'Mark (Manager)', text: 'We need to talk tomorrow.', time: '11:47 PM'},
	{id: 'morning', start: 105.8, end: 108.8, sender: 'Mark (Manager)', text: "I'm in the office. Come by when you're ready.", time: '8:12 AM'},
];

/** On-screen title cards. */
export const TITLES = {
	hook: {start: 10, end: 12},
	end: {start: 117.2, end: 120},
};

/** Scripture typography timing (Scene 5). */
export const VERSE = {
	line1: {start: 86.6, end: 104.6, text: 'I, even I, am he who comforts you.'},
	line2: {start: 93.8, end: 104.6, text: 'Who are you that you fear mere mortals, human beings who are but grass?'},
	reference: {start: 101.8, end: 104.6, text: 'ISAIAH 51:12 — NIV'},
};

/** Seconds of source footage a shot consumes (dissolve + on-screen time, scaled by playback rate). */
export const sourceSecondsNeeded = (s: Shot) => (s.trimStart ?? 0) + (s.end - s.start + s.dissolve) * (s.playbackRate ?? 1);

/** Every media file the film expects. */
export const ALL_ASSETS: string[] = [
	...SHOTS.map((s) => s.file),
	...CUES.map((c) => c.file),
	...Array.from(new Set(SFX.map((s) => s.file))),
	MUSIC_FILE,
];
