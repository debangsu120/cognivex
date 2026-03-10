import { View, Text, TouchableOpacity, StyleSheet, ScrollView, Dimensions } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { MaterialIcons } from "@expo/vector-icons";
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from "../../constants/theme";

const { width } = Dimensions.get("window");
const CIRCLE_SIZE = 64;
const STROKE_WIDTH = 3;
const RADIUS = (CIRCLE_SIZE - STROKE_WIDTH) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

const skills = [
  { name: "Python", score: 8, total: 10 },
  { name: "FastAPI", score: 7, total: 10 },
  { name: "SQL", score: 7, total: 10 },
  { name: "Problem Solving", score: 8, total: 10 },
];

const ProgressRing = ({ score, total }: { score: number; total: number }) => {
  const progress = score / total;
  const strokeDashoffset = CIRCUMFERENCE * (1 - progress);

  return (
    <View style={styles.ringContainer}>
      <View style={styles.ring}>
        <View style={styles.ringBackground} />
        <View
          style={[
            styles.ringProgress,
            {
              borderColor: COLORS.primary,
              borderWidth: STROKE_WIDTH,
              borderRadius: RADIUS,
              width: CIRCLE_SIZE,
              height: CIRCLE_SIZE,
              transform: [{ rotate: "-90deg" }],
            },
          ]}
        >
          <View
            style={[
              styles.ringProgressInner,
              {
                width: CIRCLE_SIZE - STROKE_WIDTH * 2,
                height: CIRCLE_SIZE - STROKE_WIDTH * 2,
                borderRadius: (CIRCLE_SIZE - STROKE_WIDTH * 2) / 2,
              },
            ]}
          />
        </View>
        <View style={styles.ringCenter}>
          <Text style={styles.ringText}>{score}/{total}</Text>
        </View>
      </View>
    </View>
  );
};

