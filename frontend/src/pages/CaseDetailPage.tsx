import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useCase } from '@/api/cases';
import { PDFViewer } from '@/components/features/PDFViewer';
import { DocumentList } from '@/components/features/DocumentList';
import { DocumentUpload } from '@/components/features/DocumentUpload';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';

export default function CaseDetailPage() {
    const { id } = useParams<{ id: string }>();
    const { data: caseData, isLoading, error, refetch } = useCase(id);
    const [selectedDocumentId, setSelectedDocumentId] = useState<string | undefined>();
    const [showUpload, setShowUpload] = useState(false);

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

    const initialDocument = caseData.documents[0];

    const handleUploadComplete = () => {
        setShowUpload(false);
        refetch();
    };

    return (
        <div className="h-full flex flex-col">
            <div className="border-b p-6 bg-white">
                <div className="space-y-2">
                    <h1 className="text-3xl font-bold text-gray-900">{caseData.title}</h1>
                    <p className="text-gray-700">{caseData.description}</p>
                </div>
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
                        selectedDocumentId={selectedDocumentId || initialDocument?.id}
                        onSelectDocument={setSelectedDocumentId}
                    />
                </div>

                <div className="flex-1 bg-gray-100 overflow-hidden">
                    {selectedDocumentId || initialDocument ? (
                        <PDFViewer
                            documentId={selectedDocumentId || initialDocument.id}
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
