import type { Document } from '@/types';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { FileText } from 'lucide-react';
import { cn } from '@/lib/utils';

interface DocumentListProps {
    documents: Document[];
    selectedDocumentId?: string;
    onSelectDocument: (documentId: string) => void;
}

export function DocumentList({ documents, selectedDocumentId, onSelectDocument }: DocumentListProps) {
    if (documents.length === 0) {
        return (
            <div className="text-center py-8 text-muted-foreground">
                <p>Geen documenten beschikbaar</p>
            </div>
        );
    }

    return (
        <div className="space-y-2">
            {documents.map((document) => (
                <Card
                    key={document.id}
                    className={cn(
                        'cursor-pointer transition-all hover:shadow-md',
                        selectedDocumentId === document.id && 'border-primary shadow-sm'
                    )}
                    onClick={() => onSelectDocument(document.id)}
                >
                    <CardHeader className="pb-3">
                        <div className="flex items-start gap-3">
                            <FileText className="h-5 w-5 text-muted-foreground mt-0.5 flex-shrink-0" />
                            <div className="flex-1 min-w-0">
                                <CardTitle className="text-base font-semibold line-clamp-1">
                                    {document.title}
                                </CardTitle>
                                {document.description && (
                                    <CardDescription className="line-clamp-2 mt-1">
                                        {document.description}
                                    </CardDescription>
                                )}
                            </div>
                        </div>
                    </CardHeader>
                    <CardContent className="pt-0">
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            {document.pageCount && (
                                <span>{document.pageCount} pagina{document.pageCount !== 1 ? "'s" : ''}</span>
                            )}
                            {document.fileSize && (
                                <span>{(document.fileSize / 1024).toFixed(1)} KB</span>
                            )}
                            {document.processingStatus && (
                                <span className={cn(
                                    'px-2 py-0.5 rounded text-xs font-medium',
                                    document.processingStatus === 'completed' && 'bg-green-100 text-green-800',
                                    document.processingStatus === 'processing' && 'bg-yellow-100 text-yellow-800',
                                    document.processingStatus === 'pending' && 'bg-gray-100 text-gray-800',
                                    document.processingStatus === 'failed' && 'bg-red-100 text-red-800'
                                )}>
                                    {document.processingStatus}
                                </span>
                            )}
                        </div>
                    </CardContent>
                </Card>
            ))}
        </div>
    );
}

