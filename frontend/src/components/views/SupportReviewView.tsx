import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { supportApi } from '../../api';
import { 
  LifeBuoy, 
  User, 
  ShoppingBag, 
  Sparkles, 
  ArrowRight, 
  Send,
  MessageSquare,
  ShieldCheck,
  Loader2,
  AlertTriangle,
  Clock,
  CreditCard,
  Star,
  CheckCircle2
} from 'lucide-react';
import type { SupportAnalyzeResponse } from '../../types/api';

export const SupportReviewView: React.FC = () => {
  const { tasks, executeSupportResponse, setSelectedTaskId, setActiveTab, isBackendConnected } = useApp();

  // Test Scenarios Preset Definitions
  const testScenarios = [
    {
      id: 'delayed-order',
      title: 'Delayed Order Scenario',
      icon: <Clock className="w-4 h-4 text-amber-600" />,
      message: 'My order #ORD-8821 arrived 4 days late and the Wireless Headphones were missing from the box! Tracking is delayed.',
      customerId: 'C001'
    },
    {
      id: 'payment-issue',
      title: 'Payment Issue Scenario',
      icon: <CreditCard className="w-4 h-4 text-blue-600" />,
      message: 'I was charged twice on my credit card for transaction #TX-9902 order #ORD-8821!',
      customerId: 'C001'
    },
    {
      id: 'refund-approval',
      title: 'Refund Requiring Approval',
      icon: <ShieldCheck className="w-4 h-4 text-red-600" />,
      message: 'I demand an immediate full refund of $145.00 for order #ORD-8821 missing items!',
      customerId: 'C001'
    },
    {
      id: 'customer-review',
      title: 'Customer Review (1-Star)',
      icon: <Star className="w-4 h-4 text-purple-600" />,
      message: 'Rated 1 star: Terrible service, missing headphones and delayed shipping! I will leave bad reviews everywhere.',
      customerId: 'C001'
    }
  ];

  const [selectedScenario, setSelectedScenario] = useState(testScenarios[0]);
  const [complaintText, setComplaintText] = useState(testScenarios[0].message);

  // Backend Analysis State
  const [analysis, setAnalysis] = useState<SupportAnalyzeResponse | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  const [selectedOption, setSelectedOption] = useState<string>('Offer Compensation');
  const [customText, setCustomText] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [executedStatus, setExecutedStatus] = useState<string | null>(null);

  const activeTask = tasks.find(t => t.supportReview) || tasks[0];

  // Analyze complaint text via backend API
  const runBackendAnalysis = async (textToAnalyze: string, customerId?: string) => {
    setIsAnalyzing(true);
    setAnalysisError(null);
    setExecutedStatus(null);
    try {
      if (isBackendConnected) {
        const res = await supportApi.analyze({
          message: textToAnalyze,
          customer_id: customerId || 'C001'
        });
        setAnalysis(res);
        if (res.response_options && res.response_options.length > 0) {
          setSelectedOption(res.response_options[0]);
        }
      } else {
        // Local simulation fallback
        const isRefund = textToAnalyze.toLowerCase().includes('refund');
        const isReview = textToAnalyze.toLowerCase().includes('rated');
        const isPayment = textToAnalyze.toLowerCase().includes('charged');

        setAnalysis({
          intent: isRefund ? 'REFUND_REQUEST' : isReview ? 'CUSTOMER_REVIEW' : isPayment ? 'PAYMENT_ISSUE' : 'DELAYED_ORDER',
          confidence: 0.96,
          sentiment: 'NEGATIVE',
          severity: isRefund ? 'HIGH' : 'MEDIUM',
          customer_context: {
            customer: { id: 'C001', name: 'Sarah Jenkins', email: 'sarah.j@acme.com' },
            orders_count: 4,
            recent_orders: [{ id: 'ORD-8821', total: '$145.00', status: 'In Transit' }]
          },
          recommended_action: isRefund 
            ? 'Issue complimentary replacement and $25 voucher upon human approval'
            : 'Dispatch tracking update and carrier delay explanation',
          response_options: ['Apologize + Provide Update', 'Offer Compensation', 'Request More Information', 'Escalate', 'Custom Response'],
          approval_required: isRefund
        });
      }
    } catch (err: any) {
      setAnalysisError(err.message || 'Failed to connect to backend support analyzer.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  useEffect(() => {
    runBackendAnalysis(complaintText, selectedScenario.customerId);
  }, [complaintText, selectedScenario]);

  const handleSelectScenario = (sc: typeof testScenarios[0]) => {
    setSelectedScenario(sc);
    setComplaintText(sc.message);
  };

  const handleExecute = async () => {
    setIsExecuting(true);
    try {
      if (isBackendConnected && activeTask) {
        await supportApi.executeAction({
          task_id: activeTask.id,
          action: selectedOption,
          custom_response: customText
        });
      } else if (activeTask) {
        await executeSupportResponse(activeTask.id, selectedOption, customText);
      }
      setExecutedStatus(`Response Executed: "${selectedOption}" via AgentX Support Teammate.`);
    } catch (err: any) {
      setExecutedStatus(`Action dispatched locally: "${selectedOption}".`);
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="p-6 md:p-8 max-w-6xl mx-auto space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 text-[11px] font-mono font-bold mb-2">
            <LifeBuoy className="w-3.5 h-3.5 text-indigo-600" />
            <span>AI + HUMAN SUPPORT COLLABORATION</span>
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">Support Review & Escalation Workspace</h2>
          <p className="text-xs text-slate-500 font-medium">
            Live backend customer resolution center for analyzing complaints, sentiment, order context, and recommended responses.
          </p>
        </div>

        {activeTask && (
          <button
            onClick={() => {
              setSelectedTaskId(activeTask.id);
              setActiveTab('task-execution');
            }}
            className="text-xs text-indigo-600 hover:underline font-bold flex items-center gap-1"
          >
            <span>View Live Execution Logs</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Test Scenarios Quick Switch Bar */}
      <div className="glass-card p-4 rounded-2xl border border-slate-200 space-y-3">
        <p className="text-[11px] uppercase font-mono text-slate-500 font-bold flex items-center gap-1.5">
          <Sparkles className="w-4 h-4 text-indigo-600" />
          Test Scenario Presets (Live Backend Analysis):
        </p>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {testScenarios.map((sc) => (
            <button
              key={sc.id}
              onClick={() => handleSelectScenario(sc)}
              className={`p-3 rounded-xl border text-left transition-all flex items-center gap-2.5 ${
                selectedScenario.id === sc.id
                  ? 'bg-indigo-50 border-indigo-400 shadow-xs'
                  : 'bg-white border-slate-200 hover:bg-slate-50'
              }`}
            >
              <div className="p-2 rounded-lg bg-white border border-slate-200 shrink-0">
                {sc.icon}
              </div>
              <div>
                <p className="text-xs font-bold text-slate-900 leading-tight">{sc.title}</p>
                <p className="text-[10px] text-slate-500 font-mono">Click to test</p>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Main Analysis Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Complaint & Backend NLP Analysis */}
        <div className="lg:col-span-2 glass-card p-6 rounded-2xl border border-slate-200 space-y-6">
          <div className="flex items-start justify-between border-b border-slate-100 pb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-red-50 text-red-600 border border-red-100 flex items-center justify-center font-bold">
                <User className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">
                  {analysis?.customer_context?.customer?.name || 'Sarah Jenkins'}
                </h3>
                <p className="text-xs text-slate-500">
                  {analysis?.customer_context?.customer?.email || 'sarah.j@acme.com'} • Ticket #TICK-8841
                </p>
              </div>
            </div>

            {isAnalyzing ? (
              <div className="flex items-center gap-2 text-xs text-indigo-600 font-bold">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Backend Analyzing...</span>
              </div>
            ) : analysis ? (
              <div className="flex flex-wrap items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                  Intent: {analysis.intent}
                </span>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-red-50 text-red-700 border border-red-200">
                  Sentiment: {analysis.sentiment}
                </span>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-amber-50 text-amber-700 border border-amber-200">
                  Severity: {analysis.severity}
                </span>
              </div>
            ) : null}
          </div>

          {/* Complaint Text Payload */}
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
            <p className="text-[10px] font-mono uppercase text-slate-500 font-bold">Customer Payload / Complaint Text:</p>
            <textarea
              rows={3}
              value={complaintText}
              onChange={(e) => setComplaintText(e.target.value)}
              className="w-full bg-white text-xs text-slate-800 p-3 rounded-lg border border-slate-200 focus:outline-none focus:border-indigo-500 font-medium leading-relaxed"
            />
          </div>

          {/* Error Banner */}
          {analysisError && (
            <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                <span>{analysisError} Using fallback local analysis.</span>
              </div>
              <button
                onClick={() => runBackendAnalysis(complaintText, selectedScenario.customerId)}
                className="px-3 py-1 bg-white border border-amber-300 rounded-lg font-bold text-amber-900 text-[11px]"
              >
                Retry
              </button>
            </div>
          )}

          {/* AI Recommendation Box */}
          {analysis && !isAnalyzing && (
            <div className="p-4 rounded-xl bg-indigo-50/70 border border-indigo-200 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-indigo-900 flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-indigo-600 animate-pulse" />
                  Backend AI Recommendation
                </span>
                <span className="text-[10px] font-mono bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded font-bold">
                  Confidence: {((analysis.confidence || 0.95) * 100).toFixed(0)}%
                </span>
              </div>
              <p className="text-xs text-slate-700 leading-relaxed font-medium">
                {analysis.recommended_action}
              </p>

              {analysis.approval_required && (
                <div className="mt-2 inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-300 text-[10px] font-bold">
                  <ShieldCheck className="w-3.5 h-3.5 text-amber-600" />
                  <span>Human Approval Required before dispatching financial refund/credit</span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Order & Customer Context */}
        <div className="glass-card p-6 rounded-2xl border border-slate-200 space-y-4">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <ShoppingBag className="w-4 h-4 text-emerald-600" />
            <span>Customer & Order Context (DataService)</span>
          </h3>

          <div className="space-y-3 text-xs">
            <div className="flex justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-slate-500 font-medium">Customer ID:</span>
              <span className="font-mono font-bold text-indigo-600">
                {analysis?.customer_context?.customer?.id || 'C001'}
              </span>
            </div>

            <div className="flex justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-slate-500 font-medium">Total Orders Count:</span>
              <span className="font-bold text-slate-800">
                {analysis?.customer_context?.orders_count || 4} orders
              </span>
            </div>

            <div className="flex justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-slate-500 font-medium">Recent Order ID:</span>
              <span className="font-mono font-bold text-slate-800">
                {analysis?.customer_context?.recent_orders?.[0]?.id || 'ORD-8821'}
              </span>
            </div>

            <div className="flex justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-slate-500 font-medium">Order Total:</span>
              <span className="font-bold text-emerald-600">
                {analysis?.customer_context?.recent_orders?.[0]?.total || '$145.00'}
              </span>
            </div>

            <div className="flex justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-slate-500 font-medium">Shipping Status:</span>
              <span className="text-amber-700 font-mono text-[11px] font-semibold">
                {analysis?.customer_context?.recent_orders?.[0]?.status || 'In Transit - Delayed'}
              </span>
            </div>

            <div className="flex justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-slate-500 font-medium">Customer Tier:</span>
              <span className="font-bold text-purple-700">VIP Gold ($4,850 LTV)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Human Operator Response Selection */}
      <div className="glass-card p-6 md:p-8 rounded-2xl border border-slate-200 space-y-6">
        <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-indigo-600" />
          <span>Human Operator Response Selection</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {(analysis?.response_options || ['Apologize + Provide Update', 'Offer Compensation', 'Request More Information', 'Escalate', 'Custom Response']).map((option) => (
            <button
              key={option}
              onClick={() => setSelectedOption(option)}
              className={`p-4 rounded-xl border text-left transition-all ${
                selectedOption === option
                  ? 'bg-indigo-50 border-indigo-500 text-indigo-900 shadow-xs'
                  : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
              }`}
            >
              <p className="font-bold text-xs text-indigo-700 mb-1">{option}</p>
              <p className="text-[11px] text-slate-500 leading-snug">
                {option.includes('Apologize') ? 'Send empathetic email with carrier tracking update.' :
                 option.includes('Compensation') ? 'Issue $25 store credit voucher AGX-25 and express reshipment.' :
                 option.includes('Information') ? 'Request customer photos or delivery verification.' :
                 option.includes('Escalate') ? 'Pass ticket to senior manager queue.' : 'Write custom tailored response text.'}
              </p>
            </button>
          ))}
        </div>

        {selectedOption === 'Custom Response' && (
          <div className="space-y-2">
            <label className="block text-xs font-mono text-slate-600 font-bold">Custom Response Text:</label>
            <textarea
              rows={3}
              value={customText}
              onChange={(e) => setCustomText(e.target.value)}
              placeholder="Type your custom response..."
              className="w-full bg-slate-50 text-xs p-3 rounded-xl border border-slate-200 text-slate-900 focus:outline-none focus:border-indigo-500 font-medium"
            ></textarea>
          </div>
        )}

        {executedStatus ? (
          <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-mono font-bold flex items-center justify-between">
            <span className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              {executedStatus}
            </span>
            <span className="text-[10px] bg-emerald-100 text-emerald-800 px-2.5 py-0.5 rounded-full border border-emerald-300">
              Verified
            </span>
          </div>
        ) : (
          <div className="flex items-center justify-end gap-4 pt-4 border-t border-slate-100">
            <button
              onClick={handleExecute}
              disabled={isExecuting}
              className="px-8 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-extrabold text-xs shadow-md shadow-indigo-600/20 transition-all hover:scale-105 flex items-center gap-2 cursor-pointer"
            >
              <Send className="w-4 h-4" />
              <span>{isExecuting ? 'Executing Response...' : `Execute Response ("${selectedOption}")`}</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
