"""Anthropic AI service for generating humorous kudo rain messages."""

import os
import random

import anthropic

STANDARD_PROMPT_TEMPLATE = """Napisz DOKŁADNIE JEDNĄ humorystyczną wiadomość która zaczyna się od "<!channel> Kudo rain for {user_name}" a następnie żartobliwy roast z odniesieniami do popkultury.

Wymagania:
- Zacznij od "<!channel> Kudo rain for @{user_name}"
- Tylko jedno zdanie, 40-60 słów
- Żartobliwie sarkastyczna o nawykach pracy {user_title}
- Użyj 1-2 RÓŻNORODNYCH odniesień do popkultury (nie trzymaj się cały czas Marvel/DC)
- Odpowiednia do miejsca pracy ale śmiała
- Zwróć TYLKO wiadomość, bez alternatyw ani wyjaśnień

Przykłady stylu:
"<!channel> Kudo rain for @alex - jak Hermiona z czasozmienką, jakoś wszędzie naraz, ale twoja prawdziwa supermoc to zamienianie 30-minutowych meetingów w Dzień świstaka!"
- "<!channel> Kudo rain for @sam - kanalizujesz swojego wewnętrznego Gordona Ramsaya w code review i Boba Rossa w debugowaniu, jesteś chodząca sprzeczność która jakoś działa!"
- "<!channel> Kudo rain for @jamie - jak Sherlock Holmes rozwiązujący zagadki, znajdujesz bugi których nikt inny nie widzi, ale w przeciwieństwie do niego wciąż gubisz się we własnej strukturze katalogów!"
- "<!channel> Kudo rain for @thomas - jak Thanos wymazał połowę życia pstryknięciem palców (nie wspominajmy o usunięciu połowy bazy danych)"

Stwórz coś ŚWIEŻEGO i ORYGINALNEGO z różnymi odniesieniami.

Napisz dokładnie jedną wiadomość:"""


WALASZEK_PATTERNS = {
    "DIALOG": {
        "description": "Krótki dialog pytanie-odpowiedź z absurdalną logiką",
        "structure": "Co X? - Y. - A Z? - W.",
        "examples": [
            "Ale pachnie! Co robisz? - Pracuję. - A dokładnie? - Siedzę. - Mmm klasyka!",
            "Co jesz? - Kanapkę. - A kiedy skończysz? - Jak zjem. - A kod? - Kod poczeka, kanapka nie.",
            "Idziesz na przerwę? - Idę. - A wracasz? - Wrócę. - Kiedy? - Jak skończę przerwę.",
            "Myślisz? - Myślę. - Nad czym? - Nad tym co zjeść. - A potem? - Potem znowu będę myślał.",
            "Działa? - Działa. - A dlaczego? - Nie wiem. - To nie ruszaj. - Nie ruszam.",
        ],
    },
    "CHALLENGE": {
        "description": "Rzucenie wyzwania z krótką ripostą/przeprosinami",
        "structure": "Taki X? To pokaż Y! - Przepraszam/Nie ma.",
        "examples": [
            "Taki produktywny? To pokaż wyniki! - Przepraszam, ale działało na localhoście.",
            "Taki szybki? To kiedy skończysz? - Jak skończę. - A kiedy to? - Nie wiem, jeszcze nie zacząłem.",
            "Taki mądry? To wytłumacz! - Co? - Cokolwiek. - Nie da się. - Czemu? - Bo nie wiem.",
            "Taki zajęty? To co robisz? - Czekam. - Na co? - Aż przestanę być zajęty.",
        ],
    },
    "LIST": {
        "description": "Lista 2 możliwych wyjaśnień (zwykle absurdalnych)",
        "structure": "Są 2 wytłumaczenia: 1) X 2) Y - stawiam na Y.",
        "examples": [
            "Są 2 wytłumaczenia czemu to działa: 1) Szczęście 2) Czary - osobiście stawiam na czary.",
            "Są 2 powody czemu skończył na czas: 1) Profesjonalizm 2) Nie zaczął - stawiam na drugie.",
            "Są 2 wytłumaczenia czemu jest w biurze: 1) Praca 2) Klimatyzacja - stawiam na klimatyzację.",
        ],
    },
    "COMPARISON": {
        "description": "Porównanie z nieoczekiwanym zwrotem",
        "structure": "Co może być X niż Y? No może Z bo...",
        "examples": [
            "Co może być piękniejszego niż działający kod? No może przerwa obiadowa bo występuje częściej.",
            "Co może być lepsze niż spotkanie? No może brak spotkania bo wtedy można iść na kawę.",
            "Co może być cenniejsze niż cisza w biurze? No może hałas bo wtedy wiadomo że nie jesteś sam.",
        ],
    },
    "MAXIM": {
        "description": "Krótka życiowa mądrość/przysłowie",
        "structure": "Jeden X, Y czasu Z - stara zasada.",
        "examples": [
            "Jedna kawa rano, cały dzień czekania na drugą - stara zasada która zawsze się sprawdza.",
            "Jedno spotkanie, godzina gadania - klasyka która nigdy nie zawodzi niestety.",
            "Kto w piątek zaczyna, ten w poniedziałek kończy - stare powiedzenie.",
            "Jeden pomysł, tydzień tłumaczenia czemu nie - zasada która działa w obie strony.",
        ],
    },
    "OBSERVATION": {
        "description": "Leniwa obserwacja/westchnienie",
        "structure": "Ahhhh/Siedzi i X. Y. Z.",
        "examples": [
            "Siedzi i klika. Czasem myśli. Niewiele, ale stara się.",
            "Patrzy w monitor od rana do wieczora. Efekty średnie ale konsekwentne.",
            "Ahhhh, biurko, klawiatura, ciepła kawa z automatu. Pięknie.",
            "Siedzi i patrzy w okno. Czasem wraca do monitora. Profesjonalista.",
        ],
    },
    "SIMPLE_TRUTH": {
        "description": "Prosta deklaracja wiary/niewiary",
        "structure": "Jestem prosty X, nie wierzę w Y za to wierzę w Z.",
        "examples": [
            "Jestem prosty developer, nie wierzę w dokumentację za to wierzę w komentarze.",
            "Zgadza się skopiował z internetu, ale tylko frajer by nie skorzystał. Trzeba było pilnować.",
            "Jestem prosty człowiek, nie wierzę w spotkania za to wierzę w maile.",
            "Zgadza się wyszedł wcześniej, ale przecież czas to umowa społeczna, prawda?",
        ],
    },
    "CHARACTER": {
        "description": "Krótka charakterystyka osoby",
        "structure": "U niego w głowie tylko X. Niewiele/Y, ale Z.",
        "examples": [
            "U niego w głowie jest tylko jedno - praca. Niewiele, ale jednak.",
            "U niego w głowie tylko kawa i obiad. Reszta gdzieś z tyłu czeka.",
            "Tyle lat w firmie a wciąż nie wie gdzie jest kuchnia. Ale pracować umie, to ważne.",
            "Jego notatki ze spotkania wyglądają jak pusta kartka. Bo to pusta kartka.",
            "Mówi mało. Robi mniej. Ale konsekwentnie, tego mu nie można odmówić.",
        ],
    },
}


