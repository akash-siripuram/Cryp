import React from 'react';
import {AbsoluteFill} from 'remotion';

/** 2.39:1 anamorphic bars inside the 16:9 frame (1920×803 picture area). */
export const BAR = 138;
export const Letterbox: React.FC = () => (
	<AbsoluteFill style={{pointerEvents: 'none'}}>
		<div style={{position: 'absolute', top: 0, left: 0, right: 0, height: BAR, background: 'black'}} />
		<div style={{position: 'absolute', bottom: 0, left: 0, right: 0, height: BAR, background: 'black'}} />
	</AbsoluteFill>
);
