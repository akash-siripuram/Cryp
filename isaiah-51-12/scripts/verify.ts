/* Verifies timeline integrity and reports missing media. Exit code 1 on timeline errors. */
import {execFileSync} from 'node:child_process';
import {existsSync} from 'node:fs';
import {join} from 'node:path';
import {ALL_ASSETS, CUES, DURATION_FRAMES, DURATION_SECONDS, FPS, SCENES, SFX, SHOTS, TITLES, VERSE, f, sourceSecondsNeeded} from '../src/timeline';

const errors: string[] = [];
const ok = (m: string) => console.log(`  ✓ ${m}`);

if (DURATION_FRAMES !== 3600 || FPS !== 30 || DURATION_SECONDS !== 120) errors.push('Duration must be 120 s @ 30 fps = 3600 frames');
else ok('Duration: 120 s × 30 fps = 3600 frames');

// Scenes are contiguous 0 → 120.
SCENES.forEach((s, i) => {
	const prevEnd = i === 0 ? 0 : SCENES[i - 1].end;
	if (s.start !== prevEnd) errors.push(`Scene ${s.number} starts at ${s.start}, expected ${prevEnd}`);
});
if (SCENES[SCENES.length - 1].end !== DURATION_SECONDS) errors.push('Last scene must end at 120');
else ok('Scenes are contiguous and end at 120 s');

// Picture coverage: every frame has a shot, except the intentional black title card 10–12 s.
const allowedGaps = [[f(TITLES.hook.start), f(TITLES.hook.end)]];
let gapFrames = 0;
for (let fr = 0; fr < DURATION_FRAMES; fr++) {
	const covered = SHOTS.some((s) => fr >= f(s.start) - f(s.dissolve) && fr < f(s.end));
	const allowed = allowedGaps.some(([a, b]) => fr >= a && fr < b);
	if (!covered && !allowed) gapFrames++;
}
if (gapFrames) errors.push(`${gapFrames} frames have no picture`);
else ok('Every frame has picture (title card 10–12 s is intentional black)');

// Shots are ordered, non-overlapping (except dissolves), and inside their scene.
SHOTS.forEach((s, i) => {
	const scene = SCENES.find((x) => x.number === s.scene)!;
	if (s.end <= s.start) errors.push(`${s.id}: end <= start`);
	if (s.start < scene.start || s.end > scene.end) errors.push(`${s.id}: outside scene ${s.scene}`);
	if (i > 0 && s.start < SHOTS[i - 1].end) errors.push(`${s.id} starts before ${SHOTS[i - 1].id} ends`);
	if (i > 0 && s.dissolve > SHOTS[i - 1].end - SHOTS[i - 1].start) errors.push(`${s.id}: dissolve longer than previous shot`);
	if (s.dissolve > 2) errors.push(`${s.id}: dissolve exceeds scene lead-in (2 s)`);
});
ok(`${SHOTS.length} shots ordered, inside scenes, dissolves valid`);

// Narration: no overlaps, inside scenes, minimum 0.25 s breath between lines.
CUES.forEach((c, i) => {
	const scene = SCENES.find((x) => x.number === c.scene)!;
	if (c.start < scene.start || c.end > scene.end) errors.push(`${c.id}: outside scene ${c.scene}`);
	if (i > 0 && c.start < CUES[i - 1].end + 0.25) errors.push(`${c.id} overlaps/too close to ${CUES[i - 1].id}`);
});
// Subtitles: rendered until end + 6 frames; must never show two at once.
const subs = CUES.filter((c) => c.subtitle);
subs.forEach((c, i) => {
	if (i > 0 && f(c.start) < f(subs[i - 1].end) + 6) errors.push(`Subtitle ${c.id} overlaps ${subs[i - 1].id}`);
});
ok(`${CUES.length} voiceover cues, ${subs.length} subtitles — no overlaps`);

// Scripture text timing matches VO.
const v16 = CUES.find((c) => c.id === 'vo16')!;
const v17 = CUES.find((c) => c.id === 'vo17')!;
if (VERSE.line1.start > v16.start || VERSE.line2.start > v17.start) errors.push('Verse text must appear no later than its narration');
else ok('Scripture text appears with its narration');

SFX.forEach((s) => {
	if (s.end > DURATION_SECONDS) errors.push(`SFX ${s.id} runs past 120 s`);
});
ok(`${SFX.length} sound-effect placements within the film`);

const missing = ALL_ASSETS.filter((a) => !existsSync(join('public', a)));
console.log(`\nMedia: ${ALL_ASSETS.length - missing.length}/${ALL_ASSETS.length} present in public/`);
if (missing.length) {
	console.log('Missing (generate with PRODUCTION_WORKFLOW.md; rendering shows labeled slates / silence until added):');
	missing.forEach((m) => console.log(`  - public/${m}`));
}

// Footage that exists must be long enough for its shot.
const probe = (file: string): number | null => {
	try {
		return parseFloat(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', file]).toString());
	} catch {
		return null;
	}
};
for (const s of SHOTS) {
	const path = join('public', s.file);
	if (!existsSync(path)) continue;
	const d = probe(path);
	if (d !== null && d + 0.05 < sourceSecondsNeeded(s)) errors.push(`${s.file} is ${d.toFixed(2)} s; needs ≥ ${sourceSecondsNeeded(s).toFixed(2)} s`);
}

if (errors.length) {
	console.error('\nTIMELINE ERRORS:');
	errors.forEach((e) => console.error(`  ✗ ${e}`));
	process.exit(1);
}
console.log('\nTimeline verified.');
if (process.argv.includes('--strict') && missing.length) process.exit(1);
