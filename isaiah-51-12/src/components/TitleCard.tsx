import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from 'remotion';
import {sans, serif, serifItalic} from '../fonts';

const fade = (frame: number, a: number, b: number) =>
	interpolate(frame, [a, b], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});

/** Scene 1 hook title on near-black. Frame is local to its Sequence. */
export const HookTitle: React.FC<{durationInFrames: number}> = ({durationInFrames}) => {
	const frame = useCurrentFrame();
	const inn = fade(frame, 4, 28);
	const out = interpolate(frame, [durationInFrames - 10, durationInFrames], [1, 0], {extrapolateLeft: 'clamp'});
	return (
		<AbsoluteFill style={{backgroundColor: '#020306', justifyContent: 'center', alignItems: 'center'}}>
			<div style={{fontFamily: sans, fontWeight: 300, fontSize: 64, letterSpacing: interpolate(inn, [0, 1], [26, 16]), color: 'rgba(225,232,245,0.92)', opacity: inn * out, filter: `blur(${(1 - inn) * 8}px)`}}>
				WHO ARE YOU AFRAID OF?
			</div>
		</AbsoluteFill>
	);
};

/** Final card over the sunrise walk, then fade to black. */
export const EndCard: React.FC<{durationInFrames: number}> = ({durationInFrames}) => {
	const frame = useCurrentFrame();
	const a = fade(frame, 0, 24);
	const b = fade(frame, 18, 42);
	const c = fade(frame, 30, 54);
	const black = interpolate(frame, [durationInFrames - 26, durationInFrames - 2], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	return (
		<AbsoluteFill>
			<AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(0,0,0,0.35), rgba(0,0,0,0.05) 70%)', opacity: a}} />
			<AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', color: '#fff8ec', textShadow: '0 2px 30px rgba(60,30,0,0.6)'}}>
				<div style={{fontFamily: sans, fontWeight: 300, fontSize: 58, letterSpacing: 14, opacity: a, transform: `translateY(${(1 - a) * 14}px)`}}>WHO ARE YOU AFRAID OF?</div>
				<div style={{fontFamily: sans, fontWeight: 500, fontSize: 26, letterSpacing: 10, marginTop: 30, opacity: b}}>ISAIAH 51:12</div>
				<div style={{fontFamily: serifItalic, fontSize: 46, marginTop: 22, opacity: c}}>God is your comfort.</div>
			</AbsoluteFill>
			<AbsoluteFill style={{backgroundColor: 'black', opacity: black}} />
		</AbsoluteFill>
	);
};

export {serif};
