import type { IndexabilityPolicy } from "./types";

export const PUBLIC_ROBOTS =
  "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1";
export const PRIVATE_ROBOTS = "noindex,nofollow,noarchive";

export const APP_INDEXABILITY_POLICY: IndexabilityPolicy = {
  home: {
    pattern: "/",
    robots: PUBLIC_ROBOTS,
    indexable: true,
  },
  policyIndex: {
    pattern: "/policy",
    robots: PUBLIC_ROBOTS,
    indexable: true,
  },
  policyDocument: {
    pattern: "/policy/:documentId",
    robots: PUBLIC_ROBOTS,
    indexable: true,
  },
  auth: {
    pattern: "/(auth)/*",
    robots: PRIVATE_ROBOTS,
    indexable: false,
  },
  tabs: {
    pattern: "/(tabs)/*",
    robots: PRIVATE_ROBOTS,
    indexable: false,
  },
  knowledge: {
    pattern: "/(knowledge)/*",
    robots: PRIVATE_ROBOTS,
    indexable: false,
  },
  policyPrivate: {
    pattern: "/(policy)/*",
    robots: PRIVATE_ROBOTS,
    indexable: false,
  },
  chatDetail: {
    pattern: "/(chat-detail)/*",
    robots: PRIVATE_ROBOTS,
    indexable: false,
  },
};
