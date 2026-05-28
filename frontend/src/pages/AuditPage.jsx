import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import Pagination from '../components/Pagination';
import { History, User, Calendar, Edit2, ShieldAlert, ArrowRight, Check } from 'lucide-react';

const AuditPage = () => {
  const [logs, setLogs] = useState([]);
  const [count, setCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(25);
  const [isLoading, setIsLoading] = useState(true);

  const fetchAuditLogs = async (page = 1) => {
    try {
      setIsLoading(true);
      const params = {
        page,
        page_size: pageSize,
      };
      const response = await apiService.getAuditLogs(params);
      setLogs(response.data.results || response.data);
      setCount(response.data.count || response.data.length || 0);
      setCurrentPage(page);
    } catch (error) {
      console.error("Failed loading audit logs:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditLogs(1);
  }, []);

  // Helpers to get action-specific badges
  const getActionInfo = (action) => {
    switch (action) {
      case 'CREATE':
        return { label: 'Created', color: 'bg-emerald-50 text-emerald-700 border-emerald-100', icon: Check };
      case 'EDIT':
        return { label: 'Edited', color: 'bg-amber-50 text-amber-700 border-amber-100', icon: Edit2 };
      case 'LOCK':
        return { label: 'Locked & Approved', color: 'bg-rose-50 text-rose-700 border-rose-100', icon: ShieldAlert };
      case 'UNLOCK':
        return { label: 'Unlocked', color: 'bg-blue-50 text-blue-700 border-blue-100', icon: History };
      default:
        return { label: action, color: 'bg-slate-50 text-slate-700 border-slate-100', icon: History };
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Info */}
      <div className="flex gap-3 items-center">
        <History className="w-8 h-8 text-slate-700 flex-shrink-0" />
        <div>
          <h1 className="text-2xl font-bold text-slate-800 tracking-tight">System Audit Log</h1>
          <p className="text-slate-500 text-sm mt-0.5">
            Immutable compliance ledger recording all analyst corrections, locks, and approvals.
          </p>
        </div>
      </div>

      {isLoading ? (
        <LoadingSpinner message="Querying audit records..." />
      ) : (
        <div className="space-y-6">
          
          {/* Audit Log Timeline */}
          <div className="relative border-l border-slate-200 ml-4 space-y-8 py-4">
            {logs.length === 0 ? (
              <div className="bg-white border border-slate-200 rounded-xl p-8 text-center text-slate-400 font-medium ml-4">
                No audit events have occurred yet for this tenant.
              </div>
            ) : (
              logs.map((log) => {
                const actionInfo = getActionInfo(log.action);
                const Icon = actionInfo.icon;
                
                return (
                  <div key={log.id} className="relative pl-8">
                    {/* Circle timeline dot */}
                    <span className={`absolute -left-3.5 top-1.5 flex items-center justify-center w-7 h-7 rounded-full border shadow-sm ${actionInfo.color}`}>
                      <Icon className="w-3.5 h-3.5" />
                    </span>

                    {/* Log Card */}
                    <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm max-w-3xl space-y-4">
                      {/* Top metadata header */}
                      <div className="flex flex-col sm:flex-row justify-between sm:items-center border-b border-slate-100 pb-3 gap-2">
                        <div className="flex items-center gap-3">
                          <span className={`px-2 py-0.5 rounded text-xs font-bold border ${actionInfo.color}`}>
                            {actionInfo.label}
                          </span>
                          <span className="text-xs font-mono text-slate-400">
                            Record ID: {log.emission_record.substring(0, 8)}...
                          </span>
                        </div>
                        <div className="flex items-center gap-4 text-xs text-slate-500">
                          <span className="flex items-center gap-1">
                            <User className="w-3.5 h-3.5" />
                            {log.changed_by ? log.changed_by.username : 'System Pipeline'}
                          </span>
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3.5 h-3.5" />
                            {new Date(log.changed_at).toLocaleString()}
                          </span>
                        </div>
                      </div>

                      {/* Diff display for EDIT action */}
                      {log.action === 'EDIT' && log.previous_values && log.new_values && (
                        <div className="space-y-2">
                          <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Historical Field Changes</p>
                          <div className="bg-slate-50 rounded-lg border border-slate-100 p-3 divide-y divide-slate-100 text-xs">
                            {Object.keys(log.previous_values).map((field) => {
                              const prevVal = log.previous_values[field];
                              const newVal = log.new_values[field];
                              
                              if (prevVal === newVal) return null; // No change in this field
                              
                              return (
                                <div key={field} className="grid grid-cols-3 py-2 first:pt-0 last:pb-0 items-center gap-4">
                                  <span className="font-semibold text-slate-600 capitalize">{field.replace('_', ' ')}</span>
                                  <span className="text-rose-600 line-through truncate">{String(prevVal || '—')}</span>
                                  <span className="flex items-center gap-2 text-emerald-600 font-semibold">
                                    <ArrowRight className="w-3 h-3 text-slate-400 flex-shrink-0" />
                                    <span className="truncate">{String(newVal || '—')}</span>
                                  </span>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {/* Info logs for locks */}
                      {log.action === 'LOCK' && (
                        <p className="text-sm text-slate-600 italic">
                          This record was approved and locked to prevent modification in the compliance ledger.
                        </p>
                      )}

                      {/* Info logs for unlocks */}
                      {log.action === 'UNLOCK' && (
                        <p className="text-sm text-slate-600 italic">
                          Record was unlocked to permit corrections on physical parameters.
                        </p>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>

          <Pagination
            currentPage={currentPage}
            count={count}
            pageSize={pageSize}
            onPageChange={fetchAuditLogs}
          />
        </div>
      )}
    </div>
  );
};

export default AuditPage;
