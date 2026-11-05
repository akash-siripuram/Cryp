import React from 'react';
import {AbsoluteFill} from 'remotion';
import {GradeTint, useGrade} from './components/ColorGrade';
import {FilmGrain} from './components/FilmGrain';
import {Letterbox} from './components/Letterbox';
import {Soundtrack} from './components/Soundtrack';
import {Subtitles} from './components/Subtitles';
import {Scene1Hook, Scene2FearOfPeople, Scene3Realization, Scene4GodSpeaks, Scene5Scripture, Scene6FinalImpact} from './scenes/Scenes';

/** Master composition: picture (graded) → grain → letterbox → subtitles, plus the full soundtrack. */
export const Film: React.FC = () => {
	const {filter} = useGrade();
	return (
		<AbsoluteFill style={{backgroundColor: 'black'}}>
			<AbsoluteFill style={{filter}}>
				<Scene1Hook />
				<Scene2FearOfPeople />
				<Scene3Realization />
				<Scene4GodSpeaks />
				<Scene5Scripture />
				<Scene6FinalImpact />
				<GradeTint />
			</AbsoluteFill>
			<FilmGrain />
			<Letterbox />
			<Subtitles />
			<Soundtrack />
		</AbsoluteFill>
	);
};
