import {Platform} from 'react-native';
import {getAccessToken, getRefreshToken, saveTokens, clearTokens} from './storage';

//Bazowy url, dla web i emulatorów: localhost/10.0.2.2, dla telefonu IP

export const BASE_URL = Platform.select({
    web: 'http://loclahost:8000',
    android: 'http://10.0.2.2:8000',
    default: 'http://localhost:8000',
});

export async function apiFetch(endpoint: string, options: RequestInit = {}): Promise<Response> {
    let token = await getAccessToken();

    const headers: Record<string, string> = {
        ...(options.headers as Record<string,string>),
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;

    }

    let response = await fetch(`${BASE_URL}${endpoint}`, {
        ...options,
        headers,
    });

    if (response.status === 401) {
        const refreshToken = await getRefreshToken();
        if (refreshToken) {
            const refreshResponse = await fetch(`${BASE_URL}/api/token/refresh/`,{
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({refresh: refreshToken}),
            });

            if (refreshResponse.ok) {
                const data = await refreshResponse.json();
                await saveTokens(data.access, refreshToken);
                headers['Authorization'] = `Bearer ${data.access}`;
                //Ponowne wysłanie zapytania z nowym tokenem
                response = await fetch(`${BASE_URL}${endpoint}`, {
                    ...options,
                    headers,
                });
            } else {
                await clearTokens();
            }
        }
    }
    return response;
}