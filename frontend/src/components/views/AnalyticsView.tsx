import React from 'react';
import { useApp } from '../../context/AppContext';
import { 
  BarChart3, 
  TrendingUp, 
  Bot, 
  Activity,
  ArrowUpRight
} from 'lucide-react';

export const AnalyticsView: React.FC = () => {
  const { analytics } = useApp();

  return (
    <div className="p-6 md:p-8 space-y-8">
      <div>
        <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 text-[11px] font-mono font-bold mb-2">
          <BarChart3 className="w-3.5 h-3.5 text-indigo-600" />
          <span>PERFORMANCE & WORKFORCE METRICS</span>
        </div>
        <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">Analytics & Intelligence Dashboard</h2>
        <p className="text-xs text-slate-500 font-medium">
          In-depth visibility into agent execution throughput, task outcomes, completion times, and escalation rates.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="glass-card p-4 rounded-xl border border-slate-200">
          <p className="text-[10px] uppercase font-mono text-slate-500 font-bold">Tasks Completed</p>
          <p className="text-2xl font-extrabold text-slate-900 mt-1">{analytics.tasksCompleted.toLocaleString()}</p>
          <p className="text-[10px] text-emerald-600 mt-1 flex items-center gap-0.5 font-bold">
            <ArrowUpRight className="w-3 h-3" /> +12.4% MoM
          </p>
        </div>

        <div className="glass-card p-4 rounded-xl border border-slate-200">
          <p className="text-[10px] uppercase font-mono text-slate-500 font-bold">Success Rate</p>
          <p className="text-2xl font-extrabold text-emerald-600 mt-1">{analytics.successRate}%</p>
          <p className="text-[10px] text-slate-500 mt-1 font-medium">Verified by assertions</p>
        </div>

        <div className="glass-card p-4 rounded-xl border border-slate-200">
          <p className="text-[10px] uppercase font-mono text-slate-500 font-bold">Avg Completion Time</p>
          <p className="text-2xl font-extrabold text-indigo-600 mt-1">{analytics.avgCompletionTime}</p>
          <p className="text-[10px] text-slate-500 mt-1 font-medium">Dispatch to finish</p>
        </div>

        <div className="glass-card p-4 rounded-xl border border-slate-200">
          <p className="text-[10px] uppercase font-mono text-slate-500 font-bold">Actions Executed</p>
          <p className="text-2xl font-extrabold text-purple-600 mt-1">{analytics.actionsExecuted.toLocaleString()}</p>
          <p className="text-[10px] text-purple-600 mt-1 font-medium">Across tool APIs</p>
        </div>

        <div className="glass-card p-4 rounded-xl border border-slate-200">
          <p className="text-[10px] uppercase font-mono text-slate-500 font-bold">Human Escalations</p>
          <p className="text-2xl font-extrabold text-amber-600 mt-1">{analytics.escalatedTasks}</p>
          <p className="text-[10px] text-amber-600 mt-1 font-medium">0.8% of total volume</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-card p-6 rounded-2xl border border-slate-200 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-indigo-600" />
              <span>Tasks Over Time (7-Day Throughput)</span>
            </h3>
            <span className="text-[10px] font-mono text-slate-500 font-bold">Completed vs Escalated</span>
          </div>

          <div className="h-48 flex items-end justify-between gap-3 pt-6 px-2">
            {analytics.tasksOverTime.map((d, i) => {
              const heightPct = Math.min((d.completed / 800) * 100, 100);
              return (
                <div key={i} className="flex-1 flex flex-col items-center gap-2">
                  <div className="w-full bg-slate-100 rounded-t-lg h-36 flex items-end overflow-hidden border border-slate-200">
                    <div
                      className="w-full bg-gradient-to-t from-indigo-600 to-indigo-500 rounded-t-md transition-all hover:brightness-110"
                      style={{ height: `${heightPct}%` }}
                      title={`${d.date}: ${d.completed} completed, ${d.escalated} escalated`}
                    ></div>
                  </div>
                  <span className="text-[11px] font-mono text-slate-500 font-bold">{d.date}</span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="glass-card p-6 rounded-2xl border border-slate-200 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Bot className="w-4 h-4 text-purple-600" />
              <span>Task Workload Distribution by Agent</span>
            </h3>
            <span className="text-[10px] font-mono text-slate-500 font-bold">3 AI Teammates</span>
          </div>

          <div className="space-y-4">
            {analytics.tasksByAgent.map((ag, i) => {
              const total = analytics.tasksByAgent.reduce((acc, curr) => acc + curr.count, 0);
              const pct = ((ag.count / total) * 100).toFixed(1);
              return (
                <div key={i} className="space-y-1.5">
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-slate-800">{ag.role} Teammate</span>
                    <span className="font-mono text-slate-500">{ag.count} tasks ({pct}%)</span>
                  </div>
                  <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden border border-slate-200">
                    <div
                      className={`h-full ${
                        i === 0 ? 'bg-indigo-600' : i === 1 ? 'bg-blue-600' : 'bg-purple-600'
                      }`}
                      style={{ width: `${pct}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="glass-card rounded-2xl border border-slate-200 p-6 space-y-4">
        <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
          <Activity className="w-4 h-4 text-emerald-600" />
          <span>Agent Utilization & Performance Specs</span>
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-[10px] uppercase font-mono text-slate-500 font-bold">
                <th className="pb-3">Teammate</th>
                <th className="pb-3">Active Tasks</th>
                <th className="pb-3">Completion Success</th>
                <th className="pb-3">Avg Execution Speed</th>
                <th className="pb-3 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {analytics.agentUtilization.map((au, idx) => (
                <tr key={idx} className="hover:bg-slate-50/80">
                  <td className="py-3 font-bold text-slate-900 flex items-center gap-2">
                    <Bot className="w-4 h-4 text-indigo-600" />
                    {au.name}
                  </td>
                  <td className="py-3 font-mono text-slate-600 font-medium">{au.activeTasks} running</td>
                  <td className="py-3 font-mono font-bold text-emerald-600">{au.completionRate}%</td>
                  <td className="py-3 font-mono text-slate-600 font-medium">{au.avgTimeSec}s per task</td>
                  <td className="py-3 text-right">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">
                      Optimal
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
