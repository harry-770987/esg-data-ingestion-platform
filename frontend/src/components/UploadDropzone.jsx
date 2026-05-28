import React, { useState, useRef } from 'react';
import { Upload, FileText, CheckCircle2, AlertCircle } from 'lucide-react';

const UploadDropzone = ({ onUpload, isUploading, uploadError, uploadSuccess, batchSummary }) => {
  const [file, setFile] = useState(null);
  const [sourceType, setSourceType] = useState('SAP_FUEL');
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const sourceTypes = [
    { id: 'SAP_FUEL', label: 'SAP Fuel Procurement (Scope 1)' },
    { id: 'UTILITY_ELEC', label: 'Utility Electricity Bills (Scope 2)' },
    { id: 'TRAVEL_CORP', label: 'Corporate Travel Portal Exports (Scope 3)' },
  ];

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleButtonClick = () => {
    fileInputRef.current.click();
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!file || !sourceType) return;
    onUpload(file, sourceType);
  };

  return (
    <div className="max-w-xl mx-auto bg-white border border-slate-200 rounded-xl p-8 shadow-sm">
      <form onSubmit={handleSubmit} className="space-y-6">
        
        {/* Source Type Selection */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Select Ingestion Target Category
          </label>
          <select
            value={sourceType}
            onChange={(e) => setSourceType(e.target.value)}
            disabled={isUploading}
            className="w-full bg-slate-50 border border-slate-200 text-slate-800 rounded-lg px-4 py-2.5 font-medium text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none transition-shadow"
          >
            {sourceTypes.map((st) => (
              <option key={st.id} value={st.id}>
                {st.label}
              </option>
            ))}
          </select>
        </div>

        {/* File Drag Box */}
        <div
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={handleButtonClick}
          className={`relative border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center cursor-pointer transition-all duration-200 ${
            dragActive ? 'border-emerald-500 bg-emerald-50/50' : 'border-slate-300 hover:border-emerald-500 hover:bg-slate-50/50'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleChange}
            disabled={isUploading}
            className="hidden"
          />

          {!file ? (
            <>
              <Upload className="w-12 h-12 text-slate-400 mb-3" />
              <p className="text-sm font-semibold text-slate-700 mb-1">
                Drag and drop your export CSV here, or click to browse
              </p>
              <p className="text-xs text-slate-400">CSV files only (up to 50MB)</p>
            </>
          ) : (
            <div className="flex items-center gap-3">
              <FileText className="w-10 h-10 text-emerald-600" />
              <div className="text-left">
                <p className="text-sm font-semibold text-slate-800">{file.name}</p>
                <p className="text-xs text-slate-500">{(file.size / 1024).toFixed(1)} KB</p>
              </div>
            </div>
          )}
        </div>

        {/* Status Responses */}
        {uploadError && (
          <div className="flex gap-2.5 bg-rose-50 border border-rose-100 rounded-lg p-4 text-rose-800 text-sm">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <div>
              <p className="font-semibold">Ingestion Failed</p>
              <p className="text-xs text-rose-700 mt-0.5">{uploadError}</p>
            </div>
          </div>
        )}

        {uploadSuccess && (
          <div className="flex gap-2.5 bg-emerald-50 border border-emerald-100 rounded-lg p-4 text-emerald-800 text-sm">
            <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
            <div>
              <p className="font-semibold">Ingestion Completed Successfully</p>
              {batchSummary && (
                <div className="text-xs text-emerald-700 mt-1 space-y-1">
                  <p>Batch ID: <code className="bg-emerald-100 px-1 py-0.5 rounded font-mono">{batchSummary.id}</code></p>
                  <p>Total rows processed: <span className="font-bold">{batchSummary.total_rows}</span></p>
                  <p>Successfully loaded: <span className="font-bold">{batchSummary.processed_rows}</span></p>
                  <p>Suspicious (Warnings): <span className="font-bold text-amber-700">{batchSummary.failed_rows}</span></p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Submit Action Button */}
        <button
          type="submit"
          disabled={!file || isUploading}
          className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2.5 px-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 disabled:opacity-50 disabled:hover:bg-emerald-600 transition-all shadow-md shadow-emerald-700/10 text-sm"
        >
          {isUploading ? 'Ingesting Payload...' : 'Start Ingestion Pipeline'}
        </button>

      </form>
    </div>
  );
};

export default UploadDropzone;
