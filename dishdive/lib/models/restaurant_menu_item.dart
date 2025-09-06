class RestaurantMenuItem {
  final int dishId;
  final String dishName;
  final String? imageLink;
  final double sentimentScore;
  final String? cuisine;
  final String? prominentFlavor;
  final bool isFavorite;
  final double recommendScore;

  // Added
  final int positiveReviews;
  final int totalReviews;

  RestaurantMenuItem({
    required this.dishId,
    required this.dishName,
    this.imageLink,
    required this.sentimentScore,
    this.cuisine,
    this.prominentFlavor,
    required this.isFavorite,
    required this.recommendScore,
    // Added (not required to avoid breaking other constructors)
    this.positiveReviews = 0,
    this.totalReviews = 0,
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
      // Added
      positiveReviews: (json['positive_reviews'] ?? 0) is num
          ? (json['positive_reviews'] as num).toInt()
          : 0,
      totalReviews: (json['total_reviews'] ?? 0) is num
          ? (json['total_reviews'] as num).toInt()
          : 0,
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
      // Added
      'positive_reviews': positiveReviews,
      'total_reviews': totalReviews,
    };
  }

  // Percent based on positive/total; fallback to sentiment_score if needed
  int get ratingPercent {
    if (totalReviews == 0) return 0;
    return ((positiveReviews / totalReviews) * 100).round().clamp(0, 100);
  }

  String get tasteDisplay => prominentFlavor ?? 'Mixed';
  String get cuisineDisplay => cuisine ?? 'Various';
}
