import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { MaterialIcons } from "@expo/vector-icons";
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from "../../constants/theme";

const skills = [
  { name: "Python", level: 100 },
  { name: "FastAPI", level: 75 },
  { name: "SQL", level: 60 },
  { name: "System", level: 90 },
];

const skillsTested = ["Python", "FastAPI", "SQL", "API Design"];

export default function InterviewDetailsScreen() {
  const router = useRouter();

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <MaterialIcons name="arrow-back" size={24} color={COLORS.primary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Interview Details</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {/* Skill Visualization */}
        <View style={styles.skillSection}>
          <View style={styles.skillCard}>
            <Text style={styles.skillLabel}>Required Skill Proficiency</Text>
            <View style={styles.skillBars}>
              {skills.map((skill, index) => (
                <View key={index} style={styles.skillBarContainer}>
                  <View
                    style={[
                      styles.skillBar,
                      { height: `${skill.level}%` },
                    ]}
                  />
                  <Text style={styles.skillName}>{skill.name}</Text>
                </View>
              ))}
            </View>
          </View>
        </View>

        {/* Details Card */}
        <View style={styles.detailsCard}>
          <View style={styles.jobHeader}>
            <Text style={styles.interviewId}>INT-123456</Text>
            <View style={styles.jobTitleRow}>
              <Text style={styles.jobTitle}>Backend Developer</Text>
              <Text style={styles.dotSeparator}>•</Text>
              <Text style={styles.company}>TechNova</Text>
            </View>
          </View>

          <View style={styles.divider} />

          <View style={styles.detailsGrid}>
            <View>
              <Text style={styles.detailLabel}>Duration</Text>
              <Text style={styles.detailValue}>10–15 minutes</Text>
            </View>
            <View>
              <Text style={styles.detailLabel}>Type</Text>
              <Text style={styles.detailValue}>Technical Round</Text>
            </View>
            <View style={styles.fullWidth}>
              <Text style={styles.detailLabel}>Skills Tested</Text>
              <View style={styles.skillsContainer}>
                {skillsTested.map((skill, index) => (
                  <View key={index} style={styles.skillBadge}>
                    <Text style={styles.skillBadgeText}>{skill}</Text>
                  </View>
                ))}
              </View>
            </View>
          </View>
        </View>

        {/* AI Interviewer Section */}
        <View style={styles.interviewerCard}>
          <View style={styles.interviewerInfo}>
            <View style={styles.interviewerAvatar}>
              <MaterialIcons name="smart-toy" size={28} color={COLORS.primary} />
              <View style={styles.onlineIndicator} />
            </View>
            <View>
              <Text style={styles.interviewerLabel}>Interviewer</Text>
              <Text style={styles.interviewerName}>AI Recruiter</Text>
            </View>
          </View>
          <View style={styles.interviewerActions}>
            <TouchableOpacity style={styles.actionButton}>
              <MaterialIcons name="chat-bubble" size={20} color={COLORS.primary} />
            </TouchableOpacity>
            <TouchableOpacity style={styles.actionButton}>
              <MaterialIcons name="call" size={20} color={COLORS.primary} />
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>

      {/* Footer Button */}
      <View style={styles.footer}>
        <TouchableOpacity
          style={styles.startButton}
          onPress={() => router.push("/interview/live")}
        >
          <Text style={styles.startButtonText}>Start AI Interview</Text>
          <MaterialIcons name="play-circle" size={24} color={COLORS.primary} />
        </TouchableOpacity>
      </View>
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
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: "rgba(255,255,255,0.1)",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.1)",
    justifyContent: "center",
    alignItems: "center",
  },
  headerTitle: {
    fontSize: FONT_SIZES.lg,
    fontWeight: "700",
    color: COLORS.primary,
  },
  content: {
    padding: SPACING.md,
    paddingBottom: 100,
  },
  skillSection: {
    marginBottom: SPACING.md,
  },
  skillCard: {
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  skillLabel: {
    fontSize: FONT_SIZES.sm,
    fontWeight: "600",
    color: COLORS.textMuted,
    textTransform: "uppercase",
    letterSpacing: 0.5,
    marginBottom: SPACING.lg,
  },
  skillBars: {
    flexDirection: "row",
    justifyContent: "space-around",
    alignItems: "flex-end",
    height: 120,
  },
  skillBarContainer: {
    alignItems: "center",
    gap: SPACING.sm,
  },
  skillBar: {
    width: 40,
    backgroundColor: COLORS.primaryMuted,
    borderTopLeftRadius: 4,
    borderTopRightRadius: 4,
  },
  skillName: {
    fontSize: 10,
    fontWeight: "700",
    color: COLORS.textMuted,
  },
  detailsCard: {
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  jobHeader: {
    marginBottom: SPACING.md,
  },
  interviewId: {
    fontSize: 30,
    fontWeight: "700",
    color: COLORS.primary,
    letterSpacing: -0.5,
  },
  jobTitleRow: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 4,
  },
  jobTitle: {
    fontSize: FONT_SIZES.lg,
    fontWeight: "600",
    color: "#e2e8f0",
  },
  dotSeparator: {
    marginHorizontal: SPACING.sm,
    color: COLORS.textMuted,
  },
  company: {
    fontSize: FONT_SIZES.md,
    color: COLORS.textMuted,
    fontWeight: "500",
  },
  divider: {
    height: 1,
    backgroundColor: COLORS.border,
    marginBottom: SPACING.lg,
  },
  detailsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: SPACING.lg,
  },
  detailLabel: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.textMuted,
    textTransform: "uppercase",
    letterSpacing: 1,
    marginBottom: 4,
  },
  detailValue: {
    fontSize: FONT_SIZES.md,
    fontWeight: "700",
    color: COLORS.primary,
  },
  fullWidth: {
    width: "100%",
  },
  skillsContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: SPACING.sm,
    marginTop: SPACING.sm,
  },
  skillBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    backgroundColor: "rgba(255,255,255,0.1)",
    borderRadius: BORDER_RADIUS.full,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.05)",
  },
  skillBadgeText: {
    fontSize: FONT_SIZES.xs,
    fontWeight: "700",
    color: "#cbd5e1",
  },
  interviewerCard: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginTop: SPACING.md,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  interviewerInfo: {
    flexDirection: "row",
    alignItems: "center",
    gap: SPACING.md,
  },
  interviewerAvatar: {
    width: 56,
    height: 56,
    borderRadius: BORDER_RADIUS.md,
    backgroundColor: COLORS.border,
    justifyContent: "center",
    alignItems: "center",
    position: "relative",
  },
  onlineIndicator: {
    position: "absolute",
    bottom: -2,
    right: -2,
    width: 16,
    height: 16,
    borderRadius: 8,
    backgroundColor: COLORS.success,
    borderWidth: 2,
    borderColor: COLORS.surface,
  },
  interviewerLabel: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.textMuted,
  },
  interviewerName: {
    fontSize: FONT_SIZES.md,
    fontWeight: "700",
    color: COLORS.primary,
  },
  interviewerActions: {
    flexDirection: "row",
    gap: SPACING.sm,
  },
  actionButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: "rgba(255,255,255,0.1)",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.05)",
    justifyContent: "center",
    alignItems: "center",
  },
  footer: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    padding: SPACING.lg,
    backgroundColor: COLORS.backgroundLight,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  startButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: SPACING.sm,
    backgroundColor: "#334155",
    paddingVertical: SPACING.md,
    borderRadius: BORDER_RADIUS.lg,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.1)",
  },
  startButtonText: {
    fontSize: FONT_SIZES.lg,
    fontWeight: "700",
    color: COLORS.primary,
  },
});
