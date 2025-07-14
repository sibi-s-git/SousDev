declare global {
  interface Window {
    electronAPI: {
      selectFolder: () => Promise<string>;
      platform: string;
      versions: any;
    };
  }
}

export {}; 