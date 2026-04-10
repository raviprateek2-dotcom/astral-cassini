import { globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";
import react from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";

/**
 * ESLint 9 flat config: rules that need a plugin must sit in the same config object
 * as `plugins: { ... }` — later objects do not inherit plugins from earlier spreads.
 */
const eslintConfig = [
  ...nextVitals,
  ...nextTs,
  globalIgnores([
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    "jest.config.js",
  ]),
  {
    plugins: {
      react,
      "react-hooks": reactHooks,
    },
    settings: {
      react: { version: "detect" },
    },
    rules: {
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/no-unused-vars": "warn",
      "react/no-unescaped-entities": "warn",
      "react-hooks/set-state-in-effect": "off",
    },
  },
  {
    files: ["e2e/**/*.ts"],
    plugins: {
      "react-hooks": reactHooks,
    },
    rules: {
      "react-hooks/rules-of-hooks": "off",
    },
  },
  {
    files: ["scripts/**/*.cjs"],
    rules: {
      "@typescript-eslint/no-require-imports": "off",
    },
  },
];

export default eslintConfig;
