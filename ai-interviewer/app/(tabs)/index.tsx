import React, { useState, useCallback } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, FlatList, TextInput, ActivityIndicator, Alert } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { MaterialIcons } from "@expo/vector-icons";
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from "../../constants/theme";
import { useAuth } from "../../contexts/AuthContext";
import { useCandidateDashboard, JobRecommendation, resumeApi } from "../../hooks/useDashboard";

const getStatusColor = (status: string) => {
  switch (status) {
    case "applied":
    case "ready":
      return { bg: "rgba(255,255,255,0.1)", dot: COLORS.primary, text: COLORS.primary };
    case "in_progress":
      return { bg: "rgba(16,185,129,0.1)", dot: COLORS.success, text: COLORS.success };
    case "completed":
      return { bg: "rgba(139,139,139,0.1)", dot: COLORS.textMuted, text: COLORS.textMuted };
    default:
      return { bg: "rgba(255,255,255,0.1)", dot: COLORS.textMuted, text: COLORS.textMuted };
  }
};

const getCompanyIcon = (company: string) => {
  switch (company?.toLowerCase()) {
    case "technova":
      return "terminal";
    case "ai labs":
      return "psychology";
    case "cloudscale":
      return "cloud";
    default:
      return "business";
  }
};

export default function HomeScreen() {
  const router = useRouter();
  const { user } = useAuth();
  const { jobs, resume, loading, error, fetchDashboard } = useCandidateDashboard();
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchDashboard();
    setRefreshing(false);
  };

  const renderJobCard = ({ item }: { item: JobRecommendation }) => {
    const job = item.job;
    const company = item.company_name || "Company";
    const status = "ready"; // Default status for recommended jobs

    const statusStyle = getStatusColor(status);

    return (
      <TouchableOpacity
        style={styles.card}
        onPress={() => router.push(`/interview/details?id=${job.id}`)}
      >
        <View style={styles.cardHeader}>
          <View style={styles.companyInfo}>
            <View style={styles.companyIcon}>
              <MaterialIcons
                name={getCompanyIcon(company) as any}
                size={28}
                color="#e2e8f0"
              />
            </View>
            <View>
              <Text style={styles.companyName}>{company}</Text>
              <Text style={styles.role}>{job.title}</Text>
            </View>
          </View>
          <View style={[styles.statusBadge, { backgroundColor: statusStyle.bg }]}>
            <View style={[styles.statusDot, { backgroundColor: statusStyle.dot }]} />
            <Text style={[styles.statusText, { color: statusStyle.text }]}>
              {item.match_score > 0 ? `${Math.round(item.match_score)}% Match` : "Available"}
            </Text>
          </View>
        </View>

        {/* Match Score Bar */}
        {item.match_score > 0 && (
          <View style={styles.matchContainer}>
            <View style={styles.matchBar}>
              <View style={[styles.matchFill, { width: `${item.match_score}%` }]} />
            </View>
            <Text style={styles.matchLabel}>
              {item.matched_skills?.length || 0} skills matched
            </Text>
          </View>
        )}

        <View style={styles.cardFooter}>
          <View style={styles.skillContainer}>
            {item.matched_skills?.slice(0, 3).map((skill, index) => (
              <View key={index} style={styles.skillBadge}>
                <Text style={styles.skillText}>{skill}</Text>
              </View>
            ))}
            {item.missing_skills?.length > 0 && (
              <Text style={styles.missingText}>+{item.missing_skills.length} needed</Text>
            )}
          </View>
          <TouchableOpacity
            style={styles.viewButton}
            onPress={() => router.push(`/interview/details?id=${job.id}`)}
          >
            <Text style={styles.viewButtonText}>View</Text>
          </TouchableOpacity>
        </View>
      </TouchableOpacity>
    );
  };

  // Mock interviews for demo
  const mockInterviews = [
    {
      id: "1",
      company: "TechNova",
      role: "Backend Developer",
      status: "applied",
      stage: 1,
      totalStages: 3,
      deadline: "2 days",
    },
    {
      id: "2",
      company: "AI Labs",
      role: "ML Engineer",
      status: "interview",
      stage: 2,
      totalStages: 3,
      scheduledDate: "Oct 24",
    },
    {
      id: "3",
      company: "CloudScale",
      role: "DevOps Architect",
      status: "closed",
      stage: 3,
      totalStages: 3,
    },
  ];

  const renderInterviewCard = ({ item }: { item: any }) => {
    const statusStyle = getStatusColor(item.status);

    return (
      <TouchableOpacity
        style={styles.card}
        onPress={() => router.push(`/interview/details?id=${item.id}`)}
      >
        <View style={styles.cardHeader}>
          <View style={styles.companyInfo}>
            <View style={styles.companyIcon}>
              <MaterialIcons
                name={getCompanyIcon(item.company) as any}
                size={28}
                color="#e2e8f0"
              />
            </View>
            <View>
              <Text style={styles.companyName}>{item.company}</Text>
              <Text style={styles.role}>{item.role}</Text>
            </View>
          </View>
          <View style={[styles.statusBadge, { backgroundColor: statusStyle.bg }]}>
            <View style={[styles.statusDot, { backgroundColor: statusStyle.dot }]} />
            <Text style={[styles.statusText, { color: statusStyle.text }]}>
              {item.status === "applied" ? "Applied" :
               item.status === "interview" ? "Interview" : "Completed"}
            </Text>
          </View>
        </View>

        <View style={styles.cardFooter}>
          <View style={styles.avatarStack}>
            <View style={[styles.avatar, styles.avatarFirst]}>
              <Text style={styles.avatarText}>AI</Text>
            </View>
            <View style={[styles.avatar, styles.avatarSecond]}>
              <Text style={styles.avatarTextDark}>JD</Text>
            </View>
          </View>
          <TouchableOpacity
            style={styles.viewButton}
            onPress={() => {
              if (item.status === "interview") {
                router.push(`/interview/live?id=${item.id}`);
              } else {
                router.push(`/interview/details?id=${item.id}`);
              }
            }}
          >
            <Text style={styles.viewButtonText}>
              {item.status === "interview" ? "Join Room" : "View Details"}
            </Text>
          </TouchableOpacity>
        </View>

        <View style={styles.cardBottom}>
          <View style={styles.stageContainer}>
            <View style={styles.stageDots}>
              {[1, 2, 3].map((s) => (
                <View
                  key={s}
                  style={[
                    styles.stageDot,
                    s <= item.stage && styles.stageDotActive,
                  ]}
                />
              ))}
            </View>
            <Text style={styles.stageText}>Stage {item.stage} of {item.totalStages}</Text>
          </View>
          <Text style={styles.deadline}>
            {item.deadline ? `Ends in ${item.deadline}` :
             item.scheduledDate ? `Scheduled: ${item.scheduledDate}` :
             "Interview process completed"}
          </Text>
        </View>
      </TouchableOpacity>
    );
  };

  // Show prompt to upload resume if not uploaded
  const showResumePrompt = !resume && !loading;

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerTop}>
          <View style={styles.userInfo}>
            <View style={styles.userIcon}>
              <MaterialIcons name="person" size={20} color="#e2e8f0" />
            </View>
            <View>
              <Text style={styles.welcomeText}>Welcome back</Text>
              <Text style={styles.userName}>
                {user?.full_name || user?.email?.split('@')[0] || "Guest"}
              </Text>
            </View>
          </View>
          <TouchableOpacity style={styles.notificationButton}>
            <MaterialIcons name="notifications" size={24} color="#e2e8f0" />
            <View style={styles.notificationDot} />
          </TouchableOpacity>
        </View>

        <Text style={styles.sectionTitle}>
          {jobs.length > 0 ? "Recommended for You" : "Available Interviews"}
        </Text>

        {/* Search Bar */}
        <View style={styles.searchContainer}>
          <MaterialIcons name="search" size={24} color={COLORS.textMuted} style={styles.searchIcon} />
          <TextInput
            placeholder="Search roles, companies..."
            placeholderTextColor={COLORS.textMuted}
            style={styles.searchInput}
          />
        </View>
      </View>

      {/* Resume Upload Prompt */}
      {showResumePrompt && (
        <TouchableOpacity style={styles.uploadPrompt} onPress={() => router.push('/upload-resume')}>
          <MaterialIcons name="upload-file" size={32} color={COLORS.primary} />
          <View style={styles.uploadTextContainer}>
            <Text style={styles.uploadTitle}>Upload Your Resume</Text>
            <Text style={styles.uploadSubtitle}>Get personalized job recommendations</Text>
          </View>
          <MaterialIcons name="chevron-right" size={24} color={COLORS.textMuted} />
        </TouchableOpacity>
      )}

      {/* Loading */}
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={COLORS.primary} />
          <Text style={styles.loadingText}>Loading recommendations...</Text>
        </View>
      ) : error ? (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={handleRefresh}>
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={jobs.length > 0 ? jobs : mockInterviews}
          keyExtractor={(item: any, index: number) => (item.job_id || item.id || index.toString())}
          renderItem={({ item }: { item: any }) => jobs.length > 0 ? renderJobCard({ item }) : renderInterviewCard({ item })}
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
          refreshing={refreshing}
          onRefresh={handleRefresh}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  header: {
    paddingHorizontal: SPACING.md,
    paddingTop: SPACING.lg,
    paddingBottom: SPACING.md,
  },
  headerTop: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: SPACING.lg,
  },
  userInfo: {
    flexDirection: "row",
    alignItems: "center",
    gap: SPACING.sm,
  },
  userIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: "rgba(255,255,255,0.1)",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.2)",
    justifyContent: "center",
    alignItems: "center",
  },
  welcomeText: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.textMuted,
    fontWeight: "500",
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  userName: {
    fontSize: FONT_SIZES.xl,
    fontWeight: "700",
    color: COLORS.primary,
  },
  notificationButton: {
    width: 40,
    height: 40,
    borderRadius: BORDER_RADIUS.md,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    justifyContent: "center",
    alignItems: "center",
  },
  notificationDot: {
    position: "absolute",
    top: 10,
    right: 10,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: COLORS.primary,
    borderWidth: 2,
    borderColor: COLORS.background,
  },
  sectionTitle: {
    fontSize: 24,
    fontWeight: "700",
    color: COLORS.primary,
    marginBottom: SPACING.md,
  },
  searchContainer: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: BORDER_RADIUS.lg,
    paddingHorizontal: SPACING.md,
    height: 56,
  },
  searchIcon: {
    marginRight: SPACING.sm,
  },
  searchInput: {
    flex: 1,
    fontSize: FONT_SIZES.lg,
    color: COLORS.primary,
    backgroundColor: "transparent",
  },
  uploadPrompt: {
    flexDirection: "row",
    alignItems: "center",
    marginHorizontal: SPACING.md,
    marginBottom: SPACING.md,
    padding: SPACING.md,
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    borderWidth: 1,
    borderColor: COLORS.primary,
  },
  uploadTextContainer: {
    flex: 1,
    marginLeft: SPACING.md,
  },
  uploadTitle: {
    fontSize: FONT_SIZES.md,
    fontWeight: "600",
    color: COLORS.primary,
  },
  uploadSubtitle: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.textMuted,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  loadingText: {
    marginTop: SPACING.md,
    color: COLORS.textMuted,
    fontSize: FONT_SIZES.md,
  },
  errorContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: SPACING.lg,
  },
  errorText: {
    color: COLORS.error || "#ef4444",
    fontSize: FONT_SIZES.md,
    textAlign: "center",
  },
  retryButton: {
    marginTop: SPACING.md,
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.sm,
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.md,
  },
  retryText: {
    color: COLORS.background,
    fontWeight: "600",
  },
  listContent: {
    paddingHorizontal: SPACING.md,
    paddingBottom: 100,
  },
  card: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: BORDER_RADIUS.lg,
    overflow: "hidden",
    marginBottom: SPACING.md,
  },
  cardHeader: {
    padding: SPACING.md,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
  },
  companyInfo: {
    flexDirection: "row",
    gap: SPACING.md,
    alignItems: "center",
  },
  companyIcon: {
    width: 56,
    height: 56,
    borderRadius: BORDER_RADIUS.md,
    backgroundColor: "rgba(255,255,255,0.05)",
    borderWidth: 1,
    borderColor: COLORS.border,
    justifyContent: "center",
    alignItems: "center",
  },
  companyName: {
    fontSize: FONT_SIZES.lg,
    fontWeight: "700",
    color: COLORS.primary,
  },
  role: {
    fontSize: FONT_SIZES.md,
    color: COLORS.textMuted,
    fontWeight: "500",
  },
  statusBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: BORDER_RADIUS.full,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  statusText: {
    fontSize: FONT_SIZES.xs,
    fontWeight: "700",
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  matchContainer: {
    paddingHorizontal: SPACING.md,
    paddingBottom: SPACING.sm,
  },
  matchBar: {
    height: 4,
    backgroundColor: COLORS.border,
    borderRadius: 2,
    overflow: "hidden",
  },
  matchFill: {
    height: "100%",
    backgroundColor: COLORS.success,
    borderRadius: 2,
  },
  matchLabel: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.textMuted,
    marginTop: 4,
  },
  cardFooter: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: SPACING.md,
    paddingTop: SPACING.sm,
  },
  skillContainer: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
    gap: 4,
    flexWrap: "wrap",
  },
  skillBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    backgroundColor: "rgba(255,255,255,0.1)",
    borderRadius: 4,
  },
  skillText: {
    fontSize: 10,
    color: COLORS.textMuted,
  },
  missingText: {
    fontSize: 10,
    color: COLORS.textMuted,
    fontStyle: "italic",
  },
  avatarStack: {
    flexDirection: "row",
  },
  avatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    borderWidth: 2,
    borderColor: COLORS.surface,
    justifyContent: "center",
    alignItems: "center",
  },
  avatarFirst: {
    backgroundColor: "#475569",
    marginRight: -8,
  },
  avatarSecond: {
    backgroundColor: "#94a3b8",
  },
  avatarText: {
    fontSize: 10,
    fontWeight: "700",
    color: COLORS.primary,
  },
  avatarTextDark: {
    fontSize: 10,
    fontWeight: "700",
    color: COLORS.background,
  },
  viewButton: {
    backgroundColor: "#e2e8f0",
    paddingHorizontal: 20,
    paddingVertical: 8,
    borderRadius: BORDER_RADIUS.sm,
  },
  viewButtonText: {
    fontSize: FONT_SIZES.sm,
    fontWeight: "700",
    color: COLORS.background,
  },
  cardBottom: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    backgroundColor: "rgba(0,0,0,0.2)",
    borderTopWidth: 1,
    borderTopColor: "rgba(42,42,44,0.5)",
    marginTop: SPACING.sm,
  },
  stageContainer: {
    flexDirection: "row",
    alignItems: "center",
    gap: SPACING.sm,
  },
  stageDots: {
    flexDirection: "row",
    gap: 4,
  },
  stageDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: "#1A1A1C",
  },
  stageDotActive: {
    backgroundColor: "#e2e8f0",
  },
  stageText: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.textMuted,
    fontWeight: "500",
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  deadline: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.textMuted,
  },
});
