import { create } from 'zustand';
import type { AuthState } from '@/types';

export const useAuthStore = create<AuthState>((set) => ({
    isLoggedIn: false,
    username: null,
    email: null,

    login: (username: string, email: string) => {
        sessionStorage.setItem('isLoggedIn', 'true');
        sessionStorage.setItem('username', username);
        sessionStorage.setItem('email', email);

        set({
            isLoggedIn: true,
            username,
            email,
        });
    },

    logout: () => {
        sessionStorage.removeItem('isLoggedIn');
        sessionStorage.removeItem('username');
        sessionStorage.removeItem('email');

        set({
            isLoggedIn: false,
            username: null,
            email: null,
        });
    },
}));

export function restoreSession() {
    const isLoggedIn = sessionStorage.getItem('isLoggedIn') === 'true';
    const username = sessionStorage.getItem('username');
    const email = sessionStorage.getItem('email');

    if (isLoggedIn && username && email) {
        useAuthStore.setState({
            isLoggedIn: true,
            username,
            email,
        });
        return true;
    }

    return false;
}

