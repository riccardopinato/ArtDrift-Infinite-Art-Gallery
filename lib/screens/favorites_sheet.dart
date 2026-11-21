import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../models/artwork.dart';
import '../services/favorites.dart';
import '../ui/localization.dart';
import '../ui/parchment.dart';

/// Favorites in the same parchment visual language as Art Drift search/settings.
Future<Artwork?> showArtFavoritesSheet(
  BuildContext context, {
  required Favorites favorites,
  required List<Artwork> catalog,
  required Future<void> Function(Artwork) onToggleFavorite,
}) => showModalBottomSheet<Artwork>(
  context: context,
  backgroundColor: Colors.transparent,
  isScrollControlled: true,
  useSafeArea: true,
  builder: (_) => _FavoritesSheet(
    favorites: favorites, catalog: catalog, onToggleFavorite: onToggleFavorite),
);

class _FavoritesSheet extends StatefulWidget {
  const _FavoritesSheet({required this.favorites,
    required this.catalog, required this.onToggleFavorite});
  final Favorites favorites;
  final List<Artwork> catalog;
  final Future<void> Function(Artwork) onToggleFavorite;

  @override
  State<_FavoritesSheet> createState() => _FavoritesSheetState();
}

class _FavoritesSheetState extends State<_FavoritesSheet> {
  bool _busy = false;

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
          : ListView.builder(
              key: const Key('artdrift-favorites-list'),
              itemCount: saved.length,
              itemBuilder: (context, index) {
                final art = saved[index];
                return Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: OrnateFrame(shadow: false, padding: EdgeInsets.zero,
                    child: ListTile(
                      contentPadding: const EdgeInsets.fromLTRB(9, 5, 5, 5),
                      leading: ClipRRect(borderRadius: BorderRadius.circular(3),
                        child: SizedBox(width: 55, height: 70,
                          child: art.hasBundledPreview
                            ? Image.asset(art.bootstrapAsset,
                                fit: BoxFit.cover, cacheWidth: 120,
                                errorBuilder: (_, __, ___) =>
                                  const ColoredBox(color: ArtPaper.faded,
                                    child: Icon(Icons.image_outlined,
                                      color: ArtPaper.ink)))
                            : Image.network(art.imageUrl(width: 200),
                                fit: BoxFit.cover, cacheWidth: 120,
                                errorBuilder: (_, __, ___) =>
                                  const ColoredBox(color: ArtPaper.faded,
                                    child: Icon(Icons.image_outlined,
                                      color: ArtPaper.ink))))),
                      title: Text(art.title, maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(color: ArtPaper.ink,
                          fontFamily: 'serif', fontWeight: FontWeight.w600)),
                      subtitle: Text(art.artist.isEmpty ? '—' : art.artist,
                        maxLines: 1, overflow: TextOverflow.ellipsis,
                        style: const TextStyle(color: Color(0xFF735A3E),
                          fontSize: 11)),
                      trailing: IconButton(
                        key: Key('artdrift-unfavorite-${art.catalogKey}'),
                        tooltip: ArtDriftLocale.text('removeFavorite'),
                        icon: const Icon(Icons.favorite, color: ArtPaper.gold),
                        onPressed: _busy ? null : () => _remove(art)),
                      onTap: () => Navigator.pop(context, art),
                    )),
                );
              })),
      ],
    )));
  }
}
