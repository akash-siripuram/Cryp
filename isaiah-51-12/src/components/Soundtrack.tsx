import React from 'react';
import {Audio, Sequence, interpolate, staticFile} from 'remotion';
import {hasAsset} from '../assets';
import {CUES, DUCK, DUCK_RAMP, FPS, MUSIC_FILE, MUSIC_LEVELS, SFX, f} from '../timeline';

/** Music level at global frame, ducked under every narrator cue. */
const musicVolume = (frame: number) => {
	const t = frame / FPS;
	const base = interpolate(t, MUSIC_LEVELS.map((k) => k[0]), MUSIC_LEVELS.map((k) => k[1]), {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	let duck = 1;
	for (const c of CUES) {
		const d = interpolate(t, [c.start - DUCK_RAMP, c.start, c.end, c.end + DUCK_RAMP], [1, DUCK, DUCK, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
		duck = Math.min(duck, d);
	}
	return base * duck;
};

export const Soundtrack: React.FC = () => (
	<>
		{hasAsset(MUSIC_FILE) && <Audio src={staticFile(MUSIC_FILE)} volume={musicVolume} name="Score" />}

		{CUES.filter((c) => hasAsset(c.file)).map((c) => (
			<Sequence key={c.id} from={f(c.start)} durationInFrames={f(c.end - c.start) + f(1.5)} name={`VO ${c.id}`}>
				<Audio src={staticFile(c.file)} volume={1} />
			</Sequence>
		))}

		{SFX.filter((s) => hasAsset(s.file)).map((s) => {
			const len = f(s.end - s.start);
			const vol = (fr: number) =>
				interpolate(fr, [0, Math.max(1, f(s.fadeIn)), len - Math.max(1, f(s.fadeOut)), len], [s.fadeIn ? 0 : s.volume, s.volume, s.volume, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
			return (
				<Sequence key={s.id} from={f(s.start)} durationInFrames={len} name={`SFX ${s.id}`}>
					<Audio src={staticFile(s.file)} volume={vol} loop={s.loop} />
				</Sequence>
			);
		})}
	</>
);
