import { View, Text, TouchableOpacity, StyleSheet, Dimensions } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { MaterialIcons } from "@expo/vector-icons";
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from "../../constants/theme";

const { width, height } = Dimensions.get("window");

export default function OnboardingScreen() {
  const router = useRouter();

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        {/* Hero Image Section */}
        <View style={styles.heroContainer}>
          <View style={styles.heroImage}>
            <View style={styles.heroPlaceholder}>
              <MaterialIcons name="smart-toy" size={80} color="#e2e8f0" />
            </View>
          </View>
          <View style={styles.heroOverlay} />
        </View>

        {/* Text Content */}
        <View style={styles.textContainer}>
          <Text style={styles.title}>
            AI Interviews{"\n"}Made Simple
          </Text>
          <Text style={styles.subtitle}>
            Get matched with companies and complete AI-powered interviews anytime.
          </Text>
        </View>

        {/* Action Buttons */}
        <View style={styles.buttonContainer}>
          <TouchableOpacity
            style={styles.iconButton}
            onPress={() => router.push("/(tabs)")}
          >
            <MaterialIcons name="arrow-forward" size={28} color="#0B0B0C" />
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.ctaButton}
            onPress={() => router.push("/(tabs)")}
          >
            <Text style={styles.ctaButtonText}>Get Started</Text>
          </TouchableOpacity>
        </View>

        {/* Pagination Dots */}
        <View style={styles.pagination}>
          <View style={styles.activeDot} />
          <View style={styles.dot} />
          <View style={styles.dot} />
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  content: {
    flex: 1,
    paddingHorizontal: SPACING.lg,
    justifyContent: "space-between",
    paddingBottom: SPACING.xl,
  },
  heroContainer: {
    width: "100%",
    aspectRatio: 4 / 5,
    borderRadius: BORDER_RADIUS.lg,
    overflow: "hidden",
    marginTop: SPACING.lg,
  },
  heroImage: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.05)",
  },
  heroPlaceholder: {
    width: "100%",
    height: "100%",
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#1A1A1C",
  },
  heroOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(0,0,0,0.4)",
  },
  textContainer: {
    gap: SPACING.md,
  },
  title: {
    fontSize: 36,
    fontWeight: "700",
    color: COLORS.primary,
    lineHeight: 42,
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: FONT_SIZES.lg,
    color: COLORS.textMuted,
    fontWeight: "300",
    lineHeight: 26,
    maxWidth: 320,
  },
  buttonContainer: {
    flexDirection: "row",
    gap: SPACING.md,
    alignItems: "center",
  },
  iconButton: {
    width: 64,
    height: 64,
    borderRadius: BORDER_RADIUS.lg,
    backgroundColor: COLORS.primaryMuted,
    justifyContent: "center",
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  ctaButton: {
    flex: 1,
    height: 64,
    borderRadius: BORDER_RADIUS.lg,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.1)",
    backgroundColor: "#cbd5e1",
    justifyContent: "center",
    alignItems: "center",
  },
  ctaButtonText: {
    fontSize: FONT_SIZES.xl,
    fontWeight: "600",
    color: COLORS.background,
    letterSpacing: 0.5,
  },
  pagination: {
    flexDirection: "row",
    gap: SPACING.sm,
    paddingLeft: SPACING.sm,
  },
  activeDot: {
    width: 32,
    height: 6,
    borderRadius: 3,
    backgroundColor: COLORS.primaryMuted,
  },
  dot: {
    width: 8,
    height: 6,
    borderRadius: 3,
    backgroundColor: "#1A1A1C",
  },
});
