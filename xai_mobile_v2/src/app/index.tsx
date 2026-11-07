import React, { useState, useEffect, useCallback } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  ActivityIndicator,
  Platform,
  Alert,
  FlatList,
  Image,
  TextInput,
} from 'react-native';
import { getAccessToken, clearTokens } from '@/services/storage';
import { apiFetch, BASE_URL } from '@/services/api';
import LoginScreen from '@/components/LoginScreen';
import WebUploadModal from '@/components/WebUploadModal';
import ScanDetailModal, {ScanItem} from '@/components/ScanDetailModal';

const FILTERS = [
  {key: '', label: 'Wszystkie'},
  {key: 'glioma', label: 'Glejak'},
  {key: 'meningioma', label: 'Oponiak'},
  {key: 'pituitary', label: 'Guz przysadki'},
  {key: 'notumor', label: 'Brak guza'},
];

export default function HomeScreen() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [scans, setScans] = useState<ScanItem[]>([]);
  const [loadingScans, setLoadingScans] = useState(false);
  const [selectedFilter, setSelectedFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedScan, setSelectedScan] = useState<ScanItem | null>(null);

  const fetchScans = useCallback(async () => {
    setLoadingScans(true);
    try {
      const params = new URLSearchParams();
      if (selectedFilter) params.append('class', selectedFilter);
      if (searchQuery.trim()) params.append('search', searchQuery.trim());

      const queryString = params.toString() ? `?${params.toString()}` : '';
      const response = await apiFetch(`/api/scans/${queryString}`);

      if (response.ok) {
        const data = await response.json();
        setScans(data);
      } else if (response.status === 401) {
        setIsAuthenticated(false);
      }
    } catch (error) {
      console.error('Błąd pobierania listy badań: ', error);
    } finally {
      setLoadingScans(false);
    }
  }, [selectedFilter, searchQuery]);


  useEffect(() => {
    const checkAuth = async () => {
    const token = await getAccessToken();
    setIsAuthenticated(!!token);
  };
  checkAuth();
  }, [])

  useEffect(() => {
    if (isAuthenticated) {
      fetchScans();
    }
  }, [isAuthenticated, fetchScans]);
  

  const handleLogout = async () => {
    await clearTokens();
    setIsAuthenticated(false);
    setScans([]);
  };

  const getImageUrl = (url: string | null) => {
    if  (!url) return '';
    if (url.startsWith('http')) return url;
    return `${BASE_URL}${url}`;
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
      {/* Pasek górny */}
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
          <TouchableOpacity style={styles.refreshBtn} onPress={fetchScans}>
            <Text style={styles.btnText}>Odśwież</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
            <Text style={styles.btnText}>Wyloguj</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Wyszukiwarka i filtry klas */}
      <View style={styles.controlsContainer}>
        <TextInput
          style={styles.searchInput}
          placeholder="Szukaj po ID pacjenta..."
          placeholderTextColor="#7f8c8d"
          value={searchQuery}
          onChangeText={setSearchQuery}
        />

        <View style={styles.filterRow}>
          {FILTERS.map((f) => (
            <TouchableOpacity
              key={f.key}
              style={[
                styles.filterChip,
                selectedFilter === f.key && styles.filterChipActive,
              ]}
              onPress={() => setSelectedFilter(f.key)}
            >
              <Text
                style={[
                  styles.filterChipText,
                  selectedFilter === f.key && styles.filterChipTextActive,
                ]}
              >
                {f.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Lista badań */}
      {loadingScans ? (
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color="#2980b9" />
        </View>
      ) : scans.length === 0 ? (
        <View style={styles.centerContainer}>
          <Text style={styles.infoText}>
            Brak zapisanych badań spełniających kryteria.
          </Text>
        </View>
      ) : (
        <FlatList
          data={scans}
          keyExtractor={(item) => item.id.toString()}
          contentContainerStyle={styles.listContent}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={styles.scanCard}
              onPress={() => setSelectedScan(item)}
            >
              <Image
                source={{ uri: getImageUrl(item.heatmap_image || item.original_image) }}
                style={styles.thumbnail}
              />
              <View style={styles.cardInfo}>
                <Text style={styles.patientId}>{item.patient_id}</Text>
                <Text style={styles.predictionText}>
                  Klasa: <Text style={styles.bold}>{item.predicted_class.toUpperCase()}</Text> ({item.confidence_percent}%)
                </Text>
                <Text style={styles.dateSmall}>
                  {new Date(item.created_at).toLocaleString('pl-PL')}
                </Text>
              </View>
              <Text style={styles.chevron}>›</Text>
            </TouchableOpacity>
          )}
        />
      )}

      {/* Modal dodawania badania (Web) */}
      {showUploadModal && (
        <WebUploadModal
          onClose={() => setShowUploadModal(false)}
          onSuccess={() => {
            setShowUploadModal(false);
            fetchScans(); // Automatyczne odświeżenie listy po analizie!
          }}
        />
      )}

      {/* Modal szczegółów badania i XAI */}
      {selectedScan && (
        <ScanDetailModal
          scan={selectedScan}
          onClose={() => setSelectedScan(null)}
          onDeleted={(deletedId) => {
            setSelectedScan(null);
            setScans((prev) => prev.filter((s) => s.id !== deletedId));
          }}
        />
      )}
    </View>
  );
}

