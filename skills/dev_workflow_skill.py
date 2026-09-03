import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from skills.base_skill import BaseSkill
from tools.base_tool import BaseTool
from tools.file_tools import resolve_folder_path

logger = logging.getLogger(__name__)

PREFERENCES_FILE = Path(__file__).resolve().parent.parent / "data" / "developer_preferences.json"

class GetDevPreferencesTool(BaseTool):
    name = "get_dev_preferences"
    description = "Retrieves Arslan's developer preferences, preferred tech stack (React, Node, Mongo, Python, Tailwind), and coding standards."
    parameters = {"type": "object", "properties": {}}

    def execute(self) -> Dict[str, Any]:
        if not PREFERENCES_FILE.exists():
            return {"status": "error", "message": "Developer preferences file not found."}
        try:
            with open(PREFERENCES_FILE, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            return {"status": "success", "preferences": data}
        except Exception as e:
            return {"status": "error", "message": f"Could not load preferences: {str(e)}"}


class ScaffoldProjectTool(BaseTool):
    name = "scaffold_project"
    description = "Generates a clean, modular starter project structure on disk for React, Express, FastAPI, or modern HTML/Tailwind."
    parameters = {
        "type": "object",
        "properties": {
            "project_type": {
                "type": "string",
                "enum": ["react_component", "express_api", "fastapi_api", "html_tailwind", "python_cli"],
                "description": "The type of boilerplate or project scaffold to create."
            },
            "destination_folder": {
                "type": "string",
                "description": "Folder or directory path to create the files in (e.g. 'desktop/my_project')."
            },
            "name": {
                "type": "string",
                "description": "Name of the component, module, or project."
            }
        },
        "required": ["project_type", "destination_folder"]
    }

    def execute(self, project_type: str, destination_folder: str, name: str = "App") -> Dict[str, Any]:
        target_dir = resolve_folder_path(destination_folder)
        target_dir.mkdir(parents=True, exist_ok=True)
        created_files = []

        try:
            ptype = project_type.lower()
            if ptype == "react_component":
                comp_file = target_dir / f"{name}.jsx"
                content = f"""import React, {{ useState }} from 'react';

/**
 * {name} Component
 * Built for Arslan's React.js + Tailwind CSS workflow.
 */
export const {name} = () => {{
  const [isActive, setIsActive] = useState(false);

  return (
    <div className="flex flex-col items-center justify-center p-6 bg-slate-900 text-white rounded-2xl shadow-xl border border-slate-800">
      <h2 className="text-2xl font-bold mb-4 text-cyan-400">{name}</h2>
      <p className="text-slate-400 mb-6">Production-ready React component with Tailwind CSS styling.</p>
      <button 
        onClick={{() => setIsActive(!isActive)}}
        className="px-6 py-2.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-medium rounded-xl transition duration-200 shadow-md"
      >
        {{isActive ? 'Active State' : 'Click Me'}}
      </button>
    </div>
  );
}};

export default {name};
"""
                comp_file.write_text(content, encoding="utf-8")
                created_files.append(str(comp_file))

            elif ptype == "express_api":
                server_file = target_dir / "server.js"
                content = """const express = require('express');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());

// Health check route
app.get('/api/health', (req, res) => {
  res.status(200).json({ status: 'ok', uptime: process.uptime(), timestamp: new Date().toISOString() });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Internal Server Error', message: err.message });
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
"""
                server_file.write_text(content, encoding="utf-8")
                created_files.append(str(server_file))

            elif ptype == "fastapi_api":
                main_file = target_dir / "main.py"
                content = """from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

app = FastAPI(title="API Service", version="1.0.0")

class HealthResponse(BaseModel):
    status: str
    version: str

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
"""
                main_file.write_text(content, encoding="utf-8")
                created_files.append(str(main_file))

            elif ptype == "html_tailwind":
                html_file = target_dir / "index.html"
                content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{name}</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex items-center justify-center p-6 font-sans">
  <div class="max-w-md w-full p-8 bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl text-center space-y-6">
    <div class="inline-flex p-3 bg-cyan-500/10 text-cyan-400 rounded-2xl border border-cyan-500/20">
      <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
    </div>
    <h1 class="text-3xl font-extrabold tracking-tight text-white">{name}</h1>
    <p class="text-slate-400 text-sm leading-relaxed">Built with Tailwind CSS for modern, high-performance UI prototyping.</p>
    <button class="w-full py-3 px-4 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-semibold rounded-xl shadow-lg transition duration-200">
      Get Started
    </button>
  </div>
</body>
</html>
"""
                html_file.write_text(content, encoding="utf-8")
                created_files.append(str(html_file))

            elif ptype == "python_cli":
                cli_file = target_dir / "cli.py"
                content = """import argparse
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

def main():
    parser = argparse.ArgumentParser(description="CLI Tool")
    parser.add_argument("--name", type=str, default="World", help="Name to greet")
    args = parser.parse_args()

    logging.info(f"Hello, {args.name}!")

if __name__ == "__main__":
    main()
"""
                cli_file.write_text(content, encoding="utf-8")
                created_files.append(str(cli_file))

            return {
                "status": "success",
                "message": f"Successfully scaffolded '{project_type}' in {target_dir}",
                "created_files": created_files
            }

        except Exception as e:
            logger.error(f"Failed to scaffold project {project_type}: {e}", exc_info=True)
            return {"status": "error", "message": f"Scaffolding failed: {str(e)}"}


class DevWorkflowSkill(BaseSkill):
    name = "dev_workflow"
    description = "Tailored full-stack developer tools for Arslan (React, Node, Express, FastAPI, Tailwind scaffolding and preferences)."

    def get_tools(self) -> List[BaseTool]:
        return [GetDevPreferencesTool(), ScaffoldProjectTool()]
