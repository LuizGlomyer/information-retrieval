import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { ModelId } from "@/lib/types";

export type Language = "en" | "pt";

interface LanguageContextValue {
  language: Language;
  setLanguage: (language: Language) => void;
  toggleLanguage: () => void;
  t: typeof translations.en;
}

const STORAGE_KEY = "ir-language";
const LanguageContext = createContext<LanguageContextValue | undefined>(undefined);

const getInitialLanguage = (): Language => {
  if (typeof window === "undefined") return "en";
  const stored = window.localStorage.getItem(STORAGE_KEY) as Language | null;
  return stored === "pt" || stored === "en" ? stored : "en";
};

export const translations = {
  en: {
    languageToggle: { label: "Switch language to Portuguese", shortLabel: "PT" },
    header: {
      nav: { pipeline: "Pipeline", models: "Models", metrics: "Metrics", playground: "Playground" },
      cta: "Try a query ->",
    },
    footer: {
      description:
        "An ongoing study of information retrieval techniques over a structured English-language game catalog.",
      backend: "Backend: FastAPI - Elasticsearch",
      frontend: "Frontend: React - Vite - Tailwind",
      copyright: "IR Lab - Vol. 01",
    },
    hero: {
      eyebrow: "Information Retrieval - Vol. 01",
      titlePrefix: "Searching",
      titleEmphasis: "games",
      titleSuffix: "across multiple algorithms.",
      lede:
        "A study in lexical and neural retrieval over a structured English-language game catalog. We index, weight, embed and rerank - then put each model on the same stand and let the metrics talk.",
      primaryCta: "Open the playground",
      secondaryCta: "Read the method",
      stats: {
        corpus: "Corpus",
        games: "games",
        indexedFields: "Indexed fields",
        rankingModels: "Ranking models",
        evaluationMetrics: "Evaluation metrics",
      },
    },
    pipeline: {
      heading: {
        eyebrow: "01 - Method",
        title: "Six steps from raw catalog to ranked answers",
        lede:
          "Each step is independently versioned and evaluated. The same preprocessing and the same filters power every ranker, so what we compare are the rankers themselves.",
      },
      steps: [
        {
          title: "Corpus ingestion",
          desc:
            "Game records normalized and indexed into Elasticsearch with a typed mapping (name, summary, genres, themes, platforms, ratings).",
          output: "232,595 documents - 11 fields",
        },
        {
          title: "Text preprocessing",
          desc:
            "Lowercasing, whitespace tokenization, English stopword pruning. Future work: lemmatization and named-entity tagging for franchises.",
          output: "Avg. 84 tokens / doc",
        },
        {
          title: "Lexical retrieval - BM25",
          desc:
            "Multi-match queries with optional field weights. Captures exact and morphological matches; serves as the strong baseline.",
          output: "Latency: ~120 ms",
        },
        {
          title: "Vector Space Model - VSM",
          desc:
            "Scripted Similarity vector space model based on TF-IDF term frequency and cosine similarity. It ranks documents using custom similarity scoring directly inside Elasticsearch.",
          output: "Latency: ~110 ms",
        },
        {
          title: "Neural reranking - BERT",
          desc:
            "Cross-encoder reads (query, document) jointly. Fine-tuned variant adapts to gaming vocabulary and editorial relevance labels.",
          output: "Latency: ~480 ms",
        },
        {
          title: "Evaluation harness",
          desc:
            "Each model is scored on the same labeled query set across nine IR metrics. Results are versioned per experiment.",
          output: "9 metrics - 4 models",
        },
      ],
    },
    models: {
      heading: {
        eyebrow: "02 - Models",
        title: "Four rankers, two families",
        lede:
          "Lexical models are fast, transparent and stubborn about vocabulary. Neural models are slower, opaque and forgiving. We ship both and let the queries decide.",
      },
      families: { lexical: "lexical", neural: "neural" },
      statuses: { stable: "stable", experimental: "experimental", planned: "planned" },
      copy: {
        bm25: {
          tagline: "Native lexical baseline",
          description:
            "Elasticsearch's native ranking. Term frequency, inverse document frequency and length normalization on each searchable field.",
          techniques: ["TF-IDF", "Length norm", "Multi-match"],
        },
        bm25_hybrid: {
          tagline: "Lexical & semantic search",
          description:
            "Combines lexical BM25 matching with dense vector embedding similarity for a rich, hybrid relevance ranking.",
          techniques: ["BM25", "BGE Embeddings", "Hybrid fusion"],
        },
        bert: {
          tagline: "Dense vector retrieval",
          description:
            "Dense retrieval using pre-trained BGE embeddings. Computes cosine similarity between query and document vectors.",
          techniques: ["BGE Embeddings", "Dense Vector", "Cosine similarity"],
        },
        svm: {
          tagline: "Vector Space Model",
          description:
            "Vector Space Model scoring based on TF-IDF term frequency and cosine similarity. Provides an alternative mathematical ranking perspective.",
          techniques: ["TF-IDF", "Cosine similarity", "Vector space"],
        },
      } satisfies Record<"bm25" | "bm25_hybrid" | "bert" | "svm", { tagline: string; description: string; techniques: string[] }>,
    },
    metrics: {
      heading: {
        eyebrow: "03 - Evaluation",
        title: "Side by side, on the same questions",
        lede:
          "Every model is evaluated on the same labeled query set. We report nine standard IR metrics - precision at k, recall, MAP, F1 and NDCG at three cutoffs.",
      },
      compareOn: "Compare on:",
      higherIsBetter: "higher is better",
      selectedMetricDescription: "Score per model on the selected metric.",
      allMetricsTitle: "All metrics, all models",
      profile: "profile",
      allMetricsDescription: "Each line is a model. Reads model strengths across the metric spectrum.",
      modelColumn: "Model",
      bestNote: "Best per column. All scores in [0, 1].",
      rankingMode: "Ranking Mode:",
      modeNormal: "Normal",
      modeRerank: "Rerank (Cross-Encoder)",
    },
    playground: {
      heading: {
        eyebrow: "04 - Playground",
        title: "Run a query. Watch the rankers disagree.",
        lede:
          "Type a search and see how each model ranks the catalog. Switch between viewing a single model in detail or comparing several side by side.",
      },
      defaultQuery: "super mario",
      suggestions: [
        "super mario",
        "combat that is mortal",
        "spartan warrior protagonist",
        "basketball with good movement",
        "zelda games",
        "zombie survival",
        "racing simulator",
        "space exploration",
        "world war",
        "cyberpunk rpg",
        "detective mystery",
        "medieval strategy",
        "anime fight",
        "coop puzzle",
        "soccer manager",
        "dungeon crawler",
        "hack and slash",
        "skate boarding",
        "psychological horror",
        "stealth assassin",
      ],
      placeholder: "e.g. super mario...",
      searchLabel: "Search query",
      search: "Search",
      try: "try:",
      viewMode: "View mode",
      single: "Single",
      compare: "Compare",
      model: "Model",
      modelsToCompare: "Models to compare",
      hits: "hits",
      milliseconds: "ms",
      noResults: "No results.",
      emptyTitle: "Ready when you are.",
      emptyDescription:
        "Hit search above, or pick one of the suggested queries to see how the rankers respond.",
      runDefault: "Run default query",
      rerankLabel: "Rerank with Cross-Encoder",
      metricsLabel: "Calculate IR Metrics",
      metricsHeader: "IR Evaluation Metrics",
      metricsUnavailable: "Metrics unavailable for this query",
    },
    resultCard: { coverAlt: "Cover art for", score: "score" },
    notFound: { message: "Oops! Page not found", home: "Return to Home" },
  },
  pt: {
    languageToggle: { label: "Mudar idioma para inglês", shortLabel: "EN" },
    header: {
      nav: { pipeline: "Pipeline", models: "Modelos", metrics: "Métricas", playground: "Playground" },
      cta: "Testar busca ->",
    },
    footer: {
      description:
        "Um estudo contínuo de técnicas de recuperação de informação em um catálogo estruturado de jogos em inglês.",
      backend: "Backend: FastAPI - Elasticsearch",
      frontend: "Frontend: React - Vite - Tailwind",
      copyright: "IR Lab - Vol. 01",
    },
    hero: {
      eyebrow: "Recuperação de Informação - Vol. 01",
      titlePrefix: "Buscando",
      titleEmphasis: "jogos",
      titleSuffix: "através de múltiplos algoritmos.",
      lede:
        "Um estudo de recuperação lexical e neural em um catálogo estruturado de jogos em inglês. Indexamos, ponderamos, geramos embeddings e aplicamos re-ranqueamento (rerank) - depois colocamos cada modelo na mesma bancada e deixamos as métricas falarem.",
      primaryCta: "Abrir o playground",
      secondaryCta: "Ler o método",
      stats: {
        corpus: "Corpus",
        games: "jogos",
        indexedFields: "Campos indexados",
        rankingModels: "Modelos de ranking",
        evaluationMetrics: "Métricas de avaliação",
      },
    },
    pipeline: {
      heading: {
        eyebrow: "01 - Método",
        title: "Seis etapas do catálogo bruto às respostas ranqueadas",
        lede:
          "Cada etapa é versionada e avaliada de forma independente. O mesmo pré-processamento e os mesmos filtros alimentam todos os rankers, então comparamos os rankers em si.",
      },
      steps: [
        {
          title: "Ingestão do corpus",
          desc:
            "Registros de jogos normalizados e indexados no Elasticsearch com um mapeamento tipado (nome, resumo, gêneros, temas, plataformas, avaliações).",
          output: "232.595 documentos - 11 campos"
        },
        {
          title: "Pré-processamento de texto",
          desc:
            "Lowercase, tokenização por espaços e remoção de stopwords em inglês. Trabalhos futuros: lematização e reconhecimento de entidades para franquias.",
          output: "Média de 84 tokens / doc",
        },
        {
          title: "Recuperação lexical - BM25",
          desc:
            "Consultas multi-match com pesos opcionais por campo. Captura correspondências exatas e morfológicas; serve como baseline forte.",
          output: "Latência: ~120 ms",
        },
        {
          title: "Modelo de Vetor Espacial - VSM",
          desc:
            "Ranqueamento baseado em frequência de termos TF-IDF e similaridade de cosseno (Vector Space Model). Executa uma similaridade roteirizada customizada diretamente no Elasticsearch.",
          output: "Latência: ~110 ms",
        },
        {
          title: "Re-ranking neural - BERT",
          desc:
            "O cross-encoder lê (consulta, documento) em conjunto. Utiliza o modelo BAAI/bge-reranker-base do Hugging Face para pontuar a relevância.",
          output: "Latência: ~480 ms",
        },
        {
          title: "Esteira de avaliação",
          desc:
            "Cada modelo é pontuado no mesmo conjunto de consultas rotuladas usando nove métricas de RI. Os resultados são versionados por experimento.",
          output: "9 métricas - 4 modelos",
        },
      ],
    },
    models: {
      heading: {
        eyebrow: "02 - Modelos",
        title: "Quatro rankers, duas famílias",
        lede:
          "Modelos lexicais são rápidos, transparentes e rígidos com vocabulário. Modelos neurais são mais lentos, opacos e tolerantes. Usamos os dois e deixamos as consultas decidirem.",
      },
      families: { lexical: "lexical", neural: "neural" },
      statuses: { stable: "estável", experimental: "experimental", planned: "planejado" },
      copy: {
        bm25: {
          tagline: "Baseline lexical nativo",
          description:
            "Ranking nativo do Elasticsearch. Frequência do termo, frequência inversa do documento e normalização de tamanho em cada campo pesquisável.",
          techniques: ["TF-IDF", "Normalização", "Multi-match"],
        },
        bm25_hybrid: {
          tagline: "Busca lexical e semântica",
          description:
            "Combina correspondência lexical BM25 com similaridade de embeddings de vetor denso para um ranqueamento híbrido robusto.",
          techniques: ["BM25", "BGE Embeddings", "Fusão híbrida"],
        },
        bert: {
          tagline: "Busca por vetor denso",
          description:
            "Recuperação densa usando embeddings BGE pré-treinados. Calcula similaridade de cosseno entre vetores da consulta e do documento.",
          techniques: ["BGE Embeddings", "Vetor Denso", "Similaridade de cosseno"],
        },
        svm: {
          tagline: "Modelo de Vetor Espacial",
          description:
            "Ranqueamento baseado em frequência de termos TF-IDF e similaridade de cosseno (Vector Space Model). Fornece uma perspectiva de ranqueamento alternativa.",
          techniques: ["TF-IDF", "Similaridade de cosseno", "Espaço vetorial"],
        },
      } satisfies Record<"bm25" | "bm25_hybrid" | "bert" | "svm", { tagline: string; description: string; techniques: string[] }>,
    },
    metrics: {
      heading: {
        eyebrow: "03 - Avaliação",
        title: "Lado a lado, nas mesmas perguntas",
        lede:
          "Cada modelo é avaliado no mesmo conjunto de consultas rotuladas. Reportamos nove métricas padrão de RI - precision at k, recall, MAP, F1 e NDCG em três cortes.",
      },
      compareOn: "Comparar por:",
      higherIsBetter: "maior é melhor",
      selectedMetricDescription: "Pontuação por modelo na métrica selecionada.",
      allMetricsTitle: "Todas as métricas, todos os modelos",
      profile: "perfil",
      allMetricsDescriptionNormal: "Cada linha é um modelo. Mostra os pontos fortes ao longo do espectro de métricas (ranqueamento base).",
      allMetricsDescriptionRerank: "Avaliado usando o Cross-Encoder BAAI/bge-reranker-base do Hugging Face para reordenar os primeiros candidatos.",
      modelColumn: "Modelo",
      bestNote: "Melhor por coluna. Todas as pontuações em [0, 1].",
      rankingMode: "Modo de Ranqueamento:",
      modeNormal: "Normal",
      modeRerank: "Rerank (Cross-Encoder)",
    },
    playground: {
      heading: {
        eyebrow: "04 - Playground",
        title: "Execute uma busca. Veja os rankers discordarem.",
        lede:
          "Digite uma busca e veja como cada modelo ranqueia o catálogo. Alterne entre ver um modelo em detalhe ou comparar vários lado a lado.",
      },
      defaultQuery: "super mario",
      suggestions: [
        "super mario",
        "combat that is mortal",
        "spartan warrior protagonist",
        "basketball with good movement",
        "zelda games",
        "zombie survival",
        "racing simulator",
        "space exploration",
        "world war",
        "cyberpunk rpg",
        "detective mystery",
        "medieval strategy",
        "anime fight",
        "coop puzzle",
        "soccer manager",
        "dungeon crawler",
        "hack and slash",
        "skate boarding",
        "psychological horror",
        "stealth assassin",
      ],
      placeholder: "ex.: super mario...",
      searchLabel: "Consulta de busca",
      search: "Buscar",
      try: "teste:",
      viewMode: "Modo de visualização",
      single: "Único",
      compare: "Comparar",
      model: "Modelo",
      modelsToCompare: "Modelos para comparar",
      hits: "resultados",
      milliseconds: "ms",
      noResults: "Sem resultados.",
      emptyTitle: "Pronto quando você estiver.",
      emptyDescription:
        "Busque acima ou escolha uma consulta sugerida para ver como os rankers respondem.",
      runDefault: "Executar busca padrão",
      rerankLabel: "Re-ranquear com Cross-Encoder",
      metricsLabel: "Calcular Métricas de RI",
      metricsHeader: "Métricas de Avaliação de RI",
      metricsUnavailable: "Métricas indisponíveis para esta consulta",
    },
    resultCard: { coverAlt: "Capa de", score: "pontuação" },
    notFound: { message: "Ops! Página não encontrada", home: "Voltar para o início" },
  },
} as const;

export const LanguageProvider = ({ children }: { children: React.ReactNode }) => {
  const [language, setLanguageState] = useState<Language>(getInitialLanguage);

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, language);
    document.documentElement.lang = language === "pt" ? "pt-BR" : "en";
  }, [language]);

  const value = useMemo<LanguageContextValue>(
    () => ({
      language,
      setLanguage: setLanguageState,
      toggleLanguage: () => setLanguageState((current) => (current === "en" ? "pt" : "en")),
      t: translations[language],
    }),
    [language],
  );

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
};

export const useLanguage = () => {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage must be used within LanguageProvider");
  return ctx;
};
