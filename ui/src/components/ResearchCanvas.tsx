"use client";

import React, { useState } from "react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import {
  useCoAgent,
  useCoAgentStateRender,
  useCopilotAction,
} from "@copilotkit/react-core";
import { Progress } from "./Progress";
import { EditResourceDialog } from "./EditResourceDialog";
import { AddResourceDialog } from "./AddResourceDialog";
import { Resources } from "./Resources";
import { AgentState, Resource } from "@/lib/types";
import { useModelSelectorContext } from "@/lib/model-selector-provider";
import { Dialog } from "@headlessui/react"; // Import dialog from Headless UI

export function ResearchCanvas() {
  const { model, agent } = useModelSelectorContext();

  const { state, setState } = useCoAgent<AgentState>({
    name: agent,
    initialState: {
      model,
    },
  });

  const [loading, setLoading] = useState(false);
  const [codelabsLink, setCodelabsLink] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false); // Modal visibility state

  useCoAgentStateRender({
    name: agent,
    render: ({ state, nodeName, status }) => {
      if (!state.logs || state.logs.length === 0) {
        return null;
      }
      return <Progress logs={state.logs} />;
    },
  });

  useCopilotAction({
    name: "DeleteResources",
    disabled: true,
    parameters: [
      {
        name: "urls",
        type: "string[]",
      },
    ],
    renderAndWait: ({ args, status, handler }) => {
      return (
        <div className="">
          <div className="font-bold text-base mb-2">
            Delete these resources?
          </div>
          <Resources
            resources={resources.filter((resource) =>
              (args.urls || []).includes(resource.url)
            )}
            customWidth={200}
          />
          {status === "executing" && (
            <div className="mt-4 flex justify-start space-x-2">
              <button
                onClick={() => handler("NO")}
                className="px-4 py-2 text-[#6766FC] border border-[#6766FC] rounded text-sm font-bold"
              >
                Cancel
              </button>
              <button
                onClick={() => handler("YES")}
                className="px-4 py-2 bg-[#6766FC] text-white rounded text-sm font-bold"
              >
                Delete
              </button>
            </div>
          )}
        </div>
      );
    },
  });

  const resources: Resource[] = state.resources || [];
  const setResources = (resources: Resource[]) => {
    setState({ ...state, resources });
  };

  // const [resources, setResources] = useState<Resource[]>(dummyResources);
  const [newResource, setNewResource] = useState<Resource>({
    url: "",
    title: "",
    description: "",
  });
  const [isAddResourceOpen, setIsAddResourceOpen] = useState(false);

  const addResource = () => {
    if (newResource.url) {
      setResources([...resources, { ...newResource }]);
      setNewResource({ url: "", title: "", description: "" });
      setIsAddResourceOpen(false);
    }
  };

  const removeResource = (url: string) => {
    setResources(
      resources.filter((resource: Resource) => resource.url !== url)
    );
  };

  const [editResource, setEditResource] = useState<Resource | null>(null);
  const [originalUrl, setOriginalUrl] = useState<string | null>(null);
  const [isEditResourceOpen, setIsEditResourceOpen] = useState(false);

  const handleCardClick = (resource: Resource) => {
    setEditResource({ ...resource });
    setOriginalUrl(resource.url);
    setIsEditResourceOpen(true);
  };

  const updateResource = () => {
    if (editResource && originalUrl) {
      setResources(
        resources.map((resource) =>
          resource.url === originalUrl ? { ...editResource } : resource
        )
      );
      setEditResource(null);
      setOriginalUrl(null);
      setIsEditResourceOpen(false);
    }
  };

  // Function to handle exporting the research draft as a PDF
  const exportDraftAsPdf = async () => {
    try {
      const response = await fetch("/api/export/pdf", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ draft: state.report || "" }),
      });

      if (!response.ok) {
        throw new Error("Failed to generate PDF");
      }

      // Convert the response to a Blob for download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);

      // Trigger download of the PDF
      const pdfLink = document.createElement("a");
      pdfLink.href = url;
      pdfLink.download = "research_draft.pdf";
      document.body.appendChild(pdfLink);
      pdfLink.click();
      pdfLink.remove();

      // Clean up the URL object
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Error exporting draft as PDF:", error);
    }
  };

  // Function to handle exporting the research draft as Codelabs
  const exportDraftAsCodelabs = async () => {
    setLoading(true);
    setCodelabsLink(null);

    try {
      const response = await fetch("/api/export/codelabs", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ draft: state.report || "" }),
      });

      if (!response.ok) {
        throw new Error("Failed to generate Codelabs link");
      }

      const data = await response.json();
      setCodelabsLink(data.codelabs_link);
      setIsModalOpen(true); // Open modal when link is ready
    } catch (error) {
      console.error("Error exporting to Codelabs:", error);
      setCodelabsLink("Error generating Codelabs link. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container w-full h-full p-10 bg-[#F5F8FF]">
      <div className="space-y-8">
        <div>
          <h2 className="text-lg font-medium mb-3 text-primary">
            Research Question
          </h2>
          <Input
            placeholder="Enter your research question"
            value={state.research_question || ""}
            onChange={(e) =>
              setState({ ...state, research_question: e.target.value })
            }
            aria-label="Research question"
            className="bg-background px-6 py-8 border-0 shadow-none rounded-xl text-md font-extralight focus-visible:ring-0 placeholder:text-slate-400"
          />
        </div>

        <div>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-medium text-primary">Resources</h2>
            <EditResourceDialog
              isOpen={isEditResourceOpen}
              onOpenChange={setIsEditResourceOpen}
              editResource={editResource}
              setEditResource={setEditResource}
              updateResource={updateResource}
            />
            <AddResourceDialog
              isOpen={isAddResourceOpen}
              onOpenChange={setIsAddResourceOpen}
              newResource={newResource}
              setNewResource={setNewResource}
              addResource={addResource}
            />
          </div>
          {resources.length === 0 && (
            <div className="text-sm text-slate-400">
              Click the button above to add resources.
            </div>
          )}

          {resources.length !== 0 && (
            <Resources
              resources={resources}
              handleCardClick={handleCardClick}
              removeResource={removeResource}
            />
          )}
        </div>

        {/* Research Draft Section */}
        <div className="flex flex-col h-full">
          {/* Heading and Export Button */}
          <div className="flex justify-between items-center mb-3">
            <h2 className="text-lg font-medium text-primary">Research Draft</h2>

            {/* Export Buttons */}
            <div className="space-x-2">
              {/* Export as PDF Button */}
              <Button onClick={exportDraftAsPdf} className="bg-[#6766FC] text-white">
                Export as PDF
              </Button>

              {/* Export as Codelabs Button */}
              <Button onClick={exportDraftAsCodelabs} className="bg-[#6766FC] text-white">
                {loading ? "Exporting..." : "Export as Codelabs"}
              </Button>
            </div>
          </div>

          {/* Textarea for Research Draft */}
          <Textarea
            placeholder="Write your research draft here"
            value={state.report || ""}
            onChange={(e) => setState({ ...state, report: e.target.value })}
            rows={10}
            aria-label="Research draft"
            className="bg-background px-6 py-8 border-0 shadow-none rounded-xl text-md font-extralight focus-visible:ring-0 placeholder:text-slate-400"
            style={{ minHeight: "200px" }}
          />
        </div>

        {/* Modal for displaying Codelabs link */}
        {isModalOpen && (
          <Dialog open={isModalOpen} onClose={() => setIsModalOpen(false)}>
            <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-30">
              <div className="bg-white p-6 rounded-lg max-w-md mx-auto text-center">
                <h2 className="text-lg font-medium mb-4">Codelabs Link</h2>
                {codelabsLink ? (
                  <a
                    href={codelabsLink}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-500 underline"
                  >
                    Open your Codelabs document
                  </a>
                ) : (
                  <p>Generating link, please wait...</p>
                )}
                <div className="mt-4">
                  <Button onClick={() => setIsModalOpen(false)}>Close</Button>
                </div>
              </div>
            </div>
          </Dialog>
        )}
      </div>
    </div>
  );
}
