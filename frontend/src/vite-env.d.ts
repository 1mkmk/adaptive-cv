/// <reference types="vite/client" />

// For TypeScript to find these types in tests
interface ImportMeta {
  readonly env: {
    readonly VITE_API_URL: string;
    readonly [key: string]: string | boolean | undefined;
  };
}
