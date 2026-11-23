import 'dart:convert';
import 'package:http/http.dart' as http;

class MomaCatalogWork {
  const MomaCatalogWork({
    required this.id,required this.title,required this.artist,
    required this.sourceUrl,required this.date,required this.medium,
    required this.dimensions,required this.department,this.thumbnailUrl,
  });
  final int id;
  final String title,artist,sourceUrl,date,medium,dimensions,department;
  final String? thumbnailUrl;

  static MomaCatalogWork? parse(Map<String,dynamic> item) {
    final id=item['id'];
    final source=item['source_url'];
    final uri=source is String?Uri.tryParse(source):null;
    if(id is! int || id<=0 || uri==null || uri.scheme!='https' ||
       uri.host!='www.moma.org' || uri.path!='/collection/works/$id')return null;
    final image=item['thumbnail_url'];
    final pic=image is String?Uri.tryParse(image):null;
    final safe=pic!=null && pic.scheme=='https' &&
      pic.userInfo.isEmpty && pic.host.isNotEmpty &&
      (item['image_rights']=='CC0' || item['image_rights']=='Public Domain');
    String str(String field)=>item[field] is String?(item[field] as String).trim():'';
    return MomaCatalogWork(
      id:id,title:str('title'),artist:str('artist'),
      sourceUrl:source,date:str('date'),medium:str('medium'),
      dimensions:str('dimensions'),department:str('department'),
      thumbnailUrl:safe?image:null);
  }
}

class MomaCatalogPage {
  const MomaCatalogPage(this.works,this.nextCursor);
  final List<MomaCatalogWork> works;
  final String? nextCursor;
}

class MomaCloudCatalog {
  MomaCloudCatalog({String? baseUrl,http.Client? client}):
    _base=baseUrl??const String.fromEnvironment('ARTDRIFT_CATALOG_API_BASE'),
    _client=client??http.Client();
  final String _base;
  final http.Client _client;

  bool get enabled {
    final uri=Uri.tryParse(_base);
    return uri!=null && uri.scheme=='https' && uri.host.isNotEmpty &&
       uri.userInfo.isEmpty && (uri.port==443 || !uri.hasPort) &&
       uri.query.isEmpty && !uri.hasFragment;
  }

  Future<MomaCatalogPage> search(String q,{
    String scope='all',String? cursor,
  }) async {
    if(!enabled)throw StateError('MoMA API not configured');
    if(q.trim().length<2 || q.length>90)throw ArgumentError('Query length');
    if(!['all','artist','title'].contains(scope))throw ArgumentError('Scope');
    if(cursor!=null && !RegExp(r'^\d{1,4}$').hasMatch(cursor)){
      throw ArgumentError('Cursor');
    }
    final origin=Uri.parse(_base);
    final path=origin.path.endsWith('/')?
      origin.path.substring(0,origin.path.length-1):origin.path;
    final uri=origin.replace(path:'$path/api/v1/search',
      queryParameters:{
        'q':q.trim(),'scope':scope,
        if(cursor!=null)'cursor':cursor,
      });
    final response=await _client.get(uri,headers:{
      'Accept':'application/json',
    }).timeout(const Duration(seconds:12));
    if(response.statusCode!=200) {
      throw StateError('Catalog HTTP '+response.statusCode.toString());
    }
    final doc=jsonDecode(utf8.decode(response.bodyBytes));
    if(doc is! Map || doc['source']!='MoMA' || doc['works'] is! List){
      throw const FormatException('Invalid MoMA API response');
    }
    final works=<MomaCatalogWork>[];
    for(final record in doc['works'] as List) {
      if(record is Map<String,dynamic>) {
        final work=MomaCatalogWork.parse(record);
        if(work!=null)works.add(work);
      }
      if(works.length>=24)break;
    }
    final next=doc['next_cursor'];
    return MomaCatalogPage(works,
      next is String && RegExp(r'^\d{1,4}$').hasMatch(next)?next:null);
  }
  void close()=>_client.close();
}
