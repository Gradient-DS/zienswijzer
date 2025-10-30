import { getDocumentPdfUrl } from '@/api/documents';

interface PDFViewerProps {
    documentId: string;
    className?: string;
}

export function PDFViewer({ documentId, className }: PDFViewerProps) {
    const pdfUrl = getDocumentPdfUrl(documentId);

    return (
        <div className={`w-full h-full ${className || ''}`}>
            <iframe
                src={pdfUrl}
                className="w-full h-full border-0"
                title="PDF Viewer"
                aria-label="PDF document viewer"
            />
        </div>
    );
}

