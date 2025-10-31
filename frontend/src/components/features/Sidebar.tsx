import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore, useUIStore } from '@/store';
import { Button } from '@/components/ui/button';
import { DocumentUploadDialog } from './DocumentUploadDialog';
import { CaseDropdown } from './CaseDropdown';
import { DocumentList } from './DocumentList';
import { StakeholderList } from './StakeholderList';
import { useCaseStakeholders, useStakeholderVerificationStatus } from '@/api/stakeholders';
import { useCaseStep } from '@/hooks/useCaseStep';
import type { Document } from '@/types';
import {
    Bell,
    Plus,
    User,
    Settings,
    LogOut,
    ChevronLeft,
} from 'lucide-react';

interface SidebarProps {
    selectedCaseId?: string;
    onCaseSelect?: (caseId: string) => void;
    documents?: Document[];
    selectedDocumentId?: string;
    onSelectDocument?: (documentId: string) => void;
    onClose?: () => void;
    isMobile?: boolean;
}

export function Sidebar({
    selectedCaseId,
    onCaseSelect,
    documents,
    selectedDocumentId,
    onSelectDocument,
    onClose,
    isMobile = false,
}: SidebarProps) {
    const navigate = useNavigate();
    const location = useLocation();
    const { logout } = useAuthStore();
    const { toggleSidebar } = useUIStore();
    const { step } = useCaseStep();
    const [isUploadDialogOpen, setIsUploadDialogOpen] = useState(false);
    const { data: stakeholders } = useCaseStakeholders(selectedCaseId);
    const { data: verifiedStakeholderIds = new Set<string>() } = useStakeholderVerificationStatus(selectedCaseId);

    const handleLogout = () => {
        logout();
        navigate('/login', { replace: true });
    };

    const handleNewCase = () => {
        navigate('/cases/new?step=create');
        if (isMobile && onClose) {
            onClose();
        }
    };

    const handleAddDocument = () => {
        setIsUploadDialogOpen(true);
        if (isMobile && onClose) {
            onClose();
        }
    };

    const renderSidebarContent = () => {
        if (step === 'belanghebbenden' && selectedCaseId) {
            const searchParams = new URLSearchParams(location.search);
            const selectedStakeholderId = searchParams.get('stakeholder') || undefined;

            const handleSelectStakeholder = (stakeholderId: string) => {
                const newSearchParams = new URLSearchParams(location.search);
                newSearchParams.set('stakeholder', stakeholderId);
                newSearchParams.set('step', 'belanghebbenden');
                navigate(`${location.pathname}?${newSearchParams.toString()}`, { replace: true });
            };

            const handleOverviewClick = () => {
                const newSearchParams = new URLSearchParams(location.search);
                newSearchParams.delete('stakeholder');
                newSearchParams.set('step', 'belanghebbenden');
                navigate(`${location.pathname}?${newSearchParams.toString()}`, { replace: true });
            };

            return (
                <div className="flex-1 flex flex-col min-h-0">
                    <div className="flex-shrink-0 p-4 pb-3 border-b border-gray-200 bg-gray-50">
                        <Button
                            variant="ghost"
                            className="w-full justify-start h-auto p-0 font-semibold text-lg hover:bg-transparent"
                            onClick={handleOverviewClick}
                        >
                            Overzicht
                        </Button>
                    </div>
                    <div className="flex-1 overflow-y-auto p-4 pt-3">
                        {stakeholders && stakeholders.length > 0 ? (
                            <StakeholderList
                                stakeholders={stakeholders}
                                selectedStakeholderId={selectedStakeholderId}
                                onSelectStakeholder={handleSelectStakeholder}
                                verifiedStakeholderIds={verifiedStakeholderIds}
                                caseId={selectedCaseId}
                            />
                        ) : (
                            <div className="text-center py-8 text-muted-foreground">
                                <p>Geen belanghebbenden beschikbaar</p>
                            </div>
                        )}
                    </div>
                </div>
            );
        }

        if (step === 'create' || selectedCaseId) {
            return (
                <div className="flex-1 flex flex-col min-h-0">
                    <div className="flex-shrink-0 flex items-center justify-between p-4 pb-3 border-b border-gray-200 bg-gray-50">
                        <h2 className="text-lg font-semibold">Documenten</h2>
                        {step === 'review' && selectedCaseId && (
                            <Button
                                onClick={handleAddDocument}
                                variant="outline"
                                size="sm"
                                className="flex items-center gap-2"
                            >
                                <Plus className="h-4 w-4" />
                                Toevoegen
                            </Button>
                        )}
                    </div>

                    <div className="flex-1 overflow-y-auto p-4 pt-3">
                        {documents && documents.length > 0 ? (
                            <DocumentList
                                documents={documents}
                                selectedDocumentId={selectedDocumentId}
                                onSelectDocument={onSelectDocument || (() => { })}
                                disabled={step === 'create' && !!selectedCaseId}
                                caseId={selectedCaseId}
                            />
                        ) : (
                            <div className="text-center py-8 text-muted-foreground">
                                <p>Geen documenten beschikbaar</p>
                            </div>
                        )}
                    </div>
                </div>
            );
        }

        return null;
    };

    return (
        <>
            {selectedCaseId && (
                <DocumentUploadDialog
                    open={isUploadDialogOpen}
                    onOpenChange={setIsUploadDialogOpen}
                    caseId={selectedCaseId}
                />
            )}
            <div className="flex flex-col h-screen w-[280px] bg-gray-50 border-r border-gray-200">
                <div className="flex-shrink-0 p-4 space-y-3 border-b border-gray-200">
                    <div className="flex items-center w-full">
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => {
                                if (isMobile && onClose) {
                                    onClose();
                                } else {
                                    toggleSidebar();
                                }
                            }}
                        >
                            <ChevronLeft className="h-4 w-4" />
                        </Button>
                        <h1 className="text-md text-gray-900 ml-auto">WOO zienswijze</h1>
                    </div>
                    <div className="space-y-1">
                        <Button
                            variant="ghost"
                            className="w-full justify-start gap-2 h-8 pl-2"
                            onClick={handleNewCase}
                        >
                            <Plus className="h-4 w-4" />
                            Nieuwe zaak
                        </Button>
                        <Button
                            variant="ghost"
                            className="w-full justify-start gap-2 h-8 pl-2"
                        >
                            <Bell className="h-4 w-4" />
                            Notificaties
                        </Button>
                        <CaseDropdown
                            selectedCaseId={selectedCaseId}
                            onCaseSelect={onCaseSelect}
                        />
                    </div>
                </div>

                {renderSidebarContent()}

                <div className="flex-shrink-0 p-4 space-y-2 border-t border-gray-200">
                    <Button
                        variant="ghost"
                        className="w-full justify-start gap-2"
                    >
                        <User className="h-4 w-4" />
                        Account
                    </Button>
                    <Button
                        variant="ghost"
                        className="w-full justify-start gap-2"
                        onClick={handleLogout}
                    >
                        <LogOut className="h-4 w-4" />
                        Uitloggen
                    </Button>
                    <Button
                        variant="ghost"
                        className="w-full justify-start gap-2"
                    >
                        <Settings className="h-4 w-4" />
                        Instellingen
                    </Button>
                </div>
            </div>
        </>
    );
}

