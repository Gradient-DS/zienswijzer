import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { Document as PDFDocument, Page as PDFPage, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';
import { useDocument } from '@/api/documents';
import { getDocumentPdfUrl } from '@/api/documents';
import { PDFHighlightOverlay } from './PDFHighlightOverlay';
import { ChunkStakeholderSidebar } from './ChunkStakeholderSidebar';
import { useUIStore } from '@/store';
import type { StakeholderMention } from '@/types';

pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';

interface PDFViewerProps {
    documentId: string;
    className?: string;
    onNextDocument?: () => void;
    allDocuments?: Array<{ id: string; chunks?: any[] }>;
    onNavigateToNextStep?: () => void;
}

interface PageDimensions {
    width: number;
    height: number;
}

export function PDFViewer({ documentId, className, onNextDocument, allDocuments, onNavigateToNextStep }: PDFViewerProps) {
    const [numPages, setNumPages] = useState<number>(0);
    const [scale, setScale] = useState<number>(1);
    const [containerWidth, setContainerWidth] = useState<number>(0);
    const [pageDimensions, setPageDimensions] = useState<Map<number, PageDimensions>>(new Map());
    const [selectedMentionId, setSelectedMentionId] = useState<string | null>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const scrollContainerRef = useRef<HTMLDivElement>(null);
    const pageRefs = useRef<Map<number, HTMLDivElement>>(new Map());
    const { id: caseId } = useParams<{ id: string }>();

    const { data: document, isLoading: documentLoading } = useDocument(documentId, caseId);
    const pdfUrl = getDocumentPdfUrl(documentId);
    const { isChunkSidebarOpen, setChunkSidebarOpen } = useUIStore();

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

    function onPageLoadSuccess(page: any, pageNum: number) {
        const viewport = page.getViewport({ scale: 1 });
        const dimensions = {
            width: viewport.width,
            height: viewport.height,
        };

        setPageDimensions((prev) => {
            const next = new Map(prev);
            next.set(pageNum, dimensions);
            return next;
        });

        if (containerWidth > 0 && viewport.width > 0) {
            const padding = 32;
            const availableWidth = containerWidth - padding;
            const calculatedScale = Math.min(availableWidth / viewport.width, 1.5);
            setScale(calculatedScale);
        }
    }

    useEffect(() => {
        if (pageDimensions.size > 0 && containerWidth > 0) {
            const firstPageDim = pageDimensions.values().next().value;
            if (firstPageDim) {
                const padding = 32;
                const availableWidth = containerWidth - padding;
                const calculatedScale = Math.min(availableWidth / firstPageDim.width, 1.5);
                setScale(calculatedScale);
            }
        }
    }, [containerWidth, pageDimensions]);

    const handleMentionClick = (mention: StakeholderMention) => {
        if (!document?.chunks) return;

        const chunkWithMention = document.chunks.find((c) =>
            c.stakeholder_mentions.some((m) => m.id === mention.id)
        );

        if (chunkWithMention) {
            setSelectedMentionId(mention.id);
            setChunkSidebarOpen(true);

            scrollToMention(chunkWithMention.page, mention);
        }
    };

    const scrollToMention = (targetPage: number, mention: StakeholderMention) => {
        setTimeout(() => {
            const scrollContainer = scrollContainerRef.current;
            const pageElement = pageRefs.current.get(targetPage);

            if (!scrollContainer || !pageElement) return;

            const pageDim = pageDimensions.get(targetPage);
            if (!pageDim) return;

            const bbox = mention.mention_bbox;
            const scaledY = bbox.y * scale;
            const scaledHeight = bbox.height * scale;

            const containerRect = scrollContainer.getBoundingClientRect();
            const pageRect = pageElement.getBoundingClientRect();

            const relativeY = pageRect.top - containerRect.top + scrollContainer.scrollTop + scaledY;
            const targetScrollTop = relativeY - containerRect.height / 2 + scaledHeight / 2;

            scrollContainer.scrollTo({
                top: Math.max(0, targetScrollTop),
                behavior: 'smooth',
            });
        }, 150);
    };

    useEffect(() => {
        if (!isChunkSidebarOpen && selectedMentionId) {
            setSelectedMentionId(null);
        }
    }, [isChunkSidebarOpen, selectedMentionId]);

    if (documentLoading) {
        return (
            <div className={`flex items-center justify-center h-full transition-opacity duration-300 ${className || ''}`}>
                <div className="flex flex-col items-center gap-3">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                    <div className="text-gray-500 text-sm">PDF laden...</div>
                </div>
            </div>
        );
    }

    return (
        <div className={`flex flex-col h-full transition-opacity duration-300 ${className || ''}`}>
            <div className="flex-1 flex overflow-hidden bg-gray-100">
                <div
                    className="flex-1 overflow-auto pdf-container"
                    ref={(el) => {
                        containerRef.current = el;
                        scrollContainerRef.current = el;
                    }}
                >
                    <div className="flex flex-col items-center py-4">
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
                            {Array.from({ length: numPages }, (_, i) => i + 1).map((pageNum) => {
                                const pageDim = pageDimensions.get(pageNum);
                                return (
                                    <div
                                        key={pageNum}
                                        ref={(el) => {
                                            if (el) {
                                                pageRefs.current.set(pageNum, el);
                                            } else {
                                                pageRefs.current.delete(pageNum);
                                            }
                                        }}
                                        className="relative mb-4"
                                        style={{ zIndex: 1 }}
                                    >
                                        <PDFPage
                                            pageNumber={pageNum}
                                            onLoadSuccess={(page) => onPageLoadSuccess(page, pageNum)}
                                            scale={scale}
                                            renderTextLayer={true}
                                            renderAnnotationLayer={true}
                                        />
                                        {document?.chunks && pageDim && (
                                            <PDFHighlightOverlay
                                                chunks={document.chunks}
                                                currentPage={pageNum}
                                                pageWidth={pageDim.width}
                                                pageHeight={pageDim.height}
                                                scale={scale}
                                                selectedMentionId={selectedMentionId}
                                                onMentionClick={handleMentionClick}
                                            />
                                        )}
                                    </div>
                                );
                            })}
                        </PDFDocument>
                    </div>
                </div>
                {isChunkSidebarOpen && (
                    <ChunkStakeholderSidebar
                        chunks={document?.chunks || []}
                        selectedMentionId={selectedMentionId}
                        onMentionClick={handleMentionClick}
                        onClose={() => {
                            setChunkSidebarOpen(false);
                            setSelectedMentionId(null);
                        }}
                        caseId={caseId}
                        onNextDocument={onNextDocument}
                        allDocuments={allDocuments}
                        onNavigateToNextStep={onNavigateToNextStep}
                    />
                )}
            </div>
        </div>
    );
}