WALASZEK_PROMPT_TEMPLATE = """Napisz DOKŁADNIE JEDNĄ absurdalną wiadomość która zaczyna się od "<!channel> Deszcz kudosów dla {user_name}" w stylu Bartosza Walaszka (Kapitan Bomba/Blok Ekipa).

KIM JEST WALASZEK:
Twórca kultowych polskich produkcji znanych z absurdalnego humoru - prosty język, broken logic, absurd w prostocie.

WYBRANA STRUKTURA NA TEN RAZ: {pattern_name}
Opis: {pattern_description}
Wzorzec: {pattern_structure}

PRZYKŁAD TEJ STRUKTURY:
"<!channel> Deszcz kudosów dla @user - {good_example}"

WAŻNE - użyj DOKŁADNIE tej struktury! Nie mieszaj z innymi wzorcami!

Styl Walaszka:
- PROSTY język (nie tech-speak!)
- Absurd w PROSTOCIE
- Praca tylko jako TŁO
- Krótkie zdania

KONTEKST ROLI ({user_title}):
- Dostosuj kontekst do roli ale NIE używaj skomplikowanych terminów
- Absurd jest ważniejszy niż kontekst pracy

Wymagania:
- Zacznij od "<!channel> Deszcz kudosów dla @{user_name}"
- Tylko jedno zdanie, 40-60 słów
- Użyj WYŁĄCZNIE struktury: {pattern_name}
- Zwróć TYLKO wiadomość, bez alternatyw

Napisz jedną wiadomość używając struktury {pattern_name}:"""


class AnthropicService:
    """Service for generating AI-powered humorous messages using Claude."""

    # Cache last pattern to ensure variety
    _last_pattern = None

    def __init__(self):
        """Initialize the Anthropic client."""
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    async def generate_kudo_rain(
        self, user_name: str, user_title: str = "Developer"
    ) -> str:
        """
        Generate a humorous kudo rain message for the selected user.

        Uses pattern rotation to ensure structural variety in messages.

        Args:
            user_name: The display name of the selected user
            user_title: The job title of the selected user

        Returns:
            A humorous one-sentence kudo rain message
        """
        # Select a pattern different from the last one
        pattern_names = list(WALASZEK_PATTERNS.keys())
        available_patterns = [
            p for p in pattern_names if p != AnthropicService._last_pattern
        ]
        chosen_pattern = random.choice(
            available_patterns if available_patterns else pattern_names
        )
        AnthropicService._last_pattern = chosen_pattern

        # Get pattern info and select random example from it
        pattern_info = WALASZEK_PATTERNS[chosen_pattern]
        good_example = random.choice(pattern_info["examples"])

        prompt = WALASZEK_PROMPT_TEMPLATE.format(
            user_name=user_name,
            user_title=user_title,
            pattern_name=chosen_pattern,
            pattern_description=pattern_info["description"],
            pattern_structure=pattern_info["structure"],
            good_example=good_example,
        )

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=150,
                temperature=0.9,  # Higher temperature for more variety
                messages=[{"role": "user", "content": prompt}],
            )

            if message.content and len(message.content) > 0:
                return message.content[0].text.strip()
            else:
                return self._fallback_message(user_name, user_title)

        except Exception as e:
            print(f"❌ Error generating kudo rain: {e}")
            return self._fallback_message(user_name, user_title)

    def _fallback_message(self, user_name: str, user_title: str = "Developer") -> str:
        """Generate a simple fallback message if AI fails."""
        return f"<!channel> Kudo rain for @{user_name} - like a superhero {user_title} whose only power is making coffee disappear and Zoom calls awkward! 🎯☕"

    def is_configured(self) -> bool:
        """Check if Anthropic API key is configured."""
        return bool(os.environ.get("ANTHROPIC_API_KEY"))
