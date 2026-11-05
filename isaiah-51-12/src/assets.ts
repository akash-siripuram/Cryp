import {getStaticFiles} from 'remotion';

let cache: Set<string> | null = null;

/** True when /public contains the file. Missing files are shown as a labeled slate, never silently replaced. */
export const hasAsset = (path: string): boolean => {
	if (!cache) {
		cache = new Set(getStaticFiles().map((f) => f.name));
	}
	return cache.has(path);
};
