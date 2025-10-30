import { Outlet } from 'react-router-dom';

/**
 * AuthLayout follows Rijkshuisstijl (Dutch Government) design guidelines
 * - Clean white background
 * - Centered content with proper spacing
 * - Accessible layout structure
 */
export function AuthLayout() {
    return (
        <div className="min-h-screen flex items-center justify-center bg-white p-4">
            <div className="w-full max-w-md">
                <Outlet />
            </div>
        </div>
    );
}

