import React from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

interface LogoutConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
}

const LogoutConfirmDialog: React.FC<LogoutConfirmDialogProps> = ({ 
  open, 
  onOpenChange,
  onConfirm
}) => {
  const { t } = useTranslation();
  
  const handleLogout = () => {
    // Usuń ciasteczko
    document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    
    // Wywołaj oryginalną funkcję wylogowania
    onConfirm();
    
    // Zamknij dialog
    onOpenChange(false);
    
    // Odśwież stronę
    window.location.reload();
  };
  
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{t('auth.logoutConfirm')}</DialogTitle>
          <DialogDescription>
            {t('auth.logoutConfirmDescription')}
          </DialogDescription>
        </DialogHeader>
        
        <DialogFooter className="flex flex-row justify-end space-x-2 pt-4">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
          >
            {t('common.cancel')}
          </Button>
          <Button
            variant="destructive"
            onClick={handleLogout}
          >
            {t('auth.signOut')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default LogoutConfirmDialog;