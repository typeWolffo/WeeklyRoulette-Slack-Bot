package services

import (
	"context"
	"fmt"
	"log/slog"
	"math/rand"

	"github.com/anthropics/anthropic-sdk-go"
	"github.com/anthropics/anthropic-sdk-go/option"
)

type Pattern struct {
	Description string
	Structure   string
	Examples    []string
}

var WalaszekPatterns = map[string]Pattern{
	"DIALOG": {
		Description: "Krótki dialog pytanie-odpowiedź z absurdalną logiką",
		Structure:   "Co X? - Y. - A Z? - W.",
		Examples: []string{
			"Ale pachnie! Co robisz? - Pracuję. - A dokładnie? - Siedzę. - Mmm klasyka!",
			"Co jesz? - Kanapkę. - A kiedy skończysz? - Jak zjem. - A kod? - Kod poczeka, kanapka nie.",
			"Idziesz na przerwę? - Idę. - A wracasz? - Wrócę. - Kiedy? - Jak skończę przerwę.",
			"Myślisz? - Myślę. - Nad czym? - Nad tym co zjeść. - A potem? - Potem znowu będę myślał.",
			"Działa? - Działa. - A dlaczego? - Nie wiem. - To nie ruszaj. - Nie ruszam.",
		},
	},
	"CHALLENGE": {
		Description: "Rzucenie wyzwania z krótką ripostą/przeprosinami",
		Structure:   "Taki X? To pokaż Y! - Przepraszam/Nie ma.",
		Examples: []string{
			"Taki produktywny? To pokaż wyniki! - Przepraszam, ale działało na localhoście.",
			"Taki szybki? To kiedy skończysz? - Jak skończę. - A kiedy to? - Nie wiem, jeszcze nie zacząłem.",
			"Taki mądry? To wytłumacz! - Co? - Cokolwiek. - Nie da się. - Czemu? - Bo nie wiem.",
			"Taki zajęty? To co robisz? - Czekam. - Na co? - Aż przestanę być zajęty.",
		},
	},
	"LIST": {
		Description: "Lista 2 możliwych wyjaśnień (zwykle absurdalnych)",
		Structure:   "Są 2 wytłumaczenia: 1) X 2) Y - stawiam na Y.",
		Examples: []string{
			"Są 2 wytłumaczenia czemu to działa: 1) Szczęście 2) Czary - osobiście stawiam na czary.",
			"Są 2 powody czemu skończył na czas: 1) Profesjonalizm 2) Nie zaczął - stawiam na drugie.",
			"Są 2 wytłumaczenia czemu jest w biurze: 1) Praca 2) Klimatyzacja - stawiam na klimatyzację.",
		},
	},
	"COMPARISON": {
		Description: "Porównanie z nieoczekiwanym zwrotem",
		Structure:   "Co może być X niż Y? No może Z bo...",
		Examples: []string{
			"Co może być piękniejszego niż działający kod? No może przerwa obiadowa bo występuje częściej.",
			"Co może być lepsze niż spotkanie? No może brak spotkania bo wtedy można iść na kawę.",
			"Co może być cenniejsze niż cisza w biurze? No może hałas bo wtedy wiadomo że nie jesteś sam.",
		},
	},
	"MAXIM": {
		Description: "Krótka życiowa mądrość/przysłowie",
		Structure:   "Jeden X, Y czasu Z - stara zasada.",
		Examples: []string{
			"Jedna kawa rano, cały dzień czekania na drugą - stara zasada która zawsze się sprawdza.",
			"Jedno spotkanie, godzina gadania - klasyka która nigdy nie zawodzi niestety.",
			"Kto w piątek zaczyna, ten w poniedziałek kończy - stare powiedzenie.",
			"Jeden pomysł, tydzień tłumaczenia czemu nie - zasada która działa w obie strony.",
		},
	},
	"OBSERVATION": {
		Description: "Leniwa obserwacja/westchnienie",
		Structure:   "Ahhhh/Siedzi i X. Y. Z.",
		Examples: []string{
			"Siedzi i klika. Czasem myśli. Niewiele, ale stara się.",
			"Patrzy w monitor od rana do wieczora. Efekty średnie ale konsekwentne.",
			"Ahhhh, biurko, klawiatura, ciepła kawa z automatu. Pięknie.",
			"Siedzi i patrzy w okno. Czasem wraca do monitora. Profesjonalista.",
		},
	},
	"SIMPLE_TRUTH": {
		Description: "Prosta deklaracja wiary/niewiary",
		Structure:   "Jestem prosty X, nie wierzę w Y za to wierzę w Z.",
		Examples: []string{
			"Jestem prosty developer, nie wierzę w dokumentację za to wierzę w komentarze.",
			"Zgadza się skopiował z internetu, ale tylko frajer by nie skorzystał. Trzeba było pilnować.",
			"Jestem prosty człowiek, nie wierzę w spotkania za to wierzę w maile.",
			"Zgadza się wyszedł wcześniej, ale przecież czas to umowa społeczna, prawda?",
		},
	},
	"CHARACTER": {
		Description: "Krótka charakterystyka osoby",
		Structure:   "U niego w głowie tylko X. Niewiele/Y, ale Z.",
		Examples: []string{
			"U niego w głowie jest tylko jedno - praca. Niewiele, ale jednak.",
			"U niego w głowie tylko kawa i obiad. Reszta gdzieś z tyłu czeka.",
			"Tyle lat w firmie a wciąż nie wie gdzie jest kuchnia. Ale pracować umie, to ważne.",
			"Jego notatki ze spotkania wyglądają jak pusta kartka. Bo to pusta kartka.",
			"Mówi mało. Robi mniej. Ale konsekwentnie, tego mu nie można odmówić.",
		},
	},
}

