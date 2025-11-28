import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/Utils/api_config.dart';
import 'package:dishdive/Components/Settings/settings_template.dart';
import 'package:dishdive/Components/Settings/settings_sentiment.dart';
import 'package:dishdive/Components/Settings/settings_cuisine.dart';
import 'package:dishdive/Components/Settings/settings_flavor.dart';
import 'package:dishdive/Components/Settings/settings_cost.dart';
import 'package:dishdive/Components/Settings/settings_restrictions.dart';
import 'package:dishdive/provider/token_provider.dart';
import 'package:provider/provider.dart';
import 'package:dio/dio.dart';

class SetPref extends StatefulWidget {
  const SetPref({super.key});

  @override
  State<SetPref> createState() => _SetPrefState();
}

class _SetPrefState extends State<SetPref> {
  bool isLoading = true;
  final Dio dio = Dio();
  late TokenProvider tokenProvider;

  // Sentiment values (0.0 to 1.0) - should be loaded from "sentiment" keyword
  double sentimentThreshold = 0.0; // Will be loaded from backend
  int sentimentValue = 0; // Will be loaded from backend

  // Available keywords from backend
  List<Map<String, dynamic>> allKeywords = [];

  // Selected keywords by category
  Map<String, Set<String>> selectedKeywords = {
    'cuisine': {},
    'restriction': {},
    'flavor': {},
    'cost': {},
  };

  // Available options by category
  Map<String, List<String>> availableOptions = {
    'cuisine': [],
    'restriction': [],
    'flavor': ["Sweet", "Salty", "Sour", "Spicy", "Oily"], // Static options
    'cost': ["Cheap", "Moderate", "Expensive"], // Static options
  };

  @override
  void initState() {
    super.initState();
    _initializeData();
  }

  Future<void> _initializeData() async {
    setState(() {
      isLoading = true;
    });

    try {
      tokenProvider = Provider.of<TokenProvider>(context, listen: false);
      await loadUserSettings();
    } catch (e) {
      print('Error initializing preferences data: $e');
    } finally {
      setState(() {
        isLoading = false;
      });
    }
  }

  Future<void> loadUserSettings() async {
    try {
      final token = tokenProvider.token;
      final userId = tokenProvider.userId;

      if (token == null || userId == null) return;

      final response = await dio.get(
        ApiConfig.getUserSettingsEndpoint(userId),
        options: Options(headers: ApiConfig.authHeaders(token)),
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = response.data;
        final List<dynamic> keywords = data['keywords'] ?? [];

        setState(() {
          allKeywords = keywords.cast<Map<String, dynamic>>();

          // Clear previous selections
          selectedKeywords.forEach((key, value) => value.clear());
          availableOptions['cuisine']!.clear();
          availableOptions['restriction']!.clear();

          // Process keywords for cuisine/restriction and sentiment only
          for (var keyword in allKeywords) {
            final String name = keyword['keyword'] ?? '';
            final String category = keyword['category'] ?? '';
            final bool isPreferred = keyword['is_preferred'] ?? false;
            final double preferenceValue =
                (keyword['preference_value']?.toDouble() ?? 0.0);

            // Sentiment (system)
            if (category == 'system' && name.toLowerCase() == 'sentiment') {
              sentimentThreshold = preferenceValue;
              sentimentValue = (preferenceValue * 100).round();
              continue;
            }

            // Dynamic lists for cuisine and restriction only
            if (category == 'cuisine' &&
                !availableOptions['cuisine']!.contains(name)) {
              availableOptions['cuisine']!.add(name);
            } else if (category == 'restriction' &&
                !availableOptions['restriction']!.contains(name)) {
              availableOptions['restriction']!.add(name);
            }

            // Apply selected state for cuisine/restriction based on Thai keywords
            if ((category == 'cuisine' || category == 'restriction') &&
                isPreferred) {
              selectedKeywords[category]!.add(name);
            }
          }

          // Initialize English group selections from normalized arrays returned by backend
          final List<dynamic> flavorEN = data['flavor_en_preferred'] ?? [];
          final List<dynamic> costEN = data['cost_en_preferred'] ?? [];
          selectedKeywords['flavor'] = flavorEN
              .map((e) => e.toString())
              .toSet();
          selectedKeywords['cost'] = costEN.map((e) => e.toString()).toSet();

          // Ensure static options exist even if not in database (fallback)
          if (availableOptions['flavor']!.isEmpty) {
            availableOptions['flavor']!.addAll([
              "Sweet",
              "Salty",
              "Sour",
              "Spicy",
              "Oily",
            ]);
          }
          if (availableOptions['cost']!.isEmpty) {
            availableOptions['cost']!.addAll([
              "Cheap",
              "Moderate",
              "Expensive",
            ]);
          }
        });
      }
    } catch (e) {
      print('Error loading user settings: $e');
    }
  }

