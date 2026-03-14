import { View, Text, TouchableOpacity, StyleSheet, FlatList, TextInput, ActivityIndicator } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { MaterialIcons } from "@expo/vector-icons";
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from "../../constants/theme";
import { Interview } from "../../types";
import { useAuth } from "../../contexts/AuthContext";
import { useInterviews } from "../../hooks/useInterviews";
import { useEffect } from "react";

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

const mapBackendInterviewToUI = (interview: any): Interview => {
  const job = interview.jobs || {};
  const company = job.companies || {};
  return {
    id: interview.id,
    company: company.name || "Company",
    role: job.title || "Role",
    status: interview.status === "ready" ? "applied" : interview.status === "in_progress" ? "interview" : interview.status === "completed" ? "closed" : "applied",
    stage: interview.current_question_index || 1,
    totalStages: interview.max_questions || 3,
    deadline: interview.status === "ready" ? "2 days" : undefined,
    scheduledDate: interview.started_at ? new Date(interview.started_at).toLocaleDateString() : undefined,
    score: interview.interview_scores?.[0]?.overall_score,
  };
};

export default function HomeScreen() {
  const router = useRouter();
  const { user } = useAuth();
  const { interviews, loading, error, refetch } = useInterviews();

  const handleRefresh = () => {
    refetch();
  };

  const renderInterviewCard = ({ item }: { item: Interview }) => {
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
             item.score ? `Score: ${item.score}%` :
             "Interview process completed"}
          </Text>
        </View>
      </TouchableOpacity>
    );
  };

  // If no user logged in, show mock data
  const displayInterviews = user ? interviews : [];
  const mockInterviews: Interview[] = !user ? [
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
  ] : [];

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

        <Text style={styles.sectionTitle}>Available Interviews</Text>

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

      {/* Interview List */}
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={COLORS.primary} />
          <Text style={styles.loadingText}>Loading interviews...</Text>
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
          data={displayInterviews.length > 0 ? displayInterviews.map(mapBackendInterviewToUI) : mockInterviews}
          keyExtractor={(item) => item.id}
          renderItem={renderInterviewCard}
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
          refreshing={loading}
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
  listContent: {
    paddingHorizontal: SPACING.md,
    paddingBottom: 100,
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
  cardFooter: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: SPACING.md,
    paddingTop: SPACING.sm,
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
