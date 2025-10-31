import { useState } from 'react';
import { Document as PDFDocument, Page as PDFPage, pdfjs } from 'react-pdf';
import { Download, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';

interface PDFPreviewProps {
    pdfUrl: string;
    filename: string;
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

export function PDFPreview({ pdfUrl, filename, open, onOpenChange }: PDFPreviewProps) {
    const [numPages, setNumPages] = useState<number>(0);
    const scale = 0.5; // Smaller scale for preview

    function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
        setNumPages(numPages);
    }

    const handleDownload = () => {
        const link = document.createElement('a');
        link.href = pdfUrl;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <FileText className="h-5 w-5 text-gray-600" />
                        PDF Preview
                        {numPages > 0 && (
                            <span className="text-sm font-normal text-gray-500">
                                ({numPages} pagina{numPages !== 1 ? "'s" : ""})
                            </span>
                        )}
                    </DialogTitle>
                    <DialogDescription>
                        Bekijk een preview van de gegenereerde PDF
                    </DialogDescription>
                </DialogHeader>

                <div className="flex-1 overflow-auto border border-gray-200 rounded bg-gray-50 p-4">
                    <div className="flex flex-col items-center">
                        <PDFDocument
                            file={pdfUrl}
                            onLoadSuccess={onDocumentLoadSuccess}
                            loading={
                                <div className="flex items-center justify-center p-8">
                                    <div className="text-sm text-gray-500">PDF laden...</div>
                                </div>
                            }
                            error={
                                <div className="flex items-center justify-center p-8">
                                    <div className="text-sm text-red-500">Fout bij het laden van de PDF</div>
                                </div>
                            }
                        >
                            {Array.from({ length: Math.min(numPages, 3) }, (_, i) => i + 1).map((pageNum) => (
                                <div key={pageNum} className="mb-2 shadow-sm">
                                    <PDFPage
                                        pageNumber={pageNum}
                                        scale={scale}
                                        renderTextLayer={false}
                                        renderAnnotationLayer={false}
                                    />
                                </div>
                            ))}
                        </PDFDocument>
                        {numPages > 3 && (
                            <div className="text-xs text-gray-500 mt-2">
                                ... en {numPages - 3} meer pagina{numPages - 3 !== 1 ? "'s" : ""}
                            </div>
                        )}
                    </div>
                </div>

                <div className="flex gap-3 pt-4 border-t">
                    <Button
                        onClick={handleDownload}
                        variant="default"
                        className="flex-1"
                    >
                        <Download className="h-4 w-4 mr-2" />
                        Download volledige PDF ({numPages} pagina{numPages !== 1 ? "'s" : ""})
                    </Button>
                    <Button
                        onClick={() => onOpenChange(false)}
                        variant="outline"
                    >
                        Sluiten
                    </Button>
                </div>
            </DialogContent>
        </Dialog>
    );
}

