import React from 'react';
import {AbsoluteFill, Easing, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {hasAsset} from '../assets';
import {Move, Shot, f} from '../timeline';
import {MissingAsset} from './MissingAsset';
import {useSceneOffset} from '../sceneTime';

const camera = (move: Move, p: number): string => {
	const e = Easing.inOut(Easing.sin)(p);
	switch (move) {
		case 'push-in':
			return `scale(${interpolate(e, [0, 1], [1.04, 1.12])})`;
		case 'pull-out':
			return `scale(${interpolate(e, [0, 1], [1.13, 1.04])})`;
		case 'drift-left':
			return `scale(1.1) translateX(${interpolate(e, [0, 1], [2.2, -2.2])}%)`;
		case 'drift-right':
			return `scale(1.1) translateX(${interpolate(e, [0, 1], [-2.2, 2.2])}%)`;
		case 'rise':
			return `scale(1.1) translateY(${interpolate(e, [0, 1], [2.5, -2.5])}%)`;
		default:
			return 'scale(1.04)';
	}
};

const ShotBody: React.FC<{shot: Shot; total: number; dissolveFrames: number}> = ({shot, total, dissolveFrames}) => {
	const frame = useCurrentFrame();
	const opacity = dissolveFrames > 0
		? interpolate(frame, [0, dissolveFrames], [0, 1], {extrapolateRight: 'clamp', easing: Easing.inOut(Easing.quad)})
		: 1;
	const progress = frame / Math.max(1, total - 1);
	const exists = hasAsset(shot.file);

	return (
		<AbsoluteFill style={{opacity, overflow: 'hidden', backgroundColor: 'black'}}>
			<AbsoluteFill style={{transform: camera(shot.move, progress), transformOrigin: '50% 50%'}}>
				{exists ? (
					<OffthreadVideo
						src={staticFile(shot.file)}
						muted
						startFrom={f(shot.trimStart ?? 0)}
						playbackRate={shot.playbackRate ?? 1}
						style={{width: '100%', height: '100%', objectFit: 'cover'}}
					/>
				) : (
					<MissingAsset file={shot.file} label={shot.id.toUpperCase()} />
				)}
			</AbsoluteFill>
		</AbsoluteFill>
	);
};

/** Places a shot on the master timeline. A dissolve starts early so it overlaps the previous shot. */
export const ShotLayer: React.FC<{shot: Shot}> = ({shot}) => {
	const offset = useSceneOffset();
	const dissolveFrames = f(shot.dissolve);
	const absFrom = f(shot.start) - dissolveFrames;
	const total = f(shot.end) - absFrom;
	const from = absFrom - offset;
	return (
		<Sequence from={from} durationInFrames={total} name={`${shot.id} ${shot.file}`}>
			<ShotBody shot={shot} total={total} dissolveFrames={dissolveFrames} />
		</Sequence>
	);
};
