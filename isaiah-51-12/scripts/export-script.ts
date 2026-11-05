/* Regenerates VOICEOVER_SCRIPT.md from src/timeline.ts so the script never drifts from the edit. */
import {writeFileSync} from 'node:fs';
import {CUES, SCENES} from '../src/timeline';

const tc = (s: number) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${(s % 60).toFixed(1).padStart(4, '0')}`;
let md = `# Voiceover Script — Isaiah 51:12 "Who Are You Afraid Of?"\n\n`;
md += `Generated from \`src/timeline.ts\` (\`npm run script\`). Each line is a separate clip: \`public/vo/<id>.mp3\`.\n`;
md += `Record each clip so the spoken words fit inside its window; leave ~0.1 s of room tone at the head. Clips may be shorter than the window, never longer.\n\n`;
md += `**Narrator:** deep, warm male voice, late 40s. Natural and conversational — a friend who has been through it, not a preacher. Close mic, little room. Never theatrical.\n\n`;
for (const s of SCENES) {
	md += `## Scene ${s.number} — ${s.title} (${tc(s.start)}–${tc(s.end)})\n\n| ID | In | Out | Max length | Line | Direction |\n|---|---|---|---|---|---|\n`;
	for (const c of CUES.filter((c) => c.scene === s.number)) {
		md += `| ${c.id} | ${tc(c.start)} | ${tc(c.end)} | ${(c.end - c.start).toFixed(1)} s | ${c.text}${c.subtitle ? '' : ' *(on-screen scripture, no subtitle)*'} | ${c.direction} |\n`;
	}
	md += '\n';
}
writeFileSync('VOICEOVER_SCRIPT.md', md);
console.log('Wrote VOICEOVER_SCRIPT.md');
