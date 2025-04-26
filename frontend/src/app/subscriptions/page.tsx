'use client'; // Indicate this is a Client Component

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import Spinner from '@/components/Spinner'; // Import the Spinner component
import ConfirmModal from '@/components/ConfirmModal'; // Import the modal

// Define an interface for the subscription data matching our backend model
interface Subscription {
  id: string; // uuid
  target_url: string;
  secret_key?: string | null;
  created_at: string; // datetime string
  updated_at: string; // datetime string
}

// Define the base URL for the backend API
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// Component for the Test Ingestion Form
function TestIngestForm({ subscriptionId, hasSecret }: { subscriptionId: string, hasSecret: boolean }) {
  const [payload, setPayload] = useState('{\n  "message": "Hello from UI Test!",\n  "timestamp": "' + new Date().toISOString() + '"\n}');
  const [signatureHash, setSignatureHash] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [sendResult, setSendResult] = useState<{ success: boolean, message: string } | null>(null);

  const handleSend = async () => {
    setIsSending(true);
    setSendResult(null);
    let isValidJson = false;
    let parsedPayload = {};

    try {
      parsedPayload = JSON.parse(payload);
      isValidJson = true;
    } catch (e) {
       setSendResult({ success: false, message: 'Invalid JSON payload format.' });
       setIsSending(false);
       return;
    }

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    // Construct and add signature header if hash is provided
    if (signatureHash) {
      // Automatically prepend 'sha256='
      headers['X-Webhook-Signature-256'] = `sha256=${signatureHash}`;
    }

    // --- Modified Error Handling --- 
    let responseStatus: number | null = null;
    let errorMessage = 'Ingestion failed: An unknown error occurred.'; 
    try {
      const response = await fetch(`${API_BASE_URL}/ingest/${subscriptionId}`, {
        method: 'POST',
        headers: headers,
        body: payload,
      });
      responseStatus = response.status; // Store status code

      if (response.status === 202) {
        setSendResult({ success: true, message: 'Webhook accepted (202). Check worker logs for delivery status.' });
      } else {
        // Try to get detail from response, otherwise use generic message
        const errorData = await response.json().catch(() => null);
        errorMessage = errorData?.detail || `Error ${response.status}: ${response.statusText}`;
        // No longer throw here, let the outer catch handle setting the state
        setSendResult({ success: false, message: `Ingest failed: ${errorMessage} (Status: ${responseStatus})` });
      }
    } catch (err: any) {
      // Catch fetch errors (network issue) or errors from processing the response
      console.error("Ingest error:", err);
       // Use the already prepared errorMessage if it came from a non-202 response
      // Otherwise, use the caught error's message
      if (responseStatus && responseStatus !== 202) {
          setSendResult({ success: false, message: `Ingest failed: ${errorMessage} (Status: ${responseStatus})` });
      } else {
          setSendResult({ success: false, message: `Ingest failed: ${err.message || 'Network or processing error'}` });
      }
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="mt-2 p-3 border rounded bg-gray-50 space-y-2">
      <label className="block text-xs font-medium text-gray-700">Test Payload (JSON):</label>
      <textarea
        className="w-full p-1 border rounded text-xs font-mono text-gray-900 min-h-[5em] resize-y"
        value={payload}
        onChange={(e) => setPayload(e.target.value)}
      />
      {hasSecret && (
        <div className="mt-1">
           <label className="block text-xs font-medium text-gray-700">SHA256 Signature Hash (Optional):</label>
           <input 
             type="text"
             className="w-full p-1 border rounded text-xs font-mono"
             value={signatureHash}
             onChange={(e) => setSignatureHash(e.target.value)}
             placeholder="Paste only the hex hash value here (e.g., e3b0c4...)"
            />
        </div>
      )}
      <button 
        onClick={handleSend}
        disabled={isSending}
        className="text-xs bg-green-500 hover:bg-green-700 text-white font-bold py-1 px-2 rounded disabled:opacity-50 flex items-center justify-center min-w-[100px]"
      >
        {isSending ? <Spinner size="sm" color="border-white" /> : 'Send Test Webhook'}
      </button>
      {sendResult && (
        <p className={`mt-1 text-xs ${sendResult.success ? 'text-green-700' : 'text-red-700'}`}>
          {sendResult.message}
        </p>
      )}
    </div>
  );
}

export default function SubscriptionsPage() {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null); // For delete errors
  const [deletingId, setDeletingId] = useState<string | null>(null); // Track which ID is being deleted

  // State to manage which subscription's test form is open
  const [testFormOpenId, setTestFormOpenId] = useState<string | null>(null);

  // --- Pagination State --- 
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10); // Or your preferred default
  const [totalCount, setTotalCount] = useState(0);
  const totalPages = Math.ceil(totalCount / pageSize);

  // --- Modal State --- 
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [subscriptionToDelete, setSubscriptionToDelete] = useState<Subscription | null>(null);

  // --- Modified fetchSubscriptions --- 
  const fetchSubscriptions = useCallback(async (page: number, limit: number) => {
    setIsLoading(true);
    setError(null);
    // Keep actionError and testFormOpenId? Or clear them?
    // Let's clear action error but keep test form potentially open if user is just paging
    setActionError(null); 

    try {
      // Call API with pagination params
      const response = await fetch(`${API_BASE_URL}/subscriptions?page=${page}&limit=${limit}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch subscriptions: ${response.statusText}`);
      }
      // Expect PaginatedSubscriptions response
      const data = await response.json(); 
      setSubscriptions(data.subscriptions);
      setTotalCount(data.total_count);
      setCurrentPage(page); // Ensure current page state matches fetched page
      
    } catch (err: any) {
      console.error("Fetch error:", err);
      setError(err.message || 'An unexpected error occurred');
      setSubscriptions([]); // Clear data on error
      setTotalCount(0);
    } finally {
      setIsLoading(false);
    }
  // Include pageSize in dependencies if it becomes changeable
  }, [pageSize]); // Dependencies for useCallback

  // Fetch subscriptions on component mount and when page changes
  useEffect(() => {
    fetchSubscriptions(currentPage, pageSize);
  // Update dependency array
  }, [currentPage, pageSize, fetchSubscriptions]);

  // --- Delete Logic --- 
  // Function to open the confirmation modal
  const handleDeleteClick = (subscription: Subscription) => {
    setSubscriptionToDelete(subscription);
    setIsModalOpen(true);
  };

  // Function to actually perform the deletion (called by modal confirm)
  const confirmDelete = async () => {
    if (!subscriptionToDelete) return;
    
    setDeletingId(subscriptionToDelete.id); // Show spinner in modal confirm button
    setActionError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/subscriptions/${subscriptionToDelete.id}`, {
        method: 'DELETE',
      });

      if (!response.ok && response.status !== 204) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to delete subscription. Invalid response from server.' }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      
      console.log(`Subscription ${subscriptionToDelete.id} deleted successfully.`);
      // Refresh the current page after delete
      fetchSubscriptions(currentPage, pageSize); 

    } catch (err: any) { 
      console.error("Delete error:", err);
      setActionError(`Failed to delete subscription ${subscriptionToDelete.id}: ${err.message}`);
    } finally {
       setDeletingId(null); // Stop spinner
       setIsModalOpen(false); // Close modal
       setSubscriptionToDelete(null); // Clear targeted subscription
    }
  };

  // Function to close the modal
  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSubscriptionToDelete(null);
  };

  // --- Pagination Handlers --- 
  const handleNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    }
  };

  const handlePreviousPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  return (
    <main className="container mx-auto p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Webhook Subscriptions</h1>
        <div> {/* Group buttons */} 
          <Link 
            href="/subscriptions/new" 
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mr-4"
          >
            Create New Subscription
          </Link>
          <Link href="/" className="text-blue-500 hover:underline">
            &larr; Back to Home
          </Link>
        </div>
      </div>

      {isLoading && (
        <div className="flex justify-center items-center p-8">
          <Spinner />
        </div>
      )}
      
      {/* Display fetch error */}
      {error && <p className="text-center text-red-500 mb-4">Error loading subscriptions: {error}</p>}
      
      {/* Display action error (e.g., delete failed) */}
      {actionError && <p className="text-center text-red-500 mb-4">Action failed: {actionError}</p>}

      {!isLoading && !error && subscriptions.length === 0 && (
        <p className="text-center text-gray-500">No subscriptions found.</p>
      )}

      {!isLoading && !error && subscriptions.length > 0 && (
        <>
          <div className="overflow-x-auto shadow-md rounded-lg">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Target URL
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Has Secret?
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ID
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created At
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {subscriptions.map((sub) => (
                  <tr key={sub.id} className="align-top">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900 break-all">{sub.target_url}</td>
                    <td className="px-6 py-4 text-sm text-gray-500">{sub.secret_key ? 'Yes' : 'No'}</td>
                    <td className="px-6 py-4 text-sm text-gray-500 font-mono">{sub.id}</td>
                    <td className="px-6 py-4 text-sm text-gray-500">{new Date(sub.created_at).toLocaleString()}</td>
                    <td className="px-6 py-4 text-sm font-medium space-y-1 align-top">
                       {/* Container for buttons */}
                      <div className="flex items-center space-x-2 mb-1">
                         {/* Test Button */}
                         <button 
                          onClick={() => setTestFormOpenId(testFormOpenId === sub.id ? null : sub.id)}
                          className="text-xs py-1 px-2 rounded bg-green-100 text-green-700 hover:bg-green-200"
                        >
                          {testFormOpenId === sub.id ? 'Close Test' : 'Test'}
                        </button>
                        {/* Edit Link */}
                        <Link 
                          href={`/subscriptions/${sub.id}/edit`} 
                          className="text-xs py-1 px-2 rounded bg-indigo-100 text-indigo-700 hover:bg-indigo-200"
                        >
                          Edit
                        </Link>
                        {/* Updated Delete Button */}
                        <button 
                          onClick={() => handleDeleteClick(sub)} // Open modal
                          // Spinner is now handled by the modal's confirm button
                          className="text-xs py-1 px-2 rounded bg-red-100 text-red-700 hover:bg-red-200 flex items-center justify-center min-w-[60px]"
                        >
                          Delete
                        </button>
                        {/* Attempts Link */}
                         <Link 
                          href={`/subscriptions/${sub.id}/attempts`} 
                          className="text-xs py-1 px-2 rounded bg-gray-100 text-gray-700 hover:bg-gray-200"
                        >
                          Attempts
                        </Link>
                      </div>
                      {/* Test Form (conditionally rendered below buttons) */}
                      {testFormOpenId === sub.id && (
                        <TestIngestForm 
                          subscriptionId={sub.id} 
                          hasSecret={!!sub.secret_key}
                        />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* --- Pagination Controls --- */}
          {totalPages > 1 && (
            <div className="flex justify-between items-center mt-4 text-sm">
              <button 
                onClick={handlePreviousPage} 
                disabled={currentPage === 1}
                className="px-3 py-1 border rounded shadow-sm bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <span>
                Page {currentPage} of {totalPages} (Total: {totalCount})
              </span>
              <button 
                onClick={handleNextPage} 
                disabled={currentPage === totalPages}
                className="px-3 py-1 border rounded shadow-sm bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}

      {/* --- Render Confirmation Modal --- */}
      <ConfirmModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onConfirm={confirmDelete}
        title="Confirm Deletion"
        message={`Are you sure you want to delete the subscription for "${subscriptionToDelete?.target_url}"? This action cannot be undone.`}
        confirmText="Delete"
        isConfirming={deletingId === subscriptionToDelete?.id}
      />
    </main>
  );
} 