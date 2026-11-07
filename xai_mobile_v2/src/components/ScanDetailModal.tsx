import React, {useState} from 'react';
import { StyleSheet, View, Text, Image, TouchableOpacity, ScrollView, Platform} from 'react-native';
import { BASE_URL, apiFetch } from '@/services/api';

export interface ScanItem {
    id: number;
    patient_id: string;
    original_image: string;
    heatmap_image: string;
    predicted_class: string;
    confidence: number;
    created_at: string;
}

interface ScanDetailModalProps {
    scan: ScanItem;
    onClose: () => void;
    onDeleted: (id: number) => void;
}

const CLASS_LABELS: Record<string, string> = {
    glioma: 'Glejak (Glioma)',
    meningioma: 'Oponiak (Meningioma)',
    notumor: 'Brak guza',
    pituitary: 'Guz przysadki (Pituitary)',
};

export default function ScanDetailModal({scan, onClose, onDeleted}: ScanDetailModalProps) {
    const [viewMode, setViewMode] = useState<'overlay' | 'original' | 'heatmap'>('overlay');
    const [opacity, setOpacity] = useState<number>(0.6);
    const [deleting, setDeleting] = useState(false);

    const getImageUrl = (url: string | null) => {
        if (!url) return '';
        if (url.startsWith('http')) return url;

        return `${BASE_URL}${url}`
    };

    const handleDelete = async () => {
        const confirmDelete =
        Platform.OS === 'web' ? window.confirm(`Czy na pewno chcesz usunąć badanie pacjenta ${scan.patient_id}?`) : true;

        if (!confirmDelete) return;

        setDeleting(true);
        try {
            const response = await apiFetch(`/api/scans/${scan.id}/`, {
                method: 'DELETE',
        });
        if (response.ok) {
            onDeleted(scan.id);
        }
        } catch (error) {
            console.error('Błąd usuwania badania: ', error);
        } finally {
            setDeleting(false);
        }
    };

    return (
        <View style={styles.overlay}>
            <View style={styles.card}>
                <ScrollView contentContainerStyle={styles.scrollContent}>
                <View style={styles.headerRow}>
                    <Text style={styles.title}>Pacjent: {scan.patient_id}</Text>
                    <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
                    <Text style={styles.closeBtnText}>✕ Zamknij</Text>
                    </TouchableOpacity>
                </View>

                <Text style={styles.dateText}>
                    Data badania: {new Date(scan.created_at).toLocaleString('pl-PL')}
                </Text>

                {/* Karta z wynikiem diagnozy */}
                <View style={styles.diagnosisBox}>
                    <View>
                    <Text style={styles.diagLabel}>Rozpoznanie modelu:</Text>
                    <Text style={styles.diagValue}>
                        {CLASS_LABELS[scan.predicted_class] || scan.predicted_class.toUpperCase()}
                    </Text>
                    </View>
                    <View style={styles.confidenceBadge}>
                    <Text style={styles.confLabel}>Pewność</Text>
                    <Text style={styles.confValue}>{scan.confidence}%</Text>
                    </View>
                </View>

                {/* Obszar wizualizacji skanu i mapy ciepła */}
                <View style={styles.imageWrapper}>
                    <Image
                    source={{ uri: getImageUrl(scan.original_image) }}
                    style={styles.scanImage}
                    resizeMode="contain"
                    />
                    {scan.heatmap_image && viewMode !== 'original' && (
                    <Image
                        source={{ uri: getImageUrl(scan.heatmap_image) }}
                        style={[
                        styles.scanImage,
                        styles.heatmapOverlay,
                        { opacity: viewMode === 'heatmap' ? 1 : opacity },
                        ]}
                        resizeMode="contain"
                    />
                    )}
                </View>

                {/* Przełącznik trybu widoku */}
                <Text style={styles.sectionLabel}>Tryb wizualizacji XAI (Layer Grad-CAM):</Text>
                <View style={styles.modeRow}>
                    <TouchableOpacity
                    style={[styles.modeBtn, viewMode === 'original' && styles.modeBtnActive]}
                    onPress={() => setViewMode('original')}
                    >
                    <Text style={[styles.modeBtnText, viewMode === 'original' && styles.modeBtnTextActive]}>
                        Oryginał MRI
                    </Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                    style={[styles.modeBtn, viewMode === 'overlay' && styles.modeBtnActive]}
                    onPress={() => setViewMode('overlay')}
                    >
                    <Text style={[styles.modeBtnText, viewMode === 'overlay' && styles.modeBtnTextActive]}>
                        Przenikanie
                    </Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                    style={[styles.modeBtn, viewMode === 'heatmap' && styles.modeBtnActive]}
                    onPress={() => setViewMode('heatmap')}
                    >
                    <Text style={[styles.modeBtnText, viewMode === 'heatmap' && styles.modeBtnTextActive]}>
                        Pełny Grad-CAM
                    </Text>
                    </TouchableOpacity>
                </View>

                {/* Sterowanie intensywnością nakładki w trybie Przenikania */}
                {viewMode === 'overlay' && (
                    <View style={styles.opacityContainer}>
                    <Text style={styles.opacityLabel}>
                        Intensywność warstwy Grad-CAM: {Math.round(opacity * 100)}%
                    </Text>
                    <View style={styles.opacityButtons}>
                        {[0.25, 0.5, 0.75, 1.0].map((val) => (
                        <TouchableOpacity
                            key={val}
                            style={[styles.opBtn, opacity === val && styles.opBtnActive]}
                            onPress={() => setOpacity(val)}
                        >
                            <Text style={[styles.opBtnText, opacity === val && styles.opBtnTextActive]}>
                            {val * 100}%
                            </Text>
                        </TouchableOpacity>
                        ))}
                    </View>
                    </View>
                )}

                {/* Przycisk usunięcia badania */}
                <TouchableOpacity
                    style={styles.deleteBtn}
                    onPress={handleDelete}
                    disabled={deleting}
                >
                    <Text style={styles.deleteBtnText}>
                    {deleting ? 'Usuwanie...' : 'Usuń badanie z bazy'}
                    </Text>
                </TouchableOpacity>
                </ScrollView>
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
    backgroundColor: 'rgba(0,0,0,0.65)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 16,
    zIndex: 1000,
  },
  card: {
    width: '100%',
    maxWidth: 520,
    maxHeight: '92%',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
  },
  scrollContent: {
    paddingBottom: 10,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#2c3e50',
  },
  closeBtn: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    backgroundColor: '#ecf0f1',
    borderRadius: 6,
  },
  closeBtnText: {
    color: '#2c3e50',
    fontWeight: 'bold',
    fontSize: 13,
  },
  dateText: {
    fontSize: 12,
    color: '#7f8c8d',
    marginBottom: 14,
  },
  diagnosisBox: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
    padding: 14,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#2980b9',
    marginBottom: 16,
  },
  diagLabel: {
    fontSize: 12,
    color: '#7f8c8d',
  },
  diagValue: {
    fontSize: 17,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginTop: 2,
  },
  confidenceBadge: {
    alignItems: 'flex-end',
  },
  confLabel: {
    fontSize: 11,
    color: '#7f8c8d',
  },
  confValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#27ae60',
  },
  imageWrapper: {
    width: 280,
    height: 280,
    alignSelf: 'center',
    backgroundColor: '#000',
    borderRadius: 10,
    overflow: 'hidden',
    marginBottom: 16,
    position: 'relative',
  },
  scanImage: {
    width: '100%',
    height: '100%',
  },
  heatmapOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
  },
  sectionLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#34495e',
    marginBottom: 8,
  },
  modeRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 14,
  },
  modeBtn: {
    flex: 1,
    paddingVertical: 9,
    borderRadius: 6,
    backgroundColor: '#ecf0f1',
    alignItems: 'center',
  },
  modeBtnActive: {
    backgroundColor: '#2980b9',
  },
  modeBtnText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#2c3e50',
  },
  modeBtnTextActive: {
    color: '#fff',
  },
  opacityContainer: {
    marginBottom: 16,
  },
  opacityLabel: {
    fontSize: 12,
    color: '#7f8c8d',
    marginBottom: 6,
  },
  opacityButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  opBtn: {
    flex: 1,
    paddingVertical: 7,
    backgroundColor: '#f1f2f6',
    borderRadius: 6,
    alignItems: 'center',
  },
  opBtnActive: {
    backgroundColor: '#34495e',
  },
  opBtnText: {
    fontSize: 12,
    color: '#2c3e50',
    fontWeight: '600',
  },
  opBtnTextActive: {
    color: '#fff',
  },
  deleteBtn: {
    marginTop: 8,
    paddingVertical: 11,
    borderRadius: 6,
    backgroundColor: '#fdecea',
    alignItems: 'center',
  },
  deleteBtnText: {
    color: '#e74c3c',
    fontWeight: 'bold',
    fontSize: 13,
  },
});