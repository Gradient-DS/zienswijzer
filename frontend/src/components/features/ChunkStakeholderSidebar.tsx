import { useMemo, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';
import type { ChunkDetail, StakeholderMention } from '@/types';
import { cn } from '@/lib/utils';

interface ChunkStakeholderSidebarProps {
    chunks: ChunkDetail[];
    selectedMentionId?: string | null;
    onMentionClick?: (mention: StakeholderMention) => void;
    onClose?: () => void;
    className?: string;
}

const STAKEHOLDER_COLORS: Record<string, string> = {
    organization: '#3B82F6',
    individual: '#10B981',
    government: '#F59E0B',
    community: '#8B5CF6',
    environmental: '#059669',
    default: '#6B7280',
};

function getStakeholderColor(type: string): string {
    return STAKEHOLDER_COLORS[type] || STAKEHOLDER_COLORS.default;
}

function ConfidenceBadge({ confidence }: { confidence: number }) {
    const percentage = Math.round(confidence * 100);
    const colorClass =
        confidence >= 0.9
            ? 'bg-green-500'
            : confidence >= 0.7
                ? 'bg-yellow-500'
                : 'bg-red-500';

    return (
        <span
            className={cn(
                'px-2 py-0.5 rounded text-xs font-semibold text-white',
                colorClass
            )}
        >
            {percentage}%
        </span>
    );
}

function VerificationBadge({ verified }: { verified: boolean }) {
    return (
        <span
            className={cn(
                'px-2 py-0.5 rounded text-xs font-medium',
                verified
                    ? 'bg-green-100 text-green-800 border border-green-300'
                    : 'bg-gray-100 text-gray-600 border border-gray-300'
            )}
        >
            {verified ? 'Geverifieerd' : 'Niet geverifieerd'}
        </span>
    );
}

export function ChunkStakeholderSidebar({
    chunks,
    selectedMentionId,
    onMentionClick,
    onClose,
    className,
}: ChunkStakeholderSidebarProps) {
    const sidebarRef = useRef<HTMLDivElement>(null);
    const cardRefs = useRef<Map<string, HTMLDivElement>>(new Map());

    const allMentions = useMemo(() => {
        const mentions: Array<{
            mention: StakeholderMention;
            chunk: ChunkDetail;
        }> = [];

        chunks.forEach((chunk) => {
            chunk.stakeholder_mentions.forEach((mention) => {
                mentions.push({ mention, chunk });
            });
        });

        return mentions.sort((a, b) => {
            if (a.chunk.page !== b.chunk.page) {
                return a.chunk.page - b.chunk.page;
            }
            const aY = a.mention.mention_bbox.y;
            const bY = b.mention.mention_bbox.y;
            const aX = a.mention.mention_bbox.x;
            const bX = b.mention.mention_bbox.x;

            if (aY !== bY) {
                return aY - bY;
            }
            return aX - bX;
        });
    }, [chunks]);

    const mentionsByPage = useMemo(() => {
        const grouped = new Map<number, typeof allMentions>();
        allMentions.forEach(({ mention, chunk }) => {
            if (!grouped.has(chunk.page)) {
                grouped.set(chunk.page, []);
            }
            grouped.get(chunk.page)!.push({ mention, chunk });
        });
        return grouped;
    }, [allMentions]);

    useEffect(() => {
        if (selectedMentionId && sidebarRef.current) {
            const cardElement = cardRefs.current.get(selectedMentionId);
            if (cardElement) {
                setTimeout(() => {
                    cardElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center',
                    });
                }, 100);
            }
        }
    }, [selectedMentionId, allMentions]);

    if (allMentions.length === 0) {
        return (
            <div
                className={cn(
                    'w-80 border-l bg-gray-100 overflow-y-auto',
                    className
                )}
            >
                <div className="p-4">
                    <div className="pb-2 border-b border-gray-300">
                        <div className="flex items-start justify-between gap-2">
                            <div className="flex-1">
                                <h3 className="text-sm font-semibold text-gray-700">
                                    Stakeholder vermeldingen
                                </h3>
                                <p className="text-xs text-gray-500 mt-1">
                                    Alle pagina's
                                </p>
                            </div>
                            {onClose && (
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-6 w-6 flex-shrink-0"
                                    onClick={onClose}
                                    aria-label="Sluit sidebar"
                                >
                                    <X className="h-4 w-4" />
                                </Button>
                            )}
                        </div>
                    </div>
                    <div className="flex items-center justify-center py-8">
                        <div className="text-sm text-gray-500 text-center">
                            Geen stakeholder vermeldingen gevonden
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div
            ref={sidebarRef}
            className={cn(
                'w-80 border-l bg-gray-100 overflow-y-auto',
                className
            )}
        >
            <div className="p-4 space-y-4">
                <div className="pb-2 border-b border-gray-300">
                    <div className="flex items-start justify-between gap-2">
                        <div className="flex-1">
                            <h3 className="text-sm font-semibold text-gray-700">
                                Stakeholder vermeldingen
                            </h3>
                            <p className="text-xs text-gray-500 mt-1">
                                {allMentions.length} {allMentions.length === 1 ? 'vermelding' : 'vermeldingen'} op {mentionsByPage.size} {mentionsByPage.size === 1 ? 'pagina' : 'pagina\'s'}
                            </p>
                        </div>
                        {onClose && (
                            <Button
                                variant="ghost"
                                size="icon"
                                className="h-6 w-6 flex-shrink-0"
                                onClick={onClose}
                                aria-label="Sluit sidebar"
                            >
                                <X className="h-4 w-4" />
                            </Button>
                        )}
                    </div>
                </div>

                {Array.from(mentionsByPage.entries()).map(([pageNum, mentions]) => (
                    <div key={pageNum} className="space-y-3">
                        <div className="sticky top-0 bg-gray-50 py-2 px-2 rounded border border-gray-200 -mx-2 z-10">
                            <h4 className="text-xs font-semibold text-gray-600">
                                Pagina {pageNum} • {mentions.length} {mentions.length === 1 ? 'vermelding' : 'vermeldingen'}
                            </h4>
                        </div>
                        {mentions.map(({ mention, chunk }) => {
                            const color = getStakeholderColor(mention.stakeholder.type);
                            const isSelected = selectedMentionId === mention.id;

                            return (
                                <Card
                                    key={mention.id}
                                    ref={(el) => {
                                        if (el) {
                                            cardRefs.current.set(mention.id, el);
                                        } else {
                                            cardRefs.current.delete(mention.id);
                                        }
                                    }}
                                    className={cn(
                                        'cursor-pointer hover:shadow-md transition-all border-2',
                                        isSelected && 'ring-2 ring-blue-500 ring-offset-2 shadow-lg'
                                    )}
                                    onClick={() => onMentionClick?.(mention)}
                                >
                                    <CardHeader className="pb-3">
                                        <div className="flex items-start justify-between gap-2">
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <div
                                                        className="w-3 h-3 rounded-full flex-shrink-0"
                                                        style={{ backgroundColor: color }}
                                                    />
                                                    <h4 className="font-semibold text-sm text-gray-900 truncate">
                                                        {mention.stakeholder.name}
                                                    </h4>
                                                </div>
                                                <p className="text-xs text-gray-500 capitalize">
                                                    {mention.stakeholder.type}
                                                </p>
                                            </div>
                                            <ConfidenceBadge confidence={mention.confidence} />
                                        </div>
                                    </CardHeader>
                                    <CardContent className="pt-0 space-y-2">
                                        <div>
                                            <p className="text-xs font-medium text-gray-600 mb-1">
                                                Vermelding:
                                            </p>
                                            <p className="text-sm text-gray-800 bg-gray-50 p-2 rounded border border-gray-200 italic">
                                                "{mention.mention_text}"
                                            </p>
                                        </div>
                                        <div className="flex items-center justify-between pt-1">
                                            <VerificationBadge verified={mention.verified} />
                                            <span className="text-xs text-gray-500">
                                                Pagina {chunk.page}
                                            </span>
                                        </div>
                                        {mention.stakeholder.contact_info && (
                                            <div className="pt-1 border-t border-gray-200">
                                                <p className="text-xs text-gray-500">
                                                    Contact: {mention.stakeholder.contact_info}
                                                </p>
                                            </div>
                                        )}
                                    </CardContent>
                                </Card>
                            );
                        })}
                    </div>
                ))}
            </div>
        </div>
    );
}

