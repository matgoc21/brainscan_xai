import React, {useState} from 'react';
import { StyleSheet, View, Text, TextInput, TouchableOpacity, ActivityIndicator, Alert, Platform, ScrollView} from 'react-native';
import {apiFetch } from '@/services/api';

interface WebUploadModalProps {
    onSuccess: () => void;
    onClose: () => void;
}

export default function WebUploadModal({ onSuccess, onClose }: WebUploadModalProps) {
    const [patientId, setPatientId] = useState('');
    const [firstName, setFirstName] = useState('');
    const [lastName, setLastName] = useState('');
    const [age, setAge] = useState('');
    const [gender, setGender] = useState('');

    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [statusMsg, setStatusMsg] = useState('');

    const handleFileChange = (event: any) => {
        if (event.target.files && event.target.files[0]) {
            setSelectedFile(event.target.files[0]);
        }
    };

    const handleUpload = async () => {
        if (!selectedFile) {
            setStatusMsg('Wybierz plik skanu MRI');
            return;
        }
        if (!patientId.trim()) {
            setStatusMsg('Podanie ID/ PESEL - u pacjenta jest wymagane');
            return;
        }

        setUploading(true);
        setStatusMsg('');

        const formData = new FormData();
        formData.append('patient_identifier', patientId.trim());
        formData.append('first_name', firstName.trim());
        formData.append('last_name', lastName.trim());
        if (age.trim()) formData.append('age', age.trim());
        if (gender.trim()) formData.append('gender', gender.trim());
        formData.append('image', selectedFile);

        try {
            const response = await apiFetch('/api/scans/', {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                onSuccess();
            }else {
                const errorData = await response.json();
                setStatusMsg(JSON.stringify(errorData));
            }

        } catch (error) {
            setStatusMsg('Wystąpił błąd podczas przesyłania pliku.');
        } finally {
            setUploading(false);
        }
    };

    return (
        <View style={styles.overlay}>
            <View style={styles.card}>
                <Text style={styles.header}>Prześlij skan MRI</Text>

                <Text style={styles.label}>ID pacjenta / badania:</Text>
                <TextInput 
                    style={styles.input}
                    placeholder="Wprowadź ID"
                    placeholderTextColor="#7f8c8d"
                    value={patientId}
                    onChangeText={setPatientId}
                />

                <View style={styles.row}>
                    <View style={styles.col}>
                        <Text style={styles.label}>Imię (Opcjonalne):</Text>
                        <TextInput 
                            style={styles.input}
                            placeholder='Jan'
                            placeholderTextColor="#7f8c8d"
                            value={firstName}
                            onChangeText={setFirstName}
                        />
                    

                    </View>
                    <View style={styles.col}>
                        <Text style={styles.label}>Nazwisko (Opcjonalne)</Text>
                        <TextInput
                            style={styles.input}
                            placeholder="Kowalski"
                            placeholderTextColor="#7f8c8d"
                            value={lastName}
                            onChangeText={setLastName}
                        />
                    </View>
                </View>

                <View style={styles.row}>
                    <View style={styles.col}>
                        <Text style={styles.label}>Płeć:</Text>
                        <TextInput
                            style={styles.input}
                            placeholder= "M/K"
                            placeholderTextColor="#7f8c8d"
                            value={gender}
                            onChangeText={setGender}
                        />
                    </View>
                    <View style={styles.col}>

                        <Text style={styles.label}>Wiek:</Text>
                        <TextInput 
                            style={styles.input}
                            placeholder="Np. 45"
                            placeholderTextColor={"#7f8c8d"}
                            keyboardType="numeric"
                            value={age}
                            onChangeText={setAge}
                        />
                    </View>
                </View>
                

                <Text style={styles.label}>Wybierz skan z dysku komputera:</Text>
                {Platform.OS === 'web' && (
                    <View style={styles.filePickerContainer}>
                        {React.createElement('input', {
                                type: 'file',
                                acceept: 'image/*',
                                onChange: handleFileChange,
                                style: {
                                    fontSize: 14,
                                    width: '100%',
                                    padding: '8px 0',
                                    cursor: 'pointer',
                                },
                        })}
                    </View>
                )}

                {statusMsg ? <Text style={styles.errorText}>{statusMsg}</Text>: null}

                <View style={styles.buttonRow}>
                    <TouchableOpacity style={[styles.btn, styles.cancelBtn]} onPress={onClose} disabled={uploading}>
                        <Text style={styles.btnText}>Anuluj</Text>
                    </TouchableOpacity>

                    <TouchableOpacity style={[styles.btn, styles.submitBtn]} onPress={handleUpload} disabled={uploading}>
                        {uploading ? (
                            <ActivityIndicator color= "#fff" />
                        ) : (
                            <Text style={styles.btnText}>Uruchom analizę</Text>
                        )}
                    </TouchableOpacity>
                </View>
            </View>
        </View>
    );
}


const styles = StyleSheet.create({
  overlay: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    zIndex: 1000,
  },
  card: {
    width: '100%',
    maxWidth: 450,
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 20,
  },
  header: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 15,
  },
  label: {
    fontSize: 13,
    color: '#34495e',
    marginBottom: 6,
    fontWeight: '600',
  },
  input: {
    backgroundColor: '#f8f9fa',
    borderWidth: 1,
    borderColor: '#ced6e0',
    borderRadius: 6,
    padding: 10,
    fontSize: 14,
    marginBottom: 15,
  },
  filePickerContainer: {
    marginBottom: 15,
  },
  errorText: {
    color: '#e74c3c',
    fontSize: 13,
    marginBottom: 10,
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 10,
    marginTop: 10,
  },
  btn: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 6,
  },
  cancelBtn: {
    backgroundColor: '#7f8c8d',
  },
  submitBtn: {
    backgroundColor: '#27ae60',
  },
  btnText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  row: {
    flexDirection: 'row',
    gap: 10
  },
  col: {
    flex: 1
  },
  scrollContent: {
    paddingBottom: 10
  },
});