import React, { useState } from 'react';
import {StyleSheet, Text, View, TextInput, TouchableOpacity, ActivityIndicator, Alert} from 'react-native';
import { BASE_URL } from '@/services/api';
import { saveTokens } from '@/services/storage';

interface LoginScreenProps {
    onLoginSuccess: () => void;

}

export default function LoginScreen({ onLoginSuccess }: LoginScreenProps) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [errorMsg, setErrorMsg] = useState('');

    const handleLogin = async () => {
        if (!username.trim() || !password) {
            setErrorMsg('Wprowadź login oraz hasło.');
            return;
        }
        setLoading(true);
        setErrorMsg('');
        try {
            const response = await fetch(`${BASE_URL}/api/token/`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username: username.trim(), password}),
            });

            const data = await response.json();

            if (response.ok && data.access) {
                await saveTokens(data.access, data.refresh);
                onLoginSuccess();
            } else {
                setErrorMsg('Nieprawidłowy login lub hasło.');
            }
        } catch (err) {
            setErrorMsg('Wystąpił błąd podczas logowania. Spróbuj ponownie.');
            
        } finally {
            setLoading(false);
        }
    };

    return (
        <View style={styles.container}>
            <View style={styles.card}>
                <Text style={styles.title}>System BrainScan</Text>
                <Text style={styles.subtitle}>Panel personelu medycznego</Text>
                {errorMsg ? <Text style={styles.errorText}>{errorMsg}</Text> : null}
                <TextInput
                    style={styles.input}
                    placeholder="Nazwa użytkownika / login"
                    placeholderTextColor="#7f8c8d"
                    value={username}
                    onChangeText={setUsername}
                    autoCapitalize="none"
                    />

                <TextInput
                    style={styles.input}
                    placeholder="Hasło"
                    placeholderTextColor="#7f8c8d"
                    value={password}
                    onChangeText={setPassword}
                    secureTextEntry
                />
                <TouchableOpacity style={styles.button} onPress={handleLogin} disabled={loading}>
                    {loading ? (
                        <ActivityIndicator color="#fff" />
                    ) : (
                        <Text style={styles.buttonText}>Zaloguj się</Text>
                    )}
                </TouchableOpacity>
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#f4f7f6',
  },
  card: {
    width: '100%',
    maxWidth: 400,
    backgroundColor: '#fff',
    padding: 25,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 6,
    elevation: 4,
  },
  title: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#2c3e50',
    textAlign: 'center',
    marginBottom: 6,
  },
  subtitle: {
    fontSize: 13,
    color: '#7f8c8d',
    textAlign: 'center',
    marginBottom: 20,
  },
  input: {
    backgroundColor: '#f8f9fa',
    borderWidth: 1,
    borderColor: '#dcdde1',
    borderRadius: 8,
    padding: 12,
    fontSize: 15,
    marginBottom: 12,
    color: '#2c3e50',
  },
  button: {
    backgroundColor: '#2980b9',
    padding: 14,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  errorText: {
    color: '#e74c3c',
    marginBottom: 12,
    textAlign: 'center',
    fontSize: 13,
  },
});