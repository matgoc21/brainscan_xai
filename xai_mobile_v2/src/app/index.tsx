import { useState } from 'react';
import {StyleSheet, Text, View, Image, TouchableOpacity, ActivityIndicator, ScrollView, Alert, Platform } from 'react-native';
import * as ImagePicker from 'expo-image-picker';

const BACKEND_URL = 'http://10.167.130.182:8000/api/analyze/';

export default function App() {
  const [imageUri, setImageUri] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  // Funkcja otwierająca galerię w telefonie
  const pickImage = async () => {
    const permissionResult = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (permissionResult.granted === false) {
      Alert.alert('Wymagane uprawnienia', 'Aplikacja potrzebuje dostępu do galerii, aby załadować skan MRI.');
      return;
    }

    let pickerResult = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      allowsEditing: true, // Pozwala przyciąć zdjęcie przed wysłaniem
      aspect: [1, 1],
      quality: 0.8,
    });

    if (!pickerResult.canceled) {
      setImageUri(pickerResult.assets[0].uri);
      setResult(null); // Resetujemy wynik przy wyborze nowego pliku
    }
  };

  // Funkcja wysyłająca zdjęcie do naszego Django API
  const analyzeImage = async () => {
    if (!imageUri) return;
    setLoading(true);
    setResult(null);

    const formData = new FormData();

    try {
      if (Platform.OS === 'web') {
        const imageResponse = await fetch(imageUri);
        if (!imageResponse.ok) {
          throw new Error(`Could not read the selected image (${imageResponse.status}).`);
        }
        const imageBlob = await imageResponse.blob();
        formData.append('image', imageBlob, 'mri_scan.jpg');
      } else {
        formData.append('image', {
          uri: imageUri,
          name: 'mri_scan.jpg',
          type: 'image/jpeg',
        } as any);
      }

      const response = await fetch(BACKEND_URL, {
        method: 'POST',
        body: formData,
      });

      const jsonResponse = await response.json();

      if (response.ok) {
        setResult(jsonResponse.data);
      } else {
        Alert.alert('Błąd API', JSON.stringify(jsonResponse));
      }
    } catch (error) {
      console.error(error);
      Alert.alert('Błąd połączenia', 'Nie można połączyć się z serwerem. Czy na pewno wpisałeś poprawne IP Fedory i Docker działa?');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Diagnostyka XAI</Text>
      
      {/* Sekcja wyboru zdjęcia */}
      <View style={styles.imageContainer}>
        {imageUri ? (
          <Image source={{ uri: imageUri }} style={styles.image} />
        ) : (
          <Text style={styles.placeholderText}>Brak załadowanego skanu MRI</Text>
        )}
      </View>

      <TouchableOpacity style={styles.button} onPress={pickImage}>
        <Text style={styles.buttonText}>Wybierz zdjęcie z galerii</Text>
      </TouchableOpacity>

      <TouchableOpacity 
        style={[styles.button, styles.analyzeButton, !imageUri && styles.buttonDisabled]} 
        onPress={analyzeImage}
        disabled={!imageUri || loading}
      >
        <Text style={styles.buttonText}>Analizuj skan (Grad-CAM)</Text>
      </TouchableOpacity>

      {/* Ekran ładowania */}
      {loading && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#3498db" />
          <Text style={styles.loadingText}>Przetwarzanie przez sieć CNN...</Text>
        </View>
      )}

      {/* Sekcja wyników */}
      {result && (
        <View style={styles.resultContainer}>
          <Text style={styles.resultTitle}>Wynik klasyfikacji:</Text>
          <Text style={styles.resultText}>Klasa: <Text style={styles.highlight}>{result.prediction.toUpperCase()}</Text></Text>
          <Text style={styles.resultText}>Pewność: <Text style={styles.highlight}>{result.confidence}%</Text></Text>
          
          <Text style={styles.resultTitle}>Wyjaśnienie modelu (Grad-CAM):</Text>
          <Image source={{ uri: result.heatmap_base64 }} style={styles.heatmapImage} />
        </View>
      )}
    </ScrollView>
  );
}

// Podstawowe style aplikacji
const styles = StyleSheet.create({
  container: { flexGrow: 1, backgroundColor: '#f4f7f6', alignItems: 'center', padding: 20, paddingTop: 60 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#2c3e50', marginBottom: 20 },
  imageContainer: { width: 250, height: 250, backgroundColor: '#e1e8ed', justifyContent: 'center', alignItems: 'center', borderRadius: 10, marginBottom: 20, overflow: 'hidden' },
  image: { width: '100%', height: '100%' },
  placeholderText: { color: '#7f8c8d', textAlign: 'center', padding: 20 },
  button: { backgroundColor: '#34495e', padding: 15, borderRadius: 8, width: '100%', alignItems: 'center', marginBottom: 10 },
  analyzeButton: { backgroundColor: '#27ae60' },
  buttonDisabled: { backgroundColor: '#95a5a6' },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  loadingContainer: { marginTop: 20, alignItems: 'center' },
  loadingText: { marginTop: 10, color: '#3498db', fontSize: 16 },
  resultContainer: { width: '100%', marginTop: 20, backgroundColor: '#fff', padding: 15, borderRadius: 10, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4, elevation: 3 },
  resultTitle: { fontSize: 18, fontWeight: 'bold', color: '#2c3e50', marginTop: 10, marginBottom: 5 },
  resultText: { fontSize: 16, color: '#34495e', marginBottom: 5 },
  highlight: { color: '#e74c3c', fontWeight: 'bold' },
  heatmapImage: { width: 250, height: 250, alignSelf: 'center', marginTop: 15, borderRadius: 8 },
});
