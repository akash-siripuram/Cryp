import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {sans} from '../fonts';
import {CUES, f} from '../timeline';
import {BAR} from './Letterbox';

/** Word-by-word subtitles, synced to the narrator clips. Exactly one cue can be active at a time (verified). */
export const Subtitles: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const cue = CUES.find((c) => c.subtitle && frame >= f(c.start) && frame < f(c.end) + 6);
	if (!cue) return null;

	const start = f(cue.start);
	const end = f(cue.end);
	const words = cue.text.split(' ');
	const perWord = (end - start) * 0.7 / words.length;
	const out = interpolate(frame, [end - 2, end + 6], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

	return (
		<AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', paddingBottom: BAR + 46, opacity: out}}>
			<div style={{maxWidth: 1350, textAlign: 'center', fontFamily: sans, fontWeight: 400, fontSize: 40, lineHeight: 1.35, color: 'rgba(255,255,255,0.94)', textShadow: '0 2px 18px rgba(0,0,0,0.85), 0 0 2px rgba(0,0,0,0.9)', letterSpacing: 0.3}}>
				{words.map((w, i) => {
					const s = spring({frame: frame - start - i * perWord, fps, config: {damping: 200, mass: 0.6}});
					return (
						<span key={i} style={{display: 'inline-block', marginRight: '0.28em', opacity: s, transform: `translateY(${(1 - s) * 10}px)`, filter: `blur(${(1 - s) * 4}px)`}}>
							{w}
						</span>
					);
				})}
			</div>
		</AbsoluteFill>
	);
};
