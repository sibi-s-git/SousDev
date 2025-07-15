declare global {
  interface Window {
    electronAPI: {
      selectFolder: () => Promise<string>;
      loadEnvVars: () => Promise<Record<string, string>>;
      saveEnvVars: (variables: Record<string, string>) => Promise<boolean>;
      ensureContextFolder: () => Promise<string | null>;
      platform: string;
      versions: any;
    };
  }
}

export {}; 