export default function ResultsScreen() {
  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.headerButton}>
          <MaterialIcons name="arrow-back" size={24} color={COLORS.primary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Interview Results</Text>
        <TouchableOpacity style={styles.headerButton}>
          <MaterialIcons name="notifications" size={24} color={COLORS.primary} />
        </TouchableOpacity>
      </View>

      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {/* Score Card */}
        <View style={styles.scoreCard}>
          <View style={styles.passedBadge}>
            <View style={styles.passedDot} />
            <Text style={styles.passedText}>Passed AI Screening</Text>
          </View>
          <Text style={styles.totalScore}>82 / 100</Text>
          <Text style={styles.scoreLabel}>Total Interview Score</Text>
          <TouchableOpacity style={styles.downloadButton}>
            <Text style={styles.downloadButtonText}>Download Interview Report</Text>
          </TouchableOpacity>
        </View>

        {/* Skill Analysis */}
        <View style={styles.skillSection}>
          <Text style={styles.sectionTitle}>Skill Analysis</Text>
          <View style={styles.skillsGrid}>
            {skills.map((skill, index) => (
              <View key={index} style={styles.skillCard}>
                <ProgressRing score={skill.score} total={skill.total} />
                <Text style={styles.skillName}>{skill.name}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* Transcript Preview */}
        <View style={styles.transcriptSection}>
          <View style={styles.transcriptHeader}>
            <Text style={styles.sectionTitle}>Transcript Preview</Text>
            <Text style={styles.questionCount}>8 Questions total</Text>
          </View>
          <View style={styles.transcriptContent}>
            <Text style={styles.questionLabel}>Q1: What is REST API?</Text>
            <Text style={styles.answerText}>
              "REST stands for Representational State Transfer. It is an architectural
              style for providing standards between computer systems on the web..."
            </Text>
          </View>
          <TouchableOpacity style={styles.viewAllButton}>
            <Text style={styles.viewAllButtonText}>View Full Transcript</Text>
          </TouchableOpacity>
        </View>

        {/* AI Insight */}
        <View style={styles.insightCard}>
          <MaterialIcons name="lightbulb" size={24} color={COLORS.textMuted} />
          <View style={styles.insightContent}>
            <Text style={styles.insightTitle}>AI Insight</Text>
            <Text style={styles.insightText}>
              You demonstrated strong technical depth in Python. Consider improving
              your explanation of FastAPI middleware for the next stage.
            </Text>
          </View>
        </View>
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
  headerButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
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
  scoreCard: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    alignItems: "center",
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  passedBadge: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "rgba(16,185,129,0.1)",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: BORDER_RADIUS.full,
    borderWidth: 1,
    borderColor: "rgba(16,185,129,0.2)",
    marginBottom: SPACING.md,
  },
  passedDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: COLORS.success,
    marginRight: 6,
  },
  passedText: {
    fontSize: FONT_SIZES.xs,
    fontWeight: "700",
    color: COLORS.success,
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  totalScore: {
    fontSize: 48,
    fontWeight: "700",
    color: COLORS.primary,
  },
  scoreLabel: {
    fontSize: FONT_SIZES.md,
    color: COLORS.textMuted,
    fontWeight: "500",
    marginBottom: SPACING.md,
  },
  downloadButton: {
    width: "100%",
    backgroundColor: "#e2e8f0",
    paddingVertical: 14,
    borderRadius: BORDER_RADIUS.md,
    alignItems: "center",
  },
  downloadButtonText: {
    fontSize: FONT_SIZES.md,
    fontWeight: "700",
    color: COLORS.background,
  },
  skillSection: {
    marginTop: SPACING.lg,
  },
  sectionTitle: {
    fontSize: FONT_SIZES.lg,
    fontWeight: "700",
    color: COLORS.primary,
    marginBottom: SPACING.md,
  },
  skillsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: SPACING.sm,
  },
  skillCard: {
    width: (width - SPACING.md * 2 - SPACING.sm) / 2 - SPACING.sm,
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    alignItems: "center",
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  ringContainer: {
    width: CIRCLE_SIZE,
    height: CIRCLE_SIZE,
    justifyContent: "center",
    alignItems: "center",
  },
  ring: {
    width: CIRCLE_SIZE,
    height: CIRCLE_SIZE,
    position: "relative",
  },
  ringBackground: {
    position: "absolute",
    width: CIRCLE_SIZE,
    height: CIRCLE_SIZE,
    borderRadius: CIRCLE_SIZE / 2,
    borderWidth: STROKE_WIDTH,
    borderColor: COLORS.border,
  },
  ringProgress: {
    position: "absolute",
    justifyContent: "center",
    alignItems: "center",
  },
  ringProgressInner: {
    backgroundColor: "transparent",
  },
  ringCenter: {
    position: "absolute",
    width: CIRCLE_SIZE,
    height: CIRCLE_SIZE,
    justifyContent: "center",
    alignItems: "center",
  },
  ringText: {
    fontSize: 12,
    fontWeight: "700",
    color: COLORS.primary,
  },
  skillName: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.textMuted,
    fontWeight: "500",
    marginTop: SPACING.sm,
    textAlign: "center",
  },
  transcriptSection: {
    marginTop: SPACING.lg,
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    borderWidth: 1,
    borderColor: COLORS.border,
    overflow: "hidden",
  },
  transcriptHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    padding: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  questionCount: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.primaryMuted,
    fontWeight: "500",
  },
  transcriptContent: {
    padding: SPACING.md,
  },
  questionLabel: {
    fontSize: FONT_SIZES.xs,
    fontWeight: "700",
    color: COLORS.primaryMuted,
    textTransform: "uppercase",
    letterSpacing: 0.5,
    marginBottom: SPACING.sm,
  },
  answerText: {
    fontSize: FONT_SIZES.md,
    color: "#a1a1aa",
    lineHeight: 22,
    fontStyle: "italic",
    borderLeftWidth: 2,
    borderLeftColor: "rgba(226,232,240,0.4)",
    paddingLeft: SPACING.sm,
  },
  viewAllButton: {
    width: "100%",
    backgroundColor: "#e2e8f0",
    paddingVertical: 14,
    alignItems: "center",
  },
  viewAllButtonText: {
    fontSize: FONT_SIZES.md,
    fontWeight: "700",
    color: COLORS.background,
  },
  insightCard: {
    flexDirection: "row",
    backgroundColor: "rgba(255,255,255,0.05)",
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginTop: SPACING.lg,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.1)",
    gap: SPACING.md,
  },
  insightContent: {
    flex: 1,
  },
  insightTitle: {
    fontSize: FONT_SIZES.md,
    fontWeight: "700",
    color: "#e2e8f0",
    marginBottom: 4,
  },
  insightText: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.textMuted,
    lineHeight: 18,
  },
});
