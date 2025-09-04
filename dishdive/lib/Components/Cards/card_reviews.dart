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
              // Dish image or grey placeholder
              Container(
                height: 180,
                width: double.infinity,
                decoration: BoxDecoration(
                  color: Colors.grey[400],
                  borderRadius: BorderRadius.circular(12),
                ),
                child: dishData.imageLink != null && dishData.imageLink!.isNotEmpty
                    ? ClipRRect(
                        borderRadius: BorderRadius.circular(12),
                        child: Image.network(
                          dishData.imageLink!,
                          width: double.infinity,
                          height: 180,
                          fit: BoxFit.cover,
                          errorBuilder: (context, error, stackTrace) {
                            return Container(
                              color: Colors.grey[400],
                              child: const Icon(
                                Icons.broken_image,
                                color: Colors.white,
                                size: 50,
                              ),
                            );
                          },
                        ),
                      )
                    : Container(
                        decoration: BoxDecoration(
                          color: Colors.grey[400],
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Center(
                          child: Icon(
                            Icons.restaurant,
                            color: Colors.white,
                            size: 50,
                          ),
                        ),
                      ),
              ),
              const SizedBox(height: 8),
              Text(
                dishData.dishName,
                style: const TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 20,
                  color: Colors.black,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                dishData.resName,
                style: const TextStyle(
                  fontSize: 16,
                  color: Colors.grey,
                ),
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
