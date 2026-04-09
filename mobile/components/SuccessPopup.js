import React, { useEffect } from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { CheckCircle2 } from 'lucide-react-native';
import Animated, { 
    useSharedValue, 
    useAnimatedStyle, 
    withSpring, 
    withTiming 
} from 'react-native-reanimated';

export default function SuccessPopup({ onReset }) {
    const scale = useSharedValue(0.5);
    const opacity = useSharedValue(0);
    const translateY = useSharedValue(20);

    useEffect(() => {
        scale.value = withSpring(1, { damping: 12, stiffness: 90 });
        opacity.value = withTiming(1, { duration: 400 });
        translateY.value = withSpring(0, { damping: 15, stiffness: 100 });
    }, []);

    const animatedStyle = useAnimatedStyle(() => {
        return {
            transform: [
                { scale: scale.value },
                { translateY: translateY.value }
            ],
            opacity: opacity.value,
        };
    });

    return (
        <View style={styles.overlay}>
            <Animated.View style={[styles.card, animatedStyle]}>
                <View style={styles.iconContainer}>
                    <CheckCircle2 color="#10b981" size={80} />
                </View>
                
                <Text style={styles.title}>Booking Confirmed!</Text>
                <Text style={styles.subtitle}>
                    Your ride is on the way. The driver will arrive shortly.
                </Text>

                <Pressable style={styles.btn} onPress={onReset}>
                    <Text style={styles.btnText}>Book Another Ride</Text>
                </Pressable>
            </Animated.View>
        </View>
    );
}

const styles = StyleSheet.create({
    overlay: {
        ...StyleSheet.absoluteFillObject,
        backgroundColor: 'rgba(0, 0, 0, 0.4)',
        justifyContent: 'center',
        alignItems: 'center',
        padding: 24,
        zIndex: 100,
    },
    card: {
        width: '100%',
        backgroundColor: '#fff',
        borderRadius: 24,
        padding: 32,
        alignItems: 'center',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 10 },
        shadowOpacity: 0.1,
        shadowRadius: 20,
        elevation: 10,
    },
    iconContainer: {
        marginBottom: 24,
    },
    title: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#111827',
        marginBottom: 12,
        textAlign: 'center',
    },
    subtitle: {
        fontSize: 16,
        color: '#6b7280',
        textAlign: 'center',
        marginBottom: 32,
        lineHeight: 24,
    },
    btn: {
        width: '100%',
        paddingVertical: 16,
        borderRadius: 12,
        backgroundColor: '#111827',
        alignItems: 'center',
    },
    btnText: {
        color: '#fff',
        fontSize: 16,
        fontWeight: '600',
    }
});
