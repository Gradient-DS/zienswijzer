import { useState, useEffect, useCallback, useRef } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { Sidebar } from '@/components/features/Sidebar';
import { useUIStore } from '@/store';
import { useCase, useCases } from '@/api/cases';
import { Button } from '@/components/ui/button';
import { Menu } from 'lucide-react';
import {
    Sheet,
    SheetContent,
    SheetTrigger,
    SheetTitle,
} from '@/components/ui/sheet';

export default function HomePage() {
    const location = useLocation();
    const navigate = useNavigate();
    const isNewCase = location.pathname === '/cases/new';
    const caseIdMatch = location.pathname.match(/\/cases\/(.+)/);
    const selectedCaseId = isNewCase ? undefined : (caseIdMatch ? caseIdMatch[1] : undefined);
    const searchParams = new URLSearchParams(location.search);
    const selectedDocumentId = searchParams.get('document') || undefined;
    const { data: caseData } = useCase(selectedCaseId);
    const { data: cases, isLoading: isLoadingCases } = useCases();
    const { isSidebarOpen, toggleSidebar, setSidebarOpen } = useUIStore();
    const [isMobile, setIsMobile] = useState(false);
    const hasAutoSelectedRef = useRef<string | undefined>(undefined);
    const hasAutoNavigatedRef = useRef(false);

    const handleSelectDocument = useCallback((documentId: string) => {
        if (selectedCaseId) {
            const newSearchParams = new URLSearchParams(location.search);
            newSearchParams.set('document', documentId);
            // Always ensure we're on the review step when selecting a document
            newSearchParams.set('step', 'review');
            navigate(`${location.pathname}?${newSearchParams.toString()}`, { replace: true });
        }
    }, [selectedCaseId, location.pathname, location.search, navigate]);

    useEffect(() => {
        const checkMobile = () => {
            const mobile = window.innerWidth < 1024;
            setIsMobile(mobile);
            if (!mobile) {
                setSidebarOpen(true);
            } else {
                setSidebarOpen(false);
            }
        };

        checkMobile();
        window.addEventListener('resize', checkMobile);
        return () => window.removeEventListener('resize', checkMobile);
    }, [setSidebarOpen]);

    useEffect(() => {
        if (selectedCaseId && caseData?.documents && caseData.documents.length > 0 && !selectedDocumentId) {
            const firstDocumentId = caseData.documents[0].id;
            if (hasAutoSelectedRef.current !== selectedCaseId) {
                hasAutoSelectedRef.current = selectedCaseId;
                handleSelectDocument(firstDocumentId);
            }
        } else if (!selectedCaseId) {
            hasAutoSelectedRef.current = undefined;
        }
    }, [selectedCaseId, caseData?.documents, selectedDocumentId, handleSelectDocument]);

    useEffect(() => {
        if (!isLoadingCases && cases && cases.length === 0 && location.pathname === '/home' && !hasAutoNavigatedRef.current) {
            hasAutoNavigatedRef.current = true;
            navigate('/cases/new?step=create', { replace: true });
        } else if (cases && cases.length > 0) {
            hasAutoNavigatedRef.current = false;
        }
    }, [cases, isLoadingCases, location.pathname, navigate]);

    const sidebarContent = (
        <Sidebar
            selectedCaseId={selectedCaseId}
            documents={isNewCase ? [] : caseData?.documents}
            selectedDocumentId={selectedDocumentId}
            onSelectDocument={handleSelectDocument}
            isMobile={isMobile}
            onClose={() => setSidebarOpen(false)}
        />
    );

    return (
        <div className="flex h-screen bg-white relative">
            {isMobile ? (
                <>
                    <div className="fixed top-4 left-4 z-50 lg:hidden">
                        <Sheet open={isSidebarOpen} onOpenChange={setSidebarOpen}>
                            <SheetTrigger asChild>
                                <Button variant="outline" size="icon">
                                    <Menu className="h-5 w-5" />
                                </Button>
                            </SheetTrigger>
                            <SheetContent side="left" className="w-[280px] p-0 overflow-y-auto" showCloseButton={false}>
                                <SheetTitle className="sr-only">Navigatie</SheetTitle>
                                {sidebarContent}
                            </SheetContent>
                        </Sheet>
                    </div>
                    <div className="flex-1 overflow-y-auto w-full pt-16">
                        <Outlet />
                    </div>
                </>
            ) : (
                <>
                    <div
                        className={`
                            transition-all duration-300 ease-in-out
                            ${isSidebarOpen ? 'w-[280px]' : 'w-0'}
                            overflow-hidden
                            flex-shrink-0
                        `}
                    >
                        {isSidebarOpen && sidebarContent}
                    </div>
                    <div className="flex-1 overflow-y-auto relative">
                        {!isSidebarOpen && (
                            <Button
                                variant="outline"
                                size="icon"
                                className="fixed top-5 left-4 z-50"
                                onClick={toggleSidebar}
                            >
                                <Menu className="h-5 w-5" />
                            </Button>
                        )}
                        <Outlet />
                    </div>
                </>
            )}
        </div>
    );
}
