import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';

const ACCESS_TOKEN_KEY = 'brainscan_access_token';

const REFRESH_TOKEN_KEY = 'brainscan_refresh_token';

export async function saveTokens(access: string, refresh: string): Promise<void> {
    if (Platform.OS === 'web') {
        localStorage.setItem(ACCESS_TOKEN_KEY, access);
        localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
    } else {
        await SecureStore.setItemAsync(ACCESS_TOKEN_KEY, access);
        await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, refresh);
    }
}

export async function getAccessToken(): Promise<string | null> {
    if (Platform.OS === 'web') {
        return localStorage.getItem(ACCESS_TOKEN_KEY);
    }
    return await SecureStore.getItemAsync(ACCESS_TOKEN_KEY);
}

export async function getRefreshToken(): Promise<string | null> {
    if (Platform.OS === 'web') {
        return localStorage.getItem(REFRESH_TOKEN_KEY);

    }
    return await SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
}

export async function clearTokens(): Promise<void> {
    if (Platform.OS === 'web') {
        localStorage.removeItem(ACCESS_TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
    } else {
        await SecureStore.deleteItemAsync(ACCESS_TOKEN_KEY);
        await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
    }
}