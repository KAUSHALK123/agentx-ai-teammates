import tasksApi from './tasks';
import approvalsApi from './approvals';

export interface ActivityFeedItem {
  id: string;
  type: 'TASK_CREATED' | 'TASK_EXECUTING' | 'TOOL_EXECUTED' | 'APPROVAL_REQUESTED' | 'APPROVAL_RESOLVED' | 'TASK_COMPLETED' | 'TASK_FAILED' | 'TASK_ESCALATED';
  title: string;
  description: string;
  timestamp: string;
  agentId?: string;
  taskId?: string;
  status?: string;
}

export const activityApi = {
  /**
   * Aggregate recent workspace activity from task events and approval records.
   */
  async getRecentActivity(limit: number = 20): Promise<ActivityFeedItem[]> {
    try {
      const [tasks, approvals] = await Promise.all([
        tasksApi.listTasks(20).catch(() => []),
        approvalsApi.listApprovals().catch(() => []),
      ]);

      const items: ActivityFeedItem[] = [];

      // Extract events from tasks
      for (const t of tasks) {
        if (t.events && t.events.length > 0) {
          for (const ev of t.events) {
            let type: ActivityFeedItem['type'] = 'TASK_EXECUTING';
            if (ev.event_type.includes('CREATE')) type = 'TASK_CREATED';
            else if (ev.event_type.includes('TOOL')) type = 'TOOL_EXECUTED';
            else if (ev.event_type.includes('APPROVAL')) type = 'APPROVAL_REQUESTED';
            else if (ev.event_type.includes('COMPLET')) type = 'TASK_COMPLETED';
            else if (ev.event_type.includes('FAIL')) type = 'TASK_FAILED';
            else if (ev.event_type.includes('ESCALAT')) type = 'TASK_ESCALATED';

            items.push({
              id: `${t.task_id}-${ev.timestamp}-${ev.event_type}`,
              type,
              title: ev.event_type.replace(/_/g, ' '),
              description: ev.description,
              timestamp: ev.timestamp,
              agentId: t.selected_agent || undefined,
              taskId: t.task_id,
              status: t.status,
            });
          }
        } else {
          // If no granular events, synthesize from task state
          items.push({
            id: `task-${t.task_id}`,
            type: t.status === 'COMPLETED' ? 'TASK_COMPLETED' : t.status === 'WAITING_FOR_APPROVAL' ? 'APPROVAL_REQUESTED' : 'TASK_CREATED',
            title: `Task ${t.task_id} (${t.status})`,
            description: t.user_request.slice(0, 80),
            timestamp: t.updated_at || t.created_at,
            agentId: t.selected_agent || undefined,
            taskId: t.task_id,
            status: t.status,
          });
        }
      }

      // Add approval events
      for (const a of approvals) {
        items.push({
          id: `approval-${a.approval_id}`,
          type: a.status === 'PENDING' ? 'APPROVAL_REQUESTED' : 'APPROVAL_RESOLVED',
          title: `Approval ${a.status}: ${a.action}`,
          description: `Action on tool ${a.tool_id} (${a.risk_level}) for task ${a.task_id}`,
          timestamp: a.resolved_at || a.created_at,
          agentId: a.agent_id,
          taskId: a.task_id,
          status: a.status,
        });
      }

      // Sort descending by timestamp
      items.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

      return items.slice(0, limit);
    } catch {
      return [];
    }
  },
};

export default activityApi;
