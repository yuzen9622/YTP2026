/** @type {import('jest').Config} */
module.exports = {
  projects: [
    {
      displayName: "unit",
      testEnvironment: "node",
      testMatch: ["<rootDir>/src/store/__tests__/**/*.test.ts"],
      setupFiles: ["<rootDir>/jest.setup.ts"],
      transform: {
        "^.+\\.tsx?$": ["ts-jest", { diagnostics: false }],
      },
      moduleNameMapper: {
        "^@/(.*)$": "<rootDir>/src/$1",
      },
      clearMocks: true,
    },
  ],
};
