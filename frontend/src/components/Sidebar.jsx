import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, UploadCloud, ShieldAlert, History, Leaf } from 'lucide-react';

const Sidebar = () => {
  const menuItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Upload CSV', path: '/upload', icon: UploadCloud },
    { name: 'Review Actions', path: '/review', icon: ShieldAlert },
    { name: 'Audit History', path: '/audit', icon: History },
  ];

  return (
    <aside className="w-16 md:w-64 bg-slate-900 text-slate-100 flex flex-col min-h-screen border-r border-slate-800 transition-all duration-300">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-4 md:px-6 border-b border-slate-800 gap-3 overflow-hidden">
        <Leaf className="w-6 h-6 text-emerald-400 flex-shrink-0" />
        <span className="hidden md:inline font-semibold text-lg tracking-wide bg-gradient-to-r from-emerald-400 to-teal-200 bg-clip-text text-transparent whitespace-nowrap animate-fade-in">
          ESG Ingestion
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-6 px-2 md:px-4 space-y-1.5">
        {menuItems.map((item) => (
          <NavLink
            key={item.name}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center justify-center md:justify-start gap-3 px-3 md:px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-950/20'
                  : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-100'
              }`
            }
            title={item.name}
          >
            <item.icon className="w-5 h-5 flex-shrink-0" />
            <span className="hidden md:inline whitespace-nowrap">{item.name}</span>
          </NavLink>
        ))}
      </nav>

      {/* Footer Info */}
      <div className="p-4 border-t border-slate-800 text-[10px] md:text-xs text-slate-500 overflow-hidden text-center md:text-left">
        <p className="font-semibold text-slate-400 hidden md:block">Auditor Console</p>
        <p className="mt-0.5 whitespace-nowrap text-slate-600"><span className="hidden md:inline">V1.0.0 • </span>SQLite</p>
      </div>
    </aside>
  );
};

export default Sidebar;
