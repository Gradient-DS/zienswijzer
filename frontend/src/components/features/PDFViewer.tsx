import { useState, useEffect, useRef } from 'react';
import { Document as PDFDocument, Page as PDFPage, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';
import { useDocument } from '@/api/documents';
import { getDocumentPdfUrl } from '@/api/documents';
import { PDFHighlightOverlay } from './PDFHighlightOverlay';
import { ChunkStakeholderSidebar } from './ChunkStakeholderSidebar';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useUIStore } from '@/store';
import type { StakeholderMention } from '@/types';

pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';

interface PDFViewerProps {
    documentId: string;
    className?: string;
}

export function PDFViewer({ documentId, className }: PDFViewerProps) {
    const [numPages, setNumPages] = useState<number>(0);
    const [pageNumber, setPageNumber] = useState<number>(1);
    const [pageWidth, setPageWidth] = useState<number>(0);
    const [pageHeight, setPageHeight] = useState<number>(0);
    const [scale, setScale] = useState<number>(1);
    const [containerWidth, setContainerWidth] = useState<number>(0);
    const [selectedMentionId, setSelectedMentionId] = useState<string | null>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    const { data: document, isLoading: documentLoading } = useDocument(documentId);
    const pdfUrl = getDocumentPdfUrl(documentId);
    const { isChunkSidebarOpen, setChunkSidebarOpen } = useUIStore();

    useEffect(() => {
        console.log('isChunkSidebarOpen changed:', isChunkSidebarOpen, 'selectedMentionId:', selectedMentionId);
    }, [isChunkSidebarOpen, selectedMentionId]);

    useEffect(() => {
        const updateContainerWidth = () => {
            if (containerRef.current) {
                setContainerWidth(containerRef.current.clientWidth);
            }
        };

        updateContainerWidth();
        window.addEventListener('resize', updateContainerWidth);
        return () => window.removeEventListener('resize', updateContainerWidth);
    }, []);

    function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
        setNumPages(numPages);
    }

    function onPageLoadSuccess(page: any) {
        const viewport = page.getViewport({ scale: 1 });
        setPageWidth(viewport.width);
        setPageHeight(viewport.height);

        if (containerWidth > 0 && viewport.width > 0) {
            const padding = 32;
            const availableWidth = containerWidth - padding;
            const calculatedScale = Math.min(availableWidth / viewport.width, 1.5);
            setScale(calculatedScale);
        }
    }

    useEffect(() => {
        if (pageWidth > 0 && containerWidth > 0) {
            const padding = 32;
            const availableWidth = containerWidth - padding;
            const calculatedScale = Math.min(availableWidth / pageWidth, 1.5);
            setScale(calculatedScale);
        }
    }, [containerWidth, pageWidth]);

    function goToPrevPage() {
        setPageNumber((prev) => Math.max(1, prev - 1));
    }

    function goToNextPage() {
        setPageNumber((prev) => Math.min(numPages, prev + 1));
    }

    const handleMentionClick = (mention: StakeholderMention) => {
        if (selectedMentionId === mention.id && isChunkSidebarOpen) {
            setSelectedMentionId(null);
            setChunkSidebarOpen(false);
        } else {
            setSelectedMentionId(mention.id);
            setChunkSidebarOpen(true);
        }
    };

    useEffect(() => {
        if (!isChunkSidebarOpen && selectedMentionId) {
            setSelectedMentionId(null);
        }
    }, [isChunkSidebarOpen, selectedMentionId]);

    useEffect(() => {
        if (selectedMentionId && document?.chunks && isChunkSidebarOpen && document.chunks.length > 0) {
            const chunkWithMention = document.chunks.find((c) =>
                c.stakeholderMentions.some((m) => m.id === selectedMentionId)
            );

            if (chunkWithMention && chunkWithMention.page !== pageNumber) {
                setSelectedMentionId(null);
                setChunkSidebarOpen(false);
            }
        }
    }, [pageNumber, document?.chunks, selectedMentionId, isChunkSidebarOpen, setChunkSidebarOpen]);

    if (documentLoading) {
        return (
            <div className={`flex items-center justify-center h-full ${className || ''}`}>
                <div className="text-gray-500">PDF laden...</div>
            </div>
        );
    }

    return (
        <div className={`flex flex-col h-full ${className || ''}`}>
            <div className="flex items-center justify-between p-4 border-b bg-white">
                <div className="flex items-center gap-2">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={goToPrevPage}
                        disabled={pageNumber <= 1}
                    >
                        <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <span className="text-sm text-gray-700">
                        Pagina {pageNumber} van {numPages}
                    </span>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={goToNextPage}
                        disabled={pageNumber >= numPages}
                    >
                        <ChevronRight className="h-4 w-4" />
                    </Button>
                </div>
            </div>

            <div className="flex-1 flex overflow-hidden bg-gray-100">
                <div className="flex-1 overflow-auto pdf-container" ref={containerRef}>
                    <div className="flex justify-center p-4">
                        <div className="relative">
                            <PDFDocument
                                file={pdfUrl}
                                onLoadSuccess={onDocumentLoadSuccess}
                                loading={
                                    <div className="flex items-center justify-center p-8">
                                        <div className="text-gray-500">PDF laden...</div>
                                    </div>
                                }
                                error={
                                    <div className="flex items-center justify-center p-8">
                                        <div className="text-red-500">Fout bij het laden van de PDF</div>
                                    </div>
                                }
                            >
                                <div className="relative" style={{ zIndex: 1 }}>
                                    <PDFPage
                                        pageNumber={pageNumber}
                                        onLoadSuccess={onPageLoadSuccess}
                                        scale={scale}
                                        renderTextLayer={true}
                                        renderAnnotationLayer={true}
                                    />
                                    {document?.chunks && pageWidth > 0 && pageHeight > 0 && (
                                        <PDFHighlightOverlay
                                            chunks={document.chunks}
                                            currentPage={pageNumber}
                                            pageWidth={pageWidth}
                                            pageHeight={pageHeight}
                                            scale={scale}
                                            selectedMentionId={selectedMentionId}
                                            onMentionClick={handleMentionClick}
                                        />
                                    )}
                                </div>
                            </PDFDocument>
                        </div>
                    </div>
                </div>
                {isChunkSidebarOpen && (
                    <ChunkStakeholderSidebar
                        chunks={document?.chunks || []}
                        currentPage={pageNumber}
                        selectedMentionId={selectedMentionId}
                        onMentionClick={handleMentionClick}
                        onClose={() => {
                            setChunkSidebarOpen(false);
                            setSelectedMentionId(null);
                        }}
                    />
                )}
            </div>
        </div>
    );
}
