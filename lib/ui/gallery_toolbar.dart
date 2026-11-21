import 'package:flutter/material.dart';
import 'localization.dart';
import 'parchment.dart';

/// Floats above the unchanged full-screen canvas; search is always the exact
/// central third of available width, with nothing wider until it is tapped.
class ArtDriftToolbar extends StatelessWidget {
  const ArtDriftToolbar({super.key, required this.onSearch,
    required this.onSettings, required this.onFavorites});
  final VoidCallback onSearch;
  final VoidCallback onSettings;
  final VoidCallback onFavorites;

  @override
  Widget build(BuildContext context) =>
      ValueListenableBuilder<String>(
        valueListenable: ArtDriftLocale.current,
        builder: (context, language, _) => LayoutBuilder(
          builder: (context, constraints) {
            final w = constraints.maxWidth;
            return SizedBox(height: 53, child: Stack(children: [
              Positioned(left: w / 3, width: w / 3, top: 5,
                child: Semantics(key: const Key('artdrift-search-control'), button: true, label: ArtDriftLocale.text('searchTitle'),
                  child: Material(color: Colors.transparent,
                    child: InkWell(
                      onTap: onSearch, borderRadius: BorderRadius.circular(9),
                      child: OrnateFrame(
                        padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 8),
                        child: Row(mainAxisAlignment: MainAxisAlignment.center,
                          mainAxisSize: MainAxisSize.min, children: [
                            const BrushMark(size: 19),
                            const SizedBox(width: 5),
                            Flexible(child: Text(ArtDriftLocale.text('search'),
                              maxLines: 1, overflow: TextOverflow.ellipsis,
                              style: const TextStyle(color: ArtPaper.ink,
                                fontFamily:'serif',fontSize: 13,
                                fontWeight: FontWeight.w600))),
                          ]),
                      )),
                  )),
              ),
              Positioned(right: 64, top: 5, child: Semantics(
                key: const Key('artdrift-favorites-control'),
                button: true, label: ArtDriftLocale.text('favorites'),
                child: Material(color: Colors.transparent,
                  child: InkWell(onTap: onFavorites,
                    borderRadius: BorderRadius.circular(9),
                    child: OrnateFrame(padding: const EdgeInsets.all(8),
                      child: const SizedBox(width: 21, height: 21,
                        child: Icon(Icons.favorite_border_rounded,
                          color: ArtPaper.ink, size: 21))),
                  )),
              )),
              Positioned(right: 12, top: 5, child: Semantics(
                key: const Key('artdrift-settings-control'),
                button: true,label: ArtDriftLocale.text('settings'),
                child: Material(color: Colors.transparent,
                  child: InkWell(onTap: onSettings,
                    borderRadius: BorderRadius.circular(9),
                    child: OrnateFrame(padding: const EdgeInsets.all(8),
                      child: const SizedBox(width: 21,height: 21,
                        child: Icon(Icons.settings_rounded,
                          color: ArtPaper.ink,size: 21))),
                  )),
              )),
            ]));
          },
        ),
      );
}
