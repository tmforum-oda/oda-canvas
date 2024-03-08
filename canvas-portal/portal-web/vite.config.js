// import { fileURLToPath, URL } from 'node:url'
import path from 'path'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import styleImport from 'vite-plugin-style-import';
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers';
import { createSvgIconsPlugin } from 'vite-plugin-svg-icons';
import monacoEditorPlugin from 'vite-plugin-monaco-editor';
const __dirname = path.resolve();
// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const config = loadEnv(mode, './');
  for (const [key, value] of Object.entries(config)) {
    console.log(`${key}:${value}`);
  }
  return {
    base: '',
    build: {
      outDir: '../portal-service/src/main/resources/static'
    },
    plugins: [
      vue(),
      monacoEditorPlugin({ languageWorkers: ['editorWorkerService', 'css', 'html', 'json', 'typescript'] }),
      AutoImport({
        resolvers: [ElementPlusResolver()],
      }),
      Components({
        resolvers: [ElementPlusResolver()],
      }),
      styleImport({
        libs: [
          {
            libraryName: 'vant',
            esModule: true,
            resolveStyle: (name) => `vant/es/${name}/style`,
          },
        ],
      }),
      createSvgIconsPlugin({
        // Specify the icon folder to be cached
        iconDirs: [path.resolve(process.cwd(), 'src/assets/icons')],
        // Specify symbolId format
        symbolId: 'icon-[dir]-[name]',
      })
    ],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src')
      }
    },
    server: {
      port: "8888",
      host: "localhost",
      open: false,
      proxy: {
        '/api': {
          target: config.VITE_BASE_URL,
          changeOrigin: true,
          rewrite: (p) => p.replace(/^\/api\//, ''),
          secure: false,
          https: false
        },
      }
    },
  }
});
