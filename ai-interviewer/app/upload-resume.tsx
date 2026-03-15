import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator, Alert, ScrollView } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { MaterialIcons } from "@expo/vector-icons";
import * as DocumentPicker from 'expo-document-picker';
import * as FileSystem from 'expo-file-system';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from "../constants/theme";
import { useAuth } from "../contexts/AuthContext";
import { resumeApi } from "../hooks/useDashboard";

export default function UploadResumeScreen() {
  const router = useRouter();
  const { user } = useAuth();
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<any>(null);
  const [uploadProgress, setUploadProgress] = useState('');

  const pickDocument = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['application/pdf'],
        copyToCacheDirectory: true,
      });

      if (result.canceled) {
        return;
      }

      const asset = result.assets[0];
      setSelectedFile({
        name: asset.name,
        uri: asset.uri,
        size: asset.size,
        type: asset.mimeType,
      });
    } catch (error) {
      Alert.alert('Error', 'Failed to pick document');
    }
  };

  const uploadResume = async () => {
    if (!selectedFile) {
      Alert.alert('Error', 'Please select a resume first');
      return;
    }

    setUploading(true);
    setUploadProgress('Uploading and analyzing your resume...');

    try {
      // Create a File object from the URI
      const response = await fetch(selectedFile.uri);
      const blob = await response.blob();
      const file = new File([blob], selectedFile.name, { type: selectedFile.type });

      setUploadProgress('Analyzing resume with AI...');

      // Upload the resume
      const resume = await resumeApi.uploadResume(file);

      setUploadProgress('Resume uploaded successfully!');

      // Show success and navigate
      Alert.alert(
        'Success!',
        'Your resume has been uploaded and analyzed. You can now see job recommendations.',
        [
          {
            text: 'View Recommendations',
            onPress: () => router.replace('/(tabs)'),
          },
        ]
      );
    } catch (error: any) {
      console.error('Upload error:', error);
      Alert.alert('Error', error.message || 'Failed to upload resume. Please try again.');
    } finally {
      setUploading(false);
      setUploadProgress('');
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <MaterialIcons name="arrow-back" size={24} color={COLORS.primary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Upload Resume</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        {/* Info Card */}
        <View style={styles.infoCard}>
          <MaterialIcons name="info" size={24} color={COLORS.primary} />
          <Text style={styles.infoText}>
            Upload your resume to get personalized job recommendations based on your skills and experience.
          </Text>
        </View>

        {/* Upload Area */}
        <TouchableOpacity
          style={styles.uploadArea}
          onPress={pickDocument}
          disabled={uploading}
        >
          {selectedFile ? (
            <View style={styles.selectedFile}>
              <MaterialIcons name="description" size={48} color={COLORS.primary} />
              <Text style={styles.fileName} numberOfLines={2}>{selectedFile.name}</Text>
              <Text style={styles.fileSize}>
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </Text>
              <TouchableOpacity
                style={styles.changeButton}
                onPress={pickDocument}
              >
                <Text style={styles.changeText}>Change File</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <>
              <MaterialIcons name="cloud-upload" size={64} color={COLORS.textMuted} />
              <Text style={styles.uploadTitle}>Tap to select PDF</Text>
              <Text style={styles.uploadSubtitle}>Only PDF files are supported</Text>
            </>
          )}
        </TouchableOpacity>

        {/* Supported Formats */}
        <View style={styles.formatsContainer}>
          <Text style={styles.formatsTitle}>What's next?</Text>
          <View style={styles.formatItem}>
            <MaterialIcons name="check-circle" size={20} color={COLORS.success} />
            <Text style={styles.formatText}>AI will extract your skills</Text>
          </View>
          <View style={styles.formatItem}>
            <MaterialIcons name="check-circle" size={20} color={COLORS.success} />
            <Text style={styles.formatText}>Get matched with suitable jobs</Text>
          </View>
          <View style={styles.formatItem}>
            <MaterialIcons name="check-circle" size={20} color={COLORS.success} />
            <Text style={styles.formatText}>Start AI-powered interviews</Text>
          </View>
        </View>

        {/* Progress */}
        {uploading && (
          <View style={styles.progressContainer}>
            <ActivityIndicator size="small" color={COLORS.primary} />
            <Text style={styles.progressText}>{uploadProgress}</Text>
          </View>
        )}

        {/* Upload Button */}
        <TouchableOpacity
          style={[
            styles.uploadButton,
            (!selectedFile || uploading) && styles.uploadButtonDisabled
          ]}
          onPress={uploadResume}
          disabled={!selectedFile || uploading}
        >
          {uploading ? (
            <ActivityIndicator size="small" color={COLORS.background} />
          ) : (
            <>
              <MaterialIcons name="upload" size={24} color={COLORS.background} />
              <Text style={styles.uploadButtonText}>
                {selectedFile ? 'Upload & Analyze Resume' : 'Select a Resume First'}
              </Text>
            </>
          )}
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  backButton: {
    width: 40,
    height: 40,
    justifyContent: "center",
    alignItems: "center",
  },
  headerTitle: {
    fontSize: FONT_SIZES.lg,
    fontWeight: "700",
    color: COLORS.primary,
  },
  content: {
    padding: SPACING.lg,
  },
  infoCard: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    gap: SPACING.md,
    marginBottom: SPACING.lg,
  },
  infoText: {
    flex: 1,
    fontSize: FONT_SIZES.sm,
    color: COLORS.textMuted,
    lineHeight: 20,
  },
  uploadArea: {
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.xl,
    padding: SPACING.xl,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 2,
    borderColor: COLORS.border,
    borderStyle: "dashed",
    marginBottom: SPACING.lg,
    minHeight: 250,
  },
  selectedFile: {
    alignItems: "center",
  },
  fileName: {
    fontSize: FONT_SIZES.lg,
    fontWeight: "600",
    color: COLORS.primary,
    marginTop: SPACING.md,
    textAlign: "center",
  },
  fileSize: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.textMuted,
    marginTop: SPACING.xs,
  },
  changeButton: {
    marginTop: SPACING.md,
  },
  changeText: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.primary,
    fontWeight: "600",
  },
  uploadTitle: {
    fontSize: FONT_SIZES.xl,
    fontWeight: "600",
    color: COLORS.primary,
    marginTop: SPACING.md,
  },
  uploadSubtitle: {
    fontSize: FONT_SIZES.md,
    color: COLORS.textMuted,
    marginTop: SPACING.xs,
  },
  formatsContainer: {
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    marginBottom: SPACING.lg,
  },
  formatsTitle: {
    fontSize: FONT_SIZES.md,
    fontWeight: "700",
    color: COLORS.primary,
    marginBottom: SPACING.md,
  },
  formatItem: {
    flexDirection: "row",
    alignItems: "center",
    gap: SPACING.sm,
    marginBottom: SPACING.sm,
  },
  formatText: {
    fontSize: FONT_SIZES.md,
    color: COLORS.textMuted,
  },
  progressContainer: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: SPACING.sm,
    marginBottom: SPACING.lg,
  },
  progressText: {
    fontSize: FONT_SIZES.md,
    color: COLORS.textMuted,
  },
  uploadButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: SPACING.sm,
    backgroundColor: COLORS.primary,
    paddingVertical: SPACING.lg,
    borderRadius: BORDER_RADIUS.lg,
  },
  uploadButtonDisabled: {
    backgroundColor: COLORS.textMuted,
  },
  uploadButtonText: {
    fontSize: FONT_SIZES.lg,
    fontWeight: "700",
    color: COLORS.background,
  },
});
