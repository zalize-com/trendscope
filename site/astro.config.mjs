// @ts-check
import { defineConfig } from 'astro/config';

import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
export default defineConfig({
  // 'file' keeps the legacy URL shape: src/pages/x.astro emits x.html,
  // not x/index.html — sitemap/links/feed/OPML stay byte-identical.
  build: {
    format: 'file'
  },
  vite: {
    plugins: [tailwindcss()]
  }
});
