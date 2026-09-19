import React, { useState, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { 
  Sparkles, 
  Mic, 
  UploadCloud, 
  FileText, 
  X, 
  Play, 
  LifeBuoy, 
  Briefcase, 
  Layers, 
  Wand2,
  Loader2,
  CheckCircle
} from 'lucide-react';
import type { AgentRole, TaskPriority } from '../../types';
import { inputsApi } from '../../api';

export const CreateTaskView: React.FC = () => {
  const { createNewTask } = useApp();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [agentRole, setAgentRole] = useState<AgentRole | 'auto'>('auto');
  const [priority, setPriority] = useState<TaskPriority>('HIGH');
  const [files, setFiles] = useState<{ name: string; size: string; type: string; inputId?: string; isUploading?: boolean }[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTimer, setRecordingTimer] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleQuickPromptComplaint = () => {
    setTitle('Investigate customer complaint: Order #ORD-8821 delayed with missing items');
    setDescription('Customer Sarah Jenkins (sarah.j@acme.com) reported high dissatisfaction with order #ORD-8821. Package delivered late and 1 item missing (Wireless Headphones). Please audit Shopify ERP, check refund limits, and formulate resolution.');
    setAgentRole('support');
    setPriority('HIGH');
    setFiles([
      { name: 'customer_email_thread.pdf', size: '1.2 MB', type: 'PDF' },
      { name: 'shipping_invoice_ORD8821.pdf', size: '480 KB', type: 'PDF' }
    ]);
  };

  const handleQuickPromptSales = () => {
    setTitle('Qualify sales lead LEAD-001: Rajesh Khanna (Cyberdyne Tech) & draft proposal');
    setDescription('Process inbound lead LEAD-001 for Rajesh Khanna (rajesh@cyberdyne.co.in) at Cyberdyne Tech. Inquired about 500 seat enterprise expansion. Qualify prospect and draft proposal.');
    setAgentRole('sales');
    setPriority('MEDIUM');
    setFiles([{ name: 'cyberdyne_expansion_requirements.csv', size: '84 KB', type: 'CSV' }]);
  };

  const handleToggleVoiceRecord = () => {
    if (!isRecording) {
      setIsRecording(true);
      setRecordingTimer(0);
      const interval = setInterval(() => {
        setRecordingTimer(prev => {
          if (prev >= 4) {
            clearInterval(interval);
            setIsRecording(false);
            setTitle('Investigate customer complaint: Order #ORD-8821 delayed');
            setDescription('Investigate customer complaint for Order ORD-8821. Check Shopify ERP, verify refund policies, and generate recommended apology update.');
            return 0;
          }
          return prev + 1;
        });
      }, 1000);
    } else {
      setIsRecording(false);
    }
  };

  const uploadAndAddFiles = async (fileList: FileList | File[]) => {
    const rawFiles = Array.from(fileList);
    for (const f of rawFiles) {
      const fileEntry = {
        name: f.name,
        size: `${(f.size / 1024).toFixed(0)} KB`,
        type: f.name.split('.').pop()?.toUpperCase() || 'FILE',
        isUploading: true
      };
      setFiles(prev => [...prev, fileEntry]);

      try {
        const uploadRes = await inputsApi.uploadInput(f);
        setFiles(prev => prev.map(item => {
          if (item.name === f.name && item.isUploading) {
            return {
              ...item,
              inputId: uploadRes.input_id,
              isUploading: false
            };
          }
          return item;
        }));
      } catch (err) {
        console.warn('File upload to backend failed, keeping local file entry:', err);
        setFiles(prev => prev.map(item => {
          if (item.name === f.name && item.isUploading) {
            return { ...item, isUploading: false };
          }
          return item;
        }));
      }
    }
  };

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      uploadAndAddFiles(e.dataTransfer.files);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      uploadAndAddFiles(e.target.files);
    }
  };

  const handleRemoveFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim()) return;

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const inputIds = files.map(f => f.inputId).filter(Boolean) as string[];
      await createNewTask({
        title: title || description.slice(0, 50) + '...',
        description,
        agentRole,
        priority,
        files,
        inputIds: inputIds.length > 0 ? inputIds : undefined
      });
    } catch (err: any) {
      setSubmitError(err?.message || 'Failed to dispatch task to AgentX backend.');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="p-6 md:p-8 max-w-5xl mx-auto space-y-8">
      <div>
        <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 text-[11px] font-mono font-bold mb-2">
          <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
          <span>AUTONOMOUS TASK DISPATCH</span>
        </div>
        <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">Create New AgentX Task</h2>
        <p className="text-xs text-slate-500">
          Describe what you need done in plain language. AgentX routes to the optimal AI teammate, plans tool execution, and handles verification.
        </p>
      </div>

      <div className="glass-card p-5 rounded-2xl border border-indigo-200 bg-indigo-50/50 relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center shrink-0 shadow-sm">
              <Wand2 className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <p className="text-xs uppercase font-mono font-bold text-indigo-700">Quick Demo Scenario</p>
              <h3 className="text-sm font-extrabold text-slate-900 mt-0.5">Simply say: "Investigate this customer complaint."</h3>
              <p className="text-xs text-slate-600 mt-1 font-normal">
                One-click pre-fills customer complaint ORD-8821, attaches invoice PDF, and triggers Support Teammate workflow.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleQuickPromptComplaint}
              className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md shadow-indigo-600/20 transition-all hover:scale-105 shrink-0"
            >
              Load Complaint Prompt
            </button>
            <button
              onClick={handleQuickPromptSales}
              className="px-3 py-2 rounded-xl bg-white hover:bg-slate-100 text-slate-700 text-xs font-bold border border-slate-200 transition-colors shrink-0"
            >
              Load Sales Lead
            </button>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="glass-card p-6 rounded-2xl border border-slate-200 space-y-4">
          <label className="block text-xs font-bold text-slate-700 uppercase font-mono">
            Task Name / Summary
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Investigate customer complaint for Order #ORD-8821"
            className="w-full bg-slate-50 text-slate-900 text-sm px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:border-indigo-500 placeholder-slate-400 font-semibold"
          />

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="block text-xs font-bold text-slate-700 uppercase font-mono">
                Detailed Task Instructions
              </label>

              <button
                type="button"
                onClick={handleToggleVoiceRecord}
                className={`flex items-center gap-2 px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                  isRecording 
                    ? 'bg-red-600 text-white animate-pulse'
                    : 'bg-slate-100 hover:bg-slate-200 text-indigo-700 border border-slate-200'
                }`}
              >
                <Mic className="w-3.5 h-3.5" />
                <span>{isRecording ? `Recording... (${recordingTimer}s)` : 'Voice Input'}</span>
              </button>
            </div>

            {isRecording && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-xl flex items-center justify-center gap-1.5">
                <div className="w-1 bg-red-600 wave-bar-1"></div>
                <div className="w-1 bg-red-600 wave-bar-2"></div>
                <div className="w-1 bg-red-600 wave-bar-3"></div>
                <div className="w-1 bg-red-600 wave-bar-4"></div>
                <div className="w-1 bg-red-600 wave-bar-5"></div>
                <span className="text-xs text-red-700 font-mono font-bold ml-2">Listening to speech input...</span>
              </div>
            )}

            <textarea
              rows={4}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Paste customer emails, complaint notes, order IDs, lead parameters, or logistics SKUs..."
              className="w-full bg-slate-50 text-slate-900 text-xs p-4 rounded-xl border border-slate-200 focus:outline-none focus:border-indigo-500 placeholder-slate-400 leading-relaxed font-medium"
            ></textarea>
          </div>
        </div>

        <div className="glass-card p-6 rounded-2xl border border-slate-200 space-y-4">
          <label className="block text-xs font-bold text-slate-700 uppercase font-mono">
            Attachments & Context Files (PDF / CSV / DOC / Images)
          </label>

          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileInputChange} 
            multiple 
            className="hidden" 
          />

          <div
            onClick={() => fileInputRef.current?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleFileDrop}
            className="border-2 border-dashed border-slate-200 hover:border-indigo-300 rounded-xl p-6 text-center bg-slate-50 transition-colors cursor-pointer"
          >
            <UploadCloud className="w-8 h-8 text-indigo-600 mx-auto mb-2" />
            <p className="text-xs font-bold text-slate-800">
              Drag & drop relevant files here, or <span className="text-indigo-600 underline">browse</span>
            </p>
            <p className="text-[10px] text-slate-500 font-medium mt-1">Supports PDF, CSV, DOCX, PNG, JPG (Max 25MB)</p>
          </div>

          {files.length > 0 && (
            <div className="space-y-2 pt-2">
              <p className="text-[11px] font-mono text-slate-500 font-bold">Attached Files ({files.length}):</p>
              <div className="flex flex-wrap gap-2">
                {files.map((file, idx) => (
                  <div
                    key={idx}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-100 border border-slate-200 text-xs text-slate-800 font-semibold"
                  >
                    {file.isUploading ? (
                      <Loader2 className="w-3.5 h-3.5 text-indigo-600 animate-spin" />
                    ) : file.inputId ? (
                      <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                    ) : (
                      <FileText className="w-3.5 h-3.5 text-indigo-600" />
                    )}
                    <span>{file.name}</span>
                    <span className="text-[10px] text-slate-500 font-mono">({file.size})</span>
                    {file.inputId && (
                      <span className="text-[9px] bg-emerald-50 text-emerald-700 border border-emerald-200 px-1.5 py-0.5 rounded font-mono font-bold">
                        {file.inputId}
                      </span>
                    )}
                    <button
                      type="button"
                      onClick={() => handleRemoveFile(idx)}
                      className="text-slate-400 hover:text-red-600 ml-1"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="glass-card p-6 rounded-2xl border border-slate-200 space-y-3">
            <label className="block text-xs font-bold text-slate-700 uppercase font-mono">
              Assigned AI Teammate
            </label>

            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setAgentRole('auto')}
                className={`p-3 rounded-xl border text-left text-xs font-semibold transition-all ${
                  agentRole === 'auto'
                    ? 'bg-indigo-50 border-indigo-300 text-indigo-900 shadow-xs'
                    : 'bg-slate-50 border-slate-200 text-slate-600 hover:text-slate-900'
                }`}
              >
                <div className="flex items-center gap-1.5 font-bold text-indigo-700 mb-1">
                  <Wand2 className="w-3.5 h-3.5" />
                  Auto-Select Agent
                </div>
                <p className="text-[10px] text-slate-500 font-normal">Smart routing engine evaluates intent</p>
              </button>

              <button
                type="button"
                onClick={() => setAgentRole('support')}
                className={`p-3 rounded-xl border text-left text-xs font-semibold transition-all ${
                  agentRole === 'support'
                    ? 'bg-indigo-50 border-indigo-300 text-indigo-900 shadow-xs'
                    : 'bg-slate-50 border-slate-200 text-slate-600 hover:text-slate-900'
                }`}
              >
                <div className="flex items-center gap-1.5 font-bold text-slate-900 mb-1">
                  <LifeBuoy className="w-3.5 h-3.5 text-indigo-600" />
                  Support Teammate
                </div>
                <p className="text-[10px] text-slate-500 font-normal">Customer resolution & refunds</p>
              </button>

              <button
                type="button"
                onClick={() => setAgentRole('sales')}
                className={`p-3 rounded-xl border text-left text-xs font-semibold transition-all ${
                  agentRole === 'sales'
                    ? 'bg-blue-50 border-blue-300 text-blue-900 shadow-xs'
                    : 'bg-slate-50 border-slate-200 text-slate-600 hover:text-slate-900'
                }`}
              >
                <div className="flex items-center gap-1.5 font-bold text-slate-900 mb-1">
                  <Briefcase className="w-3.5 h-3.5 text-blue-600" />
                  Sales Teammate
                </div>
                <p className="text-[10px] text-slate-500 font-normal">Leads, CRM & outbound</p>
              </button>

              <button
                type="button"
                onClick={() => setAgentRole('operations')}
                className={`p-3 rounded-xl border text-left text-xs font-semibold transition-all ${
                  agentRole === 'operations'
                    ? 'bg-purple-50 border-purple-300 text-purple-900 shadow-xs'
                    : 'bg-slate-50 border-slate-200 text-slate-600 hover:text-slate-900'
                }`}
              >
                <div className="flex items-center gap-1.5 font-bold text-slate-900 mb-1">
                  <Layers className="w-3.5 h-3.5 text-purple-600" />
                  Operations & n8n
                </div>
                <p className="text-[10px] text-slate-500 font-normal">ERP & stock reorders</p>
              </button>
            </div>
          </div>

          <div className="glass-card p-6 rounded-2xl border border-slate-200 space-y-3">
            <label className="block text-xs font-bold text-slate-700 uppercase font-mono">
              Task Execution Priority
            </label>

            <div className="grid grid-cols-2 gap-2">
              {(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] as TaskPriority[]).map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setPriority(p)}
                  className={`p-3 rounded-xl border text-xs font-extrabold transition-all text-center ${
                    priority === p
                      ? p === 'CRITICAL' ? 'bg-red-50 border-red-300 text-red-700 shadow-xs' :
                        p === 'HIGH' ? 'bg-amber-50 border-amber-300 text-amber-800 shadow-xs' :
                        'bg-indigo-50 border-indigo-300 text-indigo-800 shadow-xs'
                      : 'bg-slate-50 border-slate-200 text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        </div>

        {submitError && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 font-medium">
            {submitError}
          </div>
        )}

        <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200">
          <button
            type="button"
            disabled={isSubmitting}
            onClick={() => {
              setTitle('');
              setDescription('');
              setFiles([]);
              setSubmitError(null);
            }}
            className="px-5 py-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold transition-colors disabled:opacity-50"
          >
            Clear / Cancel
          </button>

          <button
            type="submit"
            disabled={isSubmitting}
            className="flex items-center gap-2 px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-extrabold shadow-md shadow-indigo-600/20 transition-all hover:scale-105 disabled:opacity-50"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Dispatching to AgentX...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                <span>Create & Launch Task</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
