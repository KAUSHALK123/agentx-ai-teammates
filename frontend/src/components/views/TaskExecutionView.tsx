import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { 
  PlayCircle, 
  CheckCircle2, 
  Clock, 
  ShieldAlert, 
  Wrench, 
  ChevronDown, 
  ChevronUp, 
  Bot, 
  Sparkles, 
  ShieldCheck, 
  ArrowRight, 
  RotateCcw,
  Check,
  X,
  AlertTriangle,
  ListChecks,
  AlertCircle,
  BookOpen
} from 'lucide-react';
import { tasksApi } from '../../api';

export const TaskExecutionView: React.FC = () => {
  const { 
    selectedTaskId, 
    tasks, 
    setSelectedTaskId, 
    setActiveTab, 
    setActiveApprovalModal,
    approveTaskAction,
    rejectTaskAction,
    startLiveSimulation,
    isBackendConnected,
    refreshTasks
  } = useApp();

  const [expandedStepId, setExpandedStepId] = useState<string | null>('step-3');
  const [rejectionReason, setRejectionReason] = useState('');
  const [showRejectInput, setShowRejectInput] = useState(false);
  const [isLoadingTrace, setIsLoadingTrace] = useState(false);

  const task = (tasks || []).find(t => t.id === selectedTaskId) || (tasks && tasks.length > 0 ? tasks[0] : null);

  // Fetch execution details when selectedTaskId changes
  useEffect(() => {
    let isMounted = true;
    if (selectedTaskId && isBackendConnected && task) {
      setIsLoadingTrace(true);
      tasksApi.getTaskExecution(selectedTaskId)
        .then(() => {
          if (isMounted) setIsLoadingTrace(false);
        })
        .catch(() => {
          if (isMounted) setIsLoadingTrace(false);
        });
    }
    return () => { isMounted = false; };
  }, [selectedTaskId, isBackendConnected]);

  if (!task) {
    return (
      <div className="p-8 max-w-xl mx-auto glass-card rounded-2xl border border-slate-200 text-center space-y-4 my-12">
        <Bot className="w-12 h-12 text-slate-400 mx-auto" />
        <h3 className="text-lg font-bold text-slate-900">No Task Selected</h3>
        <p className="text-xs text-slate-500 max-w-md mx-auto">
          No autonomous task is currently selected. Dispatch a new task or browse task history to inspect real-time execution logs.
        </p>
        <div className="flex justify-center gap-3 pt-2">
          <button
            onClick={() => setActiveTab('create-task')}
            className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-sm transition-all cursor-pointer"
          >
            Create New Task
          </button>
          <button
            onClick={() => setActiveTab('task-history')}
            className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold border border-slate-200 transition-all cursor-pointer"
          >
            View Task History
          </button>
        </div>
      </div>
    );
  }

  const stepsList = task.steps || [];
  const currentStep = stepsList.find(s => s.status === 'IN_PROGRESS') || stepsList[task.currentStepIndex - 1] || stepsList[0];
  const isWaitingApproval = (task.status === 'WAITING_FOR_APPROVAL' || (task.status as string) === 'APPROVAL_REQUIRED') && task.approvalRequest;

  const toggleExpand = (id: string) => {
    setExpandedStepId(expandedStepId === id ? null : id);
  };

  return (
    <div className="p-6 md:p-8 max-w-6xl mx-auto space-y-8">
      {/* Header & Task Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
              {task.id}
            </span>
            <span className="text-xs text-slate-500 font-medium">Assigned to {task.agentName}</span>
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">{task.title}</h2>
          <p className="text-xs text-slate-600 mt-1 max-w-2xl font-normal leading-relaxed">{task.description}</p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={task.id}
            onChange={(e) => setSelectedTaskId(e.target.value)}
            className="bg-white text-slate-800 text-xs font-bold rounded-xl px-3.5 py-2 border border-slate-200 focus:outline-none focus:border-indigo-500 cursor-pointer shadow-xs"
          >
            {tasks.map(t => (
              <option key={t.id} value={t.id}>
                {t.id} - {t.title.slice(0, 30)}... ({t.status})
              </option>
            ))}
          </select>

          <button
            onClick={() => {
              if (isBackendConnected) refreshTasks();
              else startLiveSimulation(task.id);
            }}
            className="p-2.5 rounded-xl bg-white border border-slate-200 text-slate-600 hover:text-indigo-600 hover:border-indigo-300 shadow-xs transition-colors cursor-pointer"
            title="Refresh Task Status"
          >
            <RotateCcw className={`w-4 h-4 ${isLoadingTrace ? 'animate-spin text-indigo-600' : ''}`} />
          </button>
        </div>
      </div>

      {/* Overview Stat Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
        <div>
          <p className="text-[10px] uppercase font-mono text-slate-500 font-bold">Execution Status</p>
          <div className="flex items-center gap-2 mt-1">
            <span className={`w-2 h-2 rounded-full ${
              task.status === 'COMPLETED' ? 'bg-emerald-500' :
              task.status === 'WAITING_FOR_APPROVAL' ? 'bg-amber-500 animate-ping' :
              task.status === 'FAILED' ? 'bg-red-500' :
              task.status === 'ESCALATED' ? 'bg-purple-500' :
              'bg-indigo-600 animate-pulse'
            }`}></span>
            <span className="text-sm font-bold text-slate-900 uppercase font-mono">{task.status}</span>
          </div>
        </div>

        <div>
          <p className="text-[10px] uppercase font-mono text-slate-500 font-bold">Assigned Agent</p>
          <p className="text-sm font-bold text-indigo-600 mt-1 flex items-center gap-1">
            <Bot className="w-4 h-4 text-indigo-600" />
            {task.agentName}
          </p>
        </div>

        <div>
          <p className="text-[10px] uppercase font-mono text-slate-500 font-bold">Started Time</p>
          <p className="text-sm font-bold text-slate-800 mt-1 flex items-center gap-1">
            <Clock className="w-4 h-4 text-slate-400" />
            {task.createdAt}
          </p>
        </div>

        <div>
          <p className="text-[10px] uppercase font-mono text-slate-500 font-bold">Duration</p>
          <p className="text-sm font-bold text-emerald-600 mt-1">
            {(task.durationMs / 1000).toFixed(1)} seconds
          </p>
        </div>
      </div>

      {/* Human Approval Needed Banner */}
      {isWaitingApproval && task.approvalRequest && (
        <div className="glass-card p-6 rounded-2xl border-2 border-amber-300 bg-amber-50/50 shadow-xl space-y-4 animate-in fade-in duration-300">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center font-bold">
                <ShieldAlert className="w-6 h-6 animate-pulse" />
              </div>
              <div>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-100 text-amber-800 border border-amber-300 uppercase">
                  APPROVAL REQUIRED • {task.approvalRequest.riskLevel}
                </span>
                <h3 className="text-base font-extrabold text-slate-900 mt-1">
                  AgentX requires human sign-off before proceeding
                </h3>
                <p className="text-xs text-slate-600 mt-0.5 font-medium">
                  Requested by <span className="text-indigo-600 font-bold">{task.approvalRequest.agentName}</span> for tool <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-amber-800 font-mono font-bold">{task.approvalRequest.toolName}</code>
                </p>
              </div>
            </div>

            <button
              onClick={() => setActiveApprovalModal(task.approvalRequest!)}
              className="text-xs text-amber-700 hover:underline font-bold flex items-center gap-1 cursor-pointer"
            >
              Open Full Modal →
            </button>
          </div>

          <div className="p-4 rounded-xl bg-white border border-slate-200 text-xs space-y-2 shadow-xs">
            <p className="text-slate-800 font-medium"><strong className="text-amber-700">Why approval is required:</strong> {task.approvalRequest.whyRequired}</p>
            <p className="text-slate-800 font-medium"><strong className="text-indigo-600">Proposed Action:</strong> {task.approvalRequest.proposedAction}</p>
            
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 font-mono text-[11px] text-indigo-900 overflow-x-auto">
              {JSON.stringify(task.approvalRequest.payloadPreview, null, 2)}
            </div>
          </div>

          <div className="flex items-center justify-between pt-2">
            {showRejectInput ? (
              <div className="flex items-center gap-2 flex-1 mr-4">
                <input
                  type="text"
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  placeholder="Optional rejection reason..."
                  className="flex-1 bg-white text-xs px-3 py-2 rounded-lg border border-slate-200 text-slate-800 focus:outline-none focus:border-red-500 font-medium"
                />
                <button
                  onClick={() => rejectTaskAction(task.approvalRequest!.id, rejectionReason)}
                  className="px-4 py-2 rounded-lg bg-red-600 text-white text-xs font-bold hover:bg-red-700 shadow-xs cursor-pointer"
                >
                  Confirm Reject
                </button>
                <button
                  onClick={() => setShowRejectInput(false)}
                  className="px-3 py-2 text-xs text-slate-500 font-medium cursor-pointer"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowRejectInput(true)}
                className="px-4 py-2 rounded-xl bg-white hover:bg-red-50 text-red-600 text-xs font-bold border border-red-200 transition-colors flex items-center gap-1.5 shadow-xs cursor-pointer"
              >
                <X className="w-4 h-4" />
                <span>Reject Action</span>
              </button>
            )}

            <button
              onClick={() => approveTaskAction(task.approvalRequest!.id)}
              className="px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold text-xs shadow-md shadow-emerald-600/20 transition-all hover:scale-105 flex items-center gap-2 cursor-pointer"
            >
              <Check className="w-4 h-4 stroke-[3]" />
              <span>Approve & Continue Task</span>
            </button>
          </div>
        </div>
      )}

      {/* Active Step & Progress Bar */}
      <div className="glass-card p-6 rounded-2xl border border-slate-200 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-600 animate-spin" />
            <span>Execution Progress & Current Action</span>
          </h3>
          <span className="text-xs font-mono font-bold text-slate-500">
            Step {task.currentStepIndex || 1} of {stepsList.length || 1}
          </span>
        </div>

        <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden border border-slate-200">
          <div
            className="bg-gradient-to-r from-indigo-600 via-purple-600 to-emerald-500 h-full transition-all duration-500"
            style={{ width: `${stepsList.length > 0 ? Math.min(100, ((task.currentStepIndex || 1) / stepsList.length) * 100) : 0}%` }}
          ></div>
        </div>

        {currentStep && (
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-[10px] uppercase font-mono text-slate-500 font-bold">Active Action</p>
              <p className="text-xs font-bold text-slate-900">{currentStep.label}</p>
              <p className="text-xs text-indigo-700 font-medium">{currentStep.actionSummary}</p>
            </div>

            {currentStep.toolUsed && (
              <div className="px-3 py-1.5 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-700 text-xs font-mono font-bold flex items-center gap-1.5">
                <Wrench className="w-3.5 h-3.5" />
                <span>Tool: {currentStep.toolUsed}</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Timeline Breakdown */}
      <div className="glass-card p-6 rounded-2xl border border-slate-200 space-y-6">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
            <PlayCircle className="w-5 h-5 text-indigo-600" />
            <span>Execution Timeline</span>
          </h3>
          <span className="text-xs text-slate-500 font-mono font-bold">Clean Business Steps (No Chain-of-Thought Exposed)</span>
        </div>

        <div className="space-y-4 relative before:absolute before:left-4 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-200">
          {stepsList.map((step) => {
            const isDone = step.status === 'COMPLETED';
            const isInProgress = step.status === 'IN_PROGRESS';
            const isWaiting = step.status === 'WAITING';
            const isFailed = step.status === 'FAILED';
            const isExpanded = expandedStepId === step.id;

            return (
              <div key={step.id} className="relative pl-10">
                <div className={`absolute left-0 top-1 w-8 h-8 rounded-full flex items-center justify-center font-mono text-xs font-bold border z-10 transition-all ${
                  isDone ? 'bg-emerald-50 text-emerald-600 border-emerald-300' :
                  isInProgress ? 'bg-indigo-50 text-indigo-600 border-indigo-400 animate-pulse' :
                  isWaiting ? 'bg-amber-50 text-amber-700 border-amber-300' :
                  isFailed ? 'bg-red-50 text-red-600 border-red-300' :
                  'bg-slate-100 text-slate-400 border-slate-200'
                }`}>
                  {isDone ? <CheckCircle2 className="w-4 h-4 text-emerald-600" /> :
                   isFailed ? <AlertCircle className="w-4 h-4 text-red-600" /> :
                   isInProgress ? <span className="w-2 h-2 rounded-full bg-indigo-600 animate-ping"></span> :
                   step.stepIndex}
                </div>

                <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 hover:border-slate-300 transition-colors shadow-xs">
                  <div className="flex items-center justify-between cursor-pointer" onClick={() => toggleExpand(step.id)}>
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-900">
                          Step {step.stepIndex}: {step.label}
                        </span>
                        {step.toolUsed && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                            {step.toolUsed}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-600 font-medium">{step.actionSummary}</p>
                    </div>

                    <div className="flex items-center gap-3">
                      <span className="text-[10px] font-mono font-bold text-slate-400">{step.timestamp}</span>
                      {isExpanded ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                    </div>
                  </div>

                  {isExpanded && step.details && (
                    <div className="mt-4 pt-4 border-t border-slate-200 space-y-3 text-xs">
                      {step.details.input && (
                        <div>
                          <p className="text-[10px] font-mono font-bold text-slate-500 uppercase">Input Payload:</p>
                          <pre className="bg-slate-100 p-2.5 rounded-lg border border-slate-200 text-[11px] font-mono text-indigo-900 mt-1 overflow-x-auto font-medium">
                            {JSON.stringify(step.details.input, null, 2)}
                          </pre>
                        </div>
                      )}
                      {step.details.output && (
                        <div>
                          <p className="text-[10px] font-mono font-bold text-slate-500 uppercase">Tool Output:</p>
                          <pre className="bg-slate-100 p-2.5 rounded-lg border border-slate-200 text-[11px] font-mono text-emerald-800 mt-1 overflow-x-auto font-medium">
                            {JSON.stringify(step.details.output, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Verification Status Card */}
      {task.verificationReport && (
        <div className="glass-card p-6 rounded-2xl border border-slate-200 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <ListChecks className="w-4 h-4 text-indigo-600" />
              <span>Automated Verification Audit</span>
            </h3>
            <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold ${
              task.verificationReport.verified
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                : 'bg-amber-50 text-amber-700 border border-amber-200'
            }`}>
              {task.verificationReport.verified ? 'VERIFIED PASSED' : 'VERIFICATION PENDING'}
            </span>
          </div>

          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-slate-500 font-mono font-bold">Safety Risk Score:</span>
              <span className="font-mono font-bold text-slate-900">{task.verificationReport.riskScore ?? 0.0}</span>
            </div>
            {task.verificationReport.notes && (
              <p className="text-slate-700 font-medium"><strong>Notes:</strong> {task.verificationReport.notes}</p>
            )}
            {task.verificationReport.criteriaChecked && task.verificationReport.criteriaChecked.length > 0 && (
              <div className="space-y-1 pt-1">
                <p className="text-[10px] font-mono font-bold text-slate-500 uppercase">Checked Criteria:</p>
                <div className="flex flex-wrap gap-1.5">
                  {task.verificationReport.criteriaChecked.map((c, idx) => (
                    <span key={idx} className="px-2 py-0.5 bg-white border border-slate-200 rounded text-[11px] font-medium text-slate-800 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                      {c}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Business Knowledge Evidence (Cognee) */}
      {task.knowledgeUsed && task.knowledgeUsed.length > 0 && (
        <div className="glass-card p-6 rounded-2xl border border-indigo-200 bg-indigo-50/40 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-indigo-950 flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-indigo-600" />
              <span>Business Knowledge Evidence (Powered by Cognee)</span>
            </h3>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-indigo-100 text-indigo-800 border border-indigo-200">
              {task.knowledgeUsed.length} Policy Documents Applied
            </span>
          </div>

          <div className="space-y-2">
            {task.knowledgeUsed.map((k, idx) => (
              <div key={idx} className="p-3.5 bg-white rounded-xl border border-indigo-100 text-xs space-y-1 shadow-xs">
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-100 text-[11px]">
                    {k.source}
                  </span>
                  {typeof k.score === 'number' && (
                    <span className="text-[10px] font-mono text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                      Relevance: {(k.score * 100).toFixed(0)}%
                    </span>
                  )}
                </div>
                {k.content && (
                  <p className="text-slate-700 text-[11px] leading-relaxed font-medium pt-1 italic">
                    "{k.content.slice(0, 200)}{k.content.length > 200 ? '...' : ''}"
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Completed State */}
      {task.status === 'COMPLETED' && (
        <div className="glass-card p-6 rounded-2xl border-2 border-emerald-300 bg-emerald-50/50 space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Task Completed & Verified</h3>
              <p className="text-xs text-emerald-700 font-medium">All business criteria and safety guardrails passed.</p>
            </div>
          </div>

          <p className="text-xs text-slate-800 bg-white p-4 rounded-xl border border-slate-200 leading-relaxed font-semibold shadow-xs">
            {task.resultSummary || 'Task successfully executed.'}
          </p>

          {task.supportReview && (
            <button
              onClick={() => setActiveTab('support-review')}
              className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-xs transition-all flex items-center gap-1.5 cursor-pointer"
            >
              <span>View Support Review Collaboration View</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          )}
        </div>
      )}

      {/* Failed State */}
      {task.status === 'FAILED' && (
        <div className="glass-card p-6 rounded-2xl border-2 border-red-300 bg-red-50/50 space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-red-100 text-red-700 flex items-center justify-center font-bold">
              <AlertCircle className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Execution Failed</h3>
              <p className="text-xs text-red-700 font-medium">Task encountered an execution error or guardrail failure.</p>
            </div>
          </div>

          <p className="text-xs text-slate-800 bg-white p-4 rounded-xl border border-slate-200 leading-relaxed font-semibold shadow-xs">
            {task.resultSummary || 'Task execution failed. Please check error logs.'}
          </p>
        </div>
      )}

      {/* Escalated State */}
      {task.status === 'ESCALATED' && (
        <div className="glass-card p-6 rounded-2xl border-2 border-purple-300 bg-purple-50/50 space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center font-bold">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Task Escalated to Human Supervisor</h3>
              <p className="text-xs text-purple-700 font-medium">Proposed action was rejected by human operator or triggered policy escalation.</p>
            </div>
          </div>

          <p className="text-xs text-slate-800 bg-white p-4 rounded-xl border border-slate-200 leading-relaxed font-semibold shadow-xs">
            {task.resultSummary || 'Task stopped following human rejection.'}
          </p>
        </div>
      )}
    </div>
  );
};
