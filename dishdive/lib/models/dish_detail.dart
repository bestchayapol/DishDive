class DishDetail {
  final int dishId;
  final String dishName;
  final String? imageLink;
  final double sentimentScore;
  final int positiveReviews;
  final int totalReviews;
  final String? cuisine;
  final String? prominentFlavor;
  final Map<String, List<String>> topKeywords;
  final bool isFavorite;

  DishDetail({
    required this.dishId,
    required this.dishName,
    this.imageLink,
    required this.sentimentScore,
    required this.positiveReviews,
    required this.totalReviews,
    this.cuisine,
    this.prominentFlavor,
    required this.topKeywords,
    required this.isFavorite,
  });

  factory DishDetail.fromJson(Map<String, dynamic> json) {
    return DishDetail(
      dishId: json['dish_id'] ?? 0,
      dishName: json['dish_name'] ?? '',
      imageLink: json['image_link'],
      sentimentScore: (json['sentiment_score'] ?? 0.0).toDouble(),
      positiveReviews: json['positive_reviews'] ?? 0,
      totalReviews: json['total_reviews'] ?? 0,
      cuisine: json['cuisine'],
      prominentFlavor: json['prominent_flavor'],
      topKeywords: Map<String, List<String>>.from(
        (json['top_keywords'] ?? {}).map(
          (key, value) => MapEntry(key, List<String>.from(value ?? [])),
        ),
      ),
      isFavorite: json['is_favorite'] ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'dish_id': dishId,
      'dish_name': dishName,
      'image_link': imageLink,
      'sentiment_score': sentimentScore,
      'positive_reviews': positiveReviews,
      'total_reviews': totalReviews,
      'cuisine': cuisine,
      'prominent_flavor': prominentFlavor,
      'top_keywords': topKeywords,
      'is_favorite': isFavorite,
    };
  }

  // Helper method to get rating percentage from sentiment score
  int get ratingPercent {
    if (totalReviews == 0) return 0;
    return ((positiveReviews / totalReviews) * 100).round().clamp(0, 100);
  }

  // Helper method to get taste/flavor display text
  String get tasteDisplay {
    return prominentFlavor ?? 'Mixed';
  }

  // Helper method to get cuisine display text  
  String get cuisineDisplay {
    return cuisine ?? 'Various';
  }

  // Helper method to get formatted keywords by category
  List<Map<String, dynamic>> get tasteKeywords {
    return _parseKeywordsFromCategory(['flavor', 'taste'], 'taste');
  }

  List<Map<String, dynamic>> get costKeywords {
    return _parseKeywordsFromCategory(['cost', 'price'], 'cost');
  }

  List<Map<String, dynamic>> get generalKeywords {
    return _parseKeywordsFromCategory(['general'], 'general');
  }

  List<Map<String, dynamic>> _parseKeywordsFromCategory(List<String> categories, String type) {
    List<Map<String, dynamic>> result = [];
    
    for (String category in categories) {
      if (topKeywords.containsKey(category)) {
        for (String keyword in topKeywords[category]!) {
          // Parse "keyword (count)" format
          RegExp regex = RegExp(r'^(.+?)\s*\((\d+)\)$');
          Match? match = regex.firstMatch(keyword);
          
          if (match != null) {
            result.add({
              'label': match.group(1)?.trim() ?? keyword,
              'count': int.tryParse(match.group(2) ?? '0') ?? 0,
              'type': type,
            });
          } else {
            result.add({
              'label': keyword,
              'count': 0,
              'type': type,
            });
          }
        }
      }
    }
    
    return result;
  }

  // Get all keywords combined for backward compatibility
  List<Map<String, dynamic>> get allKeywords {
    List<Map<String, dynamic>> all = [];
    all.addAll(tasteKeywords);
    all.addAll(costKeywords);
    all.addAll(generalKeywords);
    return all;
  }
}
