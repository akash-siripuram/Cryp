import React from 'react';
import {AbsoluteFill, interpolate} from 'remotion';
import {PhoneNotification} from '../components/PhoneNotification';
import {ShotLayer} from '../components/ShotLayer';
import {EndCard, HookTitle} from '../components/TitleCard';
import {Verse} from '../components/Verse';
import {At, SceneSequence, useGlobalFrame} from '../sceneTime';
import {SHOTS, TITLES, f} from '../timeline';

const Shots: React.FC<{scene: number}> = ({scene}) => (
	<>
		{SHOTS.filter((s) => s.scene === scene).map((s) => (
			<ShotLayer key={s.id} shot={s} />
		))}
	</>
);

/** 0–12s. Dark room → phone lights up → anxious face → eyes → black → title. */
export const Scene1Hook: React.FC = () => {
	const frame = useGlobalFrame();
	// The room sinks into near-black on the eyes shot before the title.
	const dim = interpolate(frame, [f(8.9), f(10)], [0, 0.92], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	return (
		<SceneSequence scene={1}>
			<Shots scene={1} />
			<AbsoluteFill style={{backgroundColor: 'black', opacity: dim}} />
			<PhoneNotification id="night" />
			<At start={TITLES.hook.start} end={TITLES.hook.end} name="Title: WHO ARE YOU AFRAID OF?">
				<HookTitle durationInFrames={f(TITLES.hook.end - TITLES.hook.start)} />
			</At>
		</SceneSequence>
	);
};

/** 12–35s. Office criticism, bedroom messages, mirror. */
export const Scene2FearOfPeople: React.FC = () => (
	<SceneSequence scene={2}>
		<Shots scene={2} />
	</SceneSequence>
);

/** 35–55s. Slow-motion city, then grass that withers. */
export const Scene3Realization: React.FC = () => (
	<SceneSequence scene={3}>
		<Shots scene={3} />
	</SceneSequence>
);

/** 55–85s. Sunrise through clouds, the man on the hill. God's presence through light only. */
export const Scene4GodSpeaks: React.FC = () => {
	const frame = useGlobalFrame();
	// Gentle warm bloom as light breaks through (restrained — no glow effects).
	const bloom = interpolate(frame, [f(56), f(62), f(83), f(85)], [0, 0.16, 0.12, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	return (
		<SceneSequence scene={4}>
			<Shots scene={4} />
			<AbsoluteFill style={{background: 'radial-gradient(ellipse at 70% 20%, rgba(255,200,120,1) 0%, rgba(255,200,120,0) 60%)', opacity: bloom, mixBlendMode: 'screen'}} />
		</SceneSequence>
	);
};

/** 85–105s. Open Bible in morning light; the verse appears phrase by phrase. */
export const Scene5Scripture: React.FC = () => (
	<SceneSequence scene={5}>
		<Shots scene={5} />
		<Verse />
	</SceneSequence>
);

/** 105–120s. Morning. New message, a breath, phone down, walk into the sunrise. */
export const Scene6FinalImpact: React.FC = () => (
	<SceneSequence scene={6}>
		<Shots scene={6} />
		<PhoneNotification id="morning" anchor={{x: 960, y: 500, scale: 0.95}} />
		<At start={TITLES.end.start} end={TITLES.end.end} name="End card">
			<EndCard durationInFrames={f(TITLES.end.end - TITLES.end.start)} />
		</At>
	</SceneSequence>
);
