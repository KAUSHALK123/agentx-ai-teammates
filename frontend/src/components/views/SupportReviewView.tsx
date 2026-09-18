import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { 
  LifeBuoy, 
  User, 
  ShoppingBag, 
  Sparkles, 
  ArrowRight, 
  Send,
  MessageSquare,
  ShieldCheck
} from 'lucide-react';
import type { SupportReviewData } from '../../types';

export const SupportReviewView: React.FC = () => {
  const { tasks, executeSupportResponse, setSelectedTaskId, setActiveTab } = useApp();

  const task = tasks.find(t => t.supportReview) || tasks[0];
  const review: SupportReviewData = task?.supportReview || {
    customerName: 'Sarah Jenkins',
    customerEmail: 'sarah.j@acme.com',
    ticketId: 'TICK-8841',
    orderId: 'ORD-8821',
    sentiment: 'Very Negative',
    intent: 'Refund & Order Complaint',
    severity: 'High',
    complaintText: 'My order #ORD-8821 arrived 4 days late and the Wireless Headphones were missing from the box! I paid for express shipping. Please resolve this immediately or I am canceling my subscription.',
    orderContext: {
      item: 'Pro Audio Bundle (Headphones + Mic)',
      amount: '$145.00',
      orderDate: 'Sept 14, 2026',
      shippingStatus: 'Partial Delivery (Carrier Delay)',
      trackingNumber: '1Z9999999999999999',
      lifetimeValue: '$4,850 (VIP Gold)'
    },
    aiRecommendation: 'Issue immediate complimentary replacement for missing Headphones ($89 value), credit $25 voucher for shipping delay, and dispatch personalized apology.',
    aiConfidence: 0.96
  };

  const [selectedOption, setSelectedOption] = useState<string>('Offer Compensation');
  const [customText, setCustomText] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);

  const handleExecute = async () => {
    if (!task) return;
    setIsExecuting(true);
    try {
      await executeSupportResponse(task.id, selectedOption, customText);
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="p-6 md:p-8 max-w-6xl mx-auto space-y-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 text-[11px] font-mono font-bold mb-2">
            <LifeBuoy className="w-3.5 h-3.5 text-indigo-600" />
            <span>AI + HUMAN SUPPORT COLLABORATION</span>
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">Support Review & Escalation Workspace</h2>
          <p className="text-xs text-slate-500 font-medium">
            Collaborative resolution center where AgentX inspects customer sentiment, order context, and recommends optimal customer responses.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {tasks.filter(t => t.supportReview).length > 1 && (
            <select
              value={task?.id || ''}
              onChange={(e) => setSelectedTaskId(e.target.value)}
              className="bg-white text-slate-800 text-xs font-bold rounded-xl px-3 py-2 border border-slate-200 shadow-xs cursor-pointer"
            >
              {tasks.filter(t => t.supportReview).map(t => (
                <option key={t.id} value={t.id}>
                  {t.id} - {t.title.slice(0, 25)}...
                </option>
              ))}
            </select>
          )}

          <button
            onClick={() => {
              if (task) setSelectedTaskId(task.id);
              setActiveTab('task-execution');
            }}
            className="text-xs text-indigo-600 hover:underline font-bold flex items-center gap-1"
          >
            <span>View Live Execution Logs</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-card p-6 rounded-2xl border border-slate-200 space-y-6">
          <div className="flex items-start justify-between border-b border-slate-100 pb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-red-50 text-red-600 border border-red-100 flex items-center justify-center font-bold">
                <User className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">{review.customerName}</h3>
                <p className="text-xs text-slate-500">{review.customerEmail} • Ticket #{review.ticketId}</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-red-50 text-red-700 border border-red-200">
                Sentiment: {review.sentiment}
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-amber-50 text-amber-700 border border-amber-200">
                Severity: {review.severity}
              </span>
            </div>
          </div>

          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
            <p className="text-[10px] font-mono uppercase text-slate-500 font-bold">Customer Complaint Payload:</p>
            <p className="text-xs text-slate-800 leading-relaxed italic font-medium">
              "{review.complaintText}"
            </p>
          </div>

          <div className="p-4 rounded-xl bg-indigo-50/70 border border-indigo-200 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-indigo-900 flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-indigo-600 animate-pulse" />
                AI Teammate Recommendation
              </span>
              <span className="text-[10px] font-mono bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded font-bold">
                Confidence: {(review.aiConfidence * 100).toFixed(0)}%
              </span>
            </div>
            <p className="text-xs text-slate-700 leading-relaxed font-medium">
              {review.aiRecommendation}
            </p>
          </div>
        </div>

        <div className="glass-card p-6 rounded-2xl border border-slate-200 space-y-4">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <ShoppingBag className="w-4 h-4 text-emerald-600" />
            <span>Order & Customer Context</span>
          </h3>

          <div className="space-y-3 text-xs">
            <div className="flex justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-slate-500 font-medium">Order ID:</span>
              <span className="font-mono font-bold text-indigo-600">{review.orderId}</span>
            </div>

            <div className="flex justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-slate-500 font-medium">Item:</span>
              <span className="font-medium text-slate-800">{review.orderContext.item}</span>
            </div>

            <div className="flex justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-slate-500 font-medium">Amount:</span>
              <span className="font-bold text-emerald-600">{review.orderContext.amount}</span>
            </div>

            <div className="flex justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-slate-500 font-medium">Shipping Status:</span>
              <span className="text-amber-700 font-mono text-[11px] font-semibold">{review.orderContext.shippingStatus}</span>
            </div>

            <div className="flex justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-slate-500 font-medium">Customer LTV:</span>
              <span className="font-bold text-purple-700">{review.orderContext.lifetimeValue}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="glass-card p-6 md:p-8 rounded-2xl border border-slate-200 space-y-6">
        <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-indigo-600" />
          <span>Human Operator Response Selection</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {[
            { id: 'Apologize + Provide Update', title: 'Apologize & Tracking Update', desc: 'Send empathetic email with carrier delay explanation.' },
            { id: 'Offer Compensation', title: 'Compensation + Voucher', desc: 'Issue $25 store credit voucher AGX-25 and express reshipment.' },
            { id: 'Request More Information', title: 'Request Photos / Info', desc: 'Ask customer to confirm missing package condition.' },
            { id: 'Escalate to Tier-2', title: 'Escalate to Senior Ops', desc: 'Pass ticket to senior manager queue.' },
            { id: 'Custom Response', title: 'Custom Response', desc: 'Write custom tailored response text.' },
          ].map((option) => (
            <button
              key={option.id}
              onClick={() => setSelectedOption(option.id)}
              className={`p-4 rounded-xl border text-left transition-all ${
                selectedOption === option.id
                  ? 'bg-indigo-50 border-indigo-500 text-indigo-900 shadow-xs'
                  : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
              }`}
            >
              <p className="font-bold text-xs text-indigo-700 mb-1">{option.title}</p>
              <p className="text-[11px] text-slate-500 leading-snug">{option.desc}</p>
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

        {review.executedStatus ? (
          <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-mono font-bold flex items-center justify-between">
            <span className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-600" />
              {review.executedStatus}
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
              className="px-8 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-extrabold text-xs shadow-md shadow-indigo-600/20 transition-all hover:scale-105 flex items-center gap-2"
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
