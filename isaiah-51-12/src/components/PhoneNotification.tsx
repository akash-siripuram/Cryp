import React from 'react';
import {AbsoluteFill, interpolate, spring, useVideoConfig} from 'remotion';
import {useGlobalFrame} from '../sceneTime';
import {sans} from '../fonts';
import {PHONE_MESSAGES, f} from '../timeline';

/**
 * Crisp lock-screen notification composited over the phone-insert footage
 * (AI video models cannot render legible text reliably). Positioned where the
 * phone screen sits in s1_02 / s6_01 — adjust `anchor` if your footage differs.
 */
export const PhoneNotification: React.FC<{id: 'night' | 'morning'; anchor?: {x: number; y: number; scale: number}}> = ({id, anchor = {x: 960, y: 470, scale: 1}}) => {
	const frame = useGlobalFrame();
	const {fps} = useVideoConfig();
	const m = PHONE_MESSAGES.find((p) => p.id === id)!;
	const start = f(m.start);
	const end = f(m.end);
	if (frame < start || frame >= end) return null;

	const enter = spring({frame: frame - start, fps, config: {damping: 18, stiffness: 120}});
	const exit = interpolate(frame, [end - 10, end], [1, 0], {extrapolateLeft: 'clamp'});
	const night = id === 'night';

	return (
		<AbsoluteFill style={{pointerEvents: 'none'}}>
			<div
				style={{
					position: 'absolute', left: anchor.x - 330, top: anchor.y - 70, width: 660,
					transform: `scale(${anchor.scale}) translateY(${(1 - enter) * -30}px)`, opacity: enter * exit,
					padding: '22px 26px', borderRadius: 28, fontFamily: sans,
					background: night ? 'rgba(40,44,54,0.78)' : 'rgba(245,240,232,0.82)',
					color: night ? 'white' : '#1d1d1f', backdropFilter: 'blur(20px)',
					boxShadow: night ? '0 0 80px rgba(120,160,255,0.25)' : '0 10px 40px rgba(0,0,0,0.2)',
				}}
			>
				<div style={{display: 'flex', justifyContent: 'space-between', fontSize: 20, opacity: 0.65, marginBottom: 8}}>
					<span>MESSAGES</span>
					<span>{m.time}</span>
				</div>
				<div style={{fontSize: 27, fontWeight: 600}}>{m.sender}</div>
				<div style={{fontSize: 27, fontWeight: 400, marginTop: 4}}>{m.text}</div>
			</div>
		</AbsoluteFill>
	);
};
