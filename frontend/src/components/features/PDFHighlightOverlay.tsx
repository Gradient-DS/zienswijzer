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

const COLORS = {
    default: '#000000',      // Black for default state
    selected: '#3B82F6',     // Blue for selected state
    accepted: '#10B981',     // Green for accepted state
    rejected: '#EF4444',     // Red for rejected state
};

function getHighlightStyle(mention: StakeholderMention, isSelected: boolean) {
    // Accepted state: green solid border with high opacity green fill
    if (mention.accepted) {
        return {
            stroke: COLORS.accepted,
            fill: `${COLORS.accepted}22`, // 80% opacity (CC in hex)
            strokeDasharray: '0',
            strokeWidth: 2,
        };
    }

    // Rejected state: red solid border with high opacity red fill
    if (mention.rejected) {
        return {
            stroke: COLORS.rejected,
            fill: `${COLORS.rejected}22`, // 80% opacity (CC in hex)
            strokeDasharray: '0',
            strokeWidth: 2,
        };
    }

    // Selected state: blue border, transparent fill (keeps area clickable)
    if (isSelected) {
        return {
            stroke: COLORS.selected,
            fill: 'transparent',
            strokeDasharray: '0',
            strokeWidth: 3,
        };
    }

    // Default state: black dashed border, transparent fill (keeps area clickable)
    return {
        stroke: COLORS.default,
        fill: 'transparent',
        strokeDasharray: '4 2',
        strokeWidth: 2,
    };
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
                const isSelected = selectedMentionId === mention.id;
                const style = getHighlightStyle(mention, isSelected);

                return (
                    <rect
                        key={mention.id}
                        x={mention.transformedBbox.x}
                        y={mention.transformedBbox.y}
                        width={mention.transformedBbox.width}
                        height={mention.transformedBbox.height}
                        fill={style.fill}
                        stroke={style.stroke}
                        strokeWidth={style.strokeWidth}
                        strokeDasharray={style.strokeDasharray}
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

