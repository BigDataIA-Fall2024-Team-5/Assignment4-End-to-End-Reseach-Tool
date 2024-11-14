# UI README

This folder contains the frontend UI built using Next.js, offering an interactive interface for querying, searching, and interacting with research data.

## Project Structure

📂 ui  
├── components.json  
├── next.config.mjs  
├── package.json  
├── pnpm-lock.yaml  
├── postcss.config.mjs  
├── tailwind.config.ts  
├── tsconfig.json  
└── src  
   ├── app  
   │   ├── Main.tsx  
   │   ├── api  
   │   │   ├── copilotkit  
   │   │   │   └── route.ts  
   │   │   └── export  
   │   │       ├── codelabs  
   │   │       └── pdf  
   ├── components  
   └── lib  

## Environment Variables
The UI requires specific environment variables for interacting with the backend services. Create an `.env` file in the `ui` directory and add the following:

# .env file in UI
REMOTE_ACTION_URL='http://localhost:8000'  # Use 'http://backend:8000' if using Docker Compose
OPENAI_API_KEY='sk-...your_openai_api_key_here...'

## Setup and Run

1. **Install dependencies**: Use `pnpm` for package management.
   
   ```bash
   pnpm i
   ```

2. **Run the development server**:

   ```bash
   pnpm dev
   ```

   By default, the UI will be available at `http://localhost:3000`.

