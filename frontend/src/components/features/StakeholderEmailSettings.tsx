import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Mail, FileText, Loader2 } from 'lucide-react';
import type { ContentType, EmailAddress } from '@/types/email';
import type { Stakeholder } from '@/types';

interface StakeholderEmailSettingsProps {
    stakeholder: Stakeholder;
    caseId?: string;
    onSendEmail: (data: {
        to: EmailAddress[];
        subject: string;
        content_type: ContentType;
        custom_message?: string;
    }) => Promise<void>;
    onGeneratePDF: (data: {
        content_type: ContentType;
    }) => Promise<void>;
    isSending?: boolean;
    isGeneratingPDF?: boolean;
}

export function StakeholderEmailSettings({
    stakeholder,
    onSendEmail,
    onGeneratePDF,
    isSending = false,
    isGeneratingPDF = false,
}: StakeholderEmailSettingsProps) {
    const [contentType, setContentType] = useState<ContentType>('chunks_only');
    const [recipientEmail, setRecipientEmail] = useState(stakeholder.contact_info || '');
    const [recipientName, setRecipientName] = useState(stakeholder.name);
    const [subject, setSubject] = useState(`WOO Verzoek - ${stakeholder.name}`);
    const [customMessage, setCustomMessage] = useState('');

    const handleSendEmail = async () => {
        if (!recipientEmail.trim()) {
            alert('Voer een e-mailadres in');
            return;
        }

        const to: EmailAddress[] = [{
            address: recipientEmail.trim(),
            name: recipientName.trim() || undefined,
        }];

        try {
            await onSendEmail({
                to,
                subject: subject.trim() || `WOO Verzoek - ${stakeholder.name}`,
                content_type: contentType,
                custom_message: customMessage.trim() || undefined,
            });
        } catch (error: any) {
            // Error handling is done in parent component
            if (error.message !== 'EMAIL_AUTH_REQUIRED') {
                throw error;
            }
        }
    };

    const handleGeneratePDF = async () => {
        await onGeneratePDF({
            content_type: contentType,
        });
    };

    return (
        <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Email of PDF versturen</h3>

            <div className="space-y-2">
                <Label className="text-sm font-medium">Inhoud Type</Label>
                <div className="flex gap-3">
                    <label className="flex items-center gap-1.5 cursor-pointer">
                        <input
                            type="radio"
                            name="content_type"
                            value="full_documents"
                            checked={contentType === 'full_documents'}
                            onChange={(e) => setContentType(e.target.value as ContentType)}
                            className="w-4 h-4 text-primary focus:ring-2 focus:ring-ring"
                        />
                        <span className="text-xs whitespace-nowrap">Volledige documenten</span>
                    </label>
                    <label className="flex items-center gap-1.5 cursor-pointer">
                        <input
                            type="radio"
                            name="content_type"
                            value="pages_only"
                            checked={contentType === 'pages_only'}
                            onChange={(e) => setContentType(e.target.value as ContentType)}
                            className="w-4 h-4 text-primary focus:ring-2 focus:ring-ring"
                        />
                        <span className="text-xs whitespace-nowrap">Alleen pagina's</span>
                    </label>
                    <label className="flex items-center gap-1.5 cursor-pointer">
                        <input
                            type="radio"
                            name="content_type"
                            value="chunks_only"
                            checked={contentType === 'chunks_only'}
                            onChange={(e) => setContentType(e.target.value as ContentType)}
                            className="w-4 h-4 text-primary focus:ring-2 focus:ring-ring"
                        />
                        <span className="text-xs whitespace-nowrap">Alleen chunks</span>
                    </label>
                </div>
            </div>

            <div className="space-y-2">
                <Label htmlFor="recipient-name" className="text-sm font-medium">Naam</Label>
                <Input
                    id="recipient-name"
                    type="text"
                    value={recipientName}
                    onChange={(e) => setRecipientName(e.target.value)}
                    placeholder="Naam"
                    disabled={isSending || isGeneratingPDF}
                    className="h-9"
                />
            </div>

            <div className="space-y-2">
                <Label htmlFor="recipient-email" className="text-sm font-medium">
                    E-mail <span className="text-destructive">*</span>
                </Label>
                <Input
                    id="recipient-email"
                    type="email"
                    value={recipientEmail}
                    onChange={(e) => setRecipientEmail(e.target.value)}
                    placeholder="email@voorbeeld.nl"
                    required
                    disabled={isSending || isGeneratingPDF}
                    className="h-9"
                />
            </div>

            <div className="space-y-2">
                <Label htmlFor="subject" className="text-sm font-medium">Onderwerp</Label>
                <Input
                    id="subject"
                    type="text"
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    placeholder="Onderwerp"
                    disabled={isSending || isGeneratingPDF}
                    className="h-9"
                />
            </div>

            <div className="space-y-2">
                <Label htmlFor="custom-message" className="text-sm font-medium">Aangepast bericht (optioneel)</Label>
                <textarea
                    id="custom-message"
                    value={customMessage}
                    onChange={(e) => setCustomMessage(e.target.value)}
                    placeholder="Optioneel: voeg een persoonlijk bericht toe..."
                    rows={3}
                    className="flex w-full rounded-md border-2 border-input bg-background px-4 py-2 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-muted resize-none"
                    disabled={isSending || isGeneratingPDF}
                />
            </div>

            <div className="flex gap-3 pt-2">
                <Button
                    onClick={handleSendEmail}
                    disabled={isSending || isGeneratingPDF || !recipientEmail.trim()}
                    className="flex-1"
                >
                    {isSending ? (
                        <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            Verzenden...
                        </>
                    ) : (
                        <>
                            <Mail className="h-4 w-4 mr-2" />
                            Verstuur E-mail
                        </>
                    )}
                </Button>
                <Button
                    onClick={handleGeneratePDF}
                    variant="outline"
                    disabled={isSending || isGeneratingPDF}
                    className="flex-1"
                >
                    {isGeneratingPDF ? (
                        <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            Genereren...
                        </>
                    ) : (
                        <>
                            <FileText className="h-4 w-4 mr-2" />
                            Genereer PDF
                        </>
                    )}
                </Button>
            </div>
        </div>
    );
}

