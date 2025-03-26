import { useState, useEffect, useRef } from "react";

// Update types for the simplified structure
type ToolCall = {
  id: string;
  name: string;
  status: "pending" | "in_progress" | "completed" | "failed";
  details?: string;
  timestamp: string;
  agentId: string;
  isExpanded: boolean;
};

type AgentStatus = {
  id: string;
  name: string;
  status: "pending" | "in_progress" | "completed" | "failed";
  progress: number;
  details?: string;
  toolCalls: ToolCall[];
  isExpanded: boolean;
};

type IterationStatus = {
  id: string;
  number: number;
  status: "pending" | "in_progress" | "completed" | "failed";
  progress: number;
  details?: string;
  agents: AgentStatus[];
  isExpanded: boolean;
};

type ProjectStatus = {
  iterations: IterationStatus[];
  overallStatus: "pending" | "in_progress" | "completed" | "failed";
  overallProgress: number;
};

// Tool Call Component
const ToolCall = ({
  tool,
  onToggleExpand,
}: {
  tool: ToolCall;
  onToggleExpand: (id: string) => void;
}) => {
  return (
    <div className="bg-white rounded shadow-sm mb-2">
      <div
        className="flex items-center space-x-3 p-2 cursor-pointer"
        onClick={() => onToggleExpand(tool.id)}
      >
        <div
          className={`w-2 h-2 rounded-full ${
            tool.status === "completed"
              ? "bg-green-500"
              : tool.status === "in_progress"
              ? "bg-blue-500"
              : tool.status === "failed"
              ? "bg-red-500"
              : "bg-gray-300"
          }`}
        />
        <div className="flex-1">
          <div className="text-sm font-medium">{tool.name}</div>
          {tool.details && !tool.isExpanded && (
            <div className="text-xs text-gray-500 truncate">{tool.details}</div>
          )}
        </div>
        <div className="flex items-center space-x-2">
          <div className="text-xs text-gray-400">{tool.timestamp}</div>
          <svg
            className={`w-4 h-4 transform transition-transform ${
              tool.isExpanded ? "rotate-180" : ""
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </div>
      </div>
      {tool.isExpanded && tool.details && (
        <div className="p-2 bg-gray-50 border-t border-gray-100">
          <div className="text-sm text-gray-600 whitespace-pre-wrap">
            {tool.details}
          </div>
        </div>
      )}
    </div>
  );
};

// Agent Status Component
const AgentStatus = ({
  agent,
  onToggleExpand,
  onToggleTool,
}: {
  agent: AgentStatus;
  onToggleExpand: (id: string) => void;
  onToggleTool: (id: string) => void;
}) => {
  return (
    <div className="bg-white rounded-lg shadow mb-4">
      <div
        className="p-4 cursor-pointer flex items-center justify-between"
        onClick={() => onToggleExpand(agent.id)}
      >
        <div className="flex items-center space-x-3">
          <div
            className={`w-3 h-3 rounded-full ${
              agent.status === "completed"
                ? "bg-green-500"
                : agent.status === "in_progress"
                ? "bg-blue-500"
                : agent.status === "failed"
                ? "bg-red-500"
                : "bg-gray-300"
            }`}
          />
          <div>
            <h3 className="font-semibold text-lg">{agent.name}</h3>
            <p className="text-sm text-gray-500">
              {agent.toolCalls.length} tool{agent.toolCalls.length !== 1 ? "s" : ""}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <span className="text-sm text-gray-500">{agent.progress}%</span>
          <svg
            className={`w-5 h-5 transform transition-transform ${
              agent.isExpanded ? "rotate-180" : ""
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </div>
      </div>

      {agent.isExpanded && (
        <div className="border-t border-gray-200">
          <div className="p-4">
            {agent.details && (
              <p className="text-sm text-gray-600 mb-4">{agent.details}</p>
            )}
            <div className="space-y-2">
              {agent.toolCalls.map((tool) => (
                <ToolCall
                  key={tool.id}
                  tool={tool}
                  onToggleExpand={onToggleTool}
                />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Iteration Status Component
const IterationStatus = ({
  iteration,
  onToggleExpand,
  onToggleAgent,
  onToggleTool,
}: {
  iteration: IterationStatus;
  onToggleExpand: (id: string) => void;
  onToggleAgent: (id: string) => void;
  onToggleTool: (id: string) => void;
}) => {
  return (
    <div className="bg-gray-50 rounded-lg p-4 mb-4">
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => onToggleExpand(iteration.id)}
      >
        <div className="flex items-center space-x-3">
          <div
            className={`w-3 h-3 rounded-full ${
              iteration.status === "completed"
                ? "bg-green-500"
                : iteration.status === "in_progress"
                ? "bg-blue-500"
                : iteration.status === "failed"
                ? "bg-red-500"
                : "bg-gray-300"
            }`}
          />
          <div>
            <h3 className="font-semibold text-lg">
              Iteration {iteration.number}
            </h3>
            <p className="text-sm text-gray-500">
              {iteration.agents.length} agent
              {iteration.agents.length !== 1 ? "s" : ""}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <span className="text-sm text-gray-500">{iteration.progress}%</span>
          <svg
            className={`w-5 h-5 transform transition-transform ${
              iteration.isExpanded ? "rotate-180" : ""
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </div>
      </div>

      {iteration.isExpanded && (
        <div className="mt-4 space-y-4">
          {iteration.details && (
            <p className="text-sm text-gray-600">{iteration.details}</p>
          )}
          {iteration.agents.map((agent) => (
            <AgentStatus
              key={agent.id}
              agent={agent}
              onToggleExpand={onToggleAgent}
              onToggleTool={onToggleTool}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// Project Status Component
const ProjectStatus = ({
  status,
  onToggleIteration,
  onToggleAgent,
  onToggleTool,
}: {
  status: ProjectStatus;
  onToggleIteration: (id: string) => void;
  onToggleAgent: (id: string) => void;
  onToggleTool: (id: string) => void;
}) => {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Project Generation Progress</h2>
        </div>
        <div className="flex items-center space-x-2">
          <div
            className={`w-3 h-3 rounded-full ${
              status.overallStatus === "completed"
                ? "bg-green-500"
                : status.overallStatus === "in_progress"
                ? "bg-blue-500"
                : status.overallStatus === "failed"
                ? "bg-red-500"
                : "bg-gray-300"
            }`}
          />
          <span className="text-sm text-gray-600">
            {status.overallProgress}%
          </span>
        </div>
      </div>

      <div className="space-y-4">
        {status.iterations.map((iteration) => (
          <IterationStatus
            key={iteration.id}
            iteration={iteration}
            onToggleExpand={onToggleIteration}
            onToggleAgent={onToggleAgent}
            onToggleTool={onToggleTool}
          />
        ))}
      </div>
    </div>
  );
};

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

  // Update initial project status
  const [projectStatus, setProjectStatus] = useState<ProjectStatus>({
    iterations: [],
    overallStatus: "pending",
    overallProgress: 0,
  });

  const connectWebSocket = (projectData: {
    project_id: string;
    directory: string;
  }) => {
    const ws = new WebSocket("ws://localhost:8000/ws");

    ws.onopen = () => {
      setIsConnected(true);
      setMessages([]);
      // Reset project status
      setProjectStatus({
        iterations: [],
        overallStatus: "pending",
        overallProgress: 0,
      });
      // Send project details to the WebSocket
      ws.send(JSON.stringify(projectData));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      // Update messages
      setMessages((prev) => [...prev, data.message]);

      // Update project status based on the message type
      if (data.type === "iteration_update") {
        setProjectStatus((prev) => {
          const existingIteration = prev.iterations.find(
            (iter) => iter.id === data.iterationId
          );
          return {
            ...prev,
            iterations: [
              ...prev.iterations.filter((iter) => iter.id !== data.iterationId),
              {
                id: data.iterationId,
                number: data.iterationNumber,
                status: data.status,
                progress: data.progress,
                details: data.details,
                agents: existingIteration?.agents || [],
                isExpanded: existingIteration?.isExpanded || false,
              },
            ],
            overallStatus: data.status,
            overallProgress: data.progress,
          };
        });
      }

      if (data.type === "agent_update") {
        setProjectStatus((prev) => ({
          ...prev,
          iterations: prev.iterations.map((iteration) =>
            iteration.id === data.iterationId
              ? {
                  ...iteration,
                  agents: [
                    ...iteration.agents.filter(
                      (agent) => agent.id !== data.agentId
                    ),
                    {
                      id: data.agentId,
                      name: data.agentName,
                      status: data.status,
                      progress: data.progress,
                      details: data.details,
                      toolCalls:
                        iteration.agents.find(
                          (agent) => agent.id === data.agentId
                        )?.toolCalls || [],
                      isExpanded:
                        iteration.agents.find(
                          (agent) => agent.id === data.agentId
                        )?.isExpanded || false,
                    },
                  ],
                }
              : iteration
          ),
        }));
      }

      if (data.type === "tool_call") {
        setProjectStatus((prev) => ({
          ...prev,
          iterations: prev.iterations.map((iteration) =>
            iteration.id === data.iterationId
              ? {
                  ...iteration,
                  agents: iteration.agents.map((agent) =>
                    agent.id === data.agentId
                      ? {
                          ...agent,
                          toolCalls: [
                            ...agent.toolCalls.filter(
                              (tool) => tool.id !== data.toolId
                            ),
                            {
                              id: data.toolId,
                              name: data.toolName,
                              status: data.status,
                              details: data.details,
                              timestamp: new Date().toLocaleTimeString(),
                              agentId: data.agentId,
                              isExpanded: false,
                            },
                          ],
                        }
                      : agent
                  ),
                }
              : iteration
          ),
        }));
      }
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

  const resetState = () => {
    setProjectName("");
    setDescription("");
    setIsConnected(false);
    setProjectDetails(null);
    setProjectStatus({
      iterations: [],
      overallStatus: "pending",
      overallProgress: 0,
    });
  };

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Add handler for toggling iteration expansion
  const handleToggleIteration = (iterationId: string) => {
    setProjectStatus((prev) => ({
      ...prev,
      iterations: prev.iterations.map((iteration) =>
        iteration.id === iterationId
          ? { ...iteration, isExpanded: !iteration.isExpanded }
          : iteration
      ),
    }));
  };

  // Add handler for toggling agent expansion
  const handleToggleAgent = (agentId: string) => {
    setProjectStatus((prev) => ({
      ...prev,
      iterations: prev.iterations.map((iteration) => ({
        ...iteration,
        agents: iteration.agents.map((agent) =>
          agent.id === agentId
            ? { ...agent, isExpanded: !agent.isExpanded }
            : agent
        ),
      })),
    }));
  };

  // Add handler for toggling tool call expansion
  const handleToggleTool = (toolId: string) => {
    setProjectStatus((prev) => ({
      ...prev,
      iterations: prev.iterations.map((iteration) => ({
        ...iteration,
        agents: iteration.agents.map((agent) => ({
          ...agent,
          toolCalls: agent.toolCalls.map((tool) =>
            tool.id === toolId
              ? { ...tool, isExpanded: !tool.isExpanded }
              : tool
          ),
        })),
      })),
    }));
  };

  // Add a function to check if all agents are completed
  const isProjectComplete = () => {
    return projectStatus.iterations.every((iteration) =>
      iteration.agents.every((agent) => agent.status === "completed")
    );
  };

  return (
    <div className="min-h-screen bg-gray-100 py-6 flex flex-col justify-center sm:py-12">
      <div className="relative py-3 sm:max-w-xl sm:mx-auto">
        <div className="relative px-4 py-10 bg-white shadow-lg sm:rounded-3xl sm:p-20">
          <div className="max-w-md mx-auto">
            <div className="divide-y divide-gray-200">
              <div className="py-8 text-base leading-6 space-y-4 text-gray-700 sm:text-lg sm:leading-7">
                <h1 className="text-3xl font-bold text-center mb-8 text-gray-900">
                  Multi-Agent Next.jsProject Generator
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

                  <div className="flex space-x-4">
                    <button
                      onClick={startProjectGeneration}
                      disabled={
                        !projectName.trim() ||
                        !description.trim() ||
                        isConnected
                      }
                      className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                    >
                      {isConnected
                        ? "Generating Project..."
                        : "Generate Next.js Project"}
                    </button>

                    {isProjectComplete() && (
                      <button
                        onClick={resetState}
                        className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                      >
                        New Project
                      </button>
                    )}
                  </div>

                  {/* Project Status Component */}
                  {isConnected && (
                    <div className="mt-8">
                      <ProjectStatus
                        status={projectStatus}
                        onToggleIteration={handleToggleIteration}
                        onToggleAgent={handleToggleAgent}
                        onToggleTool={handleToggleTool}
                      />
                    </div>
                  )}

                  {/* Project details section */}
                  {isProjectComplete() && projectDetails && (
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
