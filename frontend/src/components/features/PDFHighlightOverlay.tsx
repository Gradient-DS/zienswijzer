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

function transformBbox(bbox: BoundingBox, scale: number): BoundingBox {
    return {
        x: bbox.x * scale,
        y: bbox.y * scale,
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
    const pageChunks = chunks.filter((chunk) => chunk.page === currentPage);

    if (pageChunks.length === 0) {
        return null;
    }

    const transformedChunks = pageChunks.map((chunk) => ({
        ...chunk,
        transformedBbox: transformBbox(chunk.bbox, scale),
        transformedMentions: chunk.stakeholder_mentions.map((mention) => ({
            ...mention,
            transformedBbox: transformBbox(mention.mention_bbox, scale),
        })),
    }));

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
            {transformedChunks.map((chunk) => (
                <g key={chunk.id}>
                    <rect
                        x={chunk.transformedBbox.x}
                        y={chunk.transformedBbox.y}
                        width={chunk.transformedBbox.width}
                        height={chunk.transformedBbox.height}
                        fill="rgba(0, 0, 0, 0.05)"
                        className="pointer-events-none"
                    />
                    {chunk.transformedMentions.map((mention) => {
                        const color = getHighlightColor(mention.stakeholder.type);
                        const opacity = getHighlightOpacity(mention.confidence);
                        const borderStyle = mention.verified ? 'solid' : 'dashed';
                        const isSelected = selectedMentionId === mention.id;

                        return (
                            <g key={mention.id}>
                                <rect
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
                            </g>
                        );
                    })}
                </g>
            ))}
        </svg>
    );
}

