'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import Spinner from '@/components/Spinner';

// Re-use the Subscription interface
interface Subscription {
  id: string; 
  target_url: string;
  secret_key?: string | null;
  created_at: string;
  updated_at: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export default function EditSubscriptionPage() {
  const router = useRouter();
  const params = useParams();
  const id = params?.id as string; // Get ID from dynamic route

  const [targetUrl, setTargetUrl] = useState('');
  const [secretKey, setSecretKey] = useState<string>(''); // Ensure it's always a string
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Fetch existing subscription data
  const fetchSubscriptionData = useCallback(async () => {
    if (!id) return; // Don't fetch if ID is not available yet
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/subscriptions/${id}`);
      if (!response.ok) {
        if (response.status === 404) {
           throw new Error('Subscription not found.');
        } 
        throw new Error(`Failed to fetch subscription: ${response.statusText}`);
      }
      const data: Subscription = await response.json();
      setTargetUrl(data.target_url);
      setSecretKey(data.secret_key || ''); // Set to empty string if null/undefined
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchSubscriptionData();
  }, [fetchSubscriptionData]);

  // Handle form submission for update
  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setSubmitError(null);
    setSuccessMessage(null);

    // Construct payload - only include fields that are being set
    const payload: { target_url?: string; secret_key?: string | null } = {};
    if (targetUrl) payload.target_url = targetUrl;
    // To explicitly remove secret, we might need a different approach or backend support.
    // For now, sending empty string means "keep as empty", sending value means "update".
    // If the field wasn't touched, don't send it? Let's send current state.
    payload.secret_key = secretKey ? secretKey : null; // Send null to clear, or the value
    
    // Basic check: if neither field has a value, maybe prevent submission?
    // Or let backend handle validation. Let's allow submitting potentially empty values.
    
    try {
      const response = await fetch(`${API_BASE_URL}/subscriptions/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to update subscription. Invalid response.' }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      setSuccessMessage('Subscription updated successfully!');
      // Optionally redirect after a delay
      setTimeout(() => {
        router.push('/subscriptions');
      }, 1500);

    } catch (err: any) {
      console.error("Update error:", err);
      setSubmitError(err.message || 'An unexpected error occurred during update');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center p-8 min-h-[300px]">
        <Spinner />
      </div>
    );
  }

  if (error) {
    return (
      <main className="container mx-auto p-8 max-w-lg">
         <div className="flex justify-between items-center mb-6">
           <h1 className="text-3xl font-bold">Edit Subscription</h1>
           <Link href="/subscriptions" className="text-blue-500 hover:underline">
             &larr; Back to List
           </Link>
         </div>
         <p className="text-center text-red-500 p-8">Error loading data: {error}</p>
       </main>
     );
  }

  return (
    <main className="container mx-auto p-8 max-w-lg">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Edit Subscription</h1>
        <Link href="/subscriptions" className="text-blue-500 hover:underline">
          &larr; Back to List
        </Link>
      </div>

      {submitError && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
          <strong className="font-bold">Update Error! </strong>
          <span className="block sm:inline">{submitError}</span>
        </div>
      )}
      {successMessage && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative mb-4" role="alert">
          <strong className="font-bold">Success! </strong>
          <span className="block sm:inline">{successMessage}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="targetUrl" className="block text-sm font-medium text-gray-700">
            Target URL <span className="text-red-500">*</span>
          </label>
          <input
            type="url"
            id="targetUrl"
            value={targetUrl}
            onChange={(e) => setTargetUrl(e.target.value)}
            required
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          />
        </div>

        <div>
          <label htmlFor="secretKey" className="block text-sm font-medium text-gray-700">
            Secret Key (Optional)
          </label>
          <input
            type="text"
            id="secretKey"
            value={secretKey}
            onChange={(e) => setSecretKey(e.target.value)}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            placeholder="Leave blank to remove, or enter new secret"
          />
           <p className="mt-1 text-xs text-gray-500">Enter value to set/update. Leave blank to remove secret.</p>
        </div>
        
         {/* Display existing ID (read-only) */}
         <div>
            <label className="block text-sm font-medium text-gray-700">Subscription ID</label>
            <input 
                type="text"
                readOnly 
                value={id}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-100 sm:text-sm"
            />
         </div>

        <div>
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? (
              <Spinner size="sm" color="border-white" />
            ) : (
              'Save Changes'
            )}
          </button>
        </div>
      </form>
    </main>
  );
} 