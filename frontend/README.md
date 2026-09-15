# Signal — Frontend

React (Vite) UI for pasting a project thread and watching Signal scan it for
contradictions between speakers.

## Run locally

```bash
cd frontend
npm install
npm run dev
```

Opens at http://localhost:5173 and talks to the backend at
http://localhost:8000 by default.

To point at a different backend (e.g. your deployed Render URL), create a
`.env` file in this folder:

```
VITE_API_URL=https://your-backend.onrender.com
```

## Deploy (Vercel)

1. Push this repo to GitHub.
2. On Vercel: New Project → import repo → set root directory to `frontend`.
3. Framework preset: Vite.
4. Add environment variable `VITE_API_URL` pointing at your deployed backend.
5. Deploy.
