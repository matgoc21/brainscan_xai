import React, {useState, useEffect} from 'react';
import { StyleSheet, View, Text, TextInput, TouchableOpacity, ActivityIndicator, Alert, Platform, ScrollView} from 'react-native';
import {apiFetch } from '@/services/api';

interface WebUploadModalProps {
    onSuccess: () => void;
    onClose: () => void;
}
interface PatientData {
  id: number;
  identifier: string;
  first_name: string;
  last_name: string;
  age: number | null;
  gender: string;
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
    const [patients, setPatients] = useState<PatientData[]>([]);
    const [filteredPatients, setFilteredPatients] = useState<PatientData[]>([]);
    const [showSuggestions, setShowSuggestions] = useState(false);

    useEffect(() => {
        // Pobranie listy pacjentów przy otwarciu modala
        const loadPatients = async () => {
        try {
            const response = await apiFetch('/api/patients/');
            if (response.ok) {
            const data = await response.json();
            setPatients(data);
            }
        } catch (error) {
            console.error('Błąd pobierania pacjentów:', error);
        }
        };
        loadPatients();
    }, []);

    const handlePatientIdChange = (text: string) => {
        setPatientId(text);
        // Filtrowanie listy pacjentów po wpisanym tekście
        if (text.length > 0) {
        const matches = patients.filter(p => 
            p.identifier.toLowerCase().includes(text.toLowerCase()) ||
            p.last_name.toLowerCase().includes(text.toLowerCase())
        );
        setFilteredPatients(matches);
        setShowSuggestions(true);
        } else {
        setShowSuggestions(false);
        }
    };

    const handleSelectPatient = (patient: PatientData) => {
        setPatientId(patient.identifier);
        setFirstName(patient.first_name);
        setLastName(patient.last_name);
        setAge(patient.age ? patient.age.toString() : '');
        setGender(patient.gender || '');
        setShowSuggestions(false); // Ukryj listę po wyborze
    };

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
                setStatusMsg(errorData.error || errorData.detail|| 'Błąd walidacji danych.');
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
        <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
          <Text style={styles.header}>Prześlij skan MRI</Text>

          <View style={styles.autocompleteContainer}>
            <Text style={styles.label}>ID pacjenta / PESEL (wymagane):</Text>
            <TextInput
              style={styles.input}
              placeholder="Wprowadź ID lub wyszukaj"
              placeholderTextColor="#7f8c8d"
              value={patientId}
              onChangeText={handlePatientIdChange}
              onFocus={() => { if (patientId) setShowSuggestions(true); }}
            />
            {/* Lista podpowiedzi */}
            {showSuggestions && filteredPatients.length > 0 && (
              <View style={styles.suggestionsList}>
                {filteredPatients.map(p => (
                  <TouchableOpacity 
                    key={p.id} 
                    style={styles.suggestionItem}
                    onPress={() => handleSelectPatient(p)}
                  >
                    <Text style={styles.suggestionId}>{p.identifier}</Text>
                    {(p.first_name || p.last_name) && (
                      <Text style={styles.suggestionName}> - {p.first_name} {p.last_name}</Text>
                    )}
                  </TouchableOpacity>
                ))}
              </View>
            )}
          </View>

          <View style={styles.row}>
            <View style={styles.col}>
              <Text style={styles.label}>Imię (opcjonalnie):</Text>
              <TextInput style={styles.input} placeholder="Jan" value={firstName} onChangeText={setFirstName} />
            </View>
            <View style={styles.col}>
              <Text style={styles.label}>Nazwisko (opcjonalnie):</Text>
              <TextInput style={styles.input} placeholder="Kowalski" value={lastName} onChangeText={setLastName} />
            </View>
          </View>

          <View style={styles.row}>
            <View style={styles.col}>
              <Text style={styles.label}>Wiek:</Text>
              <TextInput
                style={styles.input}
                placeholder="Np. 45"
                keyboardType="numeric"
                value={age}
                onChangeText={(text) => setAge(text.replace(/[^0-9]/g, ''))}
              />
            </View>
            <View style={styles.col}>
              <Text style={styles.label}>Płeć:</Text>
              <View style={styles.genderRow}>
                <TouchableOpacity 
                  style={[styles.genderBtn, gender === 'M' && styles.genderBtnActive]} 
                  onPress={() => setGender(gender === 'M' ? '' : 'M')}
                >
                  <Text style={[styles.genderText, gender === 'M' && styles.genderTextActive]}>Mężczyzna</Text>
                </TouchableOpacity>
                <TouchableOpacity 
                  style={[styles.genderBtn, gender === 'K' && styles.genderBtnActive]} 
                  onPress={() => setGender(gender === 'K' ? '' : 'K')}
                >
                  <Text style={[styles.genderText, gender === 'K' && styles.genderTextActive]}>Kobieta</Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>

          <Text style={styles.label}>Wybierz skan z dysku komputera:</Text>
          {Platform.OS === 'web' && (
            <View style={styles.filePickerContainer}>
              {React.createElement('input', {
                type: 'file',
                accept: 'image/jpeg, image/png, image/jpg',
                onChange: handleFileChange,
                style: { fontSize: 14, width: '100%', padding: '8px 0', cursor: 'pointer' },
              })}
            </View>
          )}

          {statusMsg ? <Text style={styles.errorText}>{statusMsg}</Text> : null}

