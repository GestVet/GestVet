import js from '@eslint/js'
import boundaries from 'eslint-plugin-boundaries'
import checkFile from 'eslint-plugin-check-file'
import react from 'eslint-plugin-react'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import sonarjs from 'eslint-plugin-sonarjs'
import globals from 'globals'
import tseslint from 'typescript-eslint'

export default tseslint.config(
  {
    ignores: ['dist/**', 'node_modules/**', 'src/api/schema.d.ts'],
  },

  // ---------------------------------------------------------------------
  // Base: correccion del lenguaje y tipos.
  // ---------------------------------------------------------------------
  js.configs.recommended,
  tseslint.configs.strictTypeChecked,
  tseslint.configs.stylisticTypeChecked,

  {
    languageOptions: {
      ecmaVersion: 2023,
      globals: globals.browser,
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },

  // ---------------------------------------------------------------------
  // React.
  // ---------------------------------------------------------------------
  {
    files: ['**/*.{ts,tsx}'],
    plugins: { react, 'react-hooks': reactHooks, 'react-refresh': reactRefresh },
    settings: { react: { version: 'detect' } },
    rules: {
      ...react.configs.flat.recommended.rules,
      ...react.configs.flat['jsx-runtime'].rules,
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],

      // SOLID, responsabilidad unica: un archivo describe un componente.
      'react/no-multi-comp': ['error', { ignoreStateless: false }],
      'react/jsx-no-useless-fragment': 'error',
      'react/self-closing-comp': 'error',
    },
  },

  // ---------------------------------------------------------------------
  // KISS y DRY: limites de tamano, complejidad y duplicacion.
  // ---------------------------------------------------------------------
  {
    files: ['**/*.{ts,tsx}'],
    plugins: { sonarjs },
    rules: {
      ...sonarjs.configs.recommended.rules,

      // DRY
      'sonarjs/no-identical-functions': 'error',
      'sonarjs/no-duplicate-string': ['error', { threshold: 3 }],
      'sonarjs/no-collapsible-if': 'error',

      // KISS
      'sonarjs/cognitive-complexity': ['error', 15],
      complexity: ['error', 10],
      'max-depth': ['error', 3],
      'max-lines': ['error', { max: 250, skipBlankLines: true, skipComments: true }],
      'max-lines-per-function': [
        'error',
        { max: 80, skipBlankLines: true, skipComments: true },
      ],
      'max-params': ['error', 4],
      'max-nested-callbacks': ['error', 3],

      // SOLID, inversion de dependencias: preferir contratos explicitos.
      '@typescript-eslint/explicit-module-boundary-types': 'off',
      '@typescript-eslint/consistent-type-imports': [
        'error',
        { prefer: 'type-imports', fixStyle: 'inline-type-imports' },
      ],
      '@typescript-eslint/no-explicit-any': 'error',
      'no-console': ['error', { allow: ['warn', 'error'] }],
      eqeqeq: ['error', 'always'],
    },
  },

  // ---------------------------------------------------------------------
  // Nombrado de carpetas y archivos.
  // ---------------------------------------------------------------------
  {
    files: ['src/**/*'],
    plugins: { 'check-file': checkFile },
    rules: {
      'check-file/folder-naming-convention': [
        'error',
        { 'src/**/': 'KEBAB_CASE' },
      ],
      'check-file/filename-naming-convention': [
        'error',
        {
          // Componentes y vistas en PascalCase, porque nombran un componente.
          'src/components/**/*.tsx': 'PASCAL_CASE',
          'src/features/**/*.tsx': 'PASCAL_CASE',
          // Todo lo demas nombra un modulo, no un componente.
          'src/{api,hooks,services,store}/**/*.ts': 'CAMEL_CASE',
          'src/features/**/*.ts': 'CAMEL_CASE',
        },
        { ignoreMiddleExtensions: true },
      ],
      'check-file/no-index': 'off',
    },
  },

  // ---------------------------------------------------------------------
  // Limites de arquitectura entre capas.
  //
  // La direccion de dependencia es una sola: la composicion conoce a las
  // caracteristicas, las caracteristicas no se conocen entre si, y las capas
  // compartidas no conocen el dominio.
  // ---------------------------------------------------------------------
  {
    files: ['src/**/*.{ts,tsx}'],
    plugins: { boundaries },
    settings: {
      // Sin este resolutor, las importaciones sin extension no se resuelven y
      // todas las reglas de limites quedan inertes sin avisar.
      'import/resolver': {
        typescript: { project: './tsconfig.json' },
      },
      // La raiz de composicion (src/main.tsx y src/App.tsx) queda fuera a
      // proposito: su trabajo es precisamente conocer todas las capas para
      // ensamblarlas. Todo lo demas si esta restringido.
      'boundaries/include': [
        'src/router/**/*',
        'src/features/**/*',
        'src/components/**/*',
        'src/hooks/**/*',
        'src/store/**/*',
        'src/api/**/*',
        'src/services/**/*',
      ],
      // El patron nombra la carpeta raiz del elemento, no sus archivos.
      'boundaries/elements': [
        { type: 'router', pattern: 'src/router' },
        { type: 'features', pattern: 'src/features/*', capture: ['feature'] },
        { type: 'components', pattern: 'src/components' },
        { type: 'hooks', pattern: 'src/hooks' },
        { type: 'store', pattern: 'src/store' },
        { type: 'api', pattern: 'src/api' },
        { type: 'services', pattern: 'src/services' },
      ],
    },
    rules: {
      'boundaries/no-unknown-dependencies': 'error',
      'boundaries/dependencies': [
        'error',
        {
          default: 'disallow',
          policies: [
            {
              from: [{ element: { type: 'router' } }],
              allow: [
                { to: { element: { type: 'features' } } },
                { to: { element: { type: 'components' } } },
              ],
            },
            {
              // Una caracteristica solo puede importarse a si misma.
              from: [{ element: { type: 'features' } }],
              allow: [
                { to: { element: { type: 'features', captured: { feature: '{{from.feature}}' } } } },
                { to: { element: { type: 'components' } } },
                { to: { element: { type: 'hooks' } } },
                { to: { element: { type: 'store' } } },
                { to: { element: { type: 'services' } } },
                { to: { element: { type: 'api' } } },
              ],
              message:
                'Una caracteristica no puede depender de otra caracteristica. Sube lo compartido a components, hooks o api.',
            },
            {
              from: [{ element: { type: 'components' } }],
              allow: [
                { to: { element: { type: 'components' } } },
                { to: { element: { type: 'hooks' } } },
              ],
              message: 'Los componentes compartidos no pueden depender de logica de dominio.',
            },
            {
              from: [{ element: { type: 'hooks' } }],
              allow: [
                { to: { element: { type: 'hooks' } } },
                { to: { element: { type: 'services' } } },
                { to: { element: { type: 'api' } } },
              ],
            },
            {
              from: [{ element: { type: 'store' } }],
              allow: [
                { to: { element: { type: 'services' } } },
                { to: { element: { type: 'api' } } },
              ],
            },
            {
              from: [{ element: { type: 'api' } }],
              allow: [
                { to: { element: { type: 'api' } } },
                { to: { element: { type: 'services' } } },
              ],
            },
            {
              from: [{ element: { type: 'services' } }],
              allow: [{ to: { element: { type: 'services' } } }],
            },
          ],
        },
      ],
    },
  },

  // ---------------------------------------------------------------------
  // Archivos de configuracion.
  // ---------------------------------------------------------------------
  {
    files: ['*.config.{js,ts}', 'eslint.config.js'],
    languageOptions: { globals: globals.node },
    extends: [tseslint.configs.disableTypeChecked],
    rules: {
      'check-file/filename-naming-convention': 'off',
    },
  },
)
