import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { Users, Server } from 'lucide-react';

const Navbar = () => {
  const [tenantId, setTenantId] = useState(
    localStorage.getItem('activeTenantId') || '11111111-1111-1111-1111-111111111111'
  );
  const [apiStatus, setApiStatus] = useState('checking');

  // Hardcoded seeded Tenants list for easy switching in developer prototype
  const tenants = [
    { id: '11111111-1111-1111-1111-111111111111', name: 'Alpha Corporate Client' },
    { id: '22222222-2222-2222-2222-222222222222', name: 'Beta Industries Group' }
  ];

  useEffect(() => {
    // Save default tenant id if not present
    if (!localStorage.getItem('activeTenantId')) {
      localStorage.setItem('activeTenantId', tenantId);
    }

    // Ping status endpoint
    apiService.getStatus()
      .then(() => setApiStatus('online'))
      .catch(() => setApiStatus('offline'));
  }, []);

  const handleTenantChange = (e) => {
    const newId = e.target.value;
    setTenantId(newId);
    localStorage.setItem('activeTenantId', newId);
    // Reload page to re-trigger API fetches under the new X-Tenant-ID header
    window.location.reload();
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-8 shadow-sm">
      <div className="flex items-center gap-4">
        <h2 className="text-lg font-semibold text-slate-800 tracking-tight">ESG compliance console</h2>
      </div>

      <div className="flex items-center gap-6">
        {/* Tenant Switcher dropdown */}
        <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 shadow-sm text-sm">
          <Users className="w-4 h-4 text-slate-500" />
          <span className="font-medium text-slate-600">Tenant:</span>
          <select
            value={tenantId}
            onChange={handleTenantChange}
            className="bg-transparent border-none text-slate-800 font-semibold focus:outline-none cursor-pointer"
          >
            {tenants.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </div>

        {/* Backend Status indicator */}
        <div className="flex items-center gap-2 text-xs">
          <Server className="w-4 h-4 text-slate-400" />
          <span className="text-slate-500 font-medium">Backend:</span>
          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-semibold ${
            apiStatus === 'online' ? 'bg-emerald-50 text-emerald-700' :
            apiStatus === 'offline' ? 'bg-rose-50 text-rose-700' : 'bg-amber-50 text-amber-700'
          }`}>
            <span className={`w-1.5 h-1.5 rounded-full ${
              apiStatus === 'online' ? 'bg-emerald-500' :
              apiStatus === 'offline' ? 'bg-rose-500' : 'bg-amber-500 animate-pulse'
            }`} />
            {apiStatus.toUpperCase()}
          </span>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
