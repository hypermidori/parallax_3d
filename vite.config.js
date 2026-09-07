import {defineConfig} from 'vite';
export default defineConfig({build:{rollupOptions:{input:{game:'index.html',enemyLab:'enemy-lab.html'},output:{manualChunks:{three:['three']}}}}});
