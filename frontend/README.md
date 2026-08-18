# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and Oxlint's TypeScript related rules in your project.

## Building for production locally

`.env.production` is intentionally **not** committed to the repository (it's excluded by the root `.gitignore`, along with all `.env*` files). On Render, `VITE_API_URL` is already set explicitly in `render.yaml` under the `accounting-frontend` service's `envVars`, so the build on Render works without this file.

If you want to run `npm run build` locally and produce a build that points at the deployed backend (instead of `http://localhost:8000/api`), create the file yourself:

```bash
# frontend/.env.production
VITE_API_URL=https://accounting-backend.onrender.com/api
```

Update the URL if the backend's Render service name/URL changes.
