import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TextInput, Pressable, ScrollView } from 'react-native';
import { MapPin, Navigation, Car, Bike, AlertCircle } from 'lucide-react-native';

export default function BookingForm({ parsedData, onConfirm, onCancel }) {
    const [destinationA, setDestinationA] = useState(parsedData.from || '');
    const [destinationB, setDestinationB] = useState(parsedData.to || '');
    const [vehicle, setVehicle] = useState(parsedData.vehicle || null);

    // Auto-fill logic
    useEffect(() => {
        const homeKeywords = ['home', 'house', 'my place'];
        const workKeywords = ['work', 'office', 'company'];
        
        let toValue = parsedData.to || '';
        
        if (toValue) {
            const lowerTo = toValue.toLowerCase();
            if (homeKeywords.some(kw => lowerTo.includes(kw))) {
                setDestinationB('123 Home Street, City');
            } else if (workKeywords.some(kw => lowerTo.includes(kw))) {
                setDestinationB('456 Corporate Blvd, City');
            }
        }
    }, [parsedData.to]);

    const isMissingVehicle = !vehicle;
    const isValid = destinationA.trim() !== '' && destinationB.trim() !== '' && vehicle;

    return (
        <ScrollView style={styles.container} contentContainerStyle={styles.content}>
            <Text style={styles.headerTitle}>Validate Details</Text>
            <Text style={styles.headerSubtitle}>Please review and confirm your ride information.</Text>

            <View style={styles.inputGroup}>
                <View style={styles.labelContainer}>
                    <MapPin color="#6b7280" size={16} />
                    <Text style={styles.label}>Pickup Location</Text>
                </View>
                <TextInput 
                    style={styles.input}
                    value={destinationA}
                    onChangeText={setDestinationA}
                    placeholder="Enter pickup location"
                    placeholderTextColor="#9ca3af"
                />
            </View>

            <View style={styles.inputGroup}>
                <View style={styles.labelContainer}>
                    <Navigation color="#6b7280" size={16} />
                    <Text style={styles.label}>Drop-off Location</Text>
                </View>
                <TextInput 
                    style={styles.input}
                    value={destinationB}
                    onChangeText={setDestinationB}
                    placeholder="Enter drop-off destination"
                    placeholderTextColor="#9ca3af"
                />
            </View>

            <View style={styles.vehicleSection}>
                <Text style={styles.label}>Vehicle Type</Text>
                
                {isMissingVehicle && (
                    <View style={styles.warningBox}>
                        <AlertCircle color="#d97706" size={18} />
                        <Text style={styles.warningText}>Please select a vehicle type to continue.</Text>
                    </View>
                )}

                <View style={styles.cardsRow}>
                    <Pressable 
                        style={[styles.vehicleCard, vehicle === 'car' && styles.vehicleCardSelected]}
                        onPress={() => setVehicle('car')}
                    >
                        <Car color={vehicle === 'car' ? '#2563eb' : '#6b7280'} size={32} />
                        <Text style={[styles.vehicleText, vehicle === 'car' && styles.vehicleTextSelected]}>Car</Text>
                    </Pressable>

                    <Pressable 
                        style={[styles.vehicleCard, vehicle === 'bike' && styles.vehicleCardSelected]}
                        onPress={() => setVehicle('bike')}
                    >
                        <Bike color={vehicle === 'bike' ? '#2563eb' : '#6b7280'} size={32} />
                        <Text style={[styles.vehicleText, vehicle === 'bike' && styles.vehicleTextSelected]}>Bike</Text>
                    </Pressable>
                </View>
            </View>

            <View style={styles.actions}>
                <Pressable style={styles.cancelBtn} onPress={onCancel}>
                    <Text style={styles.cancelBtnText}>Discard</Text>
                </Pressable>
                
                <Pressable 
                    style={[styles.confirmBtn, !isValid && styles.confirmBtnDisabled]} 
                    disabled={!isValid}
                    onPress={() => onConfirm({ from: destinationA, to: destinationB, vehicle })}
                >
                    <Text style={styles.confirmBtnText}>Confirm Booking</Text>
                </Pressable>
            </View>
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        width: '100%',
    },
    content: {
        paddingHorizontal: 24,
        paddingBottom: 40,
    },
    headerTitle: {
        fontSize: 28,
        fontWeight: 'bold',
        color: '#111827',
        marginTop: 10,
        marginBottom: 8,
    },
    headerSubtitle: {
        fontSize: 16,
        color: '#6b7280',
        marginBottom: 32,
    },
    inputGroup: {
        marginBottom: 20,
    },
    labelContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 8,
        gap: 6,
    },
    label: {
        fontSize: 14,
        fontWeight: '600',
        color: '#374151',
    },
    input: {
        backgroundColor: '#f3f4f6',
        borderRadius: 12,
        paddingHorizontal: 16,
        paddingVertical: 14,
        fontSize: 16,
        color: '#1f2937',
        borderWidth: 1,
        borderColor: '#e5e7eb',
    },
    vehicleSection: {
        marginTop: 10,
        marginBottom: 30,
    },
    warningBox: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#fef3c7',
        padding: 12,
        borderRadius: 8,
        marginTop: 10,
        gap: 8,
    },
    warningText: {
        color: '#92400e',
        fontSize: 14,
        fontWeight: '500',
    },
    cardsRow: {
        flexDirection: 'row',
        gap: 16,
        marginTop: 16,
    },
    vehicleCard: {
        flex: 1,
        backgroundColor: '#fff',
        borderWidth: 2,
        borderColor: '#e5e7eb',
        borderRadius: 16,
        paddingVertical: 20,
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
    },
    vehicleCardSelected: {
        borderColor: '#2563eb',
        backgroundColor: '#eff6ff',
    },
    vehicleText: {
        fontSize: 16,
        fontWeight: '600',
        color: '#6b7280',
    },
    vehicleTextSelected: {
        color: '#2563eb',
    },
    actions: {
        flexDirection: 'row',
        gap: 12,
        marginTop: 10,
    },
    cancelBtn: {
        flex: 1,
        paddingVertical: 16,
        borderRadius: 12,
        backgroundColor: '#f3f4f6',
        alignItems: 'center',
    },
    cancelBtnText: {
        color: '#4b5563',
        fontSize: 16,
        fontWeight: '600',
    },
    confirmBtn: {
        flex: 2,
        paddingVertical: 16,
        borderRadius: 12,
        backgroundColor: '#111827',
        alignItems: 'center',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.2,
        shadowRadius: 8,
        elevation: 6,
    },
    confirmBtnDisabled: {
        backgroundColor: '#9ca3af',
        shadowOpacity: 0,
        elevation: 0,
    },
    confirmBtnText: {
        color: '#fff',
        fontSize: 16,
        fontWeight: '600',
    }
});
