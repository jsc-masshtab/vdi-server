module.exports = {
  env: {
    browser: true,
  },
  parser: "@typescript-eslint/parser",
  parserOptions: {
    tsconfigRootDir: __dirname,
    project: "tsconfig.json",
    sourceType: "module",
  },
  plugins: [
    "eslint-plugin-import",
    "@angular-eslint/eslint-plugin",
    "@typescript-eslint",
  ],
  rules: {
    "@angular-eslint/component-class-suffix": "error",
    "@angular-eslint/directive-class-suffix": "error",
    "@angular-eslint/no-host-metadata-property": "error",
    "@angular-eslint/no-input-rename": "error",
    "@angular-eslint/no-inputs-metadata-property": "error",
    "@angular-eslint/no-output-on-prefix": "error",
    "@angular-eslint/no-output-rename": "error",
    "@angular-eslint/no-outputs-metadata-property": "error",
    "@angular-eslint/use-lifecycle-interface": "error",
    "@angular-eslint/use-pipe-transform-interface": "error",
    "@typescript-eslint/adjacent-overload-signatures": "error",
    "@typescript-eslint/array-type": "off",
    "@typescript-eslint/consistent-type-assertions": "error",
    "@typescript-eslint/dot-notation": "off",
    "@typescript-eslint/explicit-member-accessibility": [
      "off",
      {
        accessibility: "explicit",
      },
    ],
    "@typescript-eslint/indent": "off",
    "@typescript-eslint/member-delimiter-style": [
      "off",
      {
        multiline: {
          delimiter: "none",
          requireLast: true,
        },
        singleline: {
          delimiter: "semi",
          requireLast: false,
        },
      },
    ],
    "@typescript-eslint/member-ordering": "off",
    "@typescript-eslint/naming-convention": "off",
    "@typescript-eslint/no-empty-function": "off",
    "@typescript-eslint/no-empty-interface": "error",
    "@typescript-eslint/no-explicit-any": "off",
    "@typescript-eslint/no-inferrable-types": "off",
    "@typescript-eslint/no-misused-new": "error",
    "@typescript-eslint/no-namespace": "error",
    "@typescript-eslint/no-non-null-assertion": "error",
    "@typescript-eslint/no-parameter-properties": "off",
    "@typescript-eslint/no-shadow": [
      "error",
      {
        hoist: "all",
      },
    ],
    "@typescript-eslint/no-unused-expressions": "error",
    "@typescript-eslint/no-use-before-define": "off",
    "@typescript-eslint/no-var-requires": "error",
    "@typescript-eslint/prefer-for-of": "off",
    "@typescript-eslint/prefer-function-type": "error",
    "@typescript-eslint/prefer-namespace-keyword": "error",
    "@typescript-eslint/quotes": ["error", "single"],
    "@typescript-eslint/semi": ["off", null],
    "@typescript-eslint/triple-slash-reference": [
      "error",
      {
        path: "always",
        types: "prefer-import",
        lib: "always",
      },
    ],
    "@typescript-eslint/type-annotation-spacing": "error",
    "@typescript-eslint/unified-signatures": "error",
    "arrow-body-style": "error",
    "arrow-parens": ["off", "always"],
    "comma-dangle": ["error", "only-multiline"],
    complexity: "off",
    "constructor-super": "error",
    curly: "error",
    "eol-last": "error",
    eqeqeq: ["error", "smart"],
    "guard-for-in": "error",
    "id-blacklist": "off",
    "id-match": "off",
    "import/no-deprecated": "warn",
    "import/order":[
      "error",
      {
        "groups": ["builtin", "external", "internal"],
        "pathGroups":[{
          "pattern": "angular",
          "group": "external",
          "position": "before"
        },
        {
          "pattern": "@core/**",
          "group": "external",
          "position": "after"
        },
        {
          "pattern": "@shared/**",
          "group": "external",
          "position": "after"
        },
        {
          "pattern": "@pages/**",
          "group": "external",
          "position": "after"
        }
      ],
        "pathGroupsExcludedImportTypes": ["angular"],
        "newlines-between": "always",
        "alphabetize": {
          "order": "asc",
          "caseInsensitive":true
        }
      }
    ],
    "max-classes-per-file": "off",
    "max-len": [
      "error",
      {
        code: 240,
      },
    ],
    "new-parens": "error",
    "no-bitwise": "error",
    "no-caller": "error",
    "no-cond-assign": "error",
    "no-console": "off",
    "no-debugger": "error",
    "no-empty": "off",
    "no-eval": "error",
    "no-fallthrough": "error",
    "no-invalid-this": "off",
    "no-multiple-empty-lines": "off",
    "no-new-wrappers": "error",
    "no-restricted-imports": ["error", "rxjs/Rx"],
    "no-throw-literal": "error",
    "no-trailing-spaces": "off",
    "no-undef-init": "error",
    "no-underscore-dangle": "off",
    "no-unsafe-finally": "error",
    "no-unused-labels": "error",
    "no-var": "off",
    "object-shorthand": "error",
    "one-var": ["error", "never"],
    "prefer-const": "off",
    "quote-props": ["error", "as-needed"],
    radix: "error",
    "space-before-function-paren": [
      "error",
      {
        anonymous: "never",
        asyncArrow: "always",
        named: "never",
      },
    ],
    "spaced-comment": [
      "error",
      "always",
      {
        markers: ["/"],
      },
    ],
    "use-isnan": "error",
    "valid-typeof": "off",
  },
};
