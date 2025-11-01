import { useMemo, useEffect, useRef, useState, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { X, Trash2, ArrowDown, ArrowUp, ArrowRight, Check } from 'lucide-react';
import { useVerifyMention, useRemoveMention, useBulkAcceptMentions } from '@/api/verification';
import { useDocumentCompletionStatus, useCase } from '@/api/cases';
import type { ChunkDetail, StakeholderMention } from '@/types';
import { cn } from '@/lib/utils';

interface ChunkStakeholderSidebarProps {
    chunks: ChunkDetail[];
    selectedMentionId?: string | null;
    onMentionClick?: (mention: StakeholderMention) => void;
    onClose?: () => void;
    className?: string;
    caseId?: string;
    onNextDocument?: () => void;
    allDocuments?: Array<{ id: string; chunks?: ChunkDetail[] }>;
    onNavigateToNextStep?: () => void;
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

function AcceptRejectButtons({
    accepted,
    rejected,
    onAccept,
    onReject,
    onRemove,
}: {
    accepted: boolean;
    rejected: boolean;
    onAccept: () => void;
    onReject: () => void;
    onRemove?: () => void;
}) {
    return (
        <div className="flex items-center">
            <div className="flex border-2 border-border rounded-md overflow-hidden shadow-sm">
                <Button
                    onClick={(e) => {
                        e.stopPropagation();
                        onAccept();
                    }}
                    variant="outline"
                    size="sm"
                    className={cn(
                        'rounded-none border-0 text-xs flex-1 h-8 font-medium',
                        accepted
                            ? 'bg-green-600 hover:bg-green-700 text-white border-0'
                            : 'bg-white hover:bg-gray-100 text-gray-900 border-r border-border'
                    )}
                >
                    Accepteer
                </Button>
                <div className="h-8 w-px bg-border flex-shrink-0" />
                <Button
                    onClick={(e) => {
                        e.stopPropagation();
                        onReject();
                    }}
                    variant="outline"
                    size="sm"
                    className={cn(
                        'rounded-none border-0 text-xs flex-1 h-8 font-medium',
                        rejected
                            ? 'bg-red-600 hover:bg-red-700 text-white border-0'
                            : 'bg-white hover:bg-gray-100 text-gray-900'
                    )}
                >
                    Weiger
                </Button>
            </div>
            {rejected && onRemove && (
                <>
                    <div className="w-2" />
                    <Button
                        onClick={(e) => {
                            e.stopPropagation();
                            onRemove();
                        }}
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
                        aria-label="Verwijder vermelding"
                    >
                        <Trash2 className="h-4 w-4" />
                    </Button>
                </>
            )}
        </div>
    );
}

export function ChunkStakeholderSidebar({
    chunks,
    selectedMentionId,
    onMentionClick,
    onClose,
    className,
    caseId,
    onNextDocument,
    allDocuments,
    onNavigateToNextStep,
}: ChunkStakeholderSidebarProps) {
    const sidebarRef = useRef<HTMLDivElement>(null);
    const cardRefs = useRef<Map<string, HTMLDivElement>>(new Map());
    const verifyMention = useVerifyMention();
    const bulkAcceptMentions = useBulkAcceptMentions();
    const location = useLocation();
    const resolvedCaseId = caseId || location.pathname.match(/\/cases\/([^/]+)/)?.[1];
    const { data: caseData } = useCase(resolvedCaseId);
    const { data: documentCompletionStatus } = useDocumentCompletionStatus(resolvedCaseId);
    const [bulkThreshold, setBulkThreshold] = useState(70);
    const [isBulkAccepting, setIsBulkAccepting] = useState(false);

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

    const uncheckedMentions = useMemo(() => {
        return allMentions.filter(({ mention }) => !mention.checked);
    }, [allMentions]);

    const getNextUncheckedMention = useCallback((currentMentionId?: string, wrapAround: boolean = false): StakeholderMention | null => {
        const startIndex = currentMentionId
            ? allMentions.findIndex(({ mention }) => mention.id === currentMentionId) + 1
            : 0;

        // Search forward from current position
        for (let i = startIndex; i < allMentions.length; i++) {
            if (!allMentions[i].mention.checked) {
                return allMentions[i].mention;
            }
        }

        // If wrapAround is true and we didn't find anything, search from the beginning
        if (wrapAround) {
            for (let i = 0; i < startIndex; i++) {
                if (!allMentions[i].mention.checked) {
                    return allMentions[i].mention;
                }
            }
        }

        return null;
    }, [allMentions]);

    const getPreviousUncheckedMention = useCallback((currentMentionId?: string, wrapAround: boolean = false): StakeholderMention | null => {
        const startIndex = currentMentionId
            ? allMentions.findIndex(({ mention }) => mention.id === currentMentionId) - 1
            : allMentions.length - 1;

        // Search backward from current position
        for (let i = startIndex; i >= 0; i--) {
            if (!allMentions[i].mention.checked) {
                return allMentions[i].mention;
            }
        }

        // If wrapAround is true and we didn't find anything, search from the end
        if (wrapAround) {
            for (let i = allMentions.length - 1; i > startIndex; i--) {
                if (!allMentions[i].mention.checked) {
                    return allMentions[i].mention;
                }
            }
        }

        return null;
    }, [allMentions]);

    const handleJumpToPreviousUnchecked = useCallback(() => {
        if (uncheckedMentions.length === 0) return;

        const prevMention = getPreviousUncheckedMention(selectedMentionId || undefined, false);

        if (prevMention && onMentionClick) {
            onMentionClick(prevMention);
        } else if (uncheckedMentions.length > 0) {
            // If we're on the first unchecked mention, wrap around to the last one
            const lastUnchecked = getPreviousUncheckedMention(undefined, false);
            if (lastUnchecked && onMentionClick) {
                onMentionClick(lastUnchecked);
            }
        }
    }, [selectedMentionId, getPreviousUncheckedMention, onMentionClick, uncheckedMentions.length]);

    const hasUncheckedChunks = useMemo(() => {
        // Use the document completion status hook to check if all documents are completed
        if (!documentCompletionStatus || documentCompletionStatus.size === 0) {
            // If we don't have completion status yet, assume there might be unchecked chunks
            return true;
        }

        // If we have allDocuments, check that we have completion status for all of them
        if (allDocuments && allDocuments.length > 0) {
            const docsWithStatus = allDocuments.filter(doc => documentCompletionStatus.has(doc.id));
            // If not all documents have completion status, assume there might be unchecked chunks
            if (docsWithStatus.length < allDocuments.length) {
                return true;
            }

            // Check if all documents with mentions are checked
            // Documents without mentions are considered "checked" (no work needed)
            const allDocsChecked = allDocuments.every(doc => {
                const status = documentCompletionStatus.get(doc.id);
                // If status is undefined, we don't have data yet, so assume unchecked
                return status === undefined ? false : status === true;
            });

            return !allDocsChecked;
        }

        // If we don't have allDocuments list, check if all documents in the completion map are checked
        const allDocsChecked = Array.from(documentCompletionStatus.values()).every(checked => checked);
        return !allDocsChecked;
    }, [documentCompletionStatus, allDocuments]);

    const handleJumpToNextUnchecked = useCallback(() => {
        // If all mentions are checked in current document
        if (uncheckedMentions.length === 0) {
            // Always call onNextDocument - it will check all documents and navigate to next step if needed
            if (onNextDocument) {
                onNextDocument();
            } else if (onNavigateToNextStep) {
                // Fallback if onNextDocument is not provided
                onNavigateToNextStep();
            }
            return;
        }

        // Try to get next unchecked mention with wrap around
        const nextMention = getNextUncheckedMention(selectedMentionId || undefined, true);

        if (nextMention && onMentionClick) {
            onMentionClick(nextMention);
        }
    }, [selectedMentionId, getNextUncheckedMention, onMentionClick, uncheckedMentions.length, onNextDocument, onNavigateToNextStep]);

    const handleBulkAccept = async () => {
        if (!resolvedCaseId) {
            alert('Case ID niet gevonden');
            return;
        }

        const threshold = bulkThreshold / 100;

        // Use current document mentions only (simple and works)
        const allCaseMentions = allMentions;

        console.log('[BulkAccept] Total mentions in current document:', allCaseMentions.length);
        console.log('[BulkAccept] Threshold:', threshold, `(${bulkThreshold}%)`);

        // Debug: log first few mentions to check confidence values
        if (allCaseMentions.length > 0) {
            console.log('[BulkAccept] Sample mentions:', allCaseMentions.slice(0, 5).map(m => ({
                id: m.mention.id.substring(0, 8),
                confidence: m.mention.confidence,
                checked: m.mention.checked
            })));
        }

        // Filter to unchecked mentions above threshold
        const mentionsToAccept = allCaseMentions.filter(
            ({ mention }) => !mention.checked && mention.confidence >= threshold
        );

        console.log('[BulkAccept] Mentions to accept:', mentionsToAccept.length);
        console.log('[BulkAccept] Breakdown:');
        console.log('  - Total mentions:', allCaseMentions.length);
        console.log('  - Unchecked:', allCaseMentions.filter(m => !m.mention.checked).length);
        console.log('  - Above threshold:', allCaseMentions.filter(m => m.mention.confidence >= threshold).length);
        console.log('  - Both conditions:', mentionsToAccept.length);

        if (mentionsToAccept.length === 0) {
            alert(`Geen vermeldingen gevonden met confidence >= ${bulkThreshold}%`);
            return;
        }

        const mentionIds = mentionsToAccept.map(({ mention }) => mention.id);
        const count = mentionIds.length;

        // Confirm for large operations
        if (count > 50) {
            const confirmed = window.confirm(
                `Je staat op het punt om ${count} vermeldingen in alle documenten te accepteren. Doorgaan?`
            );
            if (!confirmed) return;
        }

        setIsBulkAccepting(true);
        try {
            // Use optimistic update hook - UI updates instantly!
            await bulkAcceptMentions.mutateAsync({
                mentionIds,
                caseId: resolvedCaseId,
            });
        } catch (error) {
            console.error('Failed to bulk accept:', error);
            alert('Bulk acceptatie mislukt.');
        } finally {
            setIsBulkAccepting(false);
        }
    };

    const removeMention = useRemoveMention();

    const handleAccept = useCallback(async (mentionId: string) => {
        if (!resolvedCaseId) {
            alert('Case ID niet gevonden');
            return;
        }
        try {
            await verifyMention.mutateAsync({
                mentionId,
                checked: true,
                accepted: true,
                rejected: null,
                caseId: resolvedCaseId,
            });

            // Wait a bit for the mutation to complete and data to refresh
            setTimeout(() => {
                // Check if there are remaining unchecked mentions (excluding the one we just accepted)
                const remainingUnchecked = allMentions.filter(({ mention }) => !mention.checked && mention.id !== mentionId);

                if (remainingUnchecked.length > 0) {
                    // Try to get next unchecked mention, wrapping around if needed
                    const nextMention = getNextUncheckedMention(mentionId, true);
                    if (nextMention && onMentionClick) {
                        onMentionClick(nextMention);
                    }
                }
            }, 100);
        } catch (error) {
            console.error('Failed to accept mention:', error);
        }
    }, [verifyMention, onMentionClick, getNextUncheckedMention, resolvedCaseId, allMentions]);

    const handleReject = useCallback(async (mentionId: string) => {
        if (!resolvedCaseId) {
            alert('Case ID niet gevonden');
            return;
        }
        try {
            await verifyMention.mutateAsync({
                mentionId,
                checked: true,
                accepted: null,
                rejected: true,
                caseId: resolvedCaseId,
            });

            // Wait a bit for the mutation to complete and data to refresh
            setTimeout(() => {
                // Find remaining unchecked mentions (excluding the one we just rejected)
                const remainingUnchecked = allMentions.filter(({ mention }) => !mention.checked && mention.id !== mentionId);

                if (remainingUnchecked.length > 0) {
                    // Try to get next unchecked mention, wrapping around if needed
                    const nextMention = getNextUncheckedMention(mentionId, true);
                    if (nextMention && onMentionClick) {
                        onMentionClick(nextMention);
                    }
                }
            }, 100);
        } catch (error) {
            console.error('Failed to reject mention:', error);
        }
    }, [verifyMention, onMentionClick, getNextUncheckedMention, resolvedCaseId, allMentions]);

    const handleRemove = useCallback(async (mentionId: string) => {
        try {
            await removeMention.mutateAsync(mentionId);
        } catch (error) {
            console.error('Failed to remove mention:', error);
        }
    }, [removeMention]);


    useEffect(() => {
        const handleKeyDown = async (e: KeyboardEvent) => {
            const activeElement = document.activeElement;
            if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA')) {
                if (e.key === 'Enter' && !e.shiftKey && !selectedMentionId) {
                    e.preventDefault();
                    e.stopPropagation();
                    handleJumpToNextUnchecked();
                }
                return;
            }

            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                e.stopPropagation();
                if (selectedMentionId) {
                    await handleAccept(selectedMentionId);
                } else {
                    handleJumpToNextUnchecked();
                }
            } else if (e.key === 'Enter' && e.shiftKey) {
                e.preventDefault();
                e.stopPropagation();
                if (selectedMentionId) {
                    await handleReject(selectedMentionId);
                }
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [selectedMentionId, handleAccept, handleReject, handleJumpToNextUnchecked]);

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
                <div className="sticky top-0 bg-gray-100 z-20 -mx-4 px-4 pt-4 pb-2 space-y-3 border-b border-gray-300">
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

                    <div className="pb-3 space-y-2">
                        <div className="flex items-center justify-between">
                            <span className="text-xs font-medium text-gray-700">
                                {uncheckedMentions.length} {uncheckedMentions.length === 1 ? 'vermelding' : 'vermeldingen'} niet gecontroleerd
                            </span>
                        </div>

                        {uncheckedMentions.length > 0 ? (
                            resolvedCaseId && (
                                <div className="flex items-center gap-2">
                                    <Label htmlFor="bulk-threshold" className="text-xs font-medium text-gray-700 whitespace-nowrap">
                                        Accepteer boven:
                                    </Label>
                                    <Input
                                        id="bulk-threshold"
                                        type="number"
                                        min="0"
                                        max="100"
                                        value={bulkThreshold}
                                        onChange={(e) => setBulkThreshold(Number(e.target.value))}
                                        className="h-7 w-20 text-xs pr-3 [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none [-moz-appearance:textfield]"
                                        onClick={(e) => e.stopPropagation()}
                                    />
                                    <span className="text-xs text-gray-600">%</span>
                                    <Button
                                        variant="default"
                                        size="sm"
                                        onClick={handleBulkAccept}
                                        disabled={isBulkAccepting}
                                        className="h-7 w-7 p-0 flex-shrink-0"
                                        title={`Accepteer alle vermeldingen boven ${bulkThreshold}% in alle documenten van deze zaak`}
                                    >
                                        {isBulkAccepting ? (
                                            <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                                        ) : (
                                            <Check className="h-4 w-4" />
                                        )}
                                    </Button>
                                </div>
                            )
                        ) : (
                            <div className="flex items-center gap-2 py-2 px-3 bg-green-50 border border-green-200 rounded-md">
                                <Check className="h-5 w-5 text-green-600 flex-shrink-0" />
                                <span className="text-xs font-medium text-green-800">
                                    {hasUncheckedChunks ? 'Alle vermeldingen zijn gecontroleerd' : 'Alle documenten zijn gecontroleerd'}
                                </span>
                            </div>
                        )}

                        {uncheckedMentions.length > 0 ? (
                            <div className="flex border-2 border-border rounded-md overflow-hidden shadow-sm">
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={handleJumpToPreviousUnchecked}
                                    disabled={uncheckedMentions.length === 0}
                                    className="rounded-none border-0 text-xs flex-1 h-7 font-medium"
                                >
                                    <ArrowUp className="h-3 w-3 mr-1" />
                                    Vorige
                                </Button>
                                <div className="h-7 w-px bg-border flex-shrink-0" />
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={handleJumpToNextUnchecked}
                                    disabled={uncheckedMentions.length === 0}
                                    className="rounded-none border-0 text-xs flex-1 h-7 font-medium"
                                >
                                    <ArrowDown className="h-3 w-3 mr-1" />
                                    Volgende
                                </Button>
                            </div>
                        ) : (
                            (hasUncheckedChunks && onNextDocument) || onNavigateToNextStep ? (
                                <Button
                                    variant="default"
                                    size="sm"
                                    onClick={handleJumpToNextUnchecked}
                                    className="w-full h-7 text-xs"
                                >
                                    <ArrowRight className="h-3 w-3 mr-1" />
                                    {hasUncheckedChunks ? 'Volgende document' : 'Belanghebbenden'}
                                </Button>
                            ) : null
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
                        {mentions.map(({ mention }) => {
                            const isSelected = selectedMentionId === mention.id;
                            const isChecked = mention.checked;
                            const isAccepted = mention.accepted === true;
                            const isRejected = mention.rejected === true;

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
                                        isSelected && 'ring-2 ring-blue-500 ring-offset-2 shadow-lg',
                                        isChecked && 'opacity-60 bg-gray-50'
                                    )}
                                    onClick={() => onMentionClick?.(mention)}
                                >
                                    <CardHeader className="pb-3">
                                        <div className="flex items-start justify-between gap-2">
                                            <div className="flex-1 min-w-0">
                                                <h4 className={cn(
                                                    'font-semibold text-sm truncate mb-1',
                                                    isChecked ? 'text-gray-500' : 'text-gray-900'
                                                )}>
                                                    {mention.stakeholder.name}
                                                </h4>
                                                <p className={cn(
                                                    'text-xs capitalize',
                                                    isChecked ? 'text-gray-400' : 'text-gray-500'
                                                )}>
                                                    {mention.stakeholder.type}
                                                </p>
                                            </div>
                                            <ConfidenceBadge confidence={mention.confidence} />
                                        </div>
                                    </CardHeader>
                                    <CardContent className="pt-0 space-y-2">
                                        <div>
                                            <p className={cn(
                                                'text-xs font-medium mb-1',
                                                isChecked ? 'text-gray-400' : 'text-gray-600'
                                            )}>
                                                Vermelding:
                                            </p>
                                            <p className={cn(
                                                'text-sm bg-gray-50 p-2 rounded border border-gray-200 italic',
                                                isChecked ? 'text-gray-500' : 'text-gray-800'
                                            )}>
                                                "{mention.mention_text}"
                                            </p>
                                        </div>
                                        <div className="flex items-center justify-start pt-1">
                                            <AcceptRejectButtons
                                                accepted={isAccepted}
                                                rejected={isRejected}
                                                onAccept={() => handleAccept(mention.id)}
                                                onReject={() => handleReject(mention.id)}
                                                onRemove={isRejected ? () => handleRemove(mention.id) : undefined}
                                            />
                                        </div>
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

