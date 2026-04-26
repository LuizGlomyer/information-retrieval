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
      titleSuffix: "measured five ways.",
      lede:
        "A study in lexical and neural retrieval over a structured English-language game catalog. We index, weight, embed and fine-tune - then put each model on the same stand and let the metrics talk.",
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
          output: "12,438 documents - 11 fields",
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
          title: "Hybrid layer - BM25 + Embeddings",
          desc:
            "Dense embeddings rescore the top-k from weighted BM25 via reciprocal rank fusion. Recovers queries with paraphrased vocabulary.",
          output: "Latency: ~210 ms",
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
          output: "9 metrics - 5 models",
        },
      ],
    },
    models: {
      heading: {
        eyebrow: "02 - Models",
        title: "Five rankers, two families",
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
        bm25_weighted: {
          tagline: "BM25 with hand-tuned field boosts",
          description:
            "Same algorithm with per-field boosts (e.g. name^3, summary^1). Encodes editorial priors about where a match matters most.",
          techniques: ["Field boosts", "Editorial priors"],
        },
        bm25_weighted_embeddings: {
          tagline: "Hybrid: lexical + dense vectors",
          description:
            "Combines weighted BM25 with a dense semantic similarity layer. Rescues queries where vocabulary doesn't match but meaning does.",
          techniques: ["Hybrid retrieval", "Dense vectors", "Reciprocal rank fusion"],
        },
        bert: {
          tagline: "Pre-trained transformer encoder",
          description:
            "Cross-encoder using a pre-trained BERT model. Reads query and document together to produce a contextual relevance score.",
          techniques: ["Transformer", "Cross-encoder", "Contextual"],
        },
        bert_finetuned: {
          tagline: "Fine-tuned on the games corpus",
          description:
            "BERT cross-encoder fine-tuned on labeled query-game pairs. Adapts the encoder to gaming vocabulary and editorial relevance.",
          techniques: ["Fine-tuning", "Domain adaptation", "Pairwise loss"],
        },
      } satisfies Record<ModelId, { tagline: string; description: string; techniques: string[] }>,
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
    },
    playground: {
      heading: {
        eyebrow: "04 - Playground",
        title: "Run a query. Watch the rankers disagree.",
        lede:
          "Type a search and see how each model ranks the catalog. Switch between viewing a single model in detail or comparing several side by side.",
      },
      defaultQuery: "open world post-apocalyptic shooter",
      suggestions: [
        "open world post-apocalyptic shooter",
        "cozy puzzle relaxing",
        "cyberpunk stealth hacking",
        "fantasy rpg knight magic",
      ],
      placeholder: "e.g. cyberpunk stealth hacking...",
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
      titleSuffix: "medidos de cinco formas.",
      lede:
        "Um estudo de recuperação lexical e neural em um catálogo estruturado de jogos em inglês. Indexamos, ponderamos, geramos embeddings e fazemos fine-tuning - depois colocamos cada modelo na mesma bancada e deixamos as metricas falarem.",
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
        title: "Seis etapas do catálogo bruto as respostas ranqueadas",
        lede:
          "Cada etapa e versionada e avaliada de forma independente. O mesmo pré-processamento e os mesmos filtros alimentam todos os rankers, então comparamos os rankers em si.",
      },
      steps: [
        {
          title: "Ingestão do corpus",
          desc:
            "Registros de jogos normalizados e indexados no Elasticsearch com um mapeamento tipado (nome, resumo, gêneros, temas, plataformas, avaliações).",
          output: "12.438 documentos - 11 campos"
        },
        {
          title: "Pré-processamento de texto",
          desc:
            "Lowercase, tokenizacao por espacos e remocao de stopwords em inglês. Trabalhos futuros: lematização e reconhecimento de entidades para franquias.",
          output: "Média de 84 tokens / doc",
        },
        {
          title: "Recuperação lexical - BM25",
          desc:
            "Consultas multi-match com pesos opcionais por campo. Captura correspondencias exatas e morfologicas; serve como baseline forte.",
          output: "Latência: ~120 ms",
        },
        {
          title: "Camada hibrida - BM25 + Embeddings",
          desc:
            "Embeddings densos reordenam o top-k do BM25 ponderado via reciprocal rank fusion. Recupera consultas com vocabulário parafraseado.",
          output: "Latência: ~210 ms",
        },
        {
          title: "Re-ranking neural - BERT",
          desc:
            "O cross-encoder le (consulta, documento) em conjunto. A variante fine-tuned se adapta ao vocabulário de games e a rótulos editoriais de relevância.",
          output: "Latência: ~480 ms",
        },
        {
          title: "Esteira de avaliacao",
          desc:
            "Cada modelo e pontuado no mesmo conjunto de consultas rotuladas usando nove metricas de RI. Os resultados sao versionados por experimento.",
          output: "9 metricas - 5 modelos",
        },
      ],
    },
    models: {
      heading: {
        eyebrow: "02 - Modelos",
        title: "Cinco rankers, duas familias",
        lede:
          "Modelos lexicais sao rapidos, transparentes e rigidos com vocabulario. Modelos neurais sao mais lentos, opacos e tolerantes. Usamos os dois e deixamos as consultas decidirem.",
      },
      families: { lexical: "lexical", neural: "neural" },
      statuses: { stable: "estavel", experimental: "experimental", planned: "planejado" },
      copy: {
        bm25: {
          tagline: "Baseline lexical nativo",
          description:
            "Ranking nativo do Elasticsearch. Frequencia do termo, frequencia inversa do documento e normalizacao de tamanho em cada campo pesquisavel.",
          techniques: ["TF-IDF", "Normalizacao", "Multi-match"],
        },
        bm25_weighted: {
          tagline: "BM25 com pesos manuais por campo",
          description:
            "Mesmo algoritmo com boosts por campo (ex.: name^3, summary^1). Codifica prioridades editoriais sobre onde uma correspondencia importa mais.",
          techniques: ["Boost por campo", "Prioridades editoriais"],
        },
        bm25_weighted_embeddings: {
          tagline: "Hibrido: lexical + vetores densos",
          description:
            "Combina BM25 ponderado com uma camada semantica densa. Recupera consultas quando o vocabulario nao coincide, mas o significado sim.",
          techniques: ["Recuperacao hibrida", "Vetores densos", "Reciprocal rank fusion"],
        },
        bert: {
          tagline: "Encoder transformer pre-treinado",
          description:
            "Cross-encoder usando um modelo BERT pre-treinado. Le consulta e documento juntos para produzir uma pontuacao contextual de relevancia.",
          techniques: ["Transformer", "Cross-encoder", "Contextual"],
        },
        bert_finetuned: {
          tagline: "Fine-tuned no corpus de jogos",
          description:
            "Cross-encoder BERT ajustado com pares consulta-jogo rotulados. Adapta o encoder ao vocabulario de games e a relevancia editorial.",
          techniques: ["Fine-tuning", "Adaptacao de dominio", "Perda pairwise"],
        },
      } satisfies Record<ModelId, { tagline: string; description: string; techniques: string[] }>,
    },
    metrics: {
      heading: {
        eyebrow: "03 - Avaliacao",
        title: "Lado a lado, nas mesmas perguntas",
        lede:
          "Cada modelo e avaliado no mesmo conjunto de consultas rotuladas. Reportamos nove metricas padrao de RI - precision at k, recall, MAP, F1 e NDCG em tres cortes.",
      },
      compareOn: "Comparar por:",
      higherIsBetter: "maior e melhor",
      selectedMetricDescription: "Pontuacao por modelo na metrica selecionada.",
      allMetricsTitle: "Todas as metricas, todos os modelos",
      profile: "perfil",
      allMetricsDescription: "Cada linha e um modelo. Mostra os pontos fortes ao longo do espectro de metricas.",
      modelColumn: "Modelo",
      bestNote: "Melhor por coluna. Todas as pontuacoes em [0, 1].",
    },
    playground: {
      heading: {
        eyebrow: "04 - Playground",
        title: "Execute uma busca. Veja os rankers discordarem.",
        lede:
          "Digite uma busca e veja como cada modelo ranqueia o catalogo. Alterne entre ver um modelo em detalhe ou comparar varios lado a lado.",
      },
      defaultQuery: "open world post-apocalyptic shooter",
      suggestions: [
        "open world post-apocalyptic shooter",
        "cozy puzzle relaxing",
        "cyberpunk stealth hacking",
        "fantasy rpg knight magic",
      ],
      placeholder: "ex.: cyberpunk stealth hacking...",
      searchLabel: "Consulta de busca",
      search: "Buscar",
      try: "teste:",
      viewMode: "Modo de visualizacao",
      single: "Unico",
      compare: "Comparar",
      model: "Modelo",
      modelsToCompare: "Modelos para comparar",
      hits: "resultados",
      milliseconds: "ms",
      noResults: "Sem resultados.",
      emptyTitle: "Pronto quando voce estiver.",
      emptyDescription:
        "Busque acima ou escolha uma consulta sugerida para ver como os rankers respondem.",
      runDefault: "Executar busca padrao",
    },
    resultCard: { coverAlt: "Capa de", score: "pontuacao" },
    notFound: { message: "Ops! Pagina nao encontrada", home: "Voltar para o inicio" },
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
