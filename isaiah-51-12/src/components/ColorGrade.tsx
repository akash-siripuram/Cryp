import React from 'react';
import {AbsoluteFill, interpolate, interpolateColors, useCurrentFrame} from 'remotion';
import {FPS} from '../timeline';

/**
 * Film-wide grade: cold desaturated blue → tense mid-tones → golden sunrise.
 * Keyframes in seconds. Applied identically to every shot so the film stays consistent.
 */
const T = [0, 12, 35, 45, 55, 62, 85, 105, 120];
const SATURATION = [0.55, 0.6, 0.62, 0.7, 0.85, 1.0, 1.05, 1.05, 1.08];
const BRIGHTNESS = [0.82, 0.86, 0.88, 0.92, 0.98, 1.02, 1.03, 1.04, 1.05];
const CONTRAST = [1.12, 1.1, 1.1, 1.08, 1.05, 1.04, 1.03, 1.04, 1.05];
const TINT = ['#12305e', '#163056', '#1d2c48', '#3a3a3a', '#7a5a2e', '#b07a2e', '#c08a3c', '#c48a3a', '#d0903a'];
const TINT_OPACITY = [0.38, 0.34, 0.3, 0.18, 0.18, 0.22, 0.2, 0.2, 0.24];

export const useGrade = () => {
	const t = useCurrentFrame() / FPS;
	const o = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
	return {
		filter: `saturate(${interpolate(t, T, SATURATION, o)}) brightness(${interpolate(t, T, BRIGHTNESS, o)}) contrast(${interpolate(t, T, CONTRAST, o)})`,
		tint: interpolateColors(t, T, TINT),
		tintOpacity: interpolate(t, T, TINT_OPACITY, o),
	};
};

export const GradeTint: React.FC = () => {
	const {tint, tintOpacity} = useGrade();
	return (
		<>
			<AbsoluteFill style={{backgroundColor: tint, opacity: tintOpacity, mixBlendMode: 'soft-light'}} />
			{/* Lens vignette */}
			<AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 45%, rgba(0,0,0,0.55) 100%)'}} />
		</>
	);
};
