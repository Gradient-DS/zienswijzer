import { useEffect, useState, useRef } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { useCase } from '@/api/cases';
import { PDFViewer } from '@/components/features/PDFViewer';
import { BreadcrumbNavigation } from '@/components/features/BreadcrumbNavigation';
import { StakeholderDetailView } from '@/components/features/StakeholderDetailView';
import { StakeholderBoard } from '@/components/features/StakeholderBoard';
import { useCaseStakeholders } from '@/api/stakeholders';
import { CreateCaseForm } from '@/components/features/CreateCaseForm';
import { CaseOverview } from '@/components/features/CaseOverview';
import { useUIStore } from '@/store';
import { useCaseStep } from '@/hooks/useCaseStep';
import { apiClient } from '@/api/client';
import { transformChunkDetail } from '@/lib/mention-utils';
import type { ChunkDetail } from '@/types';
import { cn } from '@/lib/utils';

export default function CaseDetailPage() {
    const { id } = useParams<{ id: string }>();
    const location = useLocation();
    const navigate = useNavigate();
    const { data: caseData, isLoading, error } = useCase(id);
    const searchParams = new URLSearchParams(location.search);
    const selectedDocumentId = searchParams.get('document') || undefined;
    const selectedStakeholderId = searchParams.get('stakeholder') || undefined;
    const { step, setStep } = useCaseStep();
    const { data: stakeholders } = useCaseStakeholders(id);
    const { isSidebarOpen } = useUIStore();
    const [isMobile, setIsMobile] = useState(false);
    const hasAutoSelectedRef = useRef<string | undefined>(undefined);

    useEffect(() => {
        const checkMobile = () => {
            setIsMobile(window.innerWidth < 1024);
        };
        checkMobile();
        window.addEventListener('resize', checkMobile);
        return () => window.removeEventListener('resize', checkMobile);
    }, []);

    useEffect(() => {
        if (step === 'review' && id && caseData?.documents && caseData.documents.length > 0 && !selectedDocumentId) {
            const firstUncompletedDocument = caseData.documents.find(
                doc => doc.parse_status !== 'completed' && doc.parse_status !== 'failed'
            ) || caseData.documents[0];

            if (hasAutoSelectedRef.current !== id) {
                hasAutoSelectedRef.current = id;
                const newSearchParams = new URLSearchParams(location.search);
                newSearchParams.set('document', firstUncompletedDocument.id);
                navigate(`${location.pathname}?${newSearchParams.toString()}`, { replace: true });
            }
        } else if (step !== 'review') {
            hasAutoSelectedRef.current = undefined;
        }
    }, [step, id, caseData?.documents, selectedDocumentId, location.pathname, location.search, navigate]);

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

    const renderMainContent = () => {
        if (step === 'create') {
            return <CreateCaseForm caseId={id} />;
        }

        if (step === 'belanghebbenden') {
            if (selectedStakeholderId && stakeholders) {
                const stakeholder = stakeholders.find(s => s.id === selectedStakeholderId);
                if (stakeholder && id) {
                    return (
                        <StakeholderDetailView
                            caseId={id}
                            stakeholderId={selectedStakeholderId}
                            stakeholder={stakeholder}
                        />
                    );
                }
            }
            // Show board view by default
            if (id) {
                return (
                    <StakeholderBoard
                        caseId={id}
                        onSelectStakeholder={(stakeholderId) => {
                            const newSearchParams = new URLSearchParams(location.search);
                            newSearchParams.set('stakeholder', stakeholderId);
                            newSearchParams.set('step', 'belanghebbenden');
                            navigate(`${location.pathname}?${newSearchParams.toString()}`, { replace: true });
                        }}
                    />
                );
            }
            return (
                <div className="flex items-center justify-center h-full text-gray-500">
                    <div className="text-center">
                        <p className="text-lg font-medium mb-2">Geen zaak geselecteerd</p>
                    </div>
                </div>
            );
        }

        if (step === 'overview') {
            if (id) {
                return <CaseOverview caseId={id} />;
            }
            return (
                <div className="flex items-center justify-center h-full text-gray-500">
                    <div className="text-center">
                        <p className="text-lg font-medium mb-2">Geen zaak geselecteerd</p>
                    </div>
                </div>
            );
        }

        if (step === 'review') {
            if (selectedDocumentId) {
                const handleNextDocument = async () => {
                    if (!caseData?.documents || caseData.documents.length === 0) return;

                    const currentIndex = caseData.documents.findIndex(doc => doc.id === selectedDocumentId);
                    if (currentIndex === -1) return;

                    // Helper to check if a document has unchecked chunks
                    const checkDocumentHasUncheckedChunks = async (docId: string): Promise<boolean> => {
                        try {
                            const res = await apiClient.get(`/documents/${docId}/chunks`, {
                                params: id ? { case_id: id } : {}
                            });
                            const chunks = (res.data.chunks || []).map(transformChunkDetail) as ChunkDetail[];
                            const allMentions = chunks.flatMap((chunk: ChunkDetail) => chunk.stakeholder_mentions || []);
                            return allMentions.some((mention) => !mention.checked);
                        } catch {
                            return false;
                        }
                    };

                    // Find next document with unchecked chunks
                    let nextIndex = currentIndex;
                    let attempts = 0;
                    let foundNext = false;

                    while (attempts < caseData.documents.length) {
                        nextIndex = (nextIndex + 1) % caseData.documents.length;
                        attempts++;
                        const nextDoc = caseData.documents[nextIndex];

                        const hasUnchecked = await checkDocumentHasUncheckedChunks(nextDoc.id);
                        if (hasUnchecked) {
                            const newSearchParams = new URLSearchParams(location.search);
                            newSearchParams.set('document', nextDoc.id);
                            newSearchParams.set('step', 'review');
                            navigate(`${location.pathname}?${newSearchParams.toString()}`);
                            foundNext = true;
                            break;
                        }
                    }

                    // If no document with unchecked chunks found, navigate to next step
                    if (!foundNext && id) {
                        setStep('belanghebbenden', id);
                    }
                };

                const handleNavigateToNextStep = () => {
                    if (id) {
                        setStep('belanghebbenden', id);
                    }
                };

                return (
                    <PDFViewer
                        documentId={selectedDocumentId}
                        className="h-full"
                        onNextDocument={handleNextDocument}
                        allDocuments={caseData.documents}
                        onNavigateToNextStep={handleNavigateToNextStep}
                    />
                );
            }
            return (
                <div className="flex items-center justify-center h-full text-gray-500">
                    <div className="text-center">
                        <p className="text-lg font-medium mb-2">Geen document geselecteerd</p>
                        <p className="text-sm">Selecteer een document uit de lijst om te bekijken</p>
                    </div>
                </div>
            );
        }

        return null;
    };

    return (
        <div className="h-full flex flex-col">
            <div className={cn(
                "border-b bg-white",
                isMobile ? "px-4 pb-3 -mt-12" : "px-6 pt-4 pb-3",
                !isMobile && !isSidebarOpen && "pl-[72px]"
            )}>
                <BreadcrumbNavigation caseId={id} />
            </div>

            <div className="flex-1 bg-gray-100 overflow-hidden">
                {renderMainContent()}
            </div>
        </div>
    );
}
