import { useNavigate, useLocation } from 'react-router-dom';
import { useCases } from '@/api/cases';
import { Button } from '@/components/ui/button';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
    DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import { ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Case } from '@/types';

function formatDateGroup(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const caseDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());

    if (caseDate.getTime() === today.getTime()) {
        return 'Vandaag';
    } else if (caseDate.getTime() === yesterday.getTime()) {
        return 'Gisteren';
    } else {
        return date.toLocaleDateString('nl-NL', { month: 'long', day: 'numeric', year: 'numeric' });
    }
}

function groupCasesByDate(cases: Case[]) {
    const groups: Record<string, Case[]> = {};

    cases.forEach((caseItem) => {
        const groupKey = formatDateGroup(caseItem.createdAt);
        if (!groups[groupKey]) {
            groups[groupKey] = [];
        }
        groups[groupKey].push(caseItem);
    });

    return groups;
}

interface CaseDropdownProps {
    selectedCaseId?: string;
    onCaseSelect?: (caseId: string) => void;
}

export function CaseDropdown({ selectedCaseId, onCaseSelect }: CaseDropdownProps) {
    const navigate = useNavigate();
    const location = useLocation();
    const { data: cases, isLoading } = useCases();

    const handleCaseClick = (caseId: string) => {
        if (onCaseSelect) {
            onCaseSelect(caseId);
        }
        navigate(`/cases/${caseId}`);
    };

    const selectedCase = cases?.find((c) => c.id === selectedCaseId || location.pathname === `/cases/${c.id}`);
    const groupedCases = cases ? groupCasesByDate(cases) : {};

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button
                    variant="ghost"
                    className="w-full justify-between gap-2 h-8 pl-2"
                >
                    <span className="flex-1 text-left truncate">
                        {selectedCase ? `Zaak: ${selectedCase.title}` : 'Selecteer zaak'}
                    </span>
                    <ChevronDown className="h-4 w-4 flex-shrink-0" />
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-[280px] max-h-[400px] overflow-y-auto" align="start">
                {isLoading ? (
                    <div className="p-2 text-sm text-gray-500">Zaken laden...</div>
                ) : cases && cases.length > 0 ? (
                    <>
                        {Object.entries(groupedCases).map(([dateGroup, dateCases], groupIndex) => (
                            <div key={dateGroup}>
                                {groupIndex > 0 && <DropdownMenuSeparator />}
                                <div className="px-2 py-1.5">
                                    <h3 className="text-xs font-medium text-gray-500 mb-1">
                                        {dateGroup}
                                    </h3>
                                </div>
                                {dateCases.map((caseItem) => {
                                    const isSelected = selectedCaseId === caseItem.id ||
                                        location.pathname === `/cases/${caseItem.id}`;
                                    return (
                                        <DropdownMenuItem
                                            key={caseItem.id}
                                            className={cn(
                                                'flex items-center gap-2 px-2 py-2 cursor-pointer',
                                                isSelected && 'bg-gray-100'
                                            )}
                                            onClick={() => handleCaseClick(caseItem.id)}
                                        >
                                            <span className="flex-1 truncate text-sm">
                                                {caseItem.title}
                                            </span>
                                        </DropdownMenuItem>
                                    );
                                })}
                            </div>
                        ))}
                    </>
                ) : (
                    <div className="p-2 text-sm text-gray-500">Nog geen zaken</div>
                )}
            </DropdownMenuContent>
        </DropdownMenu>
    );
}

