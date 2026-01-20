// components/CsvViewer.jsx
"use client";

import React, { useState, useEffect } from "react";
import styled from "styled-components";
import Papa from "papaparse"; // <--- Import PapaParse

const CsvViewer = ({ file }) => {
  // <--- Now expects a 'file' prop
  const [parsedData, setParsedData] = useState([]);
  const [headers, setHeaders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!file) {
      setParsedData([]);
      setHeaders([]);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);

    const reader = new FileReader();

    reader.onload = async (event) => {
      const csvText = event.target.result;

      // Use PapaParse to parse the CSV text
      Papa.parse(csvText, {
        header: true, // Treat the first row as headers
        skipEmptyLines: true,
        complete: (results) => {
          if (results.errors.length) {
            setError(`Error parsing CSV: ${results.errors[0].message}`);
            setParsedData([]);
            setHeaders([]);
          } else {
            setParsedData(results.data);
            setHeaders(results.meta.fields || []); // PapaParse returns fields in meta
            if (results.data.length === 0) {
              setError("CSV file is empty or contains no valid data rows.");
            }
          }
          setLoading(false);
        },
        error: (parseError) => {
          setError(`Parsing failed: ${parseError.message}`);
          setLoading(false);
          setParsedData([]);
          setHeaders([]);
        },
      });
    };

    reader.onerror = () => {
      setError("Failed to read file.");
      setLoading(false);
      setParsedData([]);
      setHeaders([]);
    };

    // Read the file as text
    reader.readAsText(file);

    // Cleanup function: If component unmounts or file changes before parsing completes
    return () => {
      reader.abort(); // Abort any ongoing file reading
    };
  }, [file]); // Re-run effect whenever the 'file' prop changes

  if (loading) {
    return <p className="text-white/70 text-center p-4">Loading CSV data...</p>;
  }

  if (error) {
    return <p className="text-red-400 text-center p-4">Error: {error}</p>;
  }

  if (parsedData.length === 0 || headers.length === 0) {
    return (
      <p className="text-white/70 text-center p-4">No CSV data to display.</p>
    );
  }

  return (
    <StyledTableContainer>
      <table className="csv-table">
        <thead>
          <tr>
            {headers.map((header) => (
              <th key={header}>{header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {parsedData.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {headers.map((header) => (
                // Ensure row[header] exists and is converted to string for display
                <td key={`${rowIndex}-${header}`}>
                  {String(row[header] || "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </StyledTableContainer>
  );
};

const StyledTableContainer = styled.div`
  max-height: 95%;
  overflow-y: auto;
  width: 100%;
  border-radius: 8px;
  border: 1px solid rgba(0, 110, 255, 0.15);
  background-color: rgba(0, 0, 0, 0.2);
  color: white;

  .csv-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
    white-space: nowrap;
  }

  .csv-table th,
  .csv-table td {
    padding: 10px 15px;
    text-align: left;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 150px; /* Adjust as needed */
  }

  .csv-table th {
    background-color: rgba(0, 110, 255, 0.1);
    font-weight: bold;
    position: sticky;
    top: 0;
    z-index: 10;
  }

  .csv-table tr:last-child td {
    border-bottom: none;
  }

  .csv-table tbody tr:hover {
    background-color: rgba(0, 110, 255, 0.05);
  }

  /* Scrollbar styling for dark theme */
  ::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }

  ::-webkit-scrollbar-track {
    background: #0d1a2a; /* Dark track */
    border-radius: 10px;
  }

  ::-webkit-scrollbar-thumb {
    background: #4a5d7c; /* Muted scrollbar thumb */
    border-radius: 10px;
  }

  ::-webkit-scrollbar-thumb:hover {
    background: #6a82a6; /* Lighter on hover */
  }
`;

export default CsvViewer;
