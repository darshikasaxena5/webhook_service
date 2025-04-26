'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import Spinner from '@/components/Spinner';

// Define interface for Delivery Attempt data
interface DeliveryAttempt {
  id: number;
  delivery_id: string; // uuid
  attempt_number: number;
  timestamp: string; // datetime string
  outcome: string; // 'success' or 'failed'
  status_code?: number | null;
  response_body?: string | null;
  error_message?: string | null;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export default function SubscriptionAttemptsPage() {
  const params = useParams();
  const subscriptionId = params?.id as string;

  const [attempts, setAttempts] = useState<DeliveryAttempt[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [limit, setLimit] = useState(20); // How many attempts to show

  // Fetch recent attempts
  const fetchAttempts = useCallback(async () => {
    if (!subscriptionId) return;
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/status/subscriptions/${subscriptionId}/attempts?limit=${limit}`);
      if (!response.ok) {
        if (response.status === 404) {
           setError('Subscription not found or no attempts available.');
           setAttempts([]); // Clear attempts if sub not found
           return; 
        }
        throw new Error(`Failed to fetch attempts: ${response.statusText}`);
      }
      const data: DeliveryAttempt[] = await response.json();
      setAttempts(data);
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  }, [subscriptionId, limit]); // Re-fetch if id or limit changes

  useEffect(() => {
    if (subscriptionId) {
      fetchAttempts();
    }
  }, [subscriptionId, fetchAttempts]);

  if (!subscriptionId) {
     return <p className="text-center p-8">Subscription ID not found.</p>;
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center p-8">
        <Spinner />
      </div>
    );
  }

  if (error) {
    return <p className="text-center text-red-500 p-8">Error loading attempts: {error}</p>;
  }

  return (
    <main className="container mx-auto p-8">
      <div className="flex justify-between items-center mb-2">
        <h1 className="text-3xl font-bold">Recent Delivery Attempts</h1>
        <Link href="/subscriptions" className="text-blue-500 hover:underline">
          &larr; Back to Subscriptions
        </Link>
      </div>
      <p className="text-sm text-gray-600 mb-4">Subscription ID: <code className="font-mono bg-gray-100 px-1 rounded">{subscriptionId}</code></p>

      {attempts.length === 0 ? (
        <p className="text-center text-gray-500">No delivery attempts found for this subscription.</p>
      ) : (
        <div className="overflow-x-auto shadow-md rounded-lg">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Delivery ID</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Attempt #</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Outcome</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status Code</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Error/Response</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {attempts.map((att) => (
                <tr key={att.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{new Date(att.timestamp).toLocaleString()}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-500">
                    <Link href={`/deliveries/${att.delivery_id}/status`} className="text-blue-600 hover:underline">
                      {att.delivery_id}
                    </Link>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{att.attempt_number}</td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm font-semibold ${att.outcome === 'success' ? 'text-green-600' : 'text-red-600'}`}>
                    {att.outcome}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{att.status_code ?? 'N/A'}</td>
                  <td className="px-6 py-4 text-sm text-gray-500 break-words max-w-xs">
                    {att.error_message ? (
                        <span className="text-red-700">{att.error_message}</span>
                    ) : (
                         <details>
                           <summary className="cursor-pointer text-blue-600 hover:underline text-xs">View Response</summary>
                           <pre className="mt-1 text-xs bg-gray-100 p-2 rounded overflow-auto max-h-32">{att.response_body || 'No response body captured.'}</pre>
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