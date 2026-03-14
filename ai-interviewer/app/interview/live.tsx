import React, { useEffect, useRef, useState, useCallback } from "react";
import { View, Text, TouchableOpacity, StyleSheet, Dimensions, Animated, Easing, Alert, ActivityIndicator } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter, useLocalSearchParams } from "expo-router";
import { MaterialIcons } from "@expo/vector-icons";
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from "../../constants/theme";
import { useInterview } from "../../hooks/useInterview";

const { width, height } = Dimensions.get("window");

const WaveformBar = ({ index, isActive }: { index: number; isActive: boolean }) => {
  const heightAnim = useRef(new Animated.Value(16)).current;
  const baseHeight = 16 + (index % 3) * 10;

  useEffect(() => {
    if (isActive) {
      const animation = Animated.loop(
        Animated.sequence([
          Animated.timing(heightAnim, {
            toValue: baseHeight + Math.random() * 20,
            duration: 200 + index * 50,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: false,
          }),
          Animated.timing(heightAnim, {
            toValue: baseHeight + Math.random() * 15,
            duration: 200 + index * 50,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: false,
          }),
        ])
      );
      animation.start();
      return () => animation.stop();
    } else {
      Animated.timing(heightAnim, {
        toValue: 16,
        duration: 300,
        useNativeDriver: false,
      }).start();
    }
  }, [isActive, index]);

  return (
    <Animated.View
      style={[
        styles.waveformBar,
        {
          height: heightAnim,
        },
      ]}
    />
  );
};

