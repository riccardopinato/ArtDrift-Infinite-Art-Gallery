import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// UI only. Artwork titles, artist names and museum text remain in their
/// authoritative original language until a reviewed translation is available.
abstract final class ArtDriftLocale {
  static final ValueNotifier<String> current = ValueNotifier<String>('it');
  static const codes = ['it', 'en', 'fr', 'es', 'de', 'pt'];
  static const names = {
    'it': 'Italiano', 'en': 'English', 'fr': 'Français',
    'es': 'Español', 'de': 'Deutsch', 'pt': 'Português',
  };

  static Future<void> initialize() async {
    final prefs = await SharedPreferences.getInstance();
    final code = prefs.getString('artdrift.locale') ?? 'it';
    current.value = codes.contains(code) ? code : 'it';
  }

  static Future<void> select(String code) async {
    if (!codes.contains(code)) return;
    current.value = code;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('artdrift.locale', code);
  }

  static String text(String key) =>
      (_messages[current.value] ?? _messages['it']!)[key] ??
      _messages['it']![key] ?? key;

  static const Map<String, Map<String, String>> _messages = {
    'it': {
      'search': 'Cerca', 'searchTitle': 'Cerca nell’arte',
      'searchHint': 'Autore, titolo o soggetto', 'filterAll': 'Tutto',
      'filterArtist': 'Autore', 'filterTitle': 'Titolo',
      'filterSubject': 'Soggetto', 'suggestions': 'Suggerimenti',
      'results': 'Opere trovate', 'noResults': 'Nessuna opera trovata nel catalogo locale',
      'museumSearch': 'Cerca anche nei musei', 'museumSearching': 'Interroghiamo i cataloghi…',
      'museumResults': 'Risultati dai musei', 'museumUnavailable': 'Musei non raggiungibili',
      'queryDisclosure': 'La ricerca nei musei invia il testo cercato ai rispettivi cataloghi.',
      'subjectNotice': 'Ricerca nei titoli e nei metadati: riconoscimento visivo non ancora attivo.',
      'settings': 'Impostazioni', 'language': 'Lingua dell’interfaccia',
      'languageNote': 'I titoli delle opere restano nella lingua originale del museo.',
      'about': 'Privacy e informazioni', 'pro': 'ArtDrift Pro',
      'proComing': 'Disponibile prossimamente su Google Play',
      'proDescription': 'Una futura versione Pro potrà eliminare la pubblicità e offrire strumenti aggiuntivi. Nessun acquisto è attivo in questa versione.',
      'proStatus': 'Piano attuale: gratuito', 'privacyTitle': 'Informazioni e privacy',
      'privacyBody': 'La galleria iniziale e i preferiti rimangono sul dispositivo. La lingua e la posizione del canvas sono salvate localmente. Le immagini dettagliate sono richieste ai musei solo quando necessario. Le ricerche locali non vengono inviate ad ArtDrift. Se avvii la ricerca internazionale, la parola cercata viene inviata direttamente alle API dei musei selezionati. Non sono attivi account, annunci pubblicitari, pagamenti o analisi utente. Prima della pubblicazione sul Play Store sarà necessaria un’informativa completa ospitata online.',
      'license': 'Opere e licenze', 'licenseBody': 'Le opere incorporate provengono da Art Institute of Chicago Open Access. I nuovi risultati sono accettati solo se segnalati come pubblico dominio/CC0 dai rispettivi musei. Per ogni opera consulta la scheda ufficiale.',
      'close': 'Chiudi', 'back': 'Indietro', 'offline': 'Risultati locali disponibili anche offline',
      'emptyQuery': 'Scrivi almeno una lettera per iniziare.',
    },
    'en': {
      'search': 'Search', 'searchTitle': 'Explore the art', 'searchHint': 'Artist, title or subject',
      'filterAll': 'All', 'filterArtist': 'Artist', 'filterTitle': 'Title',
      'filterSubject': 'Subject', 'suggestions': 'Suggestions', 'results': 'Artworks',
      'noResults': 'No results in the local collection',
      'museumSearch': 'Search museum collections', 'museumSearching': 'Searching museum catalogs…',
      'museumResults': 'Museum results', 'museumUnavailable': 'Museums unavailable',
      'queryDisclosure': 'Museum search sends your query to museum catalogs.',
      'subjectNotice': 'Searches titles and metadata; visual recognition is not active yet.',
      'settings': 'Settings', 'language': 'Interface language',
      'languageNote': 'Artwork titles remain in the museum’s original language.',
      'about': 'Privacy and information', 'pro': 'ArtDrift Pro',
      'proComing': 'Coming later on Google Play',
      'proDescription': 'Pro may remove ads and unlock additional features. Purchases are not active in this build.',
      'proStatus': 'Current plan: Free', 'privacyTitle': 'Information and privacy',
      'privacyBody': 'The initial gallery and favorites remain on your device. Language and canvas position are stored locally. Detailed images are fetched from museums only when needed. Local searches are not sent to ArtDrift. International searches send your query directly to participating museums’ APIs. There are no accounts, ads, purchases or analytics active. A fully hosted privacy policy is required before Play Store publication.',
      'license': 'Art and licenses', 'licenseBody': 'Bundled works come from Art Institute of Chicago Open Access. International results are eligible only when the source museum flags them as public domain/CC0. See each official record.',
      'close': 'Close', 'back': 'Back', 'offline': 'Local results also work offline',
      'emptyQuery': 'Enter a letter to begin.',
    },
    'fr': {
      'search': 'Recherche', 'searchTitle': 'Explorer les œuvres', 'searchHint': 'Artiste, titre ou sujet',
      'filterAll': 'Tout', 'filterArtist': 'Artiste', 'filterTitle': 'Titre',
      'filterSubject': 'Sujet', 'suggestions': 'Suggestions', 'results': 'Œuvres',
      'noResults': 'Aucun résultat dans la collection locale',
      'museumSearch': 'Chercher dans les musées', 'museumSearching': 'Recherche dans les musées…',
      'museumResults': 'Résultats des musées', 'museumUnavailable': 'Musées indisponibles',
      'queryDisclosure': 'La recherche envoie votre requête aux musées.',
      'subjectNotice': 'Recherche dans les titres et métadonnées ; analyse visuelle indisponible.',
      'settings': 'Paramètres', 'language': 'Langue de l’interface',
      'languageNote': 'Les titres conservent la langue originale du musée.',
      'about': 'Confidentialité et informations', 'pro': 'ArtDrift Pro',
      'proComing': 'Bientôt sur Google Play',
      'proDescription': 'Pro pourra supprimer les publicités et offrir des fonctions supplémentaires. Aucun achat actif.',
      'proStatus': 'Offre actuelle : gratuite', 'privacyTitle': 'Informations et confidentialité',
      'privacyBody': 'La galerie initiale, les favoris, la langue et la position du canevas sont conservés sur l’appareil. Les images haute définition sont chargées à la demande. La recherche locale reste sur l’appareil. Une recherche internationale envoie votre requête aux API des musées. Aucun compte, annonce, achat ou analyse utilisateur n’est activé. Une politique de confidentialité publique est requise avant diffusion.',
      'license': 'Œuvres et licences', 'licenseBody': 'Les œuvres initiales viennent de l’Art Institute of Chicago Open Access ; les résultats externes doivent être signalés domaine public ou CC0.',
      'close': 'Fermer', 'back': 'Retour', 'offline': 'Recherche locale hors ligne',
      'emptyQuery': 'Saisissez une lettre pour commencer.',
    },
    'es': {
      'search': 'Buscar', 'searchTitle': 'Explorar el arte', 'searchHint': 'Autor, título o tema',
      'filterAll': 'Todo', 'filterArtist': 'Autor', 'filterTitle': 'Título',
      'filterSubject': 'Tema', 'suggestions': 'Sugerencias', 'results': 'Obras',
      'noResults': 'No hay resultados en la colección local',
      'museumSearch': 'Buscar en museos', 'museumSearching': 'Buscando en museos…',
      'museumResults': 'Resultados de museos', 'museumUnavailable': 'Museos no disponibles',
      'queryDisclosure': 'La búsqueda envía tu consulta a los museos.',
      'subjectNotice': 'Busca en títulos y metadatos; el reconocimiento visual aún no está activo.',
      'settings': 'Ajustes', 'language': 'Idioma de la interfaz',
      'languageNote': 'Los títulos conservan el idioma original del museo.',
      'about': 'Privacidad e información', 'pro': 'ArtDrift Pro',
      'proComing': 'Próximamente en Google Play',
      'proDescription': 'Pro podrá quitar anuncios y añadir herramientas. Las compras no están activas.',
      'proStatus': 'Plan actual: gratuito', 'privacyTitle': 'Información y privacidad',
      'privacyBody': 'La galería inicial, favoritos, idioma y posición se guardan en el dispositivo. Las imágenes detalladas se descargan bajo demanda. La búsqueda local permanece en el dispositivo. Buscar en museos envía la consulta a sus API. No hay cuentas, anuncios, compras ni analítica activa. Antes de publicar será necesaria una política pública.',
      'license': 'Obras y licencias', 'licenseBody': 'Las obras iniciales proceden de Art Institute of Chicago Open Access; los resultados externos deben figurar como dominio público o CC0.',
      'close': 'Cerrar', 'back': 'Volver', 'offline': 'Búsqueda local sin conexión',
      'emptyQuery': 'Escribe una letra para empezar.',
    },
    'de': {
      'search': 'Suche', 'searchTitle': 'Kunst entdecken', 'searchHint': 'Künstler, Titel oder Motiv',
      'filterAll': 'Alles', 'filterArtist': 'Künstler', 'filterTitle': 'Titel',
      'filterSubject': 'Motiv', 'suggestions': 'Vorschläge', 'results': 'Werke',
      'noResults': 'Keine Ergebnisse in der lokalen Sammlung',
      'museumSearch': 'In Museen suchen', 'museumSearching': 'Museen werden durchsucht…',
      'museumResults': 'Museumsergebnisse', 'museumUnavailable': 'Museen nicht erreichbar',
      'queryDisclosure': 'Die Museumssuche sendet Ihre Anfrage an die Museen.',
      'subjectNotice': 'Suche in Titeln und Metadaten; keine visuelle Erkennung.',
      'settings': 'Einstellungen', 'language': 'Sprache der Oberfläche',
      'languageNote': 'Werktitel bleiben in der Originalsprache des Museums.',
      'about': 'Datenschutz und Informationen', 'pro': 'ArtDrift Pro',
      'proComing': 'Demnächst bei Google Play',
      'proDescription': 'Pro kann Werbung entfernen und Extras anbieten. Käufe sind noch nicht aktiv.',
      'proStatus': 'Aktueller Plan: Kostenlos', 'privacyTitle': 'Datenschutz und Informationen',
      'privacyBody': 'Startgalerie, Favoriten, Sprache und Position bleiben auf dem Gerät. Große Bilder werden nur bei Bedarf geladen. Lokale Suche bleibt lokal; Museumssuche sendet Suchbegriffe an die APIs der Museen. Keine Konten, Werbung, Käufe oder Analytik sind aktiv. Vor Veröffentlichung ist eine öffentliche Datenschutzerklärung erforderlich.',
      'license': 'Werke und Lizenzen', 'licenseBody': 'Die ersten Werke stammen aus dem Art Institute of Chicago Open Access. Externe Ergebnisse müssen als gemeinfrei oder CC0 gekennzeichnet sein.',
      'close': 'Schließen', 'back': 'Zurück', 'offline': 'Lokale Suche funktioniert offline',
      'emptyQuery': 'Einen Buchstaben eingeben.',
    },
    'pt': {
      'search': 'Pesquisar', 'searchTitle': 'Explorar arte', 'searchHint': 'Artista, título ou tema',
      'filterAll': 'Tudo', 'filterArtist': 'Artista', 'filterTitle': 'Título',
      'filterSubject': 'Tema', 'suggestions': 'Sugestões', 'results': 'Obras',
      'noResults': 'Sem resultados na coleção local',
      'museumSearch': 'Pesquisar em museus', 'museumSearching': 'Pesquisando nos museus…',
      'museumResults': 'Resultados dos museus', 'museumUnavailable': 'Museus indisponíveis',
      'queryDisclosure': 'A pesquisa envia o termo para as APIs dos museus.',
      'subjectNotice': 'Pesquisa títulos e metadados; análise visual ainda indisponível.',
      'settings': 'Definições', 'language': 'Idioma da interface',
      'languageNote': 'Os títulos permanecem no idioma original do museu.',
      'about': 'Privacidade e informações', 'pro': 'ArtDrift Pro',
      'proComing': 'Em breve no Google Play',
      'proDescription': 'O Pro poderá remover anúncios e incluir recursos extras. Compras não estão ativas.',
      'proStatus': 'Plano atual: gratuito', 'privacyTitle': 'Informações e privacidade',
      'privacyBody': 'Galeria inicial, favoritos, idioma e posição são guardados no dispositivo. Imagens maiores são carregadas conforme necessário. Pesquisas locais ficam no aparelho; pesquisas internacionais enviam o termo às APIs dos museus. Sem contas, anúncios, compras ou análises ativas. Antes de publicar, será necessária uma política pública.',
      'license': 'Obras e licenças', 'licenseBody': 'As obras iniciais são do Art Institute of Chicago Open Access. Resultados externos devem ter indicação domínio público ou CC0.',
      'close': 'Fechar', 'back': 'Voltar', 'offline': 'Pesquisa local também sem internet',
      'emptyQuery': 'Digite uma letra para começar.',
    },
  };
}
