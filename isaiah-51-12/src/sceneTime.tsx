import React, {createContext, useContext} from 'react';
import {Sequence, useCurrentFrame} from 'remotion';
import {SCENES, f} from './timeline';

/** Frames before a scene's start where its first dissolve begins. */
export const LEAD_IN = f(2);

const OffsetContext = createContext(0);

/** Absolute (film) frame, regardless of which scene Sequence we are inside. */
export const useGlobalFrame = () => useCurrentFrame() + useContext(OffsetContext);
export const useSceneOffset = () => useContext(OffsetContext);

/** Wraps one scene in a Sequence; children use absolute timeline values via useSceneOffset/useGlobalFrame. */
export const SceneSequence: React.FC<{scene: number; children: React.ReactNode}> = ({scene, children}) => {
	const s = SCENES.find((x) => x.number === scene)!;
	const from = Math.max(0, f(s.start) - LEAD_IN);
	return (
		<Sequence from={from} durationInFrames={f(s.end) - from} name={`Scene ${s.number} — ${s.title}`}>
			<OffsetContext.Provider value={from}>{children}</OffsetContext.Provider>
		</Sequence>
	);
};

/** A Sequence placed at absolute film seconds, from inside a scene. */
export const At: React.FC<{start: number; end: number; name?: string; children: React.ReactNode}> = ({start, end, name, children}) => {
	const off = useSceneOffset();
	return (
		<Sequence from={f(start) - off} durationInFrames={f(end) - f(start)} name={name}>
			{children}
		</Sequence>
	);
};
