import { describe, it, expect, beforeEach } from 'vitest';
import { useAuthStore, restoreSession } from '../auth-store';

describe('Auth Store', () => {
    beforeEach(() => {
        sessionStorage.clear();
        useAuthStore.setState({
            isLoggedIn: false,
            username: null,
            email: null,
        });
    });

    it('should have initial state', () => {
        const state = useAuthStore.getState();
        expect(state.isLoggedIn).toBe(false);
        expect(state.username).toBeNull();
        expect(state.email).toBeNull();
    });

    it('should login and store in sessionStorage', () => {
        const { login } = useAuthStore.getState();
        login('testuser', 'test@example.com');

        const state = useAuthStore.getState();
        expect(state.isLoggedIn).toBe(true);
        expect(state.username).toBe('testuser');
        expect(state.email).toBe('test@example.com');

        expect(sessionStorage.getItem('isLoggedIn')).toBe('true');
        expect(sessionStorage.getItem('username')).toBe('testuser');
        expect(sessionStorage.getItem('email')).toBe('test@example.com');
    });

    it('should logout and clear sessionStorage', () => {
        const { login, logout } = useAuthStore.getState();

        login('testuser', 'test@example.com');
        logout();

        const state = useAuthStore.getState();
        expect(state.isLoggedIn).toBe(false);
        expect(state.username).toBeNull();
        expect(state.email).toBeNull();

        expect(sessionStorage.getItem('isLoggedIn')).toBeNull();
        expect(sessionStorage.getItem('username')).toBeNull();
        expect(sessionStorage.getItem('email')).toBeNull();
    });

    it('should restore session from sessionStorage', () => {
        sessionStorage.setItem('isLoggedIn', 'true');
        sessionStorage.setItem('username', 'restoreduser');
        sessionStorage.setItem('email', 'restored@example.com');

        const restored = restoreSession();
        expect(restored).toBe(true);

        const state = useAuthStore.getState();
        expect(state.isLoggedIn).toBe(true);
        expect(state.username).toBe('restoreduser');
        expect(state.email).toBe('restored@example.com');
    });

    it('should not restore session if data is incomplete', () => {
        sessionStorage.setItem('isLoggedIn', 'true');
        sessionStorage.setItem('username', 'testuser');

        const restored = restoreSession();
        expect(restored).toBe(false);

        const state = useAuthStore.getState();
        expect(state.isLoggedIn).toBe(false);
    });

    it('should overwrite previous login', () => {
        const { login } = useAuthStore.getState();

        login('user1', 'user1@example.com');
        login('user2', 'user2@example.com');

        const state = useAuthStore.getState();
        expect(state.username).toBe('user2');
        expect(state.email).toBe('user2@example.com');
    });
});

