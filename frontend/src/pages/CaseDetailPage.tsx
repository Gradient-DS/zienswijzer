import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { useCase } from '@/api/cases';
import { PDFViewer } from '@/components/features/PDFViewer';
import { DocumentList } from '@/components/features/DocumentList';
import { DocumentUpload } from '@/components/features/DocumentUpload';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import { useUIStore } from '@/store';
import { cn } from '@/lib/utils';

export default function CaseDetailPage() {
    const { id } = useParams<{ id: string }>();
    const { data: caseData, isLoading, error, refetch } = useCase(id);
    const [selectedDocumentId, setSelectedDocumentId] = useState<string | undefined>();
    const [showUpload, setShowUpload] = useState(false);
    const previousCaseIdRef = useRef<string | undefined>(undefined);
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

    useEffect(() => {
        const caseIdChanged = previousCaseIdRef.current !== undefined && previousCaseIdRef.current !== id;
        previousCaseIdRef.current = id;

        if (caseData?.documents && caseData.documents.length > 0) {
            const firstDocumentId = caseData.documents[0].id;
            setSelectedDocumentId((currentSelection) => {
                if (caseIdChanged || !currentSelection || !caseData.documents.find(doc => doc.id === currentSelection)) {
                    return firstDocumentId;
                }
                return currentSelection;
            });
        } else {
            setSelectedDocumentId(undefined);
        }
    }, [id, caseData?.documents]);

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

    const handleUploadComplete = () => {
        setShowUpload(false);
        refetch();
    };

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
                            <h1 className="text-xl font-bold text-gray-900 truncate leading-tight">{caseData.title}</h1>
                            <p className="text-sm text-gray-700 truncate mt-1">{caseData.description}</p>
                        </div>
                    </div>
                ) : (
                    <div className="space-y-1">
                        <h1 className="text-xl font-bold text-gray-900 leading-tight">{caseData.title}</h1>
                        <p className="text-sm text-gray-700">{caseData.description}</p>
                    </div>
                )}
            </div>

            <div className="flex-1 flex overflow-hidden">
                <div className="w-80 border-r bg-white overflow-y-auto p-4">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-lg font-semibold">Documenten</h2>
                        <Button
                            onClick={() => setShowUpload(!showUpload)}
                            variant="outline"
                            size="sm"
                            className="flex items-center gap-2"
                        >
                            <Plus className="h-4 w-4" />
                            Toevoegen
                        </Button>
                    </div>

                    {showUpload && (
                        <div className="mb-6">
                            <DocumentUpload
                                caseId={caseData.id}
                                onUploadComplete={handleUploadComplete}
                            />
                        </div>
                    )}

                    <DocumentList
                        documents={caseData.documents}
                        selectedDocumentId={selectedDocumentId}
                        onSelectDocument={setSelectedDocumentId}
                    />
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
        </div>
    );
}
