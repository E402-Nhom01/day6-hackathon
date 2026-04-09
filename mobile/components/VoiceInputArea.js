import React, { useEffect } from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { Mic, MicOff } from 'lucide-react-native';
import Animated, { 
    useSharedValue, 
    useAnimatedStyle, 
    withRepeat, 
    withTiming, 
    withSequence,
    Easing 
} from 'react-native-reanimated';

export default function VoiceInputArea({ isRecording, onStart, onStop, partialTranscript, title }) {
    const scale = useSharedValue(1);
    const opacity = useSharedValue(1);

    useEffect(() => {
        if (isRecording) {
            scale.value = withRepeat(
                withSequence(
                    withTiming(1.3, { duration: 800, easing: Easing.inOut(Easing.ease) }),
                    withTiming(1, { duration: 800, easing: Easing.inOut(Easing.ease) })
                ), 
                -1, 
                true
            );
            opacity.value = withRepeat(
                withSequence(
                    withTiming(0.4, { duration: 800, easing: Easing.inOut(Easing.ease) }),
                    withTiming(0.8, { duration: 800, easing: Easing.inOut(Easing.ease) })
                ), 
                -1, 
                true
            );
        } else {
            scale.value = withTiming(1, { duration: 300 });
            opacity.value = withTiming(0, { duration: 300 });
        }
    }, [isRecording]);

    const pulseStyle = useAnimatedStyle(() => {
        return {
            transform: [{ scale: scale.value }],
            opacity: opacity.value,
        };
    });

    return (
        <View style={styles.container}>
            <Text style={styles.title}>{title}</Text>
            
            <View style={styles.micContainer}>
                {/* Pulsing ring background */}
                <Animated.View style={[styles.pulseRing, pulseStyle]} />
                
                {/* Main Button */}
                <Pressable 
                    onPress={isRecording ? onStop : onStart} 
                    style={[styles.micButton, isRecording ? styles.micRecording : styles.micIdle]}
                >
                    {isRecording ? (
                        <MicOff color="#fff" size={32} />
                    ) : (
                        <Mic color="#fff" size={32} />
                    )}
                </Pressable>
            </View>

            <View style={styles.transcriptBox}>
                <Text style={styles.transcriptLabel}>Live Transcript</Text>
                <Text style={styles.transcriptText}>
                    {partialTranscript || (isRecording ? "Listening..." : "Tap to speak your destination...")}
                </Text>
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        alignItems: 'center',
        paddingVertical: 40,
        width: '100%',
    },
    title: {
        fontSize: 24,
        fontWeight: '700',
        color: '#111827',
        marginBottom: 40,
        textAlign: 'center',
    },
    micContainer: {
        width: 120,
        height: 120,
        justifyContent: 'center',
        alignItems: 'center',
    },
    pulseRing: {
        position: 'absolute',
        width: 100,
        height: 100,
        borderRadius: 50,
        backgroundColor: '#3b82f6',
    },
    micButton: {
        width: 80,
        height: 80,
        borderRadius: 40,
        justifyContent: 'center',
        alignItems: 'center',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 8 },
        shadowOpacity: 0.15,
        shadowRadius: 12,
        elevation: 10,
        zIndex: 2,
    },
    micIdle: {
        backgroundColor: '#111827',
    },
    micRecording: {
        backgroundColor: '#ef4444',
    },
    transcriptBox: {
        marginTop: 50,
        width: '90%',
        backgroundColor: '#f9fafb',
        borderRadius: 16,
        padding: 24,
        borderWidth: 1,
        borderColor: '#e5e7eb',
        minHeight: 120,
    },
    transcriptLabel: {
        fontSize: 12,
        fontWeight: '600',
        textTransform: 'uppercase',
        color: '#9ca3af',
        marginBottom: 8,
        letterSpacing: 0.5,
    },
    transcriptText: {
        fontSize: 18,
        color: '#374151',
        lineHeight: 28,
        fontStyle: 'italic',
    }
});
