import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/Components/Settings/settings_template.dart';
import 'package:dishdive/Components/Settings/settings_sentiment.dart';
import 'package:dishdive/Components/Settings/settings_cuisine.dart';
import 'package:dishdive/Components/Settings/settings_flavor.dart';
import 'package:dishdive/Components/Settings/settings_cost.dart';
import 'package:dishdive/Components/Settings/settings_restrictions.dart';
// Commented out for static data example
// import 'package:dio/dio.dart';
// import 'package:provider/provider.dart';;

class SetBlack extends StatefulWidget {
  const SetBlack({super.key});

  @override
  State<SetBlack> createState() => _SetBlackState();
}

class _SetBlackState extends State<SetBlack> {
  int sentimentValue = 55;

  final List<String> cuisines = [
    "Thai",
    "Indian",
    "Japanese",
    "Chinese",
    "French",
    "Italian",
  ];
  Set<String> selectedCuisines = {};

  final List<String> flavors = ["Sweet", "Salty", "Sour", "Spicy", "Oily"];
  Set<String> zeroToMedium = {};
  Set<String> mediumToHigh = {};

  final List<String> costs = ["Cheap", "Moderate", "Expensive"];
  Set<String> selectedCosts = {};

  final List<String> restrictions = ["Halal", "Vegan"];
  Set<String> selectedRestrictions = {};

  @override
  Widget build(BuildContext context) {
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
          "Set Blacklist",
          style: TextStyle(
            fontFamily: 'InriaSans',
            fontWeight: FontWeight.bold,
            fontSize: 32,
            color: Colors.white,
          ),
        ),
        centerTitle: true,
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
                      onIncrement: () => setState(
                        () =>
                            sentimentValue = (sentimentValue + 1).clamp(0, 100),
                      ),
                      onDecrement: () => setState(
                        () =>
                            sentimentValue = (sentimentValue - 1).clamp(0, 100),
                      ),
                      isBlacklist: true,
                    ),
                  ),
                  SettingsDropdown(
                    title: "Cuisine type",
                    child: CuisineSetting(
                      cuisines: cuisines,
                      selectedCuisines: selectedCuisines,
                      isBlacklist: true,
                      onToggle: (cuisine) {
                        setState(() {
                          if (selectedCuisines.contains(cuisine)) {
                            selectedCuisines.remove(cuisine);
                          } else {
                            selectedCuisines.add(cuisine);
                          }
                        });
                      },
                    ),
                  ),
                  SettingsDropdown(
                    title: "Flavors",
                    child: FlavorSetting(
                      flavors: flavors,
                      zeroToMedium: zeroToMedium,
                      mediumToHigh: mediumToHigh,
                      isBlacklist: true,
                      onToggle: (flavor, isHigh) {
                        setState(() {
                          if (isHigh) {
                            if (mediumToHigh.contains(flavor)) {
                              mediumToHigh.remove(flavor);
                            } else {
                              mediumToHigh.add(flavor);
                            }
                          } else {
                            if (zeroToMedium.contains(flavor)) {
                              zeroToMedium.remove(flavor);
                            } else {
                              zeroToMedium.add(flavor);
                            }
                          }
                        });
                      },
                    ),
                  ),
                  SettingsDropdown(
                    title: "Cost",
                    child: CostSetting(
                      costs: costs,
                      selectedCosts: selectedCosts,
                      isBlacklist: true,
                      onToggle: (cost) {
                        setState(() {
                          if (selectedCosts.contains(cost)) {
                            selectedCosts.remove(cost);
                          } else {
                            selectedCosts.add(cost);
                          }
                        });
                      },
                    ),
                  ),
                  SettingsDropdown(
                    title: "Restrictions",
                    child: RestrictionSetting(
                      restrictions: restrictions,
                      selectedRestrictions: selectedRestrictions,
                      isBlacklist: true,
                      onToggle: (restriction) {
                        setState(() {
                          if (selectedRestrictions.contains(restriction)) {
                            selectedRestrictions.remove(restriction);
                          } else {
                            selectedRestrictions.add(restriction);
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
