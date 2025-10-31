import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Mail, RefreshCw, Clock, ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useEmailReplies, useSyncEmailReplies } from '@/api/email';
import type { SentEmail } from '@/types/email';
interface EmailTimelineProps {
    emails: SentEmail[];
    onEmailClick?: (email: SentEmail) => void;
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

function EmailItem({ email, onEmailClick }: { email: SentEmail; onEmailClick?: (email: SentEmail) => void }) {
    const [isExpanded, setIsExpanded] = useState(false);
    const { data: replies = [], refetch: refetchReplies } = useEmailReplies(email.id);
    const syncReplies = useSyncEmailReplies();

    const hasReplies = replies.length > 0;
    const isUnreadReplies = replies.some(r => !r.isRead);
    const isSyncing = syncReplies.isPending;

    const handleSyncReplies = async () => {
        try {
            await syncReplies.mutateAsync(email.id);
            refetchReplies();
        } catch (error) {
            console.error('Failed to sync replies:', error);
        }
    };

    return (
        <Card className="border-2 cursor-pointer hover:border-primary transition-colors" onClick={() => onEmailClick?.(email)}>
            <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                            <Mail className="h-4 w-4 text-gray-500 flex-shrink-0" />
                            <CardTitle className="text-base truncate">{email.subject}</CardTitle>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                            <span>Naar: {email.toRecipients.map(r => r.name || r.address).join(', ')}</span>
                            <span>•</span>
                            <span>{formatDate(email.sentAt)}</span>
                        </div>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                        {hasReplies && (
                            <span className={cn(
                                "px-2 py-1 rounded text-xs font-semibold",
                                isUnreadReplies ? "bg-blue-100 text-blue-700" : "bg-gray-100 text-gray-700"
                            )}>
                                {replies.length} {replies.length === 1 ? 'reactie' : 'reacties'}
                            </span>
                        )}
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                                e.stopPropagation();
                                setIsExpanded(!isExpanded);
                            }}
                            className="h-8"
                        >
                            {isExpanded ? (
                                <ChevronUp className="h-4 w-4" />
                            ) : (
                                <ChevronDown className="h-4 w-4" />
                            )}
                        </Button>
                    </div>
                </div>
            </CardHeader>
            {isExpanded && (
                <CardContent className="pt-0 space-y-4">
                    <div className="space-y-2">
                        <div className="text-sm">
                            <span className="font-medium">Onderwerp:</span> {email.subject}
                        </div>
                        <div className="text-sm">
                            <span className="font-medium">Ontvangers:</span>{' '}
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
                    </div>

                    <div className="flex gap-2">
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={handleSyncReplies}
                            disabled={isSyncing}
                            className="h-8"
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
                    </div>

                    {hasReplies && (
                        <div className="space-y-3 pt-2 border-t">
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
                                            <div className="text-gray-600 line-clamp-3">
                                                {reply.bodyPreview || reply.body || 'Geen preview beschikbaar'}
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    )}

                    {!hasReplies && (
                        <div className="text-center py-4 text-sm text-gray-500">
                            <Clock className="h-5 w-5 mx-auto mb-2 text-gray-400" />
                            <p>Nog geen reacties ontvangen</p>
                        </div>
                    )}
                </CardContent>
            )}
        </Card>
    );
}

export function EmailTimeline({ emails, onEmailClick }: EmailTimelineProps) {
    if (emails.length === 0) {
        return (
            <Card className="border-2">
                <CardContent className="py-8 text-center">
                    <Mail className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                    <p className="text-gray-600">Nog geen e-mails verzonden</p>
                </CardContent>
            </Card>
        );
    }

    const sortedEmails = [...emails].sort((a, b) =>
        new Date(b.sentAt).getTime() - new Date(a.sentAt).getTime()
    );

    return (
        <div className="space-y-4">
            <div className="flex items-center gap-2">
                <Mail className="h-5 w-5 text-gray-700" />
                <h2 className="text-lg font-semibold text-gray-900">
                    E-mail Timeline ({emails.length})
                </h2>
            </div>
            <div className="space-y-3">
                {sortedEmails.map((email) => (
                    <EmailItem key={email.id} email={email} onEmailClick={onEmailClick} />
                ))}
            </div>
        </div>
    );
}

