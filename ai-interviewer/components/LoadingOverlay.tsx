/**
 * Loading Overlay Component
 * Full-screen loading indicator with optional message
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from '../constants/theme';

interface LoadingOverlayProps {
  visible: boolean;
  message?: string;
  showCancel?: boolean;
  onCancel?: () => void;
  progress?: number;
}

export function LoadingOverlay({
  visible,
  message = 'Loading...',
  showCancel = false,
  onCancel,
  progress,
}: LoadingOverlayProps) {
  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      statusBarTranslucent
    >
      <View style={styles.overlay}>
        <View style={styles.container}>
          {progress !== undefined ? (
            // Progress indicator
            <View style={styles.progressContainer}>
              <View style={styles.progressCircle}>
                <Text style={styles.progressText}>{progress}%</Text>
              </View>
              <View style={styles.progressBar}>
                <View
                  style={[styles.progressFill, { width: `${progress}%` }]}
                />
              </View>
            </View>
          ) : (
            // Spinner
            <ActivityIndicator
              size="large"
              color={COLORS.primary}
            />
          )}

          <Text style={styles.message}>{message}</Text>

          {showCancel && onCancel && (
            <TouchableOpacity
              style={styles.cancelButton}
              onPress={onCancel}
            >
              <Text style={styles.cancelText}>Cancel</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>
    </Modal>
  );
}

/**
 * Inline Loading Spinner
 * Smaller loading indicator for inline use
 */

interface LoadingSpinnerProps {
  size?: 'small' | 'large';
  message?: string;
  fullScreen?: boolean;
}

export function LoadingSpinner({
  size = 'large',
  message,
  fullScreen = false,
}: LoadingSpinnerProps) {
  const content = (
    <>
      <ActivityIndicator
        size={size}
        color={COLORS.primary}
      />
      {message && (
        <Text style={styles.spinnerMessage}>{message}</Text>
      )}
    </>
  );

  if (fullScreen) {
    return <View style={styles.spinnerFullScreen}>{content}</View>;
  }

  return <View style={styles.spinnerContainer}>{content}</View>;
}

/**
 * Skeleton Loader
 * Placeholder while content loads
 */

interface SkeletonProps {
  width?: number | string;
  height?: number;
  borderRadius?: number;
  style?: object;
}

export function Skeleton({
  width = '100%',
  height = 20,
  borderRadius = 4,
  style,
}: SkeletonProps) {
  return (
    <View
      style={[
        styles.skeleton,
        {
          width,
          height,
          borderRadius,
        },
        style,
      ]}
    />
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  container: {
    backgroundColor: COLORS.card,
    padding: SPACING.xl,
    borderRadius: BORDER_RADIUS.xl,
    alignItems: 'center',
    minWidth: 200,
  },
  message: {
    marginTop: SPACING.lg,
    fontSize: FONT_SIZES.md,
    color: COLORS.text,
    textAlign: 'center',
  },
  cancelButton: {
    marginTop: SPACING.lg,
    paddingVertical: SPACING.sm,
  },
  cancelText: {
    color: COLORS.textMuted,
    fontSize: FONT_SIZES.md,
  },
  progressContainer: {
    alignItems: 'center',
    width: '100%',
  },
  progressCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: COLORS.background,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: SPACING.lg,
  },
  progressText: {
    fontSize: FONT_SIZES.xl,
    fontWeight: '700',
    color: COLORS.primary,
  },
  progressBar: {
    width: '100%',
    height: 8,
    backgroundColor: COLORS.border,
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: COLORS.primary,
    borderRadius: 4,
  },
  spinnerContainer: {
    padding: SPACING.lg,
    alignItems: 'center',
    justifyContent: 'center',
  },
  spinnerFullScreen: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.background,
  },
  spinnerMessage: {
    marginTop: SPACING.md,
    fontSize: FONT_SIZES.md,
    color: COLORS.textMuted,
  },
  skeleton: {
    backgroundColor: COLORS.border,
  },
});
