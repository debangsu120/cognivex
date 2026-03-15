/**
 * Network Status Hook
 * Monitors network connectivity
 */

import { useState, useEffect, useCallback } from 'react';
import NetInfo, { NetInfoState } from '@react-native-community/netinfo';

interface NetworkStatus {
  isConnected: boolean | null;
  isInternetReachable: boolean | null;
  type: string | null;
  details: any;
}

export function useNetworkStatus() {
  const [networkStatus, setNetworkStatus] = useState<NetworkStatus>({
    isConnected: null,
    isInternetReachable: null,
    type: null,
    details: null,
  });

  const [isLoading, setIsLoading] = useState(true);

  const fetchNetworkStatus = useCallback(async () => {
    setIsLoading(true);
    try {
      const state = await NetInfo.fetch();
      setNetworkStatus({
        isConnected: state.isConnected,
        isInternetReachable: state.isInternetReachable,
        type: state.type,
        details: state.details,
      });
    } catch (error) {
      console.error('Error fetching network status:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // Fetch initial status
    fetchNetworkStatus();

    // Subscribe to changes
    const unsubscribe = NetInfo.addEventListener((state: NetInfoState) => {
      setNetworkStatus({
        isConnected: state.isConnected,
        isInternetReachable: state.isInternetReachable,
        type: state.type,
        details: state.details,
      });
    });

    return () => {
      unsubscribe();
    };
  }, [fetchNetworkStatus]);

  return {
    ...networkStatus,
    isLoading,
    refresh: fetchNetworkStatus,
    isOnline: networkStatus.isConnected === true,
  };
}

/**
 * Hook to check if should make API calls
 * Useful for preventing calls when offline
 */
export function useOnlineStatus() {
  const { isConnected, isInternetReachable } = useNetworkStatus();

  const canMakeRequests = isConnected && isInternetReachable;

  return {
    isOnline: canMakeRequests,
    isConnected: isConnected ?? false,
    isInternetReachable: isInternetReachable ?? false,
  };
}
