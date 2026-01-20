"use client";

import React, { useState } from "react";
import { PanelGroup, Panel, PanelResizeHandle } from "react-resizable-panels";
import { ToastContainer, toast } from "react-toastify";
import axios from "axios";
import "react-toastify/dist/ReactToastify.css";
import Form from "../components/form";
import Buttonwow from "../components/submit";
import CsvViewer from "../components/csvviewer.js";
import Loader from "../components/loader.js";

const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;

const Page = () => {
  const [file, setFile] = useState(null);
  const [query, setQuery] = useState("");
  const [output, setOutput] = useState("Output will be shown here");
  const [isfile, setIsfile] = useState(false);
  const [displayedCsvData, setDisplayedCsvData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleUpload = async () => {
    toast.dismiss();

    if (!file) {
      toast.error("Please select a file to upload first!", {
        autoClose: 5000,
        closeButton: true,
      });
      return;
    }

    if (file.type !== "text/csv") {
      toast.error("Please select a CSV file to upload!", {
        autoClose: 5000,
        closeButton: true,
      });
      return;
    }

    if (query === "") {
      toast.warn("Please enter a query to process your data better!");
      return;
    }

    setOutput("");
    setIsLoading(true);

    const uploadToastId = toast.info("Uploading file... Please wait.", {
      autoClose: false,
      closeButton: false,
      isLoading: true,
    });

    const formData = new FormData();
    formData.append("csv_file", file);
    formData.append("query", query);
    setIsfile(true);

    try {
      const response = await axios.post(`${backendUrl}/uploadcsv`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        withCredentials: true,
      });

      if (response.status === 200) {
        const result = response.data;
        toast.update(uploadToastId, {
          render: `Upload successful: ${result.message}`,
          isLoading: false,
          autoClose: 5000,
          closeButton: true,
        });

        console.log("Upload successful:", result);
        setOutput(JSON.stringify(result.processed_data, null, 2));
        setIsLoading(false);
      } else {
        const errorData = response.data;
        toast.update(uploadToastId, {
          render: `Upload failed: ${errorData.detail || response.statusText}`,
          type: toast.TYPE.ERROR,
          isLoading: false,
          autoClose: 5000,
          closeButton: true,
        });

        console.error("Upload failed:", response.status, errorData);
      }
    } catch (error) {
      let errorMessage = "An unknown error occurred during upload.";

      if (axios.isAxiosError(error)) {
        errorMessage = error.response?.data?.detail || error.message;
      } else {
        errorMessage = error.message;
      }

      toast.update(uploadToastId, {
        render: `An error occurred: ${errorMessage}`,
        type: toast.TYPE.ERROR,
        isLoading: false,
        autoClose: 5000,
        closeButton: true,
      });

      console.error("Network error during upload:", error);
      setIsLoading(false);
    }
  };

  const handleFilepresence = () => {
    setDisplayedCsvData(null);
    setIsfile(false);
    setOutput("Output will be shown here");
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen bg-[#0F172A] text-gray-100 p-4">
      <div className="max-w-full mx-auto">
        

        <ToastContainer
          position="top-right"
          autoClose={5000}
          hideProgressBar={false}
          newestOnTop
          closeOnClick
          rtl={false}
          pauseOnFocusLoss
          draggable
          pauseOnHover
          theme="dark"
        />

        <div className="bg-[#1E293B] rounded-xl shadow-xl border border-gray-800">
          <PanelGroup direction="horizontal" className="max-h-[90vh] min-h-[90vh] w-full">
            {/* CSV Upload & Display Panel */}
            <Panel defaultSize={50} minSize={20} className="bg-[#1E293B]">
              <div className="h-full p-4 flex flex-col">
                <div className="mb-2 flex justify-between items-center">
                  <h2 className="text-xl font-semibold text-gray-200">
                    CSV Data
                  </h2>
                  {isfile && (
                    <button
                      className="p-1.5 rounded-md bg-gray-700 hover:bg-gray-600 transition-colors text-white"
                      onClick={handleFilepresence}
                      title="Clear file"
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="h-5 w-5"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M6 18L18 6M6 6l12 12"
                        />
                      </svg>
                    </button>
                  )}
                </div>

                <div className="flex h-full w-full rounded-lg border border-gray-700 bg-[#0F172A]">
                  {!isfile ? (
                    <div className="h-full w-full flex flex-col items-center justify-center p-6">
                      <div className="flex flex-col items-center justify-center max-w-md w-full space-y-4">
                        <Form file={file} setFile={setFile} />
                        <Buttonwow handleUpload={handleUpload} />
                      </div>
                    </div>
                  ) : (
                    <div className="h-[100%] p-4 overflow-x-auto overflow-y-hidden">
                      <CsvViewer file={file} />
                    </div>
                  )}
                </div>
              </div>
            </Panel>

            <PanelResizeHandle className="w-1.5 bg-gray-700 hover:bg-gray-600 transition-colors">
              <div className="h-full flex items-center justify-center">
                <div className="w-0.5 h-10 bg-gray-500 rounded-full"></div>
              </div>
            </PanelResizeHandle>

            {/* Query & Results Panel */}
            <Panel defaultSize={50} minSize={20} className="bg-[#1E293B]">
              <PanelGroup direction="vertical" className="h-full">
                {/* Query Input Panel */}
                <Panel defaultSize={40} minSize={15} className="bg-[#1E293B]">
                  <div className="h-full p-4 flex flex-col">
                    <h2 className="text-xl font-semibold text-gray-200 mb-2">
                      Query
                    </h2>
                    <div className="relative flex-1">
                      <textarea
                        placeholder="Enter your query (e.g., what are the highest sales in the data)"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        className="w-full h-full p-4 bg-[#0F172A] text-gray-100 rounded-lg border border-gray-700 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 resize-none outline-none"
                      ></textarea>
                      <button
                        onClick={handleUpload}
                        className="absolute right-3 top-3 px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white rounded-md shadow-md transition-all transform hover:scale-105"
                      >
                        Run Query
                      </button>
                    </div>
                  </div>
                </Panel>

                <PanelResizeHandle className="h-1.5 bg-gray-700 hover:bg-gray-600 transition-colors">
                  <div className="w-full flex items-center justify-center">
                    <div className="h-0.5 w-10 bg-gray-500 rounded-full"></div>
                  </div>
                </PanelResizeHandle>

                {/* Results Panel */}
                <Panel defaultSize={60} minSize={15} className="bg-[#1E293B]">
                  <div className="h-full p-4 flex flex-col">
                    <h2 className="text-xl font-semibold text-gray-200 mb-2">
                      Results
                    </h2>
                    <div className="relative flex-1 rounded-lg border border-gray-700 bg-[#0F172A] overflow-hidden">
                      {isLoading && (
                        <div className="absolute inset-0 flex items-center justify-center bg-[#0F172A] bg-opacity-80 z-10">
                          <Loader />
                        </div>
                      )}
                      <pre className="h-full p-4 overflow-auto text-sm text-gray-300 whitespace-pre-wrap font-mono">
                        {output}
                      </pre>
                    </div>
                  </div>
                </Panel>
              </PanelGroup>
            </Panel>
          </PanelGroup>
        </div>

        <footer className="mt-6 text-center text-gray-500 text-sm">
          <p>Upload CSV files and analyze them with AI-powered queries</p>
        </footer>
      </div>
    </div>
  );
};

export default Page;
