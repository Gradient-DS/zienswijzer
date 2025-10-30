import { Outlet } from 'react-router-dom';

export function AuthLayout() {
    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-blue-50 to-white">
            <Outlet />
        </div>
    );
}

