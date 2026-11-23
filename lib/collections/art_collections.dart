import '../models/artwork.dart';
import '../models/art_creation_date.dart';

/// A collection is an explainable, entirely local filter over *existing*
/// museum metadata. It does not invent an image subject or artistic movement.
class ArtCollection {
  const ArtCollection(this.id, this.names, this.hints);
  final String id;
  final Map<String, String> names;
  final Map<String, String> hints;

  String title(String language) => names[language] ?? names['en']!;
  String subtitle(String language) => hints[language] ?? hints['en']!;

  bool contains(Artwork art) => ArtCollections.matches(this, art);
}

class ArtCollections {
  ArtCollections._();

  /// Based on actual image pixels and available local artwork previews,
  /// never on an inferred artistic movement from titles or author names.
  static const colorFirst = ArtCollection('color-first',
    {'it':'Colori e capolavori', 'en':'Color and masterpieces',
     'fr':'Couleurs et chefs-d’œuvre', 'es':'Color y obras maestras',
     'de':'Farben und Meisterwerke', 'pt':'Cores e obras-primas'},
    {'it':'1200 dipinti selezionati per colore', 'en':'1200 color-selected paintings',
     'fr':'1200 tableaux choisis par couleur',
     'es':'1200 pinturas elegidas por color',
     'de':'1200 farblich ausgewählte Gemälde',
     'pt':'1200 pinturas selecionadas pela cor'});

