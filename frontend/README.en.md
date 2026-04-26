# Searching Games

React interface for demonstrating and comparing information retrieval models over a game catalog. The project was created in Lovable and uses Vite, Tailwind, shadcn/ui, and mocked data to simulate the future backend integration.

Leia em portugues: [README.md](./README.md)

## Requirements

- Node.js 18 or newer.
- npm, which is installed with Node.

You do not need Bun to run this project. The `bun.lockb` file came from Lovable, but the repository also has `package-lock.json`, so the Node/npm workflow works normally.

## Running Locally

1. Install dependencies:

```bash
npm install
```

2. Start the development server:

```bash
npm run dev
```

3. Open the URL shown in the terminal. With the current Vite configuration, the default is:

```text
http://localhost:8080
```

## Available Scripts

- `npm run dev`: starts Vite in development mode.
- `npm run build`: creates the production build in `dist/`.
- `npm run build:dev`: builds using `development` mode.
- `npm run preview`: serves the generated build locally.
- `npm run lint`: runs ESLint.
- `npm run test`: runs tests with Vitest.
- `npm run test:watch`: runs Vitest in watch mode.

## Language and Theme

The interface can switch between English and Portuguese from the language button in the header. The choice is persisted in `localStorage`, following the same idea used by the light/dark theme toggle.

The light/dark theme toggle remains available in the header.

## Mocked Data and Future Integration

The game data and metrics are intentionally still mocked:

- Games: `src/lib/mockData.ts`
- Models and metrics: `src/lib/models.ts`
- Search simulation: `src/lib/searchService.ts`
- Types that can be shared with a backend: `src/lib/types.ts`

Do not remove these mocks before the backend is ready. `src/lib/searchService.ts` already acts as the seam that can later be replaced with a `fetch` call to an API, for example FastAPI + Elasticsearch.

## Main Structure

- `src/components/LanguageProvider.tsx`: translated strings, language state, and persistence.
- `src/components/LanguageToggle.tsx`: EN/PT button.
- `src/components/ThemeProvider.tsx`: light/dark theme state.
- `src/components/sections/`: landing page sections.
- `src/components/playground/`: search form and result cards.
- `src/pages/`: pages routed by React Router.
