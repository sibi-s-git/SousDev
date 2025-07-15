declare global {
  interface Window {
    electronAPI: {
      selectFolder: () => Promise<string>;
      loadEnvVars: () => Promise<Record<string, string>>;
      saveEnvVars: (variables: Record<string, string>) => Promise<boolean>;
      ensureContextFolder: () => Promise<string | null>;
      vectorizeProject: (projectPath: string, contentPath: string, openaiApiKey: string) => Promise<any>;
      platform: string;
      versions: any;
    };
  }
}

export {}; 