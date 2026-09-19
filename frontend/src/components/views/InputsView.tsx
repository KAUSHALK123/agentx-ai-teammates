import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { 
  FileText, 
  UploadCloud, 
  FileSpreadsheet, 
  Mic, 
  Image as ImageIcon, 
  CheckCircle2, 
  PlayCircle, 
  RefreshCw,
  Search,
  Eye
} from 'lucide-react';
import { inputsApi } from '../../api';
import type { InputDetailResponse } from '../../types/api';

export const InputsView: React.FC = () => {
  const { setActiveTab } = useApp();
  const [inputsList, setInputsList] = useState<InputDetailResponse[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [selectedInput, setSelectedInput] = useState<InputDetailResponse | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Mock initial business inputs so UI is instantly rich even if backend store is fresh
  const initialFallbackInputs: InputDetailResponse[] = [
    {
      input_id: 'inp_refund_proof',
      type: 'pdf',
      filename: 'kaushal_receipt_ORD8821.pdf',
      content_reference: 'storage/kaushal_receipt_ORD8821.pdf',
      size_bytes: 492000,
      mime_type: 'application/pdf',
      extracted_text: 'PURCHASE RECEIPT #ORD-8821\nCustomer: Kaushal (k8849819@gmail.com)\nItem: Pro Audio Bundle ($145.00)\nTracking ID: 1Z999888777666\nDelivery Exception: Carrier delay, damaged package reported.',
      structured_data: {
        order_id: 'ORD-8821',
        customer_email: 'k8849819@gmail.com',
        amount: 145.0,
        currency: 'USD',
        sentiment: 'Dissatisfied'
      },
      metadata: { page_count: 1, ocr_engine: 'tesseract_enterprise' },
      status: 'PROCESSED',
      task_id: 'TASK-9042',
      created_at: new Date(Date.now() - 3600000).toISOString(),
      updated_at: new Date(Date.now() - 3500000).toISOString()
    },
    {
      input_id: 'inp_lead_prospects',
      type: 'csv',
      filename: 'q4_enterprise_inbound_leads.csv',
      content_reference: 'storage/q4_enterprise_inbound_leads.csv',
      size_bytes: 86400,
      mime_type: 'text/csv',
      extracted_text: 'company,contact_name,email,headcount,budget,timeline\nCloudCorp,David Ross,david@cloudcorp.io,450,$120k,Immediate\nFinScale,Elena Rostova,elena@finscale.tech,180,$65k,Q1\nLogiGlobal,Marcus Vance,m.vance@logiglobal.com,2200,$250k,Immediate',
      structured_data: {
        total_rows: 3,
        qualified_leads: 3,
        high_value_pipeline: '$435,000'
      },
      metadata: { delimiter: ',', row_count: 3 },
      status: 'PROCESSED',
      task_id: 'TASK-8812',
      created_at: new Date(Date.now() - 7200000).toISOString(),
      updated_at: new Date(Date.now() - 7100000).toISOString()
    },
    {
      input_id: 'inp_voice_memo',
      type: 'audio',
      filename: 'warehouse_operations_memo.mp3',
      content_reference: 'storage/warehouse_operations_memo.mp3',
      size_bytes: 1240000,
      mime_type: 'audio/mpeg',
      extracted_text: 'Transcribed Audio: Notice for Operations Teammate. We noticed a 14% stock discrepancy in aisle 4B for item SKU-9018. Please reconcile inventory database and flag any missing shipments from suppliers.',
      structured_data: {
        detected_intent: 'Inventory Reconciliation',
        urgency: 'Medium',
        sku: 'SKU-9018',
        target_agent: 'operations'
      },
      metadata: { duration_seconds: 18.4, sample_rate_hz: 44100 },
      status: 'PROCESSED',
      task_id: 'TASK-7731',
      created_at: new Date(Date.now() - 10800000).toISOString(),
      updated_at: new Date(Date.now() - 10700000).toISOString()
    }
  ];

  const fetchInputs = async () => {
    setIsLoading(true);
    try {
      // In practice we can fetch from task inputs or fallback
      setInputsList(prev => prev.length > 0 ? prev : initialFallbackInputs);
    } catch {
      setInputsList(initialFallbackInputs);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchInputs();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploadStatus('Uploading and extracting multimodal context...');
    try {
      const uploadRes = await inputsApi.uploadInput(files[0]);
      
      const newEntry: InputDetailResponse = {
        input_id: uploadRes.input_id,
        type: uploadRes.type,
        filename: uploadRes.filename,
        content_reference: `storage/${uploadRes.filename}`,
        size_bytes: uploadRes.size_bytes,
        mime_type: uploadRes.mime_type,
        extracted_text: `Processed ${uploadRes.filename} content ready for autonomous agents.`,
        structured_data: { source: 'User Upload', status: 'Ready' },
        metadata: uploadRes.metadata,
        status: uploadRes.status,
        task_id: uploadRes.task_id,
        created_at: uploadRes.created_at,
        updated_at: uploadRes.created_at
      };

      setInputsList(prev => [newEntry, ...prev]);
      setSelectedInput(newEntry);
      setUploadStatus('File successfully processed & extracted!');
      setTimeout(() => setUploadStatus(null), 3000);
    } catch (err: any) {
      setUploadStatus(`Upload error: ${err.message || 'Server error'}`);
      setTimeout(() => setUploadStatus(null), 4000);
    }
  };

  const getFileIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'pdf': return <FileText className="w-5 h-5 text-red-500" />;
      case 'csv': return <FileSpreadsheet className="w-5 h-5 text-emerald-500" />;
      case 'audio': return <Mic className="w-5 h-5 text-purple-500" />;
      case 'image': return <ImageIcon className="w-5 h-5 text-blue-500" />;
      default: return <FileText className="w-5 h-5 text-slate-500" />;
    }
  };

  const filtered = inputsList.filter(i => 
    i.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
    i.input_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (i.extracted_text && i.extracted_text.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 text-[11px] font-mono font-bold mb-2">
            <UploadCloud className="w-3.5 h-3.5 text-indigo-600" />
            <span>PHASE 10 — MULTIMODAL INGESTION LAYER</span>
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">Business Document & Audio Ingestion</h2>
          <p className="text-xs text-slate-500 font-medium">
            Upload PDFs, CSV spreadsheets, DOCX contracts, voice memos, and images for automatic extraction and agent reasoning.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileUpload} 
            className="hidden" 
            accept=".pdf,.csv,.doc,.docx,.png,.jpg,.jpeg,.mp3,.wav,.ogg"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md shadow-indigo-600/20 transition-all cursor-pointer"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Upload New Input</span>
          </button>
        </div>
      </div>

      {uploadStatus && (
        <div className="p-3.5 rounded-xl bg-indigo-50 border border-indigo-200 text-indigo-800 text-xs font-semibold flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-indigo-600" />
          <span>{uploadStatus}</span>
        </div>
      )}

      {/* Main Grid: Upload Zone + Input List + Detail Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Search & Inputs List (7 Cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="glass-card p-4 rounded-2xl border border-slate-200 flex items-center justify-between gap-4">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search extracted documents, CSVs, audio memos..."
                className="w-full bg-slate-50 text-slate-900 text-xs pl-9 pr-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:border-indigo-500 font-medium"
              />
            </div>
            <button
              onClick={fetchInputs}
              className="p-2.5 rounded-xl bg-white border border-slate-200 text-slate-600 hover:text-indigo-600 shadow-xs transition-colors cursor-pointer"
              title="Refresh Inputs"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>

          <div className="space-y-3">
            {filtered.length === 0 ? (
              <div className="glass-card p-8 rounded-2xl border border-slate-200 text-center space-y-2">
                <FileText className="w-8 h-8 text-slate-400 mx-auto" />
                <p className="text-sm font-bold text-slate-700">No Business Inputs Found</p>
                <p className="text-xs text-slate-500">Upload a PDF receipt, CSV lead sheet, or voice recording to start.</p>
              </div>
            ) : (
              filtered.map((item) => {
                const isSelected = selectedInput?.input_id === item.input_id;
                return (
                  <div
                    key={item.input_id}
                    onClick={() => setSelectedInput(item)}
                    className={`glass-card p-4 rounded-2xl border transition-all cursor-pointer flex items-center justify-between ${
                      isSelected 
                        ? 'border-indigo-500 bg-indigo-50/40 shadow-sm' 
                        : 'border-slate-200 hover:border-slate-300 bg-white/70'
                    }`}
                  >
                    <div className="flex items-center gap-3.5 min-w-0">
                      <div className="p-2.5 bg-slate-100 rounded-xl shrink-0">
                        {getFileIcon(item.type)}
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-xs font-bold text-slate-900 truncate">{item.filename}</p>
                          <span className="px-1.5 py-0.2 rounded text-[9px] font-mono uppercase bg-slate-100 text-slate-600 font-bold">
                            {item.type}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-500 font-mono mt-0.5 truncate">
                          {item.input_id} • {(item.size_bytes / 1024).toFixed(0)} KB
                        </p>
                      </div>
                    </div>

                    <div className="text-right shrink-0 space-y-1">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        {item.status}
                      </span>
                      <p className="text-[10px] text-slate-400">
                        {new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Column: Preview & Extracted Structured Data (5 Cols) */}
        <div className="lg:col-span-5">
          {selectedInput ? (
            <div className="glass-card p-6 rounded-2xl border border-slate-200 space-y-5 sticky top-8 bg-white/80">
              <div className="flex items-start justify-between border-b border-slate-100 pb-4">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-indigo-50 rounded-xl">
                    {getFileIcon(selectedInput.type)}
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">{selectedInput.filename}</h3>
                    <p className="text-[10px] font-mono text-slate-500">{selectedInput.input_id}</p>
                  </div>
                </div>

                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  {selectedInput.status}
                </span>
              </div>

              {/* Extracted Text Preview */}
              <div className="space-y-2">
                <p className="text-[10px] uppercase font-mono text-slate-500 font-bold">
                  Extracted Context / Transcript
                </p>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-700 font-mono leading-relaxed max-h-48 overflow-y-auto whitespace-pre-wrap">
                  {selectedInput.extracted_text || 'No text extracted.'}
                </div>
              </div>

              {/* Structured JSON Entities */}
              {selectedInput.structured_data && (
                <div className="space-y-2">
                  <p className="text-[10px] uppercase font-mono text-slate-500 font-bold">
                    Structured Semantic Entities
                  </p>
                  <pre className="p-3 bg-slate-900 text-slate-100 rounded-xl text-[11px] font-mono overflow-x-auto max-h-44">
                    {JSON.stringify(selectedInput.structured_data, null, 2)}
                  </pre>
                </div>
              )}

              {/* Dispatch Action */}
              <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
                <span className="text-[11px] text-slate-500 font-medium">
                  Attached to Task: <strong className="text-indigo-600 font-mono">{selectedInput.task_id || 'None'}</strong>
                </span>

                <button
                  onClick={() => setActiveTab('create-task')}
                  className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition-all shadow-xs cursor-pointer"
                >
                  <PlayCircle className="w-3.5 h-3.5" />
                  <span>Dispatch Task</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="glass-card p-12 rounded-2xl border border-dashed border-slate-300 text-center space-y-3 bg-slate-50/50">
              <Eye className="w-8 h-8 text-slate-400 mx-auto" />
              <h4 className="text-sm font-bold text-slate-700">Select an Input to Inspect Context</h4>
              <p className="text-xs text-slate-500 max-w-xs mx-auto">
                Click any document, spreadsheet, or audio memo from the list on the left to review its extracted information.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
export default InputsView;
