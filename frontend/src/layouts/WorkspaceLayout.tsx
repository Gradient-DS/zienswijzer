import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/store';
import { useEffect } from 'react';

const IS_DEVELOPMENT = import.meta.env.DEV;

export function WorkspaceLayout() {
    const isLoggedIn = useAuthStore((state) => state.isLoggedIn);

    useEffect(() => {
        if (IS_DEVELOPMENT && !isLoggedIn) {
            useAuthStore.getState().login('dev_user', 'dev@example.com');
            return;
        }

        if (!isLoggedIn) {
            const storedLogin = sessionStorage.getItem('isLoggedIn') === 'true';
            const username = sessionStorage.getItem('username');
            const email = sessionStorage.getItem('email');

            if (storedLogin && username && email) {
                useAuthStore.getState().login(username, email);
            }
        }
    }, [isLoggedIn]);

    if (!IS_DEVELOPMENT && !isLoggedIn) {
        return <Navigate to="/login" replace />;
    }

    return (
        <div className="min-h-screen bg-background">
            <Outlet />
        </div>
    );
}

