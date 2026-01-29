import React from 'react';
import { cn } from '../../utils/cn';

interface DialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    children?: React.ReactNode;
}

export const Dialog: React.FC<DialogProps> = ({ open, onOpenChange, children }) => {
    if (!open) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
            <div
                className="fixed inset-0 z-50 bg-black/50"
                onClick={() => onOpenChange(false)}
            />
            <div className="relative z-50 w-full max-w-lg p-6 bg-background rounded-lg shadow-lg border">
                {children}
            </div>
        </div>
    );
};

export const DialogContent: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className }) => (
    <div className={cn("grid gap-4", className)}>{children}</div>
);

export const DialogHeader: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className }) => (
    <div className={cn("flex flex-col space-y-1.5 text-center sm:text-left", className)}>{children}</div>
);

export const DialogTitle: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className }) => (
    <h3 className={cn("text-lg font-semibold leading-none tracking-tight", className)}>{children}</h3>
);

export const DialogDescription: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className }) => (
    <p className={cn("text-sm text-muted-foreground", className)}>{children}</p>
);

export const DialogFooter: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className }) => (
    <div className={cn("flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2", className)}>{children}</div>
);