  static const all = <ArtCollection>[
    ArtCollection('landscapes',
      {'it':'Paesaggi', 'en':'Landscapes', 'fr':'Paysages',
       'es':'Paisajes', 'de':'Landschaften', 'pt':'Paisagens'},
      {'it':'Titoli e soggetti verificabili', 'en':'Titles and documented subjects',
       'fr':'Titres et sujets documentés', 'es':'Títulos y temas documentados',
       'de':'Titel und dokumentierte Themen', 'pt':'Títulos e temas documentados'}),
    ArtCollection('portraits',
      {'it':'Ritratti', 'en':'Portraits', 'fr':'Portraits',
       'es':'Retratos', 'de':'Porträts', 'pt':'Retratos'},
      {'it':'Persone e autoritratti', 'en':'People and self-portraits',
       'fr':'Personnes et autoportraits', 'es':'Personas y autorretratos',
       'de':'Menschen und Selbstporträts', 'pt':'Pessoas e autorretratos'}),
    ArtCollection('flowers',
      {'it':'Fiori e giardini', 'en':'Flowers and gardens', 'fr':'Fleurs et jardins',
       'es':'Flores y jardines', 'de':'Blumen und Gärten', 'pt':'Flores e jardins'},
      {'it':'Natura nella pittura', 'en':'Nature in paintings',
       'fr':'La nature en peinture', 'es':'Naturaleza en pintura',
       'de':'Natur in der Malerei', 'pt':'Natureza na pintura'}),
    ArtCollection('seascapes',
      {'it':'Mare e acqua', 'en':'Seas and water', 'fr':'Mers et eaux',
       'es':'Mares y agua', 'de':'Meer und Wasser', 'pt':'Mares e água'},
      {'it':'Marine, fiumi e laghi', 'en':'Marine scenes, rivers and lakes',
       'fr':'Marines, fleuves et lacs', 'es':'Marinas, ríos y lagos',
       'de':'Seestücke, Flüsse und Seen', 'pt':'Marinhas, rios e lagos'}),
    ArtCollection('still-life',
      {'it':'Nature morte', 'en':'Still lifes', 'fr':'Natures mortes',
       'es':'Bodegones', 'de':'Stillleben', 'pt':'Naturezas-mortas'},
      {'it':'Oggetti e composizioni', 'en':'Objects and arrangements',
       'fr':'Objets et compositions', 'es':'Objetos y composiciones',
       'de':'Objekte und Arrangements', 'pt':'Objetos e composições'}),
    ArtCollection('modern-from-1950',
      {'it':'Dal 1950 a oggi', 'en':'From 1950 onward',
       'fr':'Depuis 1950', 'es':'Desde 1950',
       'de':'Seit 1950', 'pt':'Desde 1950'},
      {'it':'Arte moderna e contemporanea con immagini riutilizzabili',
       'en':'Modern and contemporary art with reusable images',
       'fr':'Art moderne et contemporain avec images réutilisables',
       'es':'Arte moderno y contemporáneo con imágenes reutilizables',
       'de':'Moderne und zeitgenössische Kunst mit frei nutzbaren Bildern',
       'pt':'Arte moderna e contemporânea com imagens reutilizáveis'}),
    ArtCollection('nineteenth-century',
      {'it':'Ottocento', 'en':'19th century', 'fr':'XIXe siècle',
       'es':'Siglo XIX', 'de':'19. Jahrhundert', 'pt':'Século XIX'},
      {'it':'Date esplicite nei metadati', 'en':'Explicit dates in museum records',
       'fr':'Dates explicites des musées', 'es':'Fechas explícitas del museo',
       'de':'Explizite Museumsdaten', 'pt':'Datas explícitas dos museus'}),
    ArtCollection('twentieth-century',
      {'it':'Novecento', 'en':'20th century', 'fr':'XXe siècle',
       'es':'Siglo XX', 'de':'20. Jahrhundert', 'pt':'Século XX'},
      {'it':'Date esplicite nei metadati', 'en':'Explicit dates in museum records',
       'fr':'Dates explicites des musées', 'es':'Fechas explícitas del museo',
       'de':'Explizite Museumsdaten', 'pt':'Datas explícitas dos museus'}),
    ArtCollection('museum-met',
      {'it':'The Met', 'en':'The Met', 'fr':'The Met',
       'es':'The Met', 'de':'The Met', 'pt':'The Met'},
      {'it':'Metropolitan Museum of Art', 'en':'Metropolitan Museum of Art',
       'fr':'Metropolitan Museum of Art', 'es':'Metropolitan Museum of Art',
       'de':'Metropolitan Museum of Art', 'pt':'Metropolitan Museum of Art'}),
    ArtCollection('museum-cleveland',
      {'it':'Cleveland', 'en':'Cleveland', 'fr':'Cleveland',
       'es':'Cleveland', 'de':'Cleveland', 'pt':'Cleveland'},
      {'it':'Cleveland Museum of Art', 'en':'Cleveland Museum of Art',
       'fr':'Cleveland Museum of Art', 'es':'Cleveland Museum of Art',
       'de':'Cleveland Museum of Art', 'pt':'Cleveland Museum of Art'}),
    ArtCollection('museum-nga',
      {'it':'National Gallery', 'en':'National Gallery', 'fr':'National Gallery',
       'es':'National Gallery', 'de':'National Gallery', 'pt':'National Gallery'},
      {'it':'Washington, D.C.', 'en':'Washington, D.C.',
       'fr':'Washington, D.C.', 'es':'Washington, D.C.',
       'de':'Washington, D.C.', 'pt':'Washington, D.C.'}),
    ArtCollection('museum-rijks',
      {'it':'Rijksmuseum', 'en':'Rijksmuseum', 'fr':'Rijksmuseum',
       'es':'Rijksmuseum', 'de':'Rijksmuseum', 'pt':'Rijksmuseum'},
      {'it':'Amsterdam', 'en':'Amsterdam', 'fr':'Amsterdam',
       'es':'Ámsterdam', 'de':'Amsterdam', 'pt':'Amsterdã'}),
    ArtCollection('museum-cooper-hewitt',
      {'it':'Cooper Hewitt', 'en':'Cooper Hewitt', 'fr':'Cooper Hewitt',
       'es':'Cooper Hewitt', 'de':'Cooper Hewitt', 'pt':'Cooper Hewitt'},
      {'it':'Design, grafica e arti applicate',
       'en':'Design, graphic and applied arts',
       'fr':'Design, arts graphiques et appliqués',
       'es':'Diseño, artes gráficas y aplicadas',
       'de':'Design, Grafik und angewandte Kunst',
       'pt':'Design, artes gráficas e aplicadas'}),
    ArtCollection('museum-hirshhorn',
      {'it':'Hirshhorn', 'en':'Hirshhorn', 'fr':'Hirshhorn',
       'es':'Hirshhorn', 'de':'Hirshhorn', 'pt':'Hirshhorn'},
      {'it':'Pittura, scultura e arti visive',
       'en':'Painting, sculpture and visual art',
       'fr':'Peinture, sculpture et arts visuels',
       'es':'Pintura, escultura y artes visuales',
       'de':'Malerei, Skulptur und bildende Kunst',
       'pt':'Pintura, escultura e artes visuais'}),
    ArtCollection('museum-african-art',
      {'it':'Museo d’arte africana', 'en':'National Museum of African Art',
       'fr':'Musée national d’art africain',
       'es':'Museo Nacional de Arte Africano',
       'de':'Nationalmuseum für afrikanische Kunst',
       'pt':'Museu Nacional de Arte Africana'},
      {'it':'Opere e materiali delle collezioni africane',
       'en':'Works and materials from African collections',
       'fr':'Œuvres et matériaux des collections africaines',
       'es':'Obras y materiales de colecciones africanas',
       'de':'Werke und Materialien afrikanischer Sammlungen',
       'pt':'Obras e materiais de coleções africanas'}),
    ArtCollection('museum-african-american-history',
      {'it':'Storia e cultura afroamericana',
       'en':'African American History and Culture',
       'fr':'Histoire et culture afro-américaines',
       'es':'Historia y cultura afroamericanas',
       'de':'Afroamerikanische Geschichte und Kultur',
       'pt':'História e cultura afro-americanas'},
      {'it':'Fotografia, stampa e arte del museo Smithsonian',
       'en':'Photography, prints and art from the Smithsonian museum',
       'fr':'Photographie, gravures et art du musée Smithsonian',
       'es':'Fotografía, grabados y arte del museo Smithsonian',
       'de':'Fotografie, Drucke und Kunst des Smithsonian',
       'pt':'Fotografia, gravuras e arte do museu Smithsonian'}),
    ArtCollection('museum-smithsonian',
      {'it':'Smithsonian', 'en':'Smithsonian', 'fr':'Smithsonian',
       'es':'Smithsonian', 'de':'Smithsonian', 'pt':'Smithsonian'},
      {'it':'Smithsonian Institution', 'en':'Smithsonian Institution',
       'fr':'Smithsonian Institution', 'es':'Smithsonian Institution',
       'de':'Smithsonian Institution', 'pt':'Smithsonian Institution'}),
  ];

