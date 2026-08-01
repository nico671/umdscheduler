# UMD Scheduler Frontend

Svelte 5 frontend powered by Vite.

## Run the frontend locally

From the repository root:

```bash
cd frontend
npm install
```

Set the backend URL in `frontend/.env`:

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

Start the Vite development server:

```bash
npm run dev
```

Open <http://localhost:5173> in a browser. Run the backend in a second
terminal using the instructions in [`backend/README.md`](../backend/README.md).

## Other commands

```bash
npm run build    # Create a production build in dist/
npm run preview  # Preview the production build locally
```