          <View style={styles.buttonRow}>
            <TouchableOpacity style={[styles.btn, styles.cancelBtn]} onPress={onClose} disabled={uploading}>
              <Text style={styles.btnText}>Anuluj</Text>
            </TouchableOpacity>

            <TouchableOpacity style={[styles.btn, styles.submitBtn]} onPress={handleUpload} disabled={uploading}>
              {uploading ? <ActivityIndicator color="#fff" /> : <Text style={styles.btnText}>Uruchom analizę</Text>}
            </TouchableOpacity>
          </View>
        </ScrollView>
      </View>
    </View>
  );
}

//     return (
//         <View style={styles.overlay}>
//             <View style={styles.card}>
//                 <Text style={styles.header}>Prześlij skan MRI</Text>

//                 <Text style={styles.label}>ID pacjenta / badania:</Text>
//                 <TextInput 
//                     style={styles.input}
//                     placeholder="Wprowadź ID"
//                     placeholderTextColor="#7f8c8d"
//                     value={patientId}
//                     onChangeText={setPatientId}
//                 />

//                 <View style={styles.row}>
//                     <View style={styles.col}>
//                         <Text style={styles.label}>Imię (Opcjonalne):</Text>
//                         <TextInput 
//                             style={styles.input}
//                             placeholder='Jan'
//                             placeholderTextColor="#7f8c8d"
//                             value={firstName}
//                             onChangeText={setFirstName}
//                         />
                    

//                     </View>
//                     <View style={styles.col}>
//                         <Text style={styles.label}>Nazwisko (Opcjonalne)</Text>
//                         <TextInput
//                             style={styles.input}
//                             placeholder="Kowalski"
//                             placeholderTextColor="#7f8c8d"
//                             value={lastName}
//                             onChangeText={setLastName}
//                         />
//                     </View>
//                 </View>

//                 <View style={styles.row}>
//                     <View style={styles.col}>
//                         <Text style={styles.label}>Płeć:</Text>
//                         <TextInput
//                             style={styles.input}
//                             placeholder= "M/K"
//                             placeholderTextColor="#7f8c8d"
//                             value={gender}
//                             onChangeText={setGender}
//                         />
//                     </View>
//                     <View style={styles.col}>

//                         <Text style={styles.label}>Wiek:</Text>
//                         <TextInput 
//                             style={styles.input}
//                             placeholder="Np. 45"
//                             placeholderTextColor={"#7f8c8d"}
//                             keyboardType="numeric"
//                             value={age}
//                             onChangeText={(text) => setAge(text.replace(/[^0-9]/g, ''))}
//                         />
//                     </View>
//                 </View>
                

//                 <Text style={styles.label}>Wybierz skan z dysku komputera:</Text>
//                 {Platform.OS === 'web' && (
//                     <View style={styles.filePickerContainer}>
//                         {React.createElement('input', {
//                                 type: 'file',
//                                 acceept: 'image/*',
//                                 onChange: handleFileChange,
//                                 style: {
//                                     fontSize: 14,
//                                     width: '100%',
//                                     padding: '8px 0',
//                                     cursor: 'pointer',
//                                 },
//                         })}
//                     </View>
//                 )}

//                 {statusMsg ? <Text style={styles.errorText}>{statusMsg}</Text>: null}

//                 <View style={styles.buttonRow}>
//                     <TouchableOpacity style={[styles.btn, styles.cancelBtn]} onPress={onClose} disabled={uploading}>
//                         <Text style={styles.btnText}>Anuluj</Text>
//                     </TouchableOpacity>

//                     <TouchableOpacity style={[styles.btn, styles.submitBtn]} onPress={handleUpload} disabled={uploading}>
//                         {uploading ? (
//                             <ActivityIndicator color= "#fff" />
//                         ) : (
//                             <Text style={styles.btnText}>Uruchom analizę</Text>
//                         )}
//                     </TouchableOpacity>
//                 </View>
//             </View>
//         </View>
//     );
// }


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
  autocompleteContainer: { 
    position: 'relative',
    zIndex: 10 
  },
  suggestionsList: { 
    backgroundColor: '#fff',
    borderWidth: 1, 
    borderColor: '#ced6e0', 
    borderRadius: 6, 
    maxHeight: 150, 
    marginBottom: 15, 
    marginTop: -10, 
    elevation: 3, 
    shadowColor: '#000', 
    shadowOffset: { width: 0, height: 2 }, 
    shadowOpacity: 0.1,
    shadowRadius: 4 
  },
  suggestionItem: { 
    flexDirection: 'row', 
    padding: 12, 
    borderBottomWidth: 1, 
    borderBottomColor: '#f1f2f6' 
  },
  suggestionId: { 
    fontWeight: 'bold', 
    color: '#2c3e50' 
  },
  suggestionName: { 
    color: '#7f8c8d' 
  },
  genderRow: { 
    flexDirection: 'row', 
    gap: 8, 
    height: 42, 
    marginBottom: 15 
  },
  genderBtn: { 
    flex: 1, 
    justifyContent: 'center', 
    alignItems: 'center', 
    backgroundColor: '#f1f2f6', 
    borderRadius: 6, 
    borderWidth: 1, 
    borderColor: '#ced6e0' 
  },
  genderBtnActive: { 
    backgroundColor: '#3498db', 
    borderColor: '#2980b9' 
  },
  genderText: { 
    fontSize: 13, 
    color: '#7f8c8d', 
    fontWeight: '600'
  },
  genderTextActive: { 
    color: '#fff'
  },

});