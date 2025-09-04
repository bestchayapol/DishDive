class DishReviewPageResponse {
  final int dishId;
  final String dishName;
  final String? imageLink;
  final int resId;
  final String resName;

  DishReviewPageResponse({
    required this.dishId,
    required this.dishName,
    this.imageLink,
    required this.resId,
    required this.resName,
  });

  factory DishReviewPageResponse.fromJson(Map<String, dynamic> json) {
    return DishReviewPageResponse(
      dishId: json['dish_id'],
      dishName: json['dish_name'],
      imageLink: json['image_link'],
      resId: json['res_id'],
      resName: json['res_name'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'dish_id': dishId,
      'dish_name': dishName,
      'image_link': imageLink,
      'res_id': resId,
      'res_name': resName,
    };
  }
}

class SubmitReviewRequest {
  final int dishId;
  final int resId;
  final int userId;
  final String reviewText;

  SubmitReviewRequest({
    required this.dishId,
    required this.resId,
    required this.userId,
    required this.reviewText,
  });

  factory SubmitReviewRequest.fromJson(Map<String, dynamic> json) {
    return SubmitReviewRequest(
      dishId: json['dish_id'],
      resId: json['res_id'],
      userId: json['user_id'],
      reviewText: json['review_text'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'dish_id': dishId,
      'res_id': resId,
      'user_id': userId,
      'review_text': reviewText,
    };
  }
}

class SubmitReviewResponse {
  final bool success;

  SubmitReviewResponse({
    required this.success,
  });

  factory SubmitReviewResponse.fromJson(Map<String, dynamic> json) {
    return SubmitReviewResponse(
      success: json['success'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'success': success,
    };
  }
}
