/**
 * Network Status Component
 * Shows connectivity status to the user
 */

import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import NetInfo, { NetInfoState } from '@react-native-community/netinfo';
import { COLORS, SPACING, FONT_SIZES } from '../constants/theme';

interface NetworkStatusProps {
  children: React.ReactNode;
}

export function NetworkStatus({ children }: NetworkStatusProps) {
  const [isConnected, setIsConnected] = useState<boolean | null>(true);
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    // Subscribe to network state changes
    const unsubscribe = NetInfo.addEventListener((state: NetInfoState) => {
      const connected = state.isConnected;
      setIsConnected(connected);

      // Show banner when disconnected
      if (connected === false) {
        setShowBanner(true);
      } else if (connected === true && showBanner) {
        // Hide banner after a delay when reconnected
        setTimeout(() => {
          setShowBanner(false);
        }, 2000);
      }
    });

    // Check initial state
    NetInfo.fetch().then((state: NetInfoState) => {
      setIsConnected(state.isConnected);
    });

    return () => {
      unsubscribe();
    };
  }, [showBanner]);

  return (
    <View style={styles.container}>
      {showBanner && !isConnected && (
        <View style={styles.banner}>
          <Text style={styles.bannerText}>
            No internet connection. Some features may not work.
          </Text>
        </View>
      )}
      {children}
    </View>
  );
}

/**
 * Network Aware Component
 * Renders different content based on connectivity
 */

interface NetworkAwareProps {
  children: React.ReactNode;
  offlineFallback?: React.ReactNode;
}

export function NetworkAware({ children, offlineFallback }: NetworkAwareProps) {
  const [isConnected, setIsConnected] = useState<boolean | null>(true);

  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener((state: NetInfoState) => {
      setIsConnected(state.isConnected);
    });

    NetInfo.fetch().then((state: NetInfoState) => {
      setIsConnected(state.isConnected);
    });

    return () => unsubscribe();
  }, []);

  if (isConnected === false) {
    return offlineFallback || <OfflineMessage />;
  }

  return <>{children}</>;
}

/**
 * Offline Message Component
 * Displayed when there's no internet connection
 */
function OfflineMessage() {
  return (
    <View style={styles.offlineContainer}>
      <Text style={styles.offlineIcon}>📡</Text>
      <Text style={styles.offlineTitle}>You're Offline</Text>
      <Text style={styles.offlineMessage}>
        Please check your internet connection and try again.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  banner: {
    backgroundColor: '#FF9800',
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.lg,
  },
  bannerText: {
    color: '#fff',
    fontSize: FONT_SIZES.sm,
    textAlign: 'center',
    fontWeight: '500',
  },
  offlineContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: SPACING.xl,
    backgroundColor: COLORS.background,
  },
  offlineIcon: {
    fontSize: 64,
    marginBottom: SPACING.lg,
  },
  offlineTitle: {
    fontSize: FONT_SIZES.xl,
    fontWeight: '700',
    color: COLORS.primary,
    marginBottom: SPACING.sm,
  },
  offlineMessage: {
    fontSize: FONT_SIZES.md,
    color: COLORS.textMuted,
    textAlign: 'center',
  },
});
