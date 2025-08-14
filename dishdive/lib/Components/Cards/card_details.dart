import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';

class CardDetails extends StatelessWidget {
  final String imagePath;
  final String dishName;
  final String cuisine;
  final String taste;
  final int ratingPercent;
  final int positiveReviews;
  final int totalReviews;
  final List<Map<String, dynamic>> keywords;

  const CardDetails({
    super.key,
    required this.imagePath,
    required this.dishName,
    required this.cuisine,
    required this.taste,
    required this.ratingPercent,
    required this.positiveReviews,
    required this.totalReviews,
    required this.keywords,
  });

  void _showKeywordModal(BuildContext context, String label, int count) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: colorUse.accent,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        content: SizedBox(
          height: 60,
          child: Center(
            child: Text(
              '$label, mentioned in $count reviews',
              style: const TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
                color: Colors.black,
              ),
              textAlign: TextAlign.center,
            ),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: colorUse.secondaryColor,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.08),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Stack(
            children: [
              ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: Image.asset(
                  imagePath,
                  height: 120,
                  width: double.infinity,
                  fit: BoxFit.cover,
                ),
              ),
              Positioned(
                top: 8,
                right: 8,
                child: Icon(
                  Icons.favorite,
                  color: Colors.white,
                  size: 28,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            dishName,
            style: const TextStyle(
              fontFamily: 'InriaSans',
              fontWeight: FontWeight.bold,
              fontSize: 22,
              color: Colors.black,
            ),
          ),
          Text(
            '$cuisine, $taste',
            style: const TextStyle(
              fontSize: 16,
              color: Colors.black87,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Ratings: $positiveReviews positive reviews from $totalReviews',
            style: const TextStyle(
              fontSize: 15,
              color: Colors.black,
            ),
          ),
          const SizedBox(height: 4),
          Container(
            width: double.infinity,
            height: 28,
            decoration: BoxDecoration(
              color: colorUse.sentimentColor,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Stack(
              children: [
                FractionallySizedBox(
                  widthFactor: ratingPercent / 100,
                  child: Container(
                    decoration: BoxDecoration(
                      color: colorUse.sentimentColor,
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                ),
                Center(
                  child: Text(
                    '$ratingPercent%',
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      fontSize: 16,
                    ),
                  ),
                ),
                Positioned(
                  right: 0,
                  top: 0,
                  bottom: 0,
                  child: Container(
                    width: 28,
                    decoration: BoxDecoration(
                      color: Colors.black,
                      borderRadius: const BorderRadius.only(
                        topRight: Radius.circular(8),
                        bottomRight: Radius.circular(8),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          const Text(
            'Top Keywords',
            style: TextStyle(
              fontWeight: FontWeight.bold,
              fontSize: 17,
              color: Colors.black,
            ),
          ),
          const SizedBox(height: 6),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: keywords.map((kw) {
              return GestureDetector(
                onTap: () => _showKeywordModal(context, kw['label'], kw['count']),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: colorUse.accent,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    '${kw['label']} (${kw['count']})',
                    style: const TextStyle(
                      color: Colors.black,
                      fontWeight: FontWeight.bold,
                      fontSize: 15,
                    ),
                  ),
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }
}