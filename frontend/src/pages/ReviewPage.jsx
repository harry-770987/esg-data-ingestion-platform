import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import Table from '../components/Table';
import Pagination from '../components/Pagination';
import Modal from '../components/Modal';
import LoadingSpinner from '../components/LoadingSpinner';
import StatusBadge from '../components/StatusBadge';
import { ShieldAlert, Save, Lock, Unlock, ClipboardList, CheckCircle2 } from 'lucide-react';

const ReviewPage = () => {
  const [records, setRecords] = useState([]);
  const [count, setCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(25);
  const [isLoading, setIsLoading] = useState(true);

  // Modal States for detail audit
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editForm, setEditForm] = useState({
    quantity: '',
    unit: '',
    activity_type: '',
    transaction_date: '',
  });
  const [auditComment, setAuditComment] = useState('');
  const [modalError, setModalError] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [successNotification, setSuccessNotification] = useState(null);

  const showSuccess = (message) => {
    setSuccessNotification(message);
    setTimeout(() => {
      setSuccessNotification(null);
    }, 4000);
  };

  const fetchSuspiciousRecords = async (page = 1) => {
    try {
      setIsLoading(true);
      const params = {
        page,
        page_size: pageSize,
      };
      const response = await apiService.getSuspiciousRecords(params);
      setRecords(response.data.results || response.data);
      setCount(response.data.count || response.data.length || 0);
      setCurrentPage(page);
    } catch (error) {
      console.error("Failed to load suspicious records:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSuspiciousRecords(1);
  }, []);

  const handleActionClick = (record) => {
    setSelectedRecord(record);
    setEditForm({
      quantity: record.quantity,
      unit: record.unit,
      activity_type: record.activity_type,
      transaction_date: record.transaction_date,
    });
    setAuditComment('');
    setModalError(null);
    setIsModalOpen(true);
  };

  const handleFormChange = (e) => {
    const { name, value } = e.target;
    setEditForm(prev => ({ ...prev, [name]: value }));
  };

  const handleSaveEdit = async (e) => {
    e.preventDefault();
    if (!selectedRecord) return;
    setIsSaving(true);
    setModalError(null);

    try {
      const response = await apiService.patchRecord(selectedRecord.id, editForm);
      setSelectedRecord(response.data);
      fetchSuspiciousRecords(currentPage);
      showSuccess("Record corrections saved successfully!");
    } catch (error) {
      console.error("Save error:", error);
      const errMsg = error.response?.data?.quantity?.[0] || error.response?.data?.detail || "Validation failed.";
      setModalError(errMsg);
    } finally {
      setIsSaving(false);
    }
  };

  const handleApprove = async () => {
    if (!selectedRecord) return;
    setIsSaving(true);
    setModalError(null);
    try {
      const response = await apiService.approveRecord(selectedRecord.id, auditComment);
      setSelectedRecord(response.data);
      fetchSuspiciousRecords(currentPage);
      setIsModalOpen(false);
      showSuccess("Record approved and locked for auditing!");
    } catch (error) {
      setModalError(error.response?.data?.detail || "Could not approve record.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleReject = async () => {
    if (!selectedRecord) return;
    setIsSaving(true);
    setModalError(null);
    try {
      const response = await apiService.rejectRecord(selectedRecord.id, auditComment);
      setSelectedRecord(response.data);
      fetchSuspiciousRecords(currentPage);
      setIsModalOpen(false);
      showSuccess("Record rejected and returned to pending review.");
    } catch (error) {
      setModalError(error.response?.data?.detail || "Could not reject record.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleUnlock = async () => {
    if (!selectedRecord) return;
    setIsSaving(true);
    setModalError(null);
    try {
      const response = await apiService.unlockRecord(selectedRecord.id);
      setSelectedRecord(response.data);
      setEditForm({
        quantity: response.data.quantity,
        unit: response.data.unit,
        activity_type: response.data.activity_type,
        transaction_date: response.data.transaction_date,
      });
      fetchSuspiciousRecords(currentPage);
      showSuccess("Record unlocked. Physical parameters can now be modified.");
    } catch (error) {
      setModalError(error.response?.data?.detail || "Could not unlock record.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Info */}
      <div className="flex gap-3 items-center">
        <ShieldAlert className="w-8 h-8 text-rose-500 flex-shrink-0" />
        <div>
          <h1 className="text-2xl font-bold text-slate-800 tracking-tight">Suspicious Records Review</h1>
          <p className="text-slate-500 text-sm mt-0.5">
            Compliance inbox. Inspect and resolve records flagged as suspicious or containing outlier parameters.
          </p>
        </div>
      </div>

      {/* Success Notification Banner */}
      {successNotification && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg p-4 flex items-center justify-between shadow-sm transition-all duration-300">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
            <span>{successNotification}</span>
          </div>
          <button 
            onClick={() => setSuccessNotification(null)}
            className="text-emerald-500 hover:text-emerald-700 text-xs font-bold px-1 focus:outline-none"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Warning summary banner */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-5 text-sm text-amber-800">
        <p className="font-semibold">Compliance Instructions</p>
        <p className="text-xs text-amber-700 mt-1">
          Each record listed below has failed one or more pipeline assertions (bounds check, date validations, or MAD outlier checks).
          Review the parameters, click <strong>Audit Row</strong>, input comments, and either edit values to make them clean or manually approve them with comment exceptions.
        </p>
      </div>

      {/* Main Table */}
      {isLoading ? (
        <LoadingSpinner message="Filtering validation alarms..." />
      ) : (
        <div className="space-y-4">
          <Table records={records} onActionClick={handleActionClick} />
          <Pagination
            currentPage={currentPage}
            count={count}
            pageSize={pageSize}
            onPageChange={fetchSuspiciousRecords}
          />
        </div>
      )}

      {/* Reused Audit Workflow Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={`Compliance Audit - Suspect Row Verification`}
      >
        {selectedRecord && (
          <div className="space-y-6">
            {/* Record Summary Headers */}
            <div className="grid grid-cols-2 gap-4 bg-slate-50 p-4 border border-slate-100 rounded-lg text-xs font-semibold">
              <div>
                <p className="text-slate-400">CATEGORY</p>
                <p className="text-slate-800 mt-0.5">{selectedRecord.category}</p>
              </div>
              <div>
                <p className="text-slate-400">SCOPE</p>
                <div className="mt-0.5">
                  <StatusBadge type="scope" value={selectedRecord.scope} />
                </div>
              </div>
              <div className="col-span-2 pt-2 border-t border-slate-200">
                <p className="text-slate-400">SOURCE ORIGIN</p>
                <p className="text-slate-800 mt-0.5">{selectedRecord.data_source_name}</p>
              </div>
            </div>

            {/* Suspicious warning box */}
            <div className="flex gap-2.5 bg-rose-50 border border-rose-100 rounded-lg p-4 text-rose-800 text-sm">
              <ShieldAlert className="w-5 h-5 flex-shrink-0" />
              <div>
                <p className="font-semibold">Validation Anomalies Detected</p>
                <ul className="list-disc list-inside text-xs text-rose-700 mt-1 space-y-0.5">
                  {selectedRecord.suspicious_reasons.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            </div>

            {modalError && (
              <div className="bg-rose-50 border border-rose-200 rounded-lg p-3 text-rose-800 text-xs font-semibold">
                Error: {modalError}
              </div>
            )}

            {/* Edit Form */}
            <form onSubmit={handleSaveEdit} className="space-y-4">
              <h4 className="text-sm font-bold text-slate-800 border-b border-slate-100 pb-1">
                {selectedRecord.locked ? 'Physical Parameters (Read-Only)' : 'Edit Physical Parameters'}
              </h4>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1">Transaction Date</label>
                  <input
                    type="date"
                    name="transaction_date"
                    value={editForm.transaction_date}
                    onChange={handleFormChange}
                    disabled={selectedRecord.locked || isSaving}
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 focus:ring-1 focus:ring-emerald-500 disabled:opacity-75 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1">Activity Type</label>
                  <input
                    type="text"
                    name="activity_type"
                    value={editForm.activity_type}
                    onChange={handleFormChange}
                    disabled={selectedRecord.locked || isSaving}
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 focus:ring-1 focus:ring-emerald-500 disabled:opacity-75 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1">Raw Quantity</label>
                  <input
                    type="number"
                    step="any"
                    name="quantity"
                    value={editForm.quantity}
                    onChange={handleFormChange}
                    disabled={selectedRecord.locked || isSaving}
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 focus:ring-1 focus:ring-emerald-500 disabled:opacity-75 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1">Raw Unit</label>
                  <input
                    type="text"
                    name="unit"
                    value={editForm.unit}
                    onChange={handleFormChange}
                    disabled={selectedRecord.locked || isSaving}
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 focus:ring-1 focus:ring-emerald-500 disabled:opacity-75 focus:outline-none"
                  />
                </div>
              </div>

              {!selectedRecord.locked && (
                <div className="flex justify-end pt-2">
                  <button
                    type="submit"
                    disabled={isSaving}
                    className="flex items-center gap-1.5 bg-slate-800 hover:bg-slate-900 text-white font-bold py-2 px-4 rounded-lg text-xs disabled:opacity-50 transition-colors"
                  >
                    <Save className="w-4 h-4" /> Save Corrections
                  </button>
                </div>
              )}
            </form>

            {/* Workflow Review */}
            <div className="pt-4 border-t border-slate-100 space-y-4">
              <h4 className="text-sm font-bold text-slate-800 flex items-center gap-1.5">
                {selectedRecord.locked ? <Lock className="w-4 h-4 text-rose-500" /> : <ClipboardList className="w-4 h-4 text-emerald-500" />}
                <span>Review & Sign-Off Workflow</span>
              </h4>

              {selectedRecord.locked ? (
                <div className="bg-rose-50/50 border border-rose-100 rounded-lg p-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 text-xs">
                  <div>
                    <p className="font-bold text-rose-800">Record Immutable (Locked)</p>
                    <p className="text-rose-700 mt-0.5">This record has been signed off and is locked.</p>
                  </div>
                  <button
                    onClick={handleUnlock}
                    disabled={isSaving}
                    className="flex items-center gap-1.5 bg-rose-600 hover:bg-rose-700 text-white font-bold py-2 px-4 rounded-lg disabled:opacity-50 transition-colors whitespace-nowrap"
                  >
                    <Unlock className="w-3.5 h-3.5" /> Unlock Record
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 mb-1">Auditor Comments (Optional)</label>
                    <textarea
                      value={auditComment}
                      onChange={(e) => setAuditComment(e.target.value)}
                      placeholder="Specify comments or explanations for the verification ledger..."
                      rows="2"
                      disabled={isSaving}
                      className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 focus:ring-1 focus:ring-emerald-500 focus:outline-none"
                    />
                  </div>

                  <div className="flex justify-end gap-3 text-xs font-bold">
                    <button
                      onClick={handleReject}
                      disabled={isSaving}
                      className="bg-rose-50 hover:bg-rose-100/70 border border-rose-200 text-rose-700 py-2 px-4 rounded-lg transition-colors"
                    >
                      Reject Record
                    </button>
                    <button
                      onClick={handleApprove}
                      disabled={isSaving}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white py-2 px-4 rounded-lg shadow-md shadow-emerald-700/10 transition-colors"
                    >
                      Approve & Lock Record
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Raw data */}
            <div className="pt-4 border-t border-slate-100">
              <details className="text-xs">
                <summary className="font-semibold text-slate-400 cursor-pointer hover:text-slate-600">
                  View Raw CSV Ingestion Payload (JSONB)
                </summary>
                <pre className="bg-slate-50 border border-slate-100 rounded-lg p-3 font-mono text-[10px] text-slate-700 overflow-x-auto mt-2 max-h-40">
                  {JSON.stringify(selectedRecord.raw_data, null, 2)}
                </pre>
              </details>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default ReviewPage;