export default function LiveInterviewScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string }>();
  const interviewId = params.id;

  const [isListening, setIsListening] = useState(true);
  const [isRecording, setIsRecording] = useState(false);
  const [timeElapsed, setTimeElapsed] = useState(0);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(1);

  const {
    interview,
    currentQuestion,
    questions,
    loading,
    error,
    startInterview,
    submitAnswer,
    getNextQuestion,
    completeInterview,
  } = useInterview(interviewId);

  const pulseAnim = useRef(new Animated.Value(1)).current;

  // Timer
  useEffect(() => {
    const timer = setInterval(() => {
      setTimeElapsed(prev => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Pulse animation
  useEffect(() => {
    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.1,
          duration: 1500,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 1500,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ])
    );
    pulse.start();
    return () => pulse.stop();
  }, []);

  // Start interview on mount
  useEffect(() => {
    if (interviewId && !interview) {
      startInterview().catch(err => {
        Alert.alert("Error", "Failed to start interview");
      });
    }
  }, [interviewId]);

  // Handle end interview
  const handleEndInterview = useCallback(async () => {
    Alert.alert(
      "End Interview",
      "Are you sure you want to end the interview?",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "End",
          style: "destructive",
          onPress: async () => {
            try {
              if (interviewId) {
                await completeInterview();
              }
              router.push("/(tabs)/results");
            } catch (err) {
              router.push("/(tabs)/results");
            }
          },
        },
      ]
    );
  }, [interviewId, completeInterview, router]);

  // Handle mic press - record audio
  const handleMicPress = useCallback(async () => {
    if (isRecording) {
      // Stop recording and submit
      setIsRecording(false);
      // In a real app, we would capture the audio blob here
      // For now, we'll submit a text answer as placeholder
      if (currentQuestion) {
        try {
          await submitAnswer(currentQuestion.id, "Audio answer placeholder");
          const nextQ = await getNextQuestion();
          if (nextQ) {
            setCurrentQuestionIndex(prev => prev + 1);
          } else {
            // No more questions
            await completeInterview();
            router.push("/(tabs)/results");
          }
        } catch (err) {
          Alert.alert("Error", "Failed to submit answer");
        }
      }
    } else {
      // Start recording
      setIsRecording(true);
    }
  }, [isRecording, currentQuestion, submitAnswer, getNextQuestion, completeInterview, router]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={handleEndInterview}>
          <MaterialIcons name="arrow-back-ios-new" size={20} color={COLORS.primary} />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={styles.headerLabel}>Live Session</Text>
          <Text style={styles.headerTitle}>AI Interview in Progress</Text>
        </View>
        <View style={{ width: 40 }} />
      </View>

      {/* Timer */}
      <View style={styles.timerContainer}>
        <View style={styles.timerBadge}>
          <View style={styles.timerDot} />
          <Text style={styles.timerText}>{formatTime(timeElapsed)}</Text>
        </View>
      </View>

      {/* Main Content */}
      <View style={styles.content}>
        {/* Loading state */}
        {loading && !currentQuestion ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={COLORS.primaryMuted} />
            <Text style={styles.loadingText}>Preparing your interview...</Text>
          </View>
        ) : (
          <>
            {/* AI Avatar */}
            <Animated.View style={[styles.avatarContainer, { transform: [{ scale: pulseAnim }] }]}>
              <View style={styles.avatarRingOuter} />
              <View style={styles.avatarRingInner} />
              <View style={styles.avatar}>
                <MaterialIcons name="smart-toy" size={80} color={COLORS.primaryMuted} />
              </View>
              <View style={styles.avatarOverlay} />
            </Animated.View>

            {/* Speech Bubble */}
            <View style={styles.speechBubble}>
              <View style={styles.speechBubbleArrow} />
              <Text style={styles.interviewerLabel}>AI Interviewer</Text>
              <Text style={styles.questionText}>
                "{currentQuestion?.question_text || 'What is REST API and how does it work?'}"
              </Text>
            </View>

            {/* Question Progress */}
            <View style={styles.progressContainer}>
              <Text style={styles.progressText}>
                Question {currentQuestionIndex} of {questions.length || 7}
              </Text>
            </View>

            {/* Audio Visualization */}
            <View style={styles.waveformContainer}>
              <View style={styles.waveform}>
                {[...Array(9)].map((_, i) => (
                  <WaveformBar key={i} index={i} isActive={isListening || isRecording} />
                ))}
              </View>
              <View style={styles.listeningContainer}>
                <Text style={styles.listeningText}>
                  {isRecording ? "Recording... Tap to submit" : "Listening..."}
                </Text>
              </View>

              {/* Mic Button */}
              <TouchableOpacity
                style={[styles.micButton, isRecording && styles.micButtonRecording]}
                onPress={handleMicPress}
                disabled={loading}
              >
                <MaterialIcons
                  name={isRecording ? "stop" : "mic"}
                  size={36}
                  color={COLORS.background}
                />
                <View style={styles.micBorder} />
              </TouchableOpacity>
            </View>
          </>
        )}
      </View>

      {/* Bottom Controls */}
      <View style={styles.controls}>
        <TouchableOpacity
          style={styles.muteButton}
          onPress={() => setIsListening(!isListening)}
        >
          <MaterialIcons
            name={isListening ? "mic" : "mic-off"}
            size={24}
            color={COLORS.textMuted}
          />
          <Text style={styles.muteButtonText}>
            {isListening ? "Mute Mic" : "Unmute"}
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.endButton}
          onPress={handleEndInterview}
        >
          <MaterialIcons name="call-end" size={24} color={COLORS.error} />
          <Text style={styles.endButtonText}>End Interview</Text>
        </TouchableOpacity>
      </View>

      {/* Bottom Nav (Optional Context) */}
      <View style={styles.bottomNav}>
        <TouchableOpacity style={styles.navItem} onPress={() => router.push("/(tabs)")}>
          <MaterialIcons name="home" size={24} color={COLORS.primaryMuted} />
        </TouchableOpacity>
        <TouchableOpacity style={styles.navItem} onPress={() => router.push("/(tabs)/results")}>
          <MaterialIcons name="history" size={24} color={COLORS.textMuted} />
        </TouchableOpacity>
        <TouchableOpacity style={styles.navItem} onPress={() => router.push("/(tabs)/profile")}>
          <MaterialIcons name="person" size={24} color={COLORS.textMuted} />
        </TouchableOpacity>
        <TouchableOpacity style={styles.navItem}>
          <MaterialIcons name="settings" size={24} color={COLORS.textMuted} />
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
    paddingHorizontal: SPACING.lg,
    paddingTop: SPACING.xl,
    paddingBottom: SPACING.md,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: "#1a1a1a",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.05)",
    justifyContent: "center",
    alignItems: "center",
  },
  headerCenter: {
    alignItems: "center",
  },
  headerLabel: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.textMuted,
    fontWeight: "600",
    textTransform: "uppercase",
    letterSpacing: 1,
  },
  headerTitle: {
    fontSize: FONT_SIZES.md,
    color: COLORS.primary,
    fontWeight: "500",
  },
  timerContainer: {
    alignItems: "center",
    paddingVertical: SPACING.sm,
  },
  timerBadge: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "rgba(226,232,240,0.1)",
    paddingHorizontal: 16,
    paddingVertical: 6,
    borderRadius: BORDER_RADIUS.full,
    borderWidth: 1,
    borderColor: "rgba(226,232,240,0.2)",
    gap: 8,
  },
  timerDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: COLORS.primaryMuted,
  },
  timerText: {
    fontSize: FONT_SIZES.md,
    fontWeight: "700",
    color: COLORS.primaryMuted,
  },
  content: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: SPACING.lg,
    gap: SPACING.xl,
  },
  loadingContainer: {
    alignItems: "center",
    gap: SPACING.lg,
  },
  loadingText: {
    color: COLORS.textMuted,
    fontSize: FONT_SIZES.md,
  },
  avatarContainer: {
    position: "relative",
    alignItems: "center",
    justifyContent: "center",
  },
  avatarRingOuter: {
    position: "absolute",
    width: 200,
    height: 200,
    borderRadius: 100,
    borderWidth: 2,
    borderColor: "rgba(226,232,240,0.3)",
    transform: [{ scale: 1.25 }],
    opacity: 0.2,
  },
  avatarRingInner: {
    position: "absolute",
    width: 200,
    height: 200,
    borderRadius: 100,
    borderWidth: 1,
    borderColor: "rgba(226,232,240,0.5)",
    transform: [{ scale: 1.1 }],
    opacity: 0.4,
  },
  avatar: {
    width: 192,
    height: 192,
    borderRadius: 96,
    backgroundColor: "#1a1a1a",
    borderWidth: 4,
    borderColor: "rgba(255,255,255,0.05)",
    justifyContent: "center",
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.5,
    shadowRadius: 16,
  },
  avatarOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(226,232,240,0.05)",
    borderRadius: 96,
  },
  speechBubble: {
    width: "100%",
    maxWidth: 320,
    backgroundColor: "rgba(255,255,255,0.03)",
    borderRadius: BORDER_RADIUS.xl,
    padding: SPACING.lg,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.05)",
    position: "relative",
  },
  speechBubbleArrow: {
    position: "absolute",
    top: -8,
    left: "50%",
    marginLeft: -8,
    width: 16,
    height: 16,
    backgroundColor: "#232323",
    transform: [{ rotate: "45deg" }],
    borderLeftWidth: 1,
    borderTopWidth: 1,
    borderColor: "rgba(255,255,255,0.05)",
  },
  interviewerLabel: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.textMuted,
    fontWeight: "600",
    textTransform: "uppercase",
    letterSpacing: 0.5,
    marginBottom: SPACING.sm,
  },
  questionText: {
    fontSize: FONT_SIZES.xl,
    fontWeight: "600",
    color: COLORS.primary,
    lineHeight: 28,
  },
  progressContainer: {
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    backgroundColor: "rgba(255,255,255,0.05)",
    borderRadius: BORDER_RADIUS.full,
  },
  progressText: {
    color: COLORS.textMuted,
    fontSize: FONT_SIZES.sm,
    fontWeight: "500",
  },
  waveformContainer: {
    alignItems: "center",
    gap: SPACING.lg,
  },
  waveform: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
    height: 48,
  },
  waveformBar: {
    width: 3,
    backgroundColor: COLORS.primaryMuted,
    borderRadius: 2,
  },
  listeningContainer: {
    flexDirection: "row",
    alignItems: "center",
    gap: SPACING.sm,
  },
  listeningText: {
    fontSize: FONT_SIZES.md,
    color: COLORS.textMuted,
    fontWeight: "500",
  },
  micButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: "#e2e8f0",
    justifyContent: "center",
    alignItems: "center",
    shadowColor: "rgba(255,255,255,0.1)",
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 1,
    shadowRadius: 40,
  },
  micButtonRecording: {
    backgroundColor: COLORS.error,
  },
  micBorder: {
    position: "absolute",
    width: 80,
    height: 80,
    borderRadius: 40,
    borderWidth: 4,
    borderColor: "rgba(255,255,255,0.2)",
  },
  controls: {
    flexDirection: "row",
    paddingHorizontal: SPACING.xl,
    paddingVertical: SPACING.xl,
    gap: SPACING.md,
  },
  muteButton: {
    flex: 1,
    height: 64,
    borderRadius: BORDER_RADIUS.xl,
    backgroundColor: "#1a1a1a",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.05)",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: SPACING.sm,
  },
  muteButtonText: {
    fontSize: FONT_SIZES.md,
    fontWeight: "600",
    color: COLORS.primary,
  },
  endButton: {
    flex: 1,
    height: 64,
    borderRadius: BORDER_RADIUS.xl,
    backgroundColor: "rgba(255,255,255,0.05)",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.1)",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: SPACING.sm,
  },
  endButtonText: {
    fontSize: FONT_SIZES.md,
    fontWeight: "600",
    color: COLORS.error,
  },
  bottomNav: {
    flexDirection: "row",
    justifyContent: "space-around",
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.md,
    borderTopWidth: 1,
    borderTopColor: "rgba(255,255,255,0.05)",
    backgroundColor: "rgba(15,15,15,0.5)",
  },
  navItem: {
    padding: SPACING.sm,
  },
});
