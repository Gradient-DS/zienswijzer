import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/store';
import { useEffect } from 'react';

export function WorkspaceLayout() {
    const isLoggedIn = useAuthStore((state) => state.isLoggedIn);

    useEffect(() => {
        if (!isLoggedIn) {
            const storedLogin = sessionStorage.getItem('isLoggedIn') === 'true';
            const username = sessionStorage.getItem('username');
            const email = sessionStorage.getItem('email');

            if (storedLogin && username && email) {
                useAuthStore.getState().login(username, email);
            }
        }
    }, [isLoggedIn]);

    if (!isLoggedIn) {
        return <Navigate to="/login" replace />;
    }

    return (
        <div className="min-h-screen bg-background">
            <Outlet />
        </div>
    );
}

