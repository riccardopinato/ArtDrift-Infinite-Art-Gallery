import 'dart:convert';
import 'package:http/http.dart' as http;

/// Read-only museum metadata API. Kept separate from Supabase user favorites.
/// No call is made unless an explicit HTTPS D1 Worker URL is supplied at build.
class MuseumCloudWork {
  const MuseumCloudWork({
    required this.key, required this.title, required this.museum,
    required this.artist, required this.date, required this.medium,
    required this.license, required this.credit,
    required this.rightsEvidenceUrl,
    this.sourceUrl, this.imageUrl,
  });

  final String key,title,museum,artist,date,medium,license,credit;
  final String rightsEvidenceUrl;
  final String? sourceUrl,imageUrl;

  static const _imageHosts=<String>{
    'www.artic.edu','images.metmuseum.org',
    'openaccess-cdn.clevelandart.org','clevelandart.org',
    'www.clevelandart.org','iiif.micr.io','api.nga.gov','media.nga.gov',
    'media.getty.edu','ids.si.edu','www.si.edu','si.edu','iip.smk.dk',
    'iip-thumb.smk.dk','api.artsmia.org','images.thewalters.org',
    'art.thewalters.org','upload.wikimedia.org',
  };
  static const _detailHosts=<String>{
    'www.artic.edu','www.metmuseum.org','metmuseum.org',
    'www.clevelandart.org','clevelandart.org','www.rijksmuseum.nl',
    'rijksmuseum.nl','data.rijksmuseum.nl','www.nga.gov','nga.gov',
    'www.getty.edu','getty.edu','data.getty.edu','www.si.edu','si.edu',
    'americanart.si.edu','npg.si.edu','asia.si.edu',
    'open.smk.dk','www.open.smk.dk','collections.artsmia.org',
    'art.thewalters.org','www.thewalters.org','commons.wikimedia.org',
  };
  static bool _https(String? value,Set<String> allowed){
    if(value==null)return false;
    final uri=Uri.tryParse(value);
    return uri!=null && uri.scheme=='https' && uri.userInfo.isEmpty &&
        allowed.contains(uri.host) && (!uri.hasPort || uri.port==443);
  }
  static MuseumCloudWork? parse(Map<String,dynamic> item){
    String get(String key)=>item[key] is String ?
        (item[key] as String).trim() : '';
    final key=get('source_key'),title=get('title'),museum=get('museum_name');
    final license=get('rights_license');
    if(!RegExp(r'^[a-z]{2,16}:[0-9]{1,15}$').hasMatch(key) ||
       title.isEmpty || museum.isEmpty ||
       !(const <String>{'CC0','Public Domain','Public Domain Mark',
         'CC BY 3.0','CC BY 4.0','CC BY-SA 3.0',
         'CC BY-SA 4.0','CC0 1.0','Public Domain Mark 1.0'}.contains(license) ||
         license.startsWith('Public Domain / ')))return null;
    final proof=get('rights_evidence_url');
    final link=proof.isEmpty?null:Uri.tryParse(proof);
    if(link==null || link.scheme!='https' || link.userInfo.isNotEmpty)return null;
    final image=get('thumbnail_url');
    final detail=get('source_url');
    return MuseumCloudWork(
      key:key,title:title,museum:museum,artist:get('artist'),
      date:get('date'),medium:get('medium'),license:license,
      credit:get('credit_line'),rightsEvidenceUrl:proof,
      sourceUrl:_https(detail,_detailHosts)?detail:null,
      imageUrl:_https(image,_imageHosts)?image:null,
    );
  }
}

class MuseumCloudPage {
  const MuseumCloudPage(this.works,this.nextCursor);
  final List<MuseumCloudWork> works;
  final String? nextCursor;
}

class MuseumCloudCatalog {
  MuseumCloudCatalog({String? baseUrl,http.Client? client}):
      _base=baseUrl??const String.fromEnvironment('ARTDRIFT_CATALOG_API_BASE'),
      _client=client??http.Client();
  final String _base;
  final http.Client _client;

  bool get enabled {
    final uri=Uri.tryParse(_base);
    return uri!=null && uri.scheme=='https' && uri.host.isNotEmpty &&
      uri.userInfo.isEmpty && (!uri.hasPort || uri.port==443) &&
      uri.query.isEmpty && !uri.hasFragment;
  }

  // Explicit release gate. An existing D1 stage and Worker deployment do
  // not automatically make these works visible in the mobile app.
  bool get approvedModernEnabled =>
      enabled && const bool.fromEnvironment(
          'ARTDRIFT_ENABLE_APPROVED_MODERN',defaultValue:false);

