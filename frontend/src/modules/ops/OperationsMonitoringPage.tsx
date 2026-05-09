import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { opsApi } from '../../api/ops';

export const OperationsMonitoringPage: React.FC = () => {
  // Use React Query to fetch operational data, polling safely
  const { data: metrics, isLoading: loadingMetrics } = useQuery({
    queryKey: ['ops', 'metrics'],
    queryFn: opsApi.getMetrics,
    refetchInterval: 15000, // Poll every 15s
  });

  const { data: jobs, isLoading: loadingJobs } = useQuery({
    queryKey: ['ops', 'scheduler-jobs'],
    queryFn: opsApi.getSchedulerJobs,
    refetchInterval: 30000,
  });

  const { data: errors, isLoading: loadingErrors } = useQuery({
    queryKey: ['ops', 'errors'],
    queryFn: () => opsApi.getRecentErrors(),
    refetchInterval: 15000,
  });

  if (loadingMetrics || loadingJobs || loadingErrors) {
    return <div className="p-6">Loading operations dashboard...</div>;
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold text-gray-900">Operations Dashboard</h1>
        <div className="text-sm text-gray-500">Auto-refreshing</div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-5 border border-gray-100">
          <h3 className="text-sm font-medium text-gray-500 mb-2">API Requests</h3>
          <div className="text-2xl font-bold text-gray-900">{metrics?.system.api_requests_total || 0}</div>
          <div className="text-xs text-gray-500 mt-1">Errors: {metrics?.system.api_errors_total || 0}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-5 border border-gray-100">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Avg API Latency</h3>
          <div className="text-2xl font-bold text-gray-900">{metrics?.system.avg_api_latency_ms?.toFixed(2) || 0} ms</div>
        </div>
        <div className="bg-white rounded-lg shadow p-5 border border-gray-100">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Scheduler Jobs</h3>
          <div className="text-2xl font-bold text-green-600">{jobs?.length || 0} Active</div>
          <div className="text-xs text-gray-500 mt-1">Skipped: {metrics?.scheduler.job_skipped_total || 0}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-5 border border-gray-100">
          <h3 className="text-sm font-medium text-gray-500 mb-2">OCR Success Rate</h3>
          <div className="text-2xl font-bold text-blue-600">{metrics?.idp.ocr_success_rate?.toFixed(1) || 0}%</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow border border-gray-100 p-5">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Scheduler Jobs Execution</h2>
          {jobs?.length === 0 ? (
            <p className="text-gray-500 text-sm">No active scheduler jobs.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Job Name</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Next Run</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200 text-sm">
                  {jobs?.map((job) => (
                    <tr key={job.id}>
                      <td className="px-4 py-3 text-gray-900">{job.name}</td>
                      <td className="px-4 py-3 text-gray-500">{job.next_run_time ? new Date(job.next_run_time).toLocaleString() : 'N/A'}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${job.pending ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'}`}>
                          {job.pending ? 'Pending' : 'Scheduled'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="bg-white rounded-lg shadow border border-gray-100 p-5">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Recent Operational Failures</h2>
          {errors?.length === 0 ? (
            <p className="text-gray-500 text-sm">No recent failures.</p>
          ) : (
            <div className="overflow-y-auto max-h-80">
              <ul className="divide-y divide-gray-200">
                {errors?.map((error) => (
                  <li key={error.id} className="py-3">
                    <div className="flex space-x-3">
                      <div className="flex-1 space-y-1">
                        <div className="flex items-center justify-between">
                          <h3 className="text-sm font-medium text-red-600">{error.service} :: {error.operation}</h3>
                          <p className="text-sm text-gray-500">{new Date(error.created_at).toLocaleString()}</p>
                        </div>
                        <p className="text-sm text-gray-800">{error.error_type}</p>
                        {error.retryable && (
                          <p className="text-xs text-gray-500">Retryable (Attempts: {error.retry_count})</p>
                        )}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
