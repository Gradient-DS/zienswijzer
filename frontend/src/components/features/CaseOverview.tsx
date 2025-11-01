import { useCaseOverview } from '@/api/cases';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { CheckCircle2, XCircle, Clock, FileText, Users, Printer } from 'lucide-react';
import { useRef } from 'react';

interface CaseOverviewProps {
    caseId: string;
}

export function CaseOverview({ caseId }: CaseOverviewProps) {
    const { data: overview, isLoading, error } = useCaseOverview(caseId);
    const printRef = useRef<HTMLDivElement>(null);

    const handlePrint = () => {
        if (!printRef.current) return;
        const printWindow = window.open('', '_blank');
        if (!printWindow) return;

        const printContent = printRef.current.innerHTML;
        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>Rapport - ${overview?.case_title || 'Zaak'}</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        padding: 40px;
                        color: #333;
                    }
                    h1 { color: #1a1a1a; border-bottom: 2px solid #333; padding-bottom: 10px; }
                    h2 { color: #2a2a2a; margin-top: 30px; }
                    .stakeholder-status { margin: 5px 0; padding: 8px; background-color: #f9fafb; border-radius: 4px; }
                    .status-agree { color: #10b981; font-weight: 600; }
                    .status-disagree { color: #ef4444; font-weight: 600; }
                    .status-pending { color: #f59e0b; font-weight: 600; }
                    @media print {
                        body { padding: 20px; }
                        .no-print { display: none; }
                    }
                </style>
            </head>
            <body>
                ${printContent}
            </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.focus();
        setTimeout(() => {
            printWindow.print();
        }, 250);
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-gray-500">Overzicht laden...</div>
            </div>
        );
    }

    if (error || !overview) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-red-500">Fout bij laden van overzicht</div>
            </div>
        );
    }

    return (
        <div className="h-full overflow-y-auto p-6">
            <div ref={printRef} className="max-w-5xl mx-auto">
                <div className="flex justify-between items-center mb-6 no-print">
                    <h1 className="text-2xl font-bold">{overview.case_title}</h1>
                    <Button onClick={handlePrint} className="gap-2">
                        <Printer className="h-4 w-4" />
                        Rapport afdrukken
                    </Button>
                </div>

                <div className="print-only mb-6">
                    <h1 className="text-3xl font-bold mb-2">Rapport: {overview.case_title}</h1>
                    <p className="text-gray-600">Datum: {new Date().toLocaleDateString('nl-NL')}</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6 no-print">
                    <Card className="p-4">
                        <div className="flex items-center gap-2 mb-2">
                            <FileText className="h-5 w-5 text-blue-600" />
                            <span className="font-semibold">Documenten</span>
                        </div>
                        <div className="text-2xl font-bold">{overview.total_documents}</div>
                    </Card>
                    <Card className="p-4">
                        <div className="flex items-center gap-2 mb-2">
                            <Users className="h-5 w-5 text-green-600" />
                            <span className="font-semibold">Reacties</span>
                        </div>
                        <div className="text-2xl font-bold">
                            {overview.stakeholders.filter(s => s.has_replied).length} / {overview.stakeholders.length}
                        </div>
                    </Card>
                </div>

                <section className="mb-8">
                    <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                        <Users className="h-5 w-5" />
                        Belanghebbenden Reacties
                    </h2>
                    <div className="space-y-2">
                        {[...overview.stakeholders]
                            .sort((a, b) => {
                                if (a.publication_status === 'agree' && b.publication_status !== 'agree') return -1;
                                if (a.publication_status !== 'agree' && b.publication_status === 'agree') return 1;
                                return 0;
                            })
                            .map((stakeholder) => (
                                <Card key={stakeholder.stakeholder_id} className="p-4">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-3">
                                            {stakeholder.has_replied ? (
                                                stakeholder.publication_status === 'agree' ? (
                                                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                                                ) : stakeholder.publication_status === 'disagree' ? (
                                                    <XCircle className="h-5 w-5 text-red-600" />
                                                ) : (
                                                    <Clock className="h-5 w-5 text-yellow-600" />
                                                )
                                            ) : (
                                                <Clock className="h-5 w-5 text-gray-400" />
                                            )}
                                            <div>
                                                <p className="font-medium">{stakeholder.stakeholder_name}</p>
                                                <p className="text-sm text-gray-600">
                                                    {stakeholder.has_replied
                                                        ? stakeholder.publication_status === 'agree'
                                                            ? 'Akkoord met publicatie'
                                                            : stakeholder.publication_status === 'disagree'
                                                                ? 'Bezwaar tegen publicatie'
                                                                : 'In behandeling'
                                                        : 'Nog geen reactie'}
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </Card>
                            ))}
                    </div>
                </section>
            </div>
        </div>
    );
}

