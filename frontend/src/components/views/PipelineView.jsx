import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { Briefcase, Users, Plus, Clock } from 'lucide-react';

const JOB_STAGES = ['applied', 'oa_test', 'interview', 'offer', 'rejected'];
const CRM_STAGES = ['New', 'Contacted', 'Proposal', 'Won', 'Lost'];

export default function PipelineView() {
  const { jobs, jobStats, jobFollowups, fetchJobs, leads, fetchLeads, showToast } = useApp();

  const [showJobModal, setShowJobModal] = useState(false);
  const [showLeadModal, setShowLeadModal] = useState(false);

  // Job Form State
  const [jobCompany, setJobCompany] = useState('');
  const [jobRole, setJobRole] = useState('');
  const [jobPlatform, setJobPlatform] = useState('');
  const [jobNotes, setJobNotes] = useState('');

  // Lead Form State
  const [leadName, setLeadName] = useState('');
  const [leadCompany, setLeadCompany] = useState('');
  const [leadDealValue, setLeadDealValue] = useState('');
  const [leadPhone, setLeadPhone] = useState('');
  const [leadEmail, setLeadEmail] = useState('');
  const [leadNotes, setLeadNotes] = useState('');

  // Handle Log Job Submit
  async function handleLogJob(e) {
    e.preventDefault();
    try {
      const res = await fetch('/api/jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company: jobCompany.trim(),
          role: jobRole.trim(),
          platform: jobPlatform.trim(),
          notes: jobNotes.trim()
        })
      });
      const data = await res.json();
      if (data.status === 'success') {
        showToast(`Logged application for ${jobCompany}`, 'success');
        setJobCompany('');
        setJobRole('');
        setJobPlatform('');
        setJobNotes('');
        setShowJobModal(false);
        fetchJobs();
      }
    } catch (err) {
      showToast('Error saving job: ' + err.message, 'error');
    }
  }

  // Handle Update Job Stage
  async function handleJobStageChange(company, newStage) {
    try {
      const res = await fetch('/api/jobs/stage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company, stage: newStage })
      });
      const data = await res.json();
      if (data.status === 'success') {
        showToast(`${company} moved to ${newStage}`, 'success');
        fetchJobs();
      }
    } catch (err) {
      showToast('Error: ' + err.message, 'error');
    }
  }

  // Handle Create Lead Submit
  async function handleCreateLead(e) {
    e.preventDefault();
    try {
      const res = await fetch('/api/leads', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: leadName.trim(),
          company: leadCompany.trim(),
          deal_value: leadDealValue.trim(),
          phone: leadPhone.trim(),
          email: leadEmail.trim(),
          notes: leadNotes.trim()
        })
      });
      const data = await res.json();
      if (data.status === 'success') {
        showToast(`Lead created for ${leadName}`, 'success');
        setLeadName('');
        setLeadCompany('');
        setLeadDealValue('');
        setLeadPhone('');
        setLeadEmail('');
        setLeadNotes('');
        setShowLeadModal(false);
        fetchLeads();
      }
    } catch (err) {
      showToast('Error: ' + err.message, 'error');
    }
  }

  // Handle Update Lead Stage
  async function handleLeadStageChange(leadId, newStage) {
    try {
      const res = await fetch('/api/leads/status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lead_identifier: leadId, status: newStage })
      });
      const data = await res.json();
      if (data.status === 'success') {
        showToast(`Lead updated to ${newStage}`, 'success');
        fetchLeads();
      }
    } catch (err) {
      showToast('Error: ' + err.message, 'error');
    }
  }

  return (
    <div className="view-panel flex-1 overflow-y-auto p-5 space-y-7">
      {/* SECTION 1: JOB APPLICATIONS FUNNEL */}
      <div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-200 mb-3 gap-2">
          <div>
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Briefcase className="w-4 h-4 text-blue-600" />
              <span>Job & Internship Pipeline</span>
            </h2>
            {jobStats && (
              <div className="flex items-center gap-3 text-xs font-mono text-slate-600 mt-1">
                <span>Total: <b className="text-slate-900">{jobStats.total_applications || 0}</b></span>
                <span>Applied: <b className="text-blue-600">{jobStats.stage_counts?.applied || 0}</b></span>
                <span>OA: <b className="text-cyan-600">{jobStats.stage_counts?.oa_test || 0}</b></span>
                <span>Interview: <b className="text-amber-600">{jobStats.stage_counts?.interview || 0}</b></span>
                <span>Offer: <b className="text-emerald-600">{jobStats.stage_counts?.offer || 0}</b></span>
              </div>
            )}
          </div>
          <button 
            onClick={() => setShowJobModal(prev => !prev)}
            className="btn-primary text-xs py-1.5 px-3 flex items-center gap-1.5 font-semibold"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Log Application</span>
          </button>
        </div>

        {/* Urgent Follow-ups Strip */}
        {jobFollowups.length > 0 && (
          <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-xs shadow-sm mb-3">
            <div className="font-semibold text-amber-900 flex items-center gap-1.5 mb-1.5">
              <Clock className="w-3.5 h-3.5 text-amber-600" />
              <span>{jobFollowups.length} Follow-ups Require Action:</span>
            </div>
            <div className="space-y-1">
              {jobFollowups.map((it, i) => (
                <div key={i} className="flex items-center justify-between text-[11.5px]">
                  <span className="text-slate-800 font-medium">
                    <b>{it.company}</b> — {it.role}
                  </span>
                  <span className={`font-mono text-[11px] font-semibold ${
                    it.is_overdue ? 'text-amber-800 bg-amber-200/60 px-1.5 py-0.5 rounded' : 'text-slate-600'
                  }`}>
                    {it.is_overdue ? 'OVERDUE' : `${it.days_until_followup}d left`}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Job Funnel Columns */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {JOB_STAGES.map(stage => {
            const stageApps = jobs.filter(a => (a.stage || 'applied').toLowerCase() === stage.toLowerCase());
            return (
              <div key={stage} className="studio-well p-3">
                <div className="flex items-center justify-between pb-2 border-b border-slate-200 mb-2.5">
                  <span className="font-bold text-xs text-slate-800 uppercase tracking-tight">{stage.replace('_', ' ')}</span>
                  <span className="font-mono text-xs px-1.5 py-0.5 rounded bg-white text-slate-700 font-semibold shadow-sm">
                    {stageApps.length}
                  </span>
                </div>

                <div className="min-h-[160px] space-y-2">
                  {stageApps.length === 0 ? (
                    <div className="text-[11px] text-slate-400 font-mono text-center py-5 border border-dashed border-slate-200 rounded-md bg-slate-50/50">
                      Empty
                    </div>
                  ) : (
                    stageApps.map((app, i) => (
                      <div key={i} className="studio-card p-3 text-xs">
                        <div className="flex items-start justify-between mb-1">
                          <span className="font-semibold text-slate-900">{app.company}</span>
                          <span className="text-[10px] text-slate-500 font-mono px-1 rounded bg-slate-100">
                            {app.platform || 'Direct'}
                          </span>
                        </div>
                        <div className="text-slate-600 text-[11px] mb-2 font-medium">{app.role}</div>
                        {app.notes && (
                          <div className="text-slate-500 text-[10.5px] bg-slate-50 border border-slate-200 p-2 rounded mb-2 font-mono truncate" title={app.notes}>
                            {app.notes}
                          </div>
                        )}
                        <div className="flex items-center justify-between border-t border-slate-100 pt-2 mt-1">
                          <select 
                            value={stage}
                            onChange={(e) => handleJobStageChange(app.company, e.target.value)}
                            className="bg-white text-slate-700 border border-slate-200 rounded px-1.5 py-0.5 text-[10.5px] font-mono"
                          >
                            {JOB_STAGES.map(s => (
                              <option key={s} value={s}>{s}</option>
                            ))}
                          </select>
                          <span className="text-[10px] text-slate-400 font-mono">
                            {(app.applied_date || '').slice(5)}
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Log Job Modal */}
        {showJobModal && (
          <div className="mt-3 p-4 studio-card border border-blue-200 bg-white shadow-md animate-in fade-in duration-100">
            <h4 className="font-bold text-xs text-slate-900 mb-2">Log New Job Application</h4>
            <form onSubmit={handleLogJob} className="grid grid-cols-1 sm:grid-cols-4 gap-2.5 text-xs">
              <input 
                type="text" 
                value={jobCompany}
                onChange={(e) => setJobCompany(e.target.value)}
                placeholder="Company Name" 
                required 
                className="studio-well px-3 py-2 bg-white text-slate-900" 
              />
              <input 
                type="text" 
                value={jobRole}
                onChange={(e) => setJobRole(e.target.value)}
                placeholder="Role (e.g. AI Intern)" 
                required 
                className="studio-well px-3 py-2 bg-white text-slate-900" 
              />
              <input 
                type="text" 
                value={jobPlatform}
                onChange={(e) => setJobPlatform(e.target.value)}
                placeholder="Platform (e.g. LinkedIn)" 
                className="studio-well px-3 py-2 bg-white text-slate-900" 
              />
              <input 
                type="text" 
                value={jobNotes}
                onChange={(e) => setJobNotes(e.target.value)}
                placeholder="Notes / Referral..." 
                className="studio-well px-3 py-2 bg-white text-slate-900" 
              />
              <div className="sm:col-span-4 flex justify-end gap-2 mt-1">
                <button 
                  type="button" 
                  onClick={() => setShowJobModal(false)} 
                  className="btn-secondary text-xs py-1.5 px-3"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary text-xs py-1.5 px-4 font-semibold">
                  Save Application
                </button>
              </div>
            </form>
          </div>
        )}
      </div>

      {/* SECTION 2: CLIENT CRM DEALS */}
      <div>
        <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-3">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Users className="w-4 h-4 text-emerald-600" />
            <span>Client CRM Pipeline</span>
          </h2>
          <button 
            onClick={() => setShowLeadModal(prev => !prev)}
            className="btn-primary text-xs py-1.5 px-3 flex items-center gap-1.5 font-semibold"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Lead</span>
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {CRM_STAGES.map(stage => {
            const stageLeads = leads.filter(l => (l.status || 'New').toLowerCase() === stage.toLowerCase());
            return (
              <div key={stage} className="studio-well p-3">
                <div className="flex items-center justify-between pb-2 border-b border-slate-200 mb-2.5">
                  <span className="font-bold text-xs text-slate-800 uppercase tracking-tight">{stage}</span>
                  <span className="font-mono text-xs px-1.5 py-0.5 rounded bg-white text-slate-700 font-semibold shadow-sm">
                    {stageLeads.length}
                  </span>
                </div>

                <div className="min-h-[160px] space-y-2">
                  {stageLeads.length === 0 ? (
                    <div className="text-[11px] text-slate-400 font-mono text-center py-5 border border-dashed border-slate-200 rounded-md bg-slate-50/50">
                      No leads
                    </div>
                  ) : (
                    stageLeads.map((lead, i) => (
                      <div key={i} className="studio-card p-3 text-xs">
                        <div className="flex items-start justify-between mb-1">
                          <span className="font-semibold text-slate-900">{lead.name}</span>
                          <span className="font-mono text-emerald-700 font-semibold text-[11px]">
                            {lead.deal_value || '$0'}
                          </span>
                        </div>
                        <div className="text-slate-500 text-[11px] mb-1.5">{lead.company || 'Direct'}</div>
                        {lead.notes && (
                          <div className="text-slate-600 text-[11px] bg-slate-50 border border-slate-200 p-2 rounded mb-2 font-mono truncate">
                            {lead.notes}
                          </div>
                        )}
                        <div className="flex items-center justify-between border-t border-slate-100 pt-2 mt-1">
                          <select 
                            value={stage}
                            onChange={(e) => handleLeadStageChange(lead.id || lead.name, e.target.value)}
                            className="bg-white text-slate-700 border border-slate-200 rounded px-1.5 py-0.5 text-[10.5px] font-mono"
                          >
                            {CRM_STAGES.map(s => (
                              <option key={s} value={s}>Move: {s}</option>
                            ))}
                          </select>
                          <span className="text-[10px] text-slate-400 font-mono">
                            {(lead.phone || lead.email || '').slice(0, 14)}
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Add Lead Modal */}
        {showLeadModal && (
          <div className="mt-3 p-4 studio-card border border-emerald-200 bg-white shadow-md animate-in fade-in duration-100">
            <h4 className="font-bold text-xs text-slate-900 mb-2">Create Business Lead</h4>
            <form onSubmit={handleCreateLead} className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 text-xs">
              <input 
                type="text" 
                value={leadName}
                onChange={(e) => setLeadName(e.target.value)}
                placeholder="Client Contact Name" 
                required 
                className="studio-well px-3 py-2 bg-white text-slate-900" 
              />
              <input 
                type="text" 
                value={leadCompany}
                onChange={(e) => setLeadCompany(e.target.value)}
                placeholder="Company / Organization" 
                className="studio-well px-3 py-2 bg-white text-slate-900" 
              />
              <input 
                type="text" 
                value={leadDealValue}
                onChange={(e) => setLeadDealValue(e.target.value)}
                placeholder="Deal Value (e.g. $5,000)" 
                className="studio-well px-3 py-2 bg-white text-slate-900" 
              />
              <input 
                type="text" 
                value={leadPhone}
                onChange={(e) => setLeadPhone(e.target.value)}
                placeholder="Phone Number" 
                className="studio-well px-3 py-2 bg-white text-slate-900" 
              />
              <input 
                type="email" 
                value={leadEmail}
                onChange={(e) => setLeadEmail(e.target.value)}
                placeholder="Email Address" 
                className="studio-well px-3 py-2 bg-white text-slate-900" 
              />
              <input 
                type="text" 
                value={leadNotes}
                onChange={(e) => setLeadNotes(e.target.value)}
                placeholder="Notes / Scope summary..." 
                className="studio-well px-3 py-2 bg-white text-slate-900" 
              />
              <div className="sm:col-span-3 flex justify-end gap-2 mt-1">
                <button 
                  type="button" 
                  onClick={() => setShowLeadModal(false)} 
                  className="btn-secondary text-xs py-1.5 px-3"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary text-xs py-1.5 px-4 font-semibold">
                  Save Lead
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
