import { View, Text, TouchableOpacity, StyleSheet, FlatList } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { MaterialIcons } from "@expo/vector-icons";
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from "../../constants/theme";
import { Interview } from "../../types";

const mockRecentInterviews: Interview[] = [
  {
    id: "1",
    company: "TechFlow Systems",
    role: "Senior Backend Engineer",
    status: "passed",
    stage: 3,
    totalStages: 3,
  },
  {
    id: "2",
    company: "CloudScale AI",
    role: "Python Developer",
    status: "pending",
    stage: 2,
    totalStages: 3,
  },
  {
    id: "3",
    company: "Nexus Fintech",
    role: "Fullstack Engineer",
    status: "failed",
    stage: 3,
    totalStages: 3,
  },
];

const skills = ["Python", "FastAPI", "React", "SQL", "AWS"];

const getCompanyIcon = (company: string) => {
  switch (company) {
    case "TechFlow Systems":
      return "corporate-fare";
    case "CloudScale AI":
      return "cloud";
    case "Nexus Fintech":
      return "token";
    default:
      return "business";
  }
};

const getStatusBadge = (status: string) => {
  switch (status) {
    case "passed":
      return { bg: "rgba(16,185,129,0.1)", text: "#10B981", label: "Passed" };
    case "pending":
      return { bg: "rgba(139,139,139,0.1)", text: "#8E8E93", label: "Pending" };
    case "failed":
      return { bg: "rgba(239,68,68,0.1)", text: "#EF4444", label: "Failed" };
    default:
      return { bg: "rgba(139,139,139,0.1)", text: "#8E8E93", label: "Unknown" };
  }
};

