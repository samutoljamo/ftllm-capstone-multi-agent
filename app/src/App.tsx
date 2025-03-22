import { useState, useEffect, useRef } from "react";

function App() {
  const [projectName, setProjectName] = useState("");
  const [description, setDescription] = useState("");
  const [messages, setMessages] = useState<string[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [projectDetails, setProjectDetails] = useState<{
    project_id: string;
    directory: string;
  } | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const connectWebSocket = (projectData: {
    project_id: string;
    directory: string;
  }) => {
    const ws = new WebSocket("ws://localhost:8000/ws");

    ws.onopen = () => {
      setIsConnected(true);
      setMessages([]);
      // Send project details to the WebSocket
      ws.send(JSON.stringify(projectData));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages((prev) => [...prev, data.message]);
    };

    ws.onclose = () => {
      setIsConnected(false);
    };

    wsRef.current = ws;
  };

  const startProjectGeneration = async () => {
    if (!projectName.trim() || !description.trim()) return;

    try {
      const response = await fetch("http://localhost:8000/start-project", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          project_name: projectName,
          description: description,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setProjectDetails(data);
        connectWebSocket(data);
      }
    } catch (error) {
      console.error("Error starting project generation:", error);
    }
  };

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-100 py-6 flex flex-col justify-center sm:py-12">
      <div className="relative py-3 sm:max-w-xl sm:mx-auto">
        <div className="relative px-4 py-10 bg-white shadow-lg sm:rounded-3xl sm:p-20">
          <div className="max-w-md mx-auto">
            <div className="divide-y divide-gray-200">
              <div className="py-8 text-base leading-6 space-y-4 text-gray-700 sm:text-lg sm:leading-7">
                <h1 className="text-3xl font-bold text-center mb-8 text-gray-900">
                  Next.js Project Generator
                </h1>

                <div className="space-y-4">
                  <div>
                    <label
                      htmlFor="projectName"
                      className="block text-sm font-medium text-gray-700"
                    >
                      Project Name
                    </label>
                    <input
                      type="text"
                      id="projectName"
                      value={projectName}
                      onChange={(e) => setProjectName(e.target.value)}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                      placeholder="Enter project name..."
                    />
                  </div>

                  <div>
                    <label
                      htmlFor="description"
                      className="block text-sm font-medium text-gray-700"
                    >
                      Project Description
                    </label>
                    <textarea
                      id="description"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                      rows={3}
                      placeholder="Enter project description..."
                    />
                  </div>

                  <button
                    onClick={startProjectGeneration}
                    disabled={
                      !projectName.trim() || !description.trim() || isConnected
                    }
                    className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    {isConnected
                      ? "Generating Project..."
                      : "Generate Next.js Project"}
                  </button>

                  {messages.length > 0 && (
                    <div className="mt-6">
                      <h2 className="text-xl font-semibold mb-2">
                        Generation Progress:
                      </h2>
                      <div className="bg-gray-50 p-4 rounded-lg max-h-60 overflow-y-auto">
                        {messages.map((message, index) => (
                          <div key={index} className="py-1">
                            {message}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {projectDetails && !isConnected && (
                    <div className="mt-6 p-4 bg-green-50 rounded-lg">
                      <h2 className="text-xl font-semibold mb-2 text-green-800">
                        Project Generated!
                      </h2>
                      <p className="text-green-700">
                        Your project has been generated successfully. To start
                        the development server, run:
                      </p>
                      <code className="block mt-2 p-2 bg-white rounded text-sm">
                        cd {projectDetails.directory} && npm run dev
                      </code>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
