import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

const Pagination = ({ currentPage, count, pageSize, onPageChange }) => {
  const totalPages = Math.ceil(count / pageSize) || 1;
  const startIdx = count === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const endIdx = Math.min(currentPage * pageSize, count);

  return (
    <div className="flex items-center justify-between px-6 py-4 bg-white border-t border-slate-200">
      {/* Row range indicators */}
      <div className="text-sm text-slate-500">
        Showing <span className="font-semibold text-slate-700">{startIdx}</span> to{' '}
        <span className="font-semibold text-slate-700">{endIdx}</span> of{' '}
        <span className="font-semibold text-slate-700">{count}</span> records
      </div>

      {/* Toggles */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="p-1.5 rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-50 disabled:opacity-50 disabled:hover:bg-transparent transition-colors"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>

        <span className="text-sm font-semibold text-slate-700">
          Page {currentPage} of {totalPages}
        </span>

        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="p-1.5 rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-50 disabled:opacity-50 disabled:hover:bg-transparent transition-colors"
        >
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};

export default Pagination;
