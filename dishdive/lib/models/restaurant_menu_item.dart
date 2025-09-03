class RestaurantMenuItem {
  final int dishId;
  final String dishName;
  final String? imageLink;
  final double sentimentScore;
  final String? cuisine;
  final String? prominentFlavor;
  final bool isFavorite;
  final double recommendScore;

  RestaurantMenuItem({
    required this.dishId,
    required this.dishName,
    this.imageLink,
    required this.sentimentScore,
    this.cuisine,
    this.prominentFlavor,
    required this.isFavorite,
    required this.recommendScore,
  });

  factory RestaurantMenuItem.fromJson(Map<String, dynamic> json) {
    return RestaurantMenuItem(
      dishId: json['dish_id'] ?? 0,
      dishName: json['dish_name'] ?? '',
      imageLink: json['image_link'],
      sentimentScore: (json['sentiment_score'] ?? 0.0).toDouble(),
      cuisine: json['cuisine'],
      prominentFlavor: json['prominent_flavor'],
      isFavorite: json['is_favorite'] ?? false,
      recommendScore: (json['recommend_score'] ?? 0.0).toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'dish_id': dishId,
      'dish_name': dishName,
      'image_link': imageLink,
      'sentiment_score': sentimentScore,
      'cuisine': cuisine,
      'prominent_flavor': prominentFlavor,
      'is_favorite': isFavorite,
      'recommend_score': recommendScore,
    };
  }

  // Helper method to get rating percentage from sentiment score
  int get ratingPercent {
    // Convert sentiment score (0.0-5.0) to percentage (0-100)
    return ((sentimentScore / 5.0) * 100).round().clamp(0, 100);
  }

  // Helper method to get taste/flavor display text
  String get tasteDisplay {
    return prominentFlavor ?? 'Mixed';
  }

  // Helper method to get cuisine display text  
  String get cuisineDisplay {
    return cuisine ?? 'Various';
  }
}
