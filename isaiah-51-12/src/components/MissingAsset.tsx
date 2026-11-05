import React from 'react';
import {AbsoluteFill} from 'remotion';
import {sans} from '../fonts';

/** Clearly labeled slate shown when a footage file has not been generated yet. */
export const MissingAsset: React.FC<{file: string; label: string}> = ({file, label}) => (
	<AbsoluteFill
		style={{
			background: 'radial-gradient(ellipse at center, #1c2230 0%, #07090d 75%)',
			justifyContent: 'center',
			alignItems: 'center',
			fontFamily: sans,
			color: 'rgba(255,255,255,0.75)',
			textAlign: 'center',
		}}
	>
		<div style={{fontSize: 22, letterSpacing: 6, opacity: 0.55, marginBottom: 18}}>FOOTAGE NOT YET GENERATED</div>
		<div style={{fontSize: 40, fontWeight: 500}}>{label}</div>
		<div style={{fontSize: 24, marginTop: 14, opacity: 0.6, fontFamily: 'monospace'}}>public/{file}</div>
		<div style={{fontSize: 20, marginTop: 10, opacity: 0.45}}>See PRODUCTION_WORKFLOW.md for the generation prompt</div>
	</AbsoluteFill>
);
