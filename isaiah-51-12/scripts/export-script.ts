/* Regenerates VOICEOVER_SCRIPT.md (ElevenLabs-ready) from src/timeline.ts so the script never drifts from the edit. */
import {writeFileSync} from 'node:fs';
import {CUES, SCENES} from '../src/timeline';

const tc = (s: number) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${(s % 60).toFixed(1).padStart(4, '0')}`;

/** ElevenLabs text: ellipses become explicit pauses (Multilingual v2 / Turbo / Flash honour <break>). */
const tts = (text: string) =>
	text
		.replace(/^…/, '')
		.replace(/…$/, '')
		.replace(/…\s*/g, ' <break time="0.8s" /> ')
		.replace(/\.\s+(?=[A-Z])/g, '. <break time="0.5s" /> ')
		.trim();

let md = `# Narration Script — "Who Are You Afraid Of?" (Isaiah 51:12)

Generated from \`src/timeline.ts\` by \`npm run script\`. **Do not edit by hand**; change the timeline instead.

## How to record it (ElevenLabs)

- **One generation per line**, 22 in total. Each line becomes one file: \`public/vo/<ID>.mp3\`. Separate files keep every line frame-accurate with the picture, whatever the take length.
- **Model:** *Eleven Multilingual v2*. It is the most natural for long-form narration and honours \`<break time="…" />\` pauses. If you use *Eleven v3* instead, delete the \`<break>\` tags and put the bracketed **v3 tag** at the start of the line.
- **Voice:** a deep, warm, unhurried male narrator in his 40s–50s with a natural American or neutral accent. In the Voice Library, filter *Narrative & Story / Male / Middle-aged / Deep*. **"Brian"** (premade: deep, resonant, comforting) is a strong default. Before generating everything, audition 3 voices on line vo06 and line vo16.
- **Settings (v2):** Stability 40 %, Similarity 80 %, Style exaggeration 15 %, Speaker boost on, Speed 0.90.
- **Takes:** generate 3 takes of each line and keep the most human-sounding one (breath, slight imperfection, no sing-song).
- **Export:** MP3 44.1 kHz 192 kbps or higher. Trim leading silence to ≈ 0.1 s.
- **Rule:** the clip **must not be longer than "Max length"**. If it is, raise Speed to 0.95 or shorten a \`<break>\`. Shorter is fine. \`npm run assets\` checks this.
- **Same voice and same settings for all 22 lines.** Write them down.

**Performance note for the whole film:** speak to *one* person who is lying awake afraid. A friend who has been there, not a preacher. Low, close, intimate at the start; warmer and steadier from "And then… God speaks"; reverent and very slow for the scripture; calm, settled courage at the end. Never theatrical.

`;
for (const s of SCENES) {
	const cues = CUES.filter((c) => c.scene === s.number);
	md += `## Scene ${s.number} — ${s.title} (${tc(s.start)}–${tc(s.end)})\n\n`;
	for (const c of cues) {
		md += `### ${c.id} · ${tc(c.start)} → ${tc(c.end)} · max length ${(c.end - c.start + 0.3).toFixed(1)} s · file \`public/vo/${c.id}.mp3\`\n\n`;
		md += `- **Line:** ${c.text}${c.subtitle ? '' : ' *(shown on screen as scripture)*'}\n`;
		md += `- **Delivery:** ${c.direction}\n`;
		md += `- **v3 tag:** ${c.scene <= 2 ? '[softly]' : c.scene === 3 ? '[thoughtful]' : c.scene === 5 ? '[reverent, slow]' : c.scene === 4 ? '[warm]' : '[calm, hopeful]'}\n\n`;
		md += '```text\n' + tts(c.text) + '\n```\n\n';
	}
}
md += `## Full read-through (for auditioning voices and checking flow; don't use it in the film)\n\n\`\`\`text\n${CUES.map((c) => tts(c.text)).join(' <break time="1.2s" />\n')}\n\`\`\`\n`;
writeFileSync('VOICEOVER_SCRIPT.md', md);
console.log('Wrote VOICEOVER_SCRIPT.md');
