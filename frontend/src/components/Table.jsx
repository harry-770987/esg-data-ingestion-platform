import React from 'react';
import StatusBadge from './StatusBadge';
import { Eye, Edit, ShieldAlert } from 'lucide-react';

const Table = ({ records, onActionClick }) => {
  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider">
              <th className="px-6 py-4">Transaction Date</th>
              <th className="px-6 py-4">Activity Type</th>
              <th className="px-6 py-4">Scope</th>
              <th className="px-6 py-4">Raw Quantity</th>
              <th className="px-6 py-4">Normalized Quantity</th>
              <th className="px-6 py-4">Quality State</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4 text-right">Actions</th>
            </tr>
          </thead>
          
          <tbody className="divide-y divide-slate-100 text-sm">
            {records.length === 0 ? (
              <tr>
                <td colSpan="8" className="px-6 py-16 text-center">
                  <div className="flex flex-col items-center justify-center space-y-3 max-w-sm mx-auto">
                    <div className="p-3 bg-slate-100 rounded-full text-slate-400">
                      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                      </svg>
                    </div>
                    <h3 className="text-sm font-semibold text-slate-700">No Matching Emission Records</h3>
                    <p className="text-xs text-slate-400 leading-relaxed">
                      We couldn't find any records matching your active filters. Try clearing your filters or uploading a new data batch.
                    </p>
                  </div>
                </td>
              </tr>
            ) : (
              records.map((r) => (
                <tr 
                  key={r.id} 
                  className={`transition-colors border-l-4 ${
                    r.suspicious 
                      ? 'bg-rose-50/40 hover:bg-rose-50/70 border-l-rose-500' 
                      : 'hover:bg-slate-50/60 border-l-transparent'
                  }`}
                >
                  {/* Transaction Date */}
                  <td className="px-6 py-4 font-medium text-slate-800 whitespace-nowrap">
                    {r.transaction_date}
                  </td>
                  
                  {/* Activity Type */}
                  <td className="px-6 py-4 font-semibold text-slate-700 whitespace-nowrap">
                    {r.activity_type}
                  </td>
                  
                  {/* Scope Badge */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <StatusBadge type="scope" value={r.scope} />
                  </td>
                  
                  {/* Raw Quantity */}
                  <td className="px-6 py-4 text-slate-600 whitespace-nowrap">
                    {Number(r.quantity).toLocaleString()} <span className="text-xs text-slate-400 font-medium">{r.unit}</span>
                  </td>
                  
                  {/* Normalized Quantity */}
                  <td className="px-6 py-4 font-mono font-semibold text-slate-800 whitespace-nowrap">
                    {r.normalized_quantity !== null 
                      ? `${Number(r.normalized_quantity).toLocaleString(undefined, {minimumFractionDigits: 2})} ${r.normalized_unit}` 
                      : '—'}
                  </td>
                  
                  {/* Quality Warnings */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <StatusBadge type="suspicious" value={r.suspicious} />
                  </td>
                  
                  {/* Locked/Approved Badges */}
                  <td className="px-6 py-4 whitespace-nowrap space-y-1">
                    <div className="flex gap-1.5 flex-wrap">
                      <StatusBadge type="approved" value={r.approved} />
                      <StatusBadge type="lock" value={r.locked} />
                    </div>
                  </td>
                  
                  {/* Row Actions */}
                  <td className="px-6 py-4 text-right whitespace-nowrap text-xs font-semibold">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => onActionClick(r)}
                        className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg border transition-colors ${
                          r.suspicious 
                            ? 'bg-rose-50 border-rose-200 text-rose-700 hover:bg-rose-100/60'
                            : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100/60 hover:text-slate-800'
                        }`}
                      >
                        {r.suspicious ? (
                          <>
                            <ShieldAlert className="w-3.5 h-3.5" />
                            <span>Audit Row</span>
                          </>
                        ) : (
                          <>
                            <Edit className="w-3.5 h-3.5" />
                            <span>Edit / Action</span>
                          </>
                        )}
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Table;
