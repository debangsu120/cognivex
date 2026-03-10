import { View, Text, TouchableOpacity, StyleSheet, FlatList, TextInput } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { MaterialIcons } from "@expo/vector-icons";
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from "../../constants/theme";
import { Candidate } from "../../types";

const mockCandidates: Candidate[] = [
  {
    id: "1",
    name: "Rahul Sharma",
    role: "Backend Developer",
    score: 86,
    status: "shortlisted",
    stage: 3,
  },
  {
    id: "2",
    name: "Meera Patel",
    role: "ML Engineer",
    score: 82,
    status: "in_review",
    stage: 2,
  },
];

export default function RecruiterScreen() {
  const renderCandidateCard = ({ item }: { item: Candidate }) => {
    return (
      <View style={styles.candidateCard}>
        <View style={styles.candidateHeader}>
          <View style={styles.candidateInfo}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>
                {item.name.split(" ").map(n => n[0]).join("")}
              </Text>
            </View>
            <View>
              <Text style={styles.candidateName}>{item.name}</Text>
              <Text style={styles.candidateRole}>{item.role}</Text>
            </View>
          </View>
          <View style={styles.scoreContainer}>
            <View style={styles.scoreBadge}>
              <Text style={styles.scoreText}>{item.score} Score</Text>
            </View>
            <Text style={styles.statusLabel}>
              {item.status === "shortlisted" ? "Top Candidate" :
               item.status === "in_review" ? "In Review" : "Interview"}
            </Text>
          </View>
        </View>

        <View style={styles.progressContainer}>
          <View style={styles.progressBar}>
            <View
              style={[
                styles.progressFill,
                { width: `${(item.stage / 3) * 100}%` },
              ]}
            />
          </View>
          <Text style={styles.progressLabel}>
            {item.status === "shortlisted" ? "Shortlisted" :
             item.status === "in_review" ? "In Review" : "Interview"}
          </Text>
        </View>

        <View style={styles.interviewersContainer}>
          <View style={styles.interviewerStack}>
            <View style={[styles.interviewerAvatar, { backgroundColor: "#334155" }]}>
              <Text style={styles.interviewerText}>JD</Text>
            </View>
            <View style={[styles.interviewerAvatar, { backgroundColor: "#334155", marginLeft: -8 }]}>
              <Text style={styles.interviewerText}>AS</Text>
            </View>
          </View>
          <Text style={styles.interviewerLabel}>
            {item.status === "shortlisted" ? "+2 interviewers" : "Assigned to interviewer"}
          </Text>
        </View>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>Company Dashboard</Text>
          <Text style={styles.headerSubtitle}>Candidate Interviews</Text>
        </View>
        <TouchableOpacity style={styles.notificationButton}>
          <MaterialIcons name="notifications" size={24} color={COLORS.primary} />
        </TouchableOpacity>
      </View>

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <MaterialIcons name="search" size={24} color={COLORS.textMuted} style={styles.searchIcon} />
        <TextInput
          placeholder="Search candidates or roles"
          placeholderTextColor={COLORS.textMuted}
          style={styles.searchInput}
        />
      </View>

      {/* Content */}
      <FlatList
        data={mockCandidates}
        keyExtractor={(item) => item.id}
        renderItem={renderCandidateCard}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        ListHeaderComponent={
          <>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Recent Candidates</Text>
              <TouchableOpacity>
                <Text style={styles.viewAllText}>View All</Text>
              </TouchableOpacity>
            </View>

            {/* Stats Cards */}
            <View style={styles.statsContainer}>
              <View style={styles.statCard}>
                <Text style={styles.statLabel}>Active Roles</Text>
                <Text style={styles.statValue}>12</Text>
              </View>
              <View style={styles.statCard}>
                <Text style={styles.statLabel}>New Apps</Text>
                <Text style={styles.statValue}>+48</Text>
              </View>
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
    backgroundColor: COLORS.background,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: SPACING.lg,
    paddingTop: SPACING.xl,
    paddingBottom: SPACING.md,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: "700",
    color: COLORS.primary,
  },
  headerSubtitle: {
    fontSize: FONT_SIZES.md,
    color: COLORS.textMuted,
    fontWeight: "500",
  },
  notificationButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: COLORS.card,
    borderWidth: 1,
    borderColor: COLORS.border,
    justifyContent: "center",
    alignItems: "center",
  },
  searchContainer: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: COLORS.card,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: BORDER_RADIUS.full,
    paddingHorizontal: SPACING.lg,
    marginHorizontal: SPACING.lg,
    marginVertical: SPACING.md,
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
    paddingHorizontal: SPACING.lg,
    paddingBottom: 100,
  },
  sectionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: SPACING.md,
    marginBottom: SPACING.md,
  },
  sectionTitle: {
    fontSize: FONT_SIZES.lg,
    fontWeight: "600",
    color: COLORS.primary,
  },
  viewAllText: {
    fontSize: FONT_SIZES.md,
    color: COLORS.textMuted,
    fontWeight: "500",
  },
  statsContainer: {
    flexDirection: "row",
    gap: SPACING.md,
    marginBottom: SPACING.lg,
  },
  statCard: {
    flex: 1,
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  statLabel: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.textMuted,
    fontWeight: "500",
  },
  statValue: {
    fontSize: 24,
    fontWeight: "700",
    color: COLORS.primary,
  },
  candidateCard: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.xl,
    padding: SPACING.lg,
    borderWidth: 1,
    borderColor: COLORS.border,
    marginBottom: SPACING.md,
  },
  candidateHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
  },
  candidateInfo: {
    flexDirection: "row",
    gap: SPACING.md,
    alignItems: "center",
  },
  avatar: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: COLORS.border,
    justifyContent: "center",
    alignItems: "center",
  },
  avatarText: {
    fontSize: FONT_SIZES.lg,
    fontWeight: "700",
    color: COLORS.primary,
  },
  candidateName: {
    fontSize: FONT_SIZES.md,
    fontWeight: "700",
    color: COLORS.primary,
  },
  candidateRole: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.textMuted,
  },
  scoreContainer: {
    alignItems: "flex-end",
    gap: 4,
  },
  scoreBadge: {
    backgroundColor: "rgba(255,255,255,0.1)",
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: BORDER_RADIUS.full,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.05)",
  },
  scoreText: {
    fontSize: FONT_SIZES.xs,
    fontWeight: "700",
    color: COLORS.primary,
  },
  statusLabel: {
    fontSize: 10,
    fontWeight: "700",
    color: COLORS.textMuted,
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  progressContainer: {
    flexDirection: "row",
    alignItems: "center",
    gap: SPACING.sm,
    marginTop: SPACING.md,
  },
  progressBar: {
    flex: 1,
    height: 6,
    backgroundColor: COLORS.border,
    borderRadius: 3,
  },
  progressFill: {
    height: 6,
    backgroundColor: COLORS.primary,
    borderRadius: 3,
  },
  progressLabel: {
    fontSize: 10,
    fontWeight: "700",
    color: COLORS.textMuted,
    marginLeft: SPACING.sm,
  },
  interviewersContainer: {
    flexDirection: "row",
    alignItems: "center",
    gap: SPACING.sm,
    marginTop: SPACING.sm,
  },
  interviewerStack: {
    flexDirection: "row",
  },
  interviewerAvatar: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: COLORS.card,
    justifyContent: "center",
    alignItems: "center",
  },
  interviewerText: {
    fontSize: 8,
    fontWeight: "700",
    color: COLORS.primary,
  },
  interviewerLabel: {
    fontSize: 10,
    color: COLORS.textMuted,
  },
});