  Future<void> savePreferences() async {
    try {
      final token = tokenProvider.token;
      final userId = tokenProvider.userId;

      if (token == null || userId == null) return;

      // Convert current selections to API format
      List<Map<String, dynamic>> settingsUpdates = [];

      for (var keyword in allKeywords) {
        int keywordId = keyword['keyword_id'] ?? 0;
        String name = keyword['keyword'] ?? '';
        String category = keyword['category'] ?? '';

        // Get current blacklist value to preserve it
        double currentBlacklist = keyword['blacklist_value']?.toDouble() ?? 0.0;
        double preferenceValue;

        // Handle sentiment keyword specifically
        if (category == 'system' && name.toLowerCase() == 'sentiment') {
          preferenceValue = sentimentThreshold;
        } else {
          // Skip Thai flavor/cost here; rely on normalized EN arrays instead
          if (category == 'flavor' || category == 'cost') {
            continue;
          }
          // Handle regular categories
          bool isSelected = selectedKeywords[category]?.contains(name) ?? false;
          preferenceValue = isSelected
              ? 1.0
              : 0.0; // Use 1.0 for selected, 0.0 for not selected
        }

        settingsUpdates.add({
          'keyword_id': keywordId,
          'preference_value': preferenceValue,
          'blacklist_value': currentBlacklist, // Preserve existing blacklist
        });
      }

      final Map<String, dynamic> requestData = {
        'settings': settingsUpdates,
        'flavor_en_preferred': selectedKeywords['flavor']!.toList(),
        'cost_en_preferred': selectedKeywords['cost']!.toList(),
      };

      final response = await dio.post(
        ApiConfig.updateUserSettingsEndpoint(userId),
        data: requestData,
        options: Options(headers: ApiConfig.authHeaders(token)),
      );

      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Preferences saved successfully')),
        );
      }
    } catch (e) {
      print('Error saving preferences: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Failed to save preferences')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return Scaffold(
        backgroundColor: colorUse.backgroundColor,
        appBar: AppBar(
          backgroundColor: colorUse.appBarColor,
          elevation: 0,
          leading: IconButton(
            icon: const Icon(Icons.arrow_back, color: Colors.white),
            onPressed: () => Navigator.pop(context),
          ),
          title: const Text(
            "Set Preferences",
            style: TextStyle(
              fontFamily: 'InriaSans',
              fontWeight: FontWeight.bold,
              fontSize: 24,
              color: Colors.white,
            ),
          ),
          centerTitle: true,
        ),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      backgroundColor: colorUse.backgroundColor,
      appBar: AppBar(
        backgroundColor: colorUse.appBarColor,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          "Set Preferences",
          style: TextStyle(
            fontFamily: 'InriaSans',
            fontWeight: FontWeight.bold,
            fontSize: 32,
            color: Colors.white,
          ),
        ),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.save, color: Colors.white),
            onPressed: savePreferences,
            tooltip: 'Save Preferences',
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  SettingsDropdown(
                    title: "Sentiment ratio",
                    child: SentimentSetting(
                      value: sentimentValue,
                      onIncrement: () => setState(() {
                        sentimentValue = (sentimentValue + 1).clamp(0, 100);
                        sentimentThreshold = sentimentValue / 100.0;
                      }),
                      onDecrement: () => setState(() {
                        sentimentValue = (sentimentValue - 1).clamp(0, 100);
                        sentimentThreshold = sentimentValue / 100.0;
                      }),
                      isBlacklist: false,
                    ),
                  ),
                  SettingsDropdown(
                    title: "Cuisine type",
                    child: CuisineSetting(
                      cuisines: availableOptions['cuisine']!,
                      selectedCuisines: selectedKeywords['cuisine']!,
                      isBlacklist: false,
                      onToggle: (cuisine) {
                        setState(() {
                          if (selectedKeywords['cuisine']!.contains(cuisine)) {
                            selectedKeywords['cuisine']!.remove(cuisine);
                          } else {
                            selectedKeywords['cuisine']!.add(cuisine);
                          }
                        });
                      },
                    ),
                  ),
                  SettingsDropdown(
                    title: "Flavors",
                    child: FlavorSetting(
                      flavors: availableOptions['flavor']!,
                      selectedFlavors: selectedKeywords['flavor']!,
                      isBlacklist: false,
                      onToggle: (flavor) {
                        // Fixed: removed isHigh parameter
                        setState(() {
                          if (selectedKeywords['flavor']!.contains(flavor)) {
                            selectedKeywords['flavor']!.remove(flavor);
                          } else {
                            selectedKeywords['flavor']!.add(flavor);
                          }
                        });
                      },
                    ),
                  ),
                  SettingsDropdown(
                    title: "Cost",
                    child: CostSetting(
                      costs: availableOptions['cost']!,
                      selectedCosts: selectedKeywords['cost']!,
                      isBlacklist: false,
                      onToggle: (cost) {
                        setState(() {
                          if (selectedKeywords['cost']!.contains(cost)) {
                            selectedKeywords['cost']!.remove(cost);
                          } else {
                            selectedKeywords['cost']!.add(cost);
                          }
                        });
                      },
                    ),
                  ),
                  SettingsDropdown(
                    title: "Restrictions",
                    child: RestrictionSetting(
                      restrictions: availableOptions['restriction']!,
                      selectedRestrictions: selectedKeywords['restriction']!,
                      isBlacklist: false,
                      onToggle: (restriction) {
                        setState(() {
                          if (selectedKeywords['restriction']!.contains(
                            restriction,
                          )) {
                            selectedKeywords['restriction']!.remove(
                              restriction,
                            );
                          } else {
                            selectedKeywords['restriction']!.add(restriction);
                          }
                        });
                      },
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
