'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import Spinner from '@/components/Spinner';

// Interfaces matching backend models
interface DeliveryAttempt {
  id: number;
  delivery_id: string; 
  attempt_number: number;
  timestamp: string; 
  outcome: string; 
  status_code?: number | null;
  response_body?: string | null;
  error_message?: string | null;
}

interface WebhookDelivery {
  id: string; 
  subscription_id: string;
  payload: Record<string, any>; // JSON object
  status: string; // 'pending', 'processing', 'success', 'failed_attempt', 'failed'
  created_at: string; 
  last_attempt_at?: string | null;
}

interface DeliveryStatusResponse {
  delivery: WebhookDelivery;
  attempts: DeliveryAttempt[];
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export default function DeliveryStatusPage() {
  const params = useParams();
  const delivery_id = params?.delivery_id as string;

  const [statusData, setStatusData] = useState<DeliveryStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDeliveryStatus = useCallback(async () => {
    if (!delivery_id) return;
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/status/deliveries/${delivery_id}/status`);
      if (!response.ok) {
         if (response.status === 404) {
           throw new Error('Delivery task not found.');
        }
        throw new Error(`Failed to fetch delivery status: ${response.statusText}`);
      }
      const data: DeliveryStatusResponse = await response.json();
      setStatusData(data);
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  }, [delivery_id]);

  useEffect(() => {
    fetchDeliveryStatus();
  }, [fetchDeliveryStatus]);

  // Helper to format status
  const formatStatus = (status: string) => {
    switch (status) {
      case 'success': return <span className="font-semibold text-green-600">Success</span>;
      case 'failed': return <span className="font-semibold text-red-600">Failed Permanently</span>;
      case 'pending': return <span className="font-semibold text-gray-600">Pending</span>;
      case 'processing': return <span className="font-semibold text-blue-600">Processing</span>;
      case 'failed_attempt': return <span className="font-semibold text-orange-600">Failed (Retrying)</span>;
      default: return <span className="font-semibold text-gray-500">{status}</span>;
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center p-8">
        <Spinner />
      </div>
    );
  }

  if (error) {
    return <p className="text-center text-red-500 p-8">Error: {error}</p>;
  }

  if (!statusData) {
     return <p className="text-center p-8">No data found for this delivery.</p>;
  }

  const { delivery, attempts } = statusData;

  return (
    <main className="container mx-auto p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Delivery Status</h1>
         {/* Link back to the specific subscription's attempts page */}
        <Link href={`/subscriptions/${delivery.subscription_id}/attempts`} className="text-blue-500 hover:underline">
          &larr; Back to Subscription Attempts
        </Link>
      </div>

      {/* Delivery Summary */}
      <div className="mb-8 p-4 border rounded shadow-sm bg-white">
          <h2 className="text-xl font-semibold mb-3 text-gray-800">Delivery Task Summary</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2 text-sm text-gray-700">
              <div><strong className="text-gray-900">Delivery ID:</strong> <code className="font-mono text-xs bg-gray-100 px-1 rounded text-gray-800">{delivery.id}</code></div>
              <div><strong className="text-gray-900">Subscription ID:</strong> <code className="font-mono text-xs bg-gray-100 px-1 rounded text-gray-800">{delivery.subscription_id}</code></div>
              <div><strong className="text-gray-900">Overall Status:</strong> {formatStatus(delivery.status)}</div>
              <div><strong className="text-gray-900">Webhook Received:</strong> {new Date(delivery.created_at).toLocaleString()}</div>
              <div><strong className="text-gray-900">Last Attempt:</strong> {delivery.last_attempt_at ? new Date(delivery.last_attempt_at).toLocaleString() : 'N/A'}</div>
          </div>
          <details className="mt-3">
              <summary className="cursor-pointer text-sm text-blue-600 hover:underline">View Payload</summary>
              <pre className="mt-1 text-xs bg-gray-100 p-2 rounded overflow-auto max-h-60 text-gray-800">{JSON.stringify(delivery.payload, null, 2)}</pre>
          </details>
      </div>

      {/* Attempts Table */}
       <h2 className="text-xl font-semibold mb-3 text-gray-800">Attempt History</h2>
       {attempts.length === 0 ? (
         <p className="text-gray-500">No attempts have been made yet for this delivery.</p>
       ) : (
        <div className="overflow-x-auto shadow-md rounded-lg">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                 <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">Attempt #</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">Timestamp</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">Outcome</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">Status Code</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">Error/Response</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {attempts.map((att) => (
                <tr key={att.id}>
                   <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{att.attempt_number}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{new Date(att.timestamp).toLocaleString()}</td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm font-semibold ${att.outcome === 'success' ? 'text-green-600' : 'text-red-600'}`}>
                    {att.outcome}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{att.status_code ?? 'N/A'}</td>
                  <td className="px-6 py-4 text-sm text-gray-700 break-words max-w-xs">
                    {att.error_message ? (
                        <span className="text-red-700">{att.error_message}</span>
                    ) : (
                         <details>
                           <summary className="cursor-pointer text-blue-600 hover:underline text-xs">View Response</summary>
                           <pre className="mt-1 text-xs bg-gray-100 p-2 rounded overflow-auto max-h-32 text-gray-800">{att.response_body || 'No response body captured.'}</pre>
                        </details>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
       )}
    </main>
  );
} 