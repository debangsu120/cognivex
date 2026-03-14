import { View, Text, TouchableOpacity, StyleSheet, Dimensions, TextInput, ActivityIndicator, Alert } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { MaterialIcons } from "@expo/vector-icons";
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from "../../constants/theme";
import { useState } from "react";
import { useAuth } from "../../contexts/AuthContext";

const { width, height } = Dimensions.get("window");

export default function OnboardingScreen() {
  const router = useRouter();
  const { signIn, signUp, loading } = useAuth();

  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState<"candidate" | "recruiter">("candidate");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!email || !password) {
      Alert.alert("Error", "Please fill in all required fields");
      return;
    }

    if (!isLogin && !fullName) {
      Alert.alert("Error", "Please enter your name");
      return;
    }

    setIsSubmitting(true);
    try {
      if (isLogin) {
        await signIn(email, password);
      } else {
        await signUp(email, password, fullName, role);
      }
      router.replace("/(tabs)");
    } catch (error: any) {
      Alert.alert("Error", error.message || "Authentication failed");
    } finally {
      setIsSubmitting(false);
    }
  };

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
            {isLogin
              ? "Welcome back! Sign in to continue."
              : "Get matched with companies and complete AI-powered interviews anytime."}
          </Text>
        </View>

        {/* Auth Form */}
        <View style={styles.formContainer}>
          {!isLogin && (
            <View style={styles.inputContainer}>
              <TextInput
                style={styles.input}
                placeholder="Full Name"
                placeholderTextColor={COLORS.textMuted}
                value={fullName}
                onChangeText={setFullName}
                autoCapitalize="words"
              />
            </View>
          )}

          <View style={styles.inputContainer}>
            <TextInput
              style={styles.input}
              placeholder="Email"
              placeholderTextColor={COLORS.textMuted}
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
            />
          </View>

          <View style={styles.inputContainer}>
            <TextInput
              style={styles.input}
              placeholder="Password"
              placeholderTextColor={COLORS.textMuted}
              value={password}
              onChangeText={setPassword}
              secureTextEntry
            />
          </View>

          {!isLogin && (
            <View style={styles.roleContainer}>
              <Text style={styles.roleLabel}>I am a:</Text>
              <View style={styles.roleButtons}>
                <TouchableOpacity
                  style={[styles.roleButton, role === "candidate" && styles.roleButtonActive]}
                  onPress={() => setRole("candidate")}
                >
                  <MaterialIcons
                    name="person"
                    size={20}
                    color={role === "candidate" ? COLORS.background : COLORS.textMuted}
                  />
                  <Text style={[styles.roleButtonText, role === "candidate" && styles.roleButtonTextActive]}>
                    Candidate
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.roleButton, role === "recruiter" && styles.roleButtonActive]}
                  onPress={() => setRole("recruiter")}
                >
                  <MaterialIcons
                    name="business"
                    size={20}
                    color={role === "recruiter" ? COLORS.background : COLORS.textMuted}
                  />
                  <Text style={[styles.roleButtonText, role === "recruiter" && styles.roleButtonTextActive]}>
                    Recruiter
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          )}

          {/* Action Buttons */}
          <View style={styles.buttonContainer}>
            <TouchableOpacity
              style={styles.iconButton}
              onPress={handleSubmit}
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <ActivityIndicator size="small" color={COLORS.background} />
              ) : (
                <MaterialIcons name="arrow-forward" size={28} color="#0B0B0C" />
              )}
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.ctaButton}
              onPress={handleSubmit}
              disabled={isSubmitting}
            >
              <Text style={styles.ctaButtonText}>
                {isSubmitting ? "Please wait..." : isLogin ? "Sign In" : "Get Started"}
              </Text>
            </TouchableOpacity>
          </View>

          {/* Toggle Login/Signup */}
          <View style={styles.toggleContainer}>
            <Text style={styles.toggleText}>
              {isLogin ? "Don't have an account?" : "Already have an account?"}
            </Text>
            <TouchableOpacity onPress={() => setIsLogin(!isLogin)}>
              <Text style={styles.toggleLink}>
                {isLogin ? " Sign Up" : " Sign In"}
              </Text>
            </TouchableOpacity>
          </View>

          {/* Skip for now */}
          <TouchableOpacity
            style={styles.skipButton}
            onPress={() => router.push("/(tabs)")}
          >
            <Text style={styles.skipText}>Skip for now</Text>
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
  formContainer: {
    gap: SPACING.md,
  },
  inputContainer: {
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    borderWidth: 1,
    borderColor: COLORS.border,
    overflow: "hidden",
  },
  input: {
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.md,
    fontSize: FONT_SIZES.md,
    color: COLORS.primary,
  },
  roleContainer: {
    gap: SPACING.sm,
  },
  roleLabel: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.textMuted,
    fontWeight: "500",
  },
  roleButtons: {
    flexDirection: "row",
    gap: SPACING.sm,
  },
  roleButton: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: SPACING.sm,
    paddingVertical: SPACING.md,
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  roleButtonActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  roleButtonText: {
    fontSize: FONT_SIZES.md,
    color: COLORS.textMuted,
    fontWeight: "500",
  },
  roleButtonTextActive: {
    color: COLORS.background,
  },
  buttonContainer: {
    flexDirection: "row",
    gap: SPACING.md,
    alignItems: "center",
    marginTop: SPACING.sm,
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
  toggleContainer: {
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    gap: SPACING.xs,
  },
  toggleText: {
    fontSize: FONT_SIZES.md,
    color: COLORS.textMuted,
  },
  toggleLink: {
    fontSize: FONT_SIZES.md,
    color: COLORS.primary,
    fontWeight: "600",
  },
  skipButton: {
    alignSelf: "center",
    paddingVertical: SPACING.sm,
  },
  skipText: {
    fontSize: FONT_SIZES.md,
    color: COLORS.textMuted,
    textDecorationLine: "underline",
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
