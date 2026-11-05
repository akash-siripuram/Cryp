/* Writes out/subtitles.srt (all narration, including scripture) from the timeline. */
import {mkdirSync, writeFileSync} from 'node:fs';
import {CUES} from '../src/timeline';

const ts = (s: number) => {
	const ms = Math.round(s * 1000);
	const p = (n: number, w = 2) => String(n).padStart(w, '0');
	return `${p(Math.floor(ms / 3600000))}:${p(Math.floor(ms / 60000) % 60)}:${p(Math.floor(ms / 1000) % 60)},${p(ms % 1000, 3)}`;
};
const srt = CUES.map((c, i) => `${i + 1}\n${ts(c.start)} --> ${ts(c.end)}\n${c.text}\n`).join('\n');
mkdirSync('out', {recursive: true});
writeFileSync('out/subtitles.srt', srt);
console.log(`Wrote out/subtitles.srt (${CUES.length} cues)`);
