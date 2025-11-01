import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { RefreshCw, Mail, Clock } from 'lucide-react';
import { useEmailReplies, useSyncEmailReplies } from '@/api/email';
import type { SentEmail } from '@/types/email';

interface EmailRepliesModalProps {
    email: SentEmail | null;
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

function formatDate(dateString: string): string {
    try {
        const date = new Date(dateString);
        const day = date.getDate();
        const month = date.toLocaleDateString('nl-NL', { month: 'short' });
        const year = date.getFullYear();
        const hours = date.getHours().toString().padStart(2, '0');
        const minutes = date.getMinutes().toString().padStart(2, '0');
        return `${day} ${month} ${year}, ${hours}:${minutes}`;
    } catch {
        return dateString;
    }
}

function stripImages(html: string): string {
    return html.replace(/<img[^>]*>/gi, '');
}

export function EmailRepliesModal({ email, open, onOpenChange }: EmailRepliesModalProps) {
    const { data: replies = [], refetch: refetchReplies } = useEmailReplies(email?.id);
    const syncReplies = useSyncEmailReplies();

    const hasReplies = replies.length > 0;
    const isUnreadReplies = replies.some(r => !r.isRead);
    const isSyncing = syncReplies.isPending;

    const handleSyncReplies = async () => {
        if (!email) return;
        try {
            await syncReplies.mutateAsync(email.id);
            refetchReplies();
        } catch (error) {
            console.error('Failed to sync replies:', error);
        }
    };

    if (!email) return null;

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <Mail className="h-5 w-5 text-gray-600" />
                        E-mail Reacties
                    </DialogTitle>
                    <DialogDescription>
                        {email.subject} - Verzonden op {formatDate(email.sentAt)}
                    </DialogDescription>
                </DialogHeader>

                <div className="flex-1 overflow-auto space-y-4 py-4">
                    <Card className="border-2 bg-blue-50">
                        <CardContent className="p-4 space-y-2">
                            <div className="text-sm">
                                <span className="font-medium">Onderwerp:</span> {email.subject}
                            </div>
                            <div className="text-sm">
                                <span className="font-medium">Naar:</span>{' '}
                                {email.toRecipients.map(r => r.name || r.address).join(', ')}
                            </div>
                            {email.ccRecipients && email.ccRecipients.length > 0 && (
                                <div className="text-sm">
                                    <span className="font-medium">CC:</span>{' '}
                                    {email.ccRecipients.map(r => r.name || r.address).join(', ')}
                                </div>
                            )}
                            <div className="text-sm">
                                <span className="font-medium">Verzonden:</span> {formatDate(email.sentAt)}
                            </div>
                        </CardContent>
                    </Card>

                    <div className="flex gap-2">
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={handleSyncReplies}
                            disabled={isSyncing}
                        >
                            {isSyncing ? (
                                <>
                                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                                    Synchroniseren...
                                </>
                            ) : (
                                <>
                                    <RefreshCw className="h-4 w-4 mr-2" />
                                    Synchroniseer Reacties
                                </>
                            )}
                        </Button>
                        {hasReplies && (
                            <span className="px-3 py-1.5 rounded text-sm font-semibold bg-gray-100 text-gray-700 self-center">
                                {replies.length} {replies.length === 1 ? 'reactie' : 'reacties'}
                                {isUnreadReplies && ' (nieuwe)'}
                            </span>
                        )}
                    </div>

                    {hasReplies && (
                        <div className="space-y-3">
                            <h4 className="text-sm font-semibold text-gray-900">
                                Reacties ({replies.length})
                            </h4>
                            {replies.map((reply) => (
                                <Card key={reply.id} className="bg-gray-50 border">
                                    <CardContent className="p-4 space-y-2">
                                        <div className="flex items-start justify-between gap-2">
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <Mail className="h-3 w-3 text-gray-500" />
                                                    <span className="text-sm font-medium">
                                                        {reply.fromAddress.name || reply.fromAddress.address}
                                                    </span>
                                                    {!reply.isRead && (
                                                        <span className="px-1.5 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-700">
                                                            Nieuw
                                                        </span>
                                                    )}
                                                </div>
                                                <div className="text-xs text-gray-600">
                                                    {formatDate(reply.receivedAt)}
                                                </div>
                                            </div>
                                        </div>
                                        <div className="text-sm text-gray-700">
                                            <div className="font-medium mb-1">{reply.subject}</div>
                                            {reply.body ? (
                                                <div
                                                    className="prose prose-sm max-w-none text-gray-600"
                                                    dangerouslySetInnerHTML={{ __html: stripImages(reply.body) }}
                                                />
                                            ) : (
                                                <div className="text-gray-600 whitespace-pre-wrap">
                                                    {reply.bodyPreview || 'Geen preview beschikbaar'}
                                                </div>
                                            )}
                                        </div>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    )}

                    {!hasReplies && (
                        <div className="text-center py-8 text-sm text-gray-500">
                            <Clock className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                            <p>Nog geen reacties ontvangen</p>
                        </div>
                    )}
                </div>

                <div className="flex justify-end pt-4 border-t">
                    <Button onClick={() => onOpenChange(false)} variant="outline">
                        Sluiten
                    </Button>
                </div>
            </DialogContent>
        </Dialog>
    );
}

