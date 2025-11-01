import type { ChunkDetail, StakeholderMention, BoundingBox } from '@/types';

interface PDFHighlightOverlayProps {
    chunks: ChunkDetail[];
    currentPage: number;
    pageWidth: number;
    pageHeight: number;
    scale: number;
    selectedMentionId?: string | null;
    onMentionClick?: (mention: StakeholderMention) => void;
}

const STAKEHOLDER_COLORS: Record<string, string> = {
    organization: '#3B82F6',
    individual: '#10B981',
    government: '#F59E0B',
    community: '#8B5CF6',
    environmental: '#059669',
    default: '#6B7280',
};

function getHighlightColor(stakeholderType: string): string {
    return STAKEHOLDER_COLORS[stakeholderType] || STAKEHOLDER_COLORS.default;
}

function getHighlightOpacity(confidence: number): number {
    return Math.max(0.3, confidence);
}

function transformBbox(bbox: BoundingBox, scale: number, pageHeight: number): BoundingBox {
    // All backend coordinates are now page-relative (0,0 = top-left of each page)
    // Simply scale them to match the rendered page size

    // Defensive clamping to prevent out-of-bounds highlights
    const clampedY = Math.max(0, Math.min(bbox.y, pageHeight));

    return {
        x: bbox.x * scale,
        y: clampedY * scale,
        width: bbox.width * scale,
        height: bbox.height * scale,
    };
}

export function PDFHighlightOverlay({
    chunks,
    currentPage,
    pageWidth,
    pageHeight,
    scale,
    selectedMentionId,
    onMentionClick,
}: PDFHighlightOverlayProps) {
    // Filter chunks for the current page
    const pageChunks = chunks.filter((chunk) => chunk.page === currentPage);

    if (pageChunks.length === 0) {
        return null;
    }

    // Debug: log chunk distribution (remove in production)
    if (import.meta.env.DEV) {
        const pageDistribution = chunks.reduce((acc, chunk) => {
            acc[chunk.page] = (acc[chunk.page] || 0) + 1;
            return acc;
        }, {} as Record<number, number>);
        console.log(`[PDFHighlightOverlay] Page ${currentPage}: ${pageChunks.length} chunks. Total distribution:`, pageDistribution);
    }

    // Flatten all mentions from all chunks on this page
    const allMentions = pageChunks.flatMap((chunk) =>
        chunk.stakeholder_mentions.map((mention) => ({
            ...mention,
            chunkPage: chunk.page, // Store chunk page for logging
            transformedBbox: transformBbox(mention.mention_bbox, scale, pageHeight),
        }))
    );

    // Debug: log individual mention coordinates (remove in production)
    if (import.meta.env.DEV && allMentions.length > 0) {
        console.log(`[PDFHighlightOverlay] Page ${currentPage} - Mentions (${allMentions.length}):`);
        allMentions.forEach((mention, idx) => {
            console.log(
                `  [${idx}] Mention ID: ${mention.id.substring(0, 8)}... | ` +
                `Chunk Page: ${mention.chunkPage} | ` +
                `Original bbox: (x:${mention.mention_bbox.x.toFixed(1)}, y:${mention.mention_bbox.y.toFixed(1)}, ` +
                `w:${mention.mention_bbox.width.toFixed(1)}, h:${mention.mention_bbox.height.toFixed(1)}) | ` +
                `Transformed: (x:${mention.transformedBbox.x.toFixed(1)}, y:${mention.transformedBbox.y.toFixed(1)}, ` +
                `w:${mention.transformedBbox.width.toFixed(1)}, h:${mention.transformedBbox.height.toFixed(1)})`
            );
        });
    }

    const scaledWidth = pageWidth * scale;
    const scaledHeight = pageHeight * scale;

    return (
        <svg
            className="absolute top-0 left-0 pointer-events-none z-10"
            width={scaledWidth}
            height={scaledHeight}
            style={{ pointerEvents: 'auto', zIndex: 10 }}
            viewBox={`0 0 ${scaledWidth} ${scaledHeight}`}
        >
            {allMentions.map((mention) => {
                const color = getHighlightColor(mention.stakeholder.type);
                const opacity = getHighlightOpacity(mention.confidence);
                const borderStyle = mention.checked ? 'solid' : 'dashed';
                const isSelected = selectedMentionId === mention.id;

                return (
                    <rect
                        key={mention.id}
                        x={mention.transformedBbox.x}
                        y={mention.transformedBbox.y}
                        width={mention.transformedBbox.width}
                        height={mention.transformedBbox.height}
                        fill={`${color}${Math.round(opacity * 255).toString(16).padStart(2, '0')}`}
                        stroke={isSelected ? '#3B82F6' : color}
                        strokeWidth={isSelected ? 4 : 2}
                        strokeDasharray={borderStyle === 'dashed' ? '4 2' : '0'}
                        style={{ cursor: 'pointer' }}
                        onClick={() => onMentionClick?.(mention)}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.opacity = '1';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.opacity = '';
                        }}
                        aria-label={`Stakeholder: ${mention.stakeholder.name} (${Math.round(mention.confidence * 100)}% confidence)`}
                    />
                );
            })}
        </svg>
    );
}