const walaszekPromptTemplate = `Napisz DOKŁADNIE JEDNĄ absurdalną wiadomość która zaczyna się od "<!channel> Deszcz kudosów dla %s" w stylu Bartosza Walaszka (Kapitan Bomba/Blok Ekipa).

KIM JEST WALASZEK:
Twórca kultowych polskich produkcji znanych z absurdalnego humoru - prosty język, broken logic, absurd w prostocie.

WYBRANA STRUKTURA NA TEN RAZ: %s
Opis: %s
Wzorzec: %s

PRZYKŁAD TEJ STRUKTURY:
"<!channel> Deszcz kudosów dla @user - %s"

WAŻNE - użyj DOKŁADNIE tej struktury! Nie mieszaj z innymi wzorcami!

Styl Walaszka:
- PROSTY język (nie tech-speak!)
- Absurd w PROSTOCIE
- Praca tylko jako TŁO
- Krótkie zdania

KONTEKST ROLI (%s):
- Dostosuj kontekst do roli ale NIE używaj skomplikowanych terminów
- Absurd jest ważniejszy niż kontekst pracy

Wymagania:
- Zacznij od "<!channel> Deszcz kudosów dla @%s"
- Tylko jedno zdanie, 40-60 słów
- Użyj WYŁĄCZNIE struktury: %s
- Zwróć TYLKO wiadomość, bez alternatyw

Napisz jedną wiadomość używając struktury %s:`

type AnthropicService struct {
	client      anthropic.Client
	lastPattern string
	configured  bool
}

func NewAnthropicService(apiKey string) *AnthropicService {
	if apiKey == "" {
		return &AnthropicService{configured: false}
	}

	client := anthropic.NewClient(
		option.WithAPIKey(apiKey),
	)

	return &AnthropicService{
		client:     client,
		configured: true,
	}
}

func (s *AnthropicService) IsConfigured() bool {
	return s.configured
}

func (s *AnthropicService) GenerateKudoRain(ctx context.Context, userName, userTitle string) (string, error) {
	if !s.configured {
		return s.fallbackMessage(userName, userTitle), nil
	}

	patternNames := make([]string, 0, len(WalaszekPatterns))
	for name := range WalaszekPatterns {
		patternNames = append(patternNames, name)
	}

	availablePatterns := make([]string, 0)
	for _, name := range patternNames {
		if name != s.lastPattern {
			availablePatterns = append(availablePatterns, name)
		}
	}

	if len(availablePatterns) == 0 {
		availablePatterns = patternNames
	}

	chosenPattern := availablePatterns[rand.Intn(len(availablePatterns))]
	s.lastPattern = chosenPattern

	pattern := WalaszekPatterns[chosenPattern]
	example := pattern.Examples[rand.Intn(len(pattern.Examples))]

	prompt := fmt.Sprintf(walaszekPromptTemplate,
		userName,
		chosenPattern,
		pattern.Description,
		pattern.Structure,
		example,
		userTitle,
		userName,
		chosenPattern,
		chosenPattern,
	)

	message, err := s.client.Messages.New(ctx, anthropic.MessageNewParams{
		Model:     anthropic.ModelClaude3_5HaikuLatest,
		MaxTokens: 150,
		Messages: []anthropic.MessageParam{
			anthropic.NewUserMessage(anthropic.NewTextBlock(prompt)),
		},
	})

	if err != nil {
		slog.Error("failed to generate kudo rain", "error", err)
		return s.fallbackMessage(userName, userTitle), nil
	}

	for _, block := range message.Content {
		if block.Type == "text" {
			return block.Text, nil
		}
	}

	return s.fallbackMessage(userName, userTitle), nil
}

func (s *AnthropicService) fallbackMessage(userName, userTitle string) string {
	return fmt.Sprintf("<!channel> Kudo rain for @%s - like a superhero %s whose only power is making coffee disappear and Zoom calls awkward! 🎯☕", userName, userTitle)
}
