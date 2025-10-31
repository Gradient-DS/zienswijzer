import { useState, useRef } from 'react';
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
import { Upload, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface DocumentUploadDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    caseId: string;
}

export function DocumentUploadDialog({ open, onOpenChange, caseId }: DocumentUploadDialogProps) {
    const [dragActive, setDragActive] = useState(false);
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const uploadMutation = useUploadDocument();

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

    const handleUpload = async () => {
        if (selectedFiles.length === 0) return;

        try {
            for (const file of selectedFiles) {
                await uploadMutation.mutateAsync({ caseId, file });
            }
            setSelectedFiles([]);
            onOpenChange(false);
        } catch (error) {
            console.error('Upload failed:', error);
        }
    };

    const handleCancel = () => {
        setSelectedFiles([]);
        onOpenChange(false);
    };

    const isSubmitting = uploadMutation.isPending;

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>Documenten toevoegen</DialogTitle>
                    <DialogDescription>
                        Upload PDF documenten voor deze zaak
                    </DialogDescription>
                </DialogHeader>
                <div className="space-y-6 py-4">
                    <div className="space-y-2">
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
                            <p className="text-sm font-semibold">Geselecteerde bestanden ({selectedFiles.length})</p>
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

                    {uploadMutation.isError && (
                        <div
                            id="error-message"
                            role="alert"
                            className="p-4 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-sm"
                        >
                            Upload mislukt. Probeer het opnieuw.
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
                    <Button
                        type="button"
                        onClick={handleUpload}
                        disabled={isSubmitting || selectedFiles.length === 0}
                    >
                        {isSubmitting
                            ? `${selectedFiles.length} bestand(en) uploaden...`
                            : `${selectedFiles.length > 0 ? `${selectedFiles.length} ` : ''}Uploaden`}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}