  // Word boundaries use non-letters rather than substring matching. Thus
  // "sea" never matches "season". Metadata may be in several languages.
  static final _year19 = RegExp(r'(?<!\d)18\d{2}(?!\d)');
  static final _year20 = RegExp(r'(?<!\d)19\d{2}(?!\d)');
  static final _nineteenth = RegExp(
    r'19th century|xix(?:e|ème)? siècle|siglo xix|19\. jahrhundert',
    caseSensitive: false);
  static final _twentieth = RegExp(
    r'20th century|xx(?:e|ème)? siècle|siglo xx|20\. jahrhundert',
    caseSensitive: false);
  static final _nonLetter = RegExp(r'[^a-zà-ÿ0-9]+');

  static bool _hasTokens(Artwork art, List<String> aliases) {
    final searchable = [
      art.title, ...art.subjectTerms,
    ].join(' ').toLowerCase().replaceAll(_nonLetter, ' ');
    final bounded = ' $searchable ';
    return aliases.any((word) => bounded.contains(' $word '));
  }

  static bool matches(ArtCollection collection, Artwork art) {
    if (!art.displayable) return false;
    switch (collection.id) {
      case 'landscapes':
        return _hasTokens(art, ['landscape','landscapes','paesaggio',
          'paesaggi','paysage','paisaje','landschaft','landschap']);
      case 'portraits':
        return _hasTokens(art, ['portrait','portraits','ritratto','ritratti',
          'retrato','porträt','portraiture','self portrait']);
      case 'flowers':
        return _hasTokens(art, ['flower','flowers','fiore','fiori','floral',
          'garden','gardens','giardino','giardini','fleur','fleurs','blumen']);
      case 'seascapes':
        return _hasTokens(art, ['sea','seascape','marine','ocean','coast',
          'shore','river','lake','mare','marina','lago','fiume','mer']);
      case 'still-life':
        return _hasTokens(art, ['still life','stillleben','natura morta',
          'nature morte','bodegón','bodegon','stilleven','naturaleza muerta']);
      case 'modern-from-1950':
        return ArtCreationDate.explicitYearFrom1950(art.date) != null;
      case 'nineteenth-century':
        return _year19.hasMatch(art.date) || _nineteenth.hasMatch(art.date);
      case 'twentieth-century':
        return _year20.hasMatch(art.date) || _twentieth.hasMatch(art.date);
      case 'museum-met': return art.museumSource == 'met';
      case 'museum-cleveland': return art.museumSource == 'cleveland';
      case 'museum-nga': return art.museumSource == 'nga';
      case 'museum-rijks': return art.museumSource == 'rijks';
      case 'museum-cooper-hewitt':
        return art.museumName == 'Cooper Hewitt, Smithsonian Design Museum';
      case 'museum-hirshhorn':
        return art.museumName == 'Hirshhorn Museum and Sculpture Garden';
      case 'museum-african-art':
        return art.museumName == 'Smithsonian National Museum of African Art';
      case 'museum-african-american-history':
        return art.museumName ==
          'Smithsonian National Museum of African American History and Culture';
      case 'museum-smithsonian': return art.museumSource == 'smithsonian';
      default: return false;
    }
  }

  static List<Artwork> members(
      ArtCollection collection, Iterable<Artwork> catalog) =>
      List.unmodifiable(catalog.where(collection.contains));

  static List<ArtCollection> available(Iterable<Artwork> catalog,
      {int minMembers = 3}) {
    final items = catalog.toList(growable: false);
    return all.where((collection) {
      var found = 0;
      for (final artwork in items) {
        if (collection.contains(artwork) && ++found >= minMembers) return true;
      }
      return false;
    }).toList(growable: false);
  }
}
