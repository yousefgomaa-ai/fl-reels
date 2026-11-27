import {defineConfig} from 'vite';
import mc from '@motion-canvas/vite-plugin';
const motionCanvas = (mc as any).default ?? mc;
export default defineConfig({plugins: [motionCanvas()], server: {port: 9000, host: '127.0.0.1'}});
