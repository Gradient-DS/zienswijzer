import type { Document } from '@/types';
import { FileText, Check, Loader2 } from 'lucide-react';
import { useDocumentCompletionStatus, useDocumentProcessingStatus } from '@/api/cases';
import { cn } from '@/lib/utils';

interface DocumentListProps {
    documents: Document[];
    selectedDocumentId?: string;
    onSelectDocument: (documentId: string) => void;
    disabled?: boolean;
    caseId?: string;
}

export function DocumentList({ documents, selectedDocumentId, onSelectDocument, disabled = false, caseId }: DocumentListProps) {
    const { data: completionStatus } = useDocumentCompletionStatus(caseId);
    const { data: processingStatus } = useDocumentProcessingStatus(caseId);

    if (documents.length === 0) {
        return (
            <div className="text-center py-8 text-muted-foreground">
                <p>Geen documenten beschikbaar</p>
            </div>
        );
    }

    return (
        <div className="space-y-1">
            {documents.map((document) => {
                const allChecked = completionStatus?.get(document.id) ?? false;
                const isProcessing = processingStatus?.get(document.id) ?? true;

                // Debug logging
                if (import.meta.env.DEV && isProcessing) {
                    console.log('[DocumentList] Document still processing:', {
                        id: document.id.substring(0, 8),
                        parse_status: document.parse_status,
                        page_count: document.page_count,
                        isProcessing: isProcessing,
                        processingStatus: processingStatus?.get(document.id)
                    });
                }

                return (
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
                        {isProcessing ? (
                            <Loader2 className="h-4 w-4 text-muted-foreground flex-shrink-0 animate-spin" />
                        ) : (
                            <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                        )}
                        <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                                <div className="text-sm font-medium truncate">
                                    {document.title}
                                </div>
                                {allChecked && !isProcessing && (
                                    <Check className="h-5 w-5 text-green-600 flex-shrink-0" />
                                )}
                            </div>
                            <div className="flex items-center gap-2 mt-0.5">
                                {isProcessing ? (
                                    <span className="text-xs text-yellow-700 font-medium animate-pulse">
                                        Verwerken...
                                    </span>
                                ) : (
                                    document.page_count && document.page_count > 0 && (
                                        <span className="text-xs text-muted-foreground">
                                            {document.page_count} pagina{document.page_count !== 1 ? "'s" : ''}
                                        </span>
                                    )
                                )}
                            </div>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}

