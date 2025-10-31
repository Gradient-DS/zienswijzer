import { useMemo, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { LayoutGrid } from 'lucide-react';
import { useStakeholderMentions } from '@/api/stakeholders';
import { useSendStakeholderEmail, useGenerateStakeholderPDF, useStakeholderEmails, useEmailAuth } from '@/api/email';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { CheckCircle2, Mail, FileText, Clock } from 'lucide-react';
import { StakeholderEmailSettings } from './StakeholderEmailSettings';
import { EmailTimeline } from './EmailTimeline';
import { EmailAuthDialog } from './EmailAuthDialog';
import { PDFPreview } from './PDFPreview';
import { EmailRepliesModal } from './EmailRepliesModal';
import { useAuthStore } from '@/store';
import type { Stakeholder, ChunkDetail, StakeholderMention } from '@/types';
import type { ContentType, EmailAddress, SentEmail } from '@/types/email';
import { getStakeholderStatus } from '@/lib/stakeholder-status';
import type { StakeholderStatus } from '@/lib/stakeholder-status';

interface StakeholderDetailViewProps {
    caseId: string;
    stakeholderId: string;
    stakeholder: Stakeholder;
}


export function StakeholderDetailView({
    caseId,
    stakeholderId,
    stakeholder,
}: StakeholderDetailViewProps) {
    const navigate = useNavigate();
    const location = useLocation();
    const { data: chunks, isLoading } = useStakeholderMentions(caseId, stakeholderId);
    const { username, email } = useAuthStore();
    const [showAuthDialog, setShowAuthDialog] = useState(false);
    const [pendingEmailData, setPendingEmailData] = useState<{
        to: EmailAddress[];
        subject: string;
        content_type: ContentType;
        custom_message?: string;
    } | null>(null);

    const sendEmail = useSendStakeholderEmail();
    const generatePDF = useGenerateStakeholderPDF();
    const { data: sentEmails = [] } = useStakeholderEmails(
        stakeholderId,
        caseId,
        stakeholder.contact_info
    );
    const emailAuth = useEmailAuth();
    const [generatedPDF, setGeneratedPDF] = useState<{ url: string; filename: string } | null>(null);
    const [showPDFModal, setShowPDFModal] = useState(false);
    const [showEmailSettingsModal, setShowEmailSettingsModal] = useState(false);
    const [showRepliesModal, setShowRepliesModal] = useState(false);
    const [selectedEmail, setSelectedEmail] = useState<SentEmail | null>(null);

    const { unprocessedChunks, processedChunks, acceptedChunks } = useMemo(() => {
        if (!chunks) {
            return {
                unprocessedChunks: [],
                processedChunks: [],
                acceptedChunks: [],
            };
        }

        const unprocessed: Array<{ chunk: ChunkDetail; mention: StakeholderMention }> = [];
        const processed: Array<{ chunk: ChunkDetail; mention: StakeholderMention }> = [];
        const accepted: Array<{ chunk: ChunkDetail; mention: StakeholderMention }> = [];

        chunks.forEach(chunk => {
            chunk.stakeholder_mentions.forEach(mention => {
                if (!mention.checked) {
                    unprocessed.push({ chunk, mention });
                } else {
                    processed.push({ chunk, mention });
                    if (mention.accepted === true) {
                        accepted.push({ chunk, mention });
                    }
                }
            });
        });

        return { unprocessedChunks: unprocessed, processedChunks: processed, acceptedChunks: accepted };
    }, [chunks]);

    // Calculate unique documents and pages - must be before conditional returns
    const uniqueDocuments = useMemo(() => {
        if (!chunks) return new Set();
        const docs = new Set<string>();
        chunks.forEach(chunk => {
            docs.add(chunk.document_id);
        });
        return docs;
    }, [chunks]);

    const uniquePages = useMemo(() => {
        if (!chunks) return new Set();
        const pages = new Set<string>();
        chunks.forEach(chunk => {
            pages.add(`${chunk.document_id}-${chunk.page}`);
        });
        return pages;
    }, [chunks]);

    const handleNavigateToDocument = (documentId: string, page?: number) => {
        const newSearchParams = new URLSearchParams(location.search);
        newSearchParams.set('document', documentId);
        newSearchParams.set('step', 'review');
        if (page) {
            newSearchParams.set('page', page.toString());
        }
        newSearchParams.delete('stakeholder');
        navigate(`${location.pathname}?${newSearchParams.toString()}`);
    };

    const handleNavigateToFirstUnverified = () => {
        if (unprocessedChunks.length === 0) return;
        const firstUnprocessed = unprocessedChunks[0];
        handleNavigateToDocument(firstUnprocessed.chunk.document_id, firstUnprocessed.chunk.page);
    };

    const allProcessed = unprocessedChunks.length === 0 && chunks && chunks.length > 0;

    // Calculate stakeholder status to match sidebar
    const stakeholderStatus: StakeholderStatus = useMemo(() => {
        if (!chunks || chunks.length === 0) {
            return 'not_processed';
        }
        return getStakeholderStatus({
            chunks,
            sentEmails,
            stakeholderId: stakeholder.id,
            contactInfo: stakeholder.contact_info,
        });
    }, [chunks, sentEmails, stakeholder.id, stakeholder.contact_info]);

    // Get status icon matching sidebar
    const getStatusIcon = (status: StakeholderStatus) => {
        switch (status) {
            case 'not_processed':
                return <FileText className="h-5 w-5 text-gray-500" />;
            case 'not_contacted':
                return <Clock className="h-5 w-5 text-gray-500" />;
            case 'contacted':
                return <Clock className="h-5 w-5 text-green-600" />;
            case 'contacted_old':
                return <Clock className="h-5 w-5 text-orange-600" />;
            case 'responded':
                return <CheckCircle2 className="h-5 w-5 text-green-600" />;
            default:
                return <FileText className="h-5 w-5 text-gray-500" />;
        }
    };

    // Get status text matching sidebar
    const getStatusText = (status: StakeholderStatus) => {
        switch (status) {
            case 'not_processed':
                return 'Niet verwerkt';
            case 'not_contacted':
                return 'Niet gecontacteerd';
            case 'contacted':
                return 'Gecontacteerd';
            case 'contacted_old':
                return 'Gecontacteerd (> 1 uur)';
            case 'responded':
                return 'Gereageerd';
            default:
                return 'Onbekend';
        }
    };

    const handleSendEmail = async (data: {
        to: EmailAddress[];
        subject: string;
        content_type: ContentType;
        custom_message?: string;
    }) => {
        if (!username || !email) {
            alert('Je moet ingelogd zijn om e-mails te versturen');
            return;
        }

        try {
            await sendEmail.mutateAsync({
                stakeholder_id: stakeholderId,
                case_id: caseId,
                user_id: username,
                ...data,
            });
        } catch (error: any) {
            console.error('Failed to send email:', error);
            if (error.message === 'EMAIL_AUTH_REQUIRED' || error.response?.status === 401) {
                // Store the email data to retry after auth
                setPendingEmailData(data);
                // Get auth URL and show dialog
                try {
                    await emailAuth.mutateAsync(username);
                    setShowAuthDialog(true);
                } catch (authError) {
                    console.error('Failed to get auth URL:', authError);
                    alert('Kon autorisatie URL niet ophalen. Probeer het opnieuw.');
                }
                return;
            }
            alert('E-mail verzenden mislukt. Controleer of je e-mail toegang hebt geautoriseerd.');
        }
    };

    const handleRetryEmail = async () => {
        if (!pendingEmailData || !username) return;

        try {
            await sendEmail.mutateAsync({
                stakeholder_id: stakeholderId,
                case_id: caseId,
                user_id: username,
                ...pendingEmailData,
            });
            setPendingEmailData(null);
        } catch (error: any) {
            if (error.message === 'EMAIL_AUTH_REQUIRED' || error.response?.status === 401) {
                // Still not authorized, show dialog again
                await emailAuth.mutateAsync(username);
                setShowAuthDialog(true);
            } else {
                alert('E-mail verzenden mislukt. Probeer het opnieuw.');
            }
        }
    };

    const handleGeneratePDF = async (data: { content_type: ContentType }) => {
        try {
            const result = await generatePDF.mutateAsync({
                stakeholder_id: stakeholderId,
                case_id: caseId,
                content_type: data.content_type,
            });

            // Store PDF URL and filename for preview
            if (result.url && result.filename) {
                setGeneratedPDF({
                    url: result.url,
                    filename: result.filename,
                });
                setShowPDFModal(true);
            }
        } catch (error) {
            console.error('Failed to generate PDF:', error);
            alert('PDF genereren mislukt.');
        }
    };

    const handleSendEmailSuccess = () => {
        // Close email settings modal after successful send
        setShowEmailSettingsModal(false);
    };

    const handleEmailClick = (email: SentEmail) => {
        setSelectedEmail(email);
        setShowRepliesModal(true);
    };


    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-gray-500">Laden...</div>
            </div>
        );
    }

    if (!chunks || chunks.length === 0) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-center">
                    <p className="text-lg font-medium mb-2">Geen vermeldingen gevonden</p>
                    <p className="text-sm text-gray-500">
                        Deze belanghebbende komt niet voor in de documenten
                    </p>
                </div>
            </div>
        );
    }

    const handleBackToOverview = () => {
        const newSearchParams = new URLSearchParams(location.search);
        newSearchParams.delete('stakeholder');
        newSearchParams.set('step', 'belanghebbenden');
        navigate(`${location.pathname}?${newSearchParams.toString()}`, { replace: true });
    };

    return (
        <div className="h-full overflow-y-auto p-6 space-y-6">
            {/* Header */}
            <div className="space-y-2">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <h1 className="text-2xl font-semibold text-gray-900">
                            {stakeholder.name}
                        </h1>
                    </div>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={handleBackToOverview}
                        className="h-9"
                    >
                        <LayoutGrid className="h-4 w-4 mr-2" />
                        Overzicht
                    </Button>
                </div>
                <div className="flex items-center gap-2">
                    <span className="px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-700 capitalize">
                        {stakeholder.type}
                    </span>
                    {stakeholder.contact_info && (
                        <span className="text-sm text-gray-600">
                            {stakeholder.contact_info}
                        </span>
                    )}
                </div>
            </div>

            {/* Top section: 50/50 split */}
            {(unprocessedChunks.length + processedChunks.length) > 0 && (
                <div className="grid grid-cols-2 gap-4" style={{ minHeight: '25vh' }}>
                    {/* Left: Verification Status */}
                    <Card className="border-2">
                        <CardContent className="p-4 h-full flex flex-col">
                            <div className="flex items-center gap-2 mb-4">
                                {getStatusIcon(stakeholderStatus)}
                                <h2 className="text-lg font-semibold text-gray-900">
                                    Status: {getStatusText(stakeholderStatus)}
                                </h2>
                            </div>

                            <div className="flex-1 space-y-3">
                                <div className="text-sm text-gray-600">
                                    <span className="font-semibold text-gray-900">{acceptedChunks.length}</span> vermelding{acceptedChunks.length !== 1 ? 'en' : ''} van de{' '}
                                    <span className="font-semibold text-gray-900">{unprocessedChunks.length + processedChunks.length}</span> geaccepteerd
                                </div>
                                <div className="text-sm text-gray-600">
                                    <span className="font-semibold text-gray-900">{processedChunks.length}</span> van{' '}
                                    <span className="font-semibold text-gray-900">{unprocessedChunks.length + processedChunks.length}</span> verwerkt
                                </div>

                                {!allProcessed && (
                                    <div className="space-y-2">
                                        <p className="text-sm text-gray-700">
                                            Er zijn nog {unprocessedChunks.length} vermelding{unprocessedChunks.length !== 1 ? 'en' : ''} die verwerkt moeten worden.
                                        </p>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={handleNavigateToFirstUnverified}
                                            className="h-8"
                                        >
                                            Bekijk eerste onverwerkte vermelding
                                        </Button>
                                    </div>
                                )}

                                {allProcessed && stakeholderStatus === 'not_contacted' && (
                                    <div className="text-sm text-green-700">
                                        Alle vermeldingen zijn verwerkt. Je kunt nu een e-mail versturen (alleen geaccepteerde vermeldingen worden meegenomen).
                                    </div>
                                )}

                                {stakeholderStatus === 'contacted' && (
                                    <div className="text-sm text-green-700">
                                        Recent gecontacteerd. Wacht op reactie.
                                    </div>
                                )}

                                {stakeholderStatus === 'contacted_old' && (
                                    <div className="text-sm text-orange-700">
                                        Meer dan 1 uur geleden gecontacteerd. Mogelijk nog geen reactie ontvangen.
                                    </div>
                                )}

                                {stakeholderStatus === 'responded' && (
                                    <div className="text-sm text-green-700">
                                        Er is gereageerd op de verzonden e-mail.
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Right: Stakeholder Summary */}
                    <Card className="border-2">
                        <CardContent className="p-4 h-full flex flex-col">
                            <h2 className="text-lg font-semibold text-gray-900 mb-4">
                                Samenvatting
                            </h2>

                            <div className="flex-1 space-y-3 text-sm">
                                <div>
                                    <span className="font-medium text-gray-700">Totale vermeldingen:</span>{' '}
                                    <span className="text-gray-900">{unprocessedChunks.length + processedChunks.length}</span>
                                </div>
                                <div>
                                    <span className="font-medium text-gray-700">Geaccepteerd:</span>{' '}
                                    <span className="text-gray-900">{acceptedChunks.length}</span>
                                </div>
                                <div>
                                    <span className="font-medium text-gray-700">Documenten:</span>{' '}
                                    <span className="text-gray-900">{uniqueDocuments.size}</span>
                                </div>
                                <div>
                                    <span className="font-medium text-gray-700">Pagina's:</span>{' '}
                                    <span className="text-gray-900">{uniquePages.size}</span>
                                </div>
                                {stakeholder.contact_info && (
                                    <div>
                                        <span className="font-medium text-gray-700">Contact:</span>{' '}
                                        <span className="text-gray-900">{stakeholder.contact_info}</span>
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}

            {unprocessedChunks.length + processedChunks.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                    <p>Geen vermeldingen gevonden voor deze belanghebbende</p>
                </div>
            )}

            {/* Send Button */}
            {allProcessed && (
                <div className="flex justify-start">
                    <Button
                        onClick={() => setShowEmailSettingsModal(true)}
                        disabled={sendEmail.isPending || generatePDF.isPending}
                        className="h-11 px-8"
                        size="lg"
                    >
                        <Mail className="h-5 w-5 mr-2" />
                        Verstuur
                    </Button>
                </div>
            )}

            {/* Email Timeline */}
            {allProcessed && (
                <div className="pt-6 border-t">
                    <EmailTimeline emails={sentEmails} onEmailClick={handleEmailClick} />
                </div>
            )}

            {/* Email Settings Modal */}
            <Dialog open={showEmailSettingsModal} onOpenChange={setShowEmailSettingsModal}>
                <DialogContent className="max-w-2xl max-h-[90vh] overflow-auto">
                    <DialogHeader>
                        <DialogTitle>Verstuur E-mail of PDF</DialogTitle>
                        <DialogDescription>
                            Verstuur een e-mail of genereer een PDF voor {stakeholder.name}
                        </DialogDescription>
                    </DialogHeader>
                    <StakeholderEmailSettings
                        stakeholder={stakeholder}
                        caseId={caseId}
                        onSendEmail={async (data) => {
                            await handleSendEmail(data);
                            handleSendEmailSuccess();
                        }}
                        onGeneratePDF={handleGeneratePDF}
                        isSending={sendEmail.isPending}
                        isGeneratingPDF={generatePDF.isPending}
                    />
                </DialogContent>
            </Dialog>

            {/* PDF Preview Modal */}
            {generatedPDF && (
                <PDFPreview
                    pdfUrl={generatedPDF.url}
                    filename={generatedPDF.filename}
                    open={showPDFModal}
                    onOpenChange={(open) => {
                        setShowPDFModal(open);
                        if (!open && generatedPDF.url) {
                            // Clean up the blob URL when closing
                            window.URL.revokeObjectURL(generatedPDF.url);
                            setGeneratedPDF(null);
                        }
                    }}
                />
            )}

            {/* Email Replies Modal */}
            <EmailRepliesModal
                email={selectedEmail}
                open={showRepliesModal}
                onOpenChange={setShowRepliesModal}
            />

            <EmailAuthDialog
                open={showAuthDialog}
                onOpenChange={setShowAuthDialog}
                authUrl={emailAuth.data?.authUrl || null}
                onRetry={handleRetryEmail}
            />
        </div>
    );
}

