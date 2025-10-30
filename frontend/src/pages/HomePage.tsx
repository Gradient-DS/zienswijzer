import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from '@/components/features/Sidebar';

export default function HomePage() {
    const location = useLocation();
    const caseIdMatch = location.pathname.match(/\/cases\/(.+)/);
    const selectedCaseId = caseIdMatch ? caseIdMatch[1] : undefined;

    return (
        <div className="flex h-screen bg-white">
            <Sidebar selectedCaseId={selectedCaseId} />
            <div className="flex-1 overflow-y-auto">
                <Outlet />
            </div>
        </div>
    );
}

