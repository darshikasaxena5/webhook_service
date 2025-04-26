'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from "next/link";
import Spinner from '@/components/Spinner';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// --- Interfaces for new data --- 
interface SystemStats {
  totalSubscriptions: number;
  recentSuccessCount: number;
  recentFailedCount: number;
  // Add more stats as needed
}

// Simplified activity item - adjust as needed based on backend
interface ActivityItem {
  type: 'subscription_created' | 'delivery_attempt';
  id: string; // Can be subscription ID or delivery ID
  timestamp: string;
  details: string; // e.g., "Target: http://..." or "Attempt #1 - Success (200)"
}

export default function HomePage() {
  // --- State for new sections --- 
  const [healthStatus, setHealthStatus] = useState<string | null>(null);
  const [isCheckingHealth, setIsCheckingHealth] = useState(true);
  const [healthError, setHealthError] = useState<string | null>(null);

  const [stats, setStats] = useState<SystemStats | null>(null);
  const [isLoadingStats, setIsLoadingStats] = useState(true);
  const [statsError, setStatsError] = useState<string | null>(null);

  const [recentActivity, setRecentActivity] = useState<ActivityItem[]>([]);
  const [isLoadingActivity, setIsLoadingActivity] = useState(true);
  const [activityError, setActivityError] = useState<string | null>(null);

  // --- Fetch Functions --- 

  const checkHealth = useCallback(async () => {
    setIsCheckingHealth(true);
    setHealthError(null);
    try {
      // NOTE: Assumes a simple GET /health endpoint returning 200 OK on success
      const response = await fetch(`${API_BASE_URL}/health`);
      if (!response.ok) {
        throw new Error(`Backend health check failed: ${response.statusText}`);
      }
      setHealthStatus('Operational');
    } catch (err: any) {
      console.error("Health check error:", err);
      setHealthStatus('Error');
      setHealthError(err.message || 'Could not connect to backend.');
    } finally {
      setIsCheckingHealth(false);
    }
  }, []);

  const fetchStats = useCallback(async () => {
    setIsLoadingStats(true);
    setStatsError(null);
    try {
      // NOTE: Assumes GET /status/stats endpoint returning SystemStats
      const response = await fetch(`${API_BASE_URL}/status/stats`);
      if (!response.ok) {
        throw new Error(`Failed to fetch stats: ${response.statusText}`);
      }
      const data: SystemStats = await response.json();
      setStats(data);
    } catch (err: any) {
      console.error("Stats fetch error:", err);
      setStatsError(err.message || 'Could not load system statistics.');
    } finally {
      setIsLoadingStats(false);
    }
  }, []);

  const fetchActivity = useCallback(async () => {
    setIsLoadingActivity(true);
    setActivityError(null);
    try {
      // NOTE: Assumes GET /status/activity?limit=5 endpoint returning ActivityItem[]
      const response = await fetch(`${API_BASE_URL}/status/activity?limit=5`);
      if (!response.ok) {
        throw new Error(`Failed to fetch activity: ${response.statusText}`);
      }
      const data: ActivityItem[] = await response.json();
      setRecentActivity(data);
    } catch (err: any) {
      console.error("Activity fetch error:", err);
      setActivityError(err.message || 'Could not load recent activity.');
    } finally {
      setIsLoadingActivity(false);
    }
  }, []);

  // --- Initial Data Fetch --- 
  useEffect(() => {
    checkHealth();
    fetchStats();
    fetchActivity();
  }, [checkHealth, fetchStats, fetchActivity]); // Depend on the useCallback functions


  return (
    <main className="flex min-h-screen flex-col items-center p-12 md:p-24 bg-black">
      <h1 className="text-4xl font-bold mb-6 text-gray-100">Webhook Delivery Service</h1>
      
      {/* --- Quick Actions --- */}
      <nav className="mb-10 flex space-x-4">
        <Link href="/subscriptions/new" className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded shadow">
          Create New Subscription
        </Link>
        <Link href="/subscriptions" className="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded shadow">
          View Subscriptions
        </Link>
      </nav>

      {/* --- Dashboard Sections --- */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-4xl">
        
        {/* Health Check Section */}
        <div className="bg-gray-800 p-4 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-2 text-gray-200">System Status</h2>
          {isCheckingHealth ? (
            <div className="flex items-center space-x-2 text-sm text-gray-400">
              <Spinner size="sm" /> 
              <span>Checking...</span>
            </div>
          ) : healthError ? (
            <div className="text-sm">
              <span className="font-semibold text-red-400">Error</span>
              <p className="text-xs text-red-400 mt-1">({healthError})</p>
            </div>
          ) : (
            <span className={`font-semibold text-sm ${healthStatus === 'Operational' ? 'text-green-400' : 'text-red-400'}`}>
               {healthStatus}
            </span>
          )}
        </div>

        {/* Stats Section */}
        <div className="bg-gray-800 p-4 rounded-lg shadow">
           <h2 className="text-lg font-semibold mb-2 text-gray-200">Statistics</h2>
           {isLoadingStats ? (
            <div className="flex items-center space-x-2 text-sm text-gray-400">
               <Spinner size="sm" />
               <span>Loading Stats...</span>
             </div>
           ) : statsError ? (
             <p className="text-sm text-red-400">Error loading stats: {statsError}</p>
           ) : stats ? (
             <ul className="text-sm space-y-1 text-gray-300">
               <li>Active Subscriptions: <strong className="text-gray-100">{stats.totalSubscriptions}</strong></li>
               <li>Recent Successes: <strong className="text-green-400">{stats.recentSuccessCount}</strong></li>
               <li>Recent Failures: <strong className="text-red-400">{stats.recentFailedCount}</strong></li>
             </ul>
           ) : (
             <p className="text-sm text-gray-400">No stats available.</p>
           )}
        </div>

        {/* Recent Activity Section */}
        <div className="bg-gray-800 p-4 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-2 text-gray-200">Recent Activity</h2>
           {isLoadingActivity ? (
             <div className="flex items-center space-x-2 text-sm text-gray-400">
               <Spinner size="sm" />
               <span>Loading Activity...</span>
             </div>
           ) : activityError ? (
             <p className="text-sm text-red-400">Error loading activity: {activityError}</p>
           ) : recentActivity.length > 0 ? (
             <ul className="text-xs space-y-2 text-gray-400">
              {recentActivity.map((item, index) => (
                <li key={index} className="border-b border-gray-700 pb-1 mb-1 last:border-b-0">
                  <span className="block text-gray-200 font-medium">{new Date(item.timestamp).toLocaleString()}</span>
                  <span className="block">{item.details}</span>
                </li>
              ))}
            </ul>
           ) : (
             <p className="text-sm text-gray-400">No recent activity found.</p>
           )}
        </div>

      </div>
      
    </main>
  );
}
