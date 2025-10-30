export interface User {
    username: string;
    email: string;
}

export interface AuthState {
    isLoggedIn: boolean;
    username: string | null;
    email: string | null;
    login: (username: string, email: string) => void;
    logout: () => void;
}

