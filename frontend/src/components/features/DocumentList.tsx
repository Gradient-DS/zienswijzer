import type { Document } from '@/types';
import { FileText } from 'lucide-react';
import { cn } from '@/lib/utils';

interface DocumentListProps {
    documents: Document[];
    selectedDocumentId?: string;
    onSelectDocument: (documentId: string) => void;
    disabled?: boolean;
}

export function DocumentList({ documents, selectedDocumentId, onSelectDocument, disabled = false }: DocumentListProps) {
    if (documents.length === 0) {
        return (
            <div className="text-center py-8 text-muted-foreground">
                <p>Geen documenten beschikbaar</p>
            </div>
        );
    }

    return (
        <div className="space-y-1">
            {documents.map((document) => (
                <div
                    key={document.id}
                    className={cn(
                        'flex items-center gap-2 px-2 py-2 rounded-md transition-colors',
                        disabled
                            ? 'cursor-not-allowed opacity-60'
                            : 'cursor-pointer',
                        !disabled && selectedDocumentId === document.id
                            ? 'bg-gray-200 text-gray-900'
                            : !disabled
                                ? 'hover:bg-gray-100 text-gray-700'
                                : 'text-gray-500'
                    )}
                    onClick={() => !disabled && onSelectDocument(document.id)}
                >
                    <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium truncate">
                            {document.title}
                        </div>
                        <div className="flex items-center gap-2 mt-0.5">
                            {document.page_count && (
                                <span className="text-xs text-muted-foreground">
                                    {document.page_count} pagina{document.page_count !== 1 ? "'s" : ''}
                                </span>
                            )}
                            {document.parse_status && (
                                <span className={cn(
                                    'px-1.5 py-0.5 rounded text-xs font-medium',
                                    document.parse_status === 'completed' && 'bg-green-100 text-green-800',
                                    document.parse_status === 'processing' && 'bg-yellow-100 text-yellow-800',
                                    document.parse_status === 'pending' && 'bg-gray-100 text-gray-800',
                                    document.parse_status === 'failed' && 'bg-red-100 text-red-800'
                                )}>
                                    {document.parse_status}
                                </span>
                            )}
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}

