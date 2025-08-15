import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/Widgets/keywords_section.dart';

class CardDetails extends StatefulWidget {
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

  @override
  State<CardDetails> createState() => _CardDetailsState();
}

class _CardDetailsState extends State<CardDetails> {
  bool isFavorite = false;

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
    // Categorize keywords
    final tasteKeywords = widget.keywords
        .where((kw) => kw['type'] == 'taste')
        .toList();
    final costKeywords = widget.keywords
        .where((kw) => kw['type'] == 'cost')
        .toList();
    final generalKeywords = widget.keywords
        .where((kw) => kw['type'] != 'taste' && kw['type'] != 'cost')
        .toList();

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
                child: Container(
                  height: 180,
                  width: double.infinity,
                  color: Colors.grey[400],
                ),
              ),
              Positioned(
                top: 8,
                right: 8,
                child: GestureDetector(
                  onTap: () {
                    setState(() {
                      isFavorite = !isFavorite;
                    });
                  },
                  child: Container(
                    width: 36,
                    height: 36,
                    decoration: const BoxDecoration(
                      color: Colors.black,
                      shape: BoxShape.circle,
                    ),
                    child: Icon(
                      Icons.favorite,
                      color: isFavorite
                          ? colorUse.sentimentColor
                          : Colors.white,
                      size: 24,
                    ),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            widget.dishName,
            style: const TextStyle(
              fontFamily: 'InriaSans',
              fontWeight: FontWeight.bold,
              fontSize: 22,
              color: Colors.black,
            ),
          ),
          Text(
            '${widget.cuisine}, ${widget.taste}',
            style: const TextStyle(fontSize: 20, color: Colors.black87),
          ),
          const SizedBox(height: 8),
          RichText(
            text: TextSpan(
              children: [
                TextSpan(
                  text: 'Ratings: ',
                  style: const TextStyle(
                    fontFamily: 'InriaSans',
                    fontWeight: FontWeight.bold,
                    fontSize: 22,
                    color: Colors.black,
                  ),
                ),
                TextSpan(
                  text:
                      '${widget.positiveReviews} positive reviews from ${widget.totalReviews}',
                  style: const TextStyle(
                    fontFamily: 'InriaSans',
                    fontWeight: FontWeight.normal,
                    fontSize: 18,
                    color: Colors.black,
                  ),
                ),
              ],
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
                  widthFactor: widget.ratingPercent / 100,
                  child: Container(
                    decoration: BoxDecoration(
                      color: colorUse.sentimentColor,
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                ),
                Center(
                  child: Text(
                    '${widget.ratingPercent}%',
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      fontSize: 18,
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
              fontSize: 22,
              color: Colors.black,
            ),
          ),
          const SizedBox(height: 6),
          // Taste keywords
          KeywordsSection(
            tasteKeywords: tasteKeywords,
            costKeywords: costKeywords,
            generalKeywords: generalKeywords,
            onKeywordTap: _showKeywordModal,
          ),
        ],
      ),
    );
  }
}
