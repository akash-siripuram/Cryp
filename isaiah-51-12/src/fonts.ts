import {loadFont as loadCormorant} from '@remotion/google-fonts/CormorantGaramond';
import {loadFont as loadInter} from '@remotion/google-fonts/Inter';

export const serif = loadCormorant('normal', {weights: ['300', '400', '500'], subsets: ['latin']}).fontFamily;
export const serifItalic = loadCormorant('italic', {weights: ['300', '400'], subsets: ['latin']}).fontFamily;
export const sans = loadInter('normal', {weights: ['300', '400', '500', '600'], subsets: ['latin']}).fontFamily;
