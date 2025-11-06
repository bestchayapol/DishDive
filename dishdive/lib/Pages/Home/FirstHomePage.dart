import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/Utils/api_config.dart';
import 'package:dishdive/Pages/Profile/profile.dart';
import 'package:dishdive/widgets/ListView.dart';
import 'package:dishdive/widgets/MapView.dart';
import 'package:dishdive/widgets/modal_filter.dart';
import 'package:dishdive/components/my_textfield.dart';
import 'package:dishdive/provider/token_provider.dart';
import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart' show compute;
import 'package:dishdive/parsers/restaurant_parsers.dart';
import 'package:provider/provider.dart';
import 'package:dishdive/provider/location_provider.dart';

class FirstHomePage extends StatefulWidget {
  const FirstHomePage({super.key});

  @override
  State<FirstHomePage> createState() => _FirstHomePageState();
}

class _FirstHomePageState extends State<FirstHomePage>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final TextEditingController _searchController = TextEditingController();
  String? username;
  String? profileImageUrl;
  int? userid;
  List<Map<String, dynamic>> restaurants = [];
  bool isLoadingRestaurants = false;
  bool isSearching = false;
  CancelToken? _searchCancelToken;

  // Debounce timer for search
  Timer? _debounceTimer;

  @override
  void initState() {
    super.initState();
    // Defer initial loads until after first frame to keep UI responsive
    WidgetsBinding.instance.addPostFrameCallback((_) {
      fetchUserData();
      fetchRestaurants();
    });
    _tabController = TabController(length: 2, vsync: this);

    // Add listener to search controller with proper debouncing
    _searchController.addListener(_onSearchTextChanged);
  }

  Future<void> fetchUserData() async {
    final token = Provider.of<TokenProvider>(context, listen: false).token;
    final userId = Provider.of<TokenProvider>(context, listen: false).userId;

    if (token == null || userId == null) {
      return;
    }

    try {
      Dio dio = Dio();
      final response = await dio.get(
        ApiConfig.getProfileOfCurrentUserByUserIdEndpoint(userId),
        options: Options(headers: ApiConfig.authHeaders(token)),
      );

      if (response.statusCode == 200) {
        final parsedJson = response.data;
        setState(() {
          profileImageUrl = parsedJson['image_link'];
          username = parsedJson['username'];
          userid = userId;
        });
      }
    } catch (e) {
      print('Error fetching user data: $e');
      // Handle error silently for now
    }
  }

  Future<void> fetchRestaurants() async {
    final token = Provider.of<TokenProvider>(context, listen: false).token;

    if (token == null) {
      return;
    }

    setState(() {
      isLoadingRestaurants = true;
    });

    try {
      Dio dio = Dio();
      final loc = Provider.of<LocationProvider>(context, listen: false);
      final query = <String, dynamic>{};
      if (loc.hasLocation) {
        query['user_lat'] = loc.latitude;
        query['user_lng'] = loc.longitude;
        // Optionally set a default radius (e.g., 25km)
        query['radius_km'] = 25;
      }
      final response = await dio.get(
        ApiConfig.getRestaurantListEndpoint,
        queryParameters: query,
        options: Options(headers: ApiConfig.authHeaders(token)),
      );

      if (response.statusCode == 200) {
        final parsed = await compute(
          parseRestaurantList,
          jsonEncode(response.data),
        );
        if (!mounted) return;
        setState(() {
          restaurants = parsed;
          isLoadingRestaurants = false;
        });
      }
    } catch (e) {
      print('Error fetching restaurants: $e');
      setState(() {
        isLoadingRestaurants = false;
      });
    }
  }

  Future<void> searchRestaurantsByDish(String query) async {
    if (query.trim().isEmpty) {
      fetchRestaurants(); // Reset to full list
      return;
    }

    final token = Provider.of<TokenProvider>(context, listen: false).token;

    if (token == null) {
      return;
    }

    setState(() {
      isSearching = true;
    });

    try {
      _searchCancelToken?.cancel("new search");
      _searchCancelToken = CancelToken();
      Dio dio = Dio();
      final loc = Provider.of<LocationProvider>(context, listen: false);
      final payload = {
        'dish_name': query,
        if (loc.hasLocation) 'latitude': loc.latitude,
        if (loc.hasLocation) 'longitude': loc.longitude,
      };
      final response = await dio.post(
        ApiConfig.searchRestaurantsByDishEndpoint,
        data: payload,
        options: Options(headers: ApiConfig.authHeaders(token)),
        cancelToken: _searchCancelToken,
      );

      if (response.statusCode == 200) {
        final parsed = await compute(
          parseSearchResults,
          jsonEncode(response.data),
        );
        if (!mounted) return;
        setState(() {
          restaurants = parsed;
          isSearching = false;
        });
      }
    } catch (e) {
      print('Error searching restaurants: $e');
      setState(() {
        isSearching = false;
      });
    }
  }

  void _onSearchTextChanged() {
    // Cancel previous timer
    _debounceTimer?.cancel();

    // Create new timer with debouncing
    _debounceTimer = Timer(const Duration(milliseconds: 500), () {
      searchRestaurantsByDish(_searchController.text);
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    _searchController.dispose();
    _searchCancelToken?.cancel("dispose");
    _debounceTimer?.cancel(); // Cancel timer on dispose
    super.dispose();
  }

  void _showFilterModal() {
    showDialog(context: context, builder: (context) => const FilterModal());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: colorUse.backgroundColor,
      body: Column(
        children: [
          // Top black section with profile icon and search bar
          Container(
            color: colorUse.appBarColor,
            padding: const EdgeInsets.only(
              top: 40,
              left: 16,
              right: 16,
              bottom: 18,
            ),
            child: Column(
              children: [
                // Row for profile icon (right-aligned)
                Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    GestureDetector(
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(builder: (_) => Profile()),
                        );
                      },
                      child: Container(
                        width: 48,
                        height: 48,
                        decoration: const BoxDecoration(
                          shape: BoxShape.circle,
                          color: Colors.grey, // Placeholder color
                        ),
                        child:
                            profileImageUrl != null &&
                                profileImageUrl!.isNotEmpty
                            ? ClipOval(
                                child: Image.network(
                                  profileImageUrl!,
                                  width: 48,
                                  height: 48,
                                  fit: BoxFit.cover,
                                  errorBuilder: (context, error, stackTrace) {
                                    return const Icon(
                                      Icons.person,
                                      color: Colors.white,
                                      size: 24,
                                    );
                                  },
                                  loadingBuilder:
                                      (context, child, loadingProgress) {
                                        if (loadingProgress == null)
                                          return child;
                                        return const Center(
                                          child: CircularProgressIndicator(
                                            strokeWidth: 2,
                                            valueColor:
                                                AlwaysStoppedAnimation<Color>(
                                                  Colors.white,
                                                ),
                                          ),
                                        );
                                      },
                                ),
                              )
                            : const Icon(
                                Icons.person,
                                color: Colors.white,
                                size: 24,
                              ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 18),
                // Search bar
                Row(
                  children: [
                    Expanded(
                      child: MyTextField(
                        hintText: "Search dish",
                        obscureText: false,
                        controller: _searchController,
                        border: true,
                        iconData: Icons.search,
                      ),
                    ),
                    const SizedBox(width: 8),
                    GestureDetector(
                      onTap: _showFilterModal,
                      child: Container(
                        width: 44,
                        height: 44,
                        decoration: BoxDecoration(
                          color: colorUse.activeButton,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: const Icon(
                          Icons.filter_alt,
                          color: Colors.white,
                          size: 28,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          // Toggle button (TabBar)
          Container(
            color: colorUse.backgroundColor,
            child: TabBar(
              controller: _tabController,
              tabs: [
                Tab(
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      vertical: 4,
                      horizontal: 18,
                    ),
                    child: const Text('List View'),
                  ),
                ),
                Tab(
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      vertical: 4,
                      horizontal: 18,
                    ),
                    child: const Text('Map View'),
                  ),
                ),
              ],
              indicator: BoxDecoration(
                color: colorUse.activeButton,
                borderRadius: BorderRadius.circular(4),
                border: Border.all(color: colorUse.activeButton, width: 2),
              ),
              indicatorSize: TabBarIndicatorSize.tab,
              labelColor: Colors.white,
              unselectedLabelColor: colorUse.activeButton,
              labelStyle: const TextStyle(
                fontFamily: 'InriaSans',
                fontWeight: FontWeight.normal,
                fontSize: 22,
              ),
              unselectedLabelStyle: const TextStyle(
                fontFamily: 'InriaSans',
                fontWeight: FontWeight.normal,
                fontSize: 22,
              ),
              dividerColor: Colors.transparent,
            ),
          ),
          // TabBarView for content
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                ListViewWidget(
                  restaurants: restaurants,
                  isLoading: isLoadingRestaurants || isSearching,
                ),
                MapViewWidget(
                  restaurants: restaurants,
                  isLoading: isLoadingRestaurants || isSearching,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
