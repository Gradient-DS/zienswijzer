import { useNavigate, useLocation } from 'react-router-dom';
import { useCases } from '@/api/cases';
import { useAuthStore, useUIStore } from '@/store';
import { Button } from '@/components/ui/button';
import type { Case } from '@/types';
import {
    Bell,
    Plus,
    User,
    Settings,
    MoreVertical,
    LogOut,
    ChevronLeft,
} from 'lucide-react';
import { cn } from '@/lib/utils';

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

interface SidebarProps {
    selectedCaseId?: string;
    onCaseSelect?: (caseId: string) => void;
    onClose?: () => void;
    isMobile?: boolean;
}

export function Sidebar({ selectedCaseId, onCaseSelect, onClose, isMobile = false }: SidebarProps) {
    const navigate = useNavigate();
    const location = useLocation();
    const { data: cases, isLoading } = useCases();
    const { logout } = useAuthStore();
    const { toggleSidebar } = useUIStore();

    const handleCaseClick = (caseId: string) => {
        if (onCaseSelect) {
            onCaseSelect(caseId);
        }
        navigate(`/cases/${caseId}`);
        if (isMobile && onClose) {
            onClose();
        }
    };

    const handleLogout = () => {
        logout();
        navigate('/login', { replace: true });
    };

    const handleNewCase = () => {
        navigate('/home');
        if (isMobile && onClose) {
            onClose();
        }
    };

    const groupedCases = cases ? groupCasesByDate(cases) : {};

    return (
        <div className="flex flex-col h-screen w-[280px] bg-gray-50 border-r border-gray-200">
            <div className="flex-shrink-0 p-4 space-y-3 border-b border-gray-200">
                <div className="flex items-center w-full">
                    <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => {
                            if (isMobile && onClose) {
                                onClose();
                            } else {
                                toggleSidebar();
                            }
                        }}
                    >
                        <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <h1 className="text-md text-gray-900 ml-auto">WOO zienswijze</h1>
                </div>
                <div className="space-y-1">
                    <Button
                        variant="ghost"
                        className="w-full justify-start gap-2"
                        onClick={handleNewCase}
                    >
                        <Plus className="h-4 w-4" />
                        Nieuwe zaak
                    </Button>
                    <Button
                        variant="ghost"
                        className="w-full justify-start gap-2"
                    >
                        <Bell className="h-4 w-4" />
                        Notificaties
                    </Button>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4">
                <h2 className="text-sm font-semibold text-gray-700 mb-3">Zaken</h2>
                {isLoading ? (
                    <div className="text-sm text-gray-500">Zaken laden...</div>
                ) : cases && cases.length > 0 ? (
                    <div className="space-y-4">
                        {Object.entries(groupedCases).map(([dateGroup, dateCases]) => (
                            <div key={dateGroup}>
                                <h3 className="text-xs font-medium text-gray-500 mb-2">
                                    {dateGroup}
                                </h3>
                                <div className="space-y-1">
                                    {dateCases.map((caseItem) => {
                                        const isSelected = selectedCaseId === caseItem.id ||
                                            location.pathname === `/cases/${caseItem.id}`;
                                        return (
                                            <div
                                                key={caseItem.id}
                                                className={cn(
                                                    'group flex items-center gap-2 px-2 py-2 rounded-md cursor-pointer transition-colors',
                                                    isSelected
                                                        ? 'bg-gray-200 text-gray-900'
                                                        : 'hover:bg-gray-100 text-gray-700'
                                                )}
                                                onClick={() => handleCaseClick(caseItem.id)}
                                            >
                                                <span className="flex-1 truncate text-sm">
                                                    {caseItem.title}
                                                </span>
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                    }}
                                                >
                                                    <MoreVertical className="h-4 w-4" />
                                                </Button>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-sm text-gray-500">Nog geen zaken</div>
                )}
            </div>

            <div className="flex-shrink-0 p-4 space-y-2 border-t border-gray-200">
                <Button
                    variant="ghost"
                    className="w-full justify-start gap-2"
                >
                    <User className="h-4 w-4" />
                    Account
                </Button>
                <Button
                    variant="ghost"
                    className="w-full justify-start gap-2"
                    onClick={handleLogout}
                >
                    <LogOut className="h-4 w-4" />
                    Uitloggen
                </Button>
                <Button
                    variant="ghost"
                    className="w-full justify-start gap-2"
                >
                    <Settings className="h-4 w-4" />
                    Instellingen
                </Button>
            </div>
        </div>
    );
}

