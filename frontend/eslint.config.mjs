import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    "jest.config.js",
  ]),
  {
    rules: {
      // Incremental cleanup: avoid failing CI on legacy pages while new code stays strict in review.
      "@typescript-eslint/no-explicit-any": "warn",
      "react/no-unescaped-entities": "warn",
      "react-hooks/set-state-in-effect": "off",
      "@typescript-eslint/no-unused-vars": "warn",
    },
  },
  {
    files: ["e2e/**/*.ts"],
    rules: {
      // Playwright fixture API uses a callback parameter named `use`, not a React Hook.
      "react-hooks/rules-of-hooks": "off",
    },
  },
]);

export default eslintConfig;
