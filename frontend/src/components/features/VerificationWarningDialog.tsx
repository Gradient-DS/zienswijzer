import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { AlertCircle, ExternalLink } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import type { ChunkDetail, StakeholderMention } from '@/types';

interface VerificationWarningDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    unverifiedMentions: Array<{ chunk: ChunkDetail; mention: StakeholderMention }>;
    documentTitles: Map<string, string>;
    onNavigateToChunk: (documentId: string, page: number) => void;
}

export function VerificationWarningDialog({
    open,
    onOpenChange,
    unverifiedMentions,
    documentTitles,
    onNavigateToChunk,
}: VerificationWarningDialogProps) {
    const handleNavigateToChunk = (chunk: ChunkDetail) => {
        onNavigateToChunk(chunk.document_id, chunk.page);
        onOpenChange(false);
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[600px] max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                    <div className="flex items-center gap-2">
                        <AlertCircle className="h-5 w-5 text-yellow-600" />
                        <DialogTitle>Niet alle vermeldingen zijn geverifieerd</DialogTitle>
                    </div>
                    <DialogDescription>
                        Er zijn {unverifiedMentions.length} vermelding{unverifiedMentions.length !== 1 ? 'en' : ''} die nog geverifieerd moeten worden voordat je een e-mail kunt versturen.
                    </DialogDescription>
                </DialogHeader>
                <div className="space-y-3 py-4">
                    {unverifiedMentions.map(({ chunk, mention }, index) => {
                        const documentTitle = documentTitles.get(chunk.document_id) || 'Onbekend document';
                        return (
                            <Card
                                key={`${chunk.id}-${mention.id}`}
                                className="border-2 cursor-pointer hover:shadow-md transition-all"
                                onClick={() => handleNavigateToChunk(chunk)}
                            >
                                <CardContent className="p-4">
                                    <div className="flex items-start justify-between gap-2">
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 mb-2">
                                                <span className="text-xs font-semibold text-gray-500">
                                                    #{index + 1}
                                                </span>
                                                <h4 className="font-semibold text-sm text-gray-900 truncate">
                                                    {documentTitle}
                                                </h4>
                                            </div>
                                            <p className="text-xs text-gray-500 mb-2">
                                                Pagina {chunk.page}
                                            </p>
                                            <div className="mb-2">
                                                <p className="text-xs font-medium text-gray-600 mb-1">
                                                    Vermelding:
                                                </p>
                                                <p className="text-sm text-gray-800 bg-gray-50 p-2 rounded border border-gray-200 italic">
                                                    "{mention.mention_text}"
                                                </p>
                                            </div>
                                            <div>
                                                <p className="text-xs font-medium text-gray-600 mb-1">
                                                    Context:
                                                </p>
                                                <p className="text-xs text-gray-700 bg-gray-50 p-2 rounded border border-gray-200 line-clamp-2">
                                                    {chunk.context}
                                                </p>
                                            </div>
                                        </div>
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleNavigateToChunk(chunk);
                                            }}
                                            className="h-8 flex-shrink-0"
                                        >
                                            <ExternalLink className="h-4 w-4 mr-1" />
                                            Bekijk
                                        </Button>
                                    </div>
                                </CardContent>
                            </Card>
                        );
                    })}
                </div>
            </DialogContent>
        </Dialog>
    );
}

