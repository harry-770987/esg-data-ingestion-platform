import React from 'react';
import { Lock, Unlock, AlertTriangle, CheckCircle, Clock, XCircle } from 'lucide-react';

const StatusBadge = ({ type, value }) => {
  const normalizedVal = String(value).toUpperCase();

  // 1. Ingestion / Batch Statuses
  if (type === 'batch-status') {
    switch (normalizedVal) {
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle className="w-3.5 h-3.5" /> COMPLETED
          </span>
        );
      case 'PROCESSING':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200 animate-pulse">
            <Clock className="w-3.5 h-3.5" /> PROCESSING
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <XCircle className="w-3.5 h-3.5" /> FAILED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-50 text-slate-600 border border-slate-200">
            {normalizedVal}
          </span>
        );
    }
  }

  // 2. Lock Statuses
  if (type === 'lock') {
    return value ? (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-xs font-bold bg-rose-50 text-rose-700 border border-rose-100">
        <Lock className="w-3.5 h-3.5" /> Locked
      </span>
    ) : (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-200">
        <Unlock className="w-3.5 h-3.5" /> Unlocked
      </span>
    );
  }

  // 3. Approval Statuses
  if (type === 'approved') {
    return value ? (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-100">
        Approved
      </span>
    ) : (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-100">
        Pending Review
      </span>
    );
  }

  // 4. Suspicious Flags
  if (type === 'suspicious') {
    return value ? (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-100 animate-pulse">
        <AlertTriangle className="w-3 h-3" /> Suspicious
      </span>
    ) : (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-100">
        Verified Clean
      </span>
    );
  }

  // 5. Emission Scopes
  if (type === 'scope') {
    const scopeVal = parseInt(value);
    switch (scopeVal) {
      case 1:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-100">
            Scope 1 (Direct)
          </span>
        );
      case 2:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-sky-50 text-sky-700 border border-sky-100">
            Scope 2 (Indirect)
          </span>
        );
      case 3:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-100">
            Scope 3 (Travel)
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-slate-100 text-slate-700">
            Scope {value}
          </span>
        );
    }
  }

  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-800">
      {value}
    </span>
  );
};

export default StatusBadge;
