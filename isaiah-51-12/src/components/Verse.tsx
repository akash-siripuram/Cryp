import React from 'react';
import {AbsoluteFill, Easing, interpolate} from 'remotion';
import {useGlobalFrame} from '../sceneTime';
import {sans, serif} from '../fonts';
import {VERSE, f} from '../timeline';

/** Phrase-by-phrase scripture reveal, timed to vo16/vo17. Uses absolute film frames. */
const Phrase: React.FC<{text: string; start: number; end: number; size: number; style?: React.CSSProperties; font?: string}> = ({text, start, end, size, style, font = serif}) => {
	const frame = useGlobalFrame();
	const s = f(start);
	const e = f(end);
	if (frame < s || frame >= e) return null;
	const words = text.split(' ');
	const out = interpolate(frame, [e - 20, e], [1, 0], {extrapolateLeft: 'clamp'});
	return (
		<div style={{fontFamily: font, fontSize: size, opacity: out, textWrap: 'balance', ...style} as React.CSSProperties}>
			{words.map((w, i) => {
				const p = interpolate(frame, [s + i * 5, s + i * 5 + 24], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
				return <span key={i} style={{display: 'inline-block', marginRight: '0.25em', opacity: p, filter: `blur(${(1 - p) * 6}px)`, transform: `translateY(${(1 - p) * 8}px)`}}>{w}</span>;
			})}
		</div>
	);
};

export const Verse: React.FC = () => {
	const frame = useGlobalFrame();
	// Line 1 eases upward when line 2 arrives.
	const lift = interpolate(frame, [f(VERSE.line2.start) - 10, f(VERSE.line2.start) + 20], [0, -70], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic)});
	const scrim = interpolate(frame, [f(VERSE.line1.start) - 15, f(VERSE.line1.start) + 15, f(VERSE.line1.end) - 15, f(VERSE.line1.end)], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	return (
		<AbsoluteFill>
			<AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(10,6,0,0.55) 0%, rgba(10,6,0,0.15) 70%)', opacity: scrim}} />
			<AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', textAlign: 'center', color: '#fff6e6', textShadow: '0 2px 24px rgba(40,20,0,0.75)', padding: '0 260px'}}>
				<div style={{transform: `translateY(${lift}px)`}}>
					<Phrase {...VERSE.line1} size={70} style={{fontWeight: 400}} />
				</div>
				<div style={{marginTop: 10}}>
					<Phrase {...VERSE.line2} size={52} style={{fontWeight: 300, lineHeight: 1.3}} />
				</div>
				<div style={{marginTop: 40}}>
					<Phrase {...VERSE.reference} size={24} font={sans} style={{letterSpacing: 9, fontWeight: 500, opacity: 0.85}} />
				</div>
			</AbsoluteFill>
		</AbsoluteFill>
	);
};
