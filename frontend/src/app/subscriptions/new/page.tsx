'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation'; // Use next/navigation for App Router
import Link from 'next/link';
import Spinner from '@/components/Spinner'; // Import Spinner

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export default function NewSubscriptionPage() {
  const [targetUrl, setTargetUrl] = useState('');
  const [secretKey, setSecretKey] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const router = useRouter();

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setSuccessMessage(null);

    const payload = {
      target_url: targetUrl,
      // Only include secret_key if it's not empty
      ...(secretKey && { secret_key: secretKey }),
    };

    try {
      const response = await fetch(`${API_BASE_URL}/subscriptions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to create subscription. Invalid response from server.' }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      // Handle success
      const createdSubscription = await response.json();
      setSuccessMessage(`Subscription created successfully! ID: ${createdSubscription.id}`);
      setTargetUrl(''); // Clear form
      setSecretKey('');
      // Optionally redirect after a short delay
      setTimeout(() => {
        router.push('/subscriptions'); // Redirect back to the list
      }, 2000); 

    } catch (err: any) {
      console.error("Submit error:", err);
      setError(err.message || 'An unexpected error occurred');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="container mx-auto p-8 max-w-lg">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Create New Subscription</h1>
        <Link href="/subscriptions" className="text-blue-500 hover:underline">
          &larr; Back to List
        </Link>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
          <strong className="font-bold">Error! </strong>
          <span className="block sm:inline">{error}</span>
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
            type="url" // Use type="url" for basic validation
            id="targetUrl"
            value={targetUrl}
            onChange={(e) => setTargetUrl(e.target.value)}
            required
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            placeholder="https://example.com/webhook-receiver"
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
            placeholder="Leave blank if no signature verification needed"
          />
          <p className="mt-1 text-xs text-gray-500">Used for HMAC-SHA256 signature verification.</p>
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
              'Create Subscription'
            )}
          </button>
        </div>
      </form>
    </main>
  );
} 