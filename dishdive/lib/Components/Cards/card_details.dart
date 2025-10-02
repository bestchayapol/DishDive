import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/Widgets/keywords_section.dart';

class CardDetails extends StatefulWidget {
  final int dishId;
  final String imagePath;
  final String dishName;
  final String cuisine;
  final String taste;
  final int ratingPercent;
  final int positiveReviews;
  final int totalReviews;
  final List<Map<String, dynamic>> keywords;
  final bool isFavorite;
  final VoidCallback? onFavoriteToggle;

  const CardDetails({
    super.key,
    required this.dishId,
    required this.imagePath,
    required this.dishName,
    required this.cuisine,
    required this.taste,
    required this.ratingPercent,
    required this.positiveReviews,
    required this.totalReviews,
    required this.keywords,
    this.isFavorite = false,
    this.onFavoriteToggle,
  });

  @override
  State<CardDetails> createState() => _CardDetailsState();
}

class _CardDetailsState extends State<CardDetails> {
  late bool isFavorite;

  @override
  void initState() {
    super.initState();
    isFavorite = widget.isFavorite;
  }

  @override
  void didUpdateWidget(CardDetails oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.isFavorite != widget.isFavorite) {
      isFavorite = widget.isFavorite;
    }
  }

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
    // Clamp and convert rating percent to width factor for the bar
    final double widthFactor = (widget.ratingPercent.clamp(0, 100)) / 100.0;
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
      width: double.infinity,
      child: Column(
        mainAxisSize:
            MainAxisSize.min, // Allow column to size itself based on content
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Title row with inlined favorite toggle (image removed)
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Text(
                  widget.dishName,
                  style: const TextStyle(
                    fontFamily: 'InriaSans',
                    fontWeight: FontWeight.bold,
                    fontSize: 22,
                    color: Colors.black,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              const SizedBox(width: 8),
              GestureDetector(
                onTap: () {
                  setState(() {
                    isFavorite = !isFavorite;
                  });
                  widget.onFavoriteToggle?.call();
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
                    color: isFavorite ? colorUse.sentimentColor : Colors.white,
                    size: 24,
                  ),
                ),
              ),
            ],
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
              // Dark background when 0%
              color: Colors.black,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Stack(
              children: [
                // Pink fill proportional to ratingPercent
                FractionallySizedBox(
                  widthFactor: widthFactor,
                  alignment: Alignment.centerLeft,
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
