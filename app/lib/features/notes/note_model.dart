/// 笔记模型（对应后端 NoteOut）。
class Note {
  final String id;
  final String title;
  final String content;
  final String sourceType; // manual | pdf | pptx | markdown
  final String? sourceName;
  final String? createdAt;
  final String? updatedAt;

  const Note({
    required this.id,
    required this.title,
    required this.content,
    required this.sourceType,
    this.sourceName,
    this.createdAt,
    this.updatedAt,
  });

  factory Note.fromJson(Map<String, dynamic> json) => Note(
        id: json['id']?.toString() ?? '',
        title: json['title']?.toString() ?? '',
        content: json['content']?.toString() ?? '',
        sourceType: json['source_type']?.toString() ?? 'manual',
        sourceName: json['source_name']?.toString(),
        createdAt: json['created_at']?.toString(),
        updatedAt: json['updated_at']?.toString(),
      );

  Note copyWith({String? title, String? content}) => Note(
        id: id,
        title: title ?? this.title,
        content: content ?? this.content,
        sourceType: sourceType,
        sourceName: sourceName,
        createdAt: createdAt,
        updatedAt: updatedAt,
      );
}
