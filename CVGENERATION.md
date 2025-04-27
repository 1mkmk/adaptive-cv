# Process generowania CV w Adaptive CV

## Architektura i przepływ danych

1. **Inicjacja procesu**:
   - Użytkownik wybiera szablon CV (np. "faangpath_simple")
   - Użytkownik dostarcza opis stanowiska pracy/ofertę
   - Backend przekazuje te dane do `LaTeXCVGenerator` w `generator.py`

2. **Przygotowanie profilu użytkownika**:
   - System pobiera profil użytkownika z bazy danych przez `ProfileProcessor`
   - Dane są wstępnie formatowane do dalszej analizy

3. **Analiza i dopasowanie profilu do oferty pracy**:
   - `ProfileProcessor` używa OpenAI do:
     - Wyodrębnienia wymagań z oferty pracy (umiejętności, doświadczenie)
     - Dopasowania profilu do oferty pracy przez metodę `process_with_ai()`

4. **Przygotowanie szablonu LaTeX**:
   - System tworzy unikalny folder wyjściowy w `assets/generated/latex`
   - Kopiuje pliki wybranego szablonu do tego folderu

5. **Analiza struktury szablonu**:
   - `TemplateAnalyzer.analyze_template_directory()` analizuje strukturę szablonu:
     - Identyfikuje główne pliki LaTeX i ich strukturę
     - Wykrywa dostępne pola i placeholdery
     - Identyfikuje środowiska LaTeX używane w szablonie

6. **Generowanie pliku debug.json**:
   - System tworzy szczegółowy plik debug.json zawierający:
     - Analizę struktury szablonu i dostępnych pól
     - Analizę dopasowania profilu do oferty pracy
     - Rekomendacje dotyczące wykorzystania szablonu
     - Sugestie poprawy profilu względem wymagań oferty

7. **Wypełnianie szablonu danymi**:
   - System używa jednej z dwóch metod w zależności od dostępności OpenAI:
     - **Metoda AI (preferowana)**: `_ai_fill_template()` używa OpenAI do inteligentnego wypełnienia szablonu
     - **Metoda tradycyjna (fallback)**: `_fill_file()` używa prostego zastępowania placeholderów

8. **Kompilacja LaTeX do PDF**:
   - System używa lokalnego kompilatora LaTeX do przetworzenia plików .tex
   - Kompilator tworzy plik PDF z CV

9. **Zwracanie wyników**:
   - System tworzy link do pobrania PDF
   - Udostępnia także pliki źródłowe LaTeX i debug.json do wglądu

## Kluczowe komponenty

- **LaTeXCVGenerator**: Główna klasa zarządzająca procesem generowania CV
- **TemplateAnalyzer**: Analizuje szablony LaTeX i wypełnia je danymi
- **ProfileProcessor**: Przetwarza profil użytkownika i dopasowuje go do oferty pracy
- **LaTeXCompiler**: Kompiluje pliki LaTeX do PDF

## Pliki i moduły

- **Frontend**:
  - `/frontend/src/pages/Jobs.tsx`: Interfejs do wyboru ofert i generowania CV
  - `/frontend/src/services/cvService.ts`: Serwis do wywołań API generowania CV

- **Backend**:
  - `/backend/app/routers/generate.py`: Endpointy API dla generowania CV
  - `/backend/app/services/latex_cv/generator.py`: Główny generator LaTeX CV
  - `/backend/app/services/latex_cv/template_analyzer.py`: Analizator szablonów
  - `/backend/app/services/latex_cv/fill_template.py`: Narzędzia do wypełniania szablonów
  - `/backend/app/services/latex_cv/profile_processor.py`: Przetwarzanie profilu użytkownika
  - `/backend/app/services/latex_cv/compilation.py`: Kompilacja LaTeX do PDF

## Rozwiązywanie problemów

1. **Timeout generowania PDF**:
   - Domyślny timeout wynosi 30 sekund
   - W przypadku przekroczenia czasu, użyj opcji bezpośredniego pobierania

2. **Błędy kompilacji LaTeX**:
   - Sprawdź logi błędów w katalogu wyjściowym generowania
   - Upewnij się, że MiKTeX lub TeX Live jest zainstalowany na serwerze