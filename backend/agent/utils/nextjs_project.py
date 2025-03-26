import os
import json

def create_base_nextjs_project(project_path: str) -> None:
    """
    Creates a base Next.js project with Tailwind CSS using a predefined template.
    
    Args:
        project_path: The path where the Next.js project will be created
    """
    # Check if the directory already exists
    if os.path.exists(project_path):
        print(f"Project directory already exists at {project_path}")
    else:
        print(f"Creating new Next.js project at {project_path}")
        
        # Create the directory structure
        os.makedirs(os.path.join(project_path, "pages"), exist_ok=True)
        os.makedirs(os.path.join(project_path, "cypress", "e2e"), exist_ok=True)
        os.makedirs(os.path.join(project_path, "cypress", "support"), exist_ok=True)
        os.makedirs(os.path.join(project_path, "styles"), exist_ok=True)
        os.makedirs(os.path.join(project_path, "public"), exist_ok=True)
        os.makedirs(os.path.join(project_path, "components"), exist_ok=True)

        # Create minimal package.json
        package_json = {
            "name": "nextjs-project",
            "version": "0.1.0",
            "private": True,
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
                "cypress": "cypress open",
                "cypress:run": "cypress run",
                "reset-db": "node db/reset.js"
            },
            "dependencies": {
                "next": "^12.0.0",
                "react": "^17.0.2",
                "react-dom": "^17.0.2",
                "tailwindcss": "^3.0.0",
                "sqlite3": "^5.1.7"
            },
            "devDependencies": {
                "cypress": "^14.2.0",
                "autoprefixer": "^10.4.0",
                "postcss": "^8.4.5"
            }
        }
        
        with open(os.path.join(project_path, "package.json"), "w") as f:
            json.dump(package_json, f, indent=2)
            
        # Create tailwind.config.js
        tailwind_config = """module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
"""
        with open(os.path.join(project_path, "tailwind.config.js"), "w") as f:
            f.write(tailwind_config)
            
        # Create postcss.config.js
        postcss_config = """module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
"""
        with open(os.path.join(project_path, "postcss.config.js"), "w") as f:
            f.write(postcss_config)
            
        # Create global.css with Tailwind imports
        global_css = """@tailwind base;
@tailwind components;
@tailwind utilities;
"""
        with open(os.path.join(project_path, "styles", "globals.css"), "w") as f:
            f.write(global_css)
            
        # Create bare minimum _app.js to import the global styles
        app_js = """import '../styles/globals.css'

function MyApp({ Component, pageProps }) {
  return <Component {...pageProps} />
}

export default MyApp
"""
        with open(os.path.join(project_path, "pages", "_app.js"), "w") as f:
            f.write(app_js)
            
        # Create cypress.json config
        cypress_config = """
                const { defineConfig } = require('cypress')

                module.exports = defineConfig({
                e2e: {
                    baseUrl: 'http://localhost:3000',
                },
                })"""
        with open(os.path.join(project_path, "cypress.config.js"), "w") as f:
            f.write(cypress_config)

        # write default support file
        with open(os.path.join(project_path, "cypress", "support", "e2e.js"), "w") as f:
            f.write("")