export default function ProfileScreen() {
  const router = useRouter();

  const renderInterviewCard = ({ item }: { item: Interview }) => {
    const statusBadge = getStatusBadge(item.status);

    return (
      <View style={styles.interviewCard}>
        <View style={styles.companyIcon}>
          <MaterialIcons
            name={getCompanyIcon(item.company) as any}
            size={24}
            color={COLORS.textMuted}
          />
        </View>
        <View style={styles.interviewInfo}>
          <Text style={styles.companyName}>{item.company}</Text>
          <Text style={styles.roleText}>{item.role}</Text>
        </View>
        <View style={styles.interviewStatus}>
          <View style={[styles.statusBadge, { backgroundColor: statusBadge.bg }]}>
            <Text style={[styles.statusText, { color: statusBadge.text }]}>
              {statusBadge.label}
            </Text>
          </View>
          <Text style={styles.timeAgo}>2 days ago</Text>
        </View>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton}>
          <MaterialIcons name="arrow-back" size={24} color={COLORS.primary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Candidate Profile</Text>
        <TouchableOpacity style={styles.settingsButton}>
          <MaterialIcons name="settings" size={22} color={COLORS.primary} />
        </TouchableOpacity>
      </View>

      <FlatList
        data={mockRecentInterviews}
        keyExtractor={(item) => item.id}
        renderItem={renderInterviewCard}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        ListHeaderComponent={
          <>
            {/* Hero Section */}
            <View style={styles.heroSection}>
              <View style={styles.avatarContainer}>
                <View style={styles.avatar}>
                  <MaterialIcons name="person" size={50} color={COLORS.textMuted} />
                </View>
                <View style={styles.onlineIndicator} />
              </View>
              <View style={styles.nameContainer}>
                <Text style={styles.name}>Debangsu Hazarika</Text>
                <Text style={styles.jobTitle}>Backend Developer</Text>
              </View>
            </View>

            {/* Stats Grid */}
            <View style={styles.statsContainer}>
              <View style={styles.statCard}>
                <Text style={styles.statLabel}>Interviews Completed</Text>
                <Text style={styles.statValue}>12</Text>
              </View>
              <View style={styles.statCard}>
                <Text style={styles.statLabel}>Average Score</Text>
                <View style={styles.scoreContainer}>
                  <Text style={styles.statValue}>78</Text>
                  <Text style={styles.scoreMax}>/ 100</Text>
                </View>
              </View>
            </View>

            {/* Skills Section */}
            <View style={styles.skillsSection}>
              <Text style={styles.sectionTitle}>Core Skills</Text>
              <View style={styles.skillsContainer}>
                {skills.map((skill, index) => (
                  <View key={index} style={styles.skillBadge}>
                    <Text style={styles.skillText}>{skill}</Text>
                  </View>
                ))}
              </View>
            </View>

            {/* Recent Interviews Header */}
            <View style={styles.recentHeader}>
              <Text style={styles.sectionTitle}>Recent Interviews</Text>
              <TouchableOpacity>
                <Text style={styles.viewAllText}>VIEW ALL</Text>
              </TouchableOpacity>
            </View>
          </>
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.backgroundLight,
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
    width: 48,
    height: 48,
    justifyContent: "center",
    alignItems: "center",
  },
  headerTitle: {
    fontSize: FONT_SIZES.lg,
    fontWeight: "700",
    color: COLORS.primary,
  },
  settingsButton: {
    width: 40,
    height: 40,
    borderRadius: BORDER_RADIUS.md,
    backgroundColor: COLORS.card,
    borderWidth: 1,
    borderColor: COLORS.border,
    justifyContent: "center",
    alignItems: "center",
  },
  listContent: {
    paddingBottom: 100,
  },
  heroSection: {
    alignItems: "center",
    paddingVertical: SPACING.xl,
    gap: SPACING.md,
  },
  avatarContainer: {
    position: "relative",
  },
  avatar: {
    width: 128,
    height: 128,
    borderRadius: 64,
    backgroundColor: COLORS.card,
    borderWidth: 4,
    borderColor: COLORS.card,
    justifyContent: "center",
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 4, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 10,
  },
  onlineIndicator: {
    position: "absolute",
    bottom: 8,
    right: 8,
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: COLORS.success,
    borderWidth: 4,
    borderColor: COLORS.backgroundLight,
  },
  nameContainer: {
    alignItems: "center",
  },
  name: {
    fontSize: FONT_SIZES.xxl,
    fontWeight: "700",
    color: COLORS.primary,
  },
  jobTitle: {
    fontSize: FONT_SIZES.md,
    color: COLORS.textMuted,
    fontWeight: "500",
  },
  statsContainer: {
    flexDirection: "row",
    paddingHorizontal: SPACING.md,
    gap: SPACING.md,
  },
  statCard: {
    flex: 1,
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    gap: SPACING.sm,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  statLabel: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.textMuted,
    fontWeight: "500",
    textTransform: "uppercase",
    letterSpacing: 1,
  },
  statValue: {
    fontSize: 36,
    fontWeight: "700",
    color: COLORS.primary,
  },
  scoreContainer: {
    flexDirection: "row",
    alignItems: "baseline",
  },
  scoreMax: {
    fontSize: FONT_SIZES.md,
    color: COLORS.textMuted,
  },
  skillsSection: {
    paddingHorizontal: SPACING.md,
    paddingTop: SPACING.xl,
  },
  sectionTitle: {
    fontSize: FONT_SIZES.sm,
    fontWeight: "700",
    color: COLORS.primary,
    textTransform: "uppercase",
    letterSpacing: 1,
    paddingBottom: SPACING.md,
  },
  skillsContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: SPACING.sm,
  },
  skillBadge: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.card,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  skillText: {
    fontSize: FONT_SIZES.md,
    color: "#cbd5e1",
    fontWeight: "500",
  },
  recentHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: SPACING.md,
    paddingTop: SPACING.xl,
    paddingBottom: SPACING.md,
  },
  viewAllText: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.textMuted,
    fontWeight: "700",
  },
  interviewCard: {
    flexDirection: "row",
    alignItems: "center",
    padding: SPACING.md,
    marginHorizontal: SPACING.md,
    marginBottom: SPACING.sm,
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  companyIcon: {
    width: 48,
    height: 48,
    borderRadius: BORDER_RADIUS.md,
    backgroundColor: COLORS.backgroundLight,
    borderWidth: 1,
    borderColor: COLORS.border,
    justifyContent: "center",
    alignItems: "center",
  },
  interviewInfo: {
    flex: 1,
    marginLeft: SPACING.md,
  },
  companyName: {
    fontSize: FONT_SIZES.md,
    fontWeight: "700",
    color: COLORS.primary,
  },
  roleText: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.textMuted,
  },
  interviewStatus: {
    alignItems: "flex-end",
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: BORDER_RADIUS.full,
  },
  statusText: {
    fontSize: FONT_SIZES.xs,
    fontWeight: "600",
  },
  timeAgo: {
    fontSize: 10,
    color: COLORS.textMuted,
    marginTop: 4,
    fontWeight: "500",
  },
});
