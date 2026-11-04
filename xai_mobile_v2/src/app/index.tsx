// import { useState } from 'react';
// import {StyleSheet, Text, View, Image, TouchableOpacity, ActivityIndicator, ScrollView, Alert, Platform } from 'react-native';
// import * as ImagePicker from 'expo-image-picker';

// const BACKEND_URL = 'http://0.0.0.0:8000/api/analyze/';

// export default function App() {
//   const [imageUri, setImageUri] = useState<string | null>(null);
//   const [loading, setLoading] = useState(false);
//   const [result, setResult] = useState<any>(null);

//   // Funkcja otwierająca galerię w telefonie
//   const pickImage = async () => {
//     const permissionResult = await ImagePicker.requestMediaLibraryPermissionsAsync();
//     if (permissionResult.granted === false) {
//       Alert.alert('Wymagane uprawnienia', 'Aplikacja potrzebuje dostępu do galerii, aby załadować skan MRI.');
//       return;
//     }

//     let pickerResult = await ImagePicker.launchImageLibraryAsync({
//       mediaTypes: ['images'],
//       allowsEditing: true, // Pozwala przyciąć zdjęcie przed wysłaniem
//       aspect: [1, 1],
//       quality: 0.8,
//     });

//     if (!pickerResult.canceled) {
//       setImageUri(pickerResult.assets[0].uri);
//       setResult(null); // Resetujemy wynik przy wyborze nowego pliku
//     }
//   };

//   // Funkcja wysyłająca zdjęcie do Django API
//   const analyzeImage = async () => {
//     if (!imageUri) return;
//     setLoading(true);
//     setResult(null);

//     const formData = new FormData();

//     try {
//       if (Platform.OS === 'web') {
//         const imageResponse = await fetch(imageUri);
//         if (!imageResponse.ok) {
//           throw new Error(`Could not read the selected image (${imageResponse.status}).`);
//         }
//         const imageBlob = await imageResponse.blob();
//         formData.append('image', imageBlob, 'mri_scan.jpg');
//       } else {
//         formData.append('image', {
//           uri: imageUri,
//           name: 'mri_scan.jpg',
//           type: 'image/jpeg',
//         } as any);
//       }

//       const response = await fetch(BACKEND_URL, {
//         method: 'POST',
//         body: formData,
//       });

//       const jsonResponse = await response.json();

//       if (response.ok) {
//         setResult(jsonResponse.data);
//       } else {
//         Alert.alert('Błąd API', JSON.stringify(jsonResponse));
//       }
//     } catch (error) {
//       console.error(error);
//       Alert.alert('Błąd połączenia', 'Nie można połączyć się z serwerem. Czy na pewno wpisałeś poprawne IP Fedory i Docker działa?');
//     } finally {
//       setLoading(false);
//     }
//   };

//   return (
//     <ScrollView contentContainerStyle={styles.container}>
//       <Text style={styles.title}>Diagnostyka XAI</Text>
      
//       {/* Sekcja wyboru zdjęcia */}
//       <View style={styles.imageContainer}>
//         {imageUri ? (
//           <Image source={{ uri: imageUri }} style={styles.image} />
//         ) : (
//           <Text style={styles.placeholderText}>Brak załadowanego skanu MRI</Text>
//         )}
//       </View>

//       <TouchableOpacity style={styles.button} onPress={pickImage}>
//         <Text style={styles.buttonText}>Wybierz zdjęcie z galerii</Text>
//       </TouchableOpacity>

//       <TouchableOpacity 
//         style={[styles.button, styles.analyzeButton, !imageUri && styles.buttonDisabled]} 
//         onPress={analyzeImage}
//         disabled={!imageUri || loading}
//       >
//         <Text style={styles.buttonText}>Analizuj skan (Grad-CAM)</Text>
//       </TouchableOpacity>

      
//       {loading && (
//         <View style={styles.loadingContainer}>
//           <ActivityIndicator size="large" color="#3498db" />
//           <Text style={styles.loadingText}>Przetwarzanie przez sieć CNN...</Text>
//         </View>
//       )}

      
//       {result && (
//         <View style={styles.resultContainer}>
//           <Text style={styles.resultTitle}>Wynik klasyfikacji:</Text>
//           <Text style={styles.resultText}>Klasa: <Text style={styles.highlight}>{result.prediction.toUpperCase()}</Text></Text>
//           <Text style={styles.resultText}>Pewność: <Text style={styles.highlight}>{result.confidence}%</Text></Text>
          
