import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';

class CardReviews extends StatelessWidget {
  final TextEditingController reviewController;

  const CardReviews({super.key, required this.reviewController});

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
              // Grey rectangle instead of image
              Container(
                height: 180,
                width: double.infinity,
                decoration: BoxDecoration(
                  color: Colors.grey[400],
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                "Fried rice",
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 20,
                  color: Colors.black,
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
