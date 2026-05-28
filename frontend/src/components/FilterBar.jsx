import React from 'react';
import { Search, Filter, RotateCcw } from 'lucide-react';

const FilterBar = ({ filters, onFilterChange, onReset }) => {
  const handleChange = (e) => {
    const { name, value } = e.target;
    onFilterChange(name, value);
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
      {/* Header Info */}
      <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
        <Filter className="w-4 h-4 text-slate-500" />
        <span>Filter Emission Records</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {/* Search Input */}
        <div className="relative col-span-1 md:col-span-2">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
          <input
            type="text"
            name="activity_type"
            value={filters.activity_type || ''}
            onChange={handleChange}
            placeholder="Search activity type (e.g. diesel)..."
            className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-4 py-2 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
          />
        </div>

        {/* Source Type Filter */}
        <div>
          <select
            name="source_type"
            value={filters.source_type || ''}
            onChange={handleChange}
            className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
          >
            <option value="">All Sources</option>
            <option value="SAP_FUEL">SAP Fuel</option>
            <option value="UTILITY_ELEC">Utility Elec</option>
            <option value="TRAVEL_CORP">Travel Corp</option>
          </select>
        </div>

        {/* Scope Filter */}
        <div>
          <select
            name="scope"
            value={filters.scope || ''}
            onChange={handleChange}
            className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
          >
            <option value="">All Scopes</option>
            <option value="1">Scope 1</option>
            <option value="2">Scope 2</option>
            <option value="3">Scope 3</option>
          </select>
        </div>

        {/* Suspicious Filter */}
        <div>
          <select
            name="suspicious"
            value={filters.suspicious || ''}
            onChange={handleChange}
            className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
          >
            <option value="">Suspicion State</option>
            <option value="true">Suspicious Only</option>
            <option value="false">Clean Only</option>
          </select>
        </div>

        {/* Approved Filter */}
        <div>
          <select
            name="approved"
            value={filters.approved || ''}
            onChange={handleChange}
            className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
          >
            <option value="">Approval Status</option>
            <option value="true">Approved</option>
            <option value="false">Pending Review</option>
          </select>
        </div>
      </div>

      {/* Date Ranges & Reset Toggles */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center pt-2 border-t border-slate-100 gap-4">
        <div className="flex items-center gap-2.5 text-xs text-slate-500">
          <span>Date Range:</span>
          <input
            type="date"
            name="start_date"
            value={filters.start_date || ''}
            onChange={handleChange}
            className="bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />
          <span>to</span>
          <input
            type="date"
            name="end_date"
            value={filters.end_date || ''}
            onChange={handleChange}
            className="bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />
        </div>

        <button
          onClick={onReset}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50 hover:text-slate-800 transition-colors"
        >
          <RotateCcw className="w-3.5 h-3.5" /> Reset Filters
        </button>
      </div>

    </div>
  );
};

export default FilterBar;
