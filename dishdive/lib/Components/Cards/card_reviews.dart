import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/models/review_models.dart';

class CardReviews extends StatelessWidget {
  final TextEditingController reviewController;
  final DishReviewPageResponse dishData;

  const CardReviews({
    super.key,
    required this.reviewController,
    required this.dishData,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Dish Information Card
        Container(
          decoration: BoxDecoration(
            color: colorUse.secondaryColor,
            borderRadius: BorderRadius.circular(12),
          ),
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                dishData.dishName,
                style: const TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 20,
                  color: Colors.black,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                dishData.resName,
                style: const TextStyle(fontSize: 16, color: Colors.grey),
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),
        // Review Text Field Card
        Container(
          decoration: BoxDecoration(
            color: colorUse.secondaryColor,
            borderRadius: BorderRadius.circular(12),
          ),
          padding: const EdgeInsets.all(12),
          child: TextField(
            controller: reviewController,
            maxLines: 5,
            style: const TextStyle(color: Colors.black),
            decoration: InputDecoration(
              hintText: "Write your review",
              filled: true,
              fillColor: colorUse.secondaryColor,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide.none,
              ),
              hintStyle: const TextStyle(color: Colors.black54),
              contentPadding: const EdgeInsets.all(16),
            ),
          ),
        ),
      ],
    );
  }
}
