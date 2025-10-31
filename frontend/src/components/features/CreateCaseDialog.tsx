import { useState, useRef, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreateCase } from '@/api/cases';
import { useUploadDocument } from '@/api/documents';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Upload, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface CreateCaseDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

export function CreateCaseDialog({ open, onOpenChange }: CreateCaseDialogProps) {
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const [dragActive, setDragActive] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const navigate = useNavigate();
    const createCase = useCreateCase();
    const uploadDocument = useUploadDocument();

    const handleFiles = (files: FileList | null) => {
        if (!files) return;

        const pdfFiles = Array.from(files).filter(file =>
            file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
        );

        setSelectedFiles(prev => {
            const existingNames = new Set(prev.map(f => f.name));
            const newFiles = pdfFiles.filter(f => !existingNames.has(f.name));
            return [...prev, ...newFiles];
        });
    };

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true);
        } else if (e.type === 'dragleave') {
            setDragActive(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleFiles(e.dataTransfer.files);
        }
    };

    const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
        handleFiles(e.target.files);
    };

    const removeFile = (index: number) => {
        setSelectedFiles(prev => prev.filter((_, i) => i !== index));
    };

    const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
        e.preventDefault();

        try {
            const response = await createCase.mutateAsync({
                title,
                description,
            });

            const caseId = response.data.case.id;

            if (selectedFiles.length > 0) {
                for (const file of selectedFiles) {
                    await uploadDocument.mutateAsync({ caseId, file });
                }
            }

            setTitle('');
            setDescription('');
            setSelectedFiles([]);
            onOpenChange(false);
            navigate(`/cases/${caseId}`);
        } catch (error) {
            console.error('Failed to create case:', error);
        }
    };

    const handleCancel = () => {
        setTitle('');
        setDescription('');
        setSelectedFiles([]);
        onOpenChange(false);
    };

    const isSubmitting = createCase.isPending || uploadDocument.isPending;

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>Nieuwe zaak aanmaken</DialogTitle>
                    <DialogDescription>
                        Vul de gegevens in om een nieuwe zaak aan te maken en upload eventueel PDF documenten
                    </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleSubmit}>
                    <div className="space-y-6 py-4">
                        <div className="space-y-2">
                            <Label htmlFor="title">
                                Titel <span className="text-destructive">*</span>
                            </Label>
                            <Input
                                id="title"
                                type="text"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                placeholder="Bijv. Environmental Impact Study"
                                required
                                disabled={isSubmitting}
                                aria-describedby={createCase.error ? 'title-error' : undefined}
                                aria-invalid={createCase.error ? 'true' : 'false'}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="description">
                                Beschrijving <span className="text-destructive">*</span>
                            </Label>
                            <Input
                                id="description"
                                type="text"
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                placeholder="Bijv. Comprehensive environmental assessment for new development"
                                required
                                disabled={isSubmitting}
                                aria-describedby={createCase.error ? 'description-error' : undefined}
                                aria-invalid={createCase.error ? 'true' : 'false'}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label>PDF Documenten (optioneel)</Label>
                            <div
                                className={cn(
                                    'border-2 border-dashed rounded-lg p-6 text-center transition-colors',
                                    dragActive ? 'border-primary bg-primary/5' : 'border-border'
                                )}
                                onDragEnter={handleDrag}
                                onDragLeave={handleDrag}
                                onDragOver={handleDrag}
                                onDrop={handleDrop}
                            >
                                <Upload className="h-10 w-10 mx-auto text-muted-foreground mb-3" />
                                <p className="text-sm font-medium mb-2">
                                    Sleep PDF bestanden hierheen of klik om te selecteren
                                </p>
                                <p className="text-xs text-muted-foreground mb-4">
                                    Je kunt meerdere PDF's selecteren of een map met PDF's
                                </p>
                                <div className="flex gap-2 justify-center">
                                    <Button
                                        type="button"
                                        variant="outline"
                                        onClick={() => fileInputRef.current?.click()}
                                        disabled={isSubmitting}
                                    >
                                        Bestanden selecteren
                                    </Button>
                                    <Button
                                        type="button"
                                        variant="outline"
                                        onClick={() => {
                                            const folderInput = document.createElement('input');
                                            folderInput.type = 'file';
                                            folderInput.webkitdirectory = true;
                                            folderInput.accept = '.pdf,application/pdf';
                                            folderInput.multiple = true;
                                            folderInput.onchange = (e) => {
                                                const target = e.target as HTMLInputElement;
                                                handleFiles(target.files);
                                            };
                                            folderInput.click();
                                        }}
                                        disabled={isSubmitting}
                                    >
                                        Map selecteren
                                    </Button>
                                </div>
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept=".pdf,application/pdf"
                                    multiple
                                    onChange={handleFileInput}
                                    className="hidden"
                                    disabled={isSubmitting}
                                />
                            </div>
                        </div>

                        {selectedFiles.length > 0 && (
                            <div className="space-y-2">
                                <Label>Geselecteerde bestanden ({selectedFiles.length})</Label>
                                <div className="space-y-2 max-h-48 overflow-y-auto border rounded-lg p-3 bg-muted/50">
                                    {selectedFiles.map((file, index) => (
                                        <div
                                            key={index}
                                            className="flex items-center justify-between p-2 bg-background rounded-md"
                                        >
                                            <span className="text-sm truncate flex-1 mr-2">{file.name}</span>
                                            <span className="text-xs text-muted-foreground mr-2">
                                                {(file.size / 1024).toFixed(1)} KB
                                            </span>
                                            <Button
                                                type="button"
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => removeFile(index)}
                                                disabled={isSubmitting}
                                                className="h-7 w-7 p-0"
                                            >
                                                <X className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {(createCase.error || uploadDocument.isError) && (
                            <div
                                id="error-message"
                                role="alert"
                                className="p-4 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-sm"
                            >
                                {createCase.error
                                    ? 'Het aanmaken van de zaak is mislukt. Probeer het opnieuw.'
                                    : 'Het uploaden van documenten is mislukt. De zaak is aangemaakt, maar probeer de documenten opnieuw te uploaden.'}
                            </div>
                        )}
                    </div>
                    <DialogFooter>
                        <Button
                            type="button"
                            variant="outline"
                            onClick={handleCancel}
                            disabled={isSubmitting}
                        >
                            Annuleren
                        </Button>
                        <Button type="submit" disabled={isSubmitting}>
                            {isSubmitting
                                ? (createCase.isPending ? 'Zaak aanmaken...' : `${selectedFiles.length} bestand(en) uploaden...`)
                                : 'Aanmaken'}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}

