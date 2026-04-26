# Searching Games

Interface React para demonstrar e comparar modelos de recuperacao de informacao em um catalogo de jogos. O projeto nasceu no Lovable, usa Vite, Tailwind, shadcn/ui e dados mockados para simular a futura integracao com backend.

Read this in English: [README.en.md](./README.en.md)

## Requisitos

- Node.js 18 ou superior.
- npm, que ja vem junto com o Node.

Voce nao precisa instalar Bun para rodar este projeto. O arquivo `bun.lockb` veio do Lovable, mas o repositorio tambem possui `package-lock.json`, entao o fluxo com Node/npm funciona normalmente.

## Como rodar

1. Instale as dependencias:

```bash
npm install
```

2. Inicie o servidor de desenvolvimento:

```bash
npm run dev
```

3. Abra o endereco exibido no terminal. Pela configuracao atual do Vite, o padrao e:

```text
http://localhost:8080
```

## Scripts disponiveis

- `npm run dev`: inicia o Vite em modo desenvolvimento.
- `npm run build`: gera a versao de producao em `dist/`.
- `npm run build:dev`: gera build usando modo `development`.
- `npm run preview`: serve localmente o build gerado.
- `npm run lint`: executa o ESLint.
- `npm run test`: executa os testes com Vitest.
- `npm run test:watch`: executa o Vitest em modo watch.

## Idioma e tema

A interface permite alternar entre ingles e portugues pelo botao de idioma no header. A escolha fica salva no `localStorage`, da mesma forma que o tema claro/escuro.

O tema claro/escuro continua disponivel no header pelo botao de tema.

## Dados mockados e futura integracao

Os dados de jogos e metricas ainda sao mockados de proposito:

- Jogos: `src/lib/mockData.ts`
- Modelos e metricas: `src/lib/models.ts`
- Simulacao de busca: `src/lib/searchService.ts`
- Tipos compartilhaveis com backend: `src/lib/types.ts`

Nao remova esses mocks enquanto o backend nao estiver pronto. O arquivo `src/lib/searchService.ts` ja funciona como a borda que pode ser trocada depois por um `fetch` para uma API, por exemplo FastAPI + Elasticsearch.

## Estrutura principal

- `src/components/LanguageProvider.tsx`: textos traduzidos, estado de idioma e persistencia.
- `src/components/LanguageToggle.tsx`: botao EN/PT.
- `src/components/ThemeProvider.tsx`: estado de tema claro/escuro.
- `src/components/sections/`: secoes da landing page.
- `src/components/playground/`: formulario de busca e cards de resultado.
- `src/pages/`: paginas roteadas pelo React Router.
