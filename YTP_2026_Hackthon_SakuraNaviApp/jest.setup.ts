// Silence expo winter runtime globals that don't exist in Jest's Node environment
(global as any).__ExpoImportMetaRegistry = {};

jest.mock("expo/fetch", () => ({
  __esModule: true,
  fetch: (...args: Parameters<typeof global.fetch>) => global.fetch(...args),
}));
