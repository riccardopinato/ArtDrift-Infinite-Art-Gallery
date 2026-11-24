import 'dart:math' as math;
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import '../models/artwork.dart';
import '../ui/artwork_preview_image.dart';
import '../services/favorites.dart';
import '../ui/localization.dart';
import '../ui/parchment.dart';

/// Favorites in the same parchment visual language as Art Drift search/settings.
Future<Artwork?> showArtFavoritesSheet(
  BuildContext context, {
  required Favorites favorites,
  required List<Artwork> catalog,
  required Future<void> Function(Artwork) onToggleFavorite,
  Listenable? changes,
}) => showModalBottomSheet<Artwork>(
  context: context,
  backgroundColor: Colors.transparent,
  isScrollControlled: true,
  useSafeArea: true,
  builder: (_) => _FavoritesSheet(
    favorites: favorites, catalog: catalog,
    onToggleFavorite: onToggleFavorite, changes: changes),
);

class _FavoritesSheet extends StatefulWidget {
  const _FavoritesSheet({required this.favorites,
    required this.catalog, required this.onToggleFavorite, this.changes});
  final Listenable? changes;
  final Favorites favorites;
  final List<Artwork> catalog;
  final Future<void> Function(Artwork) onToggleFavorite;

  @override
  State<_FavoritesSheet> createState() => _FavoritesSheetState();
}

class _FavoritesSheetState extends State<_FavoritesSheet> {
  bool _busy = false;

  void _refresh() {
    if (mounted) setState(() {});
  }

  @override
  void initState() {
    super.initState();
    widget.changes?.addListener(_refresh);
  }

  @override
  void dispose() {
    widget.changes?.removeListener(_refresh);
    super.dispose();
  }

  Future<void> _remove(Artwork artwork) async {
    if (_busy) return;
    setState(() => _busy = true);
    try {
      await widget.onToggleFavorite(artwork);
      if (mounted) setState(() {});
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final mq = MediaQuery.of(context);
    final available = mq.size.height - mq.viewInsets.bottom - 24;
    final height = math.max(280.0, math.min(mq.size.height * .82, available));
    final saved = widget.favorites.savedFrom(widget.catalog);
    return SizedBox(height: height, child: ParchmentPanel(child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(children: [
          const Icon(Icons.favorite, color: ArtPaper.gold, size: 23),
          const SizedBox(width: 12),
          Expanded(child: Text(ArtDriftLocale.text('favorites'),
            style: const TextStyle(color: ArtPaper.ink, fontSize: 25,
              fontFamily: 'serif', fontWeight: FontWeight.bold))),
          IconButton(tooltip: ArtDriftLocale.text('close'),
            icon: const Icon(Icons.close, color: ArtPaper.ink),
            onPressed: () => Navigator.pop(context)),
        ]),
        const Divider(color: ArtPaper.gold),
        const SizedBox(height: 8),
        Text('${saved.length} · ${ArtDriftLocale.text('favoritesSubtitle')}',
          style: const TextStyle(color: Color(0xFF745936), fontSize: 12)),
        const SizedBox(height: 12),
        Expanded(child: saved.isEmpty
          ? Center(child: Padding(
              padding: const EdgeInsets.all(22),
              child: Text(ArtDriftLocale.text('favoritesEmpty'),
                textAlign: TextAlign.center,
                style: const TextStyle(color: ArtPaper.ink,
                  fontFamily: 'serif', fontSize: 16))))
          : LayoutBuilder(builder: (context, bounds) {
              final count = bounds.maxWidth >= 640 ? 4
                  : bounds.maxWidth >= 440 ? 3 : 2;
              return GridView.builder(
                key: const Key('artdrift-favorites-grid'),
                padding: const EdgeInsets.only(bottom: 16),
                itemCount: saved.length,
                gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: count,
                  crossAxisSpacing: 9, mainAxisSpacing: 10,
                  childAspectRatio: count == 4 ? .70 : .61),
                itemBuilder: (context, index) {
                  final art = saved[index];
                  return OrnateFrame(
                    shadow: false, padding: EdgeInsets.zero, radius: 5,
                    child: Material(color: Colors.transparent,
                      child: InkWell(
                        key: Key('artdrift-favorite-open-${art.catalogKey}'),
                        onTap: () => Navigator.pop(context, art),
                        child: Padding(
                          padding: const EdgeInsets.all(7),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Expanded(child: Stack(children: [
                                Positioned.fill(child: ClipRRect(
                                  borderRadius: BorderRadius.circular(2),
                                  child: ColoredBox(
                                    color: const Color(0xFFDED1B9),
                                    child: ArtworkPreviewImage(
                                      artwork: art,
                                      fit: BoxFit.contain, cacheWidth: 240),
                                  ))),
                                Positioned(right: 3, top: 3, child: DecoratedBox(
                                  decoration: BoxDecoration(
                                    color: const Color(0xEAF4E9D4),
                                    borderRadius: BorderRadius.circular(4),
                                    border: Border.all(
                                      color: ArtPaper.gold)),
                                  child: SizedBox(width: 42, height: 42,
                                    child: IconButton(
                                      key: Key('artdrift-unfavorite-${art.catalogKey}'),
                                      padding: EdgeInsets.zero,
                                      tooltip: ArtDriftLocale.text('removeFavorite'),
                                      icon: const Icon(Icons.favorite,
                                        color: ArtPaper.gold, size: 20),
                                      onPressed: _busy
                                          ? null : () => _remove(art),
                                    )))),
                              ])),
                              const SizedBox(height: 8),
                              Text(art.title, maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                                style: const TextStyle(
                                  color: ArtPaper.ink, fontFamily: 'serif',
                                  fontSize: 13, fontWeight: FontWeight.w600)),
                              const SizedBox(height: 3),
                              Text(art.artist.isEmpty ? '—' : art.artist,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: const TextStyle(
                                  color: Color(0xFF735A3E), fontSize: 10)),
                            ],
                          ),
                        ),
                      ),
                    ),
                  );
                },
              );
            })),
      ],
    )));
  }
}
