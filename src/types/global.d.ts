declare global {
  interface Window {
    electronAPI: {
      selectFolder: () => Promise<string>;
      loadEnvVars: () => Promise<Record<string, string>>;
      saveEnvVars: (variables: Record<string, string>) => Promise<boolean>;
      ensureContextFolder: () => Promise<string | null>;
      checkProjectIntelligence: (contentPath: string) => Promise<{intelligence_exists: boolean, embeddings_exist: boolean}>;
      analyzeProject: (projectPath: string, contentPath: string, anthropicApiKey: string) => Promise<any>;
      vectorizeProject: (projectPath: string, contentPath: string, openaiApiKey: string) => Promise<any>;
      reloadProject: (projectPath: string, contentPath: string, openaiApiKey: string, anthropicApiKey: string) => Promise<any>;
      intelligentChat: (userMessage: string, images: string[], projectPath: string, contentPath: string, anthropicApiKey: string) => Promise<any>;
      platform: string;
      versions: any;
    };
  }
}

export {}; 