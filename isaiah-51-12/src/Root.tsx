import React from 'react';
import {Composition} from 'remotion';
import {Film} from './Film';
import {DURATION_FRAMES, FPS, HEIGHT, WIDTH} from './timeline';
import './fonts';

export const RemotionRoot: React.FC = () => (
	<Composition id="WhoAreYouAfraidOf" component={Film} durationInFrames={DURATION_FRAMES} fps={FPS} width={WIDTH} height={HEIGHT} />
);
