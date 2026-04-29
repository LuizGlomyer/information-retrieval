import g1 from "@/assets/games/game-1.jpg";
import g2 from "@/assets/games/game-2.jpg";
import g3 from "@/assets/games/game-3.jpg";
import g4 from "@/assets/games/game-4.jpg";
import g5 from "@/assets/games/game-5.jpg";
import g6 from "@/assets/games/game-6.jpg";
import type { GameResult } from "./types";

export const MOCK_GAMES: GameResult[] = [
  {
    id: "g1",
    name: "Ashfall: Last Light",
    cover: g1,
    summary:
      "A lone scavenger climbs the ruins of a fallen capital, piecing together what ended the world while a hostile city watches.",
    rating: 87.4,
    release_date: "2022-09-14",
    genres: ["Shooter", "Action", "Adventure"],
    platforms: ["PC", "PlayStation 5", "Xbox Series X"],
    themes: ["Post-apocalyptic", "Survival", "Open world"],
  },
  {
    id: "g2",
    name: "Verdant Crown",
    cover: g2,
    summary:
      "A high fantasy RPG of oaths and old magic. Forge alliances across six kingdoms while a forgotten god claws back into the world.",
    rating: 91.0,
    release_date: "2023-04-02",
    genres: ["RPG", "Adventure"],
    platforms: ["PC", "PlayStation 5", "Switch"],
    themes: ["Fantasy", "Open world", "Story-rich"],
  },
  {
    id: "g3",
    name: "Neon Drift Protocol",
    cover: g3,
    summary:
      "A cyberpunk infiltration thriller. Hack, talk or shoot your way through a vertical city run by warring AI conglomerates.",
    rating: 83.2,
    release_date: "2021-11-30",
    genres: ["Action", "Shooter", "Stealth"],
    platforms: ["PC", "Xbox Series X"],
    themes: ["Cyberpunk", "Sci-Fi", "Stealth"],
  },
  {
    id: "g4",
    name: "Lighthouse Keepers",
    cover: g4,
    summary:
      "A cozy isometric puzzle game about restoring a chain of automated lighthouses. Quiet seas, charming machinery, no failure states.",
    rating: 78.5,
    release_date: "2024-02-20",
    genres: ["Puzzle", "Indie", "Casual"],
    platforms: ["PC", "Switch", "iOS"],
    themes: ["Cozy", "Nautical", "Relaxing"],
  },
  {
    id: "g5",
    name: "Ward 9: Quiet Hours",
    cover: g5,
    summary:
      "A first-person psychological horror set in an abandoned hospital. Limited light, no combat, and something that learns your habits.",
    rating: 80.1,
    release_date: "2023-10-13",
    genres: ["Horror", "Adventure"],
    platforms: ["PC", "PlayStation 5"],
    themes: ["Horror", "Psychological", "First Person"],
  },
  {
    id: "g6",
    name: "Outer Bloom",
    cover: g6,
    summary:
      "Drift through a hand-painted solar system collecting samples, narrating discoveries and slowly uncovering why the stars are dimming.",
    rating: 88.9,
    release_date: "2024-06-07",
    genres: ["Adventure", "Exploration", "Indie"],
    platforms: ["PC", "PlayStation 5", "Switch"],
    themes: ["Sci-Fi", "Exploration", "Story-rich"],
  },
];
