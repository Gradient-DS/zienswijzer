import { useEffect, useState } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { useCase } from '@/api/cases';
import { PDFViewer } from '@/components/features/PDFViewer';
import { useUIStore } from '@/store';
import { cn } from '@/lib/utils';

export default function CaseDetailPage() {
    const { id } = useParams<{ id: string }>();
    const location = useLocation();
    const { data: caseData, isLoading, error } = useCase(id);
    const searchParams = new URLSearchParams(location.search);
    const selectedDocumentId = searchParams.get('document') || undefined;
    const { isSidebarOpen } = useUIStore();
    const [isMobile, setIsMobile] = useState(false);

    useEffect(() => {
        const checkMobile = () => {
            setIsMobile(window.innerWidth < 1024);
        };
        checkMobile();
        window.addEventListener('resize', checkMobile);
        return () => window.removeEventListener('resize', checkMobile);
    }, []);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-gray-500">Zaak laden...</div>
            </div>
        );
    }

    if (error || !caseData) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-red-500">Zaak niet gevonden</div>
            </div>
        );
    }

    return (
        <div className="h-full flex flex-col">
            <div className={cn(
                "border-b bg-white",
                isMobile ? "px-4 pb-3 -mt-12" : "px-6 pt-4 pb-3",
                !isMobile && !isSidebarOpen && "pl-[72px]"
            )}>
                {isMobile ? (
                    <div className="flex items-start gap-4 pl-[56px]">
                        <div className="flex-1 min-w-0">
                            <h1 className="text-xl font-bold text-gray-900 truncate leading-tight">Zaak: {caseData.title}</h1>
                            <p className="text-sm text-gray-700 truncate mt-1">Beschrijving: {caseData.description}</p>
                        </div>
                    </div>
                ) : (
                    <div className="space-y-1">
                        <h1 className="text-xl font-bold text-gray-900 leading-tight">Zaak: {caseData.title}</h1>
                        <p className="text-sm text-gray-700">Beschrijving: {caseData.description}</p>
                    </div>
                )}
            </div>

            <div className="flex-1 bg-gray-100 overflow-hidden">
                {selectedDocumentId ? (
                    <PDFViewer
                        documentId={selectedDocumentId}
                        className="h-full"
                    />
                ) : (
                    <div className="flex items-center justify-center h-full text-gray-500">
                        <div className="text-center">
                            <p className="text-lg font-medium mb-2">Geen document geselecteerd</p>
                            <p className="text-sm">Selecteer een document uit de lijst om te bekijken</p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
