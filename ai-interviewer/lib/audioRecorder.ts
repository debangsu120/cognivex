/**
 * Audio Recording Service
 * Handles audio recording for interview answers
 */

import { Audio, AVPlaybackStatus } from 'expo-av';
import { readAsStringAsync } from 'expo-file-system';

export interface RecordingResult {
  uri: string;
  duration: number;
  base64?: string;
}

export interface RecordingState {
  isRecording: boolean;
  isPaused: boolean;
  duration: number;
}

class AudioRecorder {
  private recording: Audio.Recording | null = null;
  private sound: Audio.Sound | null = null;
  private recordingState: RecordingState = {
    isRecording: false,
    isPaused: false,
    duration: 0,
  };

  /**
   * Request microphone permissions
   */
  async requestPermissions(): Promise<boolean> {
    try {
      const { status } = await Audio.requestPermissionsAsync();
      return status === 'granted';
    } catch (error) {
      console.error('Error requesting audio permissions:', error);
      return false;
    }
  }

  /**
   * Configure audio mode for recording
   */
  private async configureAudioMode(): Promise<void> {
    try {
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
        staysActiveInBackground: false,
        shouldDuckAndroid: true,
        playThroughEarpieceAndroid: false,
      });
    } catch (error) {
      console.error('Error configuring audio mode:', error);
      throw error;
    }
  }

  /**
   * Start audio recording
   */
  async start(): Promise<void> {
    // Check if already recording
    if (this.recordingState.isRecording) {
      console.log('Already recording');
      return;
    }

    // Request permissions
    const hasPermission = await this.requestPermissions();
    if (!hasPermission) {
      throw new Error('Microphone permission not granted. Please enable microphone access in settings.');
    }

    // Configure audio mode
    await this.configureAudioMode();

    try {
      // Create recording
      const { recording } = await Audio.Recording.createAsync(
        {
          android: {
            extension: '.m4a',
            outputFormat: Audio.AndroidOutputFormat.MPEG_4,
            audioEncoder: Audio.AndroidAudioEncoder.AAC,
            sampleRate: 44100,
            numberOfChannels: 1,
            bitRate: 128000,
          },
          ios: {
            extension: '.m4a',
            outputFormat: Audio.IOSOutputFormat.MPEG4AAC,
            audioQuality: Audio.IOSAudioQuality.HIGH,
            sampleRate: 44100,
            numberOfChannels: 1,
            bitRate: 128000,
            linearPCMBitDepth: 16,
            linearPCMIsBigEndian: false,
            linearPCMIsFloat: false,
          },
          web: {
            mimeType: 'audio/webm',
            bitsPerSecond: 128000,
          },
        },
        (status) => {
          if (status.isRecording) {
            this.recordingState.duration = status.durationMillis || 0;
          }
        }
      );

      this.recording = recording;
      this.recordingState.isRecording = true;
      this.recordingState.isPaused = false;

      console.log('Recording started');
    } catch (error) {
      console.error('Error starting recording:', error);
      throw new Error('Failed to start recording. Please try again.');
    }
  }

  /**
   * Pause recording
   */
  async pause(): Promise<void> {
    if (!this.recording || !this.recordingState.isRecording) {
      return;
    }

    try {
      await this.recording.pauseAsync();
      this.recordingState.isPaused = true;
      console.log('Recording paused');
    } catch (error) {
      console.error('Error pausing recording:', error);
      throw error;
    }
  }

  /**
   * Resume recording
   */
  async resume(): Promise<void> {
    if (!this.recording || !this.recordingState.isPaused) {
      return;
    }

    try {
      await this.recording.startAsync();
      this.recordingState.isPaused = false;
      console.log('Recording resumed');
    } catch (error) {
      console.error('Error resuming recording:', error);
      throw error;
    }
  }

  /**
   * Stop recording and get result
   */
  async stop(): Promise<RecordingResult> {
    if (!this.recording) {
      throw new Error('No active recording to stop');
    }

    try {
      // Stop recording
      await this.recording.stopAndUnloadAsync();

      // Get URI and status
      const uri = this.recording.getURI();
      const status = await this.recording.getStatusAsync();
      const duration = status.durationMillis || this.recordingState.duration;

      // Reset state
      this.recording = null;
      this.recordingState = {
        isRecording: false,
        isPaused: false,
        duration: 0,
      };

      // Reset audio mode
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,
        playsInSilentModeIOS: true,
      });

      if (!uri) {
        throw new Error('Recording URI not available');
      }

      // Read file as base64
      let base64: string | undefined;
      try {
        base64 = await readAsStringAsync(uri, {
          encoding: 'base64' as any,
        });
      } catch (error) {
        console.warn('Could not read file as base64:', error);
      }

      console.log('Recording stopped, duration:', duration);

      return {
        uri,
        duration,
        base64,
      };
    } catch (error) {
      console.error('Error stopping recording:', error);
      // Reset state even on error
      this.recording = null;
      this.recordingState = {
        isRecording: false,
        isPaused: false,
        duration: 0,
      };
      throw error;
    }
  }

  /**
   * Cancel recording without saving
   */
  async cancel(): Promise<void> {
    if (!this.recording) {
      return;
    }

    try {
      await this.recording.stopAndUnloadAsync();
    } catch (error) {
      // Ignore errors when cancelling
    }

    this.recording = null;
    this.recordingState = {
      isRecording: false,
      isPaused: false,
      duration: 0,
    };

    // Reset audio mode
    try {
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,
        playsInSilentModeIOS: true,
      });
    } catch (error) {
      // Ignore
    }

    console.log('Recording cancelled');
  }

  /**
   * Get current recording state
   */
  getState(): RecordingState {
    return { ...this.recordingState };
  }

  /**
   * Check if currently recording
   */
  isActive(): boolean {
    return this.recordingState.isRecording;
  }

  /**
   * Check if recording is paused
   */
  isPausedState(): boolean {
    return this.recordingState.isPaused;
  }

  /**
   * Get recording duration in seconds
   */
  getDuration(): number {
    return Math.floor(this.recordingState.duration / 1000);
  }

  /**
   * Play recorded audio for preview
   */
  async playRecording(uri: string): Promise<void> {
    try {
      // Unload previous sound if exists
      if (this.sound) {
        await this.sound.unloadAsync();
      }

      // Load and play
      const { sound } = await Audio.Sound.createAsync(
        { uri },
        { shouldPlay: true }
      );

      this.sound = sound;

      // Cleanup when done
      sound.setOnPlaybackStatusUpdate((status: AVPlaybackStatus) => {
        if (status.isLoaded && status.didJustFinish) {
          sound.unloadAsync();
          this.sound = null;
        }
      });
    } catch (error) {
      console.error('Error playing recording:', error);
      throw error;
    }
  }

  /**
   * Stop playback
   */
  async stopPlayback(): Promise<void> {
    if (this.sound) {
      await this.sound.stopAsync();
      await this.sound.unloadAsync();
      this.sound = null;
    }
  }
}

// Export singleton instance
export const audioRecorder = new AudioRecorder();
