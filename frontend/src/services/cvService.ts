import { API_BASE_URL, DIRECT_API_URL, fetchApi } from './api';

export interface GenerateCVParams {
  prompt: string;
  job_id?: number;
  format?: 'markdown' | 'pdf';
  creativity_levels?: {
    personal_info: number;
    summary: number;
    experience: number;
    education: number;
    skills: number;
    projects: number;
    awards: number;
    presentations: number;
    interests: number;
  };
}

export interface CVResponse {
  result: string;
  format: 'markdown' | 'pdf';
  preview?: string;
  error?: string;
  job_key?: string;
  latex_path?: string; 
  pdf_path?: string;
  preview_path?: string;
}

/**
 * Generuje CV na podstawie opisu stanowiska i opcjonalnie ID oferty pracy
 */
export async function generateCV(params: GenerateCVParams): Promise<CVResponse | null> {
  try {
    const response = await fetchApi('/generate', {
      method: 'POST',
      body: JSON.stringify(params),
    });
    
    return response;
  } catch (error) {
    console.error('Error generating CV:', error);
    return null;
  }
}

/**
 * Generuje CV w formacie PDF dla konkretnej oferty pracy
 */
export async function generatePdfCV(jobId: number): Promise<CVResponse | null> {
  try {
    const response = await fetchApi(`/generate/pdf/${jobId}`, {
      method: 'GET',
    });
    
    return response;
  } catch (error) {
    console.error('Error generating PDF CV:', error);
    return null;
  }
}

/**
 * Pobiera URL do bezpośredniego pobrania CV w formacie PDF
 */
export function getDownloadCvUrl(jobId: number): string {
  // Najpierw spróbuj z API_BASE_URL
  try {
    return `${API_BASE_URL}/generate/download/${jobId}`;
  } catch (e) {
    // Jeśli nie zadziała, użyj DIRECT_API_URL
    return `${DIRECT_API_URL}/generate/download/${jobId}`;
  }
}

/**
 * Pobiera URL do bezpośredniego pobrania kodu LaTeX
 */
export function getDownloadLatexUrl(jobId: number): string {
  // Najpierw spróbuj z API_BASE_URL
  try {
    return `${API_BASE_URL}/generate/download/latex/${jobId}`;
  } catch (e) {
    // Jeśli nie zadziała, użyj DIRECT_API_URL
    return `${DIRECT_API_URL}/generate/download/latex/${jobId}`;
  }
}

/**
 * Pobiera URL do podglądu CV w formacie obrazu
 */
export function getPreviewCvUrl(jobId: number): string {
  // Najpierw spróbuj z API_BASE_URL
  try {
    return `${API_BASE_URL}/generate/preview/${jobId}`;
  } catch (e) {
    // Jeśli nie zadziała, użyj DIRECT_API_URL
    return `${DIRECT_API_URL}/generate/preview/${jobId}`;
  }
}

/**
 * Inicjuje pobieranie CV w formacie PDF
 */
export function downloadCV(jobId: number, jobTitle: string, companyName: string): void {
  try {
    // Generuj nazwę pliku na podstawie danych oferty
    const filename = `CV_${jobTitle}_${companyName}_${new Date().toISOString().split('T')[0]}.pdf`.replace(/\s+/g, '_');
    
    // Utwórz element <a> do pobierania
    const downloadLink = document.createElement('a');
    downloadLink.href = getDownloadCvUrl(jobId);
    downloadLink.download = filename;
    downloadLink.target = '_blank';
    
    // Dodaj do dokumentu i kliknij
    document.body.appendChild(downloadLink);
    downloadLink.click();
    
    // Usuń element z dokumentu
    setTimeout(() => {
      document.body.removeChild(downloadLink);
    }, 100);
  } catch (error) {
    console.error('Error downloading CV:', error);
    alert('Wystąpił błąd podczas pobierania CV. Spróbuj ponownie później.');
  }
}

/**
 * Otwiera CV w formacie PDF w nowej karcie przeglądarki
 */
export function openCVInBrowser(jobId: number): void {
  try {
    window.open(getDownloadCvUrl(jobId), '_blank');
  } catch (error) {
    console.error('Error opening CV in browser:', error);
    alert('Wystąpił błąd podczas otwierania CV. Spróbuj ponownie później.');
  }
}

/**
 * Wyświetla/pobiera PDF z danych zakodowanych w base64
 */
export function displayPdf(base64Data: string, filename: string = 'cv.pdf'): void {
  try {
    // Zabezpieczenie przed nieprawidłowymi znakami w base64
    // Usuń wszystkie potencjalne znaki, które nie są częścią formatu base64
    const cleanBase64 = base64Data.replace(/[^A-Za-z0-9+/=]/g, '');
    
    // Przekieruj na pobieranie przez bezpośredni URL
    if (cleanBase64 === "placeholder" && filename) {
      // Wyciągnij ID z nazwy pliku
      const jobId = filename.match(/(\d+)/);
      if (jobId && jobId[1]) {
        console.log(`Redirecting to direct download for job ID: ${jobId[1]}`);
        window.open(getDownloadCvUrl(parseInt(jobId[1])), '_blank');
        return;
      }
    }
    
    try {
      // Create blob from base64 data
      const byteCharacters = atob(cleanBase64);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: 'application/pdf' });
      
      // Create object URL for the blob
      const blobUrl = URL.createObjectURL(blob);
      
      // Open PDF in new tab
      window.open(blobUrl, '_blank');
      
      // Optional: Create download link
      const downloadLink = document.createElement('a');
      downloadLink.href = blobUrl;
      downloadLink.download = filename;
      document.body.appendChild(downloadLink);
      downloadLink.click();
      document.body.removeChild(downloadLink);
      
      // Clean up the URL object
      setTimeout(() => {
        URL.revokeObjectURL(blobUrl);
      }, 100);
    } catch (decodeError) {
      console.error('Error decoding Base64:', decodeError);
      // Fallback - pobierz bezpośrednio przez API
      console.log('Falling back to direct download');
      window.open(getDownloadCvUrl(1), '_blank');
    }
  } catch (error) {
    console.error('Error displaying PDF:', error);
    alert('Error displaying PDF. Trying direct download now.');
    // Fallback - spróbuj pobrać bezpośrednio
    window.open('/generate/download/1', '_blank');
  }
}