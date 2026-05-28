import React from 'react';

const RecordCard = ({ title, value, subtext, icon: Icon, color = 'emerald' }) => {
  const colorMap = {
    emerald: 'bg-emerald-50 text-emerald-600 border-emerald-100',
    rose: 'bg-rose-50 text-rose-600 border-rose-100 animate-pulse',
    amber: 'bg-amber-50 text-amber-600 border-amber-100',
    indigo: 'bg-indigo-50 text-indigo-600 border-indigo-100',
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex items-center justify-between transition-transform duration-200 hover:-translate-y-0.5">
      <div className="space-y-1">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{title}</p>
        <p className="text-2xl font-bold text-slate-800 tracking-tight">{value}</p>
        {subtext && <p className="text-xs text-slate-500 font-medium">{subtext}</p>}
      </div>
      
      <div className={`p-3 rounded-xl border ${colorMap[color] || colorMap.emerald}`}>
        {Icon && <Icon className="w-6 h-6" />}
      </div>
    </div>
  );
};

export default RecordCard;
