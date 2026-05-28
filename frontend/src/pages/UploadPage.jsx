import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import UploadDropzone from '../components/UploadDropzone';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import { RefreshCw, FileText, AlertTriangle } from 'lucide-react';

const UploadPage = () => {
  const [batches, setBatches] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [batchSummary, setBatchSummary] = useState(null);

  const fetchBatches = async () => {
    try {
      setIsLoading(true);
      const response = await apiService.getBatches();
      setBatches(response.data.results || response.data);
    } catch (error) {
      console.error("Failed fetching batches:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchBatches();
  }, []);

  const handleUpload = async (file, sourceType) => {
    setIsUploading(true);
    setUploadError(null);
    setUploadSuccess(false);
    setBatchSummary(null);

    try {
      const response = await apiService.uploadBatch(file, sourceType);
      setUploadSuccess(true);
      setBatchSummary(response.data);
      fetchBatches(); // Refresh table
    } catch (error) {
      console.error("Upload error:", error);
      const errMsg = error.response?.data?.error_summary || error.response?.data?.error || "An unknown network error occurred.";
      setUploadError(errMsg);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Title Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-800 tracking-tight">Ingest CSV Activity Data</h1>
        <p className="text-slate-500 text-sm mt-0.5">
          Upload activity logs. Supported sources: SAP Fuels, Electricity Utilities, and Expedia Travel.
        </p>
      </div>

      {/* Upload Dropzone Container */}
      <UploadDropzone
        onUpload={handleUpload}
        isUploading={isUploading}
        uploadError={uploadError}
        uploadSuccess={uploadSuccess}
        batchSummary={batchSummary}
      />

      {/* Upload History list */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
            <FileText className="w-5 h-5 text-slate-500" />
            <span>Ingestion Batch History</span>
          </h3>
          <button
            onClick={fetchBatches}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Reload History
          </button>
        </div>

        {isLoading ? (
          <LoadingSpinner message="Fetching batch records..." />
        ) : (
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider">
                    <th className="px-6 py-3">Created At</th>
                    <th className="px-6 py-3">File Name</th>
                    <th className="px-6 py-3">Source Name</th>
                    <th className="px-6 py-3">Status</th>
                    <th className="px-6 py-3 text-center">Total Rows</th>
                    <th className="px-6 py-3 text-center">Clean Rows</th>
                    <th className="px-6 py-3 text-center">Suspicious Rows</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-sm">
                  {batches.length === 0 ? (
                    <tr>
                      <td colSpan="7" className="px-6 py-8 text-center text-slate-400">
                        No files uploaded yet for this tenant.
                      </td>
                    </tr>
                  ) : (
                    batches.map((b) => (
                      <tr key={b.id} className="hover:bg-slate-50/50 transition-colors">
                        <td className="px-6 py-4 text-slate-500">
                          {new Date(b.created_at).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 font-semibold text-slate-800">{b.file_name}</td>
                        <td className="px-6 py-4 text-slate-600">{b.data_source_name}</td>
                        <td className="px-6 py-4">
                          <StatusBadge type="batch-status" value={b.status} />
                        </td>
                        <td className="px-6 py-4 text-center font-semibold text-slate-800">
                          {b.total_rows}
                        </td>
                        <td className="px-6 py-4 text-center text-emerald-600 font-bold">
                          {b.processed_rows}
                        </td>
                        <td className={`px-6 py-4 text-center font-bold ${
                          b.failed_rows > 0 ? 'text-rose-600 bg-rose-50/20' : 'text-slate-400'
                        }`}>
                          {b.failed_rows}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default UploadPage;