//           <Text style={styles.resultTitle}>Wyjaśnienie modelu (Grad-CAM):</Text>
//           <Image source={{ uri: result.heatmap_base64 }} style={styles.heatmapImage} />
//         </View>
//       )}
//     </ScrollView>
//   );
// }


// const styles = StyleSheet.create({
//   container: { flexGrow: 1, backgroundColor: '#f4f7f6', alignItems: 'center', padding: 20, paddingTop: 60 },
//   title: { fontSize: 24, fontWeight: 'bold', color: '#2c3e50', marginBottom: 20 },
//   imageContainer: { width: 250, height: 250, backgroundColor: '#e1e8ed', justifyContent: 'center', alignItems: 'center', borderRadius: 10, marginBottom: 20, overflow: 'hidden' },
//   image: { width: '100%', height: '100%' },
//   placeholderText: { color: '#7f8c8d', textAlign: 'center', padding: 20 },
//   button: { backgroundColor: '#34495e', padding: 15, borderRadius: 8, width: '100%', alignItems: 'center', marginBottom: 10 },
//   analyzeButton: { backgroundColor: '#27ae60' },
//   buttonDisabled: { backgroundColor: '#95a5a6' },
//   buttonText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
//   loadingContainer: { marginTop: 20, alignItems: 'center' },
//   loadingText: { marginTop: 10, color: '#3498db', fontSize: 16 },
//   resultContainer: { width: '100%', marginTop: 20, backgroundColor: '#fff', padding: 15, borderRadius: 10, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4, elevation: 3 },
//   resultTitle: { fontSize: 18, fontWeight: 'bold', color: '#2c3e50', marginTop: 10, marginBottom: 5 },
//   resultText: { fontSize: 16, color: '#34495e', marginBottom: 5 },
//   highlight: { color: '#e74c3c', fontWeight: 'bold' },
//   heatmapImage: { width: 250, height: 250, alignSelf: 'center', marginTop: 15, borderRadius: 8 },
// });
import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  ActivityIndicator,
  Platform,
  Alert,
} from 'react-native';
import { getAccessToken, clearTokens } from '@/services/storage';
import LoginScreen from '@/components/LoginScreen';
import WebUploadModal from '@/components/WebUploadModal';

export default function HomeScreen() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [showUploadModal, setShowUploadModal] = useState(false);

  const checkAuth = async () => {
    const token = await getAccessToken();
    setIsAuthenticated(!!token);
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const handleLogout = async () => {
    await clearTokens();
    setIsAuthenticated(false);
  };

  if (isAuthenticated === null) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#2980b9" />
      </View>
    );
  }

  if (!isAuthenticated) {
    return <LoginScreen onLoginSuccess={() => setIsAuthenticated(true)} />;
  }

  return (
    <View style={styles.container}>
      <View style={styles.topBar}>
        <Text style={styles.heading}>Panel Badań MRI</Text>
        <View style={styles.topBarButtons}>
          {Platform.OS === 'web' && (
            <TouchableOpacity
              style={styles.addBtn}
              onPress={() => setShowUploadModal(true)}
            >
              <Text style={styles.btnText}>+ Dodaj badanie (Web)</Text>
            </TouchableOpacity>
          )}
          <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
            <Text style={styles.btnText}>Wyloguj</Text>
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.placeholderBox}>
        <Text style={styles.infoText}>
          Jesteś zalogowany. Gotowy do podpięcia listy badań i map Grad-CAM.
        </Text>
      </View>

      {showUploadModal && (
        <WebUploadModal
          onClose={() => setShowUploadModal(false)}
          onSuccess={() => {
            setShowUploadModal(false);
            Alert.alert(
              'Sukces',
              'Skan został przeanalizowany i zapisany w bazie danych.'
            );
          }}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f4f7f6',
  },
  container: {
    flex: 1,
    backgroundColor: '#f4f7f6',
    padding: 20,
    paddingTop: 50,
  },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  heading: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#2c3e50',
  },
  topBarButtons: {
    flexDirection: 'row',
    gap: 10,
  },
  addBtn: {
    backgroundColor: '#27ae60',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
  },
  logoutBtn: {
    backgroundColor: '#e74c3c',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
  },
  btnText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 13,
  },
  placeholderBox: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  infoText: {
    color: '#7f8c8d',
    fontSize: 15,
    textAlign: 'center',
  },
});