  Future<MuseumCloudPage> approvedModern({String? cursor}) async {
    if(!approvedModernEnabled)throw StateError('Modern catalog not enabled');
    if(cursor!=null && !RegExp(r'^\d{1,4}
    String scope='all',String? cursor,
  }) async {
    if(!enabled)throw StateError('D1 museum API not configured');
    if(query.trim().length<2 || query.length>90)throw ArgumentError('Query length');
    if(!const <String>['all','artist','title'].contains(scope)) {
      throw ArgumentError('Scope');
    }
    if(cursor!=null && !RegExp(r'^\d{1,4}$').hasMatch(cursor)) {
      throw ArgumentError('Cursor');
    }
    final base=Uri.parse(_base);
    final prefix=base.path.endsWith('/') ?
      base.path.substring(0,base.path.length-1):base.path;
    final uri=base.replace(path:'$prefix/api/v1/museum-search',
      queryParameters:{'q':query.trim(),'scope':scope,
        if(cursor!=null)'cursor':cursor});
    final response=await _client.get(uri,headers:{
      'Accept':'application/json',
    }).timeout(const Duration(seconds:12));
    if(response.statusCode!=200) {
      throw StateError('Museum cloud HTTP '+response.statusCode.toString());
    }
    final doc=jsonDecode(utf8.decode(response.bodyBytes));
    if(doc is! Map || doc['source']!='ArtDrift-Museums' ||
       doc['works'] is! List)throw const FormatException('Invalid museum D1 response');
    final works=<MuseumCloudWork>[];
    for(final item in doc['works'] as List){
      if(item is Map<String,dynamic>){
        final work=MuseumCloudWork.parse(item);
        if(work!=null)works.add(work);
      }
      if(works.length>=24)break;
    }
    final next=doc['next_cursor'];
    return MuseumCloudPage(works,
      next is String && RegExp(r'^\d{1,4}$').hasMatch(next)?next:null);
  }
  void close()=>_client.close();
}
).hasMatch(cursor)){
      throw ArgumentError('Cursor');
    }
    final base=Uri.parse(_base);
    final prefix=base.path.endsWith('/') ?
      base.path.substring(0,base.path.length-1):base.path;
    final uri=base.replace(path:'$prefix/api/v1/modern-approved',
      queryParameters:{if(cursor!=null)'cursor':cursor});
    final response=await _client.get(uri,headers:{'Accept':'application/json'})
        .timeout(const Duration(seconds:12));
    if(response.statusCode!=200){
      throw StateError('Approved-modern HTTP '+response.statusCode.toString());
    }
    final doc=jsonDecode(utf8.decode(response.bodyBytes));
    if(doc is! Map || doc['source']!='ArtDrift-Modern-Approved' ||
       doc['works'] is! List)throw const FormatException('Invalid approved-modern response');
    final works=<MuseumCloudWork>[];
    for(final item in doc['works'] as List){
      if(item is Map<String,dynamic>){
        final work=MuseumCloudWork.parse(item);
        if(work!=null)works.add(work);
      }
      if(works.length>=24)break;
    }
    final next=doc['next_cursor'];
    return MuseumCloudPage(works,
      next is String && RegExp(r'^\d{1,4}
    String scope='all',String? cursor,
  }) async {
    if(!enabled)throw StateError('D1 museum API not configured');
    if(query.trim().length<2 || query.length>90)throw ArgumentError('Query length');
    if(!const <String>['all','artist','title'].contains(scope)) {
      throw ArgumentError('Scope');
    }
    if(cursor!=null && !RegExp(r'^\d{1,4}$').hasMatch(cursor)) {
      throw ArgumentError('Cursor');
    }
    final base=Uri.parse(_base);
    final prefix=base.path.endsWith('/') ?
      base.path.substring(0,base.path.length-1):base.path;
    final uri=base.replace(path:'$prefix/api/v1/museum-search',
      queryParameters:{'q':query.trim(),'scope':scope,
        if(cursor!=null)'cursor':cursor});
    final response=await _client.get(uri,headers:{
      'Accept':'application/json',
    }).timeout(const Duration(seconds:12));
    if(response.statusCode!=200) {
      throw StateError('Museum cloud HTTP '+response.statusCode.toString());
    }
    final doc=jsonDecode(utf8.decode(response.bodyBytes));
    if(doc is! Map || doc['source']!='ArtDrift-Museums' ||
       doc['works'] is! List)throw const FormatException('Invalid museum D1 response');
    final works=<MuseumCloudWork>[];
    for(final item in doc['works'] as List){
      if(item is Map<String,dynamic>){
        final work=MuseumCloudWork.parse(item);
        if(work!=null)works.add(work);
      }
      if(works.length>=24)break;
    }
    final next=doc['next_cursor'];
    return MuseumCloudPage(works,
      next is String && RegExp(r'^\d{1,4}$').hasMatch(next)?next:null);
  }
  void close()=>_client.close();
}
).hasMatch(next)?next:null);
  }

  Future<MuseumCloudPage> search(String query,{
    String scope='all',String? cursor,
  }) async {
    if(!enabled)throw StateError('D1 museum API not configured');
    if(query.trim().length<2 || query.length>90)throw ArgumentError('Query length');
    if(!const <String>['all','artist','title'].contains(scope)) {
      throw ArgumentError('Scope');
    }
    if(cursor!=null && !RegExp(r'^\d{1,4}$').hasMatch(cursor)) {
      throw ArgumentError('Cursor');
    }
    final base=Uri.parse(_base);
    final prefix=base.path.endsWith('/') ?
      base.path.substring(0,base.path.length-1):base.path;
    final uri=base.replace(path:'$prefix/api/v1/museum-search',
      queryParameters:{'q':query.trim(),'scope':scope,
        if(cursor!=null)'cursor':cursor});
    final response=await _client.get(uri,headers:{
      'Accept':'application/json',
    }).timeout(const Duration(seconds:12));
    if(response.statusCode!=200) {
      throw StateError('Museum cloud HTTP '+response.statusCode.toString());
    }
    final doc=jsonDecode(utf8.decode(response.bodyBytes));
    if(doc is! Map || doc['source']!='ArtDrift-Museums' ||
       doc['works'] is! List)throw const FormatException('Invalid museum D1 response');
    final works=<MuseumCloudWork>[];
    for(final item in doc['works'] as List){
      if(item is Map<String,dynamic>){
        final work=MuseumCloudWork.parse(item);
        if(work!=null)works.add(work);
      }
      if(works.length>=24)break;
    }
    final next=doc['next_cursor'];
    return MuseumCloudPage(works,
      next is String && RegExp(r'^\d{1,4}$').hasMatch(next)?next:null);
  }
  void close()=>_client.close();
}