//   return (
//     <View style={styles.container}>
//       <View style={styles.topBar}>
//         <Text style={styles.heading}>Panel Badań MRI</Text>
//         <View style={styles.topBarButtons}>
//           {Platform.OS === 'web' && (
//             <TouchableOpacity
//               style={styles.addBtn}
//               onPress={() => setShowUploadModal(true)}
//             >
//               <Text style={styles.btnText}>+ Dodaj badanie (Web)</Text>
//             </TouchableOpacity>
//           )}
//           <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
//             <Text style={styles.btnText}>Wyloguj</Text>
//           </TouchableOpacity>
//         </View>
//       </View>

//       <View style={styles.placeholderBox}>
//         <Text style={styles.infoText}>
//           Jesteś zalogowany. Gotowy do podpięcia listy badań i map Grad-CAM.
//         </Text>
//       </View>

//       {showUploadModal && (
//         <WebUploadModal
//           onClose={() => setShowUploadModal(false)}
//           onSuccess={() => {
//             setShowUploadModal(false);
//             Alert.alert(
//               'Sukces',
//               'Skan został przeanalizowany i zapisany w bazie danych.'
//             );
//           }}
//         />
//       )}
//     </View>
//   );
// }
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
    paddingTop: 40,
  },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
    flexWrap: 'wrap',
    gap: 10,
  },
  heading: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#2c3e50',
  },
  topBarButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  addBtn: {
    backgroundColor: '#27ae60',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
  },
  refreshBtn: {
    backgroundColor: '#2980b9',
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
  controlsContainer: {
    marginBottom: 14,
  },
  searchInput: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#dcdde1',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 9,
    fontSize: 14,
    marginBottom: 10,
    color: '#2c3e50',
  },
  filterRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  filterChip: {
    backgroundColor: '#e1e8ed',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 16,
  },
  filterChipActive: {
    backgroundColor: '#2c3e50',
  },
  filterChipText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#2c3e50',
  },
  filterChipTextActive: {
    color: '#fff',
  },
  listContent: {
    paddingBottom: 30,
  },
  scanCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: 12,
    borderRadius: 10,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 3,
    elevation: 2,
  },
  thumbnail: {
    width: 64,
    height: 64,
    borderRadius: 8,
    backgroundColor: '#000',
    marginRight: 14,
  },
  cardInfo: {
    flex: 1,
  },
  patientId: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 3,
  },
  predictionText: {
    fontSize: 13,
    color: '#34495e',
    marginBottom: 3,
  },
  bold: {
    fontWeight: 'bold',
    color: '#2980b9',
  },
  dateSmall: {
    fontSize: 11,
    color: '#95a5a6',
  },
  chevron: {
    fontSize: 24,
    color: '#bdc3c7',
    paddingHorizontal: 8,
  },
  infoText: {
    color: '#7f8c8d',
    fontSize: 15,
    textAlign: 'center',
  },